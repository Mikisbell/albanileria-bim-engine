import glob, re

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Eliminar viejo style block
    content = re.sub(r'<style>.*?</style>', '', content, flags=re.DOTALL)
    content = content.replace('st.markdown(\"\"\"\n\n\"\"\", unsafe_allow_html=True)', '')
    content = content.replace('st.markdown(\"\"\"\n\"\"\", unsafe_allow_html=True)', '')
    
    # Eliminar viejos sidebars
    content = re.sub(r'st\.sidebar\.markdown\(.*?unsafe_allow_html=True\)', '', content, flags=re.DOTALL)

    # Insertar nuevo style después de set_page_config
    parts = content.split('initial_sidebar_state="expanded"\n)')
    if len(parts) == 2:
        new_content = parts[0] + 'initial_sidebar_state="expanded"\n)\n\n'
        new_content += 'st.markdown("""' + '''    <style>
        [data-testid="stHeader"] { display: none !important; }
        [data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid #1e293b !important; }
        
        /* Ocultar el enlace 'app' que se auto-genera */
        [data-testid="stSidebarNav"] ul li:first-child { display: none !important; }

        /* Reordenar el sidebar para que el Logo vaya arriba y el menú abajo */
        [data-testid="stSidebar"] > div:first-child > div:first-child {
            display: flex;
            flex-direction: column;
        }
        [data-testid="stSidebarNav"] { order: 2; margin-top: 1rem; }
        [data-testid="stSidebarUserContent"] { order: 1; }

        /* Estilos de Botones Nav */
        [data-testid="stSidebarNav"] span { color: #cbd5e1 !important; font-weight: 500; font-size: 0.95rem; font-family: 'Inter', sans-serif; }
        [data-testid="stSidebarNav"] div:hover { background-color: #1e293b !important; border-radius: 6px; }
        [data-testid="stSidebarNav"] [aria-current="page"] { background-color: #2563eb !important; border-radius: 6px; }
        [data-testid="stSidebarNav"] [aria-current="page"] span { color: #ffffff !important; font-weight: 700; }
        
        .block-container { 
            padding-top: 0rem !important; padding-bottom: 0rem !important; 
            padding-left: 0rem !important; padding-right: 0rem !important;
            max-width: 100% !important; margin: 0 !important;
        }
        iframe { height: 100vh !important; width: 100% !important; border: none; display: block; }
    </style>''' + '""", unsafe_allow_html=True)\n\n'
        new_content += '''st.sidebar.markdown('''
<div style="padding-bottom: 1rem; border-bottom: 1px solid #334155; margin-bottom: 0.5rem;">
    <h2 style="color: #3b82f6; font-weight: 900; margin: 0; font-size: 1.4rem;">📐 Albañilería BIM</h2>
</div>
''', unsafe_allow_html=True)

st.sidebar.markdown('''
<div style="margin-top: 2rem; padding: 1rem; border-top: 1px solid #1e293b; background-color: #0b1120; border-radius: 8px;">
    <div style="color: #10b981; font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; gap: 6px; margin-bottom: 4px;">
        <span style="height: 8px; width: 8px; background-color: #10b981; border-radius: 50%; display: inline-block;"></span> Server Online
    </div>
    <div style="color: #64748b; font-size: 0.7rem; font-family: monospace;">v2.1.0 • Build 2026</div>
    <div style="color: #475569; font-size: 0.65rem; margin-top: 8px;">Ingeniero: Miguel Rivera Ospina</div>
</div>
''', unsafe_allow_html=True)''' + '\n\n'
        new_content += parts[1].lstrip()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

for f in ['app.py', 'pages/1_Modelo.py', 'pages/2_Dashboard_LCA.py', 'pages/3_Documentacion.py']:
    try:
        update_file(f)
    except Exception as e:
        print(f"Error en {f}: {e}")
