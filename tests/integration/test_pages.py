import pytest
from html.parser import HTMLParser

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

from main import create_app


pytestmark = pytest.mark.integration


class ImageSourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            source = dict(attrs).get("src")
            if source:
                self.sources.append(source)


class MatchPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.players = []
        self.stylesheets = []
        self.pitch_labels = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        classes = attributes.get("class", "").split()
        if tag == "article" and "match-player" in classes:
            style = dict(
                declaration.strip().split(":", 1)
                for declaration in attributes["style"].split(";")
                if declaration.strip()
            )
            self.players.append(
                {
                    "team": attributes["data-team"],
                    "x": int(style["--x"]),
                    "y": int(style["--y"]),
                }
            )
        if tag == "link" and attributes.get("rel") == "stylesheet":
            self.stylesheets.append(attributes.get("href"))
        if tag == "svg" and "match-pitch-lines" in classes:
            self.pitch_labels.append(attributes.get("aria-label"))


# Verifica se a página inicial responde com HTML.
def test_home_page_is_available(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


# Verifica se a rota de clube continua servindo sua página base.
def test_club_page_is_currently_static(client):
    response = client.get("/clube/999999")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


# Renderiza duas formações completas, normalizadas e espelhadas na página da partida.
def test_match_page_renders_two_static_mirrored_formations(client):
    response = client.get("/partida")
    parser = MatchPageParser()
    parser.feed(response.text)

    home_players = [player for player in parser.players if player["team"] == "home"]
    away_players = [player for player in parser.players if player["team"] == "away"]

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert len(home_players) == 11
    assert len(away_players) == 11
    assert all(0 <= player["x"] <= 100 for player in parser.players)
    assert all(0 <= player["y"] <= 100 for player in parser.players)
    assert [player["x"] for player in away_players] == [
        100 - player["x"] for player in home_players
    ]
    assert [player["y"] for player in away_players] == [
        player["y"] for player in home_players
    ]
    assert parser.pitch_labels == ["Campo de futebol com duas formações estáticas"]


# Serve a folha de estilos própria sem depender do editor de escalação legado.
def test_match_page_has_available_dedicated_stylesheet(client):
    response = client.get("/partida")
    parser = MatchPageParser()
    parser.feed(response.text)

    assert "/static/partida.css" in parser.stylesheets
    stylesheet = client.get("/static/partida.css")
    assert stylesheet.status_code == 200
    assert stylesheet.headers["content-type"].startswith("text/css")


# Verifica se todos os escudos exibidos na página inicial existem e são servidos como imagem.
def test_home_team_badges_are_available(client):
    page = client.get("/")
    parser = ImageSourceParser()
    parser.feed(page.text)

    assert len(parser.sources) == 20
    for source in parser.sources:
        image = client.get(source)
        assert image.status_code == 200, source
        assert image.headers["content-type"].startswith("image/"), source
        assert image.content, source


# Garante que o startup padrão não cria tabelas fora do controle do Alembic.
def test_default_application_startup_does_not_create_database_schema(tmp_path):
    database_path = tmp_path / "startup_test.db"
    engine = create_engine(f"sqlite+pysqlite:///{database_path.as_posix()}")
    application = create_app(database_engine=engine)

    with TestClient(application) as test_client:
        assert test_client.get("/").status_code == 200

    assert inspect(engine).get_table_names() == []
    engine.dispose()
