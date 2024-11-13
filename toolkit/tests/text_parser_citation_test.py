"""Test cases for citation parsing and line numbering functionality."""

import pytest
from pathlib import Path
from toolkit.parsers.text import TextParser, TextLine

@pytest.fixture
def text_parser():
    """Create a TextParser instance for testing."""
    return TextParser()

@pytest.mark.asyncio
async def test_basic_citation_line_numbering():
    """Test basic line numbering with citations."""
    parser = TextParser()
    content = """.1.1 First line
.1.2 Second line
.1.3 Third line"""
    
    tmp_path = Path("test_file.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 3
        
        # Line numbers should match citation line numbers
        assert lines[0].line_number == 1
        assert lines[1].line_number == 2
        assert lines[2].line_number == 3
        
        # Check chapter numbers
        for line in lines:
            assert line.citation.chapter == "1"
            assert not line.is_title
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_chapter_transitions():
    """Test line numbering across chapter transitions."""
    parser = TextParser()
    content = """.1.1 Chapter 1, line 1
.1.2 Chapter 1, line 2
.2.1 Chapter 2, line 1
.2.2 Chapter 2, line 2"""
    
    tmp_path = Path("test_file.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 4
        
        # Chapter 1 lines
        assert lines[0].citation.chapter == "1"
        assert lines[0].line_number == 1
        assert lines[1].citation.chapter == "1"
        assert lines[1].line_number == 2
        
        # Chapter 2 lines (line numbers should reset)
        assert lines[2].citation.chapter == "2"
        assert lines[2].line_number == 1
        assert lines[3].citation.chapter == "2"
        assert lines[3].line_number == 2
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_title_and_content_mixing():
    """Test line numbering with mixed title and content lines."""
    parser = TextParser()
    content = """[0627][010][][] Header
.t.1 First Title
.1.1 Content line one
.t.2 Second Title
.1.2 Content line two"""
    
    tmp_path = Path("test_file.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 5
        
        # Header (no line number)
        assert lines[0].line_number is None
        assert not lines[0].is_title
        
        # First title
        assert lines[1].line_number is None
        assert lines[1].title_number == 1
        assert lines[1].is_title
        
        # First content line
        assert lines[2].line_number == 1
        assert not lines[2].is_title
        
        # Second title
        assert lines[3].line_number is None
        assert lines[3].title_number == 2
        assert lines[3].is_title
        
        # Second content line
        assert lines[4].line_number == 2
        assert not lines[4].is_title
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_citation_inheritance():
    """Test line number inheritance for lines without explicit citations."""
    parser = TextParser()
    content = """.1.5 Line with citation
Continuation line one
Continuation line two
.1.6 Next citation line"""
    
    tmp_path = Path("test_file.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 4
        
        # Line with explicit citation
        assert lines[0].line_number == 5
        assert lines[0].citation.chapter == "1"
        
        # Continuation lines inherit citation
        assert lines[1].line_number == 5
        assert lines[1].citation.chapter == "1"
        assert lines[2].line_number == 5
        assert lines[2].citation.chapter == "1"
        
        # New citation line
        assert lines[3].line_number == 6
        assert lines[3].citation.chapter == "1"
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_complex_citation_patterns():
    """Test line numbering with complex citation patterns."""
    parser = TextParser()
    content = """[0627][010][][] Work header
.t.1 {ΠΕΡΙ ΑΡΘΡΩΝ.}
.1 Chapter heading
.1.10 Numbered line
.1.11.1 Line with section
.1.12.1.1 Line with subsection
Continuation line
.t.2.1 Sectioned title"""
    
    tmp_path = Path("test_file.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 8
        
        # Work header (no line number)
        assert lines[0].line_number is None
        assert lines[0].citation.author_id == "0627"
        
        # Title
        assert lines[1].line_number is None
        assert lines[1].title_number == 1
        assert lines[1].is_title
        
        # Chapter heading (no line number)
        assert lines[2].line_number is None
        assert lines[2].citation.chapter == "1"
        
        # Numbered line
        assert lines[3].line_number == 10
        assert lines[3].citation.chapter == "1"
        
        # Line with section
        assert lines[4].line_number == 11
        assert lines[4].citation.section == "1"
        
        # Line with subsection
        assert lines[5].line_number == 12
        assert lines[5].citation.subsection == "1"
        
        # Continuation line
        assert lines[6].line_number == 12
        assert lines[6].citation.subsection == "1"
        
        # Sectioned title
        assert lines[7].line_number is None
        assert lines[7].title_number == 2
        assert lines[7].citation.section == "1"
        assert lines[7].is_title
    finally:
        tmp_path.unlink()

@pytest.mark.asyncio
async def test_tlg_reference_handling():
    """Test line numbering with TLG references."""
    parser = TextParser()
    content = """[0627][010][][] First reference
[0627][010][][] Second reference
[0627][010][][].1.1 First line
[0627][010][][].1.2 Second line"""
    
    tmp_path = Path("test_file.txt")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    try:
        lines = await parser.parse_file(tmp_path)
        assert len(lines) == 4
        
        # References without line numbers
        assert lines[0].line_number is None
        assert lines[0].citation.author_id == "0627"
        assert lines[1].line_number is None
        assert lines[1].citation.author_id == "0627"
        
        # Lines with numbers
        assert lines[2].line_number == 1
        assert lines[2].citation.author_id == "0627"
        assert lines[2].citation.chapter == "1"
        
        assert lines[3].line_number == 2
        assert lines[3].citation.author_id == "0627"
        assert lines[3].citation.chapter == "1"
    finally:
        tmp_path.unlink()
