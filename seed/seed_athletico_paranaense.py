import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── ATHLETICO PARANAENSE ────────────────────────────
ATHLETICO_PARANAENSE_ID = 3

jogadores = [
    # GOLEIROS
    {"nome": "Santos",          "number": 23, "posicao": "GOL"},
    {"nome": "Mycael",          "number": 1,  "posicao": "GOL"},
    {"nome": "Matheus Soares",  "number": 42, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Gilberto Junior",      "number": 2,  "posicao": "LAT"},
    {"nome": "Lucas Esquivel",       "number": 37, "posicao": "LAT"},
    {"nome": "Leo Pinheiro",         "number": 3,  "posicao": "ZAG"},
    {"nome": "Arthur Dias",          "number": 4,  "posicao": "ZAG"},
    {"nome": "Juan Felipe Aguirre",  "number": 33, "posicao": "ZAG"},
    {"nome": "Carlos Terán",         "number": 22, "posicao": "ZAG"},
    {"nome": "Gastón Benavídez",     "number": 29, "posicao": "LAT"},
    {"nome": "Leonardo Derik",       "number": 6,  "posicao": "LAT"},
    {"nome": "Dudu",                 "number": 98, "posicao": "LAT"},
    {"nome": "Claudinho",            "number": 26, "posicao": "LAT"},

    # MEIO-CAMPISTAS
    {"nome": "Luiz Gustavo",      "number": 14, "posicao": "VOL"},
    {"nome": "Bruno Zapelli",     "number": 10, "posicao": "MEI"},
    {"nome": "Camilo Portilla",   "number": 27, "posicao": "VOL"},
    {"nome": "Stiven Mendoza",    "number": 7,  "posicao": "MEI"},
    {"nome": "João Cruz",         "number": 8,  "posicao": "VOL"},
    {"nome": "Dudu",              "number": 53, "posicao": "MEI"},
    {"nome": "Bruno Braga Ramos", "number": 48, "posicao": "MEI"},
    {"nome": "Jadson",            "number": 16, "posicao": "VOL"},
    {"nome": "Isaac",             "number": 11, "posicao": "MEI"},
    {"nome": "Felipinho",         "number": 5,  "posicao": "VOL"},
    {"nome": "Alejandro García",  "number": 20, "posicao": "MEI"},

    # ATACANTES
    {"nome": "Kevin Viveros",          "number": 9,  "posicao": "ATA"},
    {"nome": "Leozinho",               "number": 21, "posicao": "ATA"},
    {"nome": "Julimar",                "number": 20, "posicao": "ATA"},
    {"nome": "Renan Viana",            "number": 50, "posicao": "ATA"},
    {"nome": "Renan Peixoto Nepomuceno","number": 70, "posicao": "ATA"},
    {"nome": "Daniel Aguilar",         "number": 99,  "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Athletico Paranaense...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], ATHLETICO_PARANAENSE_ID)
    print("\nConcluído!")