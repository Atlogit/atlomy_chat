import unittest
import os
import json
import logging
from corpus_manager import CorpusManager

class TestCorpusManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test_corpus')
        os.makedirs(self.test_dir, exist_ok=True)
        self.corpus_manager = CorpusManager(self.test_dir)

    def tearDown(self):
        for file in os.listdir(self.test_dir):
            os.remove(os.path.join(self.test_dir, file))
        os.rmdir(self.test_dir)

    def test_import_text(self):
        # Test importing a sample JSONL file
        sample_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'examples', 'jsonl_example.jsonl')
        self.corpus_manager.import_text(sample_file)
        self.assertTrue(self.corpus_manager.text_exists('jsonl_example.jsonl'))

        # Test importing a non-existent file
        with self.assertRaises(FileNotFoundError):
            self.corpus_manager.import_text('non_existent_file.txt')

    def test_get_text(self):
        # Import a sample text
        sample_text = [{"text": "Sample sentence", "tokens": []}]
        self.corpus_manager.add_text("sample.jsonl", sample_text)

        # Test retrieving the text
        retrieved_text = self.corpus_manager.get_text("sample.jsonl")
        self.assertEqual(retrieved_text, sample_text)

        # Test retrieving a non-existent text
        with self.assertRaises(FileNotFoundError):
            self.corpus_manager.get_text("non_existent.jsonl")

    def test_list_texts(self):
        # Add sample texts
        self.corpus_manager.add_text("text1.jsonl", [])
        self.corpus_manager.add_text("text2.jsonl", [])

        # Test listing texts
        texts = self.corpus_manager.list_texts()
        self.assertIn("text1.jsonl", texts)
        self.assertIn("text2.jsonl", texts)

    def test_add_text(self):
        sample_text = [{"text": "Sample sentence", "tokens": []}]
        self.corpus_manager.add_text("new_text.jsonl", sample_text)
        self.assertTrue(self.corpus_manager.text_exists("new_text.jsonl"))

    def test_update_text(self):
        # Add initial text
        initial_text = [{"text": "Initial sentence", "tokens": []}]
        self.corpus_manager.add_text("update_test.jsonl", initial_text)

        # Update the text
        updated_text = [{"text": "Updated sentence", "tokens": []}]
        self.corpus_manager.update_text("update_test.jsonl", updated_text)

        # Verify the update
        retrieved_text = self.corpus_manager.get_text("update_test.jsonl")
        self.assertEqual(retrieved_text, updated_text)

    def test_remove_text(self):
        # Add a text
        self.corpus_manager.add_text("remove_test.jsonl", [])

        # Remove the text
        self.corpus_manager.remove_text("remove_test.jsonl")

        # Verify the text is removed
        self.assertFalse(self.corpus_manager.text_exists("remove_test.jsonl"))

    def test_search_texts(self):
        # Add sample texts
        text1 = [{"text": "This is a sample sentence.", "tokens": []}]
        text2 = [{"text": "This is another example.", "tokens": []}]
        self.corpus_manager.add_text("text1.jsonl", text1)
        self.corpus_manager.add_text("text2.jsonl", text2)

        # Search for a term
        results = self.corpus_manager.search_texts("sample")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['text_id'], "text1.jsonl")

        # Search for a term present in both texts
        results = self.corpus_manager.search_texts("is")
        self.assertEqual(len(results), 2)

    def test_error_handling(self):
        # Test importing non-existent file
        with self.assertRaises(FileNotFoundError):
            self.corpus_manager.import_text("non_existent_file.txt")

        # Test updating non-existent text
        with self.assertRaises(FileNotFoundError):
            self.corpus_manager.update_text("non_existent.jsonl", [])

        # Test removing non-existent text
        with self.assertRaises(FileNotFoundError):
            self.corpus_manager.remove_text("non_existent.jsonl")

if __name__ == '__main__':
    unittest.main()
