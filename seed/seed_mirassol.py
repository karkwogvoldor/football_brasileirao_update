import requests

BASE_URL = "https://footballbrasileiraoupdate-production.up.railway.app"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── MIRASSOL ────────────────────────────────────────
MIRASSOL_ID = 14

jogadores = [
    # GOLEIROS
    {"nome": "Walter",      "number": 22, "posicao": "GOL"},
    {"nome": "Alex Muralha","number": 23, "posicao": "GOL"},
    {"nome": "Thomazella",  "number": 90, "posicao": "GOL"},
    {"nome": "Georgemy",    "number": 95, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Reinaldo",         "number": 6,  "posicao": "LAT"},
    {"nome": "Victor Luis",      "number": 12, "posicao": "LAT"},
    {"nome": "Willian Machado",  "number": 3,  "posicao": "ZAG"},
    {"nome": "Igor Formiga",     "number": 32, "posicao": "LAT"},
    {"nome": "Igor Cariús",      "number": 16, "posicao": "LAT"},
    {"nome": "João Victor",      "number": 34, "posicao": "ZAG"},
    {"nome": "Rodrigues",        "number": 97, "posicao": "ZAG"},
    {"nome": "Daniel Borges",    "number": 20, "posicao": "LAT"},
    {"nome": "Wesley Santos",    "number": 20, "posicao": "LAT"},
    {"nome": "Lucas Oliveira","number": 2,  "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Eduardo",       "number": 21, "posicao": "MEI"},
    {"nome": "Antonio Galeano","number": 27, "posicao": "MEI"},
    {"nome": "Chico",         "number": 10, "posicao": "MEI"},
    {"nome": "Lucas Mugni",   "number": 26, "posicao": "MEI"},
    {"nome": "Gabriel Pires", "number": 18, "posicao": "VOL"},
    {"nome": "Shaylon",       "number": 7,  "posicao": "MEI"},
    {"nome": "Denilson",      "number": 8,  "posicao": "VOL"},
    {"nome": "Neto Moura",    "number": 25, "posicao": "VOL"},
    {"nome": "José Aldo",     "number": 21, "posicao": "VOL"},
    {"nome": "Yuri Lara",     "number": 5,  "posicao": "VOL"},
    {"nome": "Luiz Filipe",   "number": 23, "posicao": "MEI"},

    # ATACANTES
    {"nome": "Tiquinho Soares", "number": 29, "posicao": "ATA"},
    {"nome": "Negueba",         "number": 11, "posicao": "ATA"},
    {"nome": "André Luis",      "number": 99, "posicao": "ATA"},
    {"nome": "Alesson",         "number": 77, "posicao": "ATA"},
    {"nome": "Carlos Eduardo",  "number": 96, "posicao": "ATA"},
    {"nome": "Everton Galdino", "number": 17, "posicao": "ATA"},
    {"nome": "Nathan Fogaça",   "number": 9,  "posicao": "ATA"},
    {"nome": "Edson Carioca",   "number": 95, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Mirassol...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], MIRASSOL_ID)
    print("\nConcluído!")