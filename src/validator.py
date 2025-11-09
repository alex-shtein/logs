import datetime as dt
import glob
import re
import os
from urllib.parse import urlparse

import requests
from src.errors import BadUsageError
from src.errors import RemoteResourceNotFoundError
from src.errors import UnexpectedRuntimeError


# Поддерживаемые форматы отчёта и ожидаемые расширения выходного файла
SUPPORTED_FORMATS = {"json", "markdown", "adoc"}
EXPECTED_EXTENSION = {"json": ".json", "markdown": ".md", "adoc": ".ad"}


class Validator:
    """Валидация параметров CLI и подготовка источников."""

    # --------------------------- формат/выход ---------------------------

    def validate_output_format(self, fmt: str) -> str:
        if not fmt:
            raise BadUsageError("Не указан формат вывода")
        key = fmt.strip().lower()
        if key not in SUPPORTED_FORMATS:
            raise BadUsageError(
                f"Неподдерживаемый формат '{fmt}'. Допустимо: {', '.join(sorted(SUPPORTED_FORMATS))}"
            )
        return key

    def validate_output_path(self, out_path: str, out_fmt: str) -> None:
        expected_ext = EXPECTED_EXTENSION.get(out_fmt)
        if not expected_ext:
            raise BadUsageError(f"Неизвестный формат '{out_fmt}'")
        if not out_path.endswith(expected_ext):
            raise BadUsageError(
                f"Файл вывода должен иметь расширение '{expected_ext}' для формата '{out_fmt}'"
            )
        if os.path.exists(out_path):
            raise BadUsageError(
                f"Файл '{out_path}' уже существует. Перезапись запрещена."
            )
        parent = os.path.dirname(os.path.abspath(out_path)) or "."
        if not os.path.isdir(parent):
            raise BadUsageError(f"Директория '{parent}' не существует")
        if not os.access(parent, os.W_OK):
            raise BadUsageError(f"Нет прав на запись в директорию '{parent}'")

    # --------------------------- даты/диапазон ---------------------------

    def parse_from(self, raw: str | None) -> dt.datetime | None:
        """Парсит --from. Если введён только день (YYYY-MM-DD), вернёт начало дня в UTC."""
        return self._parse_iso8601(raw, is_end=False)

    def parse_to(self, raw: str | None) -> dt.datetime | None:
        """Парсит --to. Если введён только день (YYYY-MM-DD), вернёт конец дня в UTC."""
        return self._parse_iso8601(raw, is_end=True)

    def _parse_iso8601(self, raw: str | None, is_end: bool) -> dt.datetime | None:
        """
        Поддерживает:
          - 'YYYY-MM-DD' (день)
          - 'YYYY-MM-DDTHH:MM[:SS[.ffffff]][±HH:MM]'
        Без таймзоны трактуется как UTC. Для day-only:
          - is_end=False -> 00:00:00
          - is_end=True  -> 23:59:59.999999
        """
        if raw is None:
            return None
        try:
            d = dt.datetime.fromisoformat(raw)
        except ValueError:
            raise BadUsageError(
                f"Некорректный формат даты '{raw}'. Ожидается ISO8601 "
                "(YYYY-MM-DD или YYYY-MM-DDTHH:MM[:SS])"
            )

        is_date_only = ("T" not in raw) and (len(raw) == 10)

        # Приводим к aware: если tz не указана — считаем UTC.
        if d.tzinfo is None:
            d = d.replace(tzinfo=dt.timezone.utc)

        if is_date_only:
            if is_end:
                d = d.replace(hour=23, minute=59, second=59, microsecond=999_999)
            else:
                d = d.replace(hour=0, minute=0, second=0, microsecond=0)

        return d

    def validate_date_range(
        self, date_from: dt.datetime | None, date_to: dt.datetime | None
    ) -> None:
        """
        Проверяет корректность диапазона. Разрешено равенство (from == to).
        Бросает BadUsageError если from > to.
        """
        if date_from and date_to and date_from > date_to:
            raise BadUsageError(
                f"--from ({date_from.isoformat()}) должен быть меньше или равен --to ({date_to.isoformat()})"
            )

    # --------------------------- источники ---------------------------

    @staticmethod
    def is_url(value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in ("http", "https")

    def resolve_sources(self, path: str) -> list[str]:
        """Возвращает список источников: локальные файлы по шаблону или один URL."""
        if self.is_url(path):
            return self._validate_remote_url(path)
        return self._resolve_local_paths(path)

    def _resolve_local_paths(self, pattern: str) -> list[str]:
        """Проверка/развёртывание локального пути/шаблона. Допустимы .log и .txt."""

        # --- 1. Нормализуем странные паттерны вроде logs**.txt ---
        def _normalize_recursive_pattern(p: str) -> str:
            # заменяем logs**.txt → logs/**/*.txt
            if "**" in p and not p.endswith("/**") and not p.endswith("/**/"):
                # если нет / перед ** — добавляем
                p = re.sub(r"(?<!/)\*\*", r"/**", p)
                # если нет /*.ext после ** — добавляем
                p = re.sub(r"/\*\*\.(\w+)$", r"/**/*.\1", p)
            return p

        # --- 2. Проверка шаблона ---
        if glob.has_magic(pattern):
            normalized = _normalize_recursive_pattern(pattern)
            recursive = "**" in normalized
            matched = glob.glob(normalized, recursive=recursive)

            if not matched:
                raise BadUsageError(
                    f"По шаблону '{pattern}' не найдено ни одного файла"
                )

            files: list[str] = []
            for f in matched:
                if not os.path.isfile(f):
                    continue  # пропускаем директории
                if not (f.endswith(".log") or f.endswith(".txt")):
                    raise BadUsageError(
                        f"Файл '{f}' имеет неподдерживаемое расширение (ожидается .log или .txt)"
                    )
                files.append(f)

            if not files:
                raise BadUsageError(
                    f"По шаблону '{pattern}' не найдено ни одного файла"
                )
            return files

        # --- 3. Конкретный путь ---
        if not os.path.exists(pattern):
            raise BadUsageError(f"Файл '{pattern}' не найден")
        if not os.path.isfile(pattern):
            raise BadUsageError(f"'{pattern}' не является обычным файлом")
        if not (pattern.endswith(".log") or pattern.endswith(".txt")):
            raise BadUsageError(
                f"Файл '{pattern}' имеет неподдерживаемое расширение (ожидается .log или .txt)"
            )
        return [pattern]

    def _validate_remote_url(self, url: str) -> list[str]:
        """HEAD-проверка удалённого ресурса. 404 -> BadUsage; 2xx/3xx -> OK; иначе Unexpected."""
        try:
            resp = requests.head(url, allow_redirects=True, timeout=5)
        except requests.RequestException as e:
            raise UnexpectedRuntimeError(
                f"Не удалось проверить удалённый ресурс '{url}': {e}"
            )
        if resp.status_code == 404:
            raise RemoteResourceNotFoundError(
                f"Удалённый ресурс '{url}' не найден (404)"
            )
        if 200 <= resp.status_code < 400:
            return [url]
        raise UnexpectedRuntimeError(
            f"Неожиданный статус при проверке удалённого ресурса '{url}': {resp.status_code}"
        )
