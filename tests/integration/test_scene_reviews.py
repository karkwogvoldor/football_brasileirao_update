import json

import pytest

from brafoot.presentation.review_store import record_scene_return


@pytest.fixture
def review_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("BRAFOOT_DEV_REVIEW_DIR", str(tmp_path))
    return tmp_path


# Sem arquivos salvos, a API devolve revisões e retornos vazios.
def test_scene_reviews_start_empty(client, review_dir):
    response = client.get("/api/v1/dev/scene-reviews")

    assert response.status_code == 200
    assert response.json() == {"reviews": {}, "returns": {}}


# Revisões enviadas pelo navegador são gravadas em arquivo e relidas sem perdas.
def test_scene_reviews_are_persisted_and_reloaded(client, review_dir):
    reviews = {"cena-a@1": {"status": "changes_requested", "note": "Ajustar passe"}}

    saved = client.put("/api/v1/dev/scene-reviews", json={"reviews": reviews})

    assert saved.status_code == 200
    assert json.loads((review_dir / "scene-reviews.json").read_text("utf-8")) == reviews
    assert client.get("/api/v1/dev/scene-reviews").json()["reviews"] == reviews


# Um corpo sem o objeto "reviews" é recusado e nada é gravado.
def test_scene_reviews_reject_invalid_payload(client, review_dir):
    response = client.put("/api/v1/dev/scene-reviews", json={"reviews": []})

    assert response.status_code == 422
    assert not (review_dir / "scene-reviews.json").exists()


# O retorno de ajuste registrado fora do navegador aparece na API para a página azul.
def test_recorded_scene_return_is_served(client, review_dir):
    record_scene_return("cena-a", 1, 2, "Passe mais curto")

    returned = client.get("/api/v1/dev/scene-reviews").json()["returns"]["cena-a"]

    assert returned["from_version"] == 1
    assert returned["to_version"] == 2
    assert returned["summary"] == "Passe mais curto"


# Retornos com versão que não avança ou resumo vazio são rejeitados.
def test_record_scene_return_validates_input(review_dir):
    with pytest.raises(ValueError):
        record_scene_return("cena-a", 2, 2, "x")
    with pytest.raises(ValueError):
        record_scene_return("cena-a", 1, 2, "   ")


# A página sincroniza revisões com o servidor e exibe o resumo do ajuste devolvido.
def test_scene_lab_syncs_reviews_and_shows_returned_adjustments(client):
    page = client.get("/dev/cenas")
    script = client.get("/static/dev-cenas.js")

    assert 'id="returnSummary"' in page.text
    assert "/api/v1/dev/scene-reviews" in script.text
    assert "function returnedAdjustment(" in script.text
    assert "function syncReviewsToServer()" in script.text
