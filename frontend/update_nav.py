import re

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(
    r'<Link to="/dashboard" style=\{\{[\s\S]*?\}\}>\s*<LibraryBig size=\{16\} /> Pathway Library\s*</Link>'
)

new_link = """<Link to="/dashboard" className="btn-reset" style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                textDecoration: 'none',
                padding: '0.5rem 1rem',
                fontSize: '0.85rem'
              }}>
                <LibraryBig size={16} /> Pathway Library
              </Link>"""

text = pattern.sub(new_link, text)

with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(text)