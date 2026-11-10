from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from database import Base

class Jogador(Base):
    __tablename__ = 'jogadores'

    id     = Column(Integer, primary_key=True, index=True)  # gerado automaticamente
    nome   = Column(String, index=True)
    number = Column(Integer)
    posicao = Column(String(4))

    # Relacionamentos (opcionais, preenchidos depois)
    team_id   = Column(Integer, ForeignKey('times.id'), nullable=True)
    team      = relationship("Team", back_populates="jogadores")


class Team(Base):
    __tablename__ = 'times'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    jogadores = relationship("Jogador", back_populates="team", uselist = True, lazy="joined")
    escudo = Column(String, nullable=True)
    foto_craque = Column(String, nullable = True)
    formacao = Column(String(10), nullable=True)  # ex: "4-3-3", "4-4-2"
    catalog_club = relationship("Club", back_populates="legacy_team", uselist=False)


class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(80), nullable=False, unique=True, index=True)
    seasons = relationship("Season", back_populates="competition")


class Season(Base):
    __tablename__ = "seasons"
    __table_args__ = (
        UniqueConstraint("competition_id", "year", name="uq_season_competition_year"),
    )

    id = Column(Integer, primary_key=True)
    competition_id = Column(Integer, ForeignKey("competitions.id"), nullable=False)
    year = Column(Integer, nullable=False)
    name = Column(String(120), nullable=False)
    source_name = Column(String(120), nullable=False)
    source_url = Column(String(500), nullable=False)

    competition = relationship("Competition", back_populates="seasons")
    fixtures = relationship("Fixture", back_populates="season")
    game_saves = relationship("GameSave", back_populates="season")


class Club(Base):
    __tablename__ = "clubs"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    slug = Column(String(80), nullable=False, unique=True, index=True)
    state = Column(String(2), nullable=False)
    legacy_team_id = Column(Integer, ForeignKey("times.id"), nullable=True, unique=True)

    legacy_team = relationship("Team", back_populates="catalog_club")
    home_fixtures = relationship(
        "Fixture", foreign_keys="Fixture.home_club_id", back_populates="home_club"
    )
    away_fixtures = relationship(
        "Fixture", foreign_keys="Fixture.away_club_id", back_populates="away_club"
    )


class Fixture(Base):
    __tablename__ = "fixtures"
    __table_args__ = (
        CheckConstraint("home_club_id <> away_club_id", name="ck_fixture_distinct_clubs"),
        CheckConstraint("round_number BETWEEN 1 AND 38", name="ck_fixture_round_range"),
        UniqueConstraint("season_id", "source_ref", name="uq_fixture_season_source_ref"),
        UniqueConstraint(
            "season_id", "home_club_id", "away_club_id", name="uq_fixture_home_away"
        ),
    )

    id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False, index=True)
    source_ref = Column(String(3), nullable=False)
    round_number = Column(Integer, nullable=False, index=True)
    scheduled_date = Column(Date, nullable=False)
    scheduled_time = Column(Time, nullable=True)
    home_club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    away_club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)

    season = relationship("Season", back_populates="fixtures")
    home_club = relationship(
        "Club", foreign_keys=[home_club_id], back_populates="home_fixtures"
    )
    away_club = relationship(
        "Club", foreign_keys=[away_club_id], back_populates="away_fixtures"
    )


class BrowserSession(Base):
    __tablename__ = "browser_sessions"

    id = Column(Integer, primary_key=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    game_saves = relationship("GameSave", back_populates="browser_session")


class GameSave(Base):
    __tablename__ = "game_saves"

    id = Column(Integer, primary_key=True)
    browser_session_id = Column(
        Integer, ForeignKey("browser_sessions.id"), nullable=False, index=True
    )
    controlled_club_id = Column(Integer, ForeignKey("clubs.id"), nullable=False)
    season_id = Column(Integer, ForeignKey("seasons.id"), nullable=False)
    snapshot_version = Column(String(40), nullable=False, default="brasileirao-2026-v1")
    ruleset_version = Column(String(40), nullable=False, default="brafoot-rules-v1")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    browser_session = relationship("BrowserSession", back_populates="game_saves")
    controlled_club = relationship("Club")
    season = relationship("Season", back_populates="game_saves")
