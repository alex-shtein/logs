from abc import ABC
from abc import abstractmethod
from typing import Iterator


class Reader(ABC):
    @abstractmethod
    def iter_lines(self) -> Iterator[str]:
        raise NotImplementedError
