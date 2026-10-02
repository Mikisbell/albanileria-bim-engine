# Visor 3D Next-Gen vs. Software Comercial (ETABS / Robot)

Este documento sustenta la implementación de características avanzadas (Next-Gen) en nuestro Visor 3D desarrollado con OpenSeesPy y Three.js, superando los paradigmas visuales de herramientas tradicionales como ETABS o SAP2000.

Mientras que el software comercial clásico se enfoca puramente en un esqueleto alámbrico y resultados crudos (orientados estrictamente al proyectista calculista y desconectados del impacto arquitectónico y económico), nuestro modelo introduce los siguientes tres pilares revolucionarios:

## 1. Ingeniería Explicable (Explainable Engineering)
**Problema tradicional:** En programas comerciales, cuando un muro de corte "falla", el software pinta el muro de color rojo e imprime un ratio en una tabla infinita (ej. `O/S 1.15`). Obliga al revisor o jurado a ir al manual del programa o a calcular a mano por qué falló.
**Nuestra Solución:** Se ha implementado un sistema interactivo en la tarjeta del Inspector de Elementos (FEM Heatmap). Al seleccionar un muro, aparece el botón **"🧠 Explicar Fórmula"**. 
Este botón abre un entorno de aprendizaje interactivo (Modal) que reconstruye la fórmula exacta del **Artículo 8.5.2 de la E.070 ($V_e \le 0.55 V_m$)** con los números precisos del muro ya reemplazados en pantalla. El modelo ya no solo te dice que "no cumple"; el modelo **te explica** la matemática detrás de la decisión, brindando total transparencia analítica frente a un jurado revisor.

## 2. Estimación Instantánea de Impacto Económico y Ambiental (LCA)
**Problema tradicional:** Ningún software de cálculo estructural convencional te advierte sobre el costo directo ni sobre la huella de carbono de las modificaciones geométricas. Engrosar una columna a 24x50 cm "soluciona" el problema numérico en ETABS, pero el ingeniero nunca ve el daño al presupuesto.
**Nuestra Solución:** Hemos acoplado a la barra de controles técnicos (Sidebar) un panel "Heads-Up Display" (HUD) enfocado en **Costo de Obra y Huella de Carbono (LCA)**. 
A medida que se compila la geometría real para WebGL, el código extrae automáticamente los volúmenes del esqueleto:
* Se estima el uso de Acero Corrugado en kilogramos.
* Se estima el volumen real de Concreto premezclado vertido in situ en m³.
* Se emite un presupuesto global para el casco estructural y su Equivalente de Dióxido de Carbono (Toneladas de CO2), concientizando al proyectista de la viabilidad económica y ecológica de la edificación.

## 3. Coherencia BIM "Caja Blanca" Total
**Problema tradicional:** ETABS requiere despojar al edificio de su piel arquitectónica. Un muro con ventana se modela como paños ciegos acoplados con "spandrels" invisibles. Es imposible saber si la columna estructural choca contra una puerta.
**Nuestra Solución:** El Visor 3D fusiona el análisis por elementos finitos del Script `20_modelo_opensees.py` directamente sobre el "Gemelo Digital" que incluye los muros divisorios (tabiques Pandereta), el pozo de luz, la caja de escalera y toda la carpintería (ventanas con alféizar y vidrios), pudiendo prender o apagar estas capas a voluntad. Esto detecta interferencias arquitectónicas a simple vista, logrando un control absoluto de la obra desde el navegador y offline (sin requerir licenciamientos en la nube ni Revit).

> **Conclusión para Sustentación:** Este visor no es solo una "visualización bonita". Es una herramienta paramétrica de toma de decisiones que educa al usuario, justifica sus cálculos apegándose estéticamente a la normativa peruana, y une la responsabilidad estructural con la economía y sustentabilidad del proyecto.
