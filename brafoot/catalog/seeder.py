from __future__ import annotations

import importlib

from sqlalchemy.orm import Session

import models
from seed.seed_times import times

from .importer import import_brasileirao_2026, normalize_name


PLAYER_MODULES = {
    "Corinthians": "seed.seed_corinthians",
    "Atlético Mineiro": "seed.seed_atletico_mineiro",
    "Athletico Paranaense": "seed.seed_athletico_paranaense",
    "Bahia": "seed.seed_bahia",
    "Botafogo": "seed.seed_botafogo",
    "Red Bull Bragantino": "seed.seed_bragantino",
    "Chapecoense": "seed.seed_chapecoense",
    "Coritiba": "seed.seed_coritiba",
    "Cruzeiro": "seed.seed_cruzeiro",
    "Flamengo": "seed.seed_flamengo",
    "Fluminense": "seed.seed_fluminense",
    "Grêmio": "seed.seed_gremio",
    "Internacional": "seed.seed_internacional",
    "Mirassol": "seed.seed_mirassol",
    "Palmeiras": "seed.seed_palmeiras",
    "Remo": "seed.seed_remo",
    "Santos": "seed.seed_santos",
    "São Paulo": "seed.seed_sao_paulo",
    "Vasco da Gama": "seed.seed_vasco",
    "Vitória": "seed.seed_vitoria",
}


def seed_legacy_teams_and_players(session: Session) -> None:
    teams_by_slug = {
        normalize_name(team.nome): team for team in session.query(models.Team).all()
    }

    for seed_team in times:
        slug = normalize_name(seed_team["nome"])
        team = teams_by_slug.get(slug)
        if team is None:
            team = models.Team(
                nome=seed_team["nome"],
                formacao=seed_team["formacao"],
            )
            session.add(team)
            session.flush()
            teams_by_slug[slug] = team
        elif team.formacao is None:
            team.formacao = seed_team["formacao"]

    session.flush()

    for club_name, module_name in PLAYER_MODULES.items():
        module = importlib.import_module(module_name)
        team = teams_by_slug[normalize_name(club_name)]
        existing_players = {
            normalize_name(player.nome): player
            for player in session.query(models.Jogador).filter_by(team_id=team.id).all()
        }
        for seed_player in module.jogadores:
            slug = normalize_name(seed_player["nome"])
            player = existing_players.get(slug)
            if player is None:
                player = models.Jogador(
                    nome=seed_player["nome"],
                    number=seed_player["number"],
                    posicao=seed_player["posicao"],
                    team_id=team.id,
                )
                session.add(player)
                existing_players[slug] = player
            else:
                player.number = seed_player["number"]
                player.posicao = seed_player["posicao"]

    session.commit()


def seed_brasileirao_2026(session: Session) -> models.Season:
    seed_legacy_teams_and_players(session)
    return import_brasileirao_2026(session)
