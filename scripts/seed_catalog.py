import json
import random
import uuid

def seed_catalog():
    # Load O*NET skills to base courses on real data
    try:
        with open('data/onet_skills.json', 'r') as f:
            skills = json.load(f)
    except FileNotFoundError:
        print("Error: data/onet_skills.json not found. Run build_onet_skills.py first.")
        return

    print(f"Loaded {len(skills)} skills. Generating catalog...")

    # Domains for variety
    domains = ["Technology", "Management", "Operations", "Healthcare", "Finance"]
    
    # Levels and their multipliers
    levels = ["Beginner", "Intermediate", "Advanced"]
    
    modules = []
    
    # We'll generate courses for valid skills (those with IDs)
    # Filter for skills that look like technical or hard skills to make it realistic
    target_skills = [s for s in skills if s.get('id')]
    
    # Pick a random sample to generate courses for, ensuring we hit the 80-120 target
    # Let's generate about 100 courses
    selected_skills = random.sample(target_skills, min(len(target_skills), 80))

    for skill in selected_skills:
        # Create 1-2 courses per selected skill
        num_courses = random.choice([1, 2])
        
        for _ in range(num_courses):
            level = random.choice(levels)
            domain = random.choice(domains)
            
            # Generate a title
            if level == "Beginner":
                title = f"Introduction to {skill['title']}"
                duration = random.choice([30, 45, 60])
                prereqs = [] if not modules else [random.choice(modules)['id']]  # Random dependency
            elif level == "Intermediate":
                title = f"{skill['title']} Fundamentals"
                duration = random.choice([60, 90, 120])
                prereqs = [] 
            else:
                title = f"Advanced {skill['title']} Mastery"
                duration = random.choice([120, 180, 240])
                prereqs = []

            module = {
                "id": f"mod_{uuid.uuid4().hex[:8]}",
                "title": title,
                "description": f"A comprehensive {level.lower()} module focusing on {skill['title']}.",
                "skill_ids": [skill['id']],
                "domain": skill.get('category', 'Technology'),
                "level": level,
                "duration_min": duration,
                "prerequisites": prereqs
            }
            modules.append(module)

    # Ensure directory exists
    import os
    os.makedirs('data/catalog', exist_ok=True)
    
    output_path = 'data/catalog/modules.json'
    with open(output_path, 'w') as f:
        json.dump(modules, f, indent=2)
        
    print(f"Successfully generated {len(modules)} modules in {output_path}")
    print("Sample module:", json.dumps(modules[0], indent=2))

if __name__ == "__main__":
    seed_catalog()
