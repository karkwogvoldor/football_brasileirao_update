import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── BAHIA ───────────────────────────────────────────
BAHIA_ID = 4

jogadores = [
    # GOLEIROS
    {"nome": "João Paulo",  "number": 34, "posicao": "GOL"},
    {"nome": "Ronaldo",     "number": 1,  "posicao": "GOL"},
    {"nome": "Leo Vieira",  "number": 22, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Luciano Juba",         "number": 46, "posicao": "LAT"},
    {"nome": "Santiago Ramos Mingo", "number": 21, "posicao": "ZAG"},
    {"nome": "Gilberto",             "number": 2,  "posicao": "LAT"},
    {"nome": "Gabriel Xavier",       "number": 3,  "posicao": "ZAG"},
    {"nome": "Kanu",                 "number": 4,  "posicao": "ZAG"},
    {"nome": "Luiz Gustavo",         "number": 43, "posicao": "ZAG"},
    {"nome": "Iago Borduchi",        "number": 25, "posicao": "LAT"},
    {"nome": "David Duarte",         "number": 33, "posicao": "ZAG"},
    {"nome": "Román Gómez",          "number": 31, "posicao": "LAT"},
    {"nome": "José Guilherme",       "number": 66, "posicao": "LAT"},

    # MEIO-CAMPISTAS
    {"nome": "Everton Ribeiro",  "number": 10, "posicao": "MEI"},
    {"nome": "Jean Lucas",       "number": 6,  "posicao": "VOL"},
    {"nome": "Rodrigo Nestor",   "number": 11, "posicao": "MEI"},
    {"nome": "Cristian Olivera", "number": 99, "posicao": "MEI"},
    {"nome": "Caio Alexandre",   "number": 8,  "posicao": "VOL"},
    {"nome": "Ruan Pablo",       "number": 52, "posicao": "MEI"},
    {"nome": "Michel Araújo",    "number": 15, "posicao": "MEI"},
    {"nome": "Nicolás Acevedo",  "number": 5,  "posicao": "VOL"},
    {"nome": "Erick",            "number": 14, "posicao": "VOL"},
    {"nome": "Mateo Sanabria",   "number": 23, "posicao": "MEI"},

    # ATACANTES
    {"nome": "Erick Pulga",   "number": 16, "posicao": "ATA"},
    {"nome": "Willian Jose",  "number": 12, "posicao": "ATA"},
    {"nome": "Dell",          "number": 89, "posicao": "ATA"},
    {"nome": "Everaldo",      "number": 27, "posicao": "ATA"},
    {"nome": "Ademir",        "number": 7,  "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Bahia...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], BAHIA_ID)
    print("\nConcluído!")