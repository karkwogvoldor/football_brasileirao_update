import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ————— VITÓRIA —————————————————————————————————————————
VITORIA_ID = 20

jogadores = [
    # GOLEIROS
    {"nome": "Lucas Arcanjo", "number": 1, "posicao": "GOL"},
    {"nome": "Gabriel", "number": 22, "posicao": "GOL"},
    {"nome": "Alexandre Fintelman", "number": 35, "posicao": "GOL"},
    {"nome": "Yuri Sena", "number": 71, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Cacá", "number": 25, "posicao": "ZAG"},
    {"nome": "Ramon", "number": 13, "posicao": "LAT"},
    {"nome": "Luan Cândido", "number": 36, "posicao": "LAT"},
    {"nome": "Camutanga", "number": 4, "posicao": "ZAG"},
    {"nome": "Claudinho", "number": 2, "posicao": "LAT"},
    {"nome": "Jamerson", "number": 83, "posicao": "LAT"},
    {"nome": "Nathan Mendes", "number": 45, "posicao": "LAT"},
    {"nome": "Neris", "number": 77, "posicao": "ZAG"},
    {"nome": "Mateusinho", "number": 98, "posicao": "LAT"},
    {"nome": "Edu", "number": 43, "posicao": "ZAG"},
    {"nome": "Riccieli", "number": 5, "posicao": "ZAG"},
    {"nome": "Kauan", "number": 18, "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Matheuzinho", "number": 10, "posicao": "MEI"},
    {"nome": "Gabriel Baralhas", "number": 44, "posicao": "VOL"},
    {"nome": "Emmanuel Martínez", "number": 6, "posicao": "MEI"},
    {"nome": "Dudu", "number": 21, "posicao": "VOL"},
    {"nome": "Ronald", "number": 8, "posicao": "VOL"},
    {"nome": "Caique Gonçalves", "number": 95, "posicao": "VOL"},
    {"nome": "Zé Vitor", "number": 88, "posicao": "VOL"},
    {"nome": "Rúben Ramos Ismael", "number": 16, "posicao": "VOL"},
    {"nome": "Pablo Santos", "number": 62, "posicao": "MEI"},
    {"nome": "Edenilson", "number": 26, "posicao": "MEI"},
    {"nome": "Gustavo Blanco", "number": 50, "posicao": "VOL"},
    {"nome": "Anderson Bispo dos Santos", "number": 28, "posicao": "MEI"},
    {"nome": "Wendell Sacramento", "number": 41, "posicao": "VOL"},

    # ATACANTES
    {"nome": "Marinho", "number": 7, "posicao": "ATA"},
    {"nome": "Erick", "number": 33, "posicao": "ATA"},
    {"nome": "Renato Kayzer", "number": 79, "posicao": "ATA"},
    {"nome": "Aitor Cantalapiedra", "number": 17, "posicao": "ATA"},
    {"nome": "Pedro Henrique", "number": 9, "posicao": "ATA"},
    {"nome": "Fabrício Santos", "number": 23, "posicao": "ATA"},
    {"nome": "Renzo López", "number": 31, "posicao": "ATA"},
    {"nome": "Renê Sousa", "number": 91, "posicao": "ATA"},
    {"nome": "Luis Miguel", "number": 64, "posicao": "ATA"},
    {"nome": "Osvaldo", "number": 11, "posicao": "ATA"},
    {"nome": "Kike Saverio", "number": 19, "posicao": "ATA"},
    {"nome": "Lucas Braga", "number": 22, "posicao": "ATA"},
    {"nome": "Diego Tarzia", "number": 12, "posicao": "ATA"},
    {"nome": "Lucas Silva", "number": 20, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Vitória...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], VITORIA_ID)
    print("\nConcluído!")