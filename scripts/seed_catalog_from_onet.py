"""
Seed modules.json from the O*NET SQLite database + Gemini LLM.

Strategy:
  1. Extract the top technology clusters (alias groups) from the DB.
  2. Extract all leaf-level soft skills / knowledge areas.
  3. For each cluster, ask the LLM to generate a Beginner → Intermediate → Advanced
     module progression grounded in real skill IDs.
  4. Write the result to data/catalog/modules.json.

This script is meant to be run ONCE (or re-run when you want to refresh the catalog).
It calls the Gemini API, so make sure GEMINI_API_KEY is set.
"""

import json
import os
import re
import sqlite3
import sys
import time

# --- Configuration ---
DB_PATH = "data/onet.sqlite"
OUTPUT_PATH = "data/catalog/modules.json"
API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Top N technology clusters to generate modules for
TOP_N_TECH_CLUSTERS = 25

# ---- LLM Calling ----
def call_llm(prompt: str, retries: int = 3) -> str:
    """Call Gemini API directly via HTTP."""
    import urllib.request
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4096}
    }).encode()
    
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"  [Retry {attempt+1}] {e}, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  [ERROR] Failed after {retries} attempts: {e}")
                return ""


def parse_json_from_llm(raw: str) -> list:
    """Extract a JSON array from LLM response."""
    cleaned = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
    return []


# ---- Data Extraction from SQLite ----
def get_tech_clusters(conn, top_n: int) -> list[dict]:
    """
    Get the top N technology alias clusters with their skill IDs.
    Returns: [{"cluster_name": "...", "skill_ids": ["TECH-xxx", ...], "example_skills": ["Python", ...]}]
    """
    c = conn.cursor()
    
    # Get top clusters by count
    c.execute("""
        SELECT a.alias, COUNT(DISTINCT a.skill_id) as cnt
        FROM aliases a
        JOIN skills s ON a.skill_id = s.id
        WHERE s.category = 'Technology'
        GROUP BY a.alias
        ORDER BY cnt DESC
        LIMIT ?
    """, (top_n,))
    
    clusters = []
    for alias, count in c.fetchall():
        # Get example skill names for this cluster
        c.execute("""
            SELECT s.id, s.title
            FROM skills s
            JOIN aliases a ON s.id = a.skill_id
            WHERE a.alias = ?
            ORDER BY s.title
            LIMIT 8
        """, (alias,))
        rows = c.fetchall()
        skill_ids = [r[0] for r in rows]
        example_names = [r[1] for r in rows]
        
        clusters.append({
            "cluster_name": alias,
            "skill_count": count,
            "skill_ids": skill_ids,
            "example_skills": example_names
        })
    
    return clusters


def get_soft_skill_groups(conn) -> list[dict]:
    """
    Get leaf-level soft skills grouped by their parent category.
    Returns: [{"group_name": "...", "domain": "...", "skills": [{"id": "SOFT-...", "title": "..."}]}]
    """
    c = conn.cursor()
    
    # Define meaningful groupings based on O*NET taxonomy
    groups = {
        "Basic Content Skills": {
            "prefix": "SOFT-2.A.1",
            "domain": "Cross-Domain",
            "filter_parents": True
        },
        "Process Skills": {
            "prefix": "SOFT-2.A.2",
            "domain": "Cross-Domain",
            "filter_parents": True
        },
        "Social Skills": {
            "prefix": "SOFT-2.B.1",
            "domain": "Cross-Domain",
            "filter_parents": True
        },
        "Complex Problem Solving": {
            "prefix": "SOFT-2.B.2",
            "domain": "Cross-Domain",
            "filter_parents": True
        },
        "Technical Skills": {
            "prefix": "SOFT-2.B.3",
            "domain": "Technology",
            "filter_parents": True
        },
        "Systems Skills": {
            "prefix": "SOFT-2.B.4",
            "domain": "Technology",
            "filter_parents": True
        },
        "Resource Management": {
            "prefix": "SOFT-2.B.5",
            "domain": "Operations",
            "filter_parents": True
        },
        "Business & Management Knowledge": {
            "prefix": "SOFT-2.C.1",
            "domain": "Operations",
            "filter_parents": True
        },
        "Engineering & Technology Knowledge": {
            "prefix": "SOFT-2.C.3",
            "domain": "Technology",
            "filter_parents": True
        },
        "Health Services Knowledge": {
            "prefix": "SOFT-2.C.5",
            "domain": "Healthcare",
            "filter_parents": True
        },
        "Education & Training": {
            "prefix": "SOFT-2.C.6",
            "domain": "Education",
            "filter_parents": False
        },
        "Law & Public Safety": {
            "prefix": "SOFT-2.C.8",
            "domain": "Legal",
            "filter_parents": True
        },
        "Work Styles - Growth": {
            "prefix": "SOFT-1.D.1",
            "domain": "Cross-Domain",
            "filter_parents": True
        },
        "Work Styles - Interpersonal": {
            "prefix": "SOFT-1.D.2",
            "domain": "Cross-Domain",
            "filter_parents": True
        },
        "Work Styles - Conscientiousness": {
            "prefix": "SOFT-1.D.3",
            "domain": "Cross-Domain",
            "filter_parents": True
        },
    }
    
    result = []
    for group_name, config in groups.items():
        prefix = config["prefix"]
        
        c.execute("SELECT id, title FROM skills WHERE id LIKE ? ORDER BY id",
                  (f"{prefix}%",))
        rows = c.fetchall()
        
        # Filter to leaf-level only (no child has this id as a prefix)
        if config.get("filter_parents") and len(rows) > 1:
            all_ids = {r[0] for r in rows}
            leaf_rows = []
            for sid, title in rows:
                # A node is a leaf if no other ID starts with sid + "."
                is_parent = any(other.startswith(sid + ".") for other in all_ids if other != sid)
                if not is_parent:
                    leaf_rows.append((sid, title))
            rows = leaf_rows if leaf_rows else rows
        
        if rows:
            result.append({
                "group_name": group_name,
                "domain": config["domain"],
                "skills": [{"id": r[0], "title": r[1]} for r in rows]
            })
    
    return result


# ---- Module Generation via LLM ----
TECH_MODULE_PROMPT = """You are a curriculum designer. Generate learning modules for the following O*NET technology skill cluster.

Cluster name: {cluster_name}
Example technologies in this cluster: {examples}
O*NET skill IDs to reference: {skill_ids}

Generate a JSON array of 2-3 learning modules forming a Beginner → Intermediate → Advanced progression.
Each module must have these exact keys:
- "id": unique module ID in format "mod_<short_slug>" (lowercase, underscores, 3-5 words max)
- "title": professional course title (5-10 words)
- "description": 1-2 sentence description of what the learner will master
- "skill_ids": array of O*NET skill IDs from the provided list that this module covers
- "domain": "{domain}"
- "level": one of "Beginner", "Intermediate", "Advanced"
- "duration_min": realistic duration in minutes (30, 45, 60, 90, or 120)
- "prerequisites": array of module IDs from this same set that must come first (empty for Beginner)

Rules:
- Use the EXACT skill IDs provided - do not invent new ones
- Each module should cover at least 1-2 skill IDs
- The Beginner module has no prerequisites
- The Intermediate module requires the Beginner as a prerequisite
- The Advanced module requires the Intermediate as a prerequisite
- Make titles specific and professional, not generic

Return ONLY valid JSON array. No explanation. No markdown fences.
"""

SOFT_MODULE_PROMPT = """You are a curriculum designer. Generate learning modules for the following O*NET skill/knowledge group.

Group: {group_name}
Domain: {domain}
Skills in this group:
{skills_list}

Generate a JSON array of 1-2 learning modules. If the group has many skills, create a Beginner + Intermediate pair. If few skills, create just 1 module.

Each module must have these exact keys:
- "id": unique module ID in format "mod_<short_slug>" (lowercase, underscores, 3-5 words max)
- "title": professional course title (5-10 words)
- "description": 1-2 sentence description covering the key competencies
- "skill_ids": array of O*NET skill IDs from the provided list that this module covers
- "domain": "{domain}"
- "level": one of "Beginner", "Intermediate", "Advanced"
- "duration_min": realistic duration in minutes (30, 45, 60, 90, or 120)
- "prerequisites": array of prerequisite module IDs from this set (empty for Beginner)

Rules:
- Use the EXACT skill IDs provided - do not invent new ones
- Each module should cover 2-4 skill IDs where possible
- Make titles actionable and specific, not generic
- Focus on practical workplace application

Return ONLY valid JSON array. No explanation. No markdown fences.
"""


def generate_tech_modules(clusters: list[dict]) -> list[dict]:
    """Generate modules for technology clusters via LLM."""
    all_modules = []
    
    for i, cluster in enumerate(clusters):
        print(f"  [{i+1}/{len(clusters)}] Generating modules for: {cluster['cluster_name']} ({cluster['skill_count']} skills)")
        
        prompt = TECH_MODULE_PROMPT.format(
            cluster_name=cluster["cluster_name"],
            examples=", ".join(cluster["example_skills"][:6]),
            skill_ids=json.dumps(cluster["skill_ids"]),
            domain="Technology"
        )
        
        raw = call_llm(prompt)
        modules = parse_json_from_llm(raw)
        
        if modules:
            all_modules.extend(modules)
            print(f"    → Generated {len(modules)} modules")
        else:
            print(f"    → FAILED to parse response")
        
        # Small delay to avoid rate limiting
        time.sleep(1)
    
    return all_modules


def generate_soft_modules(groups: list[dict]) -> list[dict]:
    """Generate modules for soft skill / knowledge groups via LLM."""
    all_modules = []
    
    for i, group in enumerate(groups):
        print(f"  [{i+1}/{len(groups)}] Generating modules for: {group['group_name']} ({len(group['skills'])} skills)")
        
        skills_text = "\n".join(f"  - {s['id']}: {s['title']}" for s in group["skills"])
        skill_ids = [s["id"] for s in group["skills"]]
        
        prompt = SOFT_MODULE_PROMPT.format(
            group_name=group["group_name"],
            domain=group["domain"],
            skills_list=skills_text
        )
        
        raw = call_llm(prompt)
        modules = parse_json_from_llm(raw)
        
        if modules:
            all_modules.extend(modules)
            print(f"    → Generated {len(modules)} modules")
        else:
            print(f"    → FAILED to parse response")
        
        time.sleep(1)
    
    return all_modules


# ---- Validation & Dedup ----
def validate_and_clean(modules: list[dict]) -> list[dict]:
    """Validate module structure and remove duplicates."""
    seen_ids = set()
    valid = []
    
    required_keys = {"id", "title", "description", "skill_ids", "domain", "level", "duration_min", "prerequisites"}
    valid_levels = {"Beginner", "Intermediate", "Advanced"}
    
    for m in modules:
        # Check required keys
        if not required_keys.issubset(m.keys()):
            missing = required_keys - set(m.keys())
            print(f"  [SKIP] {m.get('id', '???')}: missing keys {missing}")
            continue
        
        # Dedup
        if m["id"] in seen_ids:
            print(f"  [SKIP] {m['id']}: duplicate ID")
            continue
        
        # Normalize
        m["level"] = m["level"].strip().title()
        if m["level"] not in valid_levels:
            m["level"] = "Intermediate"
        
        m["duration_min"] = int(m.get("duration_min", 60))
        m["skill_ids"] = m.get("skill_ids", [])
        m["prerequisites"] = m.get("prerequisites", [])
        
        seen_ids.add(m["id"])
        valid.append(m)
    
    return valid


def fix_prerequisites(modules: list[dict]) -> list[dict]:
    """Remove any prerequisites that reference non-existent module IDs."""
    all_ids = {m["id"] for m in modules}
    for m in modules:
        m["prerequisites"] = [p for p in m["prerequisites"] if p in all_ids]
    return modules


# ---- Main ----
def main():
    if not API_KEY:
        print("ERROR: GEMINI_API_KEY not set. Export it first.")
        sys.exit(1)
    
    print(f"Opening {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    
    # Step 1: Extract clusters
    print(f"\n=== Step 1: Extracting top {TOP_N_TECH_CLUSTERS} technology clusters ===")
    tech_clusters = get_tech_clusters(conn, TOP_N_TECH_CLUSTERS)
    print(f"Found {len(tech_clusters)} clusters")
    
    print(f"\n=== Step 2: Extracting soft skill groups ===")
    soft_groups = get_soft_skill_groups(conn)
    print(f"Found {len(soft_groups)} groups")
    
    conn.close()
    
    # Step 2: Generate modules via LLM
    print(f"\n=== Step 3: Generating technology modules ===")
    tech_modules = generate_tech_modules(tech_clusters)
    
    print(f"\n=== Step 4: Generating soft skill modules ===")
    soft_modules = generate_soft_modules(soft_groups)
    
    # Step 3: Combine, validate, deduplicate
    print(f"\n=== Step 5: Validation ===")
    all_modules = tech_modules + soft_modules
    print(f"Raw total: {len(all_modules)}")
    
    all_modules = validate_and_clean(all_modules)
    all_modules = fix_prerequisites(all_modules)
    print(f"Valid total: {len(all_modules)}")
    
    # Step 4: Write
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_modules, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Written {len(all_modules)} modules to {OUTPUT_PATH}")
    
    # Summary
    by_domain = {}
    by_level = {}
    for m in all_modules:
        by_domain[m["domain"]] = by_domain.get(m["domain"], 0) + 1
        by_level[m["level"]] = by_level.get(m["level"], 0) + 1
    
    print(f"\n--- By Domain ---")
    for d, c in sorted(by_domain.items()):
        print(f"  {d}: {c}")
    
    print(f"\n--- By Level ---")
    for l, c in sorted(by_level.items()):
        print(f"  {l}: {c}")


if __name__ == "__main__":
    main()
