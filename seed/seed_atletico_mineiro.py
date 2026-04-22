import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── ATLÉTICO MINEIRO ────────────────────────────────
ATLETICO_MINEIRO_ID = 2  # ← confirma o ID no seu banco!

jogadores = [
    # GOLEIROS
    {"nome": "Everson",                "number": 22, "posicao": "GOL"},
    {"nome": "Gabriel Delfim",         "number": 1,  "posicao": "GOL"},
    {"nome": "Robert Alves",           "number": 31, "posicao": "GOL"},
    {"nome": "Pedro Cobra Rodrigues",  "number": 99,  "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Renan Lodi",         "number": 16, "posicao": "LAT"},
    {"nome": "Lyanco",             "number": 13, "posicao": "ZAG"},
    {"nome": "Iván Román",         "number": 23, "posicao": "ZAG"},
    {"nome": "Junior Alonso",      "number": 6,  "posicao": "ZAG"},
    {"nome": "Ruan",               "number": 4,  "posicao": "ZAG"},
    {"nome": "Natanael",           "number": 2,  "posicao": "LAT"},
    {"nome": "Vitor Hugo",         "number": 14, "posicao": "ZAG"},
    {"nome": "Vitão",              "number": 40, "posicao": "ZAG"},
    {"nome": "Kauã Pascini",       "number": 36, "posicao": "LAT"},
    {"nome": "Samuel Lima Barros", "number": 15, "posicao": "ZAG"},
    {"nome": "Luis Gustavo",       "number": 32, "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Reinier",         "number": 19, "posicao": "MEI"},
    {"nome": "Gustavo Scarpa",  "number": 10, "posicao": "MEI"},
    {"nome": "Victor Hugo",     "number": 30, "posicao": "VOL"},
    {"nome": "Maycon",          "number": 8,  "posicao": "VOL"},
    {"nome": "Alan Franco",     "number": 21, "posicao": "VOL"},
    {"nome": "Ángelo Preciado", "number": 23, "posicao": "MEI"},
    {"nome": "Bernard",         "number": 11, "posicao": "MEI"},
    {"nome": "Tomás Cuello",    "number": 28, "posicao": "MEI"},
    {"nome": "Alexsander",      "number": 5,  "posicao": "VOL"},
    {"nome": "Tomás Pérez",     "number": 25, "posicao": "VOL"},
    {"nome": "Igor Gomes",      "number": 17, "posicao": "VOL"},
    {"nome": "Patrick",         "number": 20, "posicao": "VOL"},
    {"nome": "Mamady Cissé",    "number": 39, "posicao": "MEI"},
    {"nome": "Mateus Iseppe",   "number": 48, "posicao": "MEI"},
    {"nome": "Índio",           "number": 38, "posicao": "VOL"},
    {"nome": "Igor Toledo",     "number": 35, "posicao": "VOL"},

    # ATACANTES
    {"nome": "Hulk",           "number": 7,  "posicao": "ATA"},
    {"nome": "Dudu",           "number": 92, "posicao": "ATA"},
    {"nome": "Alan Minda",     "number": 11, "posicao": "ATA"},
    {"nome": "Mateo Cassierra","number": 9,  "posicao": "ATA"},
    {"nome": "Cauã Soares",    "number": 29, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Atlético Mineiro...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], ATLETICO_MINEIRO_ID)
    print("\nConcluído!")