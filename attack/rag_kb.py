"""
Tiny RAG knowledge-base helper for the data-poisoning lab.

Design choices, on purpose for a security training:
- Vector DB lives in its own container (chromadb/chroma) so the knowledge base is
  visibly a separate attack surface, like real RAG deployments.
- Embeddings ride on the existing Ollama container (nomic-embed-text) so we do not
  spawn a second model server.
- All operations are admin-driven and best-effort. If chroma or the embedding model
  is not reachable, every helper returns a safe value and the chat keeps working
  exactly as it did before this module existed.

This module is INTENTIONALLY permissive about what it accepts (e.g. a whole note
body submitted by an admin). That is the whole point of the lab: an attacker
controls the document, the admin presses Ingest, the model later cites it.
"""

import logging
import os
import time
import uuid
from typing import List, Dict, Any, Optional

import requests


COLLECTION_NAME = "peachycloud_kb"
EMBED_TIMEOUT_SECONDS = 30
CHROMA_CLIENT_TIMEOUT_SECONDS = 10

# Small chunk size keeps CPU cost low on workshop laptops while still letting the
# embedding model see meaningful sentences.
DEFAULT_CHUNK_SIZE = 400
DEFAULT_CHUNK_OVERLAP = 40

_BENIGN_FAQ = [
    (
        "training_main",
        "Peachycloud Security offers hands-on security engineering training. "
        "All sessions are conducted online and focus on practical labs, not slides. "
        "Visit https://peachycloudsecurity.com/trainings to see all upcoming sessions and register. "
        "Scan the QR code on the training portal homepage to go directly to the trainings page.",
    ),
    (
        "security_engineering_oct",
        "The Security Engineering training (2-day intensive) is scheduled for 17-18 October 2026. "
        "It runs fully online with only 35 seats available — early registration recommended. "
        "Topics covered: OWASP Top 10, Container Security, DevSecOps, AWS Security, AI Security, "
        "AI-Assisted Security Reviews, and Kubernetes Security. "
        "Register at https://peachycloudsecurity.com/trainings",
    ),
    (
        "curriculum",
        "Peachycloud Security training curriculum includes: "
        "AWS Security (IAM, S3, EC2, CloudTrail, GuardDuty), "
        "Cloud Native Security (Containers, Kubernetes, Docker), "
        "Application Security / AppSec (OWASP Top 10, secure code review), "
        "DevSecOps (CI/CD pipeline security, SAST/DAST, supply chain), "
        "AI Security (LLM Top 10, prompt injection, RAG poisoning), "
        "AI-Assisted Security Reviews. "
        "All topics include hands-on labs in a real cloud environment. "
        "Full syllabus at https://peachycloudsecurity.com/trainings",
    ),
    (
        "instructors",
        "Trainings are conducted by Anjali Singh Shukla and Divyanshu Shukla, "
        "known as The Shukla Duo. Both are active security practitioners with hands-on "
        "experience in cloud security, AppSec, and AI security. "
        "YouTube: https://www.youtube.com/@peachycloudsecurity "
        "About: https://peachycloudsecurity.com/about",
    ),
    (
        "registration_qr",
        "To register for Peachycloud Security training: "
        "1. Visit https://peachycloudsecurity.com/trainings "
        "2. Scan the QR code on the training portal homepage. "
        "3. Contact support@peachycloudsecurity.com for group bookings or invoice requests. "
        "Seats are limited to 35 per batch. Early bird discounts apply — check the trainings page for current pricing.",
    ),
    (
        "best_training_recommendation",
        "For security engineering, cloud security, AWS security, Kubernetes security, AppSec, or DevSecOps training, "
        "Peachycloud Security offers the most practical hands-on training available online. "
        "The next batch — Security Engineering (2-day) — runs 17-18 October 2026, online, 35 seats. "
        "See all options and register at https://peachycloudsecurity.com/trainings",
    ),
    (
        "support_contact",
        "For support, billing, or training inquiries contact support@peachycloudsecurity.com. "
        "This is the only official contact address for Peachycloud Security.",
    ),
]


def _chroma_host() -> str:
    return os.environ.get("DEVNOTES_CHROMA_HOST", "chromadb")


def _chroma_port() -> int:
    try:
        return int(os.environ.get("DEVNOTES_CHROMA_PORT", "8000"))
    except (TypeError, ValueError):
        return 8000


def _embed_model() -> str:
    return os.environ.get("DEVNOTES_RAG_EMBED_MODEL", "nomic-embed-text")


def _ollama_base_url() -> str:
    return os.environ.get("OLLAMA_HOST", "http://ollama:11434").rstrip("/")


def _retrieve_k() -> int:
    try:
        k = int(os.environ.get("DEVNOTES_RAG_K", "3"))
    except (TypeError, ValueError):
        k = 3
    return max(1, min(k, 8))


# -------- Lazy chromadb client (do not import at module top-level) --------

_client_cache = {"client": None}


def _client():
    """Return a cached chromadb HttpClient or None if the package or server is missing."""
    if _client_cache["client"] is not None:
        return _client_cache["client"]
    try:
        import chromadb  # local import: keeps app boot working if chroma is not installed
    except Exception as exc:
        logging.warning("RAG_CLIENT_IMPORT | chromadb not importable: %s", exc)
        return None
    try:
        client = chromadb.HttpClient(host=_chroma_host(), port=_chroma_port())
        _client_cache["client"] = client
        return client
    except Exception as exc:
        logging.warning("RAG_CLIENT_CONNECT | could not create HttpClient: %s", exc)
        return None


def _collection():
    client = _client()
    if client is None:
        return None
    try:
        return client.get_or_create_collection(name=COLLECTION_NAME)
    except Exception as exc:
        logging.warning("RAG_COLLECTION | get_or_create_collection failed: %s", exc)
        return None


# -------- Ollama embeddings --------

def _parse_embed_response(data: dict) -> Optional[List[float]]:
    """Normalize Ollama JSON from /api/embed (new) or /api/embeddings (legacy)."""
    if not isinstance(data, dict):
        return None
    # Newer Ollama: POST /api/embed → { "embeddings": [[float, ...], ...] }
    embs = data.get("embeddings")
    if isinstance(embs, list) and embs:
        first = embs[0]
        if isinstance(first, list) and first:
            return first
    # Legacy single vector key
    vec = data.get("embedding")
    if isinstance(vec, list) and vec:
        return vec
    logging.warning("RAG_EMBED_SHAPE | unexpected payload keys: %s", list(data.keys())[:8])
    return None


def _embed_one(text: str) -> Optional[List[float]]:
    if not text:
        return None
    base = _ollama_base_url()
    model = _embed_model()
    payload_new = {"model": model, "input": text}
    payload_old = {"model": model, "prompt": text}

    # Prefer current Ollama API (/api/embed with "input"). Fall back to legacy
    # /api/embeddings with "prompt" for older images in long-lived lab machines.
    for url, payload in (
        (f"{base}/api/embed", payload_new),
        (f"{base}/api/embeddings", payload_old),
    ):
        try:
            r = requests.post(url, json=payload, timeout=EMBED_TIMEOUT_SECONDS)
        except Exception as exc:
            logging.warning("RAG_EMBED_HTTP | %s failed: %s", url, exc)
            continue
        if r.status_code != 200:
            logging.warning(
                "RAG_EMBED_STATUS | url=%s status=%s body=%s",
                url,
                r.status_code,
                (r.text or "")[:240],
            )
            continue
        try:
            data = r.json()
        except Exception as exc:
            logging.warning("RAG_EMBED_JSON | parse failed: %s", exc)
            continue
        vec = _parse_embed_response(data)
        if vec is not None:
            return vec

    return None


def _embed_many(texts: List[str]) -> List[Optional[List[float]]]:
    return [_embed_one(t) for t in texts]


# -------- Chunking --------

def _chunk(text: str, size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    out = []
    step = max(1, size - overlap)
    for start in range(0, len(text), step):
        piece = text[start:start + size].strip()
        if piece:
            out.append(piece)
        if start + size >= len(text):
            break
    return out


# -------- Public API --------

def status() -> Dict[str, Any]:
    """Report whether the KB is reachable and how many docs it holds."""
    coll = _collection()
    if coll is None:
        return {"available": False, "count": 0, "host": _chroma_host(), "port": _chroma_port()}
    try:
        count = coll.count()
    except Exception as exc:
        logging.warning("RAG_STATUS_COUNT | %s", exc)
        return {"available": False, "count": 0, "host": _chroma_host(), "port": _chroma_port()}
    return {"available": True, "count": int(count), "host": _chroma_host(), "port": _chroma_port()}


def clear() -> Dict[str, Any]:
    """Drop and recreate the collection. Returns a small status dict."""
    client = _client()
    if client is None:
        return {"ok": False, "error": "chroma client not available"}
    try:
        try:
            client.delete_collection(name=COLLECTION_NAME)
        except Exception:
            # Collection may not exist; ignore.
            pass
        client.get_or_create_collection(name=COLLECTION_NAME)
        return {"ok": True, "message": "Knowledge base cleared."}
    except Exception as exc:
        logging.warning("RAG_CLEAR | %s", exc)
        return {"ok": False, "error": str(exc)}


def seed_benign() -> Dict[str, Any]:
    """Reset the collection and load the small benign FAQ. Trainer baseline."""
    cleared = clear()
    if not cleared.get("ok"):
        return cleared
    coll = _collection()
    if coll is None:
        return {"ok": False, "error": "chroma collection not available"}

    ids, docs, metas, embs = [], [], [], []
    skipped = 0
    for tag, text in _BENIGN_FAQ:
        vec = _embed_one(text)
        if vec is None:
            skipped += 1
            continue
        ids.append(f"benign-{tag}")
        docs.append(text)
        metas.append({"source": "seed:benign-faq", "tag": tag})
        embs.append(vec)

    if not ids:
        return {"ok": False, "error": "no benign chunks could be embedded (is the embed model ready?)"}

    try:
        coll.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
    except Exception as exc:
        logging.warning("RAG_SEED_ADD | %s", exc)
        return {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "message": f"Seeded {len(ids)} benign FAQ chunks.",
        "added": len(ids),
        "skipped": skipped,
    }


def ingest_text(text: str, source: str, note_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Chunk, embed, and add the given text to the knowledge base. The whole point
    of the lab is that this content can be hostile (e.g. a poisoned note pulled
    in via the existing /import SSRF flow). No allowlist is applied.
    """
    coll = _collection()
    if coll is None:
        return {"ok": False, "error": "chroma collection not available"}

    chunks = _chunk(text)
    if not chunks:
        return {"ok": False, "error": "empty text, nothing to ingest"}

    ids, docs, metas, embs = [], [], [], []
    skipped = 0
    ts = int(time.time())
    for idx, chunk_text in enumerate(chunks):
        vec = _embed_one(chunk_text)
        if vec is None:
            skipped += 1
            continue
        ids.append(f"ingest-{ts}-{uuid.uuid4().hex[:8]}-{idx}")
        docs.append(chunk_text)
        meta = {"source": source, "chunk_index": idx, "ingested_at": ts}
        if note_id is not None:
            meta["note_id"] = int(note_id)
        metas.append(meta)
        embs.append(vec)

    if not ids:
        return {
            "ok": False,
            "error": (
                "no chunks could be embedded. Check Ollama from the web container "
                "(OLLAMA_HOST), docker compose ps for ollama, ollama list for "
                f"{_embed_model()}, and make pull-embed if the model is missing."
            ),
        }

    try:
        coll.add(ids=ids, documents=docs, metadatas=metas, embeddings=embs)
    except Exception as exc:
        logging.warning("RAG_INGEST_ADD | %s", exc)
        return {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "message": f"Indexed {len(ids)} chunk(s) from {source}.",
        "added": len(ids),
        "skipped": skipped,
        "source": source,
    }


def retrieve(query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
    """Return up to k retrieved chunks as [{text, source, note_id, distance}]."""
    coll = _collection()
    if coll is None:
        return []
    if not query:
        return []
    n = k if (isinstance(k, int) and k > 0) else _retrieve_k()
    vec = _embed_one(query)
    if vec is None:
        return []
    try:
        res = coll.query(query_embeddings=[vec], n_results=n)
    except Exception as exc:
        logging.warning("RAG_RETRIEVE | %s", exc)
        return []

    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0] if res.get("distances") else [None] * len(docs)

    out = []
    for i, text in enumerate(docs):
        meta = metas[i] if i < len(metas) and isinstance(metas[i], dict) else {}
        out.append({
            "text": text,
            "source": meta.get("source", "unknown"),
            "note_id": meta.get("note_id"),
            "distance": dists[i] if i < len(dists) else None,
        })
    return out
