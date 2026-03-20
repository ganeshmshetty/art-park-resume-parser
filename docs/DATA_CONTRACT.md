# Data Contract (v0)

## Canonical Skill
```json
{
  "skill_id": "ONET-SKILL-123",
  "name": "Machine Learning",
  "domain": "Tech",
  "importance_weight": 0.9
}
```

## Resume Skill (Person 1 -> Person 2)
```json
{
  "skill_id": "ONET-SKILL-123",
  "name": "Machine Learning",
  "current_level": 1,
  "years_experience": 0.8,
  "confidence": 0.88,
  "evidence": "Built a capstone classification project"
}
```

## JD Skill (Person 1 -> Person 2)
```json
{
  "skill_id": "ONET-SKILL-123",
  "name": "Machine Learning",
  "required_level": 3,
  "required": true,
  "importance_weight": 0.9,
  "confidence": 0.9
}
```

## Course Catalog Module
```json
{
  "id": "mod_ml_intro",
  "title": "ML Intro",
  "skill_ids": ["ONET-SKILL-123"],
  "domain": "Tech",
  "level": "Beginner",
  "duration_min": 240,
  "prerequisites": ["mod_python_foundations"]
}
```

## Gap Node (internal)
```json
{
  "skill_id": "ONET-SKILL-123",
  "delta": 2,
  "importance": 0.9,
  "priority": 1.8
}
```

## Pathway Node (Person 2 -> Person 3)
```json
{
  "module_id": "mod_ml_intro",
  "phase": "Core",
  "skills_targeted": ["ONET-SKILL-123"],
  "estimated_minutes": 240,
  "reasoning_ref": "trace_004"
}
```

## Levels (locked)
- 0: none
- 1: basic
- 2: intermediate
- 3: advanced
