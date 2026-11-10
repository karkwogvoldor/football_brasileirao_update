"""Create the legacy gallery schema for fresh databases."""

from alembic import op
import sqlalchemy as sa


revision = "0001_legacy_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "times",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(), nullable=True),
        sa.Column("escudo", sa.String(), nullable=True),
        sa.Column("foto_craque", sa.String(), nullable=True),
        sa.Column("formacao", sa.String(length=10), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_times_id", "times", ["id"])
    op.create_index("ix_times_nome", "times", ["nome"])
    op.create_table(
        "jogadores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(), nullable=True),
        sa.Column("number", sa.Integer(), nullable=True),
        sa.Column("posicao", sa.String(length=4), nullable=True),
        sa.Column("team_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["times.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_jogadores_id", "jogadores", ["id"])
    op.create_index("ix_jogadores_nome", "jogadores", ["nome"])


def downgrade() -> None:
    op.drop_index("ix_jogadores_nome", table_name="jogadores")
    op.drop_index("ix_jogadores_id", table_name="jogadores")
    op.drop_table("jogadores")
    op.drop_index("ix_times_nome", table_name="times")
    op.drop_index("ix_times_id", table_name="times")
    op.drop_table("times")
