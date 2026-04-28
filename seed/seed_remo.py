import requests

BASE_URL = "https://footballbrasileiraoupdate-production.up.railway.app"

def criar_jogador(nome, number, posicao, team_id):
    data = {"nome": nome, "number": number, "posicao": posicao, "team_id": team_id}
    response = requests.post(f"{BASE_URL}/jogadores/", json=data)
    if response.status_code == 200:
        print(f"✅ {nome}")
    else:
        print(f"❌ Erro em {nome}: {response.text}")

# ————— REMO ———————————————————————————————————————————
REMO_ID = 16

jogadores = [
    # GOLEIROS
    {"nome": "Ivan Quaresma", "number": 97, "posicao": "GOL"},
    {"nome": "Marcelo Rangel", "number": 88, "posicao": "GOL"},
    {"nome": "Ygor Vinhas", "number": 94, "posicao": "GOL"},
    {"nome": "Marcos Alexandre", "number": 50, "posicao": "GOL"},

    # DEFENSORES
    {"nome": "João Lucas", "number": 2, "posicao": "LAT"},
    {"nome": "Mayk Silva", "number": 98, "posicao": "LAT"},
    {"nome": "Marllon", "number": 13, "posicao": "ZAG"},
    {"nome": "Matheus Alexandre", "number": 2, "posicao": "LAT"},
    {"nome": "Kayky Almeida", "number": 27, "posicao": "ZAG"},
    {"nome": "Duplexe Tchamba", "number": 18, "posicao": "ZAG"},
    {"nome": "Braian Cufré", "number": 24, "posicao": "LAT"},
    {"nome": "Thalisson Gabriel", "number": 3, "posicao": "ZAG"},
    {"nome": "Marcelinho", "number": 79, "posicao": "LAT"},
    {"nome": "Cristian Tassano", "number": 17, "posicao": "ZAG"},
    {"nome": "Léo", "number": 5, "posicao": "ZAG"},

    # MEIO-CAMPISTAS
    {"nome": "Yago Pikachu", "number": 22, "posicao": "MEI"},
    {"nome": "Patrick de Paula", "number": 12, "posicao": "VOL"},
    {"nome": "Diego Hernández", "number": 33, "posicao": "MEI"},
    {"nome": "Vitor Bueno", "number": 15, "posicao": "MEI"},
    {"nome": "Patrick", "number": 8, "posicao": "MEI"},
    {"nome": "Ze Welison", "number": 28, "posicao": "VOL"},
    {"nome": "Leonel Picco", "number": 14, "posicao": "VOL"},
    {"nome": "Jáderson", "number": 10, "posicao": "MEI"},
    {"nome": "Panagiotis Tachtsidis", "number": 77, "posicao": "MEI"},
    {"nome": "Jajá", "number": 37, "posicao": "MEI"},
    {"nome": "Zé Ricardo", "number": 55, "posicao": "VOL"},
    {"nome": "David Braga", "number": 26, "posicao": "MEI"},
    {"nome": "Giovanni Pavani", "number": 7, "posicao": "VOL"},
    {"nome": "Nicolás Ferreira", "number": 25, "posicao": "MEI"},
    {"nome": "Franco Catarozzi", "number": 23, "posicao": "MEI"},
    {"nome": "Freitas", "number": 35, "posicao": "VOL"},
    {"nome": "Guty", "number": 23, "posicao": "MEI"},

    # ATACANTES
    {"nome": "Carlinhos", "number": 9, "posicao": "ATA"},
    {"nome": "Alef Manga", "number": 11, "posicao": "ATA"},
    {"nome": "Gabriel Taliari", "number": 19, "posicao": "ATA"},
    {"nome": "Gabriel Poveda", "number": 99, "posicao": "ATA"},
    {"nome": "Rafael Monti", "number": 71, "posicao": "ATA"},
    {"nome": "Joao Pedro", "number": 45, "posicao": "ATA"},
    {"nome": "Eduardo Melo", "number": 39, "posicao": "ATA"},
]

if __name__ == "__main__":
    print("Povoando Remo...\n")
    for j in jogadores:
        criar_jogador(j["nome"], j["number"], j["posicao"], REMO_ID)
    print("\nConcluído!")