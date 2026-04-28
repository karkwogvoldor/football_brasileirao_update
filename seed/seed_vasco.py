import requests

BASE_URL = "https://footballbrasileiraoupdate-production.up.railway.app"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ————— VASCO ———————————————————————————————————————————
VASCO_ID = 19

jogadores = [
    # GOLEIROS
    {"nome": "Léo Jardim", "number": 1, "posicao": "GOL"},
    {"nome": "Daniel Fuzato", "number": 13, "posicao": "GOL"},
    {"nome": "Pablo", "number": 37, "posicao": "GOL"},
    {"nome": "Phillipe Gabriel", "number": 40, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Paulo Henrique", "number": 96, "posicao": "LAT"},
    {"nome": "Carlos Cuesta", "number": 46, "posicao": "ZAG"},
    {"nome": "Lucas Piton", "number": 6, "posicao": "LAT"},
    {"nome": "Cuiabano", "number": 66, "posicao": "LAT"},
    {"nome": "Robert Renan", "number": 30, "posicao": "ZAG"},
    {"nome": "Puma Rodríguez", "number": 2, "posicao": "LAT"},
    {"nome": "Lucas Freitas", "number": 43, "posicao": "ZAG"},
    {"nome": "Alan Saldivia", "number": 4, "posicao": "ZAG"},
    {"nome": "Riquelme Avellar", "number": 82, "posicao": "LAT"},

    # MEIO-CAMPISTAS
    {"nome": "Cauan Barros", "number": 88, "posicao": "VOL"},
    {"nome": "Tchê Tchê", "number": 3, "posicao": "VOL"},
    {"nome": "Thiago Mendes", "number": 23, "posicao": "VOL"},
    {"nome": "Hugo Moura", "number": 25, "posicao": "VOL"},
    {"nome": "Jair", "number": 8, "posicao": "VOL"},
    {"nome": "JP", "number": 98, "posicao": "MEI"},
    {"nome": "Mateus Carvalho", "number": 85, "posicao": "VOL"},
    {"nome": "Lukas Zuccarello", "number": 86, "posicao": "MEI"},
    {"nome": "Lucas Eduardo", "number": 58, "posicao": "MEI"},
    {"nome": "Euder", "number": 70, "posicao": "MEI"},
    {"nome": "João Vitor Silva", "number": 60, "posicao": "MEI"},
    {"nome": "Samuel", "number": 67, "posicao": "MEI"},

    # ATACANTES
    {"nome": "Matheus França", "number": 9, "posicao": "ATA"},
    {"nome": "Brenner", "number": 20, "posicao": "ATA"},
    {"nome": "Claudio Spinelli", "number": 77, "posicao": "ATA"},
    {"nome": "David", "number": 7, "posicao": "ATA"},
    {"nome": "Adson", "number": 28, "posicao": "ATA"},
    {"nome": "Marino Hinestroza", "number": 18, "posicao": "ATA"},
    {"nome": "Andrés Gómez", "number": 11, "posicao": "ATA"},
    {"nome": "Nuno Moreira", "number": 17, "posicao": "ATA"},
    {"nome": "Johan Rojas", "number": 10, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Vasco...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], VASCO_ID)
    print("\nConcluído!")