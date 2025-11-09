import sys

import logging

from src.cli.args import parse_args
from src.config import build_app_config
from src.errors import BadUsageError
from src.errors import UnexpectedRuntimeError
from src.exit_codes import ExitCode
from src.formatters.registry import get_formatter
from src.logging_setup import setup_logging
from src.pipeline.executor import execute_pipeline
from src.report_writer import write_report
from src.validator import Validator

logger = logging.getLogger("log-analyzer")


def run(argv=None) -> int:
    setup_logging()
    try:
        args = parse_args(argv)
        validator = Validator()
        config = build_app_config(args, validator)

        logger.info("Параметры успешно проверены.")
        logger.info("Формат отчета: %s", config.output_format)
        logger.info("Выходной файл: %s", config.output_path)
        logger.info("Источник логов: %s", config.input_path)
        if config.date_from:
            logger.info("--from: %s", config.date_from.isoformat())
        if config.date_to:
            logger.info("--to: %s", config.date_to.isoformat())

        result = execute_pipeline(config)
        formatter = get_formatter(config.output_format)
        report = formatter.format(result)
        write_report(config.output_path, report)
        return ExitCode.OK

    except SystemExit as e:
        code = getattr(e, "code", 1)
        return ExitCode.BAD_USAGE if code == 2 else ExitCode.UNEXPECTED_ERROR
    except BadUsageError as e:
        logger.error("Некорректное использование программы: %s", e)
        return ExitCode.BAD_USAGE
    except UnexpectedRuntimeError as e:
        logger.error("Непредвиденная ошибка исполнения: %s", e)
        return ExitCode.UNEXPECTED_ERROR
    except Exception:
        logger.exception("Непредвиденная ошибка (неперехваченное исключение)")
        return ExitCode.UNEXPECTED_ERROR


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
