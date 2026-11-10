import models
from brafoot.catalog.importer import import_brasileirao_2026, load_fixture_payload
from brafoot.gameplay.sessions import COOKIE_NAME


def seed_catalog(db_session):
    payload = load_fixture_payload()
    for club_name in payload["clubs"]:
        db_session.add(models.Team(nome=club_name, formacao="4-3-3"))
    db_session.commit()
    season = import_brasileirao_2026(db_session)
    club = db_session.query(models.Club).filter_by(slug="corinthians").one()
    return season, club


# Cria um save anônimo, guarda apenas um token no cookie e recupera o mesmo save.
def test_anonymous_browser_session_creates_and_recovers_save(client, db_session):
    season, club = seed_catalog(db_session)

    response = client.post(
        "/api/v1/saves",
        json={"season_id": season.id, "controlled_club_id": club.id},
    )

    assert response.status_code == 201
    assert response.json()["controlled_club_id"] == club.id
    cookie_header = response.headers["set-cookie"]
    assert COOKIE_NAME in cookie_header
    assert "HttpOnly" in cookie_header
    assert "SameSite=lax" in cookie_header
    assert "controlled_club_id" not in cookie_header

    recovered = client.get("/api/v1/saves/current")
    assert recovered.status_code == 200
    assert recovered.json()["id"] == response.json()["id"]


# Impede que a mesma sessão controle dois clubes em saves ativos simultâneos.
def test_browser_session_allows_only_one_active_save(client, db_session):
    season, club = seed_catalog(db_session)
    first = client.post(
        "/api/v1/saves",
        json={"season_id": season.id, "controlled_club_id": club.id},
    )

    second = client.post(
        "/api/v1/saves",
        json={"season_id": season.id, "controlled_club_id": club.id},
    )

    assert first.status_code == 201
    assert second.status_code == 409


# Expõe as 380 partidas da temporada em ordem de rodada e referência oficial.
def test_fixture_api_returns_complete_official_calendar(client, db_session):
    season, _ = seed_catalog(db_session)

    response = client.get(f"/api/v1/seasons/{season.id}/fixtures")

    assert response.status_code == 200
    fixtures = response.json()
    assert len(fixtures) == 380
    assert fixtures[0]["round_number"] == 1
    assert fixtures[-1]["round_number"] == 38
