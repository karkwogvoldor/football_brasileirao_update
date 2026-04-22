import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ─── CORINTHIANS (ID: 1) ──────────────────────────────

CORINTHIANS_ID = 1

jogadores = [
    # GOLEIROS
    {"nome": "Hugo Souza",      "number": 1,  "posicao": "GOL"},
    {"nome": "Matheus Donelli", "number": 32, "posicao": "GOL"},
    {"nome": "Felipe Longo",    "number": 40, "posicao": "GOL"},
    {"nome": "Kauê",            "number": 51, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Matheuzinho",        "number": 2,  "posicao": "LAT"},
    {"nome": "Matheus Bidu",       "number": 21, "posicao": "LAT"},
    {"nome": "Gustavo Henrique",   "number": 13, "posicao": "ZAG"},
    {"nome": "Gabriel Paulista",   "number": 3,  "posicao": "ZAG"},
    {"nome": "Andre Ramalho",      "number": 5,  "posicao": "ZAG"},
    {"nome": "Fabrizio Angileri",  "number": 26, "posicao": "LAT"},
    {"nome": "João Pedro Tchoca",  "number": 4,  "posicao": "ZAG"},
    {"nome": "Hugo",               "number": 46, "posicao": "LAT"},
    {"nome": "Pedro Milans",       "number": 20, "posicao": "LAT"},
    {"nome": "Renato Santos",      "number": 41, "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Rodrigo Garro",    "number": 8,  "posicao": "MEI"},
    {"nome": "Andre Carrillo",   "number": 19, "posicao": "MEI"},
    {"nome": "Breno Bidon",      "number": 7,  "posicao": "MEI"},
    {"nome": "Raniele",          "number": 14, "posicao": "VOL"},
    {"nome": "Allan",            "number": 29, "posicao": "VOL"},
    {"nome": "Matheus Pereira",  "number": 23, "posicao": "MEI"},
    {"nome": "Charles",          "number": 35, "posicao": "VOL"},
    {"nome": "André Luiz",       "number": 49, "posicao": "MEI"},
    {"nome": "Dieguinho",        "number": 61, "posicao": "MEI"},
    {"nome": "Alex Santana",     "number": 80, "posicao": "VOL"},
    {"nome": "Zakaria Labyad",   "number": 52, "posicao": "MEI"},

    # ATACANTES
    {"nome": "Memphis Depay",    "number": 10, "posicao": "SA"},
    {"nome": "Yuri Alberto",     "number": 9,  "posicao": "ATA"},
    {"nome": "Jesse Lingard",    "number": 77, "posicao": "PT"},
    {"nome": "Pedro Raul",       "number": 18, "posicao": "ATA"},
    {"nome": "Gui Negão",        "number": 56, "posicao": "ATA"},
    {"nome": "Vitinho",          "number": 11, "posicao": "PT"},
    {"nome": "Kayke Ferrari",    "number": 31, "posicao": "PT"},
    {"nome": "Kaio César",       "number": 37, "posicao": "PT"},
]

if __name__ == "__main__":
    print("Povoando Corinthians...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], CORINTHIANS_ID)
    print("\nConcluído!")