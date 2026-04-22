from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
import shutil, os
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import text
import models, schemas
from database import engine, SessionLocal, get_db
from typing import List, Optional

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

FORMATOS_ACEITOS = ["image/png", "image/webp", "image/jpeg"]


@app.post("/jogadores/", response_model=schemas.Jogador)
def create_jogador(jogador: schemas.JogadorCreate, db: Session = Depends(get_db)):
    db_jogador = models.Jogador(
        nome    = jogador.nome,
        number  = jogador.number,
        posicao = jogador.posicao,
        team_id = jogador.team_id,
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


@app.delete("/jogadores/{jogador_id}", status_code=204)
def delete_jogador(jogador_id: int, db: Session = Depends(get_db)):
    jogador = db.query(models.Jogador).filter(models.Jogador.id == jogador_id).first()
    if jogador is None:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    
    db.delete(jogador)
    db.commit()
    return {"message": f"O jogador {jogador.nome} foi deletado com sucesso."}
    
    
    
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

@app.get("/times/", response_model=List[schemas.Team])
def listar_times(db: Session = Depends(get_db)):
    time = db.query(models.Team).all()
    return time

@app.get('/times/{team_id}', response_model=schemas.Team)
def get_team (team_id: int, db: Session = Depends(get_db)):
    time = db.query(models.Team).filter(models.Team.id == team_id).first()
    if time is None:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    return time


@app.delete("/times/{team_id}", status_code=204)
def delete_time(team_id: int, db: Session = Depends(get_db)):
    time = db.query(models.Team).filter(models.Team.id == team_id).first()
    if time is None:
        raise HTTPException(status_code=404, detail="Time não encontrado")
    
    db.delete(time)
    db.commit()
    return


@app.post("/times/", response_model=schemas.Team)
async def criar_time(
    nome:        str                  = Form(...),
    formacao:    Optional[str]        = Form(None),
    escudo:      Optional[UploadFile] = File(None),
    foto_craque: Optional[UploadFile] = File(None),
    db:          Session              = Depends(get_db)
):
    FORMATOS_ACEITOS = ["image/png", "image/webp", "image/jpeg"]

    caminho_escudo = None
    if escudo and escudo.filename:
        if escudo.content_type not in FORMATOS_ACEITOS:
            raise HTTPException(status_code=400, detail="Formato de imagem inválido")
        os.makedirs("static/escudos", exist_ok=True)
        caminho = f"static/escudos/{escudo.filename}"
        with open(caminho, "wb") as buffer:
            shutil.copyfileobj(escudo.file, buffer)
        caminho_escudo = caminho

    caminho_craque = None
    if foto_craque and foto_craque.filename:
        if foto_craque.content_type not in FORMATOS_ACEITOS:
            raise HTTPException(status_code=400, detail="Formato de imagem inválido")
        os.makedirs("static/craques", exist_ok=True)
        caminho = f"static/craques/{foto_craque.filename}"
        with open(caminho, "wb") as buffer:
            shutil.copyfileobj(foto_craque.file, buffer)
        caminho_craque = caminho

    time = models.Team(
        nome=nome,
        formacao=formacao,
        escudo=caminho_escudo,
        foto_craque=caminho_craque
    )
    db.add(time)
    db.commit()
    db.refresh(time)
    return time

@app.patch("/times/{team_id}", response_model=schemas.Team)
async def update_time(
    team_id:     int,
    nome:        Optional[str]        = Form(None),
    formacao:    Optional[str]        = Form(None),  
    escudo:      Optional[UploadFile] = File(None),
    foto_craque: Optional[UploadFile] = File(None),
    db:          Session              = Depends(get_db)
):
    FORMATOS_ACEITOS = ["image/png", "image/webp", "image/jpeg"]

    db_team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if db_team is None:
        raise HTTPException(status_code=404, detail="Time não encontrado")

    if nome:
        db_team.nome = nome

    if formacao:          
        db_team.formacao = formacao     

    if escudo and escudo.filename:
        if escudo.content_type not in FORMATOS_ACEITOS:
            raise HTTPException(status_code=400, detail="Formato de imagem inválido")
        os.makedirs("static/escudos", exist_ok=True)
        caminho = f"static/escudos/{escudo.filename}"
        with open(caminho, "wb") as buffer:
            shutil.copyfileobj(escudo.file, buffer)
        db_team.escudo = caminho

    if foto_craque and foto_craque.filename:
        if foto_craque.content_type not in FORMATOS_ACEITOS:
            raise HTTPException(status_code=400, detail="Formato de imagem inválido")
        os.makedirs("static/craques", exist_ok=True)
        caminho = f"static/craques/{foto_craque.filename}"
        with open(caminho, "wb") as buffer:
            shutil.copyfileobj(foto_craque.file, buffer)
        db_team.foto_craque = caminho

    db.commit()
    db.refresh(db_team)
    return db_team