import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from api.ai.models import ExtractedSkill, JDSkill, GapItem
from api.ai.gap_analyzer import compute_gap_vector, generate_adaptive_pathway
from api.app.services.catalog import CourseCatalogService, CatalogModule

# --- MOCK DATA ---
resume_skills = [
    ExtractedSkill(name="Python", onet_id="111", proficiency_level=2, confidence=0.9), # Mid
    ExtractedSkill(name="SQL", onet_id="222", proficiency_level=1, confidence=0.8),    # Junior
]

jd_skills = [
    JDSkill(name="Python", onet_id="111", required_level=3, importance=4.5), # Senior requested (Gap: 3-2=1)
    JDSkill(name="SQL", onet_id="222", required_level=2, importance=3.0),    # Mid requested (Gap: 2-1=1)
    JDSkill(name="AWS", onet_id="333", required_level=2, importance=4.0),    # Mid requested (Gap: 2-0=2)
    JDSkill(name="Teamwork", onet_id="444", required_level=2, is_required=False) # Optional
]

# --- MOCK CATALOG ---
mock_modules = [
    CatalogModule(id="m1", title="Advanced Python", description="...", skill_ids=["111"], domain="Tech", level="Advanced", duration_min=120, prerequisites=["m2"]),
    CatalogModule(id="m2", title="Intermediate Python", description="...", skill_ids=["111"], domain="Tech", level="Intermediate", duration_min=90, prerequisites=[]),
    CatalogModule(id="m3", title="SQL Fundamentals", description="...", skill_ids=["222"], domain="Tech", level="Intermediate", duration_min=60, prerequisites=[]),
    CatalogModule(id="m4", title="AWS Cloud Basics", description="...", skill_ids=["333"], domain="Tech", level="Beginner", duration_min=60, prerequisites=[]),
    CatalogModule(id="m5", title="AWS Solutions Architect", description="...", skill_ids=["333"], domain="Tech", level="Intermediate", duration_min=180, prerequisites=["m4"]),
]

catalog_service = CourseCatalogService(modules=mock_modules)

def test_gap_analysis():
    print("--- Testing compute_gap_vector ---")
    gaps = compute_gap_vector(resume_skills, jd_skills)
    
    for g in gaps:
        print(f"Gap: {g.skill_name} (O*NET: {g.onet_id}) | Score: {g.gap_score} | Req: {g.required_level} vs Curr: {g.current_level}")
        
    # Expected:
    # AWS: Gap 2 * 4.0 = 8.0
    # Python: Gap 1 * 4.5 = 4.5
    # SQL: Gap 1 * 3.0 = 3.0
    
    assert len(gaps) == 3
    assert gaps[0].skill_name == "AWS"
    assert gaps[1].skill_name == "Python"
    assert gaps[2].skill_name == "SQL"
    print("✓ Vector coputation passed!\n")
    
    print("--- Testing generate_adaptive_pathway ---")
    pathway = generate_adaptive_pathway(gaps, catalog_service)
    
    print(f"Total Duration: {pathway.total_duration} min")
    print(f"Total Modules: {len(pathway.nodes)}")
    
    print("Pathway Sequence:")
    for node in pathway.nodes:
        print(f"  [{node.phase}] {node.title} ({node.estimated_duration}m) -> covers {node.skill_gaps_covered}")
        if node.reasoning:
             print(f"     Reasoning: {node.reasoning.justification}")

    # Verify order: m4 -> m5 (AWS), m2 -> m1 (Python), m3 (SQL)
    # The topological sort should ensure prereqs come first.
    # m1 needs m2. m5 needs m4.
    
    # Check if m2 comes before m1
    ids = [n.module_id for n in pathway.nodes]
    if "m1" in ids and "m2" in ids:
        assert ids.index("m2") < ids.index("m1"), "Prerequisite m2 should be before m1"
        
    if "m5" in ids and "m4" in ids:
        assert ids.index("m4") < ids.index("m5"), "Prerequisite m4 should be before m5"
        
    print("✓ Pathway generation passed!")

if __name__ == "__main__":
    test_gap_analysis()
