from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy import relationship
from database import Base

class Jogador(Base):
    __tablename__ = 'jogadores'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    team_id = Column(Integer, ForeignKey('times.id'))
    team = relationship("Team", back_populates="players")
    position = relationship("Position", back_populates="players")
    number = Column(Integer)

class Team(Base):
    __tablename__ = 'times'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    titles = Column(Integer)
    players = relationship("Jogador", back_populates="team", uselist = False)
    
class Position (Base):
    __tablename__='positions'
    id = Column(Integer, primary_key=True, index=True)
    posicao = Column(String, index=True)
    jogador_id = Column(Integer, ForeignKey('jogadores.id'))
    jogador = relationship("Jogador", back_populates="position")
    
class EsquemaTatico (Base):
    __tablename__ = 'esquema_tatico'
    id = Column(Integer, primary_key=True, index=True)
    esquema = Column(String, index=True)
    time_id = Column(Integer, ForeignKey('times.id'))
    time = relationship("Team", back_populates="esquema_tatico", uselist = False)
    
    
    