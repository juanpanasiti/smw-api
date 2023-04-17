"""Create users table

Revision ID: 2145cc6ccdd7
Revises:
Create Date: 2023-04-16 01:34:26.070324

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '2145cc6ccdd7'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
                    sa.Column('username', sa.String(
                        length=50), nullable=False),
                    sa.Column('password', sa.String(
                        length=60), nullable=False),
                    sa.Column('email', sa.String(length=50), nullable=False),
                    sa.Column('role', sa.Enum('superadmin', 'admin',
                                              'common', name='roleenum'), nullable=True),
                    sa.Column('id', sa.UUID(), nullable=False),
                    sa.Column('creation_date', sa.DateTime(), nullable=True),
                    sa.Column('last_update', sa.DateTime(), nullable=True),
                    sa.Column('is_deleted', sa.Boolean(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'),
                    'users', ['username'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
