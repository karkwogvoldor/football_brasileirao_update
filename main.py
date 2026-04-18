from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas
from database import engine, SessionLocal, get_db
from typing import List
from sqlalchemy.orm import joinedload

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

@app.post("/jogadores/", response_model=schemas.Jogador)
def create_jogador(jogador: schemas.JogadorCreate, db: Session = Depends(get_db)):
    db_jogador = models.Jogador(
        name = jogador.name,
        number = jogador.number,
    )
    db.add(db_jogador)
    db.commit()
    db.refresh(db_jogador)
    return db_jogador


@app.get("/jogadores/", response_model=List[schemas.Jogador])
def listar_jogadores(db: Session = Depends(get_db)):
    jogadores = db.query(models.Jogador).all()
    return jogadores

@app.get('/jogadores/{jogador_id}', response_model=schemas.Jogador)
def get_jogador (jogador_id: int, db: Session = Depends(get_db)):
    jogador = db.query(models.Jogador).filter(models.Jogador.id == jogador_id).first()
    if jogador is None:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    return jogador


@app.delete("/jogadores/{jogador_id}")
def delete_jogador(jogador_id: int, db: Session = Depends(get_db)):
    jogador = db.query(models.Jogador).filter(models.Jogador.id == jogador_id).first()
    if jogador is None:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    
    db.delete(jogador)
    db.commit()
    return {"message": f"O jogador {jogador.name} foi deletado com sucesso."}
    
    
    
@app.patch("/jogadores/{jogador_id}", response_model=schemas.JogadorUpdate)
def update_jogador(jogador_id: int, jogador: schemas.JogadorUpdate, db: Session = Depends(get_db)):
    db_jogador = db.query(models.Jogador).filter(models.Jogador.id == jogador_id).first()
    if db_jogador is None:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    dados = jogador.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(db_jogador, campo, valor)
    db.commit()
    db.refresh(db_jogador)
    return db_jogador

