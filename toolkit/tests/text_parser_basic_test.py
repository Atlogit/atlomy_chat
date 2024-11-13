"""Test cases for basic text parsing functionality."""

import pytest
from pathlib import Path
from toolkit.parsers.text import TextParser, TextLine

@pytest.fixture
def text_parser():
    """Create a TextParser instance for testing."""
    return TextParser()

def test_clean_text():
    """Test text cleaning functionality."""
    parser = TextParser()
    
    # Test basic cleaning
    assert parser._clean_text("  test  text  ") == "test text"
    
    # Test preservation of citation dots
    assert parser._clean_text("  .1.1  text  ") == ".1.1 text"
    
    # Test curly brace removal
    assert parser._clean_text("{test} text") == "test text"
    
    # Test apostrophe normalization
    assert parser._clean_text("test'text") == "testʼtext"

def test_extract_title_text():
    """Test title text extraction."""
    parser = TextParser()
    
    assert parser.extract_title_text("<Title>") == "Title"
    assert parser.extract_title_text("Text <Title> More") == "Title"
    assert parser.extract_title_text("No Title") is None

@pytest.mark.asyncio
async def test_basic_line_parsing():
    """Test basic line parsing without citations."""
    parser = TextParser()
    content = """Simple line
Another line
Third line"""
    
    tmp_path = Path("test_file.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 3
        
        # Basic lines should have no citations or line numbers
        for line in lines:
            assert line.citation is None
            assert line.line_number is None
            assert not line.is_title
            assert line.title_number is None
            
        # Check content is preserved
        assert lines[0].content == "Simple line"
        assert lines[1].content == "Another line"
        assert lines[2].content == "Third line"
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_empty_and_whitespace_lines():
    """Test handling of empty and whitespace-only lines."""
    parser = TextParser()
    content = """First line

  
Second line
    
Last line"""
    
    tmp_path = Path("test_file.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 3  # Empty/whitespace lines should be skipped
        
        assert lines[0].content == "First line"
        assert lines[1].content == "Second line"
        assert lines[2].content == "Last line"
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_special_character_handling():
    """Test handling of special characters and formatting."""
    parser = TextParser()
    content = """Line with {braces}
Line with 'apostrophes'
Line with multiple    spaces
Line with Greek: ἄνθρωπος"""
    
    tmp_path = Path("test_file.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 4
        
        # Braces should be removed
        assert lines[0].content == "Line with braces"
        
        # Apostrophes should be normalized
        assert "'" not in lines[1].content
        assert "ʼ" in lines[1].content
        
        # Multiple spaces should be normalized
        assert "    " not in lines[2].content
        assert lines[2].content == "Line with multiple spaces"
        
        # Greek characters should be preserved
        assert "ἄνθρωπος" in lines[3].content
    finally:
        tmp_path.unlink()
