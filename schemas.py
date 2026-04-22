from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

# ─────────────────────────────────────────
# JOGADOR
# ─────────────────────────────────────────
class Posicao(str, Enum):
    GOL = "GOL"
    ZAG = "ZAG"
    LAT = "LAT"
    LAD = "LAD"
    LAE = "LAE"
    VOL = "VOL"
    MEI = "MEI"
    SA = "SA"
    PTD = "PTD"
    PTE = "PTE"
    ATA = "ATA"
    TEC = "TEC"
    # adicione as que precisar

class JogadorBase(BaseModel):
    name:   str
    number: int
    posicao: Posicao

class JogadorCreate(JogadorBase):
    pass  # só nome e número na criação

class JogadorUpdate(BaseModel):
    name:    Optional[str] = None
    number:  Optional[int] = None
    team_id: Optional[int] = None  # linka ao time depois

class Jogador(JogadorBase):
    id:        int
    team_id:   Optional[int] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# TEAM
# ─────────────────────────────────────────
class TeamBase(BaseModel):
    name:   str
    titles: int

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    nome:        Optional[str] = None
    escudo:      Optional[str] = None
    foto_craque: Optional[str] = None

class Team(TeamBase):
    id:      int
    players: List[Jogador] = []
    escudo: Optional[str] = None
    foto_craque: Optional[str] = None

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# ESQUEMA TÁTICO
# ─────────────────────────────────────────
class EsquemaTaticoBase(BaseModel):
    esquema: str
    time_id: Optional[int] = None

class EsquemaTaticoCreate(EsquemaTaticoBase):
    pass

class EsquemaTaticoUpdate(BaseModel):
    esquema: Optional[str] = None
    time_id: Optional[int]         = None

class EsquemaTatico(EsquemaTaticoBase):
    id: int

    class Config:
        from_attributes = True


# necessário para resolver referências circulares (Jogador <-> Position)
Jogador.model_rebuild()