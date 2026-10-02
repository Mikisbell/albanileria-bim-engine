import streamlit as st
import os

# Mostrar logo corporativo centrado si existe
logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logo.png")
if os.path.exists(logo_path):
    c_l1, c_l2, c_l3 = st.columns([1.5, 1, 1.5])
    with c_l2:
        st.image(logo_path, use_container_width=True)

# Título y encabezado principal
st.markdown('''
<div style="text-align: center; margin-top: 1rem; margin-bottom: 2.5rem;">
    <h1 style="font-size: 2.6rem; font-weight: 900; color: #f8fafc; margin-bottom: 0.2rem;">🏢 Engine de Albañilería Confinada</h1>
    <h3 style="color: #3b82f6; font-weight: 600; margin-top: 0.2rem;">Diseño, Análisis Estructural y Evaluación LCA</h3>
    <p style="color: #94a3b8; font-size: 1.05rem; max-width: 650px; margin: 1rem auto 0 auto; line-height: 1.5;">
        Plataforma unificada para el modelamiento avanzado de edificaciones de albañilería confinada (5 niveles). Integra comprobaciones normativas (E.070 / E.030 / E.020), gemelo digital 3D interactivo y análisis de ciclo de vida.
    </p>
</div>
''', unsafe_allow_html=True)

# Tarjetas interactivas de navegación rápida
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("### 🧱 Visor BIM 3D")
        st.markdown(
            "Gemelo digital estructural interactivo con renderizado Three.js, visualización paño a paño, modos de vibración y despiece de muros."
        )
        st.page_link("pages/modelo_3d.py", label="Abrir Visor 3D →", icon="🧱", use_container_width=True)

with col2:
    with st.container(border=True):
        st.markdown("### 📊 Dashboard LCA & Costos")
        st.markdown(
            "Métricas ejecutivas de sostenibilidad: cálculo de huella de carbono (kg CO₂e), presupuesto de concreto, acero y albañilería."
        )
        st.page_link("pages/dashboard_lca.py", label="Ver Dashboard LCA →", icon="📊", use_container_width=True)

with col3:
    with st.container(border=True):
        st.markdown("### 📖 Memoria Técnica")
        st.markdown(
            "Memoria de cálculo paso a paso, auditoría comparativa frente a ETABS/CYPECAD y justificación de confinamientos según E.070."
        )
        st.page_link("pages/documentacion.py", label="Consultar Memoria →", icon="📖", use_container_width=True)

st.markdown("<br><hr><p style='text-align: center; color: #475569; font-size: 0.8rem;'>Desarrollado por Ing. Miguel Rivera Ospina • Universidad Continental</p>", unsafe_allow_html=True)
