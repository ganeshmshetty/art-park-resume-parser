# Team Board

## Owners
- Person 1: Extraction + mapping + reasoning text
- Person 2: API + gap engine + DAG
- Person 3: Frontend UI + graph + charts
- Person 4: Docker + docs + slides + video

## Daily Update Format (10 min)
- Yesterday done:
- Today plan:
- Blockers:
- Any contract/schema change:

## Definition of Done (per task)
- Code merged to `main`
- Contract updated if shape changed
- One sample input/output attached in PR
- Basic test evidence included

## Priority Order
1. Contracts and schemas
2. Core algorithm correctness
3. Frontend integration
4. Metrics and polish

## 24-Hour Delivery Plan

### H0-H2
- Person 2 + Person 4: verify data files load (`onet_skills.json`, `modules.json`) and API boots.
- Person 1: validate extraction output shape against `docs/DATA_CONTRACT.md`.
- Person 3: ensure upload UI posts to `/analyze` and polls `/result/{job_id}`.

### H2-H10
- Person 2: finalize gap + pathway generation and contract-aligned response.
- Person 1: tighten prompts for stable JSON output and grounding quality.
- Person 3: render pathway nodes + reasoning in UI.

### H10-H18
- Integrate full flow and test with at least 2 resume/JD pairs.
- Fix schema mismatches immediately in docs and backend together.

### H18-H24
- Person 4 leads final QA, demo script, README pass, and submission assets.
- Freeze features; only bug fixes and demo stability changes.

## 24-Hour Exit Criteria
- End-to-end demo works from upload to pathway output.
- No contract drift between docs and backend models.
- No hallucinated modules (all module IDs exist in catalog).
