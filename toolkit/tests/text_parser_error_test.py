"""Test cases for error handling and edge cases in text parsing."""

import pytest
from pathlib import Path
from toolkit.parsers.text import TextParser, TextLine
from toolkit.parsers.exceptions import TextExtractionError, EncodingError

@pytest.fixture
def text_parser():
    """Create a TextParser instance for testing."""
    return TextParser()

@pytest.mark.asyncio
async def test_nonexistent_file():
    """Test handling of non-existent files."""
    parser = TextParser()
    
    with pytest.raises(FileNotFoundError):
        await parser.parse_file("nonexistent.txt")

@pytest.mark.asyncio
async def test_empty_file():
    """Test handling of empty files."""
    parser = TextParser()
    
    tmp_path = Path("empty.txt")
    tmp_path.touch()
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 0
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_whitespace_only_file():
    """Test handling of files containing only whitespace."""
    parser = TextParser()
    content = """
    
        
    """
    
    tmp_path = Path("whitespace.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 0
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_invalid_citation_format():
    """Test handling of invalid citation formats."""
    parser = TextParser()
    content = """.invalid.citation Text content
.1.invalid Second line
[invalid][citation][] Third line
.t.invalid.1 Invalid title"""
    
    tmp_path = Path("invalid.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 4
        
        # Invalid citations should result in lines with no citation info
        for line in lines:
            assert line.line_number is None
            assert not line.is_title
            assert line.title_number is None
            
        # Content should be preserved
        assert "Text content" in lines[0].content
        assert "Second line" in lines[1].content
        assert "Third line" in lines[2].content
        assert "Invalid title" in lines[3].content
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_mixed_encodings():
    """Test handling of mixed character encodings."""
    parser = TextParser()
    content = "Line with UTF-8: ἄνθρωπος\nLine with Latin-1: é è à"
    
    tmp_path = Path("mixed_encoding.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 2
        
        # Both UTF-8 and Latin-1 characters should be preserved
        assert "ἄνθρωπος" in lines[0].content
        assert "é è à" in lines[1].content
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_malformed_citations():
    """Test handling of malformed citation patterns."""
    parser = TextParser()
    content = """[0627[010][][] Mismatched brackets
[0627]]010[[][] Extra brackets
.1..2 Extra dots
.t1..2. Trailing dot
..1.2 Leading dots"""
    
    tmp_path = Path("malformed.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 5
        
        # Malformed citations should not crash the parser
        for line in lines:
            assert line.line_number is None  # No valid line numbers from malformed citations
            
        # Content should be preserved
        assert "Mismatched brackets" in lines[0].content
        assert "Extra brackets" in lines[1].content
        assert "Extra dots" in lines[2].content
        assert "Trailing dot" in lines[3].content
        assert "Leading dots" in lines[4].content
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_citation_edge_cases():
    """Test handling of edge cases in citation formats."""
    parser = TextParser()
    content = """.1. Dot without line number
.t. Title without number
. Single dot
... Multiple dots
.1.2.3.4.5 Too many numbers"""
    
    tmp_path = Path("edge_cases.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 5
        
        # Edge cases should be handled gracefully
        for line in lines:
            assert line.line_number is None  # Invalid citations should not produce line numbers
            
        # Content should be preserved
        assert "Dot without line number" in lines[0].content
        assert "Title without number" in lines[1].content
        assert "Single dot" in lines[2].content
        assert "Multiple dots" in lines[3].content
        assert "Too many numbers" in lines[4].content
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_special_characters_in_citations():
    """Test handling of special characters in citation patterns."""
    parser = TextParser()
    content = """[0627][010][α][β] Greek letters in citation
[0627][010][*][#] Special chars in citation
.1.α Greek letter as line
.t.# Special char as title"""
    
    tmp_path = Path("special_chars.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 4
        
        # Special characters in citations should not crash the parser
        for line in lines:
            assert line.line_number is None  # Invalid citations should not produce line numbers
            
        # Content should be preserved
        assert "Greek letters in citation" in lines[0].content
        assert "Special chars in citation" in lines[1].content
        assert "Greek letter as line" in lines[2].content
        assert "Special char as title" in lines[3].content
    finally:
        tmp_path.unlink()
