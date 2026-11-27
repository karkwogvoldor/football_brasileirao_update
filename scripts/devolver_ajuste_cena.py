"""Registra o retorno de um ajuste de cena para nova revisão no laboratório.

Uso: venv\Scripts\python.exe scripts\devolver_ajuste_cena.py ID DE PARA "resumo"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brafoot.presentation.review_store import record_scene_return  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print(__doc__)
        return 2
    record_scene_return(argv[1], int(argv[2]), int(argv[3]), argv[4])
    print(f"Retorno registrado para {argv[1]} (v{argv[2]} -> v{argv[3]}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
