from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

# ─────────────────────────────────────────
# JOGADOR
# ─────────────────────────────────────────
class JogadorBase(BaseModel):
    name:   str
    number: int

class JogadorCreate(JogadorBase):
    pass  # só nome e número na criação

class JogadorUpdate(BaseModel):
    name:    Optional[str] = None
    number:  Optional[int] = None
    team_id: Optional[int] = None  # linka ao time depois

class Jogador(JogadorBase):
    id:        int
    team_id:   Optional[int] = None
    positions: List["Position"] = []

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
    name:   Optional[str] = None
    titles: Optional[int] = None

class Team(TeamBase):
    id:      int
    players: List[Jogador] = []

    class Config:
        from_attributes = True


# ─────────────────────────────────────────
# POSITION
# ─────────────────────────────────────────
class PositionBase(BaseModel):
    posicao:    str
    tipo:       str            # "primaria" ou "secundaria"
    parent_id:  Optional[int] = None  # None = é primária
    jogador_id: Optional[int] = None  # linkado depois

class PositionCreate(PositionBase):
    pass

class PositionUpdate(BaseModel):
    posicao:    Optional[str] = None
    jogador_id: Optional[int] = None

class Position(PositionBase):
    id:          int
    secundarias: List["Position"] = []  # sub-posições

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
Position.model_rebuild()