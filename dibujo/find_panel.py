import re

file_path = 'generar_visor_3d.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar info-panel
match = re.search(r'<div id="info-panel".*?>', content, re.DOTALL)
if match:
    print('ENCONTRADO INFO PANEL:')
    print(match.group(0))
else:
    print('NO INFO PANEL')
