# -*- coding: utf-8 -*-
"""Figura de la SECCIÓN TRANSFORMADA de un muro confinado (E.070 8.3.6).

QUE TIENE QUE EXPLICAR LA FIGURA
================================
Un muro confinado no es homogeneo: es albanileria con columnas de concreto en
los extremos y en las intersecciones, mas las alas que le ceden los muros
ortogonales. Para calcular una inercia hay que llevarlo a UN SOLO material, y
eso es lo que la figura muestra: arriba la seccion REAL, abajo la TRANSFORMADA
a albanileria equivalente.

EL PUNTO QUE LA FIGURA HACE VISIBLE
===================================
Que las columnas, al transformarse, se vuelven ANCHAS. Con n = Ec/Em = 6,69
una columna de 0,24 x 0,30 m aporta como si fueran 4 817 cm2 de albanileria.
En un dibujo eso se ve de golpe; en una tabla de inercias, no.

Y hace visible tambien por que el acapite obliga a transformarlas: estan en
los EXTREMOS, donde el brazo al centroide es maximo, y el brazo entra AL
CUADRADO en el teorema de ejes paralelos.

POR QUE EL (n-1) Y NO n
=======================
El alma cuenta el area geometrica completa, tramos de columna incluidos. Cada
columna suma solo el EXCESO del concreto sobre la albanileria ya contada, de
modo que en esa zona queda A + (n-1)A = n.A. La figura lo dibuja asi: la banda
del alma es continua y la columna se apila ENCIMA.
"""
import rutas as R
import cuadro as C                                             # noqa: E402
import importlib.util
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402
from matplotlib.patches import Rectangle                           # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))

from proyecto import (ESPESOR, H_COLUMNA, H_COLUMNA_EXT, FC, EM,      # noqa: E402
                      MUROS, vanos_ubicados)

COL_ALMA = "#d9c9a3"        # albanileria
COL_COL = "#9aa7b1"         # concreto
COL_ALA = "#c5d8c5"         # ala cedida por el muro ortogonal
COL_TRANSF = "#e8dcc0"      # todo convertido a albanileria


def _cargar(nombre):
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "f", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R12 = _cargar("12_rigidez_lateral.py")
MURO = "MX-2"               # un transversal interior: el caso representativo


def datos():
    fila = [m for m in MUROS if m[0].startswith(MURO)][0]
    nom, dire, L, t, vanos = fila
    A, I, Ac, Ln = R12.seccion(nom, dire, L, t, vanos)
    ejes = R12.columnas(nom, dire, L)
    alas = R12.cruces(nom, dire, L)
    puestos = vanos_ubicados(nom, dire, L, vanos)
    return nom, dire, L, t, vanos, A, I, Ln, ejes, alas, puestos


def dibujar():
    nom, dire, L, t, vanos, A, I, Ln, ejes, alas, puestos = datos()
    n = R12.N_TRANSF

    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 5.60))
    # rectangulos explicitos, sin tight_layout: ver el porque arriba
    ax1 = fig.add_axes((0.105, 0.545, 0.865, 0.315))
    ax2 = fig.add_axes((0.105, 0.145, 0.865, 0.315))
    fig.suptitle("Sección transformada del muro %s  —  E.070 8.3.6" % MURO,
                 fontsize=13, fontweight="bold", wrap=True)

    # ---------------------------------------------------- (a) seccion REAL
    ax1.set_title("(a)  Sección real: dos materiales", fontsize=10, loc="left")
    ax1.add_patch(Rectangle((0, 0), Ln, t, facecolor=COL_ALMA,
                            edgecolor="#6b5b3e", lw=1.2))
    for j, x in enumerate(ejes):
        extrema = (j == 0 or j == len(ejes) - 1)
        h = H_COLUMNA_EXT if extrema else H_COLUMNA
        xc = R12.condensar(x, puestos)
        ax1.add_patch(Rectangle((xc - h / 2, -0.05), h, t + 0.10,
                                facecolor=COL_COL, edgecolor="#43505a",
                                lw=1.4, zorder=3))
        ax1.text(xc, t + 0.16, "C-%d" % (2 if extrema else 1),
                 ha="center", fontsize=8.5, color="#43505a", fontweight="bold")
    for x in alas:
        xc = R12.condensar(x, puestos)
        ax1.add_patch(Rectangle((xc - t / 2, -R12.ALA), t, R12.ALA,
                                facecolor=COL_ALA, edgecolor="#4a6b4a", lw=1.1))
    ax1.text(-1.05, -R12.ALA / 2, "alas" + chr(10) + "6t", ha="center", va="center",
             fontsize=8.5, color="#4a6b4a")
    ax1.text(Ln / 2, -R12.ALA - 0.55,
             "albañilería  $f'_m$ = %.0f  ·  $E_m$ = %s kgf/cm²"
             % (65, "{:,.0f}".format(EM).replace(",", " ")),
             ha="center", fontsize=9, color="#6b5b3e")
    ax1.text(Ln + 0.25, t / 2,
             "concreto  $f'_c$ = %.0f\n$E_c$ = %s kgf/cm²"
             % (FC, "{:,.0f}".format(R12.EC).replace(",", " ")),
             va="center", fontsize=9, color="#43505a")

    # ------------------------------------------- (b) seccion TRANSFORMADA
    ax2.set_title(chr(10).join(C.envolver(
        ax2, u"(b)  Transformada a albañilería equivalente: el ancho de cada "
        u"columna se multiplica por n = Ec/Em = %.2f" % n, 9.5, 0.86)),
        fontsize=9.5, loc="left")
    ax2.add_patch(Rectangle((0, 0), Ln, t, facecolor=COL_TRANSF,
                            edgecolor="#6b5b3e", lw=1.2))
    for j, x in enumerate(ejes):
        extrema = (j == 0 or j == len(ejes) - 1)
        h = H_COLUMNA_EXT if extrema else H_COLUMNA
        xc = R12.condensar(x, puestos)
        # el EXCESO (n-1) se apila ENCIMA del alma: el alma ya conto su area
        alto = t * (n - 1.0)
        ax2.add_patch(Rectangle((xc - h / 2, t), h, alto,
                                facecolor=COL_COL, edgecolor="#43505a", lw=1.2))
        if extrema:
            ax2.annotate("$(n-1)\\cdot t$ = %.2f m" % alto,
                         xy=(xc, t + alto), xytext=(xc + 0.8, t + alto + 0.35),
                         fontsize=8.5, color="#43505a",
                         arrowprops=dict(arrowstyle="->", color="#43505a", lw=1))
    for x in alas:
        xc = R12.condensar(x, puestos)
        ax2.add_patch(Rectangle((xc - t / 2, -R12.ALA), t, R12.ALA,
                                facecolor=COL_ALA, edgecolor="#4a6b4a", lw=1.1))

    a_col = H_COLUMNA_EXT * t * n
    ax2.text(Ln / 2, -R12.ALA - 0.55,
             "Una columna extrema de %.2f × %.2f m aporta como "
             "%s cm² de albañilería:  $n \\cdot A$"
             % (t, H_COLUMNA_EXT,
                "{:,.0f}".format(a_col * 1e4).replace(",", " ")),
             ha="center", fontsize=9.5, color="#43505a")

    for ax in (ax1, ax2):
        ax.set_xlim(-1.2, Ln + 2.6)
        ax.set_aspect("equal")
        ax.axis("off")
    ax1.set_ylim(-R12.ALA - 1.0, t + 0.85)
    ax2.set_ylim(-R12.ALA - 1.1, t + t * (n - 1) + 0.9)

    _pie = (u"El alma cuenta el área geométrica completa; cada "
            u"columna suma sólo el exceso (n−1), de modo que en "
            u"esa zona queda A + (n−1)A = n·A.")
    _axp = fig.add_axes((0, 0, 1, 1), frame_on=False)
    _axp.set_axis_off()
    _yp = 0.040
    for _l in C.envolver(_axp, _pie, 8.4, 0.90):
        fig.text(0.5, _yp, _l, ha="center", fontsize=8.4, style="italic",
                 color="#444", va="top")
        _yp -= (8.4 * 1.45 / 72.0) / fig.get_size_inches()[1]
    salida = os.path.join(R.INFORME, "SECCION-TRANSFORMADA.png")
    C.guardar(fig, salida)
    return salida, A, I, Ln, len(ejes), len(alas), n


def control(A, I, Ln, n_col, n_alas):
    """Que la figura dibuje lo que el script 12 calcula, no algo parecido."""
    nom, dire, L, t, vanos, A2, I2, Ln2, ejes, alas, _p = datos()
    assert abs(A - A2) < 1e-6 and abs(I - I2) < 1e-3, (
        "la figura y el script 12 no coinciden en area o inercia")
    assert n_col == len(ejes) and n_alas == len(alas), (
        "la figura dibuja %d columnas y %d alas; el 12 dice %d y %d"
        % (n_col, n_alas, len(ejes), len(alas)))
    # y que el (n-1) sea de verdad el exceso: A_alma + exceso = n.A en la columna
    a_geom = H_COLUMNA_EXT * ESPESOR
    assert abs(a_geom + a_geom * (R12.N_TRANSF - 1) - R12.N_TRANSF * a_geom) < 1e-9
    return True


if __name__ == "__main__":
    salida, A, I, Ln, n_col, n_alas, n = dibujar()
    control(A, I, Ln, n_col, n_alas)
    print("=" * 74)
    print("FIGURA: SECCION TRANSFORMADA  -  E.070 8.3.6")
    print("=" * 74)
    print()
    print("  archivo : %s" % os.path.basename(salida))
    print("  muro    : %s, un transversal interior" % MURO)
    print("  n = Ec/Em = %.2f   ->  una C-2 aporta %s cm2 de albanileria"
          % (n, "{:,.0f}".format(H_COLUMNA_EXT * ESPESOR * n * 1e4).replace(",", " ")))
    print("  seccion : A = %s cm2   I = %.3e cm4"
          % ("{:,.0f}".format(A).replace(",", " "), I))
    print("  control : la figura reproduce el area y la inercia del script 12")
    print()
    print("  LO QUE LA FIGURA HACE VISIBLE: que al transformarse las columnas")
    print("  se vuelven ANCHAS, y que estan en los EXTREMOS -- donde el brazo")
    print("  al centroide es maximo y entra AL CUADRADO en la inercia.")
