"""merge_lexical_value_heads

Revision ID: 4b4e34b4f167
Revises: add_direct_citation_links, add_sentence_context, merge_all_current_heads
Create Date: 2024-10-29 00:53:49.364537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b4e34b4f167'
down_revision: Union[str, None] = ('add_direct_citation_links', 'add_sentence_context', 'merge_all_current_heads')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
