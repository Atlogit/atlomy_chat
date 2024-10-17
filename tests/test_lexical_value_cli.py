import unittest
from unittest.mock import Mock, patch
from src.lexical_value_cli import LexicalValueCLI
from src.lexical_value import LexicalValue

class TestLexicalValueCLI(unittest.TestCase):
    def setUp(self):
        self.mock_generator = Mock()
        self.cli = LexicalValueCLI(self.mock_generator)

    def test_list_lexical_values(self):
        self.mock_generator.list_lexical_values.return_value = ['lemma1', 'lemma2']
        self.mock_generator.get_lexical_value.side_effect = [
            LexicalValue('lemma1', short_description='desc1'),
            LexicalValue('lemma2', short_description='desc2')
        ]
        result = self.cli.list_lexical_values()
        expected = [
            {'lemma': 'lemma1', 'short_description': 'desc1'},
            {'lemma': 'lemma2', 'short_description': 'desc2'}
        ]
        self.assertEqual(result, expected)

    def test_view_lexical_value(self):
        mock_lv = LexicalValue('test_lemma', short_description='test_desc')
        self.mock_generator.get_lexical_value.return_value = mock_lv
        self.mock_generator.suggest_updates.return_value = {'suggested': 'update'}
        result = self.cli.view_lexical_value('test_lemma')
        expected = {**mock_lv.__dict__, 'suggested_updates': {'suggested': 'update'}}
        self.assertEqual(result, expected)

    def test_edit_lexical_value(self):
        mock_lv = LexicalValue('test_lemma', short_description='old_desc')
        self.mock_generator.get_lexical_value.return_value = mock_lv
        self.cli.edit_lexical_value('test_lemma', short_description='new_desc')
        self.mock_generator.update_lexical_value.assert_called_once()
        self.assertEqual(mock_lv.short_description, 'new_desc')

    def test_suggest_updates(self):
        self.mock_generator.suggest_updates.return_value = {'suggested': 'update'}
        result = self.cli.suggest_updates('test_lemma', 'new text')
        self.assertEqual(result, {'suggested': 'update'})

    def test_view_version_history(self):
        mock_history = [LexicalValue('test_lemma', version=1), LexicalValue('test_lemma', version=2)]
        self.mock_generator.get_version_history.return_value = mock_history
        result = self.cli.view_version_history('test_lemma')
        expected = [lv.__dict__ for lv in mock_history]
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
