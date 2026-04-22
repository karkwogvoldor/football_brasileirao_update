from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Jogador(Base):
    __tablename__ = 'jogadores'

    id     = Column(Integer, primary_key=True, index=True)  # gerado automaticamente
    name   = Column(String, index=True)
    number = Column(Integer)
    posicao = Column(String(4))

    # Relacionamentos (opcionais, preenchidos depois)
    team_id   = Column(Integer, ForeignKey('times.id'), nullable=True)
    team      = relationship("Team", back_populates="players")


class Team(Base):
    __tablename__ = 'times'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    players = relationship("Jogador", back_populates="team", uselist = False)
    esquema_tatico = relationship("EsquemaTatico", back_populates="time")
    escudo = Column(String, nullable=True)
    foto_craque = Column(String, nullable = True)
    formacao = Column(String(10), nullable=True)  # ex: "4-3-3", "4-4-2"
    
    
class EsquemaTatico (Base):
    __tablename__ = 'esquema_tatico'
    id = Column(Integer, primary_key=True, index=True)
    esquema = Column(String, index=True)
    time_id = Column(Integer, ForeignKey('times.id'))
    time = relationship("Team", back_populates="esquema_tatico", uselist = False)

