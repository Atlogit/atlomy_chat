"""
Tests for sentence parsing functionality.
"""

import pytest
from toolkit.parsers.sentence import SentenceParser
from toolkit.parsers.text import TextLine

def test_normalize_line():
    """Test line normalization."""
    parser = SentenceParser()
    
    # Test line marker removal
    text = "7.475.t3. ΒΙΒΛΙΟΝ"
    normalized, start_pos = parser.normalize_line(text)
    assert normalized == "ΒΙΒΛΙΟΝ"
    assert start_pos == 10  # Length of "7.475.t3. "
    
    # Test brace removal
    text = "{ΓΑΛΗΝΟΥ ΠΡΟΣ ΤΟΥΣ}"
    normalized, start_pos = parser.normalize_line(text)
    assert normalized == "ΓΑΛΗΝΟΥ ΠΡΟΣ ΤΟΥΣ"
    assert start_pos == 0
    
    # Test special character removal
    text = "Ἀμφημερινός                    κδʹ"
    normalized, start_pos = parser.normalize_line(text)
    assert normalized == "Ἀμφημερινός"
    assert start_pos == 0
    
    # Test multiple spaces
    text = "ΓΑΛΗΝΟΥ    ΠΡΟΣ    ΤΟΥΣ"
    normalized, start_pos = parser.normalize_line(text)
    assert normalized == "ΓΑΛΗΝΟΥ ΠΡΟΣ ΤΟΥΣ"
    assert start_pos == 0

def test_hyphenation():
    """Test handling of hyphenated words."""
    parser = SentenceParser()
    
    # Test basic hyphenation
    current = ["This is a sen-"]
    parser.join_hyphenated_words(current, "tence")
    assert current == ["This is a sentence"]
    
    # Test with spaces
    current = ["First sen-"]
    parser.join_hyphenated_words(current, " tence")
    assert current == ["First sentence"]
    
    # Test without hyphen
    current = ["Complete"]
    parser.join_hyphenated_words(current, "word")
    assert current == ["Complete", "word"]

def test_sentence_parsing():
    """Test sentence parsing with hyphenation."""
    parser = SentenceParser()
    
    lines = [
        TextLine(content="This is a sen-"),
        TextLine(content="tence that spans lines."),
        TextLine(content="This is another· And this continues.")
    ]
    
    sentences = parser.parse_lines(lines)
    print("\nActual sentences:")  # Debug output
    for i, s in enumerate(sentences):
        print(f"{i+1}: {s.content}")
        
    assert len(sentences) == 3
    assert sentences[0].content == "This is a sentence that spans lines."
    assert sentences[1].content == "This is another·"
    assert sentences[2].content == "And this continues."
    
    # Check source line references
    assert len(sentences[0].source_lines) == 2  # Spans two lines
    assert len(sentences[1].source_lines) == 1
    assert len(sentences[2].source_lines) == 1

def test_greek_text_parsing():
    """Test parsing of Greek text with special formatting."""
    parser = SentenceParser()
    
    lines = [
        TextLine(content="7.475.t1. {ΓΑΛΗΝΟΥ ΠΡΟΣ ΤΟΥΣ ΠΕΡΙ ΤΥΠΩΝ.}"),
        TextLine(content="ΤΥΠΟΙ ΩΡΑΣ."),
        TextLine(content="Ἀμφημερινός                    κδʹ"),
        TextLine(content="Τριταῖος                       μηʹ.")
    ]
    
    sentences = parser.parse_lines(lines)
    assert len(sentences) == 3
    assert sentences[0].content == "ΓΑΛΗΝΟΥ ΠΡΟΣ ΤΟΥΣ ΠΕΡΙ ΤΥΠΩΝ."
    assert sentences[1].content == "ΤΥΠΟΙ ΩΡΑΣ."
    assert "Ἀμφημερινός" in sentences[2].content
    assert "Τριταῖος" in sentences[2].content

def test_mixed_content():
    """Test parsing of mixed regular and Greek text."""
    parser = SentenceParser()
    
    lines = [
        TextLine(content="Regular sentence."),
        TextLine(content="7.475.t1. {Greek title.}"),
        TextLine(content="Mixed sen-"),
        TextLine(content="tence with Ἀμφημερινός.")
    ]
    
    sentences = parser.parse_lines(lines)
    assert len(sentences) == 3
    assert sentences[0].content == "Regular sentence."
    assert sentences[1].content == "Greek title."
    assert sentences[2].content == "Mixed sentence with Ἀμφημερινός."

def test_citation_tracking():
    """Test citation tracking in sentences."""
    parser = SentenceParser()
    
    class MockCitation:
        def __init__(self, ref):
            self.ref = ref
        def __str__(self):
            return self.ref
    
    # Create lines with citations
    lines = [
        TextLine(content="First line.", citation=MockCitation("ref1")),
        TextLine(content="Second line.", citation=MockCitation("ref2"))
    ]
    
    sentences = parser.parse_lines(lines)
    citations = parser.get_sentence_citations(sentences[0])
    assert len(citations) == 1
    assert str(citations[0]) == "ref1"

def test_empty_lines():
    """Test handling of empty or whitespace-only lines."""
    parser = SentenceParser()
    
    lines = [
        TextLine(content=""),
        TextLine(content="   "),
        TextLine(content="Valid line."),
        TextLine(content="\n\t")
    ]
    
    sentences = parser.parse_lines(lines)
    assert len(sentences) == 1
    assert sentences[0].content == "Valid line."

def test_sentence_endings():
    """Test handling of different sentence endings."""
    parser = SentenceParser()
    
    lines = [
        TextLine(content="Period ending."),
        TextLine(content="Middle dot ending·"),
        TextLine(content="Mixed endings. And More.")
    ]
    
    sentences = parser.parse_lines(lines)
    print("\nActual sentence endings:")  # Debug output
    for i, s in enumerate(sentences):
        print(f"{i+1}: {s.content}")
        
    assert len(sentences) == 4
    assert sentences[0].content == "Period ending."
    assert sentences[1].content == "Middle dot ending·"
    assert sentences[2].content == "Mixed endings."
    assert sentences[3].content == "And More."
