import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── INTERNACIONAL ───────────────────────────────────
INTERNACIONAL_ID = 13

jogadores = [
    # GOLEIROS
    {"nome": "Sergio Rochet", "number": 1,  "posicao": "GOL"},
    {"nome": "Anthoni",       "number": 12, "posicao": "GOL"},
    {"nome": "Kauan",         "number": 22, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Félix Torres",             "number": 4,  "posicao": "ZAG"},
    {"nome": "Alexandro Bernabei",       "number": 26, "posicao": "LAT"},
    {"nome": "Gabriel Mercado",          "number": 25, "posicao": "ZAG"},
    {"nome": "Bruno Gomes",              "number": 15, "posicao": "LAT"},
    {"nome": "Victor Gabriel",           "number": 41, "posicao": "ZAG"},
    {"nome": "Braian Aguirre",           "number": 35, "posicao": "LAT"},
    {"nome": "Matheus Bahia",            "number": 6,  "posicao": "LAT"},
    {"nome": "Juninho",                  "number": 18, "posicao": "ZAG"},
    {"nome": "Clayton Sampaio",          "number": 20, "posicao": "ZAG"},
    {"nome": "Esley Ezequiel dos Reis",  "number": 4,  "posicao": "ZAG"},
    {"nome": "Alisson Rodrigues de Melo", "number": 30, "posicao": "LAT"},

    # MEIO-CAMPISTAS
    {"nome": "Alan Patrick",              "number": 10, "posicao": "MEI"},
    {"nome": "Kayky",                     "number": 11, "posicao": "MEI"},
    {"nome": "Paulinho Paula",            "number": 27, "posicao": "MEI"},
    {"nome": "Thiago Maia",               "number": 29, "posicao": "VOL"},
    {"nome": "Bruno Tabata",              "number": 17, "posicao": "MEI"},
    {"nome": "Vitinho",                   "number": 28, "posicao": "MEI"},
    {"nome": "Bruno Henrique",            "number": 8,  "posicao": "VOL"},
    {"nome": "Rodrigo Villagra",          "number": 5,  "posicao": "VOL"},
    {"nome": "Ronaldo",                   "number": 16, "posicao": "VOL"},
    {"nome": "Alan Rodríguez",            "number": 14, "posicao": "VOL"},
    {"nome": "Richard",                   "number": 36, "posicao": "VOL"},
    {"nome": "Yago Noal",                 "number": 37, "posicao": "MEI"},
    {"nome": "Allex",                     "number": 31, "posicao": "ATA"},
    {"nome": "Benjamin Arhin",            "number": 33, "posicao": "VOL"},


    # ATACANTES
    {"nome": "Rafael Borré",              "number": 19, "posicao": "ATA"},
    {"nome": "Johan Carbonero",           "number": 7,  "posicao": "ATA"},
    {"nome": "Alerrandro",                "number": 9,  "posicao": "ATA"},
    {"nome": "Raykkonen Pereira Soares",  "number": 48, "posicao": "ATA"},
    {"nome": "Lucca Drummond",            "number": 48, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Internacional...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], INTERNACIONAL_ID)
    print("\nConcluído!")