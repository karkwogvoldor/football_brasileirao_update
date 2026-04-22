import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ————— SÃO PAULO ———————————————————————————————————————
SAO_PAULO_ID = 18

jogadores = [
    # GOLEIROS
    {"nome": "Rafael", "number": 23, "posicao": "GOL"},
    {"nome": "Young", "number": 50, "posicao": "GOL"},
    {"nome": "Carlos Coronel", "number": 31, "posicao": "GOL"},
    {"nome": "Felipe Gabriel Preis", "number": 52, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Robert Arboleda", "number": 5, "posicao": "ZAG"},
    {"nome": "Wendell", "number": 18, "posicao": "LAT"},
    {"nome": "Alan Franco", "number": 28, "posicao": "ZAG"},
    {"nome": "Enzo Díaz", "number": 13, "posicao": "LAT"},
    {"nome": "Rafael Tolói", "number": 2, "posicao": "ZAG"},
    {"nome": "Sabino", "number": 35, "posicao": "ZAG"},
    {"nome": "Maik", "number": 42, "posicao": "LAT"},
    {"nome": "Moreira", "number": 15, "posicao": "LAT"},
    {"nome": "Lucas Ramon", "number": 19, "posicao": "LAT"},
    {"nome": "Igor Felisberto", "number": 40, "posicao": "LAT"},
    {"nome": "Matheus Belém", "number": 15, "posicao": "ZAG"},
    {"nome": "Doria", "number": 4, "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Marcos Antônio", "number": 8, "posicao": "VOL"},
    {"nome": "Cauly", "number": 80, "posicao": "MEI"},
    {"nome": "Damián Bobadilla", "number": 16, "posicao": "VOL"},
    {"nome": "Pablo Maia", "number": 29, "posicao": "VOL"},
    {"nome": "Luan Santos", "number": 33, "posicao": "VOL"},
    {"nome": "Cédric Soares", "number": 21, "posicao": "LAT"},
    {"nome": "Lucca", "number": 45, "posicao": "MEI"},
    {"nome": "Danielzinho", "number": 94, "posicao": "VOL"},
    {"nome": "Felipe Negrucci", "number": 30, "posicao": "VOL"},
    {"nome": "Tetê", "number": 34, "posicao": "MEI"},
    {"nome": "Djhordney Ferreira", "number": 48, "posicao": "MEI"},
    {"nome": "Hugo Leonardo", "number": 38, "posicao": "MEI"},

    # ATACANTES
    {"nome": "Lucas Moura", "number": 7, "posicao": "ATA"},
    {"nome": "Jonathan Calleri", "number": 9, "posicao": "ATA"},
    {"nome": "Luciano", "number": 10, "posicao": "ATA"},
    {"nome": "Gonzalo Tapia", "number": 14, "posicao": "ATA"},
    {"nome": "André Silva", "number": 17, "posicao": "ATA"},
    {"nome": "Paulo Sérgio", "number": 39, "posicao": "ATA"},
    {"nome": "Ferreirinha", "number": 11, "posicao": "ATA"},
    {"nome": "Artur", "number": 37, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando São Paulo...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], SAO_PAULO_ID)
    print("\nConcluído!")