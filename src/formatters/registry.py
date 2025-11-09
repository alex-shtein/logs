from src.errors import BadUsageError

from src.formatters.adoc_formatter import AdocFormatter
from src.formatters.json_formatter import JsonFormatter
from src.formatters.markdown_formatter import MarkdownFormatter


def get_formatter(name: str):
    key = (name or "").strip().lower()
    if key == "json":
        return JsonFormatter()
    if key == "markdown":
        return MarkdownFormatter()
    if key == "adoc":
        return AdocFormatter()
    raise BadUsageError(f"Неподдерживаемый формат: {name}")
