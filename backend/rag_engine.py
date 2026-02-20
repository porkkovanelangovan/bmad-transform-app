"""
RAG Engine — Document persistence, chunking, embedding, and semantic retrieval.
Stores embeddings as JSON arrays (works on both SQLite and PostgreSQL without extensions).
Uses OpenAI text-embedding-3-small for embeddings, falls back to keyword search.
"""

import json
import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)


# ─── Text Chunking ───────────────────────────────────────────────────────────


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> List[str]:
    """Split text into overlapping chunks by word count."""
    if not text or not text.strip():
        return []
    words = text.split()
    if len(words) <= chunk_size:
        return [text.strip()]
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
        i += chunk_size - overlap
    return chunks


# ─── Embedding Generation ────────────────────────────────────────────────────


async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings using OpenAI text-embedding-3-small."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set")
    from openai import AsyncOpenAI

    client = AsyncOpenAI()
    # Process in batches of 20 to avoid rate limits
    all_embeddings = []
    for i in range(0, len(texts), 20):
        batch = texts[i : i + 20]
        response = await client.embeddings.create(
            model="text-embedding-3-small", input=batch
        )
        all_embeddings.extend([item.embedding for item in response.data])
    return all_embeddings


# ─── Cosine Similarity ───────────────────────────────────────────────────────


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ─── Document Storage ────────────────────────────────────────────────────────


async def store_document(
    db,
    org_id: int,
    filename: str,
    file_type: str,
    content_text: str,
    doc_category: str = "general",
    upload_source: str = "manual",
    step_number: int = None,
) -> int:
    """Store a document with its text, chunk it, and generate embeddings."""
    if not content_text or not content_text.strip():
        return 0

    # Truncate very large documents to 50K chars for storage
    stored_text = content_text[:50000]

    # Insert document record
    doc_id = await db.execute(
        "INSERT INTO org_documents (org_id, filename, file_type, content_text, "
        "doc_category, upload_source, step_number) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [org_id, filename, file_type, stored_text, doc_category, upload_source, step_number],
    )
    await db.commit()

    # Chunk text
    chunks = chunk_text(content_text)
    if not chunks:
        return doc_id

    # Try to generate embeddings
    embeddings = None
    try:
        embeddings = await generate_embeddings(chunks)
        logger.info("Generated %d embeddings for %s", len(embeddings), filename)
    except Exception as e:
        logger.warning("Embedding generation failed for %s: %s (storing without embeddings)", filename, e)

    # Store chunks
    for idx, chunk in enumerate(chunks):
        embedding_json = json.dumps(embeddings[idx]) if embeddings and idx < len(embeddings) else None
        await db.execute(
            "INSERT INTO document_chunks (document_id, chunk_index, chunk_text, "
            "embedding_json, token_count) VALUES (?, ?, ?, ?, ?)",
            [doc_id, idx, chunk, embedding_json, len(chunk.split())],
        )
    await db.commit()
    return doc_id


# ─── Semantic Retrieval ──────────────────────────────────────────────────────


async def retrieve_relevant_chunks(
    db,
    query: str,
    org_id: int = None,
    top_k: int = 10,
    doc_category: str = None,
) -> List[dict]:
    """Retrieve most relevant document chunks for a query using cosine similarity."""
    # Try semantic search first
    try:
        query_embedding = (await generate_embeddings([query]))[0]
    except Exception as e:
        logger.warning("Query embedding failed: %s — falling back to keyword search", e)
        return await _keyword_search(db, query, org_id, top_k, doc_category)

    # Get all chunks with embeddings for this org
    where_parts = ["dc.embedding_json IS NOT NULL"]
    params = []
    if org_id:
        where_parts.append("od.org_id = ?")
        params.append(org_id)
    if doc_category:
        where_parts.append("od.doc_category = ?")
        params.append(doc_category)

    where = " AND ".join(where_parts)
    rows = await db.execute_fetchall(
        f"SELECT dc.id, dc.chunk_text, dc.embedding_json, od.filename, od.doc_category "
        f"FROM document_chunks dc "
        f"JOIN org_documents od ON dc.document_id = od.id "
        f"WHERE {where}",
        params,
    )

    # Compute similarities
    results = []
    for row in rows:
        row_dict = dict(row)
        try:
            embedding = json.loads(row_dict.get("embedding_json", "[]"))
            if embedding:
                sim = cosine_similarity(query_embedding, embedding)
                row_dict["similarity"] = sim
                results.append(row_dict)
        except Exception:
            continue

    # Sort by similarity descending, return top_k
    results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    return results[:top_k]


async def _keyword_search(
    db, query: str, org_id: int, top_k: int, doc_category: str
) -> List[dict]:
    """Fallback keyword search when embeddings are unavailable."""
    where_parts = []
    params = []
    if org_id:
        where_parts.append("od.org_id = ?")
        params.append(org_id)
    if doc_category:
        where_parts.append("od.doc_category = ?")
        params.append(doc_category)

    # Extract keywords from query
    keywords = [w for w in query.lower().split() if len(w) > 3][:5]
    if keywords:
        kw_clauses = ["LOWER(dc.chunk_text) LIKE ?" for _ in keywords]
        where_parts.append("(" + " OR ".join(kw_clauses) + ")")
        params.extend(f"%{kw}%" for kw in keywords)

    where = " AND ".join(where_parts) if where_parts else "1=1"
    rows = await db.execute_fetchall(
        f"SELECT dc.id, dc.chunk_text, od.filename, od.doc_category "
        f"FROM document_chunks dc "
        f"JOIN org_documents od ON dc.document_id = od.id "
        f"WHERE {where} LIMIT ?",
        params + [top_k],
    )
    return [dict(r) for r in rows]


# ─── RAG Context Builder ─────────────────────────────────────────────────────


async def build_rag_context(
    db,
    query: str,
    org_id: int = None,
    top_k: int = 8,
    doc_category: str = None,
) -> str:
    """Build a context string from retrieved chunks for inclusion in AI prompts."""
    chunks = await retrieve_relevant_chunks(db, query, org_id, top_k, doc_category)
    if not chunks:
        return ""

    parts = []
    for chunk in chunks:
        source = chunk.get("filename", "Unknown")
        category = chunk.get("doc_category", "general")
        text = chunk.get("chunk_text", "")
        sim = chunk.get("similarity")
        header = f"[Source: {source} | Type: {category}"
        if sim is not None:
            header += f" | Relevance: {sim:.2f}"
        header += "]"
        parts.append(f"{header}\n{text}")

    return "\n\n---\n\n".join(parts)


# ─── Data Mode Helpers ───────────────────────────────────────────────────────


async def get_org_data_mode(db) -> str:
    """Get the current organization's data_mode ('demo' or 'live')."""
    row = await db.execute_fetchone("SELECT data_mode FROM organization LIMIT 1")
    if row:
        return row.get("data_mode", "demo") or "demo"
    return "demo"


async def is_live_mode(db) -> bool:
    """Check if the organization is in live (RAG-enabled) mode."""
    return (await get_org_data_mode(db)) == "live"
