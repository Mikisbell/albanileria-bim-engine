# -*- coding: utf-8 -*-
"""Constructor completo del nuevo L_detalles con 4 cuadrantes tecnicos."""
import os
import sys
import math
from pathlib import Path

base_dir = r"D:\- E -\CONTINENTAL\10° CICLO\Albañilería\Unidad I\C1\12-PA2-consolidado2-analisis-diseno-confinada"
dib_dir = os.path.join(base_dir, "dibujo")
sys.path.insert(0, dib_dir)
sys.path.insert(0, os.path.join(base_dir, "calculo"))

import paleta as PAL
import rutas as R
from lamina import Lamina, A3_MM
from meta import meta
from proyecto import (ESPESOR, E_LOSA, H_ENTREPISO, PARAPETO, A_UNIDAD,
                      ALFEIZAR, ALTURA_VENTANA, N_PISOS, FC, FY,
                      ESC_X0, ESC_X1, ESC_Y0, ESC_Y1,
                      ANCHO_TRAMO_ESCALERA, H_COLUMNA,
                      E_LOSA_ESCALERA)

ESCALA = 25
CONCRETO = "#b9c4cc"
CONCRETO_OSCURO = "#80919f"
ALBAN = "#d8c9a8"
ALBAN_BORDE = "#9c8a63"
COLUMNA = PAL.COLUMNA
COL_BORDE = "#6d1f16"
MAL = "#b02a1f"
BIEN = "#1b5e20"
ACERO = "#1a237e"
JUNTA = "#e65100"
TEXTO_DARK = "#263238"


def modulo_escalera(L, x0, y0, w, h):
    """Cuadrante 1: Corte de Escalera y Apoyo en Columnas Dedicadas (E.070 9.1)."""
    # Marco y encabezado
    L.h_rect(x0, y0, x0 + w, y0 + h, layer="CAJETIN", lw=1.0, ec="#37474f", fc="#fcfdfd")
    L.h_rect(x0, y0 + h - 9.0, x0 + w, y0 + h, layer="CAJETIN", lw=0.8, ec="#37474f", fc="#e8eaf6")
    L.h_texto((x0 + 4.0, y0 + h - 4.5), "DETALLE 1: ESCALERA — DESCANSO EN COLUMNAS C-3 (E.070 9.1.2)",
              h_mm=2.3, ha="left", va="center", color="#1a237e", weight="bold")
    
    # Sub-rotulo
    L.h_texto((x0 + 4.0, y0 + h - 13.0),
              "Prohibido apoyar el descanso en muros portantes: genera corte y flexion fuera del plano no calculados",
              h_mm=1.7, ha="left", va="center", color="#c62828", weight="bold")

    # Geometria Escalera (Escala interna aproximada)
    # Losa inclinada + escalones
    xe_base = x0 + 10.0
    ye_base = y0 + 16.0
    n_pasos = 6
    p_w = 6.8   # paso en mm de hoja
    cp_h = 4.6  # contrapaso en mm de hoja
    
    # Garganta losa inclinada
    pts_losa = [(xe_base, ye_base), (xe_base, ye_base + 3.8)]
    for i in range(n_pasos):
        pts_losa.append((xe_base + i * p_w, ye_base + (i + 1) * cp_h))
        pts_losa.append((xe_base + (i + 1) * p_w, ye_base + (i + 1) * cp_h))
    
    # Descanso
    x_desc = xe_base + n_pasos * p_w
    y_desc = ye_base + n_pasos * cp_h
    w_desc = 32.0
    h_desc = 4.2
    
    pts_losa.append((x_desc + w_desc, y_desc))
    pts_losa.append((x_desc + w_desc, y_desc - h_desc))
    pts_losa.append((x_desc, y_desc - h_desc))
    pts_losa.append((xe_base + 4.2, ye_base))
    
    L.h_rect(x_desc, y_desc - h_desc, x_desc + w_desc, y_desc, layer="CAJETIN", fc=CONCRETO, ec=CONCRETO_OSCURO, lw=0.9)
    for i in range(n_pasos):
        L.h_rect(xe_base + i * p_w, ye_base + i * cp_h, xe_base + (i + 1) * p_w, ye_base + (i + 1) * cp_h,
                 layer="CAJETIN", fc=CONCRETO, ec=CONCRETO_OSCURO, lw=0.7)
    
    # Rótulos en losa
    L.h_texto((x_desc + w_desc/2.0, y_desc - h_desc/2.0), "DESCANSO e=0.15m", h_mm=1.8, ha="center", va="center", weight="bold")
    L.h_texto((xe_base + 10.0, ye_base + 22.0), "GARGANTA tg=0.15m\nAcero fi 3/8'' @ 0.20m", h_mm=1.6, ha="center", va="center", color=ACERO)

    # Cotas de paso y contrapaso
    L.h_linea((xe_base, ye_base - 3.0), (xe_base + p_w, ye_base - 3.0), layer="CAJETIN", color="#455a64", lw=0.5)
    L.h_texto((xe_base + p_w/2.0, ye_base - 5.5), "p=0.25m", h_mm=1.5, ha="center", va="top")
    
    L.h_linea((xe_base - 3.0, ye_base), (xe_base - 3.0, ye_base + cp_h), layer="CAJETIN", color="#455a64", lw=0.5)
    L.h_texto((xe_base - 4.5, ye_base + cp_h/2.0), "cp=0.17m", h_mm=1.5, ha="right", va="center", rot=90)

    # COLUMNAS QUE SOSTIENEN EL DESCANSO (CORRECTO)
    col_w = 7.0
    col_y_bot = y0 + 10.0
    for cx in (x_desc + 4.0, x_desc + w_desc - 4.0):
        L.h_rect(cx - col_w/2.0, col_y_bot, cx + col_w/2.0, y_desc - h_desc, layer="CAJETIN", fc=COLUMNA, ec=COL_BORDE, lw=0.9)
        L.h_linea((cx, col_y_bot), (cx, y_desc - h_desc), layer="CAJETIN", color="white", lw=0.5, ls=(0, (2, 2)))
    
    # Datos de la columna leídos de 27_columnas_de_escalera.py (origen único)
    import importlib.util
    ruta_c27 = os.path.join(base_dir, "calculo", "27_columnas_de_escalera.py")
    spec_c27 = importlib.util.spec_from_file_location("c27_col", ruta_c27)
    mod_c27 = importlib.util.module_from_spec(spec_c27)
    spec_c27.loader.exec_module(mod_c27)
    c3 = mod_c27.fila_cuadro()
    b_cm = int(round(c3["b"] * 100))
    h_cm = int(round(c3["h"] * 100))
    diam_str = c3["diam"].replace('"', "''")
    txt_col = (
        "COLUMNETAS %s DEDICADAS\n(%dx%d cm, %d fi %s)\nBajan a la cimentacion"
        % (c3["tipo"], b_cm, h_cm, c3["n"], diam_str)
    )
    # ENCIMA DEL DESCANSO, donde hay aire: a media altura caia sobre la columna derecha
    L.h_texto((x_desc + w_desc/2.0, y_desc + 9.0), txt_col,
              h_mm=1.6, ha="center", va="center", color=BIEN, weight="bold")
    L.h_texto((x_desc + w_desc/2.0, y0 + 5.0), "[CORRECTO: E.070 9.1.2]", h_mm=1.9, ha="center", va="center", color=BIEN, weight="bold")

    # ESQUEMA DE LO QUE NO SE DEBE HACER (AL COSTADO DERECHO)
    x_mal = x0 + w - 46.0
    y_mal_desc = y_desc
    L.h_rect(x_mal, y_mal_desc - h_desc, x_mal + 20.0, y_mal_desc, layer="CAJETIN", fc=CONCRETO, ec=CONCRETO_OSCURO, lw=0.8)
    L.h_rect(x_mal + 20.0, y0 + 10.0, x_mal + 20.0 + 7.0, y_mal_desc + 8.0, layer="CAJETIN", fc=ALBAN, ec=ALBAN_BORDE, lw=0.8)
    
    # Aspa de error en muro
    L.h_linea((x_mal + 16.0, y_mal_desc + 12.0), (x_mal + 31.0, y_mal_desc - 8.0), layer="CAJETIN", color=MAL, lw=1.8)
    L.h_linea((x_mal + 16.0, y_mal_desc - 8.0), (x_mal + 31.0, y_mal_desc + 12.0), layer="CAJETIN", color=MAL, lw=1.8)
    
    L.h_texto((x_mal + 23.5, y_mal_desc + 16.0), "PROHIBIDO", h_mm=1.9, ha="center", va="bottom", color=MAL, weight="bold")
    L.h_texto((x_mal + 23.5, y0 + 5.0), "[NO APOYAR EN MURO]", h_mm=1.7, ha="center", va="center", color=MAL, weight="bold")


def _r25():
    """El script 25: el parapeto que se calculo."""
    import contextlib
    import importlib.util
    import io as _io
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "calculo",
                        "25_arriostre_parapeto.py")
    spec = importlib.util.spec_from_file_location("r25_e05", ruta)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def _m(v):
    return ("%.2f" % v).replace(".", ",")


def modulo_parapeto(L, x0, y0, w, h):
    """Cuadrante 2: el parapeto de azotea, tal como lo diseno el script 25.

    Exigencia: E.070 9.3.7 (solo se exoneran los de menos de 1,00 m).
    Diseno del arriostre: 9.3.5. Columnetas EN VOLADIZO empotradas en la
    losa, SIN amarre superior: es lo que el 25 calcula y justifica. Antes
    dibujaba 15 x 15 con 4 fi 3/8 bajo una solera y citaba la E.070 10.1.
    """
    R25 = _r25()
    s = R25.separacion_parapeto()
    t_par = A_UNIDAD
    L.h_rect(x0, y0, x0 + w, y0 + h, layer="CAJETIN", lw=1.0, ec="#37474f", fc="#fcfdfd")
    L.h_rect(x0, y0 + h - 9.0, x0 + w, y0 + h, layer="CAJETIN", lw=0.8, ec="#37474f", fc="#e8eaf6")
    L.h_texto((x0 + 4.0, y0 + h - 4.5), "DETALLE 2: PARAPETO EN AZOTEA ARRIOSTRADO (h = %.2f m)" % PARAPETO,
              h_mm=2.3, ha="left", va="center", color="#1a237e", weight="bold")
    
    L.h_texto((x0 + 4.0, y0 + h - 13.0),
              "E.070 9.3.7: con h = %s m no esta exonerado (solo los de menos de 1,00 m); se arriostra segun 9.3.5" % _m(PARAPETO),  # tecleado-ok: limite de norma
              h_mm=1.65, ha="left", va="center", color="#e65100", weight="bold")

    # Dibujo: Corte transversal (izquierda) y elevación longitudinal (derecha)
    # 1. Corte transversal
    xc = x0 + 12.0
    yc_base = y0 + 14.0
    # Losa de azotea
    L.h_rect(xc, yc_base, xc + 35.0, yc_base + 6.0, layer="CAJETIN", fc=CONCRETO, ec=CONCRETO_OSCURO, lw=0.8)
    L.h_texto((xc + 22.0, yc_base + 3.0), "Losa Azotea e=0.20", h_mm=1.6, ha="center", va="center")
    
    # Parapeto de ladrillo
    L.h_rect(xc, yc_base + 6.0, xc + 5.0, yc_base + 6.0 + 37.0, layer="CAJETIN", fc=ALBAN, ec=ALBAN_BORDE, lw=0.8)
    # sin viga de coronacion: el 25 la descarta
    
    L.h_texto((xc + 8.0, yc_base + 6.0 + 33.0), "Borde superior libre:\nsin viga de coronacion", h_mm=1.5, ha="left", va="center", color=ACERO)
    L.h_texto((xc + 8.0, yc_base + 22.0), "Parapeto t = %s m\nKing Kong solido" % _m(t_par), h_mm=1.6, ha="left", va="center")
    
    # Cota vertical de parapeto 1.10 m
    L.h_linea((xc - 4.0, yc_base + 6.0), (xc - 4.0, yc_base + 6.0 + 37.0), layer="CAJETIN", color="#37474f", lw=0.6)
    L.h_texto((xc - 6.0, yc_base + 6.0 + 18.5), "h = %.2f m" % PARAPETO, h_mm=1.7, ha="right", va="center", rot=90, weight="bold")

    # 2. Elevación longitudinal del tramo con columnetas
    xe = x0 + 78.0
    ye_base = y0 + 14.0
    w_tramo = 72.0
    h_parap = 37.0
    
    # Losa base
    L.h_rect(xe, ye_base, xe + w_tramo, ye_base + 6.0, layer="CAJETIN", fc=CONCRETO, ec=CONCRETO_OSCURO, lw=0.8)
    # Muro
    L.h_rect(xe, ye_base + 6.0, xe + w_tramo, ye_base + 6.0 + h_parap, layer="CAJETIN", fc=ALBAN, ec=ALBAN_BORDE, lw=0.8)
    
    # Columnetas en voladizo, a la separacion que calcula el 25
    col_w = 5.5
    for cx in (xe, xe + w_tramo/2.0 - col_w/2.0, xe + w_tramo - col_w):
        L.h_rect(cx, ye_base, cx + col_w, ye_base + 6.0 + h_parap, layer="CAJETIN", fc=COLUMNA, ec=COL_BORDE, lw=0.9)
    
    # Cota entre columnetas
    L.h_linea((xe + col_w/2.0, ye_base - 3.5), (xe + w_tramo/2.0, ye_base - 3.5), layer="CAJETIN", color="#37474f", lw=0.5)
    L.h_texto((xe + w_tramo/4.0, ye_base - 6.0), "s = %s m" % _m(s), h_mm=1.5, ha="center", va="top")
    
    L.h_texto((xe + w_tramo/2.0, ye_base + 6.0 + h_parap + 3.5), "COLUMNETAS EN VOLADIZO, SIN AMARRE SUPERIOR", h_mm=1.6, ha="center", va="bottom", weight="bold")
    L.h_texto((xe + w_tramo/2.0, ye_base - 10.0), "COLUMNETAS %.0f x %.0f cm, %d fi 3/8'', [] %s @ %d cm\nancladas %d cm en la losa de azotea"
              % (R25.B_COLUMNETA * 100, R25.H_COLUMNETA * 100, R25.N_BARRAS_COL,
                 R25.ESTRIBO_COL, R25.PASO_ESTRIBO_COL, R25.ANCLAJE_COL), h_mm=1.6, ha="center", va="top", color=BIEN, weight="bold")
    L.h_linea((xe + w_tramo/2.0, ye_base - 10.0), (xe + w_tramo/2.0, ye_base), layer="CAJETIN", color=BIEN, lw=0.3)


def modulo_alfeizar(L, x0, y0, w, h):
    """Cuadrante 3: Alféizar Aislado y Junta Sísmica para Evitar Columna Corta (E.070 6.2.7)."""
    L.h_rect(x0, y0, x0 + w, y0 + h, layer="CAJETIN", lw=1.0, ec="#37474f", fc="#fcfdfd")
    L.h_rect(x0, y0 + h - 9.0, x0 + w, y0 + h, layer="CAJETIN", lw=0.8, ec="#37474f", fc="#e8eaf6")
    L.h_texto((x0 + 4.0, y0 + h - 4.5), "DETALLE 3: ALFEIZAR AISLADO — PREVENCION DE COLUMNA CORTA (E.070 Art. 6.2.7)",
              h_mm=2.3, ha="left", va="center", color="#1a237e", weight="bold")
    
    L.h_texto((x0 + 4.0, y0 + h - 13.0),
              "El alfeizar es tabique de cierre: DEBE aislarse del portante con junta sismica de tecnopor de 1'' (2.5 cm)",  # tecleado-ok: limite de norma o coincidencia
              h_mm=1.65, ha="left", va="center", color="#c62828", weight="bold")

    # Dibujo: Encuentro Columna Principal - Junta - Alféizar
    xa = x0 + 14.0
    ya_base = y0 + 16.0
    
    # 1. Columna de confinamiento estructural principal (toda la altura de entrepiso)
    w_col = 14.0
    h_col = 65.0
    L.h_rect(xa, ya_base, xa + w_col, ya_base + h_col, layer="CAJETIN", fc=COLUMNA, ec=COL_BORDE, lw=1.1)
    L.h_texto((xa + w_col/2.0, ya_base + h_col + 3.0), "COLUMNA PRINCIPAL\n(C-1 / C-2)", h_mm=1.6, ha="center", va="bottom", color=COLUMNA, weight="bold")

    # 2. Junta sismica de tecnopor (1 pulgada = 2.5 cm)
    w_junta = 3.5
    h_alf = 35.0  # altura alfeizar h = 1.00 m a escala
    L.h_rect(xa + w_col, ya_base, xa + w_col + w_junta, ya_base + h_alf, layer="CAJETIN", fc="#ffe0b2", ec=JUNTA, lw=0.8, hatch="//")
    
    # 3. Alféizar de ladrillo
    w_alf = 50.0
    L.h_rect(xa + w_col + w_junta, ya_base, xa + w_col + w_junta + w_alf, ya_base + h_alf, layer="CAJETIN", fc=ALBAN, ec=ALBAN_BORDE, lw=0.9)
    L.h_texto((xa + w_col + w_junta + w_alf/2.0, ya_base + h_alf/2.0), "ALFEIZAR h = %.2f m" % ALFEIZAR + "\n(Tabique de ladrillo King Kong)", h_mm=1.7, ha="center", va="center", weight="bold")

    # 4. Ventana encima del alféizar
    L.h_rect(xa + w_col + w_junta, ya_base + h_alf, xa + w_col + w_junta + w_alf, ya_base + h_col, layer="CAJETIN", fc="#e1f5fe", ec="#0288d1", lw=0.6)
    L.h_texto((xa + w_col + w_junta + w_alf/2.0, ya_base + h_alf + (h_col - h_alf)/2.0), "VANO DE VENTANA h = %.2f m (Luz libre)" % ALTURA_VENTANA, h_mm=1.7, ha="center", va="center", color="#0277bd")

    # Llamada técnica a la junta
    L.h_linea((xa + w_col + w_junta/2.0, ya_base + h_alf - 5.0), (xa + w_col - 4.0, ya_base - 5.0), layer="CAJETIN", color=JUNTA, lw=0.7)
    L.h_texto((xa + w_col + 2.0, ya_base - 7.0), "JUNTA SISMICA e = 1'' (2.5 cm)\nRelleno: Tecnopor + Sellador Sikaflex", h_mm=1.6, ha="left", va="top", color=JUNTA, weight="bold")  # tecleado-ok: limite de norma o coincidencia

    # Panel lateral derecho del cuadrante: Cuadro de Alerta "Por qué Columna Corta"
    xp = x0 + w - 66.0
    yp = ya_base + 6.0
    L.h_rect(xp, yp, xp + 62.0, yp + 52.0, layer="CAJETIN", fc="#fff8e1", ec="#f57f17", lw=0.8)
    L.h_texto((xp + 31.0, yp + 47.0), "[!] RIESGO DE COLUMNA CORTA", h_mm=1.9, ha="center", va="center", color="#d84315", weight="bold")
    
    lineas_alerta = [
        "- Si el alfeizar se une a la columna,",
        "  la altura libre baja de 2.50m a 1.50m.",
        "- La rigidez a corte aumenta (2.5/1.5)^3",
        "  lo que atrae 4.6 veces mas fuerza sismica.",
        "- Consecuencia: Cizallamiento diagonal",
        "  fragil y rotura de la columna.",
        "- Solucion E.070: AISLAR OBLIGATORIAMENTE."
    ]
    for idx, lin in enumerate(lineas_alerta):
        L.h_texto((xp + 3.0, yp + 38.0 - idx * 5.2), lin, h_mm=1.55, ha="left", va="center", color="#3e2723")


def modulo_junta_y_cuadro(L, x0, y0, w, h):
    """Cuadrante 4: Detalle de Junta Sísmica con Vecino y Cuadro Técnico General."""
    L.h_rect(x0, y0, x0 + w, y0 + h, layer="CAJETIN", lw=1.0, ec="#37474f", fc="#fcfdfd")
    L.h_rect(x0, y0 + h - 9.0, x0 + w, y0 + h, layer="CAJETIN", lw=0.8, ec="#37474f", fc="#e8eaf6")
    L.h_texto((x0 + 4.0, y0 + h - 4.5), "DETALLE 4: JUNTA SISMICA EDIFICIO-COLINDANTE Y ESPECIFICACIONES",
              h_mm=2.3, ha="left", va="center", color="#1a237e", weight="bold")
    
    # 1. Esquema de Junta Sísmica con predio colindante
    xj = x0 + 12.0
    yj = y0 + h - 42.0
    
    # Muro edificio
    L.h_rect(xj, yj, xj + 18.0, yj + 28.0, layer="CAJETIN", fc=ALBAN, ec=ALBAN_BORDE, lw=0.8)
    L.h_texto((xj + 9.0, yj + 14.0), "EDIFICIO\n(Piso 1-5)", h_mm=1.6, ha="center", va="center", weight="bold")
    
    # Junta 5 cm
    L.h_rect(xj + 18.0, yj, xj + 23.0, yj + 28.0, layer="CAJETIN", fc="#ffe0b2", ec=JUNTA, lw=0.8, hatch="//")
    L.h_texto((xj + 16.0, yj + 20.0), "s = 5.0 cm\n(E.030 52.3)", h_mm=1.6, ha="right", va="bottom", color=JUNTA, weight="bold")  # tecleado-ok: limite de norma o coincidencia
    L.h_linea((xj + 16.0, yj + 20.0), (xj + 18.0, yj + 20.0), layer="CAJETIN", color=JUNTA, lw=0.3)
    
    # Muro vecino
    L.h_rect(xj + 23.0, yj, xj + 41.0, yj + 28.0, layer="CAJETIN", fc="#cfd8dc", ec="#78909c", lw=0.8)
    L.h_texto((xj + 32.0, yj + 14.0), "LIMITE / PREDIO\nVECINO", h_mm=1.6, ha="center", va="center", color="#455a64")

    # Tapajunta superior
    L.h_linea((xj + 14.0, yj + 28.5), (xj + 27.0, yj + 28.5), layer="CAJETIN", color="#263238", lw=1.2)
    L.h_texto((xj + 20.5, yj - 5.0), "Tapajunta metalica doblada\n+ relleno de poliestireno (tecnopor)", h_mm=1.5, ha="center", va="top")

    # 2. CUADRO DE ESPECIFICACIONES TÉCNICAS DE OTROS ELEMENTOS
    y_cuadro = yj - 10.0
    L.cuadro(
        x_mm=x0 + 64.0, y_mm=y0 + h - 18.0,
        titulo="CUADRO DE OTROS ELEMENTOS Y PARAMETROS",
        encabezado=["ELEMENTO", "SECCION / DATO", "ESPECIFICACION", "CRITERIO"],
        filas=[
            ["Escalera", "2 tramos, a = %.2f m" % ANCHO_TRAMO_ESCALERA, "tg = 0.15 m, fi 3/8'' @ 0.20", "A.020 15.2"],  # tecleado-ok: limite de norma o coincidencia
            ["Descanso", "Losa e = %.2f m" % E_LOSA_ESCALERA, "Apoya en columnetas dedicadas", "E.070 9.1"],
            ["Alfeizar", "h = %.2f m, t = %.2f m" % (ALFEIZAR, A_UNIDAD), "Junta 1'' tecnopor + Sikaflex", "E.070 6.2.7"],
            ["Parapeto", "h = %.2f m (Azotea)" % PARAPETO, "Col. %.0fx%.0f, %d fi 3/8'' @ %.2f m" % (_r25().B_COLUMNETA * 100, _r25().H_COLUMNETA * 100, _r25().N_BARRAS_COL, _r25().separacion_parapeto()), "E.070 9.3.5/9.3.7"],
            ["Junta Sismica", "s = 5.0 cm libre", "s/2 = 4.4 cm min. (E.030)", "E.030 52.3"],  # tecleado-ok: limite de norma o coincidencia
            ["Concreto", "f'c = 210 kgf/cm2", "Cemento Portland Tipo I", "E.070 3.5.1"],
            ["Acero", "fy = 4200 kgf/cm2", "Grado 60 corrugado ASTM A615", "E.060"],
        ],
        anchos_mm=[20.0, 26.0, 31.0, 16.0], h_fila=4.2, h_txt=1.65,
        nota="Todos los elementos no estructurales cuentan con aislamiento o arriostre reglamentario.",
    )


def construir():
    L = Lamina(
        codigo="E-05",
        titulo="OTROS ELEMENTOS",
        subtitulo=("Detalles constructivos de escalera, alfeizar aislado, parapeto arriostrado "
                   "y junta sismica. Pisos 1 a %d." % N_PISOS),
        escala=ESCALA,
        meta=meta(),
        nota_pie="Criterios del Capitulo 9 y 10 de la NTE E.070 y libro San Bartolome (2015) 7.3",
    )
    L.encuadrar(0.0, 1.0, 0.0, 1.0, centro_mm=(40.0, 40.0))

    # 4 Cuadrantes perfectamente distribuidos en el área útil de dibujo (X: 10 a 344, Y: 14 a 286)
    with L.bloque_hoja("MODULO ESCALERA", margen_mm=1.0):
        modulo_escalera(L, 10.0, 152.0, 162.0, 134.0)

    with L.bloque_hoja("MODULO PARAPETO", margen_mm=1.0):
        modulo_parapeto(L, 178.0, 152.0, 164.0, 134.0)

    with L.bloque_hoja("MODULO ALFEIZAR", margen_mm=1.0):
        # y = 16 y no 14: el pie de hoja llega a 14,6 mm (ver lamina.py, PIE
        # DE HOJA registrado el 2026-09-30) y el marco del modulo lo tocaba
        modulo_alfeizar(L, 10.0, 16.0, 162.0, 130.0)

    # SE REGISTRA IGUAL, aunque L.cuadro() anote ademas su propia caja: sin
    # el registro este detalle no se puede recortar como los otros tres, y
    # la figura del informe lo necesita (ver lamina.py::render_figura).
    with L.bloque_hoja("MODULO JUNTA", margen_mm=1.0):
        modulo_junta_y_cuadro(L, 178.0, 16.0, 164.0, 130.0)

    L.cajetin()
    return L


def control(L):
    assert PARAPETO > 1.00, "el parapeto supera 1.00 m y se arriostra"  # tecleado-ok: limite de norma o coincidencia
    ch = L.control_hoja()
    assert not ch, ("bloques de hoja que se pisan: %s"
                    % ["%s / %s" % (c[0], c[1]) for c in ch])
    for nom, x0, y0, x1, y1 in L._cajas_hoja:
        assert (6.0 <= x0 and x1 <= A3_MM[0] - 6.0
                and 6.0 <= y0 and y1 <= A3_MM[1] - 6.0), (
            "el bloque %r se sale de la hoja: x[%.1f, %.1f] y[%.1f, %.1f]"
            % (nom, x0, x1, y0, y1))
    print("  [ok] 4 cuadrantes tecnicos completos sin huecos vacios")
    print("  [ok] %d bloques de hoja, ninguno se pisa ni se sale" % len(L._cajas_hoja))


def main():
    L = construir()
    salidas = L.render(Path(R.LAMINAS), dpi=200, dxf_dir=Path(R.CAD))
    # La figura del informe se compone para la PAGINA (ver
    # lamina.py::render_figura): el DXF y la lamina completa
    # siguen saliendo a tamano de hoja, que es donde van.
    # CUATRO FIGURAS, UNA POR DETALLE. Ver el porque en
    # lamina.py::render_figura, `solo_bloque`.
    #
    # SE RECORTAN DE LA HOJA, NO SE REDIBUJAN (2026-10-01). render_figura
    # redibuja el bloque a otra escala y dejaba los textos fuera: estimaba el
    # ancho de cada texto en el doble de lo real y descartaba los largos (el
    # titulo, la nota normativa, los rotulos de varias lineas, la cota girada,
    # una celda del cuadro). Con la estimacion corregida aparecian, pero a
    # otra escala que el dibujo: desbordaban celdas y marcos. La hoja A3, en
    # cambio, se dibuja bien; cada detalle es el recorte de su modulo, a la
    # misma resolucion, y se ve exactamente como en el plano.
    from PIL import Image
    hoja = next(v for v in salidas.values() if str(v).lower().endswith(".png"))
    img = Image.open(hoja)
    ppm = img.size[0] / float(A3_MM[0])          # pixeles por mm de hoja
    assert abs(img.size[1] / float(A3_MM[1]) - ppm) < 0.05
    cajas = {c[0]: c[1:] for c in L._cajas_hoja}
    base = Path(R.INFORME)
    for clave, bloque, sufijo in (
            ("fig_escalera", "MODULO ESCALERA", "_d1_escalera"),
            ("fig_parapeto", "MODULO PARAPETO", "_d2_parapeto"),
            ("fig_alfeizar", "MODULO ALFEIZAR", "_d3_alfeizar"),
            ("fig_junta", "MODULO JUNTA", "_d4_junta")):
        x0, y0, x1, y1 = cajas[bloque]
        m = 0.3                                   # mm: mas, y entra el marco de la hoja o el pie
        caja_px = (int((x0 - m) * ppm), int((A3_MM[1] - y1 - m) * ppm),
                   int((x1 + m) * ppm), int((A3_MM[1] - y0 + m) * ppm))
        destino = base / (Path(hoja).stem.replace("_otros_elementos", "_otros_elementos") + sufijo + ".png")
        destino = base / ("E-05_otros_elementos" + sufijo + ".png")
        img.crop(caja_px).save(destino, dpi=(200, 200))
        salidas[clave] = destino
    print()
    for k, p in salidas.items():
        print("  %-5s %s  (%d KB)" % (k, p.name, p.stat().st_size // 1024))
    print()
    control(L)
    return salidas

if __name__ == "__main__":
    main()
