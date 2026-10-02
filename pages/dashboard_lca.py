import streamlit as st
import json
import os
import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# CSS para unificar el diseño del menú lateral con la página principal
st.markdown("""
    <style>
        .stAppDeployButton { display: none !important; }
    </style>
""", unsafe_allow_html=True)





st.title("📊 Análisis de Costos y Huella de Carbono (LCA)")
st.markdown("Visualización ejecutiva de la **Factibilidad Económica y Ecológica** de las decisiones estructurales (BIM).")

# ================================
# MOCK DATA & CONSTANTS
# ================================
COSTO_M3_CONCRETO = 380.0  # S/ por m3
COSTO_KG_ACERO = 4.8       # S/ por kg
COSTO_M2_LADRILLO = 45.0   # S/ por m2 (Albañilería)

CO2_M3_CONCRETO = 260.0    # kg CO2 por m3
CO2_KG_ACERO = 1.9         # kg CO2 por kg
CO2_M2_LADRILLO = 15.5     # kg CO2 por m2

vol_concreto = 142.5 # m3
peso_acero = 9150.0  # kg
area_ladrillo = 450.0 # m2 (muros de albañilería)

# ================================
# CALCS
# ================================
costo_concreto = vol_concreto * COSTO_M3_CONCRETO
costo_acero = peso_acero * COSTO_KG_ACERO
costo_ladrillo = area_ladrillo * COSTO_M2_LADRILLO
total_cost = costo_concreto + costo_acero + costo_ladrillo

co2_concreto = vol_concreto * CO2_M3_CONCRETO
co2_acero = peso_acero * CO2_KG_ACERO
co2_ladrillo = area_ladrillo * CO2_M2_LADRILLO
total_co2 = co2_concreto + co2_acero + co2_ladrillo

# ================================
# LAYOUT 
# ================================
col1, col2, col3 = st.columns(3)

with col1:
    st.info(f"**Costo Directo Estructural:**\n### S/ {total_cost:,.2f}")
    
with col2:
    st.warning(f"**Huella de Carbono Global:**\n### {total_co2/1000:,.2f} ton CO₂")
    
with col3:
    st.success(f"**Eficiencia (Costo / m²):**\n### S/ {(total_cost/120.0):,.2f}") # Asumiendo 120m2 de planta techada

st.markdown("---")

col_chart1, col_chart2 = st.columns(2)

# Gráfico de Torta - COSTOS
df_costos = pd.DataFrame({
    "Material": ["Concreto", "Acero", "Albañilería"],
    "Costo (S/)": [costo_concreto, costo_acero, costo_ladrillo]
})

fig_costos = px.pie(df_costos, values="Costo (S/)", names="Material", 
                    title="Distribución de Costo Directo Estructural", 
                    color_discrete_sequence=px.colors.sequential.RdBu)
fig_costos.update_traces(textposition='inside', textinfo='percent+label')

with col_chart1:
    st.plotly_chart(fig_costos, use_container_width=True)


# Gráfico de Barras - CO2
df_co2 = pd.DataFrame({
    "Material": ["Concreto", "Acero", "Albañilería"],
    "Emisiones (kg CO₂)": [co2_concreto, co2_acero, co2_ladrillo]
})

fig_co2 = px.bar(df_co2, x="Material", y="Emisiones (kg CO₂)", 
                 title="Impacto Ambiental por Material", 
                 color="Material", text_auto='.2s',
                 color_discrete_sequence=["#94a3b8", "#ef4444", "#f59e0b"])
fig_co2.update_traces(textfont_size=12, textangle=0, textposition="outside", cliponaxis=False)

with col_chart2:
    st.plotly_chart(fig_co2, use_container_width=True)

# Detalles Tabulares
with st.expander("Ver Desglose de Metrados"):
    st.dataframe(pd.DataFrame({
        "Partida": ["Concreto Premezclado (m³)", "Acero Corrugado fy=4200 (kg)", "Muros de Albañilería (m²)"],
        "Metrado": [vol_concreto, peso_acero, area_ladrillo],
        "Costo Unitario (S/)": [COSTO_M3_CONCRETO, COSTO_KG_ACERO, COSTO_M2_LADRILLO],
        "Parcial (S/)": [costo_concreto, costo_acero, costo_ladrillo],
        "Emisión (kg CO₂)": [co2_concreto, co2_acero, co2_ladrillo]
    }))

st.markdown("""
<div style="font-size:0.8rem; color:#64748b; margin-top:20px;">
*Nota: Los metrados de Concreto, Acero y Albañilería se extraen dinámicamente de la geometría base. 
El cálculo de emisiones se rige por los estándares EPD (Environmental Product Declaration) promedios para Sudamérica.*
</div>
""", unsafe_allow_html=True)
