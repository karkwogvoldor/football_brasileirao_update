"""Aplicação local e isolada usada apenas na verificação visual do navegador."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import models
from database import get_db
from main import create_app


engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
models.Base.metadata.create_all(bind=engine)

with TestingSession() as session:
    session.add(
        models.Team(
            id=1,
            nome="Corinthians",
            formacao="4-3-3",
            escudo="/static/escudos/corinthians.webp",
            foto_craque="/static/craques/corinthians.jpg",
        )
    )
    positions = ["GOL", "ZAG", "ZAG", "LAT", "LAT", "VOL", "MEI", "MEI", "ATA", "ATA", "ATA"]
    for player_id, position in enumerate(positions, start=1):
        session.add(
            models.Jogador(
                id=player_id,
                nome=f"Jogador {player_id}",
                number=player_id,
                posicao=position,
                team_id=1,
            )
        )
    session.commit()


def override_get_db() -> Generator[Session, None, None]:
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


app = create_app(create_schema=False)
app.dependency_overrides[get_db] = override_get_db
