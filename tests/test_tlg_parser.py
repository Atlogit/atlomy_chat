import unittest
import tempfile
import os
import shutil
import spacy
from src.data_parsing.tlg_parser import (
    remove_tlg_ref_tags,
    fix_words_that_carry_over_next_line,
    replace_citation_levels,
    split_text_into_sections,
    process_text_sections,
    process_tlg_file,
    create_data,
    spaCy_Model
)
from src.data_parsing.utils import (
    sentencizer,
    clean_text,
    create_text_tagging_object
)
from src.corpus_manager import CorpusManager

class TestTLGParser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Setting up TestTLGParser")
        cls.nlp = spacy.load(spaCy_Model)
        cls.nlp.get_pipe("spancat").cfg["threshold"] = 0.2
        cls.temp_dir = tempfile.mkdtemp()
        cls.corpus_path = os.path.join(cls.temp_dir, 'test_corpus')
        os.makedirs(cls.corpus_path, exist_ok=True)
        print("TestTLGParser setup complete")

    @classmethod
    def tearDownClass(cls):
        print("Tearing down TestTLGParser")
        shutil.rmtree(cls.temp_dir)
        print("TestTLGParser teardown complete")

    def setUp(self):
        self.corpus_manager = CorpusManager(self.corpus_path)

    def test_remove_tlg_ref_tags(self):
        print("Running test_remove_tlg_ref_tags")
        text = "Some text <tlg_ref>reference</tlg_ref> more text"
        result = remove_tlg_ref_tags(text)
        self.assertEqual(result, "Some text  more text")
        print("test_remove_tlg_ref_tags passed")

    def test_fix_words_that_carry_over_next_line(self):
        print("Running test_fix_words_that_carry_over_next_line")
        text = "word-<tlg_ref>reference</tlg_ref>continuation"
        result = fix_words_that_carry_over_next_line(text)
        self.assertEqual(result, "wordcontinuation<tlg_ref>reference</tlg_ref>")
        print("test_fix_words_that_carry_over_next_line passed")

    def test_replace_citation_levels(self):
        print("Running test_replace_citation_levels")
        text = "1.2.3"
        result = replace_citation_levels(text)
        self.assertEqual(result, "VOL(1)*VB(2)*L(3)")
        print("test_replace_citation_levels passed")

    def test_split_text_into_sections(self):
        print("Running test_split_text_into_sections")
        text = "[A] [B] [C] [D] Section 1 [A] [B] [C] [D] Section 2"
        result = split_text_into_sections(text)
        self.assertEqual(len(result), 4)
        print("test_split_text_into_sections passed")

    def test_process_text_sections(self):
        print("Running test_process_text_sections")
        sections = ["[A] [B] [C] [D]", "1.2.3 Some text", "[A] [B] [C] [D]", "4.5.6 More text"]
        result = process_text_sections(sections)
        self.assertIn("VOL(1)*VB(2)*L(3)", result)
        self.assertIn("VOL(4)*VB(5)*L(6)", result)
        print("test_process_text_sections passed")

    def test_sentencizer(self):
        print("Running test_sentencizer")
        text = "First sentence. Second sentence."
        result = sentencizer(text)
    def test_process_tlg_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write("[A] [B] [C] [D] 1.2.3 Sample TLG content.")
            temp_file_path = temp_file.name

        result = process_tlg_file(temp_file_path, self.nlp)
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

        os.unlink(temp_file_path)

    def test_create_data_with_corpus_manager(self):
        # Create a temporary TLG file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write("[A] [B] [C] [D] 1.2.3 Sample TLG content for corpus test.")
            temp_file_path = temp_file.name

        # Process the file and add it to the corpus
        create_data(temp_file_path, self.corpus_manager, self.nlp)

        # Check if the text was added to the corpus
        text_id = os.path.splitext(os.path.basename(temp_file_path))[0]
        self.assertTrue(self.corpus_manager.text_exists(text_id))

        # Retrieve the processed text from the corpus
        processed_text = self.corpus_manager.get_text(text_id)
        self.assertIsNotNone(processed_text)
        self.assertIsInstance(processed_text, list)
        self.assertGreater(len(processed_text), 0)

        os.unlink(temp_file_path)

if __name__ == '__main__':
    unittest.main()
