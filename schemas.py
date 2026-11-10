from datetime import date, datetime, time
from typing import Optional

from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)

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

    model_config = ConfigDict(from_attributes=True)


class ClubRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    state: str


class FixtureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_ref: str
    round_number: int
    scheduled_date: date
    scheduled_time: Optional[time]
    home_club: ClubRead
    away_club: ClubRead


class GameSaveCreate(BaseModel):
    controlled_club_id: int
    season_id: int


class GameSaveRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    controlled_club_id: int
    season_id: int
    snapshot_version: str
    ruleset_version: str
    status: str
    created_at: datetime
    updated_at: datetime

Jogador.model_rebuild()
