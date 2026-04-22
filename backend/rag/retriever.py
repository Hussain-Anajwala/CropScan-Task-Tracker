"""Knowledge base retrieval for CropScan RAG."""

from __future__ import annotations

import json
from pathlib import Path
import re

from loguru import logger

from backend.config import settings
from backend.prompts import (
    RAG_CONTEXT_TEMPLATE,
    RAG_QUERY_FALLBACK,
    RAG_QUERY_PRIMARY,
    RAG_QUERY_SECONDARY,
)


def _load_manifest_records() -> list[dict[str, str]]:
    manifest_path = settings.resolve_path(settings.chroma_persist_dir) / "ingested_chunks.jsonl"
    if not manifest_path.exists():
        return []
    return [
        json.loads(line)
        for line in manifest_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _tokenize_query(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9_]+", text.lower()) if len(token) > 2]


def _score_text(query_tokens: list[str], text: str) -> int:
    haystack = text.lower()
    return sum(1 for token in query_tokens if token in haystack)


def retrieve_context(disease_name: str, crop_name: str, top_k: int = 5) -> str:
    """Retrieve relevant RAG context for a disease and crop query."""
    queries = [
        RAG_QUERY_PRIMARY.format(disease_name=disease_name, crop_name=crop_name),
        RAG_QUERY_SECONDARY.format(disease_name=disease_name, crop_name=crop_name),
        RAG_QUERY_FALLBACK.format(disease_name=disease_name, crop_name=crop_name),
    ]
    query_text = " ".join(queries).lower()
    query_tokens = _tokenize_query(query_text)

    try:
        from chromadb import PersistentClient

        client = PersistentClient(path=str(settings.resolve_path(settings.chroma_persist_dir)))
        collection = client.get_collection(name=settings.chroma_collection_name)
        results = collection.query(query_texts=queries, n_results=top_k)
        documents_by_query = results.get("documents", [])
        metadatas_by_query = results.get("metadatas", [])
        distances_by_query = results.get("distances", [])
        unique_chunks: dict[tuple[str, str], tuple[float, str]] = {}
        for documents, metadatas, distances in zip(documents_by_query, metadatas_by_query, distances_by_query, strict=False):
            for document, metadata, distance in zip(documents, metadatas, distances, strict=False):
                source_name = metadata.get("source", "unknown")
                score = 1.0 - float(distance or 0.0)
                key = (source_name, document)
                best = unique_chunks.get(key)
                if best is None or score > best[0]:
                    unique_chunks[key] = (score, document)

        chunks = []
        for (source_name, document), (score, _) in sorted(unique_chunks.items(), key=lambda item: item[1][0], reverse=True)[:top_k]:
            chunks.append(
                RAG_CONTEXT_TEMPLATE.format(
                    source_name=source_name,
                    relevance_score=score,
                    chunk_text=document,
                )
            )
        if chunks:
            logger.info("Retrieved {} context chunks from Chroma for disease='{}' crop='{}'", len(chunks), disease_name, crop_name)
            return "".join(chunks[:top_k])
    except Exception as exc:
        logger.warning("Chroma retrieval unavailable, falling back to manifest search: {}", exc)

    scored_records: list[tuple[int, dict[str, str]]] = []
    for record in _load_manifest_records():
        text = record.get("text", "")
        score = _score_text(query_tokens, text)
        if score > 0:
            scored_records.append((score, record))
    scored_records.sort(key=lambda item: item[0], reverse=True)
    context = "".join(
        RAG_CONTEXT_TEMPLATE.format(
            source_name=record.get("source", "unknown"),
            relevance_score=float(score),
            chunk_text=record.get("text", ""),
        )
        for score, record in scored_records[:top_k]
    )
    logger.info(
        "Retrieved {} context chunks from manifest for disease='{}' crop='{}'",
        min(len(scored_records), top_k),
        disease_name,
        crop_name,
    )
    return context
