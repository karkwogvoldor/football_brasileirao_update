import requests

BASE_URL = "https://footballbrasileiraoupdate-production.up.railway.app"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── FLAMENGO ────────────────────────────────────────
FLAMENGO_ID = 10

jogadores = [
    # GOLEIROS
    {"nome": "Agustín Rossi",    "number": 1,  "posicao": "GOL"},
    {"nome": "Andrew",           "number": 42, "posicao": "GOL"},
    {"nome": "Dyogo Alves",      "number": 49, "posicao": "GOL"},
    {"nome": "Leonardo Nannetti","number": 58, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Danilo",          "number": 13, "posicao": "ZAG"},
    {"nome": "Alex Sandro",     "number": 26, "posicao": "LAT"},
    {"nome": "Leo Pereira",     "number": 4,  "posicao": "ZAG"},
    {"nome": "Léo Ortiz",       "number": 3,  "posicao": "ZAG"},
    {"nome": "Emerson Royal",   "number": 22, "posicao": "LAT"},
    {"nome": "Guillermo Varela", "number": 2,  "posicao": "LAT"},
    {"nome": "Ayrton Lucas",    "number": 6,  "posicao": "LAT"},
    {"nome": "Vitão",           "number": 44, "posicao": "ZAG"},
    {"nome": "João Victor",     "number": 61, "posicao": "ZAG"},
    {"nome": "Daniel Sales",    "number": 51, "posicao": "LAT"},

    # MEIO-CAMPISTAS
    {"nome": "Giorgian de Arrascaeta", "number": 14, "posicao": "MEI"},
    {"nome": "Lucas Paquetá",          "number": 20, "posicao": "MEI"},
    {"nome": "Jorginho",               "number": 21, "posicao": "VOL"},
    {"nome": "Samuel Lino",            "number": 16, "posicao": "MEI"},
    {"nome": "Gonzalo Plata",          "number": 19, "posicao": "MEI"},
    {"nome": "Nicolás de la Cruz",     "number": 18, "posicao": "VOL"},
    {"nome": "Luiz Araújo",            "number": 7,  "posicao": "MEI"},
    {"nome": "Jorge Carrascal",        "number": 15, "posicao": "MEI"},
    {"nome": "Saul Niguez",            "number": 8,  "posicao": "VOL"},
    {"nome": "Erick Pulgar",           "number": 5,  "posicao": "VOL"},
    {"nome": "Everton",                "number": 11, "posicao": "MEI"},
    {"nome": "Evertton Araujo",        "number": 52, "posicao": "VOL"},
    {"nome": "Guilherme Gomes",        "number": 47, "posicao": "MEI"},
    {"nome": "Pablo Lucio",            "number": 56, "posicao": "VOL"},

    # ATACANTES
    {"nome": "Pedro",               "number": 9,  "posicao": "ATA"},
    {"nome": "Bruno Henrique",      "number": 27, "posicao": "ATA"},
    {"nome": "Wallace Yan",         "number": 64, "posicao": "ATA"},
    {"nome": "Douglas Costa Telles","number": 81, "posicao": "ATA"},
    {"nome": "Joao Camargo",        "number": 80, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Flamengo...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], FLAMENGO_ID)
    print("\nConcluído!")