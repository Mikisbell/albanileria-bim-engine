# -*- coding: utf-8 -*-
"""Figuras de IDEALIZACION para los metrados. Criterios 3 y 4.

QUE CIERRA ESTE SCRIPT
======================
La rubrica no pide "metrar": pide **IDEALIZAR y metrar**. La palabra aparece en
los dos niveles altos de ambos criterios:

    2,0  "IDEALIZA y realiza el metrado de todas las losas / de todos los
          muros portantes, considera el efecto de todas las solicitaciones"
    1,5  "IDEALIZA las losas y realiza sus metrado de cargas incompleto"
    1,0  "Realiza un metrado de cargas deficiente"   <- sin idealizar

O sea que la idealizacion esta en el 2,0 Y en el 1,5, y desaparece recien en el
1,0. Sin estas figuras el techo de cada criterio es 1,00 de sus 2,00 puntos,
por mas correcto que sea el metrado.

QUE ES IDEALIZAR, Y POR QUE NO ES UN DIBUJO BONITO
==================================================
Idealizar es declarar **que modelo se metra**: donde se supone que apoya cada
elemento, que ancho de losa carga sobre cada muro, y que se desprecia. Un
metrado sin idealizacion declarada no se puede auditar, porque no se sabe
contra que geometria comparar sus numeros.

Las dos figuras responden una pregunta cada una:
  C3  -  la losa: .como se reparte el peso de la losa entre sus apoyos?
  C4  -  el muro: .que porcion de esa losa termina bajando por cada muro?
"""
import rutas as R
import cuadro as C                                             # noqa: E402
import importlib.util
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow

AQUI = os.path.dirname(os.path.abspath(__file__))
CALCULO = os.path.join(AQUI, "..", "calculo")
sys.path.insert(0, CALCULO)

from proyecto import (PANOS_Y, EJES_MX, FRENTE, FONDO, E_LOSA, ESPESOR,
                      POZO_X0, POZO_X1, POZO_Y0, POZO_Y1, tributaria_mx,
                      LOSA_ALIGERADA, PISO_TERMINADO, TABIQUERIA, SC_VIVIENDA,
                      N_PISOS, HN, MUROS)

SEP_VIGUETAS = 0.40      # no-ssot: m entre ejes
B_ALMA = 0.10            # no-ssot: m, ancho del alma
E_LOSA_SUP = 0.05        # no-ssot: m, losa superior

AZUL = "#2471a3"
ROJO = "#c0392b"
GRIS = "#7f8c8d"
CREMA = "#fdebd0"


# ------------------------------------------------------------ figura C3

def figura_losa(salida):
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 8.30))
    fig.suptitle(u"Idealizaci\u00f3n de la losa aligerada  \u00b7  criterio 3",
                 fontsize=14, fontweight="bold", wrap=True)

    # --- (a) seccion transversal del aligerado
    ax = fig.add_subplot(2, 2, 1)
    ax.set_title(u"(a) Secci\u00f3n transversal: la vigueta T", fontsize=11)
    n = 3
    for k in range(n):
        x0 = k * SEP_VIGUETAS
        # ladrillo de techo
        ax.add_patch(Rectangle((x0 + B_ALMA, 0), SEP_VIGUETAS - B_ALMA,
                               E_LOSA - E_LOSA_SUP, facecolor=CREMA,
                               edgecolor=GRIS, hatch="//"))
        # alma de la vigueta
        ax.add_patch(Rectangle((x0, 0), B_ALMA, E_LOSA - E_LOSA_SUP,
                               facecolor="#d5d8dc", edgecolor="k"))
    # losa superior corrida
    ax.add_patch(Rectangle((0, E_LOSA - E_LOSA_SUP), n * SEP_VIGUETAS,
                           E_LOSA_SUP, facecolor="#d5d8dc", edgecolor="k"))
    # cotas
    ax.annotate("", xy=(0, -0.045), xytext=(SEP_VIGUETAS, -0.045),
                arrowprops=dict(arrowstyle="<->", color=ROJO))
    ax.text(SEP_VIGUETAS / 2, -0.075, "%.2f m" % SEP_VIGUETAS, ha="center",
            color=ROJO, fontsize=9)
    ax.annotate("", xy=(n * SEP_VIGUETAS + 0.05, 0),
                xytext=(n * SEP_VIGUETAS + 0.05, E_LOSA),
                arrowprops=dict(arrowstyle="<->", color=ROJO))
    ax.text(n * SEP_VIGUETAS + 0.09, E_LOSA / 2, "h = %.2f" % E_LOSA,
            va="center", color=ROJO, fontsize=9)
    ax.text(B_ALMA / 2, 0.055, "%.2f m" % B_ALMA, ha="center",
            va="bottom", fontsize=7.2, color="#455a64")
    ax.set_xlim(-0.12, n * SEP_VIGUETAS + 0.30)
    # el limite inferior deja sitio para la nota; antes la nota iba ARRIBA y
    # se pisaba con el titulo del panel, defecto que solo se vio al mirar la
    # figura, no al correr el script.
    ax.set_ylim(-0.30, E_LOSA + 0.04)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(0, -0.52,
            "Se metra por METRO CUADRADO (%d kgf/m2, E.020 Anexo 1),\n"
            "no vigueta por vigueta." % LOSA_ALIGERADA, fontsize=7.8,
            va="top")

    # --- (b) la vigueta como viga continua
    ax = fig.add_subplot(2, 2, 2)
    ax.set_title("(b) La vigueta idealizada: viga continua de 6 tramos", fontsize=11)
    y0 = 0
    for i, y in enumerate(EJES_MX):
        ax.plot([y, y], [y0 - 0.16, y0], color="k", lw=1.4)
        ax.plot([y - 0.12, y + 0.12], [y0 - 0.16, y0 - 0.16], color="k", lw=2.2)
        ax.text(y, y0 - 0.30, "MX-%d" % (i + 1), ha="center", fontsize=7.5)
    ax.plot([0, FONDO], [y0, y0], color=AZUL, lw=3.0)
    for x in [k * 0.5 for k in range(int(FONDO * 2) + 1)]:
        ax.annotate("", xy=(x, y0), xytext=(x, y0 + 0.30),
                    arrowprops=dict(arrowstyle="->", color=ROJO, lw=0.9))
    ax.plot([0, FONDO], [y0 + 0.30, y0 + 0.30], color=ROJO, lw=1.4)
    for i, L in enumerate(PANOS_Y):
        xm = (EJES_MX[i] + EJES_MX[i + 1]) / 2
        cond = "1 ext." if i in (0, len(PANOS_Y) - 1) else "2 ext."
        # ALTERNADOS en dos alturas: seis rotulos seguidos no entran en el
        # ancho de la pagina y se montan de a pares.
        dy = -0.50 if i % 2 == 0 else -0.80
        ax.text(xm, y0 + dy, "%.2f m\n(%s)" % (L, cond),
                ha="center", va="top", fontsize=7.0, color=AZUL,
                linespacing=1.25)
    ax.text(FONDO / 2, y0 + 0.46,
            "w = (%d + %d + %d) + %d = %d kgf/m2"
            % (LOSA_ALIGERADA, PISO_TERMINADO, TABIQUERIA, SC_VIVIENDA,
               LOSA_ALIGERADA + PISO_TERMINADO + TABIQUERIA + SC_VIVIENDA),
            ha="center", color=ROJO, fontsize=9)
    ax.set_xlim(-0.8, FONDO + 0.8)
    ax.set_ylim(-1.40, 0.70)
    ax.axis("off")

    # --- (c) en planta: sentido de las viguetas
    ax = fig.add_subplot(2, 1, 2)
    ax.set_title("(c) En planta: las viguetas apoyan en los muros TRANSVERSALES",
                 fontsize=11)
    # esquema en PLANTA: no lleva ejes numericos, y sus
    # ticks eran los que pisaban el titulo del panel
    ax.set_xticks([])
    ax.set_yticks([])
    ax.add_patch(Rectangle((0, 0), FRENTE, FONDO, facecolor="#f4f6f7",
                           edgecolor="k"))
    ax.add_patch(Rectangle((POZO_X0, POZO_Y0), POZO_X1 - POZO_X0,
                           POZO_Y1 - POZO_Y0, facecolor="w", edgecolor=GRIS,
                           hatch="xx"))
    ax.text((POZO_X0 + POZO_X1) / 2, (POZO_Y0 + POZO_Y1) / 2, "POZO\n(sin losa)",
            ha="center", va="center", fontsize=8, color=GRIS)
    for y in EJES_MX:
        ax.plot([0, FRENTE], [y, y], color="k", lw=2.6)
    x = 0.45
    while x < FRENTE:
        for i in range(len(PANOS_Y)):
            ya, yb = EJES_MX[i] + 0.10, EJES_MX[i + 1] - 0.10
            if POZO_X0 < x < POZO_X1 and POZO_Y0 <= ya and yb <= POZO_Y1:
                continue
            ax.plot([x, x], [ya, yb], color=AZUL, lw=0.7, alpha=0.75)
        x += 0.45
    ax.set_xlim(-0.6, FRENTE + 0.6)
    ax.set_ylim(-0.6, FONDO + 0.6)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.text(FRENTE + 0.8, FONDO / 2,
            "Las viguetas corren en Y y\n"
            u"salvan el pa\u00f1o entre dos MX.\n\n"
            "Por eso los muros LONGITUDINALES\n"
            "(MY) casi no reciben carga de losa:\n"
            "corren PARALELOS a las viguetas.",
            fontsize=9, va="center")
    fig.tight_layout(rect=[0, 0.01, 1, 0.95], h_pad=2.6)
    C.guardar(fig, salida)


# ------------------------------------------------------------ figura C4

def figura_muro(salida):
    filas = tributaria_mx()
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 7.80))
    fig.suptitle(u"Idealizaci\u00f3n del muro portante  \u00b7  criterio 4",
                 fontsize=14, fontweight="bold", wrap=True)

    # --- (a) franjas tributarias en planta
    ax = fig.add_subplot(1, 2, 1)
    ax.set_title("(a) Franja tributaria de cada muro transversal", fontsize=11)
    # esquema en PLANTA: no lleva ejes numericos, y sus
    # ticks eran los que pisaban el titulo del panel
    ax.set_xticks([])
    ax.set_yticks([])
    critico = max(filas, key=lambda f: f[3])
    for nom, y, ancho, area in filas:
        y0, y1 = y - ancho / 2, y + ancho / 2
        es = (nom == critico[0])
        ax.add_patch(Rectangle((0, y0), FRENTE, ancho,
                               facecolor=(ROJO if es else "#d6eaf8"),
                               alpha=0.35 if es else 0.55, edgecolor=GRIS))
        ax.plot([0, FRENTE], [y, y], color="k", lw=2.4)
        ax.text(FRENTE + 0.25, y, "%s\n%.2f m" % (nom.split()[0], ancho),
                va="center", fontsize=8,
                color=(ROJO if es else "k"),
                fontweight=("bold" if es else "normal"))
    ax.add_patch(Rectangle((POZO_X0, POZO_Y0), POZO_X1 - POZO_X0,
                           POZO_Y1 - POZO_Y0, facecolor="w", edgecolor=GRIS,
                           hatch="xx"))
    ax.set_xlim(-0.5, FRENTE + 2.6)
    ax.set_ylim(-0.5, FONDO + 0.5)
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    mas_ancho = max(filas, key=lambda f: f[2])
    # LA NOTA VA AL PIE DE LA FIGURA, no bajo el eje. Dibujada en coordenadas
    # de datos (ax.text en y = -2,1) caia sobre las marcas del eje x, sobre
    # sus numeros y sobre el rotulo "x (m)", y los cinco renglones quedaban
    # ilegibles. Se vio AMPLIANDO el PDF: a tamano de pantalla el PNG parecia
    # sano, porque lo que los encima es la escala a la que Word lo inserta.
    _pie = (u"La franja llega hasta la MITAD del paño a cada lado. "
            u"OJO: el de franja MÁS ANCHA no es el más cargado: "
            u"%s tiene %.2f m de franja y solo %.0f m², porque el pozo "
            u"le quita losa, mientras que %s tiene %.2f m y %.0f m². "
            u"Por eso no se usa un ancho tributario único."
            % (mas_ancho[0].split()[0], mas_ancho[2], mas_ancho[3],
               critico[0].split()[0], critico[2], critico[3]))
    _axp = fig.add_axes((0, 0, 1, 1), frame_on=False)
    _axp.set_axis_off()
    _yp = 0.085
    for _ln in C.envolver(_axp, _pie, 8.2, 0.90):
        fig.text(0.055, _yp, _ln, fontsize=8.2, color="#333", va="top")
        _yp -= 0.0175

    # --- (b) que baja por el muro critico
    ax = fig.add_subplot(1, 2, 2)
    ax.set_title(u"(b) Lo que baja por el muro m\u00e1s cargado (%s)"
                 % critico[0].split()[0], fontsize=11)
    ancho_m = 6.0
    for k in range(N_PISOS):
        yb = k * 2.70
        ax.add_patch(Rectangle((0, yb), ancho_m, 0.20, facecolor="#d5d8dc",
                               edgecolor="k"))
        ax.add_patch(Rectangle((0, yb + 0.20), ancho_m, 2.50,
                               facecolor="#fadbd8", edgecolor=GRIS, alpha=0.5))
        ax.annotate("", xy=(ancho_m / 2, yb + 0.20), xytext=(ancho_m / 2, yb + 0.95),
                    arrowprops=dict(arrowstyle="->", color=ROJO, lw=1.8))
        ax.text(ancho_m / 2 + 0.25, yb + 0.6, "piso %d" % (N_PISOS - k),
                fontsize=8, color=ROJO)
    ax.add_patch(Rectangle((-0.9, -0.7), ancho_m + 1.8, 0.7,
                           facecolor="#d5d8dc", edgecolor="k", hatch="//"))
    ax.text(ancho_m / 2, -0.35, u"cimiento corrido", ha="center", fontsize=8,
            bbox=dict(facecolor="w", edgecolor="none", pad=1.5))
    ax.set_xlim(-1.6, ancho_m + 3.4)
    ax.set_ylim(-1.2, N_PISOS * 2.70 + 0.6)
    ax.axis("off")
    ax.text(ancho_m + 0.4, N_PISOS * 1.35,
            "Cada nivel aporta:\n"
            "  · su franja de losa\n"
            "  · el peso del propio muro\n"
            "  · su tarrajeo (2 caras)\n\n"
            u"Franja cr\u00edtica: %.2f m\n"
            u"\u00c1rea tributaria: %.2f m\u00b2\n\n"
            "El axial del 7.1.1.b se\n"
            "verifica en la BASE, con\n"
            "los %d niveles acumulados."
            % (critico[2], critico[3], N_PISOS),
            fontsize=9, va="center")
    fig.tight_layout(rect=[0, 0.13, 1, 0.94])
    C.guardar(fig, salida)
    return critico


def control(critico):
    """Que la figura represente la geometria del SSOT, no una parecida."""
    filas = tributaria_mx()
    suma = sum(f[2] for f in filas)
    assert abs(suma - FONDO) < 1e-9, (
        "las franjas tributarias suman %.4f y el fondo es %.4f" % (suma, FONDO))
    print("  [ok] las %d franjas tributarias suman el fondo completo (%.2f m)"
          % (len(filas), FONDO))
    assert abs(sum(PANOS_Y) - FONDO) < 1e-9, "los panos no suman el fondo"
    print("  [ok] los %d panos de losa suman el fondo (%.2f m)" % (len(PANOS_Y), FONDO))
    # El critico es el de mayor AREA, no el de mayor FRANJA. No son el mismo
    # muro: el pozo le descuenta losa a los de su borde, que son justamente
    # los de franja mas ancha. La primera version de este control verificaba
    # por franja y reviento -- que es exactamente para lo que esta.
    assert critico[3] == max(f[3] for f in filas), (
        "el muro marcado como critico no es el de mayor AREA tributaria")
    mas_ancho = max(filas, key=lambda f: f[2])
    print("  [ok] el muro destacado es el de mayor AREA: %s (%.2f m2)"
          % (critico[0].split()[0], critico[3]))
    if mas_ancho[0] != critico[0]:
        print("  [i]  y NO es el de mayor franja (%s, %.2f m): el pozo le"
              % (mas_ancho[0].split()[0], mas_ancho[2]))
        print("       descuenta losa y lo deja en %.0f m2 contra %.0f"
              % (mas_ancho[3], critico[3]))


def main():
    print("=" * 78)
    print("FIGURAS DE IDEALIZACION  -  criterios 3 y 4")
    print("=" * 78)
    f3 = os.path.join(R.INFORME, "IDEALIZACION-LOSA.png")
    f4 = os.path.join(R.INFORME, "IDEALIZACION-MURO.png")
    figura_losa(f3)
    critico = figura_muro(f4)
    print("  %-26s %.1f KB" % (os.path.basename(f3), os.path.getsize(f3) / 1024))
    print("  %-26s %.1f KB" % (os.path.basename(f4), os.path.getsize(f4) / 1024))
    print()
    control(critico)


if __name__ == "__main__":
    main()
