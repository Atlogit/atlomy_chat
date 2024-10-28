"""update_lemma_models_to_uuid

Revision ID: f9a6638d6233
Revises: 55e2200734a2
Create Date: 2024-10-28 19:03:37.297993

"""
from typing import Sequence, Union
import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'f9a6638d6233'
down_revision: Union[str, None] = '55e2200734a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable uuid-ossp extension first
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create a connection to execute SQL
    conn = op.get_bind()

    # Drop existing UUID columns if they exist
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lemmas' AND column_name = 'uuid_id') THEN
                ALTER TABLE lemmas DROP COLUMN uuid_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lemma_analyses' AND column_name = 'uuid_id') THEN
                ALTER TABLE lemma_analyses DROP COLUMN uuid_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'lemma_analyses' AND column_name = 'uuid_lemma_id') THEN
                ALTER TABLE lemma_analyses DROP COLUMN uuid_lemma_id;
            END IF;
        END $$;
    """))

    # Create temporary columns
    op.add_column('lemmas', sa.Column('uuid_id', UUID(as_uuid=True), nullable=True))
    op.add_column('lemma_analyses', sa.Column('uuid_id', UUID(as_uuid=True), nullable=True))
    op.add_column('lemma_analyses', sa.Column('uuid_lemma_id', UUID(as_uuid=True), nullable=True))

    # Update lemmas with new UUIDs
    conn.execute(sa.text("""
        UPDATE lemmas 
        SET uuid_id = uuid_generate_v4()
    """))

    # Update lemma_analyses with corresponding UUIDs
    conn.execute(sa.text("""
        UPDATE lemma_analyses la
        SET uuid_id = uuid_generate_v4(),
            uuid_lemma_id = l.uuid_id
        FROM lemmas l
        WHERE la.lemma_id = l.id
    """))

    # Drop foreign key constraint first
    op.drop_constraint('lemma_analyses_lemma_id_fkey', 'lemma_analyses', type_='foreignkey')

    # Then drop primary key constraints
    op.drop_constraint('lemmas_pkey', 'lemmas', type_='primary')
    op.drop_constraint('lemma_analyses_pkey', 'lemma_analyses', type_='primary')

    # Drop old columns
    op.drop_column('lemmas', 'id')
    op.drop_column('lemma_analyses', 'id')
    op.drop_column('lemma_analyses', 'lemma_id')

    # Rename UUID columns
    op.alter_column('lemmas', 'uuid_id', new_column_name='id', nullable=False)
    op.alter_column('lemma_analyses', 'uuid_id', new_column_name='id', nullable=False)
    op.alter_column('lemma_analyses', 'uuid_lemma_id', new_column_name='lemma_id', nullable=False)

    # Add new primary key constraints
    op.create_primary_key('lemmas_pkey', 'lemmas', ['id'])
    op.create_primary_key('lemma_analyses_pkey', 'lemma_analyses', ['id'])
    
    # Add new foreign key constraint
    op.create_foreign_key(
        'lemma_analyses_lemma_id_fkey',
        'lemma_analyses', 'lemmas',
        ['lemma_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Drop foreign key constraint first
    op.drop_constraint('lemma_analyses_lemma_id_fkey', 'lemma_analyses', type_='foreignkey')

    # Then drop primary key constraints
    op.drop_constraint('lemmas_pkey', 'lemmas', type_='primary')
    op.drop_constraint('lemma_analyses_pkey', 'lemma_analyses', type_='primary')

    # Create temporary columns
    op.add_column('lemmas', sa.Column('int_id', sa.Integer(), nullable=True))
    op.add_column('lemma_analyses', sa.Column('int_id', sa.Integer(), nullable=True))
    op.add_column('lemma_analyses', sa.Column('int_lemma_id', sa.Integer(), nullable=True))

    # Create a connection to execute SQL
    conn = op.get_bind()

    # Create sequence for lemmas
    conn.execute(sa.text("""
        CREATE SEQUENCE IF NOT EXISTS lemmas_id_seq
    """))

    # Update lemmas with sequential IDs
    conn.execute(sa.text("""
        UPDATE lemmas 
        SET int_id = nextval('lemmas_id_seq')
    """))

    # Update lemma_analyses with corresponding IDs
    conn.execute(sa.text("""
        UPDATE lemma_analyses la
        SET int_id = nextval('lemmas_id_seq'),
            int_lemma_id = l.int_id
        FROM lemmas l
        WHERE la.lemma_id = l.id
    """))

    # Drop old columns
    op.drop_column('lemmas', 'id')
    op.drop_column('lemma_analyses', 'id')
    op.drop_column('lemma_analyses', 'lemma_id')

    # Rename integer columns
    op.alter_column('lemmas', 'int_id', new_column_name='id', nullable=False)
    op.alter_column('lemma_analyses', 'int_id', new_column_name='id', nullable=False)
    op.alter_column('lemma_analyses', 'int_lemma_id', new_column_name='lemma_id', nullable=False)

    # Add new primary key constraints
    op.create_primary_key('lemmas_pkey', 'lemmas', ['id'])
    op.create_primary_key('lemma_analyses_pkey', 'lemma_analyses', ['id'])
    
    # Add new foreign key constraint
    op.create_foreign_key(
        'lemma_analyses_lemma_id_fkey',
        'lemma_analyses', 'lemmas',
        ['lemma_id'], ['id'],
        ondelete='CASCADE'
    )

    # Drop sequences
    conn.execute(sa.text("""
        DROP SEQUENCE IF EXISTS lemmas_id_seq
    """))
