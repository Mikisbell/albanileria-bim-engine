import re

file_path = 'generar_visor_3d.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'\.[A-Za-z0-9_-]+\s*\{[^\}]*top:[^\}]*\}|#[A-Za-z0-9_-]+\s*\{[^\}]*top:[^\}]*\}', content)
if match:
    print(match.group(0))

