# Merge Conflict Prevention Guide

## Branching Rules
- One feature per branch.
- Branch naming:
  - `feat/person1-extraction-*`
  - `feat/person2-backend-*`
  - `feat/person3-frontend-*`
  - `feat/person4-devops-*`

## File Ownership (Soft Rules)
- Person 1: `api/app/extraction/**`, `data/onet/**`
- Person 2: `api/app/api/**`, `api/app/engine/**`
- Person 3: `frontend/src/**`
- Person 4: `docker-compose.yml`, `README.md`, `docs/**`, CI files

## Daily Sync Habit
1. Pull latest `main` before starting:
```bash
git checkout main
git pull origin main
```
2. Rebase your branch at least twice a day:
```bash
git checkout <your-branch>
git rebase main
```
3. Open small PRs (under ~300 lines when possible).

## Avoiding Hotspot Conflicts
- Keep shared files small and split by concern.
- Avoid multiple people editing `README.md` simultaneously.
- Use dedicated files per feature instead of giant single files.

## Contract-First Changes
- If JSON shape changes, update `docs/API_CONTRACT.md` and `docs/DATA_CONTRACT.md` in same PR.
- Announce schema change in team sync before merge.

## If Conflict Happens
1. Do not panic and do not force push over teammates.
2. Pull/rebase and resolve only marked conflict sections.
3. Run app/tests locally after resolving.
4. Ask the file owner to review final resolved diff.

## Golden Rule
Prefer many small PRs over one big PR.
