"""align legacy schema

Databases created before Alembic were only stamped by the initial revision,
so they miss a few indexes and constraints and still store salaries as FLOAT.
Each step checks the live schema first, so fresh databases are unaffected.

Revision ID: b5e8f1a2c3d4
Revises: 9a2b7c4d1e3f
Create Date: 2026-10-29 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5e8f1a2c3d4'
down_revision = '9a2b7c4d1e3f'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())

    leave_indexes = {index['name'] for index in inspector.get_indexes('izinler')}
    if 'ix_izin_durum_tarih' not in leave_indexes:
        op.create_index('ix_izin_durum_tarih', 'izinler', ['durum', 'baslangic', 'bitis'], unique=False)
    if 'ix_izinler_durum' not in leave_indexes:
        op.create_index('ix_izinler_durum', 'izinler', ['durum'], unique=False)

    unique_names = {constraint['name'] for constraint in inspector.get_unique_constraints('login_attempts')}
    if 'uq_login_attempt_principal_ip' not in unique_names:
        # Counters are disposable; keep the newest row of any duplicate pair.
        op.execute(
            'DELETE FROM login_attempts WHERE id NOT IN '
            '(SELECT MAX(id) FROM login_attempts GROUP BY kullanici_adi, ip_adresi)'
        )
        with op.batch_alter_table('login_attempts', schema=None) as batch_op:
            batch_op.create_unique_constraint('uq_login_attempt_principal_ip', ['kullanici_adi', 'ip_adresi'])

    salary = next(column for column in inspector.get_columns('personeller') if column['name'] == 'maas')
    # sa.Float subclasses sa.Numeric, so test for it explicitly.
    if isinstance(salary['type'], sa.Float) or not isinstance(salary['type'], sa.Numeric):
        with op.batch_alter_table('personeller', schema=None) as batch_op:
            batch_op.alter_column(
                'maas',
                existing_type=salary['type'],
                type_=sa.Numeric(precision=12, scale=2),
                existing_nullable=salary['nullable'],
            )


def downgrade():
    # The aligned schema is what the models expect; nothing to undo.
    pass
