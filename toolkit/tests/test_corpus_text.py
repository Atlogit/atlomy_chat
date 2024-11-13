"""
Tests for the corpus text module.

Tests the handling of line numbers and divisions with work structures.
"""

import pytest
from unittest.mock import patch, MagicMock
from toolkit.migration.corpus_text import CorpusText
from app.models.text_division import TextDivision
from app.models.text_line import TextLine
from toolkit.parsers.text import TextLine as ParserTextLine
from toolkit.parsers.sentence import Sentence
from toolkit.parsers.citation import Citation

@pytest.fixture
def corpus_text():
    """Create a CorpusText instance for testing."""
    session = MagicMock()
    return CorpusText(session)

def test_convert_to_parser_text_line_with_work_structure(corpus_text):
    """Test converting database line to parser line with work structure."""
    # Mock TLG_WORKS_INDEX and TLG_MASTER_INDEX
    mock_works_index = {
        "0627": {"010": "De Articulis"}
    }
    mock_master_index = {
        "hippocrates": {
            "tlg_id": "TLG0627",
            "works": {
                "De Articulis": ["Section", "Line"]
            }
        }
    }
    
    # Create test division and line
    division = TextDivision(
        author_id_field="0627",
        work_number_field="010",
        chapter="1"
    )
    db_line = TextLine(
        content=".1.5 Some text here",
        line_number=5
    )
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        parser_line = corpus_text._convert_to_parser_text_line(db_line, division)
        
        assert parser_line.content == "Some text here"
        assert parser_line.line_number == 5
        assert parser_line.citation.section == "1"
        assert parser_line.citation.line == "5"
        assert parser_line.citation.hierarchy_levels == {"section": "1", "line": "5"}

def test_get_line_number_with_work_structure(corpus_text):
    """Test getting line number from citation with work structure."""
    # Mock TLG_WORKS_INDEX and TLG_MASTER_INDEX
    mock_works_index = {
        "0627": {"010": "De Articulis"}
    }
    mock_master_index = {
        "hippocrates": {
            "tlg_id": "TLG0627",
            "works": {
                "De Articulis": ["Section", "Line"]
            }
        }
    }
    
    # Create test line with citation
    citation = Citation(
        author_id="0627",
        work_id="010",
        hierarchy_levels={"section": "1", "line": "5"}
    )
    parser_line = ParserTextLine(
        content="Some text here",
        citation=citation,
        line_number=None
    )
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        line_number = corpus_text._get_line_number(parser_line)
        assert line_number == 5

def test_get_sentence_division_with_work_structure(corpus_text):
    """Test getting division from sentence with work structure."""
    # Mock TLG_WORKS_INDEX and TLG_MASTER_INDEX
    mock_works_index = {
        "0627": {"010": "De Articulis"}
    }
    mock_master_index = {
        "hippocrates": {
            "tlg_id": "TLG0627",
            "works": {
                "De Articulis": ["Section", "Line"]
            }
        }
    }
    
    # Create test sentence with citation
    citation = Citation(
        author_id="0627",
        work_id="010",
        hierarchy_levels={"section": "1", "line": "5"}
    )
    sentence = Sentence(
        content="Some text here",
        citation=citation,
        source_lines=[]
    )
    division = TextDivision(chapter="1")
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        division_value = corpus_text._get_sentence_division(sentence, division)
        assert division_value == "1"

def test_get_sentence_lines_with_work_structure(corpus_text):
    """Test getting sentence lines with work structure."""
    # Mock TLG_WORKS_INDEX and TLG_MASTER_INDEX
    mock_works_index = {
        "0627": {"010": "De Articulis"}
    }
    mock_master_index = {
        "hippocrates": {
            "tlg_id": "TLG0627",
            "works": {
                "De Articulis": ["Section", "Line"]
            }
        }
    }
    
    # Create test sentence with source lines
    citation1 = Citation(
        author_id="0627",
        work_id="010",
        hierarchy_levels={"section": "1", "line": "5"}
    )
    citation2 = Citation(
        author_id="0627",
        work_id="010",
        hierarchy_levels={"section": "1", "line": "6"}
    )
    source_line1 = ParserTextLine(
        content="First line",
        citation=citation1,
        line_number=5
    )
    source_line2 = ParserTextLine(
        content="Second line",
        citation=citation2,
        line_number=6
    )
    sentence = Sentence(
        content="First line Second line",
        citation=None,
        source_lines=[source_line1, source_line2]
    )
    
    # Create database lines
    db_line1 = TextLine(content="First line", line_number=5)
    db_line2 = TextLine(content="Second line", line_number=6)
    db_lines = [db_line1, db_line2]
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        sentence_lines = corpus_text._get_sentence_lines(sentence, db_lines)
        assert len(sentence_lines) == 2
        assert sentence_lines[0].content == "First line"
        assert sentence_lines[1].content == "Second line"
