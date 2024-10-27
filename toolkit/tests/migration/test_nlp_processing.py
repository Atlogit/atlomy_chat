"""
Tests for NLP processing validation in the migration toolkit.

This module tests the accuracy of sentence segmentation, NLP analysis results,
and performance with large texts.
"""

import pytest
from typing import List
import spacy
from sqlalchemy.ext.asyncio import AsyncSession
import psutil
import time

from toolkit.nlp.pipeline import NLPPipeline
from toolkit.parsers.sentence import SentenceParser, Sentence, TextLine
from toolkit.migration.corpus_processor import CorpusProcessor
from toolkit.migration.content_validator import ContentValidator

# Sample texts for testing
SAMPLE_TEXTS = {
    "basic": "Τὸ σῶμα τοῦ ἀνθρώπου ἔχει ὀστέα· καὶ νεῦρα καὶ σάρκας.",
    "multi_sentence": (
        "ἡ κεφαλὴ ἔχει ἐγκέφαλον. "
        "τὸ στῆθος ἔχει καρδίαν· "
        "ἡ γαστὴρ ἔχει ἧπαρ καὶ σπλῆνα."
    ),
    "hyphenated": (
        "ὁ ἐγκέφα-\n"
        "λος ἐστὶ μαλακός."
    ),
    "complex": (
        "περὶ δὲ τῆς ἱερῆς νούσου καλεομένης ὧδε ἔχει· "
        "οὐδέν τί μοι δοκέει τῶν ἄλλων θειοτέρη εἶναι νούσων οὐδὲ ἱερωτέρη· "
        "ἀλλὰ φύσιν μὲν ἔχει καὶ πρόφασιν."
    ),
    "invalid_chars": "This contains invalid characters: abc123",
    "mixed_scripts": "Τὸ σῶμα mixed with Latin characters"
}

@pytest.fixture
def nlp_pipeline():
    """Create NLPPipeline instance for testing."""
    return NLPPipeline()

@pytest.fixture
def sentence_parser():
    """Create SentenceParser instance for testing."""
    return SentenceParser()

@pytest.fixture
def sample_text_lines() -> List[TextLine]:
    """Create sample TextLine objects for testing."""
    return [
        TextLine(content="Τὸ σῶμα τοῦ ἀνθρώπου ἔχει ὀστέα· "),
        TextLine(content="καὶ νεῦρα καὶ σάρκας."),
        TextLine(content="ἡ κεφαλὴ ἔχει ἐγκέφαλον. "),
        TextLine(content="ὁ ἐγκέφα-"),
        TextLine(content="λος ἐστὶ μαλακός.")
    ]

async def test_sentence_segmentation(sentence_parser, sample_text_lines):
    """Test accuracy of sentence segmentation."""
    # Parse lines into sentences
    sentences = sentence_parser.parse_lines(sample_text_lines)
    
    # Verify correct number of sentences
    assert len(sentences) == 3
    
    # Verify sentence content
    assert sentences[0].content == "Τὸ σῶμα τοῦ ἀνθρώπου ἔχει ὀστέα· καὶ νεῦρα καὶ σάρκας."
    assert sentences[1].content == "ἡ κεφαλὴ ἔχει ἐγκέφαλον."
    assert sentences[2].content == "ὁ ἐγκέφαλος ἐστὶ μαλακός."
    
    # Verify source line references
    assert len(sentences[0].source_lines) == 2
    assert len(sentences[1].source_lines) == 1
    assert len(sentences[2].source_lines) == 2

def test_nlp_analysis_basic(nlp_pipeline):
    """Test basic NLP analysis results."""
    # Process sample text
    result = nlp_pipeline.process_text(SAMPLE_TEXTS["basic"])
    
    # Verify structure
    assert "text" in result
    assert "tokens" in result
    assert len(result["tokens"]) > 0
    
    # Verify token attributes
    token = result["tokens"][0]
    required_attrs = ["text", "lemma", "pos", "tag", "dep", "morph", "category"]
    for attr in required_attrs:
        assert attr in token

def test_nlp_analysis_categories(nlp_pipeline):
    """Test category detection in NLP analysis."""
    # Process text with anatomical terms
    result = nlp_pipeline.process_text(SAMPLE_TEXTS["basic"])
    
    # Extract categories
    categories = nlp_pipeline.extract_categories(result)
    
    # Verify anatomical terms are categorized
    assert len(categories) > 0
    # Assuming the model categorizes body parts
    assert any("BODY" in cat for cat in categories)

def test_nlp_batch_processing(nlp_pipeline):
    """Test batch processing performance."""
    # Create batch of texts
    texts = list(SAMPLE_TEXTS.values())
    
    # Process batch
    results = nlp_pipeline.process_batch(texts)
    
    # Verify all texts processed
    assert len(results) == len(texts)
    
    # Verify structure of each result
    for result in results:
        assert "text" in result
        assert "tokens" in result
        assert len(result["tokens"]) > 0

def test_hyphenation_handling(sentence_parser):
    """Test handling of hyphenated words across lines."""
    lines = [
        TextLine(content="ὁ ἐγκέφα-"),
        TextLine(content="λος ἐστὶ μαλακός.")
    ]
    
    sentences = sentence_parser.parse_lines(lines)
    
    # Verify hyphenation was handled correctly
    assert len(sentences) == 1
    assert "ἐγκέφαλος" in sentences[0].content
    assert "-" not in sentences[0].content

async def test_large_text_performance(nlp_pipeline):
    """Test performance with large texts."""
    # Create large text by repeating sample
    large_text = SAMPLE_TEXTS["complex"] * 100
    
    # Record memory usage before processing
    process = psutil.Process()
    mem_before = process.memory_info().rss
    
    # Process large text and measure token count
    start_time = time.time()
    result = nlp_pipeline.process_text(large_text)
    processing_time = time.time() - start_time
    
    # Record memory usage after processing
    mem_after = process.memory_info().rss
    mem_increase = mem_after - mem_before
    
    # Verify processing completed within reasonable time and memory
    assert len(result["tokens"]) > 1000  # Arbitrary threshold for large text
    assert processing_time < 60  # Should process within 60 seconds
    assert mem_increase < 500 * 1024 * 1024  # Memory increase should be less than 500MB

def test_unicode_handling(nlp_pipeline):
    """Test handling of Unicode Greek characters."""
    # Process text with various Unicode Greek characters
    result = nlp_pipeline.process_text(SAMPLE_TEXTS["complex"])
    
    # Verify correct handling of Greek characters
    for token in result["tokens"]:
        # Check that Greek characters are preserved
        assert any(0x0370 <= ord(c) <= 0x03FF for c in token["text"])

def test_script_validation():
    """Test script-specific validation for Greek text."""
    # Test valid Greek text
    assert ContentValidator.validate_script(SAMPLE_TEXTS["basic"], "greek") is True
    
    # Test invalid characters
    with pytest.raises(ValueError):
        ContentValidator.validate_script(SAMPLE_TEXTS["invalid_chars"], "greek")
    
    # Test mixed scripts
    with pytest.raises(ValueError):
        ContentValidator.validate_script(SAMPLE_TEXTS["mixed_scripts"], "greek")

def test_batch_memory_usage(nlp_pipeline):
    """Test memory usage with different batch sizes."""
    # Create large dataset
    texts = [SAMPLE_TEXTS["basic"]] * 1000
    
    # Test with different batch sizes
    batch_sizes = [100, 500, 1000]
    for batch_size in batch_sizes:
        nlp_pipeline.batch_size = batch_size
        
        # Record memory before
        process = psutil.Process()
        mem_before = process.memory_info().rss
        
        # Process batch
        results = nlp_pipeline.process_batch(texts[:batch_size])
        
        # Record memory after
        mem_after = process.memory_info().rss
        mem_increase = mem_after - mem_before
        
        # Verify reasonable memory usage (less than 100MB per 100 texts)
        assert mem_increase < (batch_size / 100) * 100 * 1024 * 1024

def test_error_handling(nlp_pipeline):
    """Test error handling and recovery."""
    # Test with invalid input
    with pytest.raises(ValueError):
        nlp_pipeline.process_text("")
    
    # Test with None input
    with pytest.raises(ValueError):
        nlp_pipeline.process_text(None)
    
    # Test recovery after error
    with pytest.raises(ValueError):
        nlp_pipeline.process_text("")
    # Should still work after error
    result = nlp_pipeline.process_text(SAMPLE_TEXTS["basic"])
    assert len(result["tokens"]) > 0

async def test_corpus_processor_integration(
    nlp_pipeline, 
    sentence_parser, 
    sample_text_lines, 
    monkeypatch
):
    """Test integration of all components in CorpusProcessor."""
    # Mock database session
    class MockSession:
        async def execute(self, stmt):
            class MockResult:
                def scalars(self):
                    class MockScalars:
                        def all(self):
                            return [sample_text_lines]
                    return MockScalars()
            return MockResult()
            
        async def commit(self):
            pass
            
        async def rollback(self):
            pass
            
        async def flush(self):
            pass
    
    # Create CorpusProcessor with mocked session
    processor = CorpusProcessor(MockSession())
    
    # Process sample work
    await processor.process_work(1)
    
    # Get processed sentences
    sentences = await processor.get_work_sentences(1)
    
    # Verify processing results
    assert len(sentences) > 0
    for sentence in sentences:
        # Verify sentence has content
        assert sentence.content
        # Verify source line references
        assert len(sentence.source_lines) > 0

def test_cache_behavior(nlp_pipeline):
    """Test caching behavior in batch processing."""
    # Process same text multiple times
    text = SAMPLE_TEXTS["basic"]
    
    # First processing
    start_time = time.time()
    result1 = nlp_pipeline.process_text(text)
    first_processing_time = time.time() - start_time
    
    # Second processing (should be faster if cached)
    start_time = time.time()
    result2 = nlp_pipeline.process_text(text)
    second_processing_time = time.time() - start_time
    
    # Verify results are identical
    assert result1 == result2
    
    # Verify second processing was faster (if caching is implemented)
    # Note: This test might need adjustment based on actual caching implementation
    assert second_processing_time <= first_processing_time
"""
