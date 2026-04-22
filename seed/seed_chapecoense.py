import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── CHAPECOENSE ─────────────────────────────────────
CHAPECOENSE_ID = 7

jogadores = [
    # GOLEIROS
    {"nome": "Anderson",            "number": 98, "posicao": "GOL"},
    {"nome": "Rafael Santos",       "number": 1,  "posicao": "GOL"},
    {"nome": "Matheus",             "number": 97,  "posicao": "GOL"},
    {"nome": "Kainã Correa Dal Magro", "number": 34, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Bruno Pacheco",                  "number": 91, "posicao": "LAT"},
    {"nome": "Rafael Thyere",                  "number": 15, "posicao": "ZAG"},
    {"nome": "Gustavo Talles",                 "number": 23, "posicao": "LAT"},
    {"nome": "Marcos Vinícius",                "number": 2,  "posicao": "LAT"},
    {"nome": "Eduardo Doma",                   "number": 3,  "posicao": "ZAG"},
    {"nome": "João Paulo",                     "number": 4,  "posicao": "ZAG"},
    {"nome": "Bruno Leonardo",                 "number": 33, "posicao": "ZAG"},
    {"nome": "Victor Caetano",                 "number": 25, "posicao": "ZAG"},
    {"nome": "Mancha",                         "number": 6,  "posicao": "LAT"},
    {"nome": "Kauan",                          "number": 21, "posicao": "ZAG"},
    {"nome": "Arthur Vanzela",                 "number": 16, "posicao": "ZAG"},
    {"nome": "Felipe Maciel de Salles",        "number": 19, "posicao": "ZAG"},
    {"nome": "Vinícius Eduardo de Almeida",    "number": 4,  "posicao": "ZAG"},
    {"nome": "Fernando Carlos da Silva Filho", "number": 14, "posicao": "LAT"},
    {"nome": "Eduardo Lopes Silva Gomes",      "number": 50, "posicao": "ZAG"},
    {"nome": "Everton",             "number": 26, "posicao": "LAT"},

    # MEIO-CAMPISTAS
    {"nome": "Camilo",              "number": 27, "posicao": "VOL"},
    {"nome": "Jean Carlos",         "number": 20, "posicao": "MEI"},
    {"nome": "Robert Santos",       "number": 8,  "posicao": "MEI"},
    {"nome": "Maurício Garcez",     "number": 31, "posicao": "MEI"},
    {"nome": "Walter Clar",         "number": 37, "posicao": "LAT"},
    {"nome": "Kevin Ramírez",       "number": 94, "posicao": "MEI"},
    {"nome": "Ênio",                "number": 97, "posicao": "MEI"},
    {"nome": "Higor Meritão",       "number": 22, "posicao": "VOL"},
    {"nome": "Vinicius Balieiro",   "number": 17, "posicao": "VOL"},
    {"nome": "Rafael Carvalheira",  "number": 99, "posicao": "VOL"},
    {"nome": "João Vitor",          "number": 5,  "posicao": "VOL"},
    {"nome": "Bruno Matias",        "number": 16, "posicao": "VOL"},
    {"nome": "Rubens Tadeu",        "number": 70, "posicao": "VOL"},
    {"nome": "David Antunes",       "number": 19, "posicao": "VOL"},
    {"nome": "Wemerson",            "number": 38, "posicao": "VOL"},
    {"nome": "Kauan Godoy Imperador","number": 16, "posicao": "VOL"},

    # ATACANTES
    {"nome": "Yannick Bolasie",             "number": 11, "posicao": "ATA"},
    {"nome": "Giovanni Augusto",            "number": 10, "posicao": "ATA"},
    {"nome": "Neto Pessoa",                 "number": 18, "posicao": "ATA"},
    {"nome": "Marcinho",                    "number": 7,  "posicao": "ATA"},
    {"nome": "Italo",                       "number": 77, "posicao": "ATA"},
    {"nome": "Wermeson",                    "number": 7,  "posicao": "ATA"},
    {"nome": "João Henrique Araújo Bom",    "number": 40, "posicao": "ATA"},
    {"nome": "Gleidson Lima dos Santos",    "number": 77, "posicao": "ATA"},
    {"nome": "Rodrigo Endrio",              "number": 23, "posicao": "ATA"},
    {"nome": "Bernardo Nicodem Grezel",     "number": 7,  "posicao": "ATA"},
    {"nome": "Kaíque Maciel",       "number": 15, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Chapecoense...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], CHAPECOENSE_ID)
    print("\nConcluído!")