# 🏢 Albañilería BIM Engine

> **Plataforma unificada para el diseño estructural, análisis sísmico y evaluación de sostenibilidad (LCA) de edificaciones de albañilería confinada (5 niveles) bajo la Norma Técnica Peruana E.070 / E.030 / E.020.**

---

## 🌟 Características Principales

* **🧱 Gemelo Digital 3D Interactivo:** Visor espacial basado en Three.js con navegación orbital, descomposición de paños de albañilería, columnas de confinamiento, soleras, vigas y losas.
* **📊 Dashboard LCA & Presupuesto Directo:** Cuantificación en tiempo real de huella de carbono ($\text{kg CO}_2\text{e}$) y costos directos de concreto, acero de refuerzo y unidades de albañilería.
* **📖 Memoria de Cálculo & Explicabilidad Normativa:** Verificación paño a paño del corte admisible ($V_m$), control de fisuración por sismo moderado ($V_e \le 0.55 V_m$), amplificación de corte dinámico y diseño de confinamientos según el Capítulo 8 de la E.070.
* **⚖️ Auditoría Frente a Software Comercial:** Comparativa técnica y resolución de vacíos analíticos existentes en CSI ETABS, CYPECAD y Robot Structural.

---

## 🚀 Despliegue Local

```bash
# 1. Clonar el repositorio
git clone https://github.com/Mikisbell/albanileria-bim-engine.git
cd albanileria-bim-engine

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar la aplicación Streamlit
streamlit run app.py
```

---

## 📐 Autor y Créditos

* **Ingeniero a cargo:** Miguel Rivera Ospina
* **Institución:** Universidad Continental
* **Versión del Motor:** v2.1.0 BIM Structural Engine
