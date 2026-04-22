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
    team      = relationship("Team", back_populates="jogadores")


class Team(Base):
    __tablename__ = 'times'
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    jogadores = relationship("Jogador", back_populates="team", uselist = True, lazy="joined")
    escudo = Column(String, nullable=True)
    foto_craque = Column(String, nullable = True)
    formacao = Column(String(10), nullable=True)  # ex: "4-3-3", "4-4-2"
    
