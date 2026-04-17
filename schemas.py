from typing import List, Optional
from pydantic import BaseModel

class Jogador(BaseModel):
    name: str
    team_id: int
    position: str
    number: Optional[int] = None
    
    class Config:
        from_attributes = True

class JogadorCreate(Jogador):
    nome: str
    time_id: int
    posicao: str
    numero: Optional[int] = None

class Team(BaseModel):
    name: str
    titles: int
    
class TeamCreate(Team):
    nome: str
    titulos: int
    
class Position(BaseModel):
    posicao: str
    jogador_id: int
    
class PositionCreate(Position):
    posicao: str

class EsquemaTatico(BaseModel):
    esquema: str
    
class EsquemaTaticoCreate(EsquemaTatico):
    esquema: str