# API Contract (v0)

## POST `/analyze`
Upload resume and JD files.

### Request
- Content-Type: `multipart/form-data`
- Fields:
  - `resume`: file (`.pdf`, `.docx`, `.txt`)
  - `jd`: file (`.pdf`, `.docx`, `.txt`)

### Response `200`
```json
{
  "job_id": "d4a1c94f-5e84-4ae9-a064-8b2ce4d6642d",
  "status": "queued"
}
```

### Error Shape
```json
{
  "error": {
    "code": "invalid_file_type",
    "message": "Only PDF, DOCX, TXT are supported",
    "details": {"field": "resume"}
  }
}
```

## GET `/result/{job_id}`
Fetch analysis result.

### Response States
- `queued`
- `processing`
- `completed`
- `failed`
- `not_found`

### Response `completed` (target shape)
```json
{
  "job_id": "d4a1c94f-5e84-4ae9-a064-8b2ce4d6642d",
  "status": "completed",
  "result": {
    "summary": {
      "coverage_score": 0.86,
      "redundancy_reduction": 0.42,
      "estimated_total_minutes": 960
    },
    "pathway": {
      "nodes": [
        {
          "module_id": "mod_python_foundations",
          "title": "Python Foundations",
          "phase": "Foundation",
          "skills_targeted": ["ONET-SKILL-123"],
          "reasoning_ref": "trace_001"
        }
      ],
      "edges": [
        {"from": "mod_python_foundations", "to": "mod_ml_intro", "type": "prerequisite"}
      ]
    },
    "reasoning_traces": [
      {
        "id": "trace_001",
        "module_id": "mod_python_foundations",
        "text": "Builds required coding baseline and unlocks ML Intro.",
        "confidence": 0.91
      }
    ]
  }
}
```
