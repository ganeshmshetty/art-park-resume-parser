# Project Context

## Problem
Candidates and teams waste time on static learning paths that ignore prior experience.

## Solution
Build an AI-adaptive onboarding engine that:
- Parses resume and job description (JD)
- Maps skills to canonical O*NET skill IDs
- Computes skill gaps with weighted scoring
- Generates a prerequisite-aware learning path from a catalog
- Explains why each module is recommended using grounded reasoning

## Core Thesis
Hybrid extraction (spaCy + LLM) + O*NET anchoring + DAG-based pathway ordering gives a reliable and explainable personalized roadmap.

## Non-Negotiables
- No hallucinated modules: every module ID must exist in course catalog.
- Deterministic pathway ordering for same input and catalog.
- API contracts are versioned and respected.
- Demo must run via Docker Compose.

## Team Ownership
- Person 1: AI/NLP extraction + reasoning text
- Person 2: Backend APIs + gap engine + DAG traversal
- Person 3: Frontend upload + graph + trace panel
- Person 4: DevOps + docs + slides + demo video

## Tech Stack (Locked)
- Backend: FastAPI, Uvicorn, Redis
- Frontend: React, Vite, React Flow, Recharts
- NLP/ML: spaCy, sentence-transformers (MiniLM), LLM for extraction/reasoning
- Data: O*NET + curated course catalog

## Out of Scope (Hackathon)
- Full auth/roles
- Production-scale queue orchestration
- Multi-tenant billing/quotas

## 24-Hour Build Mode (Locked)

This project is scoped for a strict 24-hour hackathon.

### Must Ship in 24 Hours
- `POST /analyze` + `GET /result/{job_id}` working end-to-end.
- Resume/JD extraction returning contract-compliant JSON.
- O*NET anchoring and gap vector generation.
- Catalog-grounded pathway generation with prerequisite ordering.
- Frontend upload flow + result rendering for one complete demo scenario.
- Docker Compose cold start and one reproducible demo script.

### Nice-to-Have (Only if time remains)
- SSE progress streaming.
- Redis-backed queue (instead of in-memory jobs).
- Advanced metrics dashboard and multiple persona demos.

### Cutline Rule
If a task does not improve demo reliability, correctness, or explainability, defer it.
