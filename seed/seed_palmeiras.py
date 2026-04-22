import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── PALMEIRAS ───────────────────────────────────────
PALMEIRAS_ID = 15

jogadores = [
    # GOLEIROS
    {"nome": "Carlos Miguel",  "number": 1,  "posicao": "GOL"},
    {"nome": "Marcelo Lomba",  "number": 14, "posicao": "GOL"},
    {"nome": "Aranha",         "number": 24, "posicao": "GOL"},
    {"nome": "Luiz Sá",        "number": 51, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Gustavo Gomez",    "number": 15, "posicao": "ZAG"},
    {"nome": "Joaquín Piquerez", "number": 22, "posicao": "LAT"},
    {"nome": "Agustín Giay",     "number": 4,  "posicao": "LAT"},
    {"nome": "Murilo",           "number": 26, "posicao": "ZAG"},
    {"nome": "Bruno Fuchs",      "number": 3,  "posicao": "ZAG"},
    {"nome": "Luis Benedetti",   "number": 43, "posicao": "ZAG"},
    {"nome": "Khellven",         "number": 12, "posicao": "LAT"},
    {"nome": "Jefté",            "number": 6,  "posicao": "LAT"},
    {"nome": "Arthur Gabriel",   "number": 56, "posicao": "LAT"},
    {"nome": "Kauã",             "number": 0,  "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Jhon Arias",        "number": 11, "posicao": "MEI"},
    {"nome": "Andreas Pereira",   "number": 8,  "posicao": "MEI"},
    {"nome": "Mauricio",          "number": 18, "posicao": "MEI"},
    {"nome": "Felipe Anderson",   "number": 7,  "posicao": "MEI"},
    {"nome": "Allan",             "number": 40, "posicao": "VOL"},
    {"nome": "Emiliano Martínez", "number": 32, "posicao": "VOL"},
    {"nome": "Marlon Freitas",    "number": 17, "posicao": "VOL"},
    {"nome": "Lucas Evangelista", "number": 30, "posicao": "VOL"},
    {"nome": "Vitor Figueiredo",  "number": 38, "posicao": "MEI"},
    {"nome": "Luis Pacheco",      "number": 50, "posicao": "VOL"},
    {"nome": "Larson",            "number": 48, "posicao": "VOL"},

    # ATACANTES
    {"nome": "Vitor Roque",  "number": 9,  "posicao": "ATA"},
    {"nome": "José López",   "number": 42, "posicao": "ATA"},
    {"nome": "Paulinho",     "number": 10, "posicao": "ATA"},
    {"nome": "Ramón Sosa",   "number": 19, "posicao": "ATA"},
    {"nome": "Luighi Hanri", "number": 31, "posicao": "ATA"},
    {"nome": "Erick Belé",   "number": 45, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Palmeiras...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], PALMEIRAS_ID)
    print("\nConcluído!")