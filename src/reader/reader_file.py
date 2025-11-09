import logging
from typing import Iterator

from src.errors import UnexpectedRuntimeError

from src.reader.base import Reader

logger = logging.getLogger("log-analyzer.reader.file")


class ReaderFile(Reader):
    def __init__(self, path: str, encoding: str = "utf-8") -> None:
        self._path = path
        self._encoding = encoding

    def iter_lines(self) -> Iterator[str]:
        logger.info("Чтение локального файла: %s", self._path)
        try:
            with open(self._path, "r", encoding=self._encoding) as f:
                for raw in f:
                    yield raw.rstrip("\r\n")
        except OSError as e:
            logger.error("Ошибка чтения '%s': %s", self._path, e)
            raise UnexpectedRuntimeError(f"Не удалось прочитать '{self._path}': {e}")
