"""
Tests for the citation processor module.

Tests the processing of citations with work structures.
"""

import pytest
from unittest.mock import patch
from toolkit.migration.citation_processor import CitationProcessor
from toolkit.parsers.citation import Citation

@pytest.fixture
def citation_processor():
    """Create a CitationProcessor instance for testing."""
    return CitationProcessor()

def test_process_text_with_work_structure(citation_processor):
    """Test processing text with work structure."""
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
    
    text = ".1.5 First line\n.1.6 Second line"
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        sections = citation_processor.process_text(text, default_author_id="0627", default_work_id="010")
        
        assert len(sections) == 2
        
        # Check first section
        assert sections[0]['content'] == "First line"
        citation = sections[0]['citation']
        assert citation.section == "1"
        assert citation.line == "5"
        assert citation.hierarchy_levels == {"section": "1", "line": "5"}
        
        # Check second section
        assert sections[1]['content'] == "Second line"
        citation = sections[1]['citation']
        assert citation.section == "1"
        assert citation.line == "6"
        assert citation.hierarchy_levels == {"section": "1", "line": "6"}

def test_process_text_with_inherited_citation(citation_processor):
    """Test processing text with inherited citation."""
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
    
    text = ".1.5 First line\nContinuation line"
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        sections = citation_processor.process_text(text, default_author_id="0627", default_work_id="010")
        
        assert len(sections) == 2
        
        # Check first section
        assert sections[0]['content'] == "First line"
        citation = sections[0]['citation']
        assert citation.section == "1"
        assert citation.line == "5"
        assert citation.hierarchy_levels == {"section": "1", "line": "5"}
        
        # Check second section (should inherit citation)
        assert sections[1]['content'] == "Continuation line"
        assert sections[1]['citation'] is None
        inherited = sections[1]['inherited_citation']
        assert inherited.section == "1"
        assert inherited.line == "5"
        assert inherited.hierarchy_levels == {"section": "1", "line": "5"}

def test_process_text_with_multiple_sections(citation_processor):
    """Test processing text with multiple sections."""
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
    
    text = ".1.5 First section\n.2.1 Second section\n.2.2 Still second section"
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        sections = citation_processor.process_text(text, default_author_id="0627", default_work_id="010")
        
        assert len(sections) == 3
        
        # Check first section
        assert sections[0]['content'] == "First section"
        citation = sections[0]['citation']
        assert citation.section == "1"
        assert citation.line == "5"
        assert citation.hierarchy_levels == {"section": "1", "line": "5"}
        
        # Check second section
        assert sections[1]['content'] == "Second section"
        citation = sections[1]['citation']
        assert citation.section == "2"
        assert citation.line == "1"
        assert citation.hierarchy_levels == {"section": "2", "line": "1"}
        
        # Check third section
        assert sections[2]['content'] == "Still second section"
        citation = sections[2]['citation']
        assert citation.section == "2"
        assert citation.line == "2"
        assert citation.hierarchy_levels == {"section": "2", "line": "2"}

def test_process_text_with_title(citation_processor):
    """Test processing text with title citations."""
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
    
    text = ".t.1 Title line\n.1.1 First section"
    
    with patch('assets.indexes.work_numbers.TLG_WORKS_INDEX', mock_works_index), \
         patch('assets.indexes.tlg_index.TLG_MASTER_INDEX', mock_master_index):
        sections = citation_processor.process_text(text, default_author_id="0627", default_work_id="010")
        
        assert len(sections) == 2
        
        # Check title section
        assert sections[0]['content'] == "Title line"
        citation = sections[0]['citation']
        assert citation.title_number == "1"
        assert citation.hierarchy_levels == {}
        
        # Check content section
        assert sections[1]['content'] == "First section"
        citation = sections[1]['citation']
        assert citation.section == "1"
        assert citation.line == "1"
        assert citation.hierarchy_levels == {"section": "1", "line": "1"}
