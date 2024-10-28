from typing import Optional
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from . import Base

class Author(Base):
    """Model for storing author information.
    
    This model represents authors of ancient medical texts, supporting
    multiple languages and normalized name variants.
    """
    __tablename__ = "authors"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Required fields
    name: Mapped[str] = mapped_column(String, nullable=False)
    reference_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True, unique=True)
    
    # Optional fields
    normalized_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    
    # Relationships
    texts = relationship("Text", back_populates="author")
    
    def __repr__(self) -> str:
        return f"Author(id={self.id}, name={self.name}, reference_code={self.reference_code})"
