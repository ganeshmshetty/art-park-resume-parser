# Evaluation Metrics

Mathematical definitions for the three evaluation metrics used to assess pathway quality.

---

## 1. Coverage Score (C)

**Definition:** The fraction of required JD skills that are addressed by at least one module in the recommended pathway.

$$C = \frac{\left|\, S_{\text{JD,required}} \cap S_{\text{pathway}} \,\right|}{\left|\, S_{\text{JD,required}} \,\right|}$$

Where:
- $S_{\text{JD,required}}$ = set of O\*NET skill IDs marked as **required** in the JD
- $S_{\text{pathway}}$ = union of all O\*NET skill IDs targeted across all pathway modules

**Range:** 0.0 – 1.0 (higher is better)  
**Target:** ≥ 0.85  
**API field:** `result.summary.coverage_score`

---

## 2. Redundancy Reduction (R)

**Definition:** The percentage reduction in learning modules compared to a naïve static curriculum that delivers all skills regardless of prior knowledge.

$$R = 1 - \frac{|\text{pathway modules}|}{|\text{static curriculum modules}|}$$

Where the static curriculum is defined as the full set of course catalog modules that cover any JD skill, without personalisation.

**Range:** 0.0 – 1.0 (higher = more personalised)  
**Target:** ≥ 0.60  
**API field:** `result.summary.redundancy_reduction`

**Example:** If the static curriculum has 25 modules but the personalised pathway has 9, then R = 1 − 9/25 = **0.64 (64% reduction)**.

---

## 3. Path Efficiency (PE)

**Definition:** How much shorter the topologically-ordered pathway depth is compared to the naïve baseline (BFS depth from root to leaves in the full prerequisite DAG).

$$PE = 1 - \frac{d_{\text{pathway}}}{d_{\text{baseline}}}$$

Where:
- $d_{\text{pathway}}$ = longest path length (in hops) in the recommended sub-DAG
- $d_{\text{baseline}}$ = longest path length in the full prerequisite DAG over the domain

**Range:** 0.0 – 1.0 (higher = more efficient learning order)  
**Target:** ≥ 0.40

---

## Composite Score

For hackathon judging, we report:

$$\text{Score} = 0.4 \cdot C + 0.35 \cdot R + 0.25 \cdot PE$$

---

## /metrics Endpoint

`GET /metrics` returns aggregate metrics across all completed jobs in the current session:

```json
{
  "total_jobs_completed": 3,
  "avg_coverage_score": 0.88,
  "avg_redundancy_reduction": 0.64,
  "avg_estimated_minutes": 840
}
```
