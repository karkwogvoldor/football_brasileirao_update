from contextlib import asynccontextmanager
import mimetypes
from datetime import timedelta

from fastapi import APIRouter, FastAPI, Depends, HTTPException, UploadFile, File, Form, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import shutil, os
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, text
import models, schemas
from database import engine, SessionLocal, get_db
from typing import List, Optional
import cloudinary
import cloudinary.uploader

from brafoot.gameplay.sessions import (
    COOKIE_NAME,
    SESSION_LIFETIME,
    create_browser_session,
    find_browser_session,
)

cloudinary.config(
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key    = os.environ.get("CLOUDINARY_API_KEY"),
    api_secret = os.environ.get("CLOUDINARY_API_SECRET"),
)

templates = Jinja2Templates(directory="templates")
router = APIRouter()

FORMATOS_ACEITOS = ["image/png", "image/webp", "image/jpeg"]


def upload_imagem(file: UploadFile, pasta: str) -> str:
    resultado = cloudinary.uploader.upload(
        file.file,
        folder=pasta,
        public_id=os.path.splitext(file.filename)[0],
        overwrite=True,
    )
    return resultado["secure_url"]


@router.get("/")
def root():
    return FileResponse("templates/index.html")

@router.get("/clube/{team_id}")
def clube(team_id: int):
    return FileResponse("templates/clube.html")


@router.post("/jogadores/", response_model=schemas.Jogador)
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


@router.get("/jogadores/", response_model=List[schemas.Jogador])
def listar_jogadores(db: Session = Depends(get_db)):
    jogadores = db.query(models.Jogador).all()
    return jogadores

@router.get('/jogadores/{jogador_id}', response_model=schemas.Jogador)
def get_jogador(jogador_id: int, db: Session = Depends(get_db)):
    jogador = db.query(models.Jogador).filter(models.Jogador.id == jogador_id).first()
    if jogador is None:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    return jogador


@router.delete("/jogadores/{jogador_id}", status_code=204)
def delete_jogador(jogador_id: int, db: Session = Depends(get_db)):
    jogador = db.query(models.Jogador).filter(models.Jogador.id == jogador_id).first()
    if jogador is None:
        raise HTTPException(status_code=404, detail="Jogador não encontrado")
    db.delete(jogador)
    db.commit()
    return


@router.patch("/jogadores/{jogador_id}", response_model=schemas.JogadorUpdate)
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


@router.get("/times/", response_model=List[schemas.Team])
def listar_times(db: Session = Depends(get_db)):
    time = db.query(models.Team).all()
    return time

@router.get('/times/{team_id}', response_model=schemas.Team)
def get_team(team_id: int, db: Session = Depends(get_db)):
    time = db.query(models.Team).filter(models.Team.id == team_id).first()
    if time is None:
        raise HTTPException(status_code=404, detail="Time não encontrado")
    return time


@router.delete("/times/{team_id}", status_code=204)
def delete_time(team_id: int, db: Session = Depends(get_db)):
    time = db.query(models.Team).filter(models.Team.id == team_id).first()
    if time is None:
        raise HTTPException(status_code=404, detail="Time não encontrado")
    db.delete(time)
    db.commit()
    return


@router.post("/times/", response_model=schemas.Team)
async def criar_time(
    nome:        str                  = Form(...),
    formacao:    Optional[str]        = Form(None),
    escudo:      Optional[UploadFile] = File(None),
    foto_craque: Optional[UploadFile] = File(None),
    db:          Session              = Depends(get_db)
):
    caminho_escudo = None
    if escudo and escudo.filename:
        if escudo.content_type not in FORMATOS_ACEITOS:
            raise HTTPException(status_code=400, detail="Formato de imagem inválido")
        caminho_escudo = upload_imagem(escudo, "brasileirao/escudos")

    caminho_craque = None
    if foto_craque and foto_craque.filename:
        if foto_craque.content_type not in FORMATOS_ACEITOS:
            raise HTTPException(status_code=400, detail="Formato de imagem inválido")
        caminho_craque = upload_imagem(foto_craque, "brasileirao/craques")

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


@router.patch("/times/{team_id}", response_model=schemas.Team)
async def update_time(
    team_id:     int,
    nome:        Optional[str]        = Form(None),
    formacao:    Optional[str]        = Form(None),
    escudo:      Optional[UploadFile] = File(None),
    foto_craque: Optional[UploadFile] = File(None),
    db:          Session              = Depends(get_db)
):
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
        db_team.escudo = upload_imagem(escudo, "brasileirao/escudos")

    if foto_craque and foto_craque.filename:
        if foto_craque.content_type not in FORMATOS_ACEITOS:
            raise HTTPException(status_code=400, detail="Formato de imagem inválido")
        db_team.foto_craque = upload_imagem(foto_craque, "brasileirao/craques")

    db.commit()
    db.refresh(db_team)
    return db_team


@router.get(
    "/api/v1/seasons/{season_id}/fixtures",
    response_model=List[schemas.FixtureRead],
)
def list_season_fixtures(season_id: int, db: Session = Depends(get_db)):
    season = db.query(models.Season).filter_by(id=season_id).one_or_none()
    if season is None:
        raise HTTPException(status_code=404, detail="Temporada não encontrada")
    return (
        db.query(models.Fixture)
        .options(
            joinedload(models.Fixture.home_club),
            joinedload(models.Fixture.away_club),
        )
        .filter_by(season_id=season_id)
        .order_by(models.Fixture.round_number, models.Fixture.source_ref)
        .all()
    )


@router.post(
    "/api/v1/saves",
    response_model=schemas.GameSaveRead,
    status_code=201,
)
def create_game_save(
    payload: schemas.GameSaveCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    season = db.query(models.Season).filter_by(id=payload.season_id).one_or_none()
    club = db.query(models.Club).filter_by(id=payload.controlled_club_id).one_or_none()
    if season is None or club is None:
        raise HTTPException(status_code=404, detail="Temporada ou clube não encontrado")

    club_in_season = (
        db.query(models.Fixture.id)
        .filter(models.Fixture.season_id == season.id)
        .filter(
            or_(
                models.Fixture.home_club_id == club.id,
                models.Fixture.away_club_id == club.id,
            )
        )
        .first()
    )
    if club_in_season is None:
        raise HTTPException(status_code=422, detail="Clube não pertence à temporada")

    browser_session = find_browser_session(
        db, request.cookies.get(COOKIE_NAME)
    )
    new_token: str | None = None
    if browser_session is None:
        browser_session, new_token = create_browser_session(db)

    active_save = (
        db.query(models.GameSave)
        .filter_by(browser_session_id=browser_session.id, status="active")
        .one_or_none()
    )
    if active_save is not None:
        raise HTTPException(
            status_code=409,
            detail="Esta sessão já possui um save ativo",
        )

    game_save = models.GameSave(
        browser_session_id=browser_session.id,
        controlled_club_id=club.id,
        season_id=season.id,
    )
    db.add(game_save)
    db.commit()
    db.refresh(game_save)

    if new_token is not None:
        response.set_cookie(
            key=COOKIE_NAME,
            value=new_token,
            max_age=int(SESSION_LIFETIME / timedelta(seconds=1)),
            httponly=True,
            secure=os.getenv("COOKIE_SECURE", "0") == "1",
            samesite="lax",
        )
    return game_save


@router.get("/api/v1/saves/current", response_model=schemas.GameSaveRead)
def get_current_game_save(request: Request, db: Session = Depends(get_db)):
    browser_session = find_browser_session(
        db, request.cookies.get(COOKIE_NAME)
    )
    if browser_session is None:
        raise HTTPException(status_code=404, detail="Sessão de jogo não encontrada")
    game_save = (
        db.query(models.GameSave)
        .filter_by(browser_session_id=browser_session.id, status="active")
        .one_or_none()
    )
    if game_save is None:
        raise HTTPException(status_code=404, detail="Save ativo não encontrado")
    return game_save


def create_app(*, create_schema: bool = False, database_engine=engine) -> FastAPI:
    """Cria uma aplicação configurável sem acessar o banco durante o import."""

    mimetypes.add_type("image/webp", ".webp")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if create_schema:
            models.Base.metadata.create_all(bind=database_engine)
        yield

    application = FastAPI(lifespan=lifespan)
    application.mount("/static", StaticFiles(directory="static"), name="static")
    application.include_router(router)
    return application


app = create_app(create_schema=os.getenv("AUTO_CREATE_SCHEMA", "0") == "1")
