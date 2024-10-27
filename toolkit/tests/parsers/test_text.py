"""
Tests for the text parser module.

Tests text extraction, cleaning, and integration with CitationParser.
"""

import pytest
from pathlib import Path
import tempfile
from toolkit.parsers.text import TextParser, TextLine
from toolkit.parsers.exceptions import TextExtractionError, EncodingError

@pytest.fixture
def text_parser():
    """Create a TextParser instance for testing."""
    return TextParser()

@pytest.fixture
def sample_text_file():
    """Create a temporary file with sample text content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] First line of text.
128.32.5 Second line with volume reference.
Just a regular line.
Line with special characters: ᾿ ' ʼ
[0057][001][2][1] New section starts here.""")
        return Path(f.name)

@pytest.fixture
def greek_text_file():
    """Create a temporary file with Greek text content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] τὸ δὲ σῶμα τοῦ ἀνθρώπου ἔχει ἐν ἑωυτῷ αἷμα
128.32.5 καὶ φλέγμα καὶ χολὴν ξανθήν τε καὶ μέλαιναν""")
        return Path(f.name)

async def test_basic_text_parsing(text_parser, sample_text_file):
    """Test basic text parsing functionality."""
    lines = await text_parser.parse_file(sample_text_file)
    
    assert len(lines) > 0
    assert isinstance(lines[0], TextLine)
    assert "First line of text" in lines[0].content
    assert lines[0].citation is not None
    assert lines[0].citation.author_id == "0057"

async def test_line_with_volume_reference(text_parser, sample_text_file):
    """Test parsing lines with volume.chapter.line references."""
    lines = await text_parser.parse_file(sample_text_file)
    
    # Find the line with volume reference
    volume_line = next(line for line in lines if "Second line" in line.content)
    assert volume_line.citation is not None
    assert volume_line.citation.volume == "128"
    assert volume_line.citation.chapter == "32"
    assert volume_line.citation.line == "5"

async def test_text_cleaning(text_parser, sample_text_file):
    """Test text cleaning functionality."""
    lines = await text_parser.parse_file(sample_text_file)
    
    # Find the line with special characters
    special_line = next(line for line in lines if "special characters" in line.content)
    assert "ʼ" in special_line.content  # Should be normalized apostrophe
    assert "᾿" not in special_line.content  # Should be replaced
    assert "'" not in special_line.content  # Should be replaced

async def test_greek_text_parsing(text_parser, greek_text_file):
    """Test parsing of Greek text."""
    lines = await text_parser.parse_file(greek_text_file)
    
    assert len(lines) > 0
    assert "τὸ" in lines[0].content
    assert "αἷμα" in lines[0].content
    assert lines[0].citation is not None
    assert lines[0].citation.author_id == "0057"

async def test_file_not_found(text_parser):
    """Test handling of non-existent files."""
    with pytest.raises(TextExtractionError):
        await text_parser.parse_file(Path("nonexistent_file.txt"))

async def test_citation_continuity(text_parser, sample_text_file):
    """Test that citations carry over to subsequent lines until new citation."""
    lines = await text_parser.parse_file(sample_text_file)
    
    # Find the line after first citation
    regular_line = next(line for line in lines if "regular line" in line.content)
    # Should inherit previous citation
    assert regular_line.citation is not None
    assert regular_line.citation.author_id == "0057"

async def test_multiple_citations(text_parser):
    """Test handling of multiple citations in text."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] First citation
[0058][002][1][1] Second citation
Regular line
[0059][003][1][1] Third citation""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    assert len(lines) >= 3
    assert lines[0].citation.author_id == "0057"
    assert lines[1].citation.author_id == "0058"
    assert lines[3].citation.author_id == "0059"

async def test_empty_file(text_parser):
    """Test handling of empty files."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    assert len(lines) == 0

async def test_whitespace_handling(text_parser):
    """Test handling of various whitespace scenarios."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2]    Extra spaces here
    Indented line
Line with    multiple    spaces
""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    assert "Extra spaces here" in lines[0].content
    assert "Indented line" in lines[1].content
    assert "Line with multiple spaces" in lines[2].content
    # Check that extra spaces are normalized
    assert "    " not in lines[2].content

async def test_hyphenated_words(text_parser):
    """Test handling of hyphenated words across lines."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] This is a hy-
phenated word.
Regular line.""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    assert len(lines) == 2
    assert "hyphenated" in lines[0].content
    assert lines[0].citation.author_id == "0057"

async def test_mixed_citations(text_parser):
    """Test handling of mixed citation formats in same file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] TLG reference
128.32.5 Volume reference
.t.1 Title reference
Regular line""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    # Check TLG reference
    assert lines[0].citation.author_id == "0057"
    
    # Check volume reference
    assert lines[1].citation.volume == "128"
    assert lines[1].citation.chapter == "32"
    
    # Check title reference
    assert lines[2].citation.title_number == "1"

async def test_special_characters(text_parser):
    """Test handling of special characters and symbols."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] Line with · middle dot
Line with Greek: καὶ τὸ μὲν
Line with various apostrophes: ' ʼ ᾿ ᾽""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    # Check middle dot preservation
    assert "·" in lines[0].content
    
    # Check Greek character preservation
    assert "καὶ" in lines[1].content
    
    # Check apostrophe normalization
    assert "ʼ" in lines[2].content
    assert "᾿" not in lines[2].content
    assert "᾽" not in lines[2].content

async def test_citation_inheritance(text_parser):
    """Test that lines inherit citations correctly until new citation."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] First section
Inherited line 1
Inherited line 2
[0058][002][1][1] New section
Inherited line 3""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    # Check first section inheritance
    assert lines[0].citation.author_id == "0057"
    assert lines[1].citation.author_id == "0057"
    assert lines[2].citation.author_id == "0057"
    
    # Check new section inheritance
    assert lines[3].citation.author_id == "0058"
    assert lines[4].citation.author_id == "0058"

async def test_encoding_fallback(text_parser):
    """Test encoding fallback mechanism."""
    # Create a file with latin-1 encoding
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        content = "[0057][001][1][2] Latin-1 encoded text".encode('latin-1')
        f.write(content)
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    assert len(lines) > 0
    assert "Latin-1 encoded text" in lines[0].content
    assert lines[0].citation.author_id == "0057"

async def test_invalid_encoding(text_parser):
    """Test handling of invalid encoding."""
    # Create a file with invalid UTF-8
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        f.write(b'\xFF\xFE Invalid UTF-8 sequence')
        temp_path = Path(f.name)
    
    with pytest.raises(EncodingError):
        await text_parser.parse_file(temp_path)

async def test_line_continuation_markers(text_parser):
    """Test handling of line continuation markers."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] This line con-
tinues here.
[0058][002][1][1] Normal line.""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    # Should combine the continued line
    assert len(lines) == 2
    assert "continues" in lines[0].content
    assert lines[0].citation.author_id == "0057"
    assert lines[1].citation.author_id == "0058"

async def test_complex_citation_patterns(text_parser):
    """Test handling of complex citation patterns."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] First citation
.a.123 Second citation type
128.32.5 Third citation type
.t.1 Fourth citation type""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    assert lines[0].citation.author_id == "0057"
    assert lines[1].citation.volume == "a"
    assert lines[1].citation.line == "123"
    assert lines[2].citation.volume == "128"
    assert lines[2].citation.chapter == "32"
    assert lines[2].citation.line == "5"
    assert lines[3].citation.title_number == "1"

async def test_error_handling(text_parser):
    """Test various error handling scenarios."""
    # Test invalid file path
    with pytest.raises(TextExtractionError):
        await text_parser.parse_file("nonexistent/path/file.txt")
    
    # Test invalid encoding
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        f.write(b'\xFF\xFE\xFF\xFE')  # Invalid UTF-8 and Latin-1
        temp_path = Path(f.name)
    
    with pytest.raises(EncodingError):
        await text_parser.parse_file(temp_path)

async def test_special_characters_preservation(text_parser):
    """Test preservation of important special characters."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] Line with middle dot · here
Line with Greek letters: ἄνθρωπος
Line with brackets: {remove} [keep] {remove}""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    assert "·" in lines[0].content  # Middle dot preserved
    assert "ἄνθρωπος" in lines[1].content  # Greek letters preserved
    assert "[keep]" in lines[2].content  # Square brackets preserved
    assert "{" not in lines[2].content  # Curly braces removed
    assert "}" not in lines[2].content  # Curly braces removed

async def test_multiple_line_continuations(text_parser):
    """Test handling of multiple line continuations."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] This is a very lo-
ng word that con-
tinues here.""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    assert len(lines) == 1
    assert "long" in lines[0].content
    assert "continues" in lines[0].content
    assert "-" not in lines[0].content  # Hyphens should be removed

async def test_mixed_content(text_parser):
    """Test handling of mixed content types in same file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] Greek: τὸ σῶμα
128.32.5 Latin: corpus
.t.1 Special chars: · ᾿ ' ʼ
Regular line with [brackets] and {braces}""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    assert "τὸ σῶμα" in lines[0].content
    assert "corpus" in lines[1].content
    assert "·" in lines[2].content
    assert "ʼ" in lines[2].content  # Normalized apostrophe
    assert "[brackets]" in lines[3].content
    assert "{" not in lines[3].content

async def test_empty_lines_handling(text_parser):
    """Test handling of empty and whitespace-only lines."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057][001][1][2] First line

   
[0058][002][1][1] After empty lines""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    assert len(lines) == 2  # Empty lines should be skipped
    assert lines[0].citation.author_id == "0057"
    assert lines[1].citation.author_id == "0058"

async def test_citation_at_end(text_parser):
    """Test handling of citations at the end of lines."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""Some text here [0057][001][1][2]
More text 128.32.5""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    assert len(lines) == 2
    assert lines[0].citation is not None
    assert lines[0].citation.author_id == "0057"
    assert lines[1].citation is not None
    assert lines[1].citation.volume == "128"

async def test_large_file_handling(text_parser):
    """Test handling of larger files."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        # Create a larger file with repeated content
        content = "[0057][001][1][2] Base line\n" * 1000
        f.write(content)
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    assert len(lines) == 1000
    assert all(line.citation.author_id == "0057" for line in lines)
    assert all("Base line" in line.content for line in lines)

async def test_malformed_citations(text_parser):
    """Test handling of malformed citations."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("""[0057[001][1][2] Malformed first bracket
[0057][001[1][2] Malformed second bracket
[0057][001][1[2] Malformed third bracket
128.32 Incomplete volume reference
.t. Incomplete title reference""")
        temp_path = Path(f.name)
    
    lines = await text_parser.parse_file(temp_path)
    
    # Should treat malformed citations as regular text
    assert "[0057[001][1][2]" in lines[0].content
    assert "128.32" in lines[3].content
    assert ".t." in lines[4].content
