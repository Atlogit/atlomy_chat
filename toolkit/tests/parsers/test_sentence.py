"""
Tests for the sentence parser module.

Tests sentence splitting while maintaining references to original lines and citations.
"""

import pytest
from typing import List
from toolkit.parsers.sentence import SentenceParser, Sentence
from toolkit.parsers.text import TextLine
from toolkit.parsers.citation import Citation

@pytest.fixture
def sentence_parser():
    """Create a SentenceParser instance for testing."""
    return SentenceParser()

@pytest.fixture
def sample_lines():
    """Create sample text lines with citations."""
    citation1 = Citation(author_id="0057", work_id="001", division="1", subdivision="2")
    citation2 = Citation(author_id="0057", work_id="001", division="1", subdivision="3")
    
    return [
        TextLine(content="First sentence. Second sentence.", citation=citation1),
        TextLine(content="Third sentence· Fourth sentence.", citation=citation1),
        TextLine(content="Fifth sentence continues", citation=citation1),
        TextLine(content="and ends here.", citation=citation1),
        TextLine(content="New section sentence.", citation=citation2)
    ]

async def test_basic_sentence_splitting(sentence_parser, sample_lines):
    """Test basic sentence splitting functionality."""
    sentences = await sentence_parser.parse_lines(sample_lines)
    
    assert len(sentences) == 5
    assert sentences[0].content == "First sentence."
    assert sentences[1].content == "Second sentence."
    assert sentences[2].content == "Third sentence·"
    assert sentences[3].content == "Fourth sentence."
    assert sentences[4].content == "Fifth sentence continues and ends here."

async def test_citation_preservation(sentence_parser, sample_lines):
    """Test that citations are preserved for each sentence."""
    sentences = await sentence_parser.parse_lines(sample_lines)
    
    # First four sentences should have citation1
    for i in range(4):
        citations = sentence_parser.get_sentence_citations(sentences[i])
        assert len(citations) == 1
        assert citations[0].author_id == "0057"
        assert citations[0].subdivision == "2"
    
    # Last sentence should have citation2
    citations = sentence_parser.get_sentence_citations(sentences[4])
    assert citations[0].subdivision == "3"

async def test_sentence_across_lines(sentence_parser):
    """Test handling of sentences that span multiple lines."""
    citation = Citation(author_id="0057", work_id="001")
    lines = [
        TextLine(content="This sentence", citation=citation),
        TextLine(content="continues across", citation=citation),
        TextLine(content="multiple lines.", citation=citation)
    ]
    
    sentences = await sentence_parser.parse_lines(lines)
    
    assert len(sentences) == 1
    assert sentences[0].content == "This sentence continues across multiple lines."
    assert len(sentences[0].source_lines) == 3

async def test_mixed_delimiters(sentence_parser):
    """Test handling of mixed sentence delimiters (. and ·)."""
    citation = Citation(author_id="0057", work_id="001")
    lines = [
        TextLine(content="First sentence. Second sentence· Third sentence.", citation=citation)
    ]
    
    sentences = await sentence_parser.parse_lines(lines)
    
    assert len(sentences) == 3
    assert sentences[0].content == "First sentence."
    assert sentences[1].content == "Second sentence·"
    assert sentences[2].content == "Third sentence."

async def test_empty_lines(sentence_parser):
    """Test handling of empty lines."""
    citation = Citation(author_id="0057", work_id="001")
    lines = [
        TextLine(content="First sentence.", citation=citation),
        TextLine(content="", citation=citation),
        TextLine(content="Second sentence.", citation=citation)
    ]
    
    sentences = await sentence_parser.parse_lines(lines)
    
    assert len(sentences) == 2
    assert sentences[0].content == "First sentence."
    assert sentences[1].content == "Second sentence."

async def test_sentence_positions(sentence_parser):
    """Test tracking of sentence positions within source lines."""
    citation = Citation(author_id="0057", work_id="001")
    lines = [
        TextLine(content="First sentence. Second sentence.", citation=citation)
    ]
    
    sentences = await sentence_parser.parse_lines(lines)
    
    assert sentences[0].start_position == 0
    assert sentences[0].end_position == 15  # Length of "First sentence."
    assert sentences[1].start_position == 16  # Start after space
    assert sentences[1].end_position == 32  # Length of "Second sentence."

async def test_multiple_citations_per_sentence(sentence_parser):
    """Test handling of sentences that span lines with different citations."""
    citation1 = Citation(author_id="0057", work_id="001", division="1")
    citation2 = Citation(author_id="0057", work_id="001", division="2")
    
    lines = [
        TextLine(content="This sentence starts", citation=citation1),
        TextLine(content="and continues", citation=citation2),
        TextLine(content="until the end.", citation=citation2)
    ]
    
    sentences = await sentence_parser.parse_lines(lines)
    
    assert len(sentences) == 1
    citations = sentence_parser.get_sentence_citations(sentences[0])
    assert len(citations) == 2  # Should have both citations
    assert citations[0].division == "1"
    assert citations[1].division == "2"

async def test_sentence_without_ending(sentence_parser):
    """Test handling of text without sentence-ending punctuation."""
    citation = Citation(author_id="0057", work_id="001")
    lines = [
        TextLine(content="This has no ending", citation=citation)
    ]
    
    sentences = await sentence_parser.parse_lines(lines)
    
    assert len(sentences) == 1
    assert sentences[0].content == "This has no ending"

async def test_multiple_dots(sentence_parser):
    """Test handling of multiple consecutive dots."""
    citation = Citation(author_id="0057", work_id="001")
    lines = [
        TextLine(content="First sentence... Second sentence.", citation=citation)
    ]
    
    sentences = await sentence_parser.parse_lines(lines)
    
    assert len(sentences) == 2
    assert sentences[0].content == "First sentence..."
    assert sentences[1].content == "Second sentence."

async def test_special_characters(sentence_parser):
    """Test preservation of special characters in sentences."""
    citation = Citation(author_id="0057", work_id="001")
    lines = [
        TextLine(content="Greek text: τὸ σῶμα. Latin text: corpus.", citation=citation)
    ]
    
    sentences = await sentence_parser.parse_lines(lines)
    
    assert len(sentences) == 2
    assert "τὸ σῶμα" in sentences[0].content
    assert "corpus" in sentences[1].content

async def test_empty_input(sentence_parser):
    """Test handling of empty input."""
    sentences = await sentence_parser.parse_lines([])
    assert len(sentences) == 0
