import os

from src.errors import UnexpectedRuntimeError


def write_report(path: str, content: str) -> None:
    try:
        parent = os.path.dirname(os.path.abspath(path)) or "."
        os.makedirs(parent, exist_ok=True)  # ← ВАЖНО
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        raise UnexpectedRuntimeError(f"Не удалось записать отчёт в '{path}': {e}")
