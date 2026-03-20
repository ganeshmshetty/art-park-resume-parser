# Data Contract (v1 - Current)

Source of truth:
- `data/onet_skills.json`
- `data/catalog/modules.json`
- `api/ai/models.py`
- `api/app/services/catalog.py`

## Canonical O*NET Skill Node (`data/onet_skills.json`)
```json
{
  "id": "TECH-269e3f5442b0",
  "title": "!Trak-it Solutions !Trak-it HR",
  "importance": 0.2962,
  "aliases": [
    "43231505",
    "human resources software"
  ],
  "category": "Technology"
}
```

## Resume Skill (`ExtractedSkill`)
```json
{
  "name": "Machine Learning",
  "onet_id": "TECH-abc123",
  "proficiency_level": 1,
  "years_exp": 0.8,
  "confidence": 0.88
}
```

## JD Skill (`JDSkill`)
```json
{
  "name": "Machine Learning",
  "onet_id": "TECH-abc123",
  "required_level": 3,
  "is_required": true,
  "importance": 0.9
}
```

## Course Catalog Module (`data/catalog/modules.json`)
```json
{
  "id": "mod_80808627",
  "title": "Advanced Commercial kitchen steamers Mastery",
  "description": "A comprehensive advanced module focusing on Commercial kitchen steamers.",
  "skill_ids": [
    "TOOL-0ad8364d760d"
  ],
  "domain": "Tools",
  "level": "Advanced",
  "duration_min": 120,
  "prerequisites": []
}
```

## Gap Item (`GapItem`)
```json
{
  "skill_name": "Machine Learning",
  "onet_id": "TECH-abc123",
  "current_level": 1,
  "required_level": 3,
  "gap_score": 1.8,
  "importance": 0.9
}
```

## Reasoning Trace (`ReasoningTrace`)
```json
{
  "module_id": "mod_ml_intro",
  "module_title": "ML Intro",
  "gap_closed": "Machine Learning",
  "justification": "This module addresses your gap in Machine Learning",
  "confidence": 0.95,
  "prerequisite_chain": []
}
```

## Pathway Node (`PathNode`)
```json
{
  "module_id": "mod_ml_intro",
  "title": "ML Intro",
  "phase": "Core",
  "reasoning": {
    "module_id": "mod_ml_intro",
    "module_title": "ML Intro",
    "gap_closed": "Machine Learning",
    "justification": "This module addresses your gap in Machine Learning",
    "confidence": 0.95,
    "prerequisite_chain": []
  },
  "status": "pending",
  "estimated_duration": 240,
  "skill_gaps_covered": [
    "Machine Learning"
  ]
}
```

## Adaptive Pathway (`AdaptivePathway`)
```json
{
  "nodes": [],
  "total_duration": 960,
  "phases": {
    "Foundation": [
      "mod_python_foundations"
    ],
    "Core": [
      "mod_ml_intro"
    ],
    "Advanced": []
  }
}
```

## Analysis Result (`AnalysisResult`)
```json
{
  "resume_skills": [],
  "jd_skills": [],
  "gap_vector": [],
  "pathway": null,
  "reasoning_traces": [],
  "coverage_score": 0.86,
  "redundancy_reduction": 0.42
}
```

## Levels (locked)
- `proficiency_level` / `required_level`: `0` none, `1` junior/basic, `2` intermediate, `3` advanced/senior
- catalog module `level`: `Beginner`, `Intermediate`, `Advanced`
