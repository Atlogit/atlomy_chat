"""
Database models for lexical values and their analyses.
"""

from sqlalchemy import Column, String, Text, DateTime, func, ForeignKey, Integer
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
    citations_used = Column(JSONB)  # Store LLM's citation analysis as JSON for flexibility
    references = Column(JSONB)      # Store system-generated citation data
    sentence_contexts = Column(JSONB)  # Store full sentence contexts
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Direct relationship with sentences using integer id
    sentence_id = Column(Integer, ForeignKey('sentences.id'), nullable=True)
    sentence = relationship("Sentence", back_populates="lexical_values")

    __table_args__ = {
        'comment': 'Stores lexical values with their analyses, citations, and sentence contexts'
    }

    def to_dict(self):
        """Convert the model to a dictionary."""
        # Get citations from references if available
        citations = []
        if self.references and 'citations' in self.references:
            citations = self.references['citations']
            # Enrich citations with sentence context if available
            for citation in citations:
                sentence_id = str(citation['sentence']['id'])
                if self.sentence_contexts and sentence_id in self.sentence_contexts:
                    context = self.sentence_contexts[sentence_id]
                    citation['sentence'].update({
                        'prev_sentence': context.get('prev', ''),
                        'next_sentence': context.get('next', ''),
                        'tokens': context.get('tokens', {})
                    })

        return {
            "id": str(self.id),
            "lemma": self.lemma,
            "translation": self.translation,
            "short_description": self.short_description,
            "long_description": self.long_description,
            "related_terms": self.related_terms,
            "citations_used": self.citations_used or [],  # Ensure we always return a list
            "references": {
                "citations": citations  # System-generated citations with context
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Create a model instance from a dictionary."""
        # Ensure citations_used is a list if provided, or initialize as empty list
        citations_used = data.get("citations_used", [])
        if not isinstance(citations_used, list):
            citations_used = [str(citations_used)]
        
        return cls(
            lemma=data["lemma"],
            translation=data.get("translation"),
            short_description=data.get("short_description"),
            long_description=data.get("long_description"),
            related_terms=data.get("related_terms", []),
            citations_used=citations_used,  # Store as JSON array
            references=data.get("references", {}),          # System citations
            sentence_contexts=data.get("sentence_contexts", {}),
            sentence_id=data.get("sentence_id")
        )

    def add_citation_link(self, sentence_id: int, context: dict) -> None:
        """Add a direct link to a sentence with its context."""
        self.sentence_id = sentence_id
        if not self.sentence_contexts:
            self.sentence_contexts = {}
        self.sentence_contexts[str(sentence_id)] = {
            'text': context.get('text', ''),
            'prev': context.get('prev_sentence', ''),
            'next': context.get('next_sentence', ''),
            'tokens': context.get('tokens', {})
        }

    def get_linked_citations(self) -> list:
        """Get all citations directly linked to this lexical value in standard format."""
        if not self.sentence:
            return []
            
        context = self.sentence_contexts.get(str(self.sentence_id), {})
        
        # Get the first text_line associated with the sentence
        text_line = self.sentence.text_lines[0] if self.sentence.text_lines else None
        if not text_line:
            return [{
                "sentence": {
                    "id": self.sentence_id,
                    "text": context.get('text', self.sentence.content),
                    "prev_sentence": context.get('prev', ''),
                    "next_sentence": context.get('next', ''),
                    "tokens": context.get('tokens', {})
                },
                "citation": '',
                "context": {
                    "line_id": '',
                    "line_text": '',
                    "line_numbers": []
                },
                "location": {
                    "volume": '',
                    "chapter": '',
                    "section": ''
                },
                "source": {
                    "author": 'Unknown',
                    "work": ''
                }
            }]
        
        division = text_line.division
        return [{
            "sentence": {
                "id": self.sentence_id,
                "text": context.get('text', self.sentence.content),
                "prev_sentence": context.get('prev', ''),
                "next_sentence": context.get('next', ''),
                "tokens": context.get('tokens', {})
            },
            "citation": division.format_citation() if hasattr(division, 'format_citation') else '',
            "context": {
                "line_id": f"{division.text.id}-{text_line.line_number}",
                "line_text": text_line.content,
                "line_numbers": [text_line.line_number]
            },
            "location": {
                "volume": division.volume,
                "chapter": division.chapter,
                "section": division.section
            },
            "source": {
                "author": division.author_name,
                "work": division.work_name
            }
        }]
