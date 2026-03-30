import os, re

PROJECT = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(PROJECT, 'templates')

def fix_split_tags(text):
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        while re.search(r'\{%[^%]*$', line.rstrip()) and not line.rstrip().endswith('%}'):
            if i + 1 < len(lines):
                i += 1
                line = line.rstrip() + lines[i].lstrip()
            else:
                break
        result.append(line)
        i += 1
    return '\n'.join(result)

fixed_count = 0
for root, dirs, files in os.walk(TEMPLATES_DIR):
    for fname in files:
        if not fname.endswith('.html'):
            continue
        fpath = os.path.join(root, fname)
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            original = f.read()
        fixed = fix_split_tags(original)
        if fixed != original.replace('\r\n', '\n').replace('\r', '\n'):
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print(f"✅ Fixed: {fpath.replace(PROJECT, '')}")
            fixed_count += 1

print(f"\nDone! Fixed {fixed_count} files.")
if fixed_count == 0:
    print("No issues found - all templates already clean!")