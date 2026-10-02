import os
import sys
from pathlib import Path
import streamlit as st

# --- BOOTSTRAP DE RUTAS CENTRALIZADO ---
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
CALCULO_DIR = BASE_DIR / "calculo"
if str(CALCULO_DIR) not in sys.path:
    sys.path.insert(0, str(CALCULO_DIR))

# --- CONFIGURACIÓN GLOBAL DE STREAMLIT ---
st.set_page_config(
    page_title="BIM Engine | Albañilería Confinada E.070",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ESTILOS GLOBALES ---
st.markdown("""
    <style>
        .stAppDeployButton { display: none !important; }
        
        /* Ajuste de tamaño del Logo corporativo en el sidebar */
        [data-testid="stLogo"] {
            height: 3.8rem !important;
            max-height: 65px !important;
        }
        [data-testid="stLogo"] img {
            height: 3.8rem !important;
            max-height: 65px !important;
            width: auto !important;
            object-fit: contain !important;
        }
        [data-testid="stSidebarHeader"] {
            padding-top: 1.2rem !important;
            padding-bottom: 0.6rem !important;
            height: auto !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- LOGO EN SIDEBAR ---
logo_path = BASE_DIR / "logo.png"
if logo_path.exists():
    try:
        st.logo(str(logo_path), size="large")
    except Exception:
        try:
            st.logo(str(logo_path))
        except Exception:
            pass

# --- ROUTER PROFESIONAL DE PÁGINAS (st.navigation) ---
inicio = st.Page("pages/inicio.py", title="Inicio", icon="🏠", default=True)
modelo = st.Page("pages/modelo_3d.py", title="Visor BIM 3D", icon="🧱")
dash   = st.Page("pages/dashboard_lca.py", title="Dashboard LCA & Costos", icon="📊")
doc    = st.Page("pages/documentacion.py", title="Memoria Técnica & E.070", icon="📖")

pg = st.navigation({
    "🏢 Plataforma BIM": [inicio, modelo],
    "📐 Ingeniería & Sostenibilidad": [dash, doc]
})
pg.run()

# --- FOOTER PROFESIONAL EN SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style="font-size: 0.8rem; color: #64748b; line-height: 1.4;">
    <strong>Ing. Miguel Rivera Ospina</strong><br>
    BIM Structural Engine v2.1<br>
    <em>Universidad Continental</em>
</div>
""", unsafe_allow_html=True)
