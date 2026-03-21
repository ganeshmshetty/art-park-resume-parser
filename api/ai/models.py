from pydantic import BaseModel
from typing import List, Optional

class ExtractedSkill(BaseModel):
    name: str
    onet_id: Optional[str] = None
    proficiency_level: int  # 0=unknown, 1=junior, 2=mid, 3=senior
    years_exp: Optional[float] = None
    confidence: float  # 0.0 – 1.0

class JDSkill(BaseModel):
    name: str
    onet_id: Optional[str] = None
    required_level: int  # target proficiency
    is_required: bool = True  # False = nice-to-have
    importance: float = 1.0  # from O*NET importance rating

class GapItem(BaseModel):
    skill_name: str
    onet_id: Optional[str]
    current_level: int
    required_level: int
    gap_score: float
    importance: float

class ReasoningTrace(BaseModel):
    module_id: str
    module_title: str
    gap_closed: str
    justification: str
    confidence: float
    prerequisite_chain: List[str] = []

class PathNode(BaseModel):
    module_id: str
    title: str
    phase: str  # "Foundation", "Core", "Advanced"
    reasoning: Optional[ReasoningTrace] = None
    status: str = "pending"  # "completed", "in-progress", "pending"
    estimated_duration: int
    skill_gaps_covered: List[str]

class PathwayEdge(BaseModel):
    source: str
    target: str
    type: str = "prerequisite"

class AdaptivePathway(BaseModel):
    nodes: List[PathNode]
    edges: List[PathwayEdge]
    total_duration: int
    phases: dict[str, List[str]] # phase_name -> [module_ids]

class AnalysisResult(BaseModel):
    resume_skills: List[ExtractedSkill]
    jd_skills: List[JDSkill]
    gap_vector: List[GapItem]
    detected_domain: Optional[str] = "General"
    pathway: Optional[AdaptivePathway] = None
    reasoning_traces: List[ReasoningTrace]
    coverage_score: float        # % of JD skills covered
    redundancy_reduction: float  # % of modules skipped vs static curriculum