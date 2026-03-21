"""
Build data/onet.sqlite from the raw O*NET text files in data/db_30_1_text/.
This replaces the old onet_skills.json entirely.

Sources:
  - Technology Skills.txt  -> tech software/frameworks
  - Tools Used.txt         -> hardware/tools
  - Content Model Reference.txt -> skills, knowledge, abilities (soft skills)
"""
import csv
import hashlib
import os
import sqlite3

DB_PATH = "data/onet.sqlite"
DATA_DIR = "data/db_30_1_text"


def _make_id(prefix: str, title: str) -> str:
    """Generate a deterministic short hex ID from a title."""
    h = hashlib.md5(title.encode()).hexdigest()[:12]
    return f"{prefix}-{h}"


def build_db():
    print(f"Building {DB_PATH}...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE skills (
            id TEXT PRIMARY KEY,
            title TEXT,
            category TEXT,
            importance REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE aliases (
            skill_id TEXT,
            alias TEXT,
            FOREIGN KEY(skill_id) REFERENCES skills(id)
        )
    """)

    # FTS5 virtual table for fast text search
    cursor.execute("""
        CREATE VIRTUAL TABLE skills_fts USING fts5(
            id UNINDEXED,
            title,
            aliases,
            tokenize='porter'
        )
    """)

    tech_count = 0
    tool_count = 0
    soft_count = 0

    # ---- 1. Technology Skills ----
    tech_path = os.path.join(DATA_DIR, "Technology Skills.txt")
    if os.path.exists(tech_path):
        print(f"  Loading {tech_path}...")
        seen_tech = {}  # title -> (id, aliases)
        with open(tech_path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)  # skip header
            for row in reader:
                if len(row) < 4:
                    continue
                # Columns: O*NET-SOC, Commodity Title (=example name), UNSPSC Code, Category Title
                example_name = row[1].strip()
                category_title = row[3].strip()

                if example_name not in seen_tech:
                    sid = _make_id("TECH", example_name)
                    seen_tech[example_name] = (sid, set())
                seen_tech[example_name][1].add(category_title)

        for title, (sid, alias_set) in seen_tech.items():
            try:
                cursor.execute(
                    "INSERT INTO skills (id, title, category, importance) VALUES (?, ?, ?, ?)",
                    (sid, title, "Technology", 0.5),
                )
                aliases_str = " ".join(alias_set)
                for alias in alias_set:
                    cursor.execute(
                        "INSERT INTO aliases (skill_id, alias) VALUES (?, ?)",
                        (sid, alias),
                    )
                cursor.execute(
                    "INSERT INTO skills_fts (id, title, aliases) VALUES (?, ?, ?)",
                    (sid, title, aliases_str),
                )
                tech_count += 1
            except sqlite3.IntegrityError:
                pass
    else:
        print(f"  WARNING: {tech_path} not found, skipping tech skills")

    # ---- 2. Tools Used ----
    tools_path = os.path.join(DATA_DIR, "Tools Used.txt")
    if os.path.exists(tools_path):
        print(f"  Loading {tools_path}...")
        seen_tools = {}
        with open(tools_path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)
            for row in reader:
                if len(row) < 4:
                    continue
                example_name = row[1].strip()
                category_title = row[3].strip()

                if example_name not in seen_tools:
                    sid = _make_id("TOOL", example_name)
                    seen_tools[example_name] = (sid, set())
                seen_tools[example_name][1].add(category_title)

        for title, (sid, alias_set) in seen_tools.items():
            try:
                cursor.execute(
                    "INSERT INTO skills (id, title, category, importance) VALUES (?, ?, ?, ?)",
                    (sid, title, "Tools", 0.3),
                )
                aliases_str = " ".join(alias_set)
                for alias in alias_set:
                    cursor.execute(
                        "INSERT INTO aliases (skill_id, alias) VALUES (?, ?)",
                        (sid, alias),
                    )
                cursor.execute(
                    "INSERT INTO skills_fts (id, title, aliases) VALUES (?, ?, ?)",
                    (sid, title, aliases_str),
                )
                tool_count += 1
            except sqlite3.IntegrityError:
                pass
    else:
        print(f"  WARNING: {tools_path} not found, skipping tools")

    # ---- 3. Content Model Reference (Soft Skills, Knowledge, Abilities) ----
    ref_path = os.path.join(DATA_DIR, "Content Model Reference.txt")
    if os.path.exists(ref_path):
        print(f"  Loading {ref_path}...")
        with open(ref_path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            next(reader)
            for row in reader:
                if len(row) < 3:
                    continue
                element_id = row[0].strip()
                title = row[1].strip()
                desc = row[2].strip()

                # Only include leaf-level items from relevant sections
                # 1.A = Abilities, 1.D = Work Styles, 2.A = Basic Skills,
                # 2.B = Cross-Functional Skills, 2.C = Knowledge
                if not element_id.startswith(
                    ("1.A", "1.D", "2.A", "2.B", "2.C")
                ):
                    continue

                # Skip broad category headers (title == description means it's a header)
                if desc == title:
                    continue

                # Determine category
                category = "Skill"
                if element_id.startswith("1.A"):
                    category = "Ability"
                elif element_id.startswith("1.D"):
                    category = "WorkStyle"
                elif element_id.startswith("2.C"):
                    category = "Knowledge"

                skill_id = f"SOFT-{element_id}"

                try:
                    cursor.execute(
                        "INSERT INTO skills (id, title, category, importance) VALUES (?, ?, ?, ?)",
                        (skill_id, title, category, 0.7),
                    )
                    # Store the full description as a searchable alias in FTS
                    cursor.execute(
                        "INSERT INTO skills_fts (id, title, aliases) VALUES (?, ?, ?)",
                        (skill_id, title, desc),
                    )
                    soft_count += 1
                except sqlite3.IntegrityError:
                    pass
    else:
        print(f"  WARNING: {ref_path} not found, skipping soft skills")

    conn.commit()

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_skills_title ON skills(LOWER(title))")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_aliases_alias ON aliases(LOWER(alias))")

    conn.close()

    print(f"\nDatabase built successfully!")
    print(f"  Technology skills: {tech_count}")
    print(f"  Tools:             {tool_count}")
    print(f"  Soft skills:       {soft_count}")
    print(f"  Total:             {tech_count + tool_count + soft_count}")


if __name__ == "__main__":
    build_db()
