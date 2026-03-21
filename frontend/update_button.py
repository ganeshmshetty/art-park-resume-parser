import re

with open('src/Dashboard.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = re.compile(
    r'<Link\s+to=\{`/pathway/\$\{run\.id\}`\}\s+style=\{\{[\s\S]*?\}\}\s*>\s*Track Pathway <ExternalLink size=\{16\} />\s*</Link>'
)

new_link = """<Link
                  to={`/pathway/${run.id}`}
                  className="btn-reset"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    textDecoration: 'none',
                    padding: '0.5rem 1rem'
                  }}
                >
                  Track Pathway <ExternalLink size={16} />
                </Link>"""

text = pattern.sub(new_link, text)

with open('src/Dashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(text)