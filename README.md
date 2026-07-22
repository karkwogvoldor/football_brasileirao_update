# ⚽ Football Brasileirão 2026

> Uma aplicação web interativa para visualizar escalações, formações e elencos dos 20 clubes do **Campeonato Brasileiro Série A 2026**.

🌐 **[Clique aqui para acessar](https://footballbrasileiraoupdate-production.up.railway.app)**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?logo=postgresql)](https://postgresql.org)
[![License](https://img.shields.io/badge/license-MIT-brightgreen)](LICENSE)


| ![Home](static/images/preview_home.png) | ![Lineup](static/images/preview_clube.png) |
---

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Tecnologias](#tecnologias)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Back-end — Como foi desenvolvido](#back-end--como-foi-desenvolvido)
- [API](#api)
- [Como rodar o projeto](#como-rodar-o-projeto)
- [Deploy](#deploy)
- [Aprendizados](#aprendizados)

---

## Sobre o Projeto

O **Football Brasileirão 2026** é uma galeria web com os elencos e escalações dos 20 times da Série A. O usuário pode navegar pelos clubes, visualizar a escalação tática no campo, arrastar reservas para fazer substituições e ver o craque de cada time.

O front-end foi fornecido pronto; o foco do desenvolvimento foi toda a infraestrutura back-end: API REST, banco de dados, hospedagem e integração com armazenamento de imagens em nuvem.

---

## Tecnologias

- **Python 3.11+**
- **FastAPI** — framework back-end principal
- **SQLAlchemy** — ORM para mapeamento do banco de dados
- **PostgreSQL** — banco de dados relacional
- **Pydantic** — validação de dados e schemas
- **Cloudinary** — armazenamento de imagens em nuvem
- **Railway** — hospedagem do app e do banco de dados
- **HTML5 + CSS3 + JavaScript** — front-end (fornecido pronto)

---

## Estrutura do Projeto

```
football_brasileirao_update/
│
├── static/
│   ├── escudos/          # Escudos dos clubes (.webp)
│   ├── craques/          # Fotos dos craques (.jpg / .webp)
│   ├── images/           # Imagem do campo (campinho.jpg)
│   ├── style.css         # Estilos da página inicial
│   ├── clube.css         # Estilos da página do clube
│   ├── clube.js          # Lógica do campo (escalações, drag & drop)
│   └── main.js           # Lógica da página inicial
│
├── templates/
│   ├── index.html        # Página inicial — grid de clubes
│   └── clube.html        # Página do clube — escalação e reservas
│
├── seed/                 # Scripts para popular o banco de dados
│   ├── seed_times.py     # Seed dos 20 times
│   ├── seed_corinthians.py
│   └── ...               # Um arquivo por clube
│
├── seed_all.py           # Roda todos os seeds em sequência
├── main.py               # FastAPI — rotas e endpoints
├── models.py             # Modelos SQLAlchemy (ORM)
├── schemas.py            # Schemas Pydantic
├── database.py           # Conexão com o banco de dados
├── requirements.txt      # Dependências do projeto
├── Procfile              # Comando de inicialização para o Railway
└── .env                  # Variáveis de ambiente (não versionado)
```

---

## Back-end — Como foi desenvolvido

### 1. Modelos e Banco de Dados

O projeto usa **SQLAlchemy ORM** com duas tabelas principais:

- **`times`** — armazena cada clube: `id`, `nome`, `formacao`, `escudo` (URL Cloudinary), `foto_craque` (URL Cloudinary)
- **`jogadores`** — armazena cada jogador: `id`, `nome`, `number`, `posicao`, `team_id` (FK → times)

```python
# models.py
class Team(Base):
    __tablename__ = "times"
    id          = Column(Integer, primary_key=True)
    nome        = Column(String)
    formacao    = Column(String, nullable=True)
    escudo      = Column(String, nullable=True)
    foto_craque = Column(String, nullable=True)
```

---

### 2. API REST com FastAPI

Endpoints implementados:

**Times (`/times`)**

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/times/` | Lista todos os times |
| `GET` | `/times/{id}` | Busca time por ID |
| `POST` | `/times/` | Cria time (multipart form) |
| `PATCH` | `/times/{id}` | Atualiza time |
| `DELETE` | `/times/{id}` | Remove time |

**Jogadores (`/jogadores`)**

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/jogadores/` | Lista todos os jogadores |
| `GET` | `/jogadores/{id}` | Busca jogador por ID |
| `POST` | `/jogadores/` | Cria jogador |
| `PATCH` | `/jogadores/{id}` | Atualiza jogador |
| `DELETE` | `/jogadores/{id}` | Remove jogador |

Documentação interativa disponível em:
```
https://footballbrasileiraoupdate-production.up.railway.app/docs
```

---

### 3. Upload de Imagens com Cloudinary

As imagens são armazenadas no **Cloudinary** (serviço de armazenamento em nuvem), evitando a perda de arquivos a cada novo deploy. O `main.py` faz o upload e salva a URL pública no banco:

```python
def upload_imagem(file: UploadFile, pasta: str) -> str:
    resultado = cloudinary.uploader.upload(
        file.file,
        folder=pasta,
        public_id=os.path.splitext(file.filename)[0],
        overwrite=True,
    )
    return resultado["secure_url"]
```

---

### 4. Seeds

Cada clube tem um arquivo de seed que popula o banco via API. O `seed_all.py` roda todos em sequência:

```bash
railway run python seed_all.py
```

---

## Como rodar o projeto

**Pré-requisitos:** Python 3.11+, PostgreSQL instalado.

```bash
# 1. Clone o repositório
git clone https://github.com/karkwogvoldor/football_brasileirao_update.git
cd football_brasileirao_update

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure o .env
DATABASE_URL=postgresql://usuario:senha@localhost/db_project
CLOUDINARY_CLOUD_NAME=seu_cloud_name
CLOUDINARY_API_KEY=sua_api_key
CLOUDINARY_API_SECRET=seu_api_secret

# 5. Rode o servidor
uvicorn main:app --reload
```

Acesse em: `http://127.0.0.1:8000`

---

## Deploy

O projeto está hospedado no **Railway** com:

- **App**: FastAPI rodando via `uvicorn`
- **Banco**: PostgreSQL gerenciado pelo Railway
- **Imagens**: Cloudinary (armazenamento persistente)

```
# Procfile
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Aprendizados

Este projeto foi desenvolvido durante minha transição de carreira da Engenharia Química para o desenvolvimento back-end. Os principais conceitos praticados foram:

- Criação de API REST com FastAPI
- Modelagem de banco de dados relacional com SQLAlchemy ORM
- Upload e gerenciamento de imagens com Cloudinary
- Deploy de aplicação Python + PostgreSQL no Railway
- Configuração de variáveis de ambiente em produção
- Criação de scripts de seed para popular banco de dados

---

*Projeto desenvolvido como parte do aprendizado em desenvolvimento back-end com Python.*
