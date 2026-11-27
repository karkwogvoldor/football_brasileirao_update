"""Persistência local das revisões do laboratório de cenas (somente desenvolvimento).

As revisões feitas no navegador são espelhadas em ``scene-reviews.json`` e as
respostas dos ajustes (escritas fora do navegador) ficam em ``scene-returns.json``.
Nenhum desses arquivos toca o banco de dados da aplicação.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REVIEW_DIR_ENV = "BRAFOOT_DEV_REVIEW_DIR"
DEFAULT_REVIEW_DIR = Path("data") / "dev"
REVIEWS_FILE = "scene-reviews.json"
RETURNS_FILE = "scene-returns.json"


def review_dir() -> Path:
    return Path(os.environ.get(REVIEW_DIR_ENV) or DEFAULT_REVIEW_DIR)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def load_scene_reviews() -> dict[str, Any]:
    """Retorna as revisões salvas e os retornos de ajuste por cena."""
    base = review_dir()
    return {
        "reviews": _read_json(base / REVIEWS_FILE),
        "returns": _read_json(base / RETURNS_FILE),
    }


def save_scene_reviews(reviews: dict[str, Any]) -> None:
    """Substitui o arquivo de revisões de forma atômica."""
    base = review_dir()
    base.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=base, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(reviews, handle, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp_name, base / REVIEWS_FILE)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def record_scene_return(
    scenario_id: str, from_version: int, to_version: int, summary: str
) -> None:
    """Registra que uma cena foi ajustada e está pronta para nova revisão."""
    if to_version <= from_version:
        raise ValueError("to_version deve ser maior que from_version")
    if not summary.strip():
        raise ValueError("summary não pode ser vazio")
    base = review_dir()
    base.mkdir(parents=True, exist_ok=True)
    returns = _read_json(base / RETURNS_FILE)
    returns[scenario_id] = {
        "from_version": from_version,
        "to_version": to_version,
        "summary": summary.strip(),
        "returned_at": datetime.now(timezone.utc).isoformat(),
    }
    (base / RETURNS_FILE).write_text(
        json.dumps(returns, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
