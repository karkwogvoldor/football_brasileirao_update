import models
from brafoot.catalog.seeder import seed_brasileirao_2026
from seed_all import validate_local_seed_url


# Bloqueia o seed quando a URL aponta para um host remoto.
def test_seed_rejects_remote_database_url():
    try:
        validate_local_seed_url("postgresql://user:password@example.com/brafoot")
    except RuntimeError as error:
        assert "banco local" in str(error)
    else:
        raise AssertionError("O seed deveria recusar um banco remoto")


# Reexecuta todos os seeds locais sem duplicar times, jogadores ou calendário.
def test_local_seed_is_idempotent(db_session):
    seed_brasileirao_2026(db_session)
    first_counts = (
        db_session.query(models.Team).count(),
        db_session.query(models.Jogador).count(),
        db_session.query(models.Fixture).count(),
    )

    seed_brasileirao_2026(db_session)
    second_counts = (
        db_session.query(models.Team).count(),
        db_session.query(models.Jogador).count(),
        db_session.query(models.Fixture).count(),
    )

    assert first_counts == second_counts
    assert first_counts[0] == 20
    assert first_counts[1] > 400
    assert first_counts[2] == 380
