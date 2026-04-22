from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

# ─── JOGADOR ────────────────────────────────────────
class Posicao(str, Enum):
    GOL = "GOL"
    ZAG = "ZAG"
    LAT = "LAT"
    LAD = "LAD"
    LAE = "LAE"
    VOL = "VOL"
    MEI = "MEI"
    PT = "PT"
    SA  = "SA"
    ATA = "ATA"
    TEC = "TEC"

class JogadorBase(BaseModel):
    nome:   str
    number: int
    posicao: Posicao

class JogadorCreate(JogadorBase):
    team_id: Optional[int] = None

class JogadorUpdate(BaseModel):
    nome:    Optional[str] = None
    number:  Optional[int] = None
    posicao: Optional[Posicao] = None  # ← estava sem o tipo Posicao
    team_id: Optional[int] = None

class Jogador(JogadorBase):
    id:      int
    team_id: Optional[int] = None

    class Config:
        from_attributes = True

# ─── TEAM ────────────────────────────────────────────
class TeamBase(BaseModel):
    nome:     str        # ← era name, corrigido para nome
    formacao: Optional[str] = None

class TeamCreate(TeamBase):
    pass

class TeamUpdate(BaseModel):
    nome:        Optional[str] = None
    formacao:    Optional[str] = None
    escudo:      Optional[str] = None
    foto_craque: Optional[str] = None

class Team(TeamBase):
    id:          int
    escudo:      Optional[str] = None
    foto_craque: Optional[str] = None

    class Config:
        from_attributes = True

Jogador.model_rebuild()