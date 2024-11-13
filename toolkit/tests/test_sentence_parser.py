"""Test cases for sentence parsing functionality."""

import pytest
from toolkit.parsers.sentence import SentenceParser
from toolkit.parsers.text import TextLine
from toolkit.parsers.citation import Citation

def create_text_line(content: str, line_number: int, is_title: bool = False, citation: Citation = None) -> TextLine:
    """Helper to create TextLine objects for testing."""
    line = TextLine(content=content, is_title=is_title, citation=citation)
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
    citation = Citation(author_id="0627", work_id="010", chapter="51")
    lines = [
        create_text_line("ἐπί τε γὰρ τὸ ἀπὸ τοῦ ἰσχίου πεφυκὸς ὀστέον,", 6, citation=citation),
        create_text_line("τὸ ἄνω φερόμενον πρὸς τὸν κτένα, ἐπὶ τοῦτο ἡ ἐπίβασις τῆς κε-", 7, citation=citation),
        create_text_line("φαλῆς τοῦ μηροῦ γίνεται, καὶ ὁ αὐχὴν τοῦ ἄρθρου ἐπὶ τῆς", 8, citation=citation),
        create_text_line("κοτύλης ὀχέεται.", 9, citation=citation)
    ]
    sentences = parser.parse_lines(lines)
    
    assert len(sentences) == 1
    assert [l.line_number for l in sentences[0].source_lines] == [6, 7, 8, 9]
    assert str(sentences[0].citation) == "[0627][010].51"

def test_real_greek_example_2():
    """Test with real Greek text example from De articulis Chapter 55."""
    parser = SentenceParser()
    citation = Citation(author_id="0627", work_id="010", chapter="55")
    lines = [
        create_text_line("Ὀχέειν δὲ δύναται τὸ σῶμα τὸ σιναρὸν σκέλος τούτοισι πολλῷ", 5, citation=citation),
        create_text_line("μᾶλλον, ἢ οἷσιν ἂν ἐς τὸ ἔσω μέρος ἐκπεπτώκῃ, ἅμα μὲν, ὅτι ἡ", 6, citation=citation),
        create_text_line("κεφαλὴ τοῦ μηροῦ, καὶ ὁ αὐχὴν τοῦ ἄρθρου πλάγιος φύσει πεφυκὼς,", 7, citation=citation),
        create_text_line("ὑπὸ συχνῷ μέρεϊ τοῦ ἰσχίου τὴν ὑπόστασιν πεποίηται, ἅμα δὲ, ὅτι", 8, citation=citation),
        create_text_line("ἄκρος ὁ ποὺς οὐκ ἐς τὸ ἔξω μέρος ἀναγκάζεται ἐκκεκλίσθαι, ἀλλ'", 9, citation=citation),
        create_text_line("ἐγγύς ἐστι τῆς ἰθυωρίης τῆς κατὰ τὸ σῶμα, καὶ τείνει καὶ", 10, citation=citation),
        create_text_line("ἐσωτέρω.", 11, citation=citation)
    ]
    sentences = parser.parse_lines(lines)
    
    assert len(sentences) == 1
    assert [l.line_number for l in sentences[0].source_lines] == [5, 6, 7, 8, 9, 10, 11]
    assert str(sentences[0].citation) == "[0627][010].55"

def test_multiple_complete_sentences_in_line():
    """Test handling multiple complete sentences in a single line."""
    parser = SentenceParser()
    line = create_text_line("Ἀτὰρ οὐδὲ ἐς τὸ ἔμπροσθεν οὐδέπω ὄπωπα, ὅ τι ἔδοξέ μοι ὠλισθηκέναι· Τοῖσι μέντοι ἰητροῖσι δοκέει κάρτα ἐς τοὔμπροσθεν ὀλισθάνειν.", 5)
    sentences = parser.parse_lines([line])
    
    assert len(sentences) == 2
    assert sentences[0].content == "Ἀτὰρ οὐδὲ ἐς τὸ ἔμπροσθεν οὐδέπω ὄπωπα, ὅ τι ἔδοξέ μοι ὠλισθηκέναι·"
    assert sentences[1].content == "Τοῖσι μέντοι ἰητροῖσι δοκέει κάρτα ἐς τοὔμπροσθεν ὀλισθάνειν."
    assert all(s.source_lines == [line] for s in sentences)
    assert all(s.source_lines[0].line_number == 5 for s in sentences)

def test_title_line_handling():
    """Test handling of title lines with regular text lines."""
    parser = SentenceParser()
    citation = Citation(title_number="1")
    lines = [
        create_text_line(".t.1 {ΠΕΡΙ ΑΡΘΡΩΝ.}", 1, is_title=True, citation=citation),
        create_text_line("Ὤμου δὲ ἄρθρον ἕνα τρόπον οἶδα ὀλισθάνον, τὸν ἐς τὴν μα-", 2),
        create_text_line("σχάλην· ἄνω δὲ οὐδέποτε εἶδον, οὐδὲ ἐς τὸ ἔξω·", 3)
    ]
    sentences = parser.parse_lines(lines)
    
    # Title line should not be included in sentence parsing
    assert len(sentences) == 2
    # First sentence should start from line 2
    assert sentences[0].source_lines[0].line_number == 2
    # Second sentence should include parts of lines 2 and 3
    assert [l.line_number for l in sentences[1].source_lines] == [2, 3]
    # Title citation should be formatted correctly
    assert str(lines[0].citation) == "t.1"

def test_citation_handling():
    """Test handling of citation text in lines."""
    parser = SentenceParser()
    citation = Citation(author_id="0627", work_id="010", chapter="51", line="1")
    lines = [
        create_text_line(".51.1 ἐπί τε γὰρ τὸ ἀπὸ τοῦ ἰσχίου πεφυκὸς ὀστέον.", 1, citation=citation),
        create_text_line(".51.2 Ἔξωθέν τε αὖ ὁ γλουτὸς κοῖλος φαίνεται.", 2, citation=citation)
    ]
    sentences = parser.parse_lines(lines)
    
    assert len(sentences) == 2
    # Citation text should be removed
    assert sentences[0].content == "ἐπί τε γὰρ τὸ ἀπὸ τοῦ ἰσχίου πεφυκὸς ὀστέον."
    assert sentences[1].content == "Ἔξωθέν τε αὖ ὁ γλουτὸς κοῖλος φαίνεται."
    # Citations should be preserved in sentence objects
    assert sentences[0].citation == citation
    assert str(sentences[0].citation) == "[0627][010].51.1"
    assert sentences[1].citation == citation
    assert str(sentences[1].citation) == "[0627][010].51.1"

def test_citation_with_greek_text():
    """Test handling of citations mixed with Greek text."""
    parser = SentenceParser()
    citation = Citation(author_id="0627", work_id="010", chapter="87", line="1")
    lines = [
        create_text_line(".87.1 Οἷσι δ' ἂν ἐκβῇ ὁ ποὺς ἢ αὐτὸς, ἢ ξὺν τῇ ἐπιφύσει,", 1, citation=citation),
        create_text_line(".87.2 ἐκπίπτει μὲν μᾶλλον ἐς τὸ ἔσω.", 2, citation=citation)
    ]
    sentences = parser.parse_lines(lines)
    
    assert len(sentences) == 2
    # Citation text should be removed but Greek text preserved
    assert sentences[0].content == "Οἷσι δ' ἂν ἐκβῇ ὁ ποὺς ἢ αὐτὸς, ἢ ξὺν τῇ ἐπιφύσει,"
    assert sentences[1].content == "ἐκπίπτει μὲν μᾶλλον ἐς τὸ ἔσω."
    # Citations should be preserved in sentence objects
    assert sentences[0].citation == citation
    assert str(sentences[0].citation) == "[0627][010].87.1"
    assert sentences[1].citation == citation
    assert str(sentences[1].citation) == "[0627][010].87.1"
