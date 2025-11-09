from urllib.parse import urlparse

from src.reader.base import Reader
from src.reader.reader_file import ReaderFile
from src.reader.reader_url import ReaderURL


def make_reader_for(source: str) -> Reader:
    if urlparse(source).scheme in ("http", "https"):
        return ReaderURL(source)
    return ReaderFile(source)
