import re

file_path = 'generar_visor_3d.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'<div[^>]*>.*?Edificio Multifamiliar', content, re.DOTALL)
if match:
    # Print a window around the match
    idx = match.start()
    print(content[max(0, idx-100) : min(len(content), idx+200)])
