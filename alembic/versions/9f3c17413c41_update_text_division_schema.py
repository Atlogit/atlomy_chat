"""update_text_division_schema

Revision ID: 9f3c17413c41
Revises: fdff7b902322
Create Date: 2024-10-26 02:29:56.132862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9f3c17413c41'
down_revision: Union[str, None] = 'fdff7b902322'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new citation component columns
    op.add_column('text_divisions', sa.Column('author_id_field', sa.String(), nullable=False, server_default=''))
    op.add_column('text_divisions', sa.Column('work_number_field', sa.String(), nullable=False, server_default=''))
    op.add_column('text_divisions', sa.Column('epithet_field', sa.String(), nullable=True))
    op.add_column('text_divisions', sa.Column('fragment_field', sa.String(), nullable=True))

    # Remove server_default after data migration
    op.alter_column('text_divisions', 'author_id_field',
                    existing_type=sa.String(),
                    server_default=None)
    op.alter_column('text_divisions', 'work_number_field',
                    existing_type=sa.String(),
                    server_default=None)

    # Add indexes for commonly queried fields
    op.create_index(op.f('ix_text_divisions_author_id_field'), 'text_divisions', ['author_id_field'], unique=False)
    op.create_index(op.f('ix_text_divisions_work_number_field'), 'text_divisions', ['work_number_field'], unique=False)


def downgrade() -> None:
    # Remove indexes
    op.drop_index(op.f('ix_text_divisions_work_number_field'), table_name='text_divisions')
    op.drop_index(op.f('ix_text_divisions_author_id_field'), table_name='text_divisions')

    # Remove citation component columns
    op.drop_column('text_divisions', 'fragment_field')
    op.drop_column('text_divisions', 'epithet_field')
    op.drop_column('text_divisions', 'work_number_field')
    op.drop_column('text_divisions', 'author_id_field')
