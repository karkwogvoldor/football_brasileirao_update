import pytest


pytestmark = pytest.mark.integration


def create_team(client):
    response = client.post(
        "/times/",
        data={"nome": "Clube do Jogador", "formacao": "4-3-3"},
    )
    assert response.status_code == 200
    return response.json()


# Verifica o ciclo completo de criação, leitura, atualização e exclusão de um jogador.
def test_player_crud_flow(client):
    team = create_team(client)
    payload = {
        "nome": "Jogador Teste",
        "number": 9,
        "posicao": "ATA",
        "team_id": team["id"],
    }

    created_response = client.post("/jogadores/", json=payload)
    assert created_response.status_code == 200
    created = created_response.json()
    player_id = created["id"]
    assert created == {"id": player_id, **payload}

    listed = client.get("/jogadores/")
    assert listed.status_code == 200
    assert listed.json() == [created]

    fetched = client.get(f"/jogadores/{player_id}")
    assert fetched.status_code == 200
    assert fetched.json() == created

    updated = client.patch(
        f"/jogadores/{player_id}",
        json={"number": 10, "posicao": "MEI"},
    )
    assert updated.status_code == 200
    assert updated.json()["number"] == 10
    assert updated.json()["posicao"] == "MEI"

    deleted = client.delete(f"/jogadores/{player_id}")
    assert deleted.status_code == 204
    assert client.get(f"/jogadores/{player_id}").status_code == 404


# Verifica se uma posição de jogador fora do domínio permitido é rejeitada.
def test_invalid_player_position_is_rejected(client):
    response = client.post(
        "/jogadores/",
        json={"nome": "Posição Inválida", "number": 7, "posicao": "XYZ"},
    )

    assert response.status_code == 422


# Verifica se operações em um jogador inexistente retornam 404.
def test_player_not_found_returns_404(client):
    assert client.get("/jogadores/999999").status_code == 404
    assert client.patch("/jogadores/999999", json={"number": 8}).status_code == 404
    assert client.delete("/jogadores/999999").status_code == 404

