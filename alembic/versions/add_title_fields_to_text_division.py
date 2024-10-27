"""add_title_fields_to_text_division

Revision ID: add_title_fields
Revises: 9f3c17413c41
Create Date: 2024-02-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_title_fields'
down_revision: Union[str, None] = '9f3c17413c41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add only the new title-related columns
    op.add_column('text_divisions', sa.Column('is_title', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('text_divisions', sa.Column('title_number', sa.String(), nullable=True))
    op.add_column('text_divisions', sa.Column('title_text', sa.String(), nullable=True))

    # Add index for title lookup
    op.create_index(op.f('ix_text_divisions_is_title'), 'text_divisions', ['is_title'], unique=False)
    op.create_index(op.f('ix_text_divisions_title_number'), 'text_divisions', ['title_number'], unique=False)


def downgrade() -> None:
    # Remove indexes
    op.drop_index(op.f('ix_text_divisions_title_number'), table_name='text_divisions')
    op.drop_index(op.f('ix_text_divisions_is_title'), table_name='text_divisions')

    # Remove title-related columns
    op.drop_column('text_divisions', 'title_text')
    op.drop_column('text_divisions', 'title_number')
    op.drop_column('text_divisions', 'is_title')
