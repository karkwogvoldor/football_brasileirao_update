from __future__ import annotations

import json
import re
import unicodedata
from datetime import date, time
from pathlib import Path

from sqlalchemy.orm import Session

import models


DEFAULT_FIXTURE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "brasileirao_2026_fixtures.json"
)

CLUB_STATES = {
    "Atlético Mineiro": "MG",
    "Athletico Paranaense": "PR",
    "Bahia": "BA",
    "Botafogo": "RJ",
    "Red Bull Bragantino": "SP",
    "Chapecoense": "SC",
    "Corinthians": "SP",
    "Coritiba": "PR",
    "Cruzeiro": "MG",
    "Flamengo": "RJ",
    "Fluminense": "RJ",
    "Grêmio": "RS",
    "Internacional": "RS",
    "Mirassol": "SP",
    "Palmeiras": "SP",
    "Remo": "PA",
    "Santos": "SP",
    "São Paulo": "SP",
    "Vasco da Gama": "RJ",
    "Vitória": "BA",
}


class CatalogImportError(ValueError):
    pass


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def load_fixture_payload(path: Path = DEFAULT_FIXTURE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_fixture_payload(payload: dict) -> None:
    fixtures = payload.get("fixtures", [])
    clubs = set(payload.get("clubs", []))
    if clubs != set(CLUB_STATES):
        raise CatalogImportError("O calendário deve conter exatamente os 20 clubes")
    if len(fixtures) != 380:
        raise CatalogImportError("O calendário deve conter 380 partidas")

    refs: set[str] = set()
    pairings: set[tuple[str, str]] = set()
    appearances = {club: 0 for club in clubs}
    home_games = {club: 0 for club in clubs}
    round_games = {round_number: 0 for round_number in range(1, 39)}

    for fixture in fixtures:
        reference = fixture["source_ref"]
        home = fixture["home_club"]
        away = fixture["away_club"]
        round_number = fixture["round_number"]
        if reference in refs:
            raise CatalogImportError(f"Referência duplicada: {reference}")
        if home == away:
            raise CatalogImportError(f"Clube enfrenta a si mesmo: {reference}")
        if (home, away) in pairings:
            raise CatalogImportError(f"Confronto duplicado: {home} x {away}")
        if round_number not in round_games:
            raise CatalogImportError(f"Rodada inválida: {round_number}")
        refs.add(reference)
        pairings.add((home, away))
        appearances[home] += 1
        appearances[away] += 1
        home_games[home] += 1
        round_games[round_number] += 1

    if set(appearances.values()) != {38}:
        raise CatalogImportError("Cada clube deve disputar 38 partidas")
    if set(home_games.values()) != {19}:
        raise CatalogImportError("Cada clube deve ter 19 mandos")
    if set(round_games.values()) != {10}:
        raise CatalogImportError("Cada rodada deve conter 10 partidas")


def import_brasileirao_2026(
    session: Session,
    path: Path = DEFAULT_FIXTURE_PATH,
) -> models.Season:
    payload = load_fixture_payload(path)
    validate_fixture_payload(payload)

    legacy_teams = {
        normalize_name(team.nome): team for team in session.query(models.Team).all()
    }
    missing = [
        club for club in payload["clubs"] if normalize_name(club) not in legacy_teams
    ]
    if missing:
        raise CatalogImportError(
            "Times legados ausentes antes da importação: " + ", ".join(missing)
        )

    competition = session.query(models.Competition).filter_by(slug="brasileirao-a").one_or_none()
    if competition is None:
        competition = models.Competition(
            name=payload["competition"], slug="brasileirao-a"
        )
        session.add(competition)
        session.flush()

    season = (
        session.query(models.Season)
        .filter_by(competition_id=competition.id, year=payload["season"])
        .one_or_none()
    )
    if season is None:
        season = models.Season(
            competition_id=competition.id,
            year=payload["season"],
            name=f"{payload['competition']} {payload['season']}",
            source_name=payload["source"],
            source_url=payload["source_url"],
        )
        session.add(season)
        session.flush()

    clubs_by_name: dict[str, models.Club] = {}
    for club_name in payload["clubs"]:
        slug = normalize_name(club_name)
        club = session.query(models.Club).filter_by(slug=slug).one_or_none()
        if club is None:
            club = models.Club(
                name=club_name,
                slug=slug,
                state=CLUB_STATES[club_name],
                legacy_team_id=legacy_teams[slug].id,
            )
            session.add(club)
            session.flush()
        clubs_by_name[club_name] = club

    existing_refs = {
        reference
        for (reference,) in session.query(models.Fixture.source_ref)
        .filter_by(season_id=season.id)
        .all()
    }
    for fixture_data in payload["fixtures"]:
        if fixture_data["source_ref"] in existing_refs:
            continue
        session.add(
            models.Fixture(
                season_id=season.id,
                source_ref=fixture_data["source_ref"],
                round_number=fixture_data["round_number"],
                scheduled_date=date.fromisoformat(fixture_data["scheduled_date"]),
                scheduled_time=(
                    time.fromisoformat(fixture_data["scheduled_time"])
                    if fixture_data["scheduled_time"]
                    else None
                ),
                home_club_id=clubs_by_name[fixture_data["home_club"]].id,
                away_club_id=clubs_by_name[fixture_data["away_club"]].id,
            )
        )

    session.commit()
    session.refresh(season)
    return season
