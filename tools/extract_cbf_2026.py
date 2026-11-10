"""Extract the official 2026 Serie A fixture list from Firecrawl markdown.

The source is the detailed CBF PDF. Only scheduling facts are retained; real
scores are intentionally discarded because BRAFOOT simulates its own results.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import date
from pathlib import Path


SOURCE_URL = (
    "https://stcbfsiteprdimgbrs.blob.core.windows.net/img-site/cdn/"
    "Tabela_Detalhada_BSA_2026_09_11_053e1416ec.pdf"
)

CLUB_PATTERNS = {
    "Atlético Mineiro": r"(?:atletico|atl.tico|athletico|athl.tico|athleticio)\s*\|?\s*mg\b",
    "Athletico Paranaense": r"(?:atletico|atl.tico|athletico|athl.tico|athleticio)\s*\|?\s*pr\b",
    "Bahia": r"bahia\s*\|?\s*ba\b",
    "Botafogo": r"botafor?go\s*\|?\s*rj\b",
    "Red Bull Bragantino": r"red\s+bull\s+bragantino\s*\|?\s*sp\b",
    "Chapecoense": r"chapecoense\s*\|?\s*sc\b",
    "Corinthians": r"corinthians\s*\|?\s*sp\b",
    "Coritiba": r"coritiba\s*\|?\s*pr\b",
    "Cruzeiro": r"(?:cruzeiro|cruzero|cruzheiro)\s*\|?\s*mg\b",
    "Flamengo": r"flamengo\s*\|?\s*rj\b",
    "Fluminense": r"fluminense\s*\|?\s*rj\b",
    "Grêmio": r"(?:gremio|gr.mio)\s*\|?\s*rs\b",
    "Internacional": r"(?:internacional|international)\s*\|?\s*rs\b",
    "Mirassol": r"mirassol\s*\|?\s*sp\b",
    "Palmeiras": r"palmeiras\s*\|?\s*sp\b",
    "Remo": r"remo\s*\|?\s*pa\b",
    "Santos": r"santos\s*\|?\s*sp\b",
    "São Paulo": r"(?:sao|s.o)\s+paulo\s*\|?\s*sp\b",
    "Vasco da Gama": r"vasco\s+da\s+gama(?:\s+saf)?\s*\|?\s*rj\b",
    "Vitória": r"(?:vitoria|vit.ria)\s*\|?\s*ba\b",
}


def _ascii(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


def _clubs_in_line(line: str) -> list[str]:
    normalized = _ascii(line)
    matches: list[tuple[int, str]] = []
    for club, pattern in CLUB_PATTERNS.items():
        for match in re.finditer(pattern, normalized):
            matches.append((match.start(), club))

    matches.sort()
    ordered: list[str] = []
    for _, club in matches:
        if club not in ordered:
            ordered.append(club)
        if len(ordered) == 2:
            break
    return ordered


def extract_fixtures(markdown: str) -> list[dict[str, object]]:
    fixtures: list[dict[str, object]] = []
    current_date: date | None = None

    for line in markdown.splitlines():
        reference_match = re.match(r"^\|\s*(\d{3})\s*\|", line)
        if not reference_match:
            continue

        reference = int(reference_match.group(1))
        date_match = re.search(r"\b(\d{2})/(\d{2})\b", line)
        if date_match:
            current_date = date(2026, int(date_match.group(2)), int(date_match.group(1)))
        if current_date is None:
            raise ValueError(f"Fixture {reference:03d} has no date context")

        clubs = _clubs_in_line(line)
        if len(clubs) != 2:
            raise ValueError(f"Fixture {reference:03d} has ambiguous clubs: {line}")

        time_match = re.search(r"\b([012]?\d:[0-5]\d)\b", line)
        fixtures.append(
            {
                "source_ref": f"{reference:03d}",
                "round_number": ((reference - 1) // 10) + 1,
                "scheduled_date": current_date.isoformat(),
                "scheduled_time": time_match.group(1) if time_match else None,
                "home_club": clubs[0],
                "away_club": clubs[1],
            }
        )

    fixtures.sort(key=lambda fixture: int(str(fixture["source_ref"])))
    return fixtures


def validate_fixtures(fixtures: list[dict[str, object]]) -> None:
    if len(fixtures) != 380:
        raise ValueError(f"Expected 380 fixtures, found {len(fixtures)}")

    refs = {fixture["source_ref"] for fixture in fixtures}
    expected_refs = {f"{number:03d}" for number in range(1, 381)}
    if refs != expected_refs:
        raise ValueError("Fixture references are incomplete or duplicated")

    clubs = set(CLUB_PATTERNS)
    appearances = {club: 0 for club in clubs}
    home_games = {club: 0 for club in clubs}
    pairs: set[tuple[str, str]] = set()
    rounds = {round_number: 0 for round_number in range(1, 39)}

    for fixture in fixtures:
        home = str(fixture["home_club"])
        away = str(fixture["away_club"])
        round_number = int(fixture["round_number"])
        if home == away:
            raise ValueError(f"Club plays itself in fixture {fixture['source_ref']}")
        if (home, away) in pairs:
            raise ValueError(f"Duplicated home/away pairing: {home} x {away}")
        pairs.add((home, away))
        appearances[home] += 1
        appearances[away] += 1
        home_games[home] += 1
        rounds[round_number] += 1

    if set(appearances.values()) != {38}:
        raise ValueError(f"Every club must play 38 matches: {appearances}")
    if set(home_games.values()) != {19}:
        raise ValueError(f"Every club must play 19 home matches: {home_games}")
    if set(rounds.values()) != {10}:
        raise ValueError(f"Every round must have 10 matches: {rounds}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    fixtures = extract_fixtures(args.input.read_text(encoding="utf-8"))
    validate_fixtures(fixtures)
    payload = {
        "competition": "Campeonato Brasileiro Série A",
        "season": 2026,
        "source": "Confederação Brasileira de Futebol",
        "source_url": SOURCE_URL,
        "clubs": sorted(CLUB_PATTERNS),
        "fixtures": fixtures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
