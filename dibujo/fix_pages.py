import os, re

files = ['pages/1_Modelo.py', 'pages/2_Dashboard_LCA.py', 'pages/3_Documentacion.py']

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Eliminar viejo titulo sidebar
    content = re.sub(r'st\.sidebar\.markdown\(\'\'\'\n<div style="padding-bottom: 1rem;.*?</div>\n\'\'\', unsafe_allow_html=True\)', '', content, flags=re.DOTALL)
    
    # Eliminar viejo footer sidebar
    content = re.sub(r'st\.sidebar\.markdown\("""\n<div style="margin-top: 2rem;.*?</div>\n""", unsafe_allow_html=True\)', '', content, flags=re.DOTALL)

    # Limpiar el CSS de la pagina, dejando solo lo esencial
    # En 1_Modelo.py queremos mantener el block-container y iframe CSS
    if '1_🏗️_Modelo.py' in f:
        new_css = '''st.markdown("""
    <style>
        .stAppDeployButton { display: none !important; }
        .block-container { 
            padding-top: 0rem !important; 
            padding-bottom: 0rem !important; 
            padding-left: 0rem !important; 
            padding-right: 0rem !important;
            max-width: 100% !important; 
            margin: 0 !important;
        }
        iframe { height: 100vh !important; width: 100% !important; border: none; display: block; }
    </style>
""", unsafe_allow_html=True)'''
        content = re.sub(r'st\.markdown\("""\n    <style>.*?    </style>\n""", unsafe_allow_html=True\)', new_css, content, flags=re.DOTALL)
    else:
        new_css = '''st.markdown("""
    <style>
        .stAppDeployButton { display: none !important; }
    </style>
""", unsafe_allow_html=True)'''
        content = re.sub(r'st\.markdown\("""\n    <style>.*?    </style>\n""", unsafe_allow_html=True\)', new_css, content, flags=re.DOTALL)

    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)
