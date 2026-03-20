import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from .models import ExtractedSkill, JDSkill

_model = None  # lazy load
_onet_cache = None
_onet_embeddings_cache = None

def _get_model():
    global _model
    if _model is None:
        # Load a smaller, faster model if available, otherwise default
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def _get_onet_data(path="data/onet_skills.json"):
    global _onet_cache, _onet_embeddings_cache
    if _onet_cache is not None:
        return _onet_cache, _onet_embeddings_cache

    if not os.path.exists(path):
        return [], None
        
    with open(path) as f:
        data = json.load(f)
        
    _onet_cache = data
    
    # Pre-compute embeddings once
    model = _get_model()
    titles = [n["title"] for n in data]
    # This might take a few seconds on first load
    try:
        if titles:
            _onet_embeddings_cache = model.encode(titles, batch_size=64, show_progress_bar=False, convert_to_numpy=True)
        else:
            _onet_embeddings_cache = np.array([])
    except Exception as e:
        print(f"Warning: Failed to embed O*NET titles: {e}")
        _onet_embeddings_cache = None
        
    return _onet_cache, _onet_embeddings_cache

def _cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    # Use numpy for faster dot product
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

def anchor_to_onet(skills: list, threshold: float = 0.82) -> list:
    """
    Match a list of ExtractedSkill or JDSkill to canonical O*NET nodes.
    Mutates onet_id in place. Returns the same list.
    """
    onet_nodes, onet_embeddings = _get_onet_data()
    if not onet_nodes:
        return skills  # graceful degradation if data not ready

    model = _get_model()
    onet_ids = [n["id"] for n in onet_nodes]
    
    # Pre-compute alias map for O(1) lookup
    # Could be cached too but it's fast enough
    alias_map = {}
    for n in onet_nodes:
        for alias in n.get("aliases", []):
            alias_map[alias.lower()] = n["id"]
    
    # Batch encode incoming skills for speed
    skill_names = [s.name for s in skills]
    if not skill_names:
        return skills
        
    skill_embeddings = model.encode(skill_names, batch_size=32, show_progress_bar=False, convert_to_numpy=True)
    
    for i, skill in enumerate(skills):
        # Stage 1: exact string match (fastest)
        lower_name = skill.name.lower()
        exact = next((n for n in onet_nodes if n["title"].lower() == lower_name), None)
        if exact:
            skill.onet_id = exact["id"]
            continue
        
        # Stage 2: alias match (e.g. "k8s" → "Kubernetes")
        if lower_name in alias_map:
            skill.onet_id = alias_map[lower_name]
            continue
        
        # Stage 3: semantic similarity via vector search
        if onet_embeddings is not None and len(onet_embeddings) > 0:
            # Vectorized cosine similarity: (A . B) / (|A| |B|)
            # Assuming embeddings are normalized by sentence-transformers usually, but let's be safe
            # Actually util.cos_sim is better but let's stick to numpy
            
            # Compute similarities against all O*NET nodes
            # onet_embeddings shape: (N_onet, D)
            # skill_embeddings[i] shape: (D,)
            
            # Check dimensions match
            if skill_embeddings[i].shape == onet_embeddings.shape[1:]:
                 # Dot product
                 scores = np.dot(onet_embeddings, skill_embeddings[i])
                 # Normalize (if not already) - assuming unit length for speed
                 # If we used normalize_embeddings=True in encode, we could skip norm
                 
                 best_idx = int(np.argmax(scores))
                 # We need true cosine similarity for threshold
                 # Let's recalculate accurately for the best match only or use a library function
                 
                 # Recalculate best score carefully
                 best_vector = onet_embeddings[best_idx]
                 sim = _cosine_sim(skill_embeddings[i], best_vector)
                 
                 if sim >= threshold:
                     skill.onet_id = onet_ids[best_idx]
    
    return skills