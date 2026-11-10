import models
from brafoot.catalog.importer import import_brasileirao_2026, load_fixture_payload


def create_legacy_teams(db_session):
    payload = load_fixture_payload()
    for club_name in payload["clubs"]:
        db_session.add(models.Team(nome=club_name, formacao="4-3-3"))
    db_session.commit()


# Importa o catálogo duas vezes sem duplicar clubes, temporada ou partidas.
def test_catalog_import_is_idempotent(db_session):
    create_legacy_teams(db_session)

    first_season = import_brasileirao_2026(db_session)
    second_season = import_brasileirao_2026(db_session)

    assert first_season.id == second_season.id
    assert db_session.query(models.Competition).count() == 1
    assert db_session.query(models.Season).count() == 1
    assert db_session.query(models.Club).count() == 20
    assert db_session.query(models.Fixture).count() == 380


# Preserva o vínculo entre os clubes do catálogo e os times da galeria legada.
def test_catalog_clubs_map_to_every_legacy_team(db_session):
    create_legacy_teams(db_session)

    import_brasileirao_2026(db_session)

    assert db_session.query(models.Club).filter_by(legacy_team_id=None).count() == 0
    assert {club.legacy_team.nome for club in db_session.query(models.Club).all()} == {
        team.nome for team in db_session.query(models.Team).all()
    }
