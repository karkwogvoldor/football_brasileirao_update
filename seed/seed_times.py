import requests

BASE_URL = "https://footballbrasileiraoupdate-production.up.railway.app"

times = [
    {"id": 1,  "nome": "Corinthians",           "formacao": "4-1-2-1-2"},
    {"id": 2,  "nome": "Atlético Mineiro",       "formacao": "4-4-2"},
    {"id": 3,  "nome": "Athletico Paranaense",   "formacao": "3-4-3"},
    {"id": 4,  "nome": "Bahia",                  "formacao": "4-3-3"},
    {"id": 5,  "nome": "Botafogo",               "formacao": "4-2-3-1"},
    {"id": 6,  "nome": "Red Bull Bragantino",    "formacao": "4-2-3-1"},
    {"id": 7,  "nome": "Chapecoense",            "formacao": "4-1-2-1-2"},
    {"id": 8,  "nome": "Coritiba",               "formacao": "4-2-3-1"},
    {"id": 9,  "nome": "Cruzeiro",               "formacao": "4-2-3-1"},
    {"id": 10, "nome": "Flamengo",               "formacao": "4-3-3"},
    {"id": 11, "nome": "Fluminense",             "formacao": "4-3-3"},
    {"id": 12, "nome": "Gremio",                 "formacao": "4-3-3"},
    {"id": 13, "nome": "Internacional",          "formacao": "4-2-3-1"},
    {"id": 14, "nome": "Mirassol",               "formacao": "3-5-2"},
    {"id": 15, "nome": "Palmeiras",              "formacao": "4-2-3-1"},
    {"id": 16, "nome": "Remo",                   "formacao": "4-2-3-1"},
    {"id": 17, "nome": "Santos",                 "formacao": "4-2-3-1"},
    {"id": 18, "nome": "São Paulo",              "formacao": "4-2-3-1"},
    {"id": 19, "nome": "Vasco da Gama",          "formacao": "4-2-3-1"},
    {"id": 20, "nome": "Vitória",                "formacao": "4-3-3"},
]

def criar_time(time):
    data = {
        "nome": time["nome"],
        "formacao": time["formacao"],
    }
    response = requests.post(f"{BASE_URL}/times/", data=data)
    if response.status_code == 200:
        print(f"✅ {time['nome']}")
    else:
        print(f"❌ Erro em {time['nome']}: {response.text}")

if __name__ == "__main__":
    print("Povoando times...\n")
    for time in times:
        criar_time(time)
    print("\nConcluído!")