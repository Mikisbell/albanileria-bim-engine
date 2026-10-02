import re

file_path = 'generar_visor_3d.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'#info-panel\s*\{[^}]*\}', content, re.DOTALL)
if match:
    print(match.group(0))

