import collections
from typing import Dict, List, Optional, Set

from ai.models import ExtractedSkill, JDSkill, GapItem, AdaptivePathway, PathNode, ReasoningTrace
from app.services.catalog import CatalogModule, CourseCatalogService

def compute_gap_vector(
    resume_skills: list[ExtractedSkill],
    jd_skills: list[JDSkill]
) -> list[GapItem]:
    """
    For each JD skill, compute gap = max(0, required_level - current_level).
    Weighted by O*NET importance. Returns sorted gap vector (highest first).
    """
    resume_map: dict[str, ExtractedSkill] = {}
    for rs in resume_skills:
        key = rs.onet_id or rs.name.lower()
        resume_map[key] = rs

    gaps = []
    for jd_skill in jd_skills:
        if not jd_skill.is_required:
            continue
            
        lookup_key = jd_skill.onet_id or jd_skill.name.lower()
        current = resume_map.get(lookup_key)
        
        # proficiency_level from LLM is 1, 2, 3
        current_level = current.proficiency_level if current else 0
        
        effective_required = jd_skill.required_level
            
        delta = max(0, effective_required - current_level)
        if delta == 0:
            continue

        gap_score = delta * jd_skill.importance
        gaps.append(GapItem(
            skill_name=jd_skill.name,
            onet_id=jd_skill.onet_id,
            current_level=current_level,
            required_level=effective_required,
            gap_score=gap_score,
            importance=jd_skill.importance
        ))

    gaps.sort(key=lambda g: g.gap_score, reverse=True)
    return gaps

def generate_adaptive_pathway(
    gaps: List[GapItem],
    catalog: CourseCatalogService,
    detected_domain: str = "Technology"
) -> AdaptivePathway:
    """
    Constructs a topologically sorted learning path based on skill gaps.
    HYBRID: Uses catalog modules when available, generates LLM modules for uncovered gaps.
    1. Identify target modules for gaps from catalog.
    2. For uncovered gaps, dynamically generate modules via LLM.
    3. Expand prerequisites to build a DAG.
    4. Topologically sort the DAG.
    5. Group into phases.
    """
    
    # --- Step 1: Identify target modules from catalog ---
    target_modules_map: Dict[str, CatalogModule] = {}
    uncovered_gaps: List[GapItem] = []
    
    for gap in gaps:
        if not gap.onet_id:
            uncovered_gaps.append(gap)
            continue
        
        candidates = catalog.modules_by_skill.get(gap.onet_id, [])
        if not candidates:
            uncovered_gaps.append(gap)
            continue
            
        # Pick best candidate matching the target level
        target_level = "Beginner"
        if gap.required_level >= 3:
            target_level = "Advanced"
        elif gap.required_level == 2:
            target_level = "Intermediate"
            
        best = next((m for m in candidates if m.level == target_level), candidates[0])
        target_modules_map[best.id] = best

    # --- Step 2: Generate LLM modules for uncovered gaps ---
    generated_modules: Dict[str, CatalogModule] = {}
    
    if uncovered_gaps:
        try:
            from ai.extractor import _call_llm
            from ai.prompts import DYNAMIC_MODULE_PROMPT
            import json
            import re
            
            for gap in uncovered_gaps:
                try:
                    prompt = DYNAMIC_MODULE_PROMPT.format(
                        skill_name=gap.skill_name,
                        domain=detected_domain,
                        current_level=gap.current_level,
                        required_level=gap.required_level,
                        importance=gap.importance
                    )
                    raw = _call_llm(prompt)
                    cleaned = re.sub(r"```json|```", "", raw).strip()
                    
                    # Try to parse as JSON object
                    try:
                        module_data = json.loads(cleaned)
                    except json.JSONDecodeError:
                        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
                        if match:
                            module_data = json.loads(match.group())
                        else:
                            continue
                    
                    gen_module = CatalogModule(
                        id=module_data.get("id", f"mod_gen_{gap.skill_name.lower().replace(' ', '_')[:20]}"),
                        title=module_data.get("title", f"{gap.skill_name} Essentials"),
                        description=module_data.get("description", f"Covers essential concepts in {gap.skill_name}."),
                        skill_ids=[gap.onet_id] if gap.onet_id else [],
                        domain=module_data.get("domain", detected_domain),
                        level=module_data.get("level", "Beginner"),
                        duration_min=int(module_data.get("duration_min", 60)),
                        prerequisites=[]
                    )
                    generated_modules[gen_module.id] = gen_module
                    target_modules_map[gen_module.id] = gen_module
                    
                except Exception as e:
                    print(f"[Pathway] Failed to generate module for '{gap.skill_name}': {e}")
                    continue
        except ImportError:
            print("[Pathway] LLM imports not available, skipping dynamic generation")

    # --- Step 3: Expand Prerequisites (DAG Build) ---
    expanded_modules: Dict[str, CatalogModule] = {}
    
    def expand(module_id: str):
        if module_id in expanded_modules:
            return
        
        # Check catalog first, then generated modules
        module = catalog.modules_by_id.get(module_id) or generated_modules.get(module_id)
        if not module:
            return 
        
        expanded_modules[module_id] = module
        for prereq_id in module.prerequisites:
            expand(prereq_id)
            
    for mid in target_modules_map:
        expand(mid)
    
    # --- Step 4: Topological Sort (Kahn's Algorithm) ---
    adj = collections.defaultdict(list)
    in_degree = {mid: 0 for mid in expanded_modules}
    
    for mid, module in expanded_modules.items():
        for prereq_id in module.prerequisites:
            if prereq_id in expanded_modules:
                adj[prereq_id].append(mid)
                in_degree[mid] += 1
                
    queue = collections.deque([mid for mid, deg in in_degree.items() if deg == 0])
    sorted_order = []
    
    while queue:
        node_id = queue.popleft()
        sorted_order.append(node_id)
        
        for neighbor in adj[node_id]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
                
    # Check for cycles / leftover nodes
    if len(sorted_order) != len(expanded_modules):
        visited = set(sorted_order)
        for mid in expanded_modules:
            if mid not in visited:
                sorted_order.append(mid)

    # --- Step 5: Construct PathNodes & Phases ---
    path_nodes = []
    current_total_min = 0
    phase_buckets = {"Foundation": [], "Core": [], "Advanced": []}
    
    total_steps = len(sorted_order)
    
    for i, mod_id in enumerate(sorted_order):
        module = expanded_modules[mod_id]
        is_generated = mod_id in generated_modules
        
        # Phase Heuristic
        if module.level == "Beginner":
            p = "Foundation"
        elif module.level == "Advanced":
            p = "Advanced"
        else:
            p = "Core"
            
        if p == "Foundation" and i > total_steps * 0.5:
            p = "Core"
            
        phase_buckets.setdefault(p, []).append(mod_id)
        
        # Determine coverage
        skills_covered = []
        for sid in module.skill_ids:
            for g in gaps:
                if g.onet_id == sid:
                    skills_covered.append(g.skill_name)
        skills_covered = list(set(skills_covered))
        
        # --- Generate Reasoning ---
        gap_desc = ", ".join(skills_covered) if skills_covered else "Prerequisite Knowledge"
        
        justification = None
        try:
            from ai.extractor import _call_llm
            from ai.prompts import REASONING_TRACE_PROMPT
            
            if i < 5:
                prompt = REASONING_TRACE_PROMPT.format(
                    module_title=module.title,
                    gap_description=gap_desc,
                    current_level=0,
                    required_level=module.level,
                    prereq_chain=", ".join(sorted_order[:i])
                )
                justification = _call_llm(prompt)
        except Exception:
            pass

        if not justification:
            source_label = " (AI-generated)" if is_generated else ""
            if skills_covered:
                justification = f"This module{source_label} addresses your gap in {skills_covered[0]}. It provides the necessary depth for {module.level} proficiency."
            else:
                justification = f"A fundamental prerequisite{source_label} that builds the necessary foundation for advanced topics in your pathway."

        reasoning = ReasoningTrace(
            module_id=module.id,
            module_title=module.title,
            gap_closed=gap_desc,
            justification=justification,
            confidence=0.95 if not is_generated else 0.85
        )
        
        path_nodes.append(PathNode(
            module_id=module.id,
            title=module.title,
            phase=p,
            status="pending",
            estimated_duration=module.duration_min,
            skill_gaps_covered=skills_covered,
            reasoning=reasoning
        ))
        
        current_total_min += module.duration_min

    # --- Step 6: Construct Edges ---
    path_edges = []
    from ai.models import PathwayEdge
    for mid, module in expanded_modules.items():
        for prereq_id in module.prerequisites:
            if prereq_id in expanded_modules:
                path_edges.append(PathwayEdge(source=prereq_id, target=mid))

    return AdaptivePathway(
        nodes=path_nodes,
        edges=path_edges,
        total_duration=current_total_min,
        phases=phase_buckets
    )