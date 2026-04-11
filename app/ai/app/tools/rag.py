from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import List

import chromadb

from app.schemas import EvidenceItem


class RagStore:
    def __init__(self) -> None:
        chroma_path = os.getenv("CHROMA_PATH", "./.chroma")
        self.docs_dir = Path(os.getenv("RESEARCH_DATA_DIR", "./data"))
        self.client = chromadb.PersistentClient(path=chroma_path)
        self.collection = self.client.get_or_create_collection("research_docs")

    def seed_if_empty(self) -> None:
        count = self.collection.count()
        if count > 0 or not self.docs_dir.exists():
            return

        for path in self.docs_dir.rglob("*"):
            if path.suffix.lower() not in {".md", ".txt"}:
                continue
            text = path.read_text(encoding="utf-8")
            chunks = self._chunk_text(text)
            for index, chunk in enumerate(chunks):
                self.collection.add(
                    ids=[self._doc_id(path, index)],
                    documents=[chunk],
                    metadatas=[
                        {
                            "title": path.stem.replace("_", " "),
                            "url": f"file://{path}",
                            "source_type": "internal_doc",
                            "chunk_index": index,
                        }
                    ],
                )

    def retrieve(self, query: str, limit: int = 4) -> List[EvidenceItem]:
        self.seed_if_empty()
        if self.collection.count() == 0:
            return []

        results = self.collection.query(query_texts=[query], n_results=limit)
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        evidence: List[EvidenceItem] = []
        for document, metadata in zip(documents, metadatas, strict=False):
            evidence.append(
                EvidenceItem(
                    title=str(metadata.get("title", "Internal research document")),
                    url=str(metadata.get("url", "internal://document")),
                    snippet=document[:1000],
                    source_type="internal_doc",
                    score=0.65,
                )
            )
        return evidence

    def _chunk_text(self, text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            chunks.append(text[start:end])
            if end == len(text):
                break
            start = max(0, end - overlap)
        return chunks

    def _doc_id(self, path: Path, index: int) -> str:
        return hashlib.sha1(f"{path}:{index}".encode("utf-8")).hexdigest()
