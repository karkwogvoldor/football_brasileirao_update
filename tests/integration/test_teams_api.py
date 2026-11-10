import pytest

import main


pytestmark = pytest.mark.integration


def create_team(client, nome="Time Teste", formacao="4-3-3"):
    response = client.post(
        "/times/",
        data={"nome": nome, "formacao": formacao},
    )
    assert response.status_code == 200
    return response.json()


# Verifica o ciclo completo de criação, leitura, atualização e exclusão de um time.
def test_team_crud_flow(client):
    created = create_team(client)
    team_id = created["id"]

    assert created == {
        "id": team_id,
        "nome": "Time Teste",
        "formacao": "4-3-3",
        "escudo": None,
        "foto_craque": None,
    }

    listed = client.get("/times/")
    assert listed.status_code == 200
    assert listed.json() == [created]

    fetched = client.get(f"/times/{team_id}")
    assert fetched.status_code == 200
    assert fetched.json() == created

    updated = client.patch(
        f"/times/{team_id}",
        data={"nome": "Time Atualizado", "formacao": "4-4-2"},
    )
    assert updated.status_code == 200
    assert updated.json()["nome"] == "Time Atualizado"
    assert updated.json()["formacao"] == "4-4-2"

    deleted = client.delete(f"/times/{team_id}")
    assert deleted.status_code == 204
    assert client.get(f"/times/{team_id}").status_code == 404


# Verifica se operações em um time inexistente retornam 404.
def test_team_not_found_returns_404(client):
    assert client.get("/times/999999").status_code == 404
    assert client.patch("/times/999999", data={"nome": "Ausente"}).status_code == 404
    assert client.delete("/times/999999").status_code == 404


# Verifica se um formato de imagem não permitido é rejeitado.
def test_invalid_team_image_is_rejected(client):
    response = client.post(
        "/times/",
        data={"nome": "Imagem Inválida"},
        files={"escudo": ("escudo.gif", b"GIF89a", "image/gif")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Formato de imagem inválido"}


# Verifica se imagens válidas passam pelo adaptador de upload e preservam suas URLs.
def test_valid_team_images_use_the_upload_adapter(client, monkeypatch):
    uploads = []

    def fake_upload(file, pasta):
        uploads.append((file.filename, pasta))
        return f"https://imagens.test/{pasta}/{file.filename}"

    monkeypatch.setattr(main, "upload_imagem", fake_upload)

    response = client.post(
        "/times/",
        data={"nome": "Time com Imagens", "formacao": "4-2-3-1"},
        files={
            "escudo": ("escudo.png", b"png", "image/png"),
            "foto_craque": ("craque.webp", b"webp", "image/webp"),
        },
    )

    assert response.status_code == 200
    assert uploads == [
        ("escudo.png", "brasileirao/escudos"),
        ("craque.webp", "brasileirao/craques"),
    ]
    assert response.json()["escudo"].endswith("/brasileirao/escudos/escudo.png")
    assert response.json()["foto_craque"].endswith(
        "/brasileirao/craques/craque.webp"
    )

