"""Initial migration

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2023-11-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for role
    role_type = postgresql.ENUM('super_admin', 'regular_admin', name='roletype')
    role_type.create(op.get_bind())
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('hashed_password', sa.String(), nullable=True),
        sa.Column('te_id', sa.String(), nullable=True),
        sa.Column('role', sa.Enum('super_admin', 'regular_admin', name='roletype'), nullable=True),
        sa.Column('plant', sa.String(), nullable=True),
        sa.Column('must_reset_password', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_te_id'), 'users', ['te_id'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # Create submissions table
    op.create_table('submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('last_name', sa.String(), nullable=True),
        sa.Column('cin', sa.String(), nullable=True),
        sa.Column('te_id', sa.String(), nullable=True),
        sa.Column('date_of_birth', sa.DateTime(), nullable=True),
        sa.Column('grey_card_number', sa.String(), nullable=True),
        sa.Column('plant', sa.String(), nullable=True),
        sa.Column('cin_file_path', sa.String(), nullable=True),
        sa.Column('picture_file_path', sa.String(), nullable=True),
        sa.Column('grey_card_file_path', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('admin_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['admin_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_submissions_cin'), 'submissions', ['cin'], unique=False)
    op.create_index(op.f('ix_submissions_grey_card_number'), 'submissions', ['grey_card_number'], unique=False)
    op.create_index(op.f('ix_submissions_id'), 'submissions', ['id'], unique=False)
    op.create_index(op.f('ix_submissions_plant'), 'submissions', ['plant'], unique=False)
    op.create_index(op.f('ix_submissions_te_id'), 'submissions', ['te_id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_submissions_te_id'), table_name='submissions')
    op.drop_index(op.f('ix_submissions_plant'), table_name='submissions')
    op.drop_index(op.f('ix_submissions_id'), table_name='submissions')
    op.drop_index(op.f('ix_submissions_grey_card_number'), table_name='submissions')
    op.drop_index(op.f('ix_submissions_cin'), table_name='submissions')
    op.drop_table('submissions')
    
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_te_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    # Drop enum type
    sa.Enum(name='roletype').drop(op.get_bind(), checkfirst=False)