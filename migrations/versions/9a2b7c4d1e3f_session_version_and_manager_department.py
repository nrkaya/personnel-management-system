"""session version and manager department

Revision ID: 9a2b7c4d1e3f
Revises: 4c73fef73c1e
Create Date: 2026-10-29 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a2b7c4d1e3f'
down_revision = '4c73fef73c1e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('kullanicilar', schema=None) as batch_op:
        batch_op.add_column(sa.Column('departman', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('oturum_surumu', sa.Integer(), nullable=False, server_default='0'))
        batch_op.create_index(batch_op.f('ix_kullanicilar_departman'), ['departman'], unique=False)


def downgrade():
    with op.batch_alter_table('kullanicilar', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_kullanicilar_departman'))
        batch_op.drop_column('oturum_surumu')
        batch_op.drop_column('departman')
