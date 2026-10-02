# -*- coding: utf-8 -*-
"""Donde va cada cosa. Un solo lugar que lo diga.

    salidas/informe/   PNG que consume generar_docx.py
    salidas/laminas/   PNG + PDF A3 del juego de planos
    salidas/cad/       DXF, en metros reales

Escribir la ruta a mano en cada generador fue lo que produjo el desorden que
esto viene a arreglar: tres carpetas con nombres que se solapaban y ningun
archivo diciendo para quien producia.
"""
import os

DIBUJO = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(DIBUJO)
CALCULO = os.path.join(RAIZ, "calculo")

INFORME = os.path.join(RAIZ, "salidas", "informe")
LAMINAS = os.path.join(RAIZ, "salidas", "laminas")
CAD = os.path.join(RAIZ, "salidas", "cad")

for _d in (INFORME, LAMINAS, CAD):
    os.makedirs(_d, exist_ok=True)
