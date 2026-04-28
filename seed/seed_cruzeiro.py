import requests

BASE_URL = "https://footballbrasileiraoupdate-production.up.railway.app"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── CRUZEIRO ────────────────────────────────────────
CRUZEIRO_ID = 9

jogadores = [
    # GOLEIROS
    {"nome": "Matheus Cunha",  "number": 31, "posicao": "GOL"},
    {"nome": "Cássio",         "number": 1,  "posicao": "GOL"},
    {"nome": "Otávio Costa",   "number": 81, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Fabrício Bruno",   "number": 15, "posicao": "ZAG"},
    {"nome": "Fagner",           "number": 23, "posicao": "LAT"},
    {"nome": "Kaiki",            "number": 6,  "posicao": "LAT"},
    {"nome": "William",          "number": 12, "posicao": "LAT"},
    {"nome": "Lucas Villalba",   "number": 25, "posicao": "ZAG"},
    {"nome": "Kauã Prates",      "number": 36, "posicao": "LAT"},
    {"nome": "João Marcelo",     "number": 43, "posicao": "ZAG"},
    {"nome": "Jonathan Jesus",   "number": 34, "posicao": "ZAG"},
    {"nome": "Kauã Moraes",      "number": 2,  "posicao": "LAT"},
    {"nome": "Janderson",        "number": 33, "posicao": "ZAG"},
    {"nome": "Bruno Alves",      "number": 44, "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Gerson",              "number": 11, "posicao": "VOL"},
    {"nome": "Matheus Pereira",     "number": 10, "posicao": "MEI"},
    {"nome": "Keny Arroyo",         "number": 99, "posicao": "MEI"},
    {"nome": "Marquinhos",          "number": 7,  "posicao": "MEI"},
    {"nome": "Matheus Henrique",    "number": 8,  "posicao": "VOL"},
    {"nome": "Lucas Romero",        "number": 29, "posicao": "VOL"},
    {"nome": "Lucas Silva",         "number": 16, "posicao": "VOL"},
    {"nome": "Christian",           "number": 88, "posicao": "MEI"},
    {"nome": "Wanderson",           "number": 94, "posicao": "MEI"},
    {"nome": "Walace",              "number": 5,  "posicao": "VOL"},
    {"nome": "Kaique Kenji",        "number": 70, "posicao": "MEI"},
    {"nome": "Japa",                "number": 77, "posicao": "VOL"},
    {"nome": "Murilo Rhikman",      "number": 35, "posicao": "VOL"},
    {"nome": "Henrique Dal Ré Lemos","number": 10, "posicao": "MEI"},
    {"nome": "Rayan Lelis",         "number": 57, "posicao": "MEI"},

    # ATACANTES
    {"nome": "Kaio Jorge",        "number": 19, "posicao": "ATA"},
    {"nome": "Luis Sinisterra",   "number": 17, "posicao": "ATA"},
    {"nome": "Neyser Villarreal", "number": 22, "posicao": "ATA"},
    {"nome": "Bruno Rodrigues",   "number": 9,  "posicao": "ATA"},
    {"nome": "Chico da Costa",    "number": 91, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Cruzeiro...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], CRUZEIRO_ID)
    print("\nConcluído!")