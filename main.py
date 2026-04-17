from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal, get_db
from typing import List
from sqlalchemy.orm import joinedload

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/jogadores/", response_model=schemas.Jogador)
def create_jogador(jogador: schemas.JogadorCreate, db: Session = Depends(get_db)):
    db_jogador = models.Jogador(
        nome = jogador.nome,
        numero = jogador.number,
        time_id = jogador.time_id,
        posicao = jogador.posicao
    )
    db.add(db_jogador)
    db.commit()
    db.refresh(db_jogador)
    return db_jogador


@app.get("/jogadores/", response_model=List[schemas.Jogador])
def listar_jogadores(db: Session = Depends(get_db)):
    jogadores = db.query(models.Jogador).all()
    return jogadores