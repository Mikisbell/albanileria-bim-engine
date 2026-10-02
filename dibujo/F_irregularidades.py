# -*- coding: utf-8 -*-
"""Irregularidades: por qué R = 3,00 se mantiene.

QUE PIDE LA RUBRICA
===================
Criterios 5 y 6, análisis en X-X y en Y-Y. La sección tenía 1 005 palabras y
**ni un gráfico**, y es de las que más se entienden mirando: una deriva se
lee en un perfil, no en una tabla.

QUE MUESTRA, Y POR QUE ASI
==========================
La conclusión de esta sección es que **no hay irregularidades y R = 3,00 se
mantiene**, lo que evita rehacer todo el análisis. Eso descansa en un dato
que conviene ver:

  **La albañilería es rígida.** La deriva máxima es 0,000701 contra un
  admisible de 0,005: el 14 % del permitido. El perfil de la izquierda lo
  muestra piso por piso y en las dos direcciones.

  **Ese 14 % es lo que apaga el criterio torsional.** La Tabla 12 de la
  E.030 dice que el criterio *"solo se aplica si el máximo desplazamiento
  relativo de entrepiso es mayor que 50 % del permisible"*. Con 14 % no se
  llega al gatillo, y por eso el panel derecho dibuja el gatillo: sin verlo,
  el descarte parece una afirmación y no una medición.
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
import matplotlib                                              # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402
# `R` ya esta tomado por `rutas as R`: el factor de reduccion
# sismico entra con otro nombre
from proyecto import (N_PISOS, H_ENTREPISO,          # noqa: E402
                      DERIVA_LIMITE, R as R_SISMO)

DIR_X = "#1f5fbf"
DIR_Y = "#c0560f"
LIM = "#b02a1f"
GATILLO = "#c98a16"


def datos():
    """Derivas por nivel y direccion, del script 16."""
    ruta = os.path.join(AQUI, "..", "calculo", "16_irregularidades.py")
    spec = importlib.util.spec_from_file_location("_m16", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
        filas, h, Fi, xm, ym, xr, yr, V = m.informe()
        out = {}
        for dire in ("X", "Y"):
            d, _EI, _GA = m.desplazamientos(filas, dire, Fi, h)
            out[dire] = m.derivas(d, R_SISMO)
    return out


def main():
    dv = datos()
    niveles = list(range(1, N_PISOS + 1))
    gatillo = 0.50 * DERIVA_LIMITE

    # el pie lo necesita ANTES de dibujar, porque el marco reserva el
    # alto segun cuantas lineas ocupe
    peor = max(max(dv["X"]), max(dv["Y"]))
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 7.20), dpi=200)
    y_ar, y_ab = C.marco(
        fig, u"Irregularidades  ·  por qué R = 3,00 se mantiene",
        pie=(u"La Tabla 12 de la E.030 acota su propio alcance: el criterio "
             u"de irregularidad torsional «solo se aplica si el máximo "
             u"desplazamiento relativo de entrepiso es mayor que 50 %% del "
             u"permisible». Acá el máximo es %.6f, el %.1f %% del admisible, "
             u"así que el criterio no llega a aplicarse: Ia = Ip = 1,00 y "
             u"R = 3,00." % (peor, 100.0 * peor / DERIVA_LIMITE)))
    _h = (y_ar - y_ab - 0.07) / 2.0

    # ---- (a) perfil de derivas por nivel --------------------------------
    # APILADOS: cada panel con el ancho entero de la pagina
    ax = fig.add_axes((0.135, y_ab + _h + 0.07, 0.83, _h * 0.76))
    ax.plot(dv["X"], niveles, "o-", color=DIR_X, lw=2.0, ms=6,
            label="dirección X-X")
    ax.plot(dv["Y"], niveles, "s-", color=DIR_Y, lw=2.0, ms=6,
            label="dirección Y-Y")
    ax.axvline(DERIVA_LIMITE, color=LIM, lw=1.6, ls="--")
    ax.annotate("admisible 0,005\n(Tabla 14, albañilería)",
                (DERIVA_LIMITE, 3.0), xytext=(DERIVA_LIMITE * 0.62, 3.4),
                fontsize=8.5, color=LIM, fontweight="bold")
    ax.axvline(gatillo, color=GATILLO, lw=1.4, ls=":")
    ax.annotate("gatillo 50 %", (gatillo, 1.3), xytext=(gatillo * 1.06, 1.15),
                fontsize=8.5, color=GATILLO, fontweight="bold")
    ax.set_xlim(0, DERIVA_LIMITE * 1.18)
    ax.set_yticks(niveles)
    ax.set_ylabel("nivel", fontsize=9)
    ax.set_xlabel("distorsión de entrepiso  Δ/h", fontsize=9)
    ax.set_title("(a)  La albañilería es rígida: se usa el 14 % del admisible",
                 fontsize=10, loc="left", color=E.TINTA, pad=8)
    ax.legend(fontsize=8.5, frameon=False, loc="lower right")
    ax.grid(color="#dde3e8", lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    # ---- (b) cuanto se usa del admisible, por nivel ---------------------
    ax2 = fig.add_axes((0.135, y_ab, 0.83, _h * 0.76))
    w = 0.38
    for k, (dire, col) in enumerate((("X", DIR_X), ("Y", DIR_Y))):
        pct = [100.0 * d / DERIVA_LIMITE for d in dv[dire]]
        ax2.bar([n + (k - 0.5) * w for n in niveles], pct, w, color=col,
                label="%s-%s" % (dire, dire))
    ax2.axhline(50.0, color=GATILLO, lw=1.6, ls=":")
    ax2.annotate("gatillo del criterio torsional  (Tabla 12): 50 %",
                 (N_PISOS / 2.0 + 0.5, 50.0), xytext=(0.9, 53.0),
                 fontsize=8.5, color=GATILLO, fontweight="bold")
    ax2.axhline(100.0, color=LIM, lw=1.6, ls="--")
    ax2.annotate("100 % = admisible", (1.0, 100.0), xytext=(0.9, 103.0),
                 fontsize=8.5, color=LIM, fontweight="bold")
    ax2.set_xticks(niveles)
    ax2.set_ylim(0, 118)
    ax2.set_xlabel("nivel", fontsize=9)
    ax2.set_ylabel("% del admisible usado", fontsize=9)
    ax2.set_title("(b)  Ni siquiera se llega al gatillo de la Tabla 12",
                  fontsize=10, loc="left", color=E.TINTA, pad=8)
    ax2.legend(fontsize=8.5, frameon=False, loc="upper right")
    ax2.grid(axis="y", color="#dde3e8", lw=0.6)
    ax2.set_axisbelow(True)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)

    peor = max(max(dv["X"]), max(dv["Y"]))
    out = os.path.join(R.INFORME, "IRREGULARIDADES.png")
    C.guardar(fig, out)
    print()
    control(dv, gatillo)


def control(dv, gatillo):
    for dire in ("X", "Y"):
        assert len(dv[dire]) == N_PISOS, (
            "la direccion %s tiene %d derivas y son %d pisos"
            % (dire, len(dv[dire]), N_PISOS))
        for k, d in enumerate(dv[dire], 1):
            assert d > 0, ("deriva nula en el nivel %d de %s" % (k, dire))
            assert d < DERIVA_LIMITE, (
                "el nivel %d de %s tiene deriva %.6f >= admisible %.6f"
                % (k, dire, d, DERIVA_LIMITE))
    peor = max(max(dv["X"]), max(dv["Y"]))
    # la figura AFIRMA que no se llega al gatillo: hay que comprobarlo, o la
    # nota al pie estaria diciendo algo que el dibujo no sostiene
    assert peor < gatillo, (
        "la deriva maxima %.6f alcanza el gatillo %.6f: la nota de la figura "
        "afirmaria algo falso" % (peor, gatillo))
    print("  [ok] %d niveles x 2 direcciones, todas bajo el admisible"
          % N_PISOS)
    print("  [ok] deriva maxima %.6f = %.1f %% del admisible"
          % (peor, 100.0 * peor / DERIVA_LIMITE))
    print("  [ok] no se llega al gatillo del 50 %: el criterio torsional "
          "no aplica")


if __name__ == "__main__":
    main()
