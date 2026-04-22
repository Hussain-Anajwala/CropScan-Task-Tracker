"""Knowledge base ingestion for CropScan RAG."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from loguru import logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import settings


def ingest_documents(source_dir: str | Path, persist_dir: str | Path | None = None) -> int:
    """Ingest PDF documents into ChromaDB with a JSONL fallback manifest."""
    source_path = Path(source_dir)
    if not source_path.is_absolute():
        source_path = settings.project_root / source_path
    persist_path = settings.resolve_path(str(persist_dir or settings.chroma_persist_dir))
    persist_path.mkdir(parents=True, exist_ok=True)
    manifest_path = persist_path / "ingested_chunks.jsonl"
    pdf_files = sorted(path for path in source_path.rglob("*") if path.is_file() and path.suffix.lower() == ".pdf")

    try:
        from chromadb import PersistentClient
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
    except Exception as exc:
        logger.warning("RAG dependencies unavailable, using JSONL-only ingestion fallback: {}", exc)
        PersistentClient = None
        SentenceTransformerEmbeddingFunction = None
        PyPDFLoader = None
        RecursiveCharacterTextSplitter = None

    collection = None
    if PersistentClient and SentenceTransformerEmbeddingFunction:
        try:
            client = PersistentClient(path=str(persist_path))
            embedding_function = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            collection = client.get_or_create_collection(
                name=settings.chroma_collection_name,
                embedding_function=embedding_function,
            )
            logger.info("Using Chroma collection '{}'", settings.chroma_collection_name)
        except Exception as exc:
            logger.warning("Chroma embedding setup unavailable, using JSONL-only ingestion fallback: {}", exc)
            collection = None

    splitter = (
        RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=64)
        if RecursiveCharacterTextSplitter
        else None
    )

    total_chunks = 0
    total_documents = 0
    with manifest_path.open("w", encoding="utf-8") as manifest_file:
        for pdf_path in pdf_files:
            if PyPDFLoader and splitter:
                documents = PyPDFLoader(str(pdf_path)).load()
                chunks = splitter.split_documents(documents)
                records = [
                    {
                        "id": f"{pdf_path.stem}-{index}",
                        "text": chunk.page_content,
                        "source": pdf_path.name,
                        "path": str(pdf_path.relative_to(source_path)),
                    }
                    for index, chunk in enumerate(chunks)
                ]
            else:
                records = [
                    {
                        "id": f"{pdf_path.stem}-0",
                        "text": f"Placeholder text extracted from {pdf_path.name}",
                        "source": pdf_path.name,
                        "path": str(pdf_path.relative_to(source_path)),
                    }
                ]

            for record in records:
                manifest_file.write(json.dumps(record) + "\n")

            if collection and records:
                collection.add(
                    ids=[record["id"] for record in records],
                    documents=[record["text"] for record in records],
                    metadatas=[{"source": record["source"], "path": record["path"]} for record in records],
                )

            total_documents += 1
            total_chunks += len(records)
            logger.info("Ingested {} chunks from {}", len(records), pdf_path.name)

    if not pdf_files:
        logger.warning("No PDF files found under {}", source_path)
    logger.info("Ingestion complete: {} documents, {} chunks", total_documents, total_chunks)
    return total_chunks


def main() -> None:
    """CLI entry point for ingestion."""
    parser = argparse.ArgumentParser(description="Ingest crop advisory PDFs into ChromaDB.")
    parser.add_argument("--source", type=Path, default=Path("data/knowledge_base"))
    parser.add_argument("--persist-dir", type=Path, default=Path(settings.chroma_persist_dir))
    args = parser.parse_args()
    total = ingest_documents(args.source, args.persist_dir)
    logger.info("Total chunks ingested: {}", total)


if __name__ == "__main__":
    main()
