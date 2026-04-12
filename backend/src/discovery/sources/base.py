from typing import Protocol

from src.db.models import RawItem


class Source(Protocol):
    source_name: str

    async def fetch(self) -> list[RawItem]: ...
