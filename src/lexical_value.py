import json
from typing import List, Dict
from dataclasses import dataclass, field, asdict

@dataclass
class LexicalValue:
    lemma: str
    translation: str
    short_description: str
    long_description: str
    related_terms: List[str] = field(default_factory=list)
    #historical_timeline: List[Dict[str, str]] = field(default_factory=list)
    references: List[Dict[str, str]] = field(default_factory=list)

    def to_json(self) -> str:
        """Serialize the LexicalValue object to JSON."""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> 'LexicalValue':
        """Deserialize a JSON string to a LexicalValue object."""
        data = json.loads(json_str)
        return cls(**data)

    def add_related_term(self, term: str) -> None:
        """Add a related term to the lexical value."""
        if term not in self.related_terms:
            self.related_terms.append(term)

    def add_timeline_event(self, period: str, description: str) -> None:
        """Add a historical timeline event to the lexical value."""
        self.historical_timeline.append({"period": period, "description": description})

    def add_reference(self, author: str, work: str, passage: str) -> None:
        """Add a reference to the lexical value."""
        self.references.append({"author": author, "work": work, "passage": passage})

# Example usage and test
if __name__ == "__main__":
    # Create a sample LexicalValue
    sample_value = LexicalValue(
        lemma="ἀρτηρία",
        translation="Artery, Windpipe",
        short_description="A term used in ancient Greek medicine to refer to various tubular structures in the body.",
        long_description="The term artēria has a complex history in ancient Greek medical terminology...",
    )

    # Add some sample data
    sample_value.add_related_term("φλέψ")
    sample_value.add_timeline_event("5th century BCE", "Used to refer to the windpipe")
    sample_value.add_timeline_event("3rd century BCE", "Distinction between arteries and veins emerges")
    sample_value.add_reference("Hippocrates", "On the Sacred Disease", "Chapter 3")

    # Serialize to JSON
    json_str = sample_value.to_json()
    print("Serialized JSON:")
    print(json_str)

    # Deserialize from JSON
    deserialized_value = LexicalValue.from_json(json_str)
    print("\nDeserialized object:")
    print(deserialized_value)

    # Verify that the deserialized object matches the original
    assert sample_value == deserialized_value, "Serialization/deserialization failed"
    print("\nSerialization/deserialization test passed!")
