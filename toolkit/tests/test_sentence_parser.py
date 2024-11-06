"""Test cases for sentence parsing functionality."""

import pytest
from toolkit.parsers.sentence import SentenceParser
from toolkit.parsers.text import TextLine

def create_text_line(content: str, line_number: int) -> TextLine:
    """Helper to create TextLine objects for testing."""
    line = TextLine(content=content)
    line.line_number = line_number  # Set the actual line number
    return line

def test_single_line_sentence():
    """Test parsing a single line containing one complete sentence."""
    parser = SentenceParser()
    line = create_text_line("This is a test sentence.", 1)
    sentences = parser.parse_lines([line])
    
    assert len(sentences) == 1
    assert sentences[0].content == "This is a test sentence."
    assert sentences[0].source_lines == [line]
    assert [l.line_number for l in sentences[0].source_lines] == [1]

def test_multiple_sentences_single_line():
    """Test parsing multiple sentences within a single line."""
    parser = SentenceParser()
    line = create_text_line("First sentence· Second sentence.", 1)
    sentences = parser.parse_lines([line])
    
    assert len(sentences) == 2
    assert sentences[0].content == "First sentence·"
    assert sentences[1].content == "Second sentence."
    assert all(s.source_lines == [line] for s in sentences)
    assert all(s.source_lines[0].line_number == 1 for s in sentences)

def test_sentence_across_lines():
    """Test parsing a sentence that spans multiple lines."""
    parser = SentenceParser()
    lines = [
        create_text_line("This sentence spans", 1),
        create_text_line("multiple lines and", 2),
        create_text_line("ends here.", 3)
    ]
    sentences = parser.parse_lines(lines)
    
    assert len(sentences) == 1
    assert sentences[0].content == "This sentence spans multiple lines and ends here."
    assert sentences[0].source_lines == lines
    assert [l.line_number for l in sentences[0].source_lines] == [1, 2, 3]

def test_hyphenated_word_across_lines():
    """Test handling of hyphenated words across line boundaries."""
    parser = SentenceParser()
    lines = [
        create_text_line("This sen-", 1),
        create_text_line("tence has hyphenation.", 2)
    ]
    sentences = parser.parse_lines(lines)
    
    assert len(sentences) == 1
    assert sentences[0].content == "This sentence has hyphenation."
    assert sentences[0].source_lines == lines
    assert [l.line_number for l in sentences[0].source_lines] == [1, 2]

def test_mixed_sentence_patterns():
    """Test handling mixed patterns of sentences and line breaks."""
    parser = SentenceParser()
    lines = [
        create_text_line("First sentence· Second sen-", 1),
        create_text_line("tence spans lines.", 2),
        create_text_line("Third sentence.", 3)
    ]
    sentences = parser.parse_lines(lines)
    
    assert len(sentences) == 3
    assert sentences[0].content == "First sentence·"
    assert sentences[1].content == "Second sentence spans lines."
    assert sentences[2].content == "Third sentence."
    assert sentences[0].source_lines == [lines[0]]
    assert sentences[1].source_lines == lines[:2]
    assert sentences[2].source_lines == [lines[2]]
    assert [l.line_number for l in sentences[0].source_lines] == [1]
    assert [l.line_number for l in sentences[1].source_lines] == [1, 2]
    assert [l.line_number for l in sentences[2].source_lines] == [3]

def test_greek_text_patterns():
    """Test handling of ancient Greek text patterns."""
    parser = SentenceParser()
    lines = [
        create_text_line("τῶν ἄλλων πλειστάκις· ἐς δὲ τὸ", 1),
        create_text_line("ὄπισθεν καὶ τὸ ἔμπροσθεν ἐκπίπτει μὲν,", 2),
        create_text_line("ὀλιγάκις δέ·", 3)
    ]
    sentences = parser.parse_lines(lines)
    
    assert len(sentences) == 2
    assert sentences[0].content == "τῶν ἄλλων πλειστάκις·"
    assert sentences[1].content == "ἐς δὲ τὸ ὄπισθεν καὶ τὸ ἔμπροσθεν ἐκπίπτει μὲν, ὀλιγάκις δέ·"
    assert sentences[0].source_lines == [lines[0]]
    assert sentences[1].source_lines == lines
    assert [l.line_number for l in sentences[0].source_lines] == [1]
    assert [l.line_number for l in sentences[1].source_lines] == [1, 2, 3]

def test_real_greek_example_1():
    """Test with real Greek text example from De articulis Chapter 51."""
    parser = SentenceParser()
    lines = [
        create_text_line("ἐπί τε γὰρ τὸ ἀπὸ τοῦ ἰσχίου πεφυκὸς ὀστέον,", 6),
        create_text_line("τὸ ἄνω φερόμενον πρὸς τὸν κτένα, ἐπὶ τοῦτο ἡ ἐπίβασις τῆς κε-", 7),
        create_text_line("φαλῆς τοῦ μηροῦ γίνεται, καὶ ὁ αὐχὴν τοῦ ἄρθρου ἐπὶ τῆς", 8),
        create_text_line("κοτύλης ὀχέεται.", 9)
    ]
    sentences = parser.parse_lines(lines)
    
    assert len(sentences) == 1
    assert [l.line_number for l in sentences[0].source_lines] == [6, 7, 8, 9]

def test_real_greek_example_2():
    """Test with real Greek text example from De articulis Chapter 55."""
    parser = SentenceParser()
    lines = [
        create_text_line("Ὀχέειν δὲ δύναται τὸ σῶμα τὸ σιναρὸν σκέλος τούτοισι πολλῷ", 5),
        create_text_line("μᾶλλον, ἢ οἷσιν ἂν ἐς τὸ ἔσω μέρος ἐκπεπτώκῃ, ἅμα μὲν, ὅτι ἡ", 6),
        create_text_line("κεφαλὴ τοῦ μηροῦ, καὶ ὁ αὐχὴν τοῦ ἄρθρου πλάγιος φύσει πεφυκὼς,", 7),
        create_text_line("ὑπὸ συχνῷ μέρεϊ τοῦ ἰσχίου τὴν ὑπόστασιν πεποίηται, ἅμα δὲ, ὅτι", 8),
        create_text_line("ἄκρος ὁ ποὺς οὐκ ἐς τὸ ἔξω μέρος ἀναγκάζεται ἐκκεκλίσθαι, ἀλλ'", 9),
        create_text_line("ἐγγύς ἐστι τῆς ἰθυωρίης τῆς κατὰ τὸ σῶμα, καὶ τείνει καὶ", 10),
        create_text_line("ἐσωτέρω.", 11)
    ]
    sentences = parser.parse_lines(lines)
    
    assert len(sentences) == 1
    assert [l.line_number for l in sentences[0].source_lines] == [5, 6, 7, 8, 9, 10, 11]
