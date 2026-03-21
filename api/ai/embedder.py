import json
import os
import math
from typing import Any

from dotenv import load_dotenv

from .models import ExtractedSkill, JDSkill

_onet_cache = None
_onet_index_cache = None
_embedding_client = None
_embedding_cache: dict[str, list[float]] = {}
_embedding_enabled: bool | None = None

load_dotenv()

EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2-preview")
EMBEDDING_THRESHOLD = float(os.getenv("GEMINI_EMBEDDING_THRESHOLD", "0.82"))
EMBEDDING_BATCH_SIZE = int(os.getenv("GEMINI_EMBEDDING_BATCH_SIZE", "32"))
EMBEDDING_MAX_CANDIDATES = int(os.getenv("GEMINI_EMBEDDING_MAX_CANDIDATES", "128"))
EMBEDDING_OUTPUT_DIMENSIONALITY = int(os.getenv("GEMINI_EMBEDDING_OUTPUT_DIMENSIONALITY", "768"))

# Common tech skill names → O*NET IDs that don't have exact title matches
# These handle cases where LLM extracts "Java" but O*NET titles it differently
COMMON_SKILL_ALIASES = {
    "java": "TECH-b6e13ad53d8e",  # Map to JavaScript as closest; Java not in O*NET separately
    "sql": "TECH-519968cbed98",  # Map to PostgreSQL
    "rest api": "TECH-90de35a5800e",  # Map to Node.js
    "rest apis": "TECH-90de35a5800e",
    "restful api": "TECH-90de35a5800e",
    "restful apis": "TECH-90de35a5800e",
    "api design": "TECH-90de35a5800e",
    "grpc": "TECH-90de35a5800e",
    "machine learning": "TECH-4235227b5143",  # Map to Python (ML uses Python)
    "ml": "TECH-4235227b5143",
    "deep learning": "TECH-3d3f421e9db6",  # Map to TensorFlow
    "artificial intelligence": "TECH-4235227b5143",
    "ai": "TECH-4235227b5143",
    "aws": "TECH-ba324ca7b1c7",  # Map to Linux (cloud = infra)
    "amazon web services": "TECH-ba324ca7b1c7",
    "azure": "TECH-ba324ca7b1c7",
    "microsoft azure": "TECH-ba324ca7b1c7",
    "gcp": "TECH-ba324ca7b1c7",
    "google cloud": "TECH-ba324ca7b1c7",
    "google cloud platform": "TECH-ba324ca7b1c7",
    "cloud": "TECH-ba324ca7b1c7",
    "cloud infrastructure": "TECH-ba324ca7b1c7",
    "cloud computing": "TECH-ba324ca7b1c7",
    "devops": "TECH-e982f17bcbe0",  # Map to Docker
    "ci/cd": "TECH-e982f17bcbe0",
    "cicd": "TECH-e982f17bcbe0",
    "continuous integration": "TECH-e982f17bcbe0",
    "continuous deployment": "TECH-e982f17bcbe0",
    "html": "TECH-b6e13ad53d8e",  # Map to JavaScript (web)
    "css": "TECH-b6e13ad53d8e",
    "html/css": "TECH-b6e13ad53d8e",
    "html5": "TECH-b6e13ad53d8e",
    "css3": "TECH-b6e13ad53d8e",
    "angular": "TECH-b6e13ad53d8e",
    "vue": "TECH-b6e13ad53d8e",
    "vue.js": "TECH-b6e13ad53d8e",
    "jenkins": "TECH-e982f17bcbe0",
    "terraform": "TECH-adc1f5c8707f",
    "ansible": "TECH-ba324ca7b1c7",
    "rust": "TECH-372946aa2608",  # Map to C++ (systems lang)
    "agile": "TECH-46f1a0bd5592",  # Map to Git (methodology)
    "scrum": "TECH-46f1a0bd5592",
    "data analysis": "TECH-4235227b5143",
    "data science": "TECH-4235227b5143",
    "data visualization": "TECH-4235227b5143",
    "data engineering": "TECH-4235227b5143",
    "microservices": "TECH-e982f17bcbe0",
    "containerization": "TECH-e982f17bcbe0",
    "kafka": "TECH-5dd9422f45dc",
    "communication": "TECH-46f1a0bd5592",  # soft skill → generic mapping
    "problem solving": "TECH-4235227b5143",
    "teamwork": "TECH-46f1a0bd5592",
    "leadership": "TECH-46f1a0bd5592",
    "react": "TECH-6b810c90aa9a",
    "react.js": "TECH-6b810c90aa9a",
    "reactjs": "TECH-6b810c90aa9a",
    "node": "TECH-90de35a5800e",
    "node.js": "TECH-90de35a5800e",
    "nodejs": "TECH-90de35a5800e",
    "express": "TECH-90de35a5800e",
    "express.js": "TECH-90de35a5800e",
    "postgresql": "TECH-519968cbed98",
    "postgres": "TECH-519968cbed98",
    "mysql": "TECH-f460c882a18c",
    "mongodb": "TECH-7f1c982e835a",
}


def _normalize_text(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _tokenize(text: str) -> list[str]:
    normalized = _normalize_text(text)
    tokens = []
    for raw in normalized.replace("/", " ").replace("-", " ").replace(".", " ").split():
        if len(raw) >= 2:
            tokens.append(raw)
    return tokens


def _normalize_vector(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in values))
    if norm == 0:
        return values
    return [v / norm for v in values]


def _dot_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return -1.0
    return sum(x * y for x, y in zip(a, b))


def _get_embedding_client():
    global _embedding_client
    if _embedding_client is not None:
        return _embedding_client

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None

    try:
        from google import genai
        _embedding_client = genai.Client(api_key=api_key)
    except Exception:
        return None
    return _embedding_client


def _is_embedding_enabled() -> bool:
    global _embedding_enabled
    if _embedding_enabled is not None:
        return _embedding_enabled

    flag = os.getenv("ENABLE_GEMINI_EMBEDDING_MATCH", "true").strip().lower()
    if flag in {"0", "false", "no", "off"}:
        _embedding_enabled = False
        return False

    _embedding_enabled = _get_embedding_client() is not None
    return _embedding_enabled


def _extract_values(embedding_obj: Any) -> list[float] | None:
    values = getattr(embedding_obj, "values", None)
    if values is None and isinstance(embedding_obj, dict):
        values = embedding_obj.get("values")
    if not values:
        return None
    return [float(v) for v in values]


def _embed_texts(texts: list[str], task_type: str) -> dict[str, list[float]]:
    client = _get_embedding_client()
    if client is None:
        return {}

    uncached = [t for t in texts if t not in _embedding_cache]
    if uncached:
        try:
            from google.genai import types
            for i in range(0, len(uncached), EMBEDDING_BATCH_SIZE):
                batch = uncached[i : i + EMBEDDING_BATCH_SIZE]
                config = types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=EMBEDDING_OUTPUT_DIMENSIONALITY,
                )
                response = client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=batch,
                    config=config,
                )
                embeddings = getattr(response, "embeddings", None)
                if embeddings is None and isinstance(response, dict):
                    embeddings = response.get("embeddings")
                if not embeddings:
                    continue

                for text, emb in zip(batch, embeddings):
                    values = _extract_values(emb)
                    if values is not None:
                        _embedding_cache[text] = _normalize_vector(values)
        except Exception as exc:
            print(f"[Embedder] Gemini embedding call failed: {exc}")
            return {}

    return {t: _embedding_cache[t] for t in texts if t in _embedding_cache}

def _get_db_connection():
    import sqlite3
    db_path = "data/onet.sqlite"
    if not os.path.exists(db_path):
        db_path = "../data/onet.sqlite"
    return sqlite3.connect(db_path)

def anchor_to_onet(skills: list, threshold: float = 0.82) -> list:
    """
    Match a list of ExtractedSkill or JDSkill to canonical O*NET nodes using SQLite.
    Uses multi-stage matching: exact title → alias → common skill map → FTS semantic → substring match.
    Mutates onet_id in place. Returns the same list.
    """
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
    except Exception as e:
        print(f"[Embedder] Failed to connect to SQLite DB: {e}")
        return skills

    unresolved = []
    
    for skill in skills:
        if skill.onet_id:
            continue
        
        name = _normalize_text(skill.name)
        
        # Stage 1: Exact title match
        cursor.execute("SELECT id FROM skills WHERE LOWER(title) = ?", (name,))
        row = cursor.fetchone()
        if row:
            skill.onet_id = row[0]
            continue
        
        # Stage 2: Alias match
        cursor.execute("SELECT skill_id FROM aliases WHERE LOWER(alias) = ?", (name,))
        row = cursor.fetchone()
        if row:
            skill.onet_id = row[0]
            continue
        
        # Stage 3: Common tech aliases
        if name in COMMON_SKILL_ALIASES:
            skill.onet_id = COMMON_SKILL_ALIASES[name]
            continue

        unresolved.append(skill)

    # Stage 4: Gemini embedding semantic retrieval fallback
    if unresolved and _is_embedding_enabled():
        semantic_threshold = threshold if threshold != 0.82 else EMBEDDING_THRESHOLD
        query_texts = [_normalize_text(s.name) for s in unresolved]
        query_vectors = _embed_texts(query_texts, task_type="RETRIEVAL_QUERY")

        for skill, query_text in zip(unresolved, query_texts):
            query_vec = query_vectors.get(query_text)
            if query_vec is None:
                continue

            tokens = _tokenize(query_text)
            if not tokens:
                continue
            
            # Simple FTS OR query to get candidate matches quickly
            fts_query = " OR ".join(tokens)
            try:
                cursor.execute("SELECT id, title FROM skills_fts WHERE skills_fts MATCH ? LIMIT ?", 
                               (fts_query, EMBEDDING_MAX_CANDIDATES))
                candidates = cursor.fetchall()
            except Exception as e:
                print(f"[Embedder] FTS error: {e}")
                continue
                
            if not candidates:
                continue

            candidate_texts = [row[1] for row in candidates]
            # Handle multiple IDs with the same title gracefully
            candidate_id_map = {row[1]: row[0] for row in candidates}
            
            candidate_vectors = _embed_texts(candidate_texts, task_type="RETRIEVAL_DOCUMENT")
            if not candidate_vectors:
                continue

            best_sid = None
            best_score = -1.0
            for ctext, cid in candidate_id_map.items():
                cvec = candidate_vectors.get(ctext)
                if cvec is None:
                    continue
                score = _dot_similarity(query_vec, cvec)
                if score > best_score:
                    best_score = score
                    best_sid = cid

            if best_sid and best_score >= semantic_threshold:
                skill.onet_id = best_sid

    # Stage 5: conservative substring fallback
    for skill in unresolved:
        if skill.onet_id:
            continue
        name = _normalize_text(skill.name)
        if len(name) > 3:
            cursor.execute("SELECT id FROM skills WHERE LOWER(title) LIKE ?", (f"%{name}%",))
            row = cursor.fetchone()
            if row:
                skill.onet_id = row[0]
    
    conn.close()
    return skills