# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import json
import os
import sys

# CSS para pantalla completa y para permitir interacción con el 3D sin bloqueos
st.markdown("""
    <style>
        .stAppDeployButton { display: none !important; }
        
        /* Permitir que los clics y arrastres del mouse atraviesen el header hacia el visor 3D */
        [data-testid="stHeader"] { 
            background-color: transparent !important; 
            pointer-events: none !important; 
        }
        [data-testid="stHeader"] * { 
            pointer-events: auto !important; 
        }
        
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
""", unsafe_allow_html=True)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

import dibujo.generar_visor_3d as gv3d

@st.cache_data
def get_viewer_html():
    datos = gv3d.extraer_datos()
    html = gv3d.generar_html(datos)
    
    # Inyectar librerías locales Three.js y OrbitControls para garantizar 100% offline y cero fallos de carga
    p_three = os.path.join(RAIZ, "salidas", "visor_3d", "three.min.js")
    p_orbit = os.path.join(RAIZ, "salidas", "visor_3d", "OrbitControls.js")
    
    if os.path.exists(p_three) and os.path.exists(p_orbit):
        try:
            with open(p_three, "r", encoding="utf-8") as f:
                three_code = f.read()
            with open(p_orbit, "r", encoding="utf-8") as f:
                orbit_code = f.read()
            
            tag_three = '<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>'
            tag_orbit = '<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>'
            
            if tag_three in html and tag_orbit in html:
                html = html.replace(tag_three, f"<script>\n{three_code}\n</script>")
                html = html.replace(tag_orbit, f"<script>\n{orbit_code}\n</script>")
        except Exception:
            pass
            
    return html

try:
    html_str = get_viewer_html()
except Exception as e:
    st.error(f"Error generando el visor 3D: {e}")
    st.stop()

# Mostrar el visor HTML nativo (Three.js) dentro de Streamlit
components.html(html_str, height=1000, scrolling=False)
