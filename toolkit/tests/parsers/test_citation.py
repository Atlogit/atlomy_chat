"""
Tests for the citation parser module.

Tests the parsing of various citation formats:
1. TLG references [author_id][work_id][division][subdivision]
2. Volume.chapter.line references
3. Title number references with various formats
4. Multi-line title references
5. Invalid citation formats
6. Standalone title parsing
"""

import pytest
from pathlib import Path
from toolkit.parsers.citation import CitationParser, Citation
from toolkit.parsers.exceptions import CitationError

@pytest.fixture
def citation_parser():
    """Create a CitationParser instance for testing."""
    config_path = Path(__file__).parent.parent.parent / "parsers" / "config" / "citation_config.json"
    return CitationParser(config_path)

def test_tlg_reference_parsing(citation_parser):
    """Test parsing of TLG reference format [author_id][work_id][division][subdivision]."""
    text = "[0057] [001] [1] [2]\nSome text here"
    remaining, citations = citation_parser.parse_citation(text)
    
    assert remaining == "Some text here"
    assert len(citations) == 1
    citation = citations[0]
    assert citation.author_id == "0057"
    assert citation.work_id == "001"
    assert citation.division == "1"
    assert citation.subdivision == "2"

def test_volume_chapter_line_parsing(citation_parser):
    """Test parsing of volume.chapter.line format."""
    text = "128.32.5 Some text here"
    remaining, citations = citation_parser.parse_citation(text)
    
    assert remaining == "Some text here"
    assert len(citations) == 1
    citation = citations[0]
    assert citation.volume == "128"
    assert citation.chapter == "32"
    assert citation.line == "5"

def test_chapter_line_parsing(citation_parser):
    """Test parsing of .chapter.line format."""
    text = ".a.123 Some text here"
    remaining, citations = citation_parser.parse_citation(text)
    
    assert remaining == "Some text here"
    assert len(citations) == 1
    citation = citations[0]
    assert citation.volume is None
    assert citation.chapter == "a"
    assert citation.line == "123"

def test_title_number_parsing(citation_parser):
    """Test parsing of title number formats."""
    test_cases = [
        ("t1 Some text here", "1", "Some text here"),
        ("t.1 Another text", "1", "Another text"),
        (".t.2 Yet another text", "2", "Yet another text")
    ]
    
    for text, expected_number, expected_remaining in test_cases:
        remaining, citations = citation_parser.parse_citation(text)
        
        assert remaining == expected_remaining
        assert len(citations) == 1
        citation = citations[0]
        assert citation.title_number == expected_number
        assert citation.volume is None
        assert citation.chapter is None
        assert citation.line is None

def test_multi_line_title_parsing(citation_parser):
    """Test parsing of multi-line title references."""
    text = "5.899.t1 {ΓΑΛΗΝΟΥ\n5.899.t2 ΠΕΡΙ ΤΟΥ ΔΙΑ ΤΗΣ ΣΜΙΚΡΑΣ ΣΦΑΙΡΑΣ ΓΥΜΝΑΣΙΟΥ}\n5.899.1 Πηλίκον μὲν ἀγαθόν ἐστιν, 〈ὦ Ἐπίγενες,〉 εἰς ὑγίειαν γυμ-"
    remaining, citations = citation_parser.parse_citation(text)
    
    assert len(citations) == 3
    assert citations[0].volume == "5"
    assert citations[0].chapter == "899"
    assert citations[0].title_number == "1"
    assert citations[1].volume == "5"
    assert citations[1].chapter == "899"
    assert citations[1].title_number == "2"
    assert citations[2].volume == "5"
    assert citations[2].chapter == "899"
    assert citations[2].line == "1"
    assert remaining == "{ΓΑΛΗΝΟΥ\nΠΕΡΙ ΤΟΥ ΔΙΑ ΤΗΣ ΣΜΙΚΡΑΣ ΣΦΑΙΡΑΣ ΓΥΜΝΑΣΙΟΥ}\nΠηλίκον μὲν ἀγαθόν ἐστιν, 〈ὦ Ἐπίγενες,〉 εἰς ὑγίειαν γυμ-"

def test_no_citation(citation_parser):
    """Test handling of text without citations."""
    text = "Just some regular text"
    remaining, citations = citation_parser.parse_citation(text)
    
    assert remaining == "Just some regular text"
    assert len(citations) == 0

def test_citation_formatting(citation_parser):
    """Test formatting citations back to string representation."""
    # TLG reference
    text = "[0057] [001] [1] [2]\nSome text"
    _, citations = citation_parser.parse_citation(text)
    assert str(citations[0]) == "[0057][001][1][2]"
    
    # Volume.chapter.line
    text = "128.32.5 Some text"
    _, citations = citation_parser.parse_citation(text)
    assert str(citations[0]) == "128.32.5"
    
    # Title reference
    text = "t1 Some text"
    _, citations = citation_parser.parse_citation(text)
    assert str(citations[0]) == "t1"

def test_invalid_citation(citation_parser):
    """Test handling of invalid citation formats."""
    invalid_texts = [
        "[invalid] Some text",
        "123.abc.xyz Some text",
        "t.invalid Some text",
        "[0057] [001] [invalid] [2] Some text"
    ]
    
    for text in invalid_texts:
        remaining, citations = citation_parser.parse_citation(text)
        assert remaining == text, f"Failed for text: {text}"
        assert len(citations) == 0, f"Expected no citations for invalid text: {text}"

def test_citation_with_metadata(citation_parser):
    """Test citation formatting with metadata."""
    text = "[0057] [001] [1] [2]\nSome text"
    _, citations = citation_parser.parse_citation(text)
    
    metadata = {
        "author_name": "Hippocrates",
        "work_name": "De Natura Hominis"
    }
    
    formatted = citation_parser.format_citation(citations[0], metadata)
    assert "Hippocrates" in formatted
    assert "De Natura Hominis" in formatted

def test_parse_standalone_title(citation_parser):
    """Test parsing of standalone title references."""
    test_cases = [
        ("t1 Some text", "1", "Some text"),
        ("t.1 Another text", "1", "Another text"),
        ("t12 Yet another text", "12", "Yet another text"),
        ("t1.2 And another", "1.2", "And another")
    ]
    
    for text, expected_number, expected_remaining in test_cases:
        remaining, citations = citation_parser.parse_standalone_title(text)
        
        assert remaining == expected_remaining
        assert len(citations) == 1
        citation = citations[0]
        assert citation.title_number == expected_number