import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── GRÊMIO ──────────────────────────────────────────
GREMIO_ID = 12

jogadores = [
    # GOLEIROS
    {"nome": "Weverton",         "number": 1,  "posicao": "GOL"},
    {"nome": "Gabriel Grando",   "number": 12, "posicao": "GOL"},
    {"nome": "Thiago Beltrame",  "number": 24, "posicao": "GOL"},
    {"nome": "Gabriel Menegon",  "number": 31, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Erick Noriega",                    "number": 19, "posicao": "ZAG"},
    {"nome": "Marcos Rocha",                     "number": 14, "posicao": "LAT"},
    {"nome": "Walter Kannemann",                 "number": 4,  "posicao": "ZAG"},
    {"nome": "Marlon",                           "number": 23, "posicao": "LAT"},
    {"nome": "Fabian Balbuena",                  "number": 2,  "posicao": "ZAG"},
    {"nome": "Caio Paulista",                    "number": 38, "posicao": "LAT"},
    {"nome": "Wagner Leonardo",                  "number": 3,  "posicao": "ZAG"},
    {"nome": "Gustavo Martins",                  "number": 6,  "posicao": "ZAG"},
    {"nome": "João Pedro",                       "number": 18, "posicao": "LAT"},
    {"nome": "Viery",                            "number": 44, "posicao": "ZAG"},
    {"nome": "Luis Guedes",                      "number": 43, "posicao": "ZAG"},
    {"nome": "Vitor Ramon",                      "number": 32, "posicao": "LAT"},
    {"nome": "Pedro Gabriel Crisostomo Pinheiro","number": 54, "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Willian",           "number": 10, "posicao": "MEI"},
    {"nome": "Arthur",            "number": 8,  "posicao": "VOL"},
    {"nome": "Gabriel Mec",       "number": 37, "posicao": "MEI"},
    {"nome": "Mathias Villasanti","number": 20, "posicao": "VOL"},
    {"nome": "José Enamorado",    "number": 99, "posicao": "MEI"},
    {"nome": "Cristian Pavon",    "number": 7,  "posicao": "MEI"},
    {"nome": "Miguel Monsalve",   "number": 11, "posicao": "MEI"},
    {"nome": "Francis Amuzu",     "number": 9,  "posicao": "MEI"},
    {"nome": "Tiaguinho",         "number": 39, "posicao": "MEI"},
    {"nome": "Juan Nardoni",      "number": 5,  "posicao": "VOL"},
    {"nome": "Dodi",              "number": 17, "posicao": "VOL"},
    {"nome": "Riquelme Freitas",  "number": 65, "posicao": "MEI"},
    {"nome": "Roger",             "number": 47, "posicao": "MEI"},
    {"nome": "Leonel Pérez",      "number": 33, "posicao": "VOL"},
    {"nome": "Jefinho",           "number": 40, "posicao": "MEI"},
    {"nome": "Zortéa",            "number": 50, "posicao": "MEI"},

    # ATACANTES
    {"nome": "Carlos Vinícius",  "number": 95, "posicao": "ATA"},
    {"nome": "Martin Braithwaite","number": 22, "posicao": "ATA"},
    {"nome": "Tetê",             "number": 21, "posicao": "ATA"},
    {"nome": "André Henrique",   "number": 77, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Grêmio...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], GREMIO_ID)
    print("\nConcluído!")