import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

logger = logging.getLogger("log-analyzer.parser")


@dataclass
class LogEntry:
    ip: str
    timestamp: datetime
    method: str
    resource: str
    protocol: str
    status_code: int
    response_size: int
    date_str: str
    weekday: str


_LOG_PATTERN = re.compile(
    r"^(?P<ip>\S+)\s+-\s+(?P<remote_user>\S+)\s+\[(?P<time_local>[^\]]+)\]\s+"
    r'"(?P<method>\S+)\s+(?P<resource>\S+)\s+(?P<protocol>[^"]+)"\s+'
    r'(?P<status>\d{3})\s+(?P<size>\S+)\s+"(?P<referer>[^"]*)"\s+"(?P<user_agent>[^"]*)"$'
)


def _parse_timestamp(raw_time: str) -> datetime:
    dt = datetime.strptime(raw_time, "%d/%b/%Y:%H:%M:%S %z")
    return dt


def parse_line(raw_line: str) -> Optional[LogEntry]:
    m = _LOG_PATTERN.match(raw_line)
    if not m:
        logger.warning(
            "Строка не соответствует формату и будет пропущена: %r", raw_line
        )
        return None
    try:
        ts = _parse_timestamp(m.group("time_local"))
        size_str = m.group("size")
        response_size = 0 if size_str == "-" else int(size_str)
        status = int(m.group("status"))
        protocol = m.group("protocol").strip()
        entry = LogEntry(
            ip=m.group("ip"),
            timestamp=ts,
            method=m.group("method"),
            resource=m.group("resource"),
            protocol=protocol,
            status_code=status,
            response_size=response_size,
            date_str=ts.date().isoformat(),
            weekday=ts.strftime("%A"),
        )
        return entry
    except Exception as e:
        logger.warning("Ошибка парсинга, пропускаем. Строка=%r Ошибка=%s", raw_line, e)
        return None
