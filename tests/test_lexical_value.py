import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
import json
from src.lexical_value import LexicalValue

class TestLexicalValue(unittest.TestCase):
    def setUp(self):
        self.sample_value = LexicalValue(
            lemma="ἀρτηρία",
            translation="Artery, Windpipe",
            short_description="A term used in ancient Greek medicine to refer to various tubular structures in the body.",
            long_description="The term artēria has a complex history in ancient Greek medical terminology...",
        )

    def test_initialization(self):
        self.assertEqual(self.sample_value.lemma, "ἀρτηρία")
        self.assertEqual(self.sample_value.translation, "Artery, Windpipe")
        self.assertEqual(len(self.sample_value.related_terms), 0)
        self.assertEqual(len(self.sample_value.historical_timeline), 0)
        self.assertEqual(len(self.sample_value.references), 0)

    def test_add_related_term(self):
        self.sample_value.add_related_term("φλέψ")
        self.assertIn("φλέψ", self.sample_value.related_terms)
        # Test adding duplicate term
        self.sample_value.add_related_term("φλέψ")
        self.assertEqual(self.sample_value.related_terms.count("φλέψ"), 1)

    def test_add_timeline_event(self):
        self.sample_value.add_timeline_event("5th century BCE", "Used to refer to the windpipe")
        self.assertEqual(len(self.sample_value.historical_timeline), 1)
        self.assertEqual(self.sample_value.historical_timeline[0]["period"], "5th century BCE")

    def test_add_reference(self):
        self.sample_value.add_reference("Hippocrates", "On the Sacred Disease", "Chapter 3")
        self.assertEqual(len(self.sample_value.references), 1)
        self.assertEqual(self.sample_value.references[0]["author"], "Hippocrates")

    def test_serialization(self):
        json_str = self.sample_value.to_json()
        deserialized_value = LexicalValue.from_json(json_str)
        self.assertEqual(self.sample_value, deserialized_value)

    def test_complex_serialization(self):
        self.sample_value.add_related_term("φλέψ")
        self.sample_value.add_timeline_event("5th century BCE", "Used to refer to the windpipe")
        self.sample_value.add_reference("Hippocrates", "On the Sacred Disease", "Chapter 3")

        json_str = self.sample_value.to_json()
        deserialized_value = LexicalValue.from_json(json_str)
        
        self.assertEqual(self.sample_value, deserialized_value)
        self.assertIn("φλέψ", deserialized_value.related_terms)
        self.assertEqual(len(deserialized_value.historical_timeline), 1)
        self.assertEqual(len(deserialized_value.references), 1)

if __name__ == '__main__':
    unittest.main()
