"""
Database models for lexical values and their analyses.
"""

from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship, Mapped
import uuid
from app.models import Base

class LexicalValue(Base):
    """Model for storing lexical values with their analyses and sentence contexts."""
    
    __tablename__ = "lexical_values"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lemma = Column(String, unique=True, nullable=False, index=True)
    translation = Column(String)
    short_description = Column(Text)
    long_description = Column(Text)
    related_terms = Column(ARRAY(String))
    citations_used = Column(JSONB)  # Store citations in structured format
    references = Column(JSONB)      # Store reference data
    sentence_contexts = Column(JSONB)  # Store full sentence contexts
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Direct relationship with sentences through text_lines
    sentence_id = Column(UUID(as_uuid=True), ForeignKey('text_lines.sentence_id'), nullable=True)
    sentence = relationship("TextLine", foreign_keys=[sentence_id], back_populates="lexical_values")

    __table_args__ = {
        'comment': 'Stores lexical values with their analyses, citations, and sentence contexts'
    }

    def to_dict(self):
        """Convert the model to a dictionary."""
        return {
            "id": str(self.id),
            "lemma": self.lemma,
            "translation": self.translation,
            "short_description": self.short_description,
            "long_description": self.long_description,
            "related_terms": self.related_terms,
            "citations_used": self.citations_used,
            "references": self.references,
            "sentence_contexts": self.sentence_contexts,
            "sentence_id": str(self.sentence_id) if self.sentence_id else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create a model instance from a dictionary."""
        return cls(
            lemma=data["lemma"],
            translation=data.get("translation"),
            short_description=data.get("short_description"),
            long_description=data.get("long_description"),
            related_terms=data.get("related_terms", []),
            citations_used=data.get("citations_used", {}),
            references=data.get("references", {}),
            sentence_contexts=data.get("sentence_contexts", {}),
            sentence_id=uuid.UUID(data["sentence_id"]) if data.get("sentence_id") else None
        )

    def get_sentence_context(self, sentence_id: str) -> dict:
        """Get the full context for a specific sentence."""
        if not self.sentence_contexts or sentence_id not in self.sentence_contexts:
            return None
        return self.sentence_contexts[sentence_id]

    def get_citations_with_context(self) -> list:
        """Get citations with their full sentence contexts in standard format."""
        if not self.references or 'citations' not in self.references:
            return []

        citations = []
        for citation in self.references['citations']:
            sentence_id = citation['sentence']['id']
            context = self.get_sentence_context(sentence_id)
            if context:
                # Format citation in standard format
                formatted_citation = {
                    "sentence": {
                        "id": sentence_id,
                        "text": context.get('text', ''),
                        "prev_sentence": context.get('prev', ''),
                        "next_sentence": context.get('next', ''),
                        "tokens": context.get('tokens', {})
                    },
                    "citation": citation.get('citation', ''),
                    "context": {
                        "line_id": citation['context']['line_id'],
                        "line_text": citation['context']['line_text'],
                        "line_numbers": citation['context']['line_numbers']
                    },
                    "location": {
                        "volume": citation['location'].get('volume', ''),
                        "chapter": citation['location'].get('chapter', ''),
                        "section": citation['location'].get('section', '')
                    },
                    "source": {
                        "author": citation['source'].get('author', 'Unknown'),
                        "work": citation['source'].get('work', '')
                    }
                }
                citations.append(formatted_citation)

        return citations

    def add_citation_link(self, sentence_id: str, context: dict) -> None:
        """Add a direct link to a sentence with its context."""
        self.sentence_id = uuid.UUID(sentence_id)
        if not self.sentence_contexts:
            self.sentence_contexts = {}
        self.sentence_contexts[sentence_id] = {
            'text': context.get('text', ''),
            'prev': context.get('prev_sentence', ''),
            'next': context.get('next_sentence', ''),
            'tokens': context.get('tokens', {})
        }

    def get_linked_citations(self) -> list:
        """Get all citations directly linked to this lexical value in standard format."""
        if not self.sentence or not self.sentence.division:
            return []
            
        division = self.sentence.division
        context = self.sentence_contexts.get(str(self.sentence_id), {})
        
        return [{
            "sentence": {
                "id": str(self.sentence_id),
                "text": context.get('text', self.sentence.content),
                "prev_sentence": context.get('prev', ''),
                "next_sentence": context.get('next', ''),
                "tokens": context.get('tokens', {})
            },
            "citation": division.format_citation(),
            "context": {
                "line_id": f"{self.sentence.division.text.id}-{self.sentence.line_number}",
                "line_text": self.sentence.content,
                "line_numbers": [self.sentence.line_number]
            },
            "location": {
                "volume": division.volume or '',
                "chapter": division.chapter or '',
                "section": division.section or ''
            },
            "source": {
                "author": division.author_name or 'Unknown',
                "work": division.work_name or ''
            }
        }]
