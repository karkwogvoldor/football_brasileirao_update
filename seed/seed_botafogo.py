import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── BOTAFOGO ────────────────────────────────────────
BOTAFOGO_ID = 5

jogadores = [
    # GOLEIROS
    {"nome": "Neto",           "number": 22, "posicao": "GOL"},
    {"nome": "Léo Linck",      "number": 24, "posicao": "GOL"},
    {"nome": "Cristhian Loor", "number": 40, "posicao": "GOL"},
    {"nome": "Raul",           "number": 1,  "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Alex Telles",       "number": 13, "posicao": "LAT"},
    {"nome": "Vitinho",           "number": 2,  "posicao": "LAT"},
    {"nome": "Nahuel Ferraresi",  "number": 5,  "posicao": "ZAG"},
    {"nome": "Bastos",            "number": 15, "posicao": "ZAG"},
    {"nome": "Alexander Barboza", "number": 20, "posicao": "ZAG"},
    {"nome": "Mateo Ponte",       "number": 4,  "posicao": "LAT"},
    {"nome": "Marcal",            "number": 21, "posicao": "LAT"},
    {"nome": "Kaio Pantaleão",    "number": 31, "posicao": "ZAG"},
    {"nome": "Jhoan Hernandez",   "number": 67, "posicao": "LAT"},
    {"nome": "Kadu Santos",       "number": 42, "posicao": "LAT"},
    {"nome": "Caio Roque",        "number": 27, "posicao": "LAT"},
    {"nome": "Ythallo",           "number": 3,  "posicao": "ZAG"},
    {"nome": "Gabriel Justino",   "number": 34, "posicao": "ZAG"},
    {"nome": "Kawan Thomaz",      "number": 54, "posicao": "ZAG"},
    {"nome": "Kauã Branco",       "number": 53, "posicao": "ZAG"},
    {"nome": "Anthony",           "number": 13, "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Danilo",           "number": 8,  "posicao": "VOL"},
    {"nome": "Álvaro Montoro",   "number": 10, "posicao": "MEI"},
    {"nome": "Allan",            "number": 25, "posicao": "VOL"},
    {"nome": "Jordan Barrera",   "number": 14, "posicao": "MEI"},
    {"nome": "Cristian Medina",  "number": 6,  "posicao": "MEI"},
    {"nome": "Santiago Rodríguez","number": 23, "posicao": "MEI"},
    {"nome": "Edenilson",        "number": 88, "posicao": "MEI"},
    {"nome": "Newton",           "number": 28, "posicao": "VOL"},
    {"nome": "Lucas Villalba",   "number": 77, "posicao": "MEI"},
    {"nome": "Wallace Davi",     "number": 55, "posicao": "VOL"},
    {"nome": "Kauan Toledo",     "number": 59, "posicao": "MEI"},
    {"nome": "Huguinho",         "number": 75, "posicao": "LAT"},
    {"nome": "Caio Valle",       "number": 45, "posicao": "VOL"},
    {"nome": "Bernardo Valim",   "number": 80, "posicao": "VOL"},

    # ATACANTES
    {"nome": "Joaquin Correa",   "number": 30, "posicao": "ATA"},
    {"nome": "Arthur Cabral",    "number": 19, "posicao": "ATA"},
    {"nome": "Júnior Santos",    "number": 7,  "posicao": "ATA"},
    {"nome": "Matheus Martins",  "number": 11, "posicao": "ATA"},
    {"nome": "Kadir Barría",     "number": 37, "posicao": "ATA"},
    {"nome": "Chris Ramos",      "number": 9,  "posicao": "ATA"},
    {"nome": "Nathan Fernandes", "number": 16, "posicao": "ATA"},
    {"nome": "Arthur Izaque",    "number": 39, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Botafogo...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], BOTAFOGO_ID)
    print("\nConcluído!")