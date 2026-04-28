import requests

BASE_URL = "https://footballbrasileiraoupdate-production.up.railway.app"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── CORITIBA ────────────────────────────────────────
CORITIBA_ID = 8

jogadores = [
    # GOLEIROS
    {"nome": "Pedro Morisco",  "number": 1,  "posicao": "GOL"},
    {"nome": "Keiller",        "number": 13, "posicao": "GOL"},
    {"nome": "Pedro Rangel",   "number": 22, "posicao": "GOL"},
    {"nome": "Benassi",        "number": 67, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "João Pedro Chermont", "number": 44, "posicao": "LAT"},
    {"nome": "Thiago Santos",       "number": 21, "posicao": "ZAG"},
    {"nome": "Maicon",              "number": 3,  "posicao": "ZAG"},
    {"nome": "Felipe Jonatan",      "number": 6,  "posicao": "LAT"},
    {"nome": "Tinga",               "number": 2,  "posicao": "LAT"},
    {"nome": "Jacy Maranhão",       "number": 55, "posicao": "ZAG"},
    {"nome": "Rodrigo Moledo",      "number": 4,  "posicao": "ZAG"},
    {"nome": "Tiago Cóser",         "number": 23, "posicao": "ZAG"},
    {"nome": "Bruno Melo",          "number": 26, "posicao": "ZAG"},
    {"nome": "João Almeida",        "number": 16, "posicao": "LAT"},

    # MEIO-CAMPISTAS
    {"nome": "Josué",                  "number": 10, "posicao": "MEI"},
    {"nome": "Breno Lopes",            "number": 77, "posicao": "MEI"},
    {"nome": "Lucas Ronier",           "number": 11, "posicao": "MEI"},
    {"nome": "Joaquín Lavega",         "number": 7,  "posicao": "MEI"},
    {"nome": "Fernando Sobral",        "number": 88, "posicao": "VOL"},
    {"nome": "Sebastian Gomez",        "number": 19, "posicao": "VOL"},
    {"nome": "Willian Oliveira",       "number": 29, "posicao": "VOL"},
    {"nome": "Gustavo",                "number": 39, "posicao": "MEI"},
    {"nome": "Wallisson Luiz",         "number": 8,  "posicao": "VOL"},
    {"nome": "Vini Paulista",          "number": 36, "posicao": "VOL"},
    {"nome": "Alejandro Ararat Diaz",  "number": 5,  "posicao": "VOL"},

    # ATACANTES
    {"nome": "Rodrigo Rodrigues", "number": 99, "posicao": "ATA"},
    {"nome": "Keno",              "number": 20, "posicao": "ATA"},
    {"nome": "Pedro Rocha",       "number": 32, "posicao": "ATA"},
    {"nome": "Renato Marques",    "number": 78, "posicao": "ATA"},
    {"nome": "Fabinho",           "number": 28, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Coritiba...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], CORITIBA_ID)
    print("\nConcluído!")