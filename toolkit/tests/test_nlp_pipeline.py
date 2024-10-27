"""Tests for the NLP pipeline module."""

import pytest
from pathlib import Path
import spacy
from toolkit.nlp.pipeline import NLPPipeline

# Sample Greek text for testing
SAMPLE_TEXT = """
ἐγὼ δὲ περὶ μὲν τούτων τῶν θεῶν οὐκ οἶδα οὔθ᾽ ὡς εἰσὶν οὔθ᾽ ὡς οὐκ εἰσὶν οὔθ᾽ 
ὁποῖοί τινες ἰδέαν: πολλὰ γὰρ τὰ κωλύοντα εἰδέναι ἥ τ᾽ ἀδηλότης καὶ βραχὺς ὢν 
ὁ βίος τοῦ ἀνθρώπου.
"""

@pytest.fixture
def nlp_pipeline():
    """Create a test NLP pipeline instance."""
    return NLPPipeline(batch_size=100)

def test_pipeline_initialization(nlp_pipeline):
    """Test that the pipeline initializes correctly."""
    assert nlp_pipeline.nlp is not None
    assert isinstance(nlp_pipeline.nlp, spacy.language.Language)
    assert nlp_pipeline.batch_size == 100

def test_process_text(nlp_pipeline):
    """Test processing a single text."""
    result = nlp_pipeline.process_text(SAMPLE_TEXT)
    
    assert isinstance(result, dict)
    assert "text" in result
    assert "tokens" in result
    assert len(result["tokens"]) > 0
    
    # Check token structure
    token = result["tokens"][0]
    required_fields = ["text", "lemma", "pos", "tag", "dep", "morph", "category"]
    for field in required_fields:
        assert field in token

def test_process_batch(nlp_pipeline):
    """Test processing multiple texts in a batch."""
    texts = [SAMPLE_TEXT, SAMPLE_TEXT]  # Use same text twice for testing
    results = nlp_pipeline.process_batch(texts)
    
    assert isinstance(results, list)
    assert len(results) == 2
    
    for result in results:
        assert isinstance(result, dict)
        assert "text" in result
        assert "tokens" in result
        assert len(result["tokens"]) > 0

def test_extract_categories(nlp_pipeline):
    """Test extracting categories from processed text."""
    # Process text first
    processed = nlp_pipeline.process_text(SAMPLE_TEXT)
    
    # Add some test categories
    processed["tokens"][0]["category"] = "Body Part, Topography"
    processed["tokens"][1]["category"] = "Body Part"
    
    # Extract categories
    categories = nlp_pipeline.extract_categories(processed)
    
    assert isinstance(categories, list)
    assert "Body Part" in categories
    assert "Topography" in categories
    assert len(categories) == 2

def test_invalid_text(nlp_pipeline):
    """Test handling of invalid text input."""
    with pytest.raises(Exception):
        nlp_pipeline.process_text(None)

def test_empty_batch(nlp_pipeline):
    """Test processing an empty batch."""
    results = nlp_pipeline.process_batch([])
    assert isinstance(results, list)
    assert len(results) == 0

def test_large_batch(nlp_pipeline):
    """Test processing a large batch of texts."""
    # Create a batch larger than the batch_size
    texts = [SAMPLE_TEXT] * 150  # 150 texts
    results = nlp_pipeline.process_batch(texts)
    
    assert isinstance(results, list)
    assert len(results) == 150
    
    # Verify all texts were processed
    for result in results:
        assert isinstance(result, dict)
        assert len(result["tokens"]) > 0
