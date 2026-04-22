import requests

BASE_URL = "http://localhost:8000"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ————— SANTOS ———————————————————————————————————————————
SANTOS_ID = 17

jogadores = [
    # GOLEIROS
    {"nome": "Gabriel Brazão", "number": 77, "posicao": "GOL"},
    {"nome": "João Pedro", "number": 79, "posicao": "GOL"},
    {"nome": "Diogenes", "number": 1, "posicao": "GOL"},
    {"nome": "Rodrigo Falcão", "number": 67, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "Mayke", "number": 12, "posicao": "LAT"},
    {"nome": "Igor Vinícius", "number": 18, "posicao": "LAT"},
    {"nome": "Zé Ivaldo", "number": 2, "posicao": "ZAG"},
    {"nome": "Lucas Veríssimo", "number": 4, "posicao": "ZAG"},
    {"nome": "Gonzalo Escobar", "number": 31, "posicao": "LAT"},
    {"nome": "Luan Peres", "number": 14, "posicao": "ZAG"},
    {"nome": "Vinicius Rodrigues Lira", "number": 3, "posicao": "LAT"},
    {"nome": "Adonis Frías", "number": 98, "posicao": "ZAG"},
    {"nome": "Alex Nascimento", "number": 2, "posicao": "ZAG"},
    {"nome": "Rafael Gonzaga", "number": 38, "posicao": "LAT"},
    {"nome": "João Paulo Ananias", "number": 23, "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Gabriel Menino", "number": 25, "posicao": "VOL"},
    {"nome": "Tomás Rincón", "number": 8, "posicao": "VOL"},
    {"nome": "Ze Rafael", "number": 6, "posicao": "VOL"},
    {"nome": "Willian Arao", "number": 15, "posicao": "VOL"},
    {"nome": "Gabriel Bontempo", "number": 49, "posicao": "MEI"},
    {"nome": "Joao Schmidt", "number": 5, "posicao": "VOL"},
    {"nome": "Christian Oliva", "number": 28, "posicao": "VOL"},
    {"nome": "Gustavo Henrique Pereira", "number": 48, "posicao": "MEI"},
    {"nome": "Robinho Júnior", "number": 7, "posicao": "MEI"},

    # ATACANTES
    {"nome": "Neymar", "number": 10, "posicao": "ATA"},
    {"nome": "Gabriel Barbosa", "number": 9, "posicao": "ATA"},
    {"nome": "Rony", "number": 33, "posicao": "ATA"},
    {"nome": "Lautaro Díaz", "number": 19, "posicao": "ATA"},
    {"nome": "Moisés", "number": 21, "posicao": "ATA"},
    {"nome": "Rafael Freitas", "number": 45, "posicao": "ATA"},
    {"nome": "Miguelito", "number": 30, "posicao": "ATA"},
    {"nome": "Benjamín Rollheiser", "number": 32, "posicao": "ATA"},
    {"nome": "Álvaro Barreal", "number": 22, "posicao": "ATA"},
    {"nome": "Thaciano", "number": 16, "posicao": "ATA"},
    {"nome": "Mateus Xavier de Sousa", "number": 47, "posicao": "ATA"},
    {"nome": "Nadson", "number": 57, "posicao": "ATA"},
    {"nome": "Enzo Duscov Boer", "number": 47, "posicao": "ATA"},
    {"nome": "Pepê Fermino", "number": 20, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Santos...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], SANTOS_ID)
    print("\nConcluído!")