# -*- coding: utf-8 -*-
"""El refuerzo horizontal: lo que entra en la junta de mortero.

POR QUE ESTA FIGURA
===================
Reemplaza a la lámina **E-02 del juego CAD antiguo** —«Identificación de los
trece muros y control de fisuración»—, que el informe seguía insertando como
figura y tenía tres problemas a la vez: **no se podía leer** (un A1 a 1:50
reducido a un A4), venía en blanco y negro, y **repetía el número E-02** de
la lámina vigente, que ya muestra los trece muros pintados por su cociente
`Ve/(0,55 Vm)`. Peor todavía: como el juego antiguo no se regenera con la
cadena, su cuadro seguía mostrando **números caducos** —`Ve/0,55Vm` = 0,63
en MY-1 cuando hoy es 0,572—.

Lo único que esa lámina aportaba y no estaba en ninguna otra parte era el
**detalle del refuerzo horizontal**, y es justo el punto donde la E.070 mete
una restricción que no es de cálculo sino de albañilería:

    4.1.2: «En las juntas que contengan refuerzo horizontal, el espesor
    mínimo de la junta será 6 mm más el diámetro de la barra».

Con el máximo de junta en 15 mm, de las dos cosas sale un tope que la norma
no escribe pero impone: **diámetro ≤ 9 mm**. Por eso la varilla de 3/8"
—9,53 mm— no entra aunque la cuantía le sobre: pediría una junta de 15,53
mm. Un dato así se pierde en una tabla y se ve en un dibujo.

QUE AFIRMA Y COMO SE VERIFICA
=============================
Todo sale de `18_diseno_muros.py`: `opciones_refuerzo_horizontal()` evalúa
cada calibre y `adoptar_refuerzo()` elige. El control comprueba que el
adoptado entre en la junta y cumpla la cuantía, que haya al menos un calibre
descartado **por la junta teniendo cuantía de sobra** —que es lo que el pie
afirma— y que el tope de 9 mm salga de la resta y no de la mano.
"""
import contextlib
import importlib.util
import io as _io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))
sys.path.insert(0, AQUI)

import rutas as R                                              # noqa: E402
import cuadro as C                                             # noqa: E402
import estilo as E                                             # noqa: E402
import paleta as PAL                                           # noqa: E402
import matplotlib                                              # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402
from matplotlib.patches import Rectangle                       # noqa: E402


def datos():
    ruta = os.path.join(AQUI, "..", "calculo", "18_diseno_muros.py")
    spec = importlib.util.spec_from_file_location("_m18", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def main():
    m = datos()
    # EL CONTRATO REAL del 18, leído y no supuesto: 'nombre', 'diam' y
    # 'junta_req' vienen en metros; 'hilada' y 's' en cm; 'n_hiladas' entero.
    ops = m.opciones_refuerzo_horizontal()
    ad = m.adoptar_refuerzo(ops)
    jmax_mm = m.JUNTA_MAX * 1000.0
    sobre_mm = m.SOBREESPESOR_JUNTA_REF * 1000.0
    rho_min = m.RHO_MIN
    # una fila por CALIBRE: la junta no depende de cuántas varillas se pongan,
    # así que se toma la combinación con el mismo n que la adoptada
    porv = [o for o in ops if o["n"] == ad["n"]]

    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 8.00), dpi=200)
    _ax_t = fig.add_axes((0, 0, 1, 1), frame_on=False)
    _ax_t.set_axis_off()
    _yt = 0.965
    for _ln in C.envolver(_ax_t, u"Refuerzo horizontal  ·  el 8.6.1 manda "
                          u"ponerlo y el 4.1.2 decide qué diámetro ENTRA en "
                          u"la junta", 12.0, 0.93, "bold"):
        fig.text(0.5, _yt, _ln, fontsize=12.0, fontweight="bold",
                 color=E.TINTA, ha="center", va="top")
        _yt -= 0.022

    # ---- (a) el muro con sus hiladas y la varilla cada n ---------------
    # la elevacion, alta y angosta, a la izquierda
    ax = fig.add_axes((0.055, 0.35, 0.28, 0.50))
    h_h = 0.10
    n_hil_dib = 13
    ancho = 2.2
    for i in range(n_hil_dib):
        ax.add_patch(Rectangle((0, i * h_h), ancho, h_h * 0.84,
                               fc=PAL.MURO, ec="#ffffff", lw=1.0))
    paso = ad["n_hiladas"]
    ys = []
    for i in range(paso - 1, n_hil_dib, paso):
        y = i * h_h + h_h * 0.88
        ys.append(y)
        ax.plot([0.04, ancho - 0.04], [y, y], color=PAL.ALERTA, lw=2.4,
                solid_capstyle="round", zorder=4)
    if len(ys) >= 2:
        ax.annotate("", xy=(ancho + 0.12, ys[0]),
                    xytext=(ancho + 0.12, ys[1]),
                    arrowprops=dict(arrowstyle="<->", color=PAL.COTA, lw=1.0))
        ax.text(ancho + 0.18, (ys[0] + ys[1]) / 2, "s = %.1f cm" % ad["s"],
                va="center", rotation=90, fontsize=9, color=PAL.COTA,
                fontweight="bold")
    ax.text(ancho / 2, n_hil_dib * h_h + 0.09,
            "%d ø %s cada %d hiladas"
            % (ad["n"], ad["nombre"], ad["n_hiladas"]),
            ha="center", fontsize=10, color=PAL.ALERTA, fontweight="bold")
    ax.text(ancho / 2, -0.10,
            "junta de asiento en esas hiladas:\n%.0f mm (el resto, %.0f)"
            % (ad["junta"] * 1000, m.JUNTA_MIN * 1000),
            ha="center", va="top", fontsize=7.2, color="#55606a",
            linespacing=1.35)
    ax.set_xlim(-0.10, ancho + 0.58)
    ax.set_ylim(-0.30, n_hil_dib * h_h + 0.26)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("(a)  Cómo va en el muro", fontsize=10, loc="left",
                 color=E.TINTA, pad=6)

    # ---- (b) el tope de la junta ---------------------------------------
    # los dos graficos de barras HORIZONTALES, apilados a la derecha:
    # una barra horizontal es ancha y baja, asi que apilarlos usa el
    # alto de la pagina en vez de pelear por su ancho.
    ax2 = fig.add_axes((0.44, 0.60, 0.51, 0.25))
    nom = [o["nombre"] for o in porv]
    jun = [o["junta_req"] * 1000.0 for o in porv]
    cols = [PAL.BIEN if o["entra"] else PAL.ALERTA for o in porv]
    ax2.barh(range(len(porv)), jun, 0.60, color=cols)
    ax2.axvline(jmax_mm, color=PAL.GOBIERNA, lw=1.7, ls=(0, (5, 3)))
    # el rótulo del umbral va ARRIBA y a la izquierda de su línea: puesto
    # abajo caía encima de los números del eje (81 % de solape medido)
    ax2.text(jmax_mm - 0.25, len(porv) - 0.68, "máximo %.0f mm" % jmax_mm,
             fontsize=8, color=PAL.GOBIERNA, fontweight="bold",
             ha="right", va="top")
    for i, j in enumerate(jun):
        # si la etiqueta fuera de la barra cruzaría la línea del máximo, se
        # mete dentro: un número encima de una punteada no se lee
        if abs(j - jmax_mm) < 1.6:
            ax2.annotate("%.2f" % j, (j, i), xytext=(j - 0.25, i),
                         va="center", ha="right", fontsize=8.5,
                         color="white", fontweight="bold")
        else:
            ax2.annotate("%.2f" % j, (j, i), xytext=(j + 0.18, i),
                         va="center", fontsize=8.5, color="#55606a")
    ax2.set_yticks(range(len(porv)))
    ax2.set_yticklabels(nom, fontsize=9.5)
    ax2.set_xlabel("junta que exige el 4.1.2  (mm)", fontsize=9)
    ax2.set_xlim(0, max(jun) * 1.22)
    ax2.grid(axis="x", color="#dde3e8", lw=0.6)
    ax2.set_axisbelow(True)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    ax2.set_title("(b)  Qué diámetro ENTRA", fontsize=10, loc="left",
                  color=E.TINTA, pad=6)

    # ---- (c) la cuantía --------------------------------------------------
    ax3 = fig.add_axes((0.44, 0.29, 0.51, 0.25))
    rho = [o["rho"] for o in porv]
    cols3 = [PAL.BIEN if o["entra"] else "#cfd6db" for o in porv]
    ax3.barh(range(len(porv)), rho, 0.60, color=cols3)
    ax3.axvline(rho_min, color=PAL.GOBIERNA, lw=1.7, ls=(0, (5, 3)))
    ax3.text(rho_min * 0.97, len(porv) - 0.68,
             "mínimo 8.6.1  %.4f" % rho_min, fontsize=8,
             color=PAL.GOBIERNA, fontweight="bold", ha="right", va="top")
    for i, r in enumerate(rho):
        if abs(r - rho_min) < rho_min * 0.22:
            # el texto va DENTRO de la barra, así que su color depende del
            # color de la barra: blanco sobre el gris claro del descartado
            # no se lee, y la figura existe justamente para que se lea
            dentro = "white" if cols3[i] == PAL.BIEN else "#37474f"
            ax3.annotate("%.5f" % r, (r, i), xytext=(r * 0.97, i),
                         va="center", ha="right", fontsize=8,
                         color=dentro, fontweight="bold")
        else:
            ax3.annotate("%.5f" % r, (r, i), xytext=(r * 1.02, i),
                         va="center", fontsize=8, color="#55606a")
    ax3.set_yticks(range(len(porv)))
    ax3.set_yticklabels([""] * len(porv))
    ax3.set_xlabel("cuantía ρ resultante", fontsize=9)
    ax3.set_xlim(0, max(rho) * 1.42)
    ax3.grid(axis="x", color="#dde3e8", lw=0.6)
    ax3.set_axisbelow(True)
    for s in ("top", "right"):
        ax3.spines[s].set_visible(False)
    ax3.set_title("(c)  Y si alcanza la cuantía", fontsize=10, loc="left",
                  color=E.TINTA, pad=6)

    fuera = [o for o in porv if not o["entra"]]
    _pie = ("La de %s SOBRA de cuantía (%.5f) y no se puede usar: el 4.1.2 "
             "pide una junta de %.0f mm más el diámetro —%.2f mm— y el "
             "máximo es %.0f. De ahí sale un tope que la norma no escribe "
             "pero impone: el diámetro no puede pasar de %.0f mm. El "
             "refuerzo horizontal no se elige por resistencia: se elige por "
             "lo que ENTRA en la junta."
            % (fuera[0]["nombre"], fuera[0]["rho"], sobre_mm,
               fuera[0]["junta_req"] * 1000, jmax_mm, jmax_mm - sobre_mm))
    # EL PIE SE ENVUELVE. Sin envolver, sus 430 caracteres en una linea
    # ensanchaban la figura de 13,2 a 19,7 pulgadas (ver el docstring).
    _y = 0.135
    for _ln in C.envolver(fig.add_axes((0, 0, 1, 1), frame_on=False),
                          _pie, 8.0, 0.925):
        fig.text(0.045, _y, _ln, fontsize=8.0, color="#55606a", va="top")
        _y -= 0.0165

    out = os.path.join(R.INFORME, "REFUERZO-HORIZONTAL.png")
    C.guardar(fig, out)
    print()
    control(m, ops, ad)


def control(m, ops, ad):
    """Lo que la figura afirma sale del 18, no del dibujo."""
    jmax = m.JUNTA_MAX
    assert ad["junta_req"] <= jmax + 1e-12, (
        "se adopta %s con junta de %.2f mm y el maximo es %.0f"
        % (ad["nombre"], ad["junta_req"] * 1000, jmax * 1000))
    assert ad["rho"] >= m.RHO_MIN - 1e-12, (
        "la cuantia adoptada %.5f no llega al minimo %.4f"
        % (ad["rho"], m.RHO_MIN))
    # LA AFIRMACION CENTRAL del panel (b) y del pie: tiene que haber un
    # calibre descartado POR LA JUNTA y que ademas tenga cuantia de sobra.
    # Si algun dia deja de ser cierto, la figura ensenaria una restriccion
    # que no restringe, que es lo que le paso a la figura de peso por nivel.
    fuera = [o for o in ops if not o["entra"]]
    assert fuera, ("la figura afirma que el 4.1.2 deja fuera algun diametro "
                   "y ninguno de los %d evaluados excede la junta" % len(ops))
    sobrados = [o for o in fuera if o["rho"] >= m.RHO_MIN]
    assert sobrados, ("el pie dice que el descartado SOBRA de cuantia y "
                      "ninguno de los descartados llega al minimo")
    tope = (jmax - m.SOBREESPESOR_JUNTA_REF) * 1000
    assert abs(tope - 9.0) < 1e-9, (
        "el pie dice que el tope es 9 mm y de la resta salen %.2f" % tope)
    print("  [ok] el adoptado (%d o %s cada %d hiladas) entra en la junta"
          % (ad["n"], ad["nombre"], ad["n_hiladas"]))
    print("  [ok] rho = %.5f >= %.4f del 8.6.1" % (ad["rho"], m.RHO_MIN))
    print("  [ok] %d combinaciones quedan fuera por la junta del 4.1.2, y %d "
          "de ellas sobraban de cuantia" % (len(fuera), len(sobrados)))
    return True


if __name__ == "__main__":
    main()
