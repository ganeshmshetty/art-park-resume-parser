# Dataset Sources

This document lists all dataset sources used by the AI-Adaptive Onboarding Engine for skill taxonomy and resume parsing.

---

## 1. O\*NET 28.0 Database

**Full name:** Occupational Information Network (O\*NET) Database, Release 28.0  
**Publisher:** National Center for O\*NET Development, U.S. Department of Labor  
**URL:** https://www.onetcenter.org/database.html  
**License:** Open to the public; attribution required  

### Files used

| File | Records | Purpose |
|------|---------|---------|
| `Skills.txt` | ~17,000 | Core skill taxonomy nodes |
| `Abilities.txt` | ~9,000 | Cognitive/physical ability nodes |
| `Knowledge.txt` | ~7,500 | Knowledge area nodes |
| `Work Activities.txt` | ~5,800 | Task-activity nodes |
| `Technology Skills.txt` | ~35,000 | Software/tool skills |

**Total canonical nodes after deduplication + alias merge:** ~1,000 unique skill IDs.

The `scripts/build_onet_skills.py` script reads these files and builds `data/onet_skills.json`:

```json
[
  {
    "id": "2.B.3.g",
    "title": "Programming",
    "importance": 0.82,
    "aliases": ["coding", "software development", "scripting"]
  }
]
```

### Citation (APA)

> National Center for O\*NET Development. (2024). *O\*NET 28.0 Database*. Retrieved from https://www.onetcenter.org/database.html

---

## 2. Kaggle Resume Dataset

**Full name:** Resume Dataset  
**Author:** Gaurav Dutta (Kaggle username: gauravduttakiit)  
**URL:** https://www.kaggle.com/datasets/gauravduttakiit/resume-dataset  
**License:** CC0 1.0 (Public Domain)  
**Records:** 2,484 resumes across 25 job categories  

### Domains covered

| Domain | Approximate count |
|--------|------------------|
| Data Science | 134 |
| HR | 122 |
| Advocate | 118 |
| Arts | 116 |
| Web Designing | 115 |
| Mechanical Engineer | 112 |
| Sales | 107 |
| Health and Fitness | 97 |
| Civil Engineer | 87 |
| Java Developer | 84 |
| … | … |

### Citation (APA)

> Dutta, G. (2021). *Resume Dataset* [Data set]. Kaggle. https://www.kaggle.com/datasets/gauravduttakiit/resume-dataset

---

## Usage Notes

- O\*NET data is downloaded separately and placed in `data/db_30_1_text/` before running bootstrap.
- Kaggle dataset used for evaluation and proficiency signal inference during development.
- No personal data is stored; files are processed in memory per request.
