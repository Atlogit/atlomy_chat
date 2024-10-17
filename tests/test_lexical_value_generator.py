import os
import sys
import unittest
from unittest.mock import Mock, patch

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.lexical_value_generator import LexicalValueGenerator, LexicalValueGeneratorError
from src.lexical_value import LexicalValue
from src.corpus_manager import CorpusManager

class TestLexicalValueGenerator(unittest.TestCase):

    def setUp(self):
        self.mock_corpus_manager = Mock(spec=CorpusManager)
        self.generator = LexicalValueGenerator(self.mock_corpus_manager)

    @patch('src.lexical_value_generator.ChatBedrock')
    @patch('src.lexical_value_generator.TLGParser')
    def test_initialization(self, mock_tlg_parser, mock_chat_bedrock):
        generator = LexicalValueGenerator(self.mock_corpus_manager)
        self.assertIsInstance(generator, LexicalValueGenerator)

    def test_get_citations(self):
        self.mock_corpus_manager.search_texts.return_value = ["Sample citation"]
        self.generator.tlg_parser.process_texts = Mock(return_value=[{"text": "Processed citation"}])
        
        citations = self.generator.get_citations("test_word")
        
        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0]["text"], "Processed citation")

    @patch('src.lexical_value_generator.LexicalValueGenerator.query_llm')
    def test_generate_lexical_term(self, mock_query_llm):
        mock_query_llm.return_value = '{"lemma": "test", "translation": "test", "short_description": "test", "long_description": "test", "related_terms": ["test"], "references": [{"author": "test", "work": "test", "passage": "test"}]}'
        
        result = self.generator.generate_lexical_term("test", ["Sample citation"])
        
        self.assertIsInstance(result, LexicalValue)
        self.assertEqual(result.lemma, "test")

    def test_create_lexical_entry(self):
        self.generator.get_citations = Mock(return_value=[{"text": "Sample citation"}])
        self.generator.generate_lexical_term = Mock(return_value=LexicalValue(
            lemma="test",
            translation="test",
            short_description="test",
            long_description="test",
            related_terms=["test"],
            references=[{"author": "test", "work": "test", "passage": "test"}]
        ))
        self.generator.storage.store = Mock()

        result = self.generator.create_lexical_entry("test")

        self.assertIsInstance(result, LexicalValue)
        self.assertEqual(result.lemma, "test")
        self.generator.storage.store.assert_called_once()

    def test_error_handling(self):
        self.generator.get_citations = Mock(side_effect=Exception("Test error"))

        with self.assertRaises(LexicalValueGeneratorError):
            self.generator.create_lexical_entry("test")

if __name__ == '__main__':
    unittest.main()
