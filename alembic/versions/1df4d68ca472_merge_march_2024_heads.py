"""Initial migration for lexical_value, sentence, text_line, and text_division models

Revision ID: 1df4d68ca472
Revises: 
Create Date: 2024-03-21 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1df4d68ca472'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Drop all existing tables using CASCADE to handle dependencies
    op.execute("DROP TABLE IF EXISTS sentence_text_lines CASCADE")
    op.execute("DROP TABLE IF EXISTS text_lines CASCADE")
    op.execute("DROP TABLE IF EXISTS text_divisions CASCADE")
    op.execute("DROP TABLE IF EXISTS lexical_values CASCADE")
    op.execute("DROP TABLE IF EXISTS sentences CASCADE")
    op.execute("DROP TABLE IF EXISTS texts CASCADE")
    op.execute("DROP TABLE IF EXISTS authors CASCADE")

    # Create the authors table first since it's referenced by texts
    op.create_table(
        'authors',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('reference_code', sa.String(20), nullable=False, unique=True),
        sa.Column('normalized_name', sa.String),
        sa.Column('language_code', sa.String(5)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text("now()"))
    )

    # Create the texts table
    op.create_table(
        'texts',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('author_id', sa.Integer, sa.ForeignKey('authors.id'), nullable=True),
        sa.Column('reference_code', sa.String(20), nullable=True, index=True),
        sa.Column('title', sa.String, nullable=False),
        sa.Column('text_metadata', sa.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text("now()"))
    )

    # Create the TextDivision table
    op.create_table(
        'text_divisions',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('text_id', sa.Integer, sa.ForeignKey('texts.id', ondelete="CASCADE"), nullable=False),
        sa.Column('author_id_field', sa.String, nullable=False),
        sa.Column('work_number_field', sa.String, nullable=False),
        sa.Column('work_abbreviation_field', sa.String, nullable=True),
        sa.Column('author_abbreviation_field', sa.String, nullable=True),
        sa.Column('author_name', sa.String, nullable=True),
        sa.Column('work_name', sa.String, nullable=True),
        sa.Column('book', sa.String(), nullable=True),
        sa.Column('fragment', sa.String, nullable=True),
        sa.Column('volume', sa.String, nullable=True),
        sa.Column('chapter', sa.String, nullable=True),
        sa.Column('line', sa.String, nullable=True),
        sa.Column('section', sa.String, nullable=True),
        sa.Column('page', sa.String, nullable=True),
        sa.Column('is_title', sa.Boolean, default=False),
        sa.Column('title_number', sa.String, nullable=True),
        sa.Column('title_text', sa.String, nullable=True),
        sa.Column('division_metadata', sa.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text("now()"))
    )

    # Create the TextLine table
    op.create_table(
        'text_lines',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('division_id', sa.Integer, sa.ForeignKey('text_divisions.id', ondelete="CASCADE"), nullable=False),
        sa.Column('line_number', sa.Integer, nullable=False),
        sa.Column('is_title', sa.Boolean, default=False),
        sa.Column('content', sa.String, nullable=False),
        sa.Column('categories', sa.ARRAY(sa.String)),
        sa.Column('spacy_tokens', sa.JSON),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text("now()"))
    )

    # Create the Sentence table
    op.create_table(
        'sentences',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('content', sa.String, nullable=False),
        sa.Column('source_line_ids', sa.ARRAY(sa.Integer), nullable=False),
        sa.Column('start_position', sa.Integer, nullable=False),
        sa.Column('end_position', sa.Integer, nullable=False),
        sa.Column('spacy_data', sa.JSON),
        sa.Column('categories', sa.ARRAY(sa.String)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text("now()"))
    )

    # Create the LexicalValue table with sentence_id
    op.create_table(
        'lexical_values',
        sa.Column('id', sa.UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column('lemma', sa.String, unique=True, nullable=False),
        sa.Column('translation', sa.String),
        sa.Column('short_description', sa.Text),
        sa.Column('long_description', sa.Text),
        sa.Column('related_terms', sa.ARRAY(sa.String)),
        sa.Column('citations_used', sa.JSON),
        sa.Column('references', sa.JSON),
        sa.Column('sentence_contexts', sa.JSON),
        sa.Column('sentence_id', sa.Integer, sa.ForeignKey('sentences.id', ondelete="SET NULL"), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text("now()"))
    )

    # Create sentence_text_lines association table
    op.create_table(
        'sentence_text_lines',
        sa.Column('sentence_id', sa.Integer, sa.ForeignKey('sentences.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('text_line_id', sa.Integer, sa.ForeignKey('text_lines.id', ondelete="CASCADE"), primary_key=True),
        sa.Column('position_start', sa.Integer, nullable=False),
        sa.Column('position_end', sa.Integer, nullable=False)
    )

    # Create indexes
    op.create_index('ix_lexical_values_sentence_id', 'lexical_values', ['sentence_id'])
    op.create_index('ix_lexical_values_lemma', 'lexical_values', ['lemma'])

def downgrade() -> None:
    # Drop all tables in reverse order with CASCADE
    op.execute("DROP TABLE IF EXISTS sentence_text_lines CASCADE")
    op.execute("DROP TABLE IF EXISTS text_lines CASCADE")
    op.execute("DROP TABLE IF EXISTS text_divisions CASCADE")
    op.execute("DROP TABLE IF EXISTS lexical_values CASCADE")
    op.execute("DROP TABLE IF EXISTS sentences CASCADE")
    op.execute("DROP TABLE IF EXISTS texts CASCADE")
    op.execute("DROP TABLE IF EXISTS authors CASCADE")
