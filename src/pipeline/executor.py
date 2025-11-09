import logging

from src.errors import UnexpectedRuntimeError
from src.parser import parse_line
from src.reader import make_reader_for
from src.stats_collector import StatsCollector

logger = logging.getLogger("log-analyzer.pipeline")


def execute_pipeline(config):
    collector = StatsCollector(config.resolved_sources)
    for source in config.resolved_sources:
        logger.info("Читаю источник: %s", source)
        reader = make_reader_for(source)
        try:
            for line in reader.iter_lines():
                if not line or not line.strip():
                    continue
                entry = parse_line(line)
                if entry is None:
                    continue
                if config.date_from and entry.timestamp < config.date_from:
                    continue
                if config.date_to and entry.timestamp > config.date_to:
                    continue
                collector.update(entry)
        except UnexpectedRuntimeError as e:
            logger.error("Сбой при чтении источника %s: %s", source, e)
            raise
    return collector.build_result()
