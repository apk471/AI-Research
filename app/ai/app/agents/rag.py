from __future__ import annotations

from app.schemas import EvidenceItem
from app.tools.rag import RagStore


class RagAgent:
    def __init__(self, store: RagStore) -> None:
        self.store = store

    async def run(self, query: str) -> list[EvidenceItem]:
        return self.store.retrieve(query)
