from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Jogador(Base):
    __tablename__ = 'jogadores'

    id     = Column(Integer, primary_key=True, index=True)  # gerado automaticamente
    name   = Column(String, index=True)
    number = Column(Integer)

    # Relacionamentos (opcionais, preenchidos depois)
    team_id   = Column(Integer, ForeignKey('times.id'), nullable=True)
    team      = relationship("Team", back_populates="players")
    positions = relationship("Position", back_populates="jogador")  # 1:N


class Team(Base):
    __tablename__ = 'times'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    titles = Column(Integer)
    players = relationship("Jogador", back_populates="team", uselist = False)
    esquema_tatico = relationship("EsquemaTatico", back_populates="time")
    
class Position(Base):
    __tablename__ = 'positions'

    id         = Column(Integer, primary_key=True, index=True)
    posicao    = Column(String, index=True)
    tipo       = Column(String)  # "primaria" ou "secundaria"
    parent_id  = Column(Integer, ForeignKey('positions.id'), nullable=True)

    # Relacionamentos
    parent       = relationship("Position", back_populates="secundarias", remote_side="Position.id")
    secundarias  = relationship("Position", back_populates="parent")
    jogador_id   = Column(Integer, ForeignKey('jogadores.id'), nullable=True)
    jogador      = relationship("Jogador", back_populates="positions")
    
class EsquemaTatico (Base):
    __tablename__ = 'esquema_tatico'
    id = Column(Integer, primary_key=True, index=True)
    esquema = Column(String, index=True)
    time_id = Column(Integer, ForeignKey('times.id'))
    time = relationship("Team", back_populates="esquema_tatico", uselist = False)

