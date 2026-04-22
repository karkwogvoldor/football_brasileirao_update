import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── FLUMINENSE ──────────────────────────────────────
FLUMINENSE_ID = 11

jogadores = [
    # GOLEIROS
    {"nome": "Fábio",             "number": 1,  "posicao": "GOL"},
    {"nome": "Marcelo Pitaluga",  "number": 27, "posicao": "GOL"},
    {"nome": "Vitor Eudes",       "number": 98, "posicao": "GOL"},
    {"nome": "Gustavo Ramalho",   "number": 50, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Guilherme Arana",            "number": 13, "posicao": "LAT"},
    {"nome": "Ignácio",                    "number": 4,  "posicao": "ZAG"},
    {"nome": "Samuel Xavier",              "number": 2,  "posicao": "LAT"},
    {"nome": "Rene",                       "number": 6,  "posicao": "LAT"},
    {"nome": "Juan Freytes",               "number": 22, "posicao": "ZAG"},
    {"nome": "Guga",                       "number": 23, "posicao": "LAT"},
    {"nome": "Igor Rabello",               "number": 21, "posicao": "ZAG"},
    {"nome": "Julián Millán",              "number": 29, "posicao": "ZAG"},
    {"nome": "Jemmes",                     "number": 3,  "posicao": "ZAG"},
    {"nome": "Júlio Fidelis",              "number": 46, "posicao": "LAT"},
    {"nome": "Davi Duarte",                "number": 40, "posicao": "ZAG"},
    {"nome": "João Loiola",                "number": 41, "posicao": "ZAG"},
    {"nome": "Wanderson Estrela Oliveira", "number": 6,  "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Yeferson Soteldo",   "number": 7,  "posicao": "MEI"},
    {"nome": "Jefferson Savarino", "number": 11, "posicao": "MEI"},
    {"nome": "Matheus Martinelli", "number": 8,  "posicao": "VOL"},
    {"nome": "Luciano Acosta",     "number": 32, "posicao": "MEI"},
    {"nome": "Kevin Serna",        "number": 90, "posicao": "MEI"},
    {"nome": "Agustín Canobbio",   "number": 17, "posicao": "MEI"},
    {"nome": "Ganso",              "number": 10, "posicao": "MEI"},
    {"nome": "Hércules",           "number": 35, "posicao": "VOL"},
    {"nome": "Alisson",            "number": 25, "posicao": "VOL"},
    {"nome": "Facundo Bernal",     "number": 5,  "posicao": "VOL"},
    {"nome": "Nonato",             "number": 16, "posicao": "VOL"},
    {"nome": "Riquelme Felipe",    "number": 28, "posicao": "MEI"},
    {"nome": "Otávio",             "number": 94, "posicao": "VOL"},
    {"nome": "David Terans",       "number": 80, "posicao": "MEI"},

    # ATACANTES
    {"nome": "Germán Cano",      "number": 14, "posicao": "ATA"},
    {"nome": "John Kennedy",     "number": 9,  "posicao": "ATA"},
    {"nome": "Rodrigo Castillo", "number": 19, "posicao": "ATA"},
    {"nome": "Matheus Reis",     "number": 15, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Fluminense...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], FLUMINENSE_ID)
    print("\nConcluído!")