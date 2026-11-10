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

