"""Convert the lineups currently embedded in clube.js into stable JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import models
from brafoot.catalog.importer import normalize_name
from brafoot.catalog.seeder import seed_brasileirao_2026


def parse_legacy_lineup_ids(javascript: str) -> dict[int, list[int]]:
    block_match = re.search(
        r"const\s+TITULARES\s*=\s*\{(?P<body>.*?)\n\};",
        javascript,
        re.DOTALL,
    )
    if block_match is None:
        raise ValueError("Bloco TITULARES não encontrado em clube.js")

    lineups: dict[int, list[int]] = {}
    for match in re.finditer(
        r"^\s*(\d+):\s*\[([^\]]+)\]",
        block_match.group("body"),
        re.MULTILINE,
    ):
        team_id = int(match.group(1))
        player_ids = [int(value) for value in re.findall(r"\d+", match.group(2))]
        lineups[team_id] = player_ids
    return lineups


def build_payload(javascript_path: Path) -> dict:
    lineups_by_team = parse_legacy_lineup_ids(
        javascript_path.read_text(encoding="utf-8")
    )
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    models.Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    payload = {"source": "static/clube.js", "lineups": []}
    with session_factory() as session:
        seed_brasileirao_2026(session)
        for team_id, player_ids in sorted(lineups_by_team.items()):
            team = session.get(models.Team, team_id)
            if team is None:
                raise ValueError(f"Time legado {team_id} não encontrado")

            players = [session.get(models.Jogador, player_id) for player_id in player_ids]
            missing = [
                player_id
                for player_id, player in zip(player_ids, players, strict=True)
                if player is None
            ]
            if missing:
                raise ValueError(f"Jogadores ausentes no time {team_id}: {missing}")

            payload["lineups"].append(
                {
                    "club_slug": normalize_name(team.nome),
                    "legacy_team_id": team.id,
                    "formation": team.formacao,
                    "starters": [
                        {
                            "legacy_player_id": player.id,
                            "name": player.nome,
                            "position": player.posicao,
                            "legacy_team_id": player.team_id,
                        }
                        for player in players
                    ],
                }
            )

    engine.dispose()
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("static/clube.js"))
    parser.add_argument(
        "--output", type=Path, default=Path("data/brasileirao_2026_lineups.json")
    )
    args = parser.parse_args()

    payload = build_payload(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
