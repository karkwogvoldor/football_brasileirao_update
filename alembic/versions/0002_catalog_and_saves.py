"""Add the versioned catalog, official fixtures and anonymous saves."""

from alembic import op
import sqlalchemy as sa


revision = "0002_catalog_and_saves"
down_revision = "0001_legacy_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "competitions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_competitions_slug", "competitions", ["slug"], unique=True)
    op.create_table(
        "seasons",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("competition_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("source_name", sa.String(length=120), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "competition_id", "year", name="uq_season_competition_year"
        ),
    )
    op.create_table(
        "clubs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("legacy_team_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["legacy_team_id"], ["times.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("legacy_team_id"),
    )
    op.create_index("ix_clubs_slug", "clubs", ["slug"], unique=True)
    op.create_table(
        "fixtures",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("source_ref", sa.String(length=3), nullable=False),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("scheduled_time", sa.Time(), nullable=True),
        sa.Column("home_club_id", sa.Integer(), nullable=False),
        sa.Column("away_club_id", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "home_club_id <> away_club_id", name="ck_fixture_distinct_clubs"
        ),
        sa.CheckConstraint(
            "round_number BETWEEN 1 AND 38", name="ck_fixture_round_range"
        ),
        sa.ForeignKeyConstraint(["away_club_id"], ["clubs.id"]),
        sa.ForeignKeyConstraint(["home_club_id"], ["clubs.id"]),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "season_id", "home_club_id", "away_club_id", name="uq_fixture_home_away"
        ),
        sa.UniqueConstraint(
            "season_id", "source_ref", name="uq_fixture_season_source_ref"
        ),
    )
    op.create_index("ix_fixtures_round_number", "fixtures", ["round_number"])
    op.create_index("ix_fixtures_season_id", "fixtures", ["season_id"])
    op.create_table(
        "browser_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_browser_sessions_token_hash",
        "browser_sessions",
        ["token_hash"],
        unique=True,
    )
    op.create_table(
        "game_saves",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("browser_session_id", sa.Integer(), nullable=False),
        sa.Column("controlled_club_id", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=False),
        sa.Column("snapshot_version", sa.String(length=40), nullable=False),
        sa.Column("ruleset_version", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["browser_session_id"], ["browser_sessions.id"]),
        sa.ForeignKeyConstraint(["controlled_club_id"], ["clubs.id"]),
        sa.ForeignKeyConstraint(["season_id"], ["seasons.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_game_saves_browser_session_id", "game_saves", ["browser_session_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_game_saves_browser_session_id", table_name="game_saves")
    op.drop_table("game_saves")
    op.drop_index("ix_browser_sessions_token_hash", table_name="browser_sessions")
    op.drop_table("browser_sessions")
    op.drop_index("ix_fixtures_season_id", table_name="fixtures")
    op.drop_index("ix_fixtures_round_number", table_name="fixtures")
    op.drop_table("fixtures")
    op.drop_index("ix_clubs_slug", table_name="clubs")
    op.drop_table("clubs")
    op.drop_table("seasons")
    op.drop_index("ix_competitions_slug", table_name="competitions")
    op.drop_table("competitions")
