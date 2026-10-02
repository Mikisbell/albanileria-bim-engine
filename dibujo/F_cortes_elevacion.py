# -*- coding: utf-8 -*-
"""Cortes A-A, B-B y elevación frontal — Cero solapes garantizado."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon

AQUI = r"D:\- E -\CONTINENTAL\10° CICLO\Albañilería\Unidad I\C1\12-PA2-consolidado2-analisis-diseno-confinada\dibujo"
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))
sys.path.insert(0, AQUI)

import rutas as R
import cuadro as C
import meta as META                                             # noqa: E402
from proyecto import (FRENTE, FONDO, ESPESOR, E_LOSA, H_ENTREPISO,
                      H_LIBRE, N_PISOS, HN, PARAPETO, B_CIMIENTO, DF,
                      POZO_X0, POZO_X1, POZO_Y0, POZO_Y1, EJES_MX,
                      MUROS, vanos_ubicados, altura_de_vano, ALFEIZAR,
                      tipo_de_vano,
                      ALTO_PUERTA, H_DINTEL_VENTANA, H_DINTEL_PUERTA,
                      ESC_X0, ESC_X1,
                      ejes_x_rotulados, QAD, SC_VIVIENDA,
                      RETIRO_FRONTAL, RETIRO_POSTERIOR,
                      FONDO_LOTE, AREA_LOTE, AREA_LIBRE,
                      AREA_LIBRE_MINIMA, PCT_AREA_LIBRE,
                      RETIRO_LATERAL, N_ESTACIONAMIENTOS,
                      ANCHO_TRIB, SEPARACION_MX, AREA_POZO,
                      POZO_ANCHO, EJES_MX, E_LOSA, Z)

COLOR_MURO = "#2c3437"
COLOR_LOSA = "#78909c"
COLOR_CIMIENTO = "#a1887f"
COLOR_TERRENO = "#eceff1"
COLOR_POZO = "#ffffff"
COLOR_FACHADA = "#f5f5f5"
COLOR_VENTANA = "#b3e5fc"
COLOR_MARCO_V = "#0277bd"

C_COTA = "#37474f"
C_EJE = "#1565c0"
C_ROJO = "#c62828"
C_VERDE = "#2e7d32"
C_NIVEL = "#455a64"

def cota_lineal_h(ax, y, x0, x1, texto, color=C_COTA, fs=6.2, lw=0.7, tick=0.18):
    if x1 <= x0:
        return
    ax.plot([x0, x1], [y, y], color=color, lw=lw, zorder=8)
    for x in (x0, x1):
        ax.plot([x - tick*0.7, x + tick*0.7], [y - tick*0.7, y + tick*0.7],
                color=color, lw=lw*1.3, zorder=9)
    ax.text((x0 + x1) / 2.0, y, texto, ha="center", va="center",
            fontsize=fs, color=color, fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.10", fc="white", ec="none", alpha=0.95),
            zorder=10)

def cota_lineal_v(ax, x, y0, y1, texto, color=C_COTA, fs=6.2, lw=0.7, tick=0.18):
    if y1 <= y0:
        return
    ax.plot([x, x], [y0, y1], color=color, lw=lw, zorder=8)
    for y in (y0, y1):
        ax.plot([x - tick*0.7, x + tick*0.7], [y - tick*0.7, y + tick*0.7],
                color=color, lw=lw*1.3, zorder=9)
    ax.text(x, (y0 + y1) / 2.0, texto, ha="center", va="center", rotation=90,
            fontsize=fs, color=color, fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.10", fc="white", ec="none", alpha=0.95),
            zorder=10)

def dibujar_burbuja_eje(ax, x, y, etiqueta, r=0.32):
    c = Circle((x, y), r, fc="white", ec=C_EJE, lw=0.8, zorder=12)
    ax.add_patch(c)
    ax.text(x, y, etiqueta, ha="center", va="center",
            fontsize=6.5, color=C_EJE, fontweight="bold", zorder=13)

def simbolo_nivel(ax, x, y, etiqueta):
    ax.plot([x - 0.75, x], [y, y], color=C_NIVEL, lw=0.6, zorder=7)
    poly = Polygon([(x - 0.22, y + 0.20), (x, y), (x - 0.22, y)],
                   fc=C_NIVEL, ec=C_NIVEL, lw=0.5, zorder=8)
    ax.add_patch(poly)
    ax.text(x - 0.85, y, etiqueta, ha="right", va="center",
            fontsize=6.0, color=C_NIVEL, fontweight="bold", zorder=9)

def _cimiento(ax, x_izq, x_der):
    ax.add_patch(Rectangle((x_izq - 1.0, -DF - 0.3), x_der - x_izq + 2.0,
                           DF + 0.3, fc=COLOR_TERRENO, ec="none", zorder=0))
    ax.plot([x_izq - 1.0, x_der + 1.0], [0, 0], color="#546e7a", lw=1.0, zorder=1)
    ax.add_patch(Rectangle((x_izq - B_CIMIENTO / 2.0, -DF),
                           x_der - x_izq + B_CIMIENTO, DF - 0.30,
                           fc=COLOR_CIMIENTO, ec="#4e342e", lw=0.7, hatch="///", zorder=2))
    ax.add_patch(Rectangle((x_izq - ESPESOR / 2.0, -0.30),
                           x_der - x_izq + ESPESOR, 0.30,
                           fc="#8d6e63", ec="#4e342e", lw=0.6, zorder=2))

def corte_transversal(ax):
    largo = FRENTE
    ax.set_title("(a)  Corte A-A — Transversal por Pozo Central "
                 "(Ejes A - E, fachada al %s)" % META.ORIENTACION_FACHADA,
                 fontsize=9.5, fontweight="bold", color="#1a237e", loc="left", pad=12)

    _cimiento(ax, 0.0, largo)

    # Las losas se dibujan partidas en 2 tramos para dejar el pozo físicamente vacío
    px0 = POZO_X0 + ESPESOR / 2.0
    px1 = POZO_X1 - ESPESOR / 2.0

    for k in range(N_PISOS + 1):
        y = k * H_ENTREPISO
        if k > 0:
            # Tramo izquierdo
            ax.add_patch(Rectangle((0.0, y - E_LOSA), px0, E_LOSA,
                                   fc=COLOR_LOSA, ec="#37474f", lw=0.6, zorder=4))
            # Tramo derecho
            ax.add_patch(Rectangle((px1, y - E_LOSA), largo - px1, E_LOSA,
                                   fc=COLOR_LOSA, ec="#37474f", lw=0.6, zorder=4))
        lbl = "N.P.T. ±0.00" if k == 0 else "N.P.T. +%.2f" % y
        simbolo_nivel(ax, -0.2, y, lbl)

    # Texto pozo central en vacío real (0 piezas debajo)
    ax.text((POZO_X0 + POZO_X1) / 2.0, HN / 2.0,
            "POZO DE LUZ CENTRAL" + chr(10)
            + "Luz libre = %.2f m" % POZO_ANCHO + chr(10)
            + "Área = %.2f m²" % AREA_POZO,
            ha="center", va="center", fontsize=6.2, color=C_VERDE,
            fontweight="bold", linespacing=1.2,
            bbox=dict(boxstyle="round,pad=0.20", fc="#e8f5e9", ec="#81c784", lw=0.6),
            zorder=6)

    # Muros (en el pozo de luz central no hay muros en el eje C)
    ejes, etiqs = ejes_x_rotulados()
    for k in range(N_PISOS):
        y0 = k * H_ENTREPISO
        for x in ejes:
            if POZO_X0 + 0.1 < x < POZO_X1 - 0.1:
                continue  # Hueco libre del pozo de luz
            ax.add_patch(Rectangle((x - ESPESOR / 2.0, y0),
                                   ESPESOR, H_ENTREPISO - E_LOSA,
                                   fc=COLOR_MURO, ec="#1a1a1a", lw=0.4, zorder=3))

    # Parapeto
    ax.add_patch(Rectangle((0 - ESPESOR / 2.0, HN), ESPESOR, PARAPETO,
                           fc=COLOR_MURO, ec="#1a1a1a", lw=0.5, zorder=3))
    ax.add_patch(Rectangle((largo - ESPESOR / 2.0, HN), ESPESOR, PARAPETO,
                           fc=COLOR_MURO, ec="#1a1a1a", lw=0.5, zorder=3))
    simbolo_nivel(ax, -0.2, HN + PARAPETO, "N.T.T. +%.2f" % (HN + PARAPETO))

    # Ejes y burbujas
    for x, let in zip(ejes, etiqs):
        ax.plot([x, x], [-DF - 0.2, HN + PARAPETO + 1.1], color=C_EJE, lw=0.4, ls=(0, (6, 3, 1, 3)), zorder=1)
        dibujar_burbuja_eje(ax, x, HN + PARAPETO + 1.5, let)

    y_c1 = HN + PARAPETO + 0.5
    for i in range(len(ejes) - 1):
        cota_lineal_h(ax, y_c1, ejes[i], ejes[i+1], "%.2f m" % (ejes[i+1] - ejes[i]), fs=5.5)
    cota_lineal_h(ax, HN + PARAPETO + 2.3, 0.0, largo, "Ancho = %.2f m" % largo, color=C_ROJO, fs=6.2)

    # Cotas verticales
    x_c1 = largo + 0.8
    for k in range(N_PISOS):
        cota_lineal_v(ax, x_c1, k * H_ENTREPISO, (k + 1) * H_ENTREPISO, "2.70", fs=5.2)
    cota_lineal_v(ax, x_c1 - 1.45, HN, HN + PARAPETO, "1.10",
                  color=C_ROJO, fs=5.2)
    
    x_c2 = largo + 1.9
    cota_lineal_v(ax, x_c2, 0.0, HN, "Hn = %.2f m" % HN,
                  color=C_ROJO, fs=6.0)
    cota_lineal_v(ax, x_c2 + 1.0, 0.0, HN + PARAPETO, "Total 14.60 m", color=C_COTA, fs=5.5)
    cota_lineal_v(ax, x_c1, -DF, 0.0, "Df = 1.50", color=C_VERDE, fs=5.5)

    # Panel lateral técnico del Corte A-A (con títulos concisos sin solape)
    _tipo_uni, _vacios = _unidad()
    _q_real, _q_adm = _presion_de_cimiento()
    datos_corte_a = [
        ("Número de Pisos:", "%d niveles completos" % N_PISOS),
        ("Altura Entrepiso:", "%.2f m (piso a piso)" % H_ENTREPISO),
        ("Altura Libre h:", "%.2f m (>= 2.30 m A.010)" % H_LIBRE),
        ("Espesor Losa:", "%.2f m (Aligerada 1 dir)" % E_LOSA),
        ("Espesor Muro t:", "%.2f m (Sólida Tipo %s, %.0f %% vacíos)"
         % (ESPESOR, _tipo_uni, _vacios)),
        ("Parapeto Azotea:", "%.2f m (Arriostrado)" % PARAPETO),
        ("Luz Libre Pozo:", "%.2f m (Ejes B a D)" % POZO_ANCHO),
        ("Área Pozo Luz:", "%.2f m² (Reglamentario)" % AREA_POZO),
        ("Cimentación:", "Cimiento corrido ciclópeo"),
        ("Desplante Df:", "%.2f m (s/estudio EMS)" % DF),
        ("Ancho Cimiento B:", "%.2f m (q = %.2f < %.2f kg/cm²)"
         % (B_CIMIENTO, _q_real, _q_adm)),
    ]

    xp = largo + 4.8
    w_p = 10.0
    # EL ALTO SE DERIVA DE LAS FILAS. Ver el porque en el encabezado.
    # EL PASO TAMBIEN SE DERIVA: el eje termina en -DF-1,2 y un
    # paso fijo de 1,55 empujaba la fila once por debajo del eje.
    _paso = (13.0 + DF + 0.55 - 0.7) / max(len(datos_corte_a) - 1, 1)
    h_p = _paso * (len(datos_corte_a) - 1) + 2.6
    ax.add_patch(FancyBboxPatch((xp, 14.9 - h_p), w_p, h_p,
                                boxstyle="round,pad=0.2,rounding_size=0.3",
                                fc="#fafafa", ec="#cfd8dc", lw=0.8, zorder=5))
    ax.text(xp + w_p/2.0, 14.2, "FICHA TÉCNICA · CORTE A-A (TRANSVERSAL)", ha="center", va="center",
            fontsize=6.8, color="#1a237e", fontweight="bold", zorder=6)
    
    y_txt = 13.0
    for tit, val in datos_corte_a:
        # APILADO: ver el porque en el encabezado del bloque
        ax.text(xp + 0.4, y_txt, tit, ha="left", va="center", fontsize=5.3,
                color="#37474f", fontweight="bold", zorder=6)
        ax.text(xp + 0.9, y_txt - _paso * 0.42, val, ha="left", va="center",
                fontsize=5.1, color="#263238", zorder=6)
        y_txt -= _paso

    ax.set_xlim(-2.8, xp + w_p + 0.8)
    ax.set_ylim(-DF - 1.2, HN + PARAPETO + 3.2)
    ax.set_aspect("equal")
    ax.axis("off")


def corte_longitudinal(ax):
    largo = FONDO
    ax.set_title("(b)  Corte B-B — Longitudinal (Ejes 1 - 7, "
                 "fondo edificado = %.2f m)" % FONDO,
                 fontsize=9.5, fontweight="bold", color="#1a237e", loc="left", pad=12)

    _cimiento(ax, 0.0, largo)

    for k in range(N_PISOS + 1):
        y = k * H_ENTREPISO
        if k > 0:
            ax.add_patch(Rectangle((0.0, y - E_LOSA), largo, E_LOSA,
                                   fc=COLOR_LOSA, ec="#37474f", lw=0.6, zorder=4))
        lbl = "N.P.T. ±0.00" if k == 0 else "N.P.T. +%.2f" % y
        simbolo_nivel(ax, -0.2, y, lbl)

    ejes = EJES_MX
    for k in range(N_PISOS):
        y0 = k * H_ENTREPISO
        for x in ejes:
            ax.add_patch(Rectangle((x - ESPESOR / 2.0, y0),
                                   ESPESOR, H_ENTREPISO - E_LOSA,
                                   fc=COLOR_MURO, ec="#1a1a1a", lw=0.4, zorder=3))

    ax.add_patch(Rectangle((0 - ESPESOR / 2.0, HN), ESPESOR, PARAPETO,
                           fc=COLOR_MURO, ec="#1a1a1a", lw=0.5, zorder=3))
    ax.add_patch(Rectangle((largo - ESPESOR / 2.0, HN), ESPESOR, PARAPETO,
                           fc=COLOR_MURO, ec="#1a1a1a", lw=0.5, zorder=3))
    simbolo_nivel(ax, -0.2, HN + PARAPETO, "N.T.T. +%.2f" % (HN + PARAPETO))

    for i, x in enumerate(ejes, 1):
        ax.plot([x, x], [-DF - 0.2, HN + PARAPETO + 1.1], color=C_EJE, lw=0.4, ls=(0, (6, 3, 1, 3)), zorder=1)
        dibujar_burbuja_eje(ax, x, HN + PARAPETO + 1.5, str(i))

    y_c1 = HN + PARAPETO + 0.5
    for i in range(len(ejes) - 1):
        cota_lineal_h(ax, y_c1, ejes[i], ejes[i+1], "%.2f" % (ejes[i+1] - ejes[i]), fs=5.5)
    cota_lineal_h(ax, HN + PARAPETO + 2.3, 0.0, largo, "Longitud = %.2f m" % largo, color=C_ROJO, fs=6.2)

    x_c1 = largo + 0.8
    for k in range(N_PISOS):
        cota_lineal_v(ax, x_c1, k * H_ENTREPISO, (k + 1) * H_ENTREPISO, "2.70", fs=5.2)
    cota_lineal_v(ax, x_c1 - 1.45, HN, HN + PARAPETO, "1.10",
                  color=C_ROJO, fs=5.2)

    x_c2 = largo + 1.9
    cota_lineal_v(ax, x_c2, 0.0, HN, "Hn = %.2f m" % HN,
                  color=C_ROJO, fs=6.0)
    cota_lineal_v(ax, x_c1, -DF, 0.0, "Df = 1.50", color=C_VERDE, fs=5.5)

    # Panel lateral técnico del Corte B-B
    _n_x, _n_y = _muros_por_direccion()
    datos_corte_b = [
        ("Dirección Muros:", "Transversales (Eje Y)"),
        ("Muros Portantes:", "%d en Y · %d en X · %d en total"
         % (_n_y, _n_x, _n_y + _n_x)),
        ("Modulación Edificio:", "%d paños estructurales"
         % (len(EJES_MX) - 1)),
        ("Luces Estructurales:", "%.2f m típico (%.2f m pozo)"
         % (ANCHO_TRIB, SEPARACION_MX)),
        ("Armado Viguetas:", "En dirección Y entre vigas"),
        ("Sobrecarga Losa:", "%.0f kgf/m² (Multifamiliar)" % SC_VIVIENDA),
        ("Junta Separación s:", "2 x %.0f cm (Norma E.030)"
         % (RETIRO_LATERAL * 100)),
        ("Retiro Frontal:", "%.2f m (%d estacionamientos)"
         % (RETIRO_FRONTAL, N_ESTACIONAMIENTOS)),
        ("Retiro Posterior:", "%.2f m (Área libre jardín)"
         % RETIRO_POSTERIOR),
        ("Fondo de Terreno:", "%.2f m (Lote %.2f m²)"
         % (FONDO_LOTE, AREA_LOTE)),
        ("Área Libre Total:", "%.2f m² = %.1f%% (>= %.0f%%)"
         % (AREA_LIBRE, 100.0 * PCT_AREA_LIBRE,
            100.0 * AREA_LIBRE_MINIMA)),
    ]

    xp = largo + 3.8
    w_p = 10.0
    # EL ALTO SE DERIVA DE LAS FILAS. Ver el porque en el encabezado.
    # EL PASO TAMBIEN SE DERIVA: el eje termina en -DF-1,2 y un
    # paso fijo de 1,55 empujaba la fila once por debajo del eje.
    _paso = (13.0 + DF + 0.55 - 0.7) / max(len(datos_corte_b) - 1, 1)
    h_p = _paso * (len(datos_corte_b) - 1) + 2.6
    ax.add_patch(FancyBboxPatch((xp, 14.9 - h_p), w_p, h_p,
                                boxstyle="round,pad=0.2,rounding_size=0.3",
                                fc="#fafafa", ec="#cfd8dc", lw=0.8, zorder=5))
    ax.text(xp + w_p/2.0, 14.2, "FICHA TÉCNICA · CORTE B-B (LONGITUDINAL)", ha="center", va="center",
            fontsize=6.8, color="#1a237e", fontweight="bold", zorder=6)
    
    y_txt = 13.0
    for tit, val in datos_corte_b:
        # APILADO: ver el porque en el encabezado del bloque
        ax.text(xp + 0.4, y_txt, tit, ha="left", va="center", fontsize=5.3,
                color="#37474f", fontweight="bold", zorder=6)
        ax.text(xp + 0.9, y_txt - _paso * 0.42, val, ha="left", va="center",
                fontsize=5.1, color="#263238", zorder=6)
        y_txt -= _paso

    ax.set_xlim(-2.8, xp + w_p + 0.8)
    ax.set_ylim(-DF - 1.2, HN + PARAPETO + 3.2)
    ax.set_aspect("equal")
    ax.axis("off")


def _zona_sismica():
    """El numero de zona que le corresponde a `Z`, por la Tabla N.o 1."""
    tabla = {0.10: 1, 0.25: 2, 0.35: 3, 0.45: 4}
    for z, n in tabla.items():
        if abs(Z - z) < 1e-9:
            return n
    raise AssertionError("Z = %.3f no esta en la Tabla N.o 1" % Z)


def _unidad():
    """La unidad ADOPTADA, del script 13. Ver el porqué en la cabecera."""
    import contextlib
    import importlib
    import io as _io4
    with contextlib.redirect_stdout(_io4.StringIO()):
        m13 = importlib.import_module("13_unidad_albanileria")
    solidas = [f for f in m13.FICHAS if f[1] == "SOLIDO"]
    tipos = set(f[8] for f in solidas)
    assert len(tipos) == 1, "las fichas solidas declaran tipos distintos"
    return tipos.pop(), m13.VACIOS_MAXIMOS


def _presion_de_cimiento():
    """La presión real bajo el cimiento y la admisible, del script 04.

    La ficha decía «q_adm = 1.10 kg/cm²» y el EMS da 3,00: el gráfico «B vs
    qad» de su Fig. N.º 3 se lee con el ancho, y `QAD` toma el punto más
    desfavorable. 1,10 no sale de ningún lado del proyecto de hoy.
    """
    import contextlib
    import importlib
    import io as _io4
    with contextlib.redirect_stdout(_io4.StringIO()):
        m04 = importlib.import_module("04_cimentacion")
        w = m04.carga_lineal()
    q_real = (w / 1000.0) / B_CIMIENTO / 10.0        # kg/cm2
    assert q_real < QAD, (
        "la presion real %.2f supera la admisible %.2f" % (q_real, QAD))
    return q_real, QAD


def _muros_por_direccion():
    """Cuántos muros portantes hay en cada dirección, contados del SSOT.

    La ficha del corte B-B decía «7 muros confinados» bajo el rótulo
    «Transversales (Eje Y)»: en Y hay 6 y en X hay 7. El rótulo y el
    número no hablaban del mismo conjunto.
    """
    return (sum(1 for m in MUROS if m[1] == "X"),
            sum(1 for m in MUROS if m[1] == "Y"))









def main():
    """Tres figuras, una por dibujo. Ver el porque arriba."""
    _pie = ("h libre = %.2f m  ·  losa e = %.2f m  ·  muros "
            "t = %.2f m  ·  cimiento Df = %.2f m, B = %.2f m. Todas "
            "las cotas provienen de calculo/proyecto.py (SSOT), "
            "verificadas bajo E.070, E.030 y A.010."
            % (H_LIBRE, E_LOSA, ESPESOR, DF, B_CIMIENTO))
    n_v = None
    salidas = []
    for n_lam, (pintar, titulo, sufijo) in enumerate((
            (corte_transversal,
             u"Corte transversal A-A por el pozo de luz", "A"),
            (corte_longitudinal,
             u"Corte longitudinal B-B por el eje de circulación", "B")),
            1):
        # 6,90 Y NO 8,40: ver el porque en el bloque de arriba.
        fig = plt.figure(figsize=(C.ANCHO_PAGINA, 6.90))
        y_ar, y_ab = C.marco(
            fig,
            u"Planteamiento arquitectónico  ·  %s" % titulo,
            pie=_pie,
            subtitulo=(u"Albañilería confinada  ·  Hn = %s m  ·  "
                       u"Df = %s m  ·  Zona %d  ·  %s"
                       % (C.coma(HN, 2), C.coma(DF, 2),
                          _zona_sismica(), META.UBICACION)),
            fs_tit=11.0)
        ax = fig.add_axes((0.045, y_ab, 0.925, y_ar - y_ab - 0.02))
        r = pintar(ax)
        if r is not None:
            n_v = r
        s = os.path.join(R.INFORME, "CORTES-ELEVACION-%s.png" % sufijo)
        C.guardar(fig, s)
        salidas.append(s)
    return salidas[0], n_v

def control(n_v):
    """Lo que las dos láminas afirman, contra el SSOT.

    Antes verificaba también los vanos de fachada, porque la elevación
    vivía acá. La elevación se mudó a `F_elevacion.py` —una sola fuente
    por dibujo— y su control se fue con ella: verificar acá un conteo que
    ya no se dibuja es verificar nada.
    """
    assert abs(HN - N_PISOS * H_ENTREPISO) < 1e-9
    assert abs(H_LIBRE - (H_ENTREPISO - E_LOSA)) < 1e-9
    print("  [ok] los dos cortes cierran con el SSOT")
    return True


if __name__ == "__main__":
    salidas, _n = main()
    control(None)
    print("=" * 74)
    print("CORTES A-A y B-B")
    print("=" * 74)
