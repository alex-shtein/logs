import logging
from typing import Iterator

import requests
from src.errors import UnexpectedRuntimeError

from src.reader.base import Reader

logger = logging.getLogger("log-analyzer.reader.url")


class ReaderURL(Reader):
    def __init__(self, url: str, timeout: float = 5.0) -> None:
        self._url = url
        self._timeout = timeout

    def iter_lines(self) -> Iterator[str]:
        logger.info("Чтение удалённого лога: %s", self._url)
        try:
            with requests.get(self._url, stream=True, timeout=self._timeout) as resp:
                if resp.status_code >= 400:
                    logger.error(
                        "Статус %s при чтении '%s'", resp.status_code, self._url
                    )
                    raise UnexpectedRuntimeError(
                        f"Статус {resp.status_code} при чтении '{self._url}'"
                    )
                for raw in resp.iter_lines(decode_unicode=True):
                    if raw is None:
                        continue
                    yield str(raw).rstrip("\r\n")
        except requests.RequestException as e:
            logger.error("Сетевая ошибка '%s': %s", self._url, e)
            raise UnexpectedRuntimeError(f"Сетевая ошибка '{self._url}': {e}")
