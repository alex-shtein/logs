import datetime as dt
from dataclasses import dataclass
from typing import List
from typing import Optional

from src.validator import Validator


@dataclass
class AppConfig:
    input_path: str
    resolved_sources: List[str]
    output_path: str
    output_format: str
    date_from: Optional[dt.datetime]
    date_to: Optional[dt.datetime]


def build_app_config(args, validator: Validator) -> AppConfig:
    """
    Строит и валидирует конфигурацию приложения на основе CLI-аргументов.
    - проверяет формат вывода и корректность выходного файла
    - парсит --from/--to (UTC-aware; для date-only расширяет до начала/конца дня)
    - валидирует диапазон дат
    - разворачивает источник(и): локальный путь/шаблон или URL
    """
    output_format = validator.validate_output_format(args.out_format)
    validator.validate_output_path(args.output, output_format)

    date_from = validator.parse_from(args.date_from)
    date_to = validator.parse_to(args.date_to)
    validator.validate_date_range(date_from, date_to)

    resolved_sources = validator.resolve_sources(args.path)

    return AppConfig(
        input_path=args.path,
        resolved_sources=resolved_sources,
        output_path=args.output,
        output_format=output_format,
        date_from=date_from,
        date_to=date_to,
    )
