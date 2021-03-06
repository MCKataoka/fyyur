"""empty message

Revision ID: 050c99667657
Revises: 3908281ca1bd
Create Date: 2020-11-16 16:47:59.103959

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '050c99667657'
down_revision = '3908281ca1bd'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('genres', sa.ARRAY(sa.String()), nullable=True))
    op.add_column('Venue', sa.Column('genres', sa.ARRAY(sa.String()), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'genres')
    op.drop_column('Artist', 'genres')
    # ### end Alembic commands ###
