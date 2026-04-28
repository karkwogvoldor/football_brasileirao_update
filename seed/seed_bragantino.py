import requests

BASE_URL = "https://footballbrasileiraoupdate-production.up.railway.app"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── BRAGANTINO ──────────────────────────────────────
BRAGANTINO_ID = 6

jogadores = [
    # GOLEIROS
    {"nome": "Tiago Volpi",      "number": 18, "posicao": "GOL"},
    {"nome": "Cleiton",          "number": 1,  "posicao": "GOL"},
    {"nome": "Fabrício",         "number": 37, "posicao": "GOL"},
    {"nome": "Gustavo Reis",     "number": 56, "posicao": "GOL"},
    {"nome": "Fernando Costa",   "number": 24, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Vanderlan",               "number": 6,  "posicao": "LAT"},
    {"nome": "Juninho Capixaba",        "number": 29, "posicao": "LAT"},
    {"nome": "José Andrés Hurtado",     "number": 34, "posicao": "LAT"},
    {"nome": "Guzmán Rodríguez",        "number": 2,  "posicao": "ZAG"},
    {"nome": "Pedro Henrique",          "number": 14, "posicao": "ZAG"},
    {"nome": "Gustavo Marques",         "number": 16, "posicao": "ZAG"},
    {"nome": "Alix Vinicius",           "number": 4,  "posicao": "ZAG"},
    {"nome": "Agustin Sant'Anna",       "number": 23, "posicao": "LAT"},
    {"nome": "Weimar Vivas Palacios",   "number": 54, "posicao": "LAT"},
    {"nome": "Eduardo Santos",          "number": 3,  "posicao": "ZAG"},
    {"nome": "Ryan Augusto",            "number": 52, "posicao": "LAT"},
    {"nome": "Cauê Nascimento Santos",  "number": 51, "posicao": "LAT"},

    # MEIO-CAMPISTAS
    {"nome": "Rodriguinho",       "number": 20, "posicao": "VOL"},
    {"nome": "Fabinho",           "number": 5,  "posicao": "VOL"},
    {"nome": "Lucas Barbosa",     "number": 21, "posicao": "MEI"},
    {"nome": "Matheus Fernandes", "number": 35, "posicao": "VOL"},
    {"nome": "Gabriel Girotto",   "number": 6,  "posicao": "VOL"},
    {"nome": "Ignacio Sosa",      "number": 15, "posicao": "VOL"},
    {"nome": "Bruno Praxedes",    "number": 25, "posicao": "MEI"},
    {"nome": "Eric Ramires",      "number": 7,  "posicao": "VOL"},
    {"nome": "Gustavo Neves",     "number": 22, "posicao": "VOL"},
    {"nome": "João Neto",         "number": 80, "posicao": "MEI"},
    {"nome": "Marcelinho Braz",   "number": 57, "posicao": "MEI"},
    {"nome": "Gabriel Lopes",     "number": 58, "posicao": "VOL"},

    # ATACANTES
    {"nome": "Isidro Pitta",              "number": 9,  "posicao": "ATA"},
    {"nome": "Eduardo Sasha",             "number": 8,  "posicao": "ATA"},
    {"nome": "Henry Mosquera",            "number": 30, "posicao": "ATA"},
    {"nome": "Fernando",                  "number": 11, "posicao": "ATA"},
    {"nome": "José Herrera",              "number": 32, "posicao": "ATA"},
    {"nome": "Vinicinho",                 "number": 17, "posicao": "ATA"},
    {"nome": "Bruno Goncalves De Jesus",  "number": 17, "posicao": "ATA"},
    {"nome": "Davi Gomes",                "number": 27, "posicao": "ATA"},
    {"nome": "Yuri Leles",                "number": 28, "posicao": "ATA"},
    {"nome": "Gabriel Novaes",            "number": 91, "posicao": "ATA"},
    {"nome": "Jhuan Nunes Coelho",        "number": 67, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Bragantino...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], BRAGANTINO_ID)
    print("\nConcluído!")