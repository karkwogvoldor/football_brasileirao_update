# ⚽ Football Brasileirão 2026

> An interactive web application to visualize lineups, formations, and squads of all 20 clubs in the **Campeonato Brasileiro Série A 2026**.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?logo=postgresql)
![License](https://img.shields.io/badge/license-MIT-brightgreen)

---

## 📸 Screenshots

| Home — Club Selection | Club Page — Lineup |
|---|---|
| ![Home](static/images/preview_home.png) | ![Lineup](static/images/preview_clube.png) |

---

## 🧩 Components

```
football_brasileirao_update/
│
├── static/
│   ├── escudos/          # Club badge images (.webp)
│   ├── craques/          # Star player photos (.jpg / .webp)
│   ├── images/           # Field background (campinho.jpg)
│   ├── style.css         # Home page styles
│   ├── clube.css         # Club page styles
│   ├── clube.js          # Club page logic (lineups, drag & drop)
│   └── main.js           # Home page logic
│
├── templates/
│   ├── index.html        # Home — club selection grid
│   └── clube.html        # Club page — lineup, bench, star player
│
├── main.py               # FastAPI app — routes & API endpoints
├── models.py             # SQLAlchemy ORM models
├── schemas.py            # Pydantic schemas
├── database.py           # DB connection & session
├── seed/                 # Seed scripts for initial data
└── requirements.txt
```

---

## ⚙️ How It Works

### 1. Home Page (`/`)
- Displays a **5-column grid** of all 20 clubs with badge and name
- Each card links to `/clube/{team_id}` on click

### 2. Club Page (`/clube/{id}`)
- Fetches club data from `GET /times/`
- Fetches all players from `GET /jogadores/`
- Filters players by `team_id`
- Reads the starting 11 from the `TITULARES` dictionary (keyed by `team_id`)
- Maps each player to a **coordinate** on the field based on the club's tactical `formacao`
- Remaining players go to the **bench**

### 3. Tactical Formations (`FORMACOES`)
- Each formation is an **ordered array of [x, y] coordinates** (percentage-based)
- The order in `TITULARES[team_id]` maps 1-to-1 with the formation coordinates:
  - Position 1 → GK
  - Positions 2–3 → CB
  - Positions 4–5 → FB
  - Positions 6–7 → VOL/MF
  - Positions 8–10 → AM/ATA
  - Position 11 → ST

### 4. Drag & Drop Substitutions
- Bench players are **draggable**
- Drop a bench player onto a starter → substitution is made
- The outgoing player returns to the bench
- Toast notification shows the swap

### 5. Star Player Card
- Name, position and description loaded from the `CRAQUES` dictionary in `clube.js`
- Photo loaded from `/static/craques/{clube}.jpg`

---

## 📋 Requirements

- Python 3.11+
- PostgreSQL 15+
- Node.js *(not required — vanilla JS)*

### Python dependencies (`requirements.txt`)

```
fastapi
uvicorn[standard]
sqlalchemy
psycopg2-binary
python-multipart
pydantic
```

---

## 🚀 Setup

### 1. Clone the repository

```bash
git clone https://github.com/youruser/football_brasileirao_update.git
cd football_brasileirao_update
```

### 2. Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the database

Create a PostgreSQL database and update `database.py`:

```python
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/brasileirao"
```

### 5. Run the application

```bash
uvicorn main:app --reload
```

Open your browser at:

```
http://127.0.0.1:8000
```

---

## 🌐 Web Pages

| Route | Description |
|---|---|
| `GET /` | Home page — club selection grid |
| `GET /clube/{team_id}` | Club page — lineup, bench, star player |

### Navigation
- Click any club card on the home page to open its lineup page
- Use the **← Brasileirão 2026** breadcrumb to go back

---

## 🔌 API

Base URL: `http://127.0.0.1:8000`

Interactive docs available at:
```
http://127.0.0.1:8000/docs
```

### Clubs (`/times`)

| Method | Route | Description |
|---|---|---|
| `GET` | `/times/` | List all clubs |
| `GET` | `/times/{id}` | Get club by ID |
| `POST` | `/times/` | Create club (multipart form) |
| `PATCH` | `/times/{id}` | Update club |
| `DELETE` | `/times/{id}` | Delete club |

**POST / PATCH fields:**

| Field | Type | Description |
|---|---|---|
| `nome` | string | Club name |
| `formacao` | string | Tactical formation e.g. `4-3-3` |
| `escudo` | file | Badge image (png, webp, jpeg) |
| `foto_craque` | file | Star player photo |

**Example response:**
```json
{
  "id": 1,
  "nome": "Corinthians",
  "formacao": "4-2-1-2",
  "escudo": "static/escudos/corinthians.webp",
  "foto_craque": "static/craques/corinthians.jpg"
}
```

---

### Players (`/jogadores`)

| Method | Route | Description |
|---|---|---|
| `GET` | `/jogadores/` | List all players |
| `GET` | `/jogadores/{id}` | Get player by ID |
| `POST` | `/jogadores/` | Create player |
| `PATCH` | `/jogadores/{id}` | Update player |
| `DELETE` | `/jogadores/{id}` | Delete player |

**Player fields:**

| Field | Type | Description |
|---|---|---|
| `nome` | string | Player name |
| `number` | int | Jersey number |
| `posicao` | string | Position: `GOL`, `ZAG`, `LAT`, `VOL`, `MEI`, `ATA`, `SA`, `PT` |
| `team_id` | int | Foreign key → Club ID |

**Example response:**
```json
{
  "id": 1,
  "nome": "Hugo Souza",
  "number": 1,
  "posicao": "GOL",
  "team_id": 1
}
```

---

## 🗂️ Configuration

### Adding a new club's starting lineup

In `static/clube.js`, find the `TITULARES` dictionary and add an entry:

```js
const TITULARES = {
  1: [1, 8, 7, 5, 6, 18, 17, 15, 26, 27, 22], // Corinthians
  2: [id_gk, id_cb1, id_cb2, ...],              // Your club
};
```

The **order of IDs** maps directly to the formation coordinates:
- `[0]` → Goalkeeper
- `[1][2]` → Center-backs
- `[3][4]` → Fullbacks
- ... and so on based on the formation

### Adding a new tactical formation

In `static/clube.js`, find `FORMACOES` and add:

```js
'4-5-1': [
  [50, 88],                                     // GK
  [33, 74], [67, 74],                           // CB
  [12, 70], [88, 70],                           // FB
  [20, 52], [38, 52], [56, 52], [74, 52],       // MF
  [88, 52],                                     // WM
  [50, 20],                                     // ST
],
```

Then update the club's `formacao` field in the database via `PATCH /times/{id}`.

### Supported formations

| Formation | Description |
|---|---|
| `4-2-1-2` | Diamond midfield |
| `4-4-2` | Classic flat four |
| `4-3-3` | Three forwards |
| `3-4-3` | Three defenders |
| `4-2-3-1` | One striker with three AMs |
| `3-5-2` | Three defenders, five midfielders |

### Position codes

| Code | Position |
|---|---|
| `GOL` | Goalkeeper |
| `ZAG` | Center-back |
| `LAT` | Fullback |
| `VOL` | Defensive midfielder |
| `MEI` | Midfielder |
| `ATA` | Forward |
| `SA` | Second striker |
| `PT` | Winger |

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2026 Football Brasileirão

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

<p align="center">Made with ⚽ for the Brasileirão 2026</p>
