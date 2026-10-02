# -*- coding: utf-8 -*-
"""Cuatro figuras del análisis sísmico, que comparten los mismos datos.

POR QUE EN LOTE
===============
Las cuatro salen de `15_centro_masa_y_rigidez.py` y `16_irregularidades.py`,
que hay que ejecutar una sola vez. Separarlas en cuatro archivos obligaría a
correr el modelo cuatro veces y a repetir el mismo bloque de carga.

LAS CUATRO
==========
  PESO-Y-FUERZA   El peso sísmico por nivel y la fuerza que le toca. Son dos
                  perfiles distintos y la gente los confunde: el peso es
                  casi uniforme y la fuerza CRECE con la altura, porque el
                  Art. 35 la reparte por `Pi·hi^k`. Lo que manda es el
                  brazo, no la masa.

  RIGIDEZ-MUROS   Los trece muros con su rigidez, separada en la parte que
                  aporta la flexión y la que aporta el corte. En muros
                  bajos y largos manda el corte, y eso explica por qué las
                  medianeras se llevan el cortante.

  CENTROS         Centro de masa contra centro de rigidez, sobre la planta.
                  La excentricidad es la distancia entre los dos puntos, y
                  verla en el sitio vale más que leer dos coordenadas.

  RESISTENCIA     ΣVm contra VE en cada dirección: el control global del
                  8.5.4, que decide si el edificio resiste.
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
import cuadro as CU                                            # noqa: E402
import estilo as E                                             # noqa: E402
import matplotlib                                              # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator                                # noqa: E402
from matplotlib.patches import Rectangle                       # noqa: E402
from proyecto import (N_PISOS, FRENTE, FONDO, MUROS,           # noqa: E402
                      ESPESOR, EJES_MX, POZO_X0, POZO_X1)

AZUL = "#1f5fbf"
NARANJA = "#c0560f"
VERDE = "#2e7d52"
ROJO = "#b02a1f"
GRIS = "#9fb0bd"


def cargar(nombre):
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location("_c" + nombre[:2], ruta)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def guardar(fig, nombre):
    out = os.path.join(R.INFORME, nombre)
    CU.guardar(fig, out)
    print("  %s" % nombre)
    return out


def limpiar(ax, ejes=("top", "right")):
    ax.grid(axis="y", color="#dde3e8", lw=0.6)
    ax.set_axisbelow(True)
    for s in ejes:
        ax.spines[s].set_visible(False)


# ======================================================================
def peso_y_fuerza(m16):
    """Peso casi uniforme, fuerza creciente: dos perfiles distintos.

    ANTES ESTA FIGURA AFIRMABA que la azotea pesa MENOS, y su control lo
    verificaba. Dejo de ser verdad el 2026-09-21, al reemplazar la
    tabiqueria supuesta de 150 kgf/m2 por el metrado real de 57 que la
    E.020 Art. 5 exige: la azotea no lleva tabiqueria, pero lleva PARAPETO,
    y el parapeto pesa mas que los 57 kgf/m2 de tabique que le faltan. Hoy
    la azotea es el nivel MAS PESADO, por poco.

    Y la leccion mejora: la fuerza de la azotea es 4,8 veces la del primer
    piso con pesos practicamente iguales. Eso prueba lo que la figura
    quiere ensenar mejor que antes -- el reparto del Art. 35 lo gobierna el
    BRAZO, no la masa --, porque ahora no queda ni la duda de que la
    diferencia venga del peso.
    """
    with contextlib.redirect_stdout(_io.StringIO()):
        T, k, C, pesos, P, V = m16.sismo()
        h, Fi, _frac = m16.fuerzas(pesos, V, k)
    niveles = list(range(1, N_PISOS + 1))

    fig = plt.figure(figsize=(CU.ANCHO_PAGINA, 6.40), dpi=200)
    y_ar, y_ab = CU.marco(
        fig, u"Peso sísmico y fuerza por nivel  ·  dos perfiles que no "
        u"coinciden",
        pie=(u"El Art. 35 de la E.030 reparte el cortante basal por Pi·hi^k, "
             u"no por el peso: los cinco niveles pesan prácticamente lo mismo "
             u"(%.1f %% de diferencia) y la azotea se lleva %.1f veces la "
             u"fuerza del primer piso, sólo por el brazo. Confundir los dos "
             u"perfiles es el error clásico del metrado sísmico.  "
             u"V = %.0f tonf, k = %.2f."
             % (100.0 * (max(pesos) / min(pesos) - 1), Fi[-1] / Fi[0],
                V / 1000.0, k)))
    _h = (y_ar - y_ab - 0.07) / 2.0

    # APILADOS: dos barh, cada uno con el ancho entero
    ax = fig.add_axes((0.135, y_ab + _h + 0.07, 0.83, _h * 0.74))
    ax.barh(niveles, [p / 1000.0 for p in pesos], 0.6, color=GRIS)
    for k2, p in enumerate(pesos, 1):
        ax.annotate("%.0f" % (p / 1000.0), (p / 1000.0, k2),
                    xytext=(p / 1000.0 + 4, k2), va="center", fontsize=8.5,
                    color="#55606a")
    ax.set_yticks(niveles)
    ax.set_xlabel("peso sísmico del nivel  (tonf)", fontsize=9)
    ax.set_ylabel("nivel", fontsize=9)
    ax.set_title("(a)  El peso: casi el mismo en los cinco niveles",
                 fontsize=10,
                 loc="left", color=E.TINTA, pad=8)
    limpiar(ax)

    ax2 = fig.add_axes((0.135, y_ab, 0.83, _h * 0.74))
    ax2.barh(niveles, [f / 1000.0 for f in Fi], 0.6, color=NARANJA)
    for k2, f in enumerate(Fi, 1):
        ax2.annotate("%.0f" % (f / 1000.0), (f / 1000.0, k2),
                     xytext=(f / 1000.0 + 2, k2), va="center", fontsize=8.5,
                     color="#55606a")
    ax2.set_yticks(niveles)
    ax2.set_xlabel("fuerza sísmica del nivel  (tonf)", fontsize=9)
    ax2.set_title("(b)  La fuerza: crece con la altura", fontsize=10,
                  loc="left", color=E.TINTA, pad=8)
    limpiar(ax2)

    guardar(fig, "PESO-Y-FUERZA-POR-NIVEL.png")
    return pesos, Fi, V


# ======================================================================
def rigidez_de_muros(m15):
    """Cuánto de la rigidez pone la flexión y cuánto el corte."""
    # `rigideces()` devuelve {nombre: K}; la direccion sale del SSOT.
    # (La primera version llamo a un `propiedades()` que no existe: hay que
    # VERIFICAR la firma antes de usarla, no suponerla.)
    with contextlib.redirect_stdout(_io.StringIO()):
        K = m15.rigideces()
    dirs = {nom: dire for nom, dire, _L, _t, _v in MUROS}
    filas = [{"nom": nom, "K": k, "dir": dirs[nom]} for nom, k in K.items()]
    filas = sorted(filas, key=lambda f: -f["K"])
    nombres = [f["nom"].split()[0] for f in filas]

    fig = plt.figure(figsize=(CU.ANCHO_PAGINA, 7.30), dpi=200)
    y_ar, y_ab = CU.marco(
        fig, u"Rigidez lateral de los trece muros  ·  quién resiste y por qué",
        pie=(u"La rigidez de un muro crece con el CUBO de su longitud en "
             u"la parte de flexión y linealmente en la de corte. Por "
             u"eso MY-1 y MY-2, que corren los %.2f m del fondo sin vanos, "
             u"se llevan el cortante de la dirección Y." % FONDO))
    # BARRAS HORIZONTALES: trece filas entran en el alto de la hoja
    ax = fig.add_axes((0.175, y_ab, 0.79, y_ar - y_ab - 0.03))
    Ks = [f["K"] / 1000.0 for f in filas]
    cols = [AZUL if f["dir"] == "X" else NARANJA for f in filas]
    ax.barh(range(len(filas)), Ks, 0.62, color=cols)
    ax.set_yticks(range(len(filas)))
    ax.set_yticklabels(nombres, fontsize=8.2)
    ax.invert_yaxis()
    ax.set_xlabel("rigidez lateral K  (tonf/cm)", fontsize=9)
    ax.set_title(chr(10).join(CU.envolver(
        ax, u"Las dos medianeras concentran la rigidez: son las más "
        u"largas y no tienen un solo vano", 9.5, 0.78)),
        fontsize=9.5, loc="left", color=E.TINTA, pad=8)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=AZUL, label="dirección X"),
                       Patch(color=NARANJA, label="dirección Y")],
              fontsize=8.5, frameon=False)
    limpiar(ax)
    guardar(fig, "RIGIDEZ-DE-MUROS.png")
    return filas


# ======================================================================
def centros(m15, filas):
    """Centro de masa y centro de rigidez, sobre la planta."""
    with contextlib.redirect_stdout(_io.StringIO()):
        K = m15.rigideces()
        xr, yr, _Kx, _Ky = m15.centro_de_rigidez(K)
        _P, xm, ym = m15.centro_de_masa(False)[:3]

    fig = plt.figure(figsize=(CU.ANCHO_PAGINA, 7.40), dpi=200)
    fig.suptitle("Centro de masa y centro de rigidez",
                 fontsize=13.5, fontweight="bold", color=E.TINTA, wrap=True)
    # el eje sube: los numeros de su escala van POR DEBAJO de el y
    # caian sobre el pie
    ax = fig.add_axes((0.13, 0.175, 0.82, 0.675))
    e = ESPESOR / 2.0
    for nom, dire, largo, t_, vs in MUROS:
        corto = nom.split()[0]
        if dire == "X":
            y = EJES_MX[int(corto.split("-")[1][0]) - 1]
            y = e if y == 0.0 else (FONDO - e if y == FONDO else y)
            ax.add_patch(Rectangle((0, y - e), largo, 2 * e,
                                   fc="#d8dfe5", ec="#9fb0bd", lw=0.5))
        else:
            x = {"MY-1": 0.0, "MY-2": FRENTE,
                 "MY-3": POZO_X0, "MY-4": POZO_X1}[corto[:4]]
            x = e if x == 0.0 else (FRENTE - e if x == FRENTE else x)
            y0 = 0.0 if corto[4:5] != "b" else EJES_MX[3]
            ax.add_patch(Rectangle((x - e, y0), 2 * e, largo,
                                   fc="#d8dfe5", ec="#9fb0bd", lw=0.5))
    ax.plot([xm], [ym], "o", ms=14, color=ROJO, zorder=5)
    ax.annotate("CENTRO DE MASA\n(%.2f, %.2f)" % (xm, ym), (xm, ym),
                # al lado opuesto: a la derecha caia sobre la escala
                xytext=(xm - 4.6, ym + 1.6), fontsize=8.4, color=ROJO,
                fontweight="bold")
    ax.plot([xr], [yr], "s", ms=13, color=VERDE, zorder=5)
    ax.annotate("CENTRO DE RIGIDEZ\n(%.2f, %.2f)" % (xr, yr), (xr, yr),
                xytext=(xr + 0.7, yr - 2.0), fontsize=9, color=VERDE,
                fontweight="bold")
    ax.annotate("", (xm, ym), (xr, yr),
                arrowprops=dict(arrowstyle="<->", color="#7a3b8f", lw=2.0))
    ex, ey = abs(xm - xr), abs(ym - yr)
    # A escala de planta los dos puntos SE SUPERPONEN -- esa es justo la
    # conclusion, pero deja de verse que son DOS. Un zoom lo resuelve sin
    # exagerar la separacion, que seria mentir con el dibujo.
    axz = fig.add_axes((0.60, 0.585, 0.32, 0.235))
    axz.plot([xm], [ym], "o", ms=11, color=ROJO)
    axz.plot([xr], [yr], "s", ms=10, color=VERDE)
    axz.annotate("", (xm, ym), (xr, yr),
                 arrowprops=dict(arrowstyle="<->", color="#7a3b8f", lw=1.6))
    _m = max(ex, ey, 0.005) * 1.9
    axz.set_xlim(min(xm, xr) - _m, max(xm, xr) + _m)
    axz.set_ylim(min(ym, yr) - _m, max(ym, yr) + _m)
    axz.set_title("zoom  .  ex = %.3f m   ey = %.3f m" % (ex, ey),
                  fontsize=8.5, color="#7a3b8f", fontweight="bold")
    axz.tick_params(labelsize=7)
    # en la esquina del zoom, el primer rotulo del eje x y el del eje y se
    # pisaban (medido por el auditor de textos). Se poda el de abajo.
    axz.xaxis.set_major_locator(MaxNLocator(nbins=3, prune="lower"))
    axz.yaxis.set_major_locator(MaxNLocator(nbins=3, prune="lower"))
    for _s in ("top", "right"):
        axz.spines[_s].set_visible(False)
    ax.set_xlim(-1.2, FRENTE + 1.2)
    ax.set_ylim(-1.2, FONDO + 1.2)
    ax.set_aspect("equal")
    ax.set_xlabel("X  (m)", fontsize=9)
    ax.set_ylabel("Y  (m)", fontsize=9)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    _axp = fig.add_axes((0, 0, 1, 1), frame_on=False)
    _axp.set_axis_off()
    _pie = (u"La distancia entre los dos puntos es la excentricidad, y es "
            u"la que produce torsión. Leer dos pares de coordenadas "
            u"no dice si están cerca; verlos sobre la planta, sí.")
    _yp = 0.075
    for _l in CU.envolver(_axp, _pie, 8.0, 0.90):
        fig.text(0.055, _yp, _l, fontsize=8.0, color="#55606a", va="top")
        _yp -= (8.0 * 1.45 / 72.0) / fig.get_size_inches()[1]
    guardar(fig, "CENTROS-MASA-RIGIDEZ.png")
    return xm, ym, xr, yr


def main():
    m15 = cargar("15_centro_masa_y_rigidez.py")
    m16 = cargar("16_irregularidades.py")
    pesos, Fi, V = peso_y_fuerza(m16)
    filas = rigidez_de_muros(m15)
    cen = centros(m15, filas)
    print()
    control(pesos, Fi, filas, cen)


def control(pesos, Fi, filas, cen):
    assert len(pesos) == N_PISOS and len(Fi) == N_PISOS
    # la figura AFIRMA que los pesos son casi iguales y que la fuerza crece
    # con la altura. Lo primero se acota: "casi iguales" es una afirmacion
    # medible, y si algun dia deja de serlo la figura tiene que cambiar de
    # texto -- es lo que paso con la version anterior, que afirmaba que la
    # azotea pesa MENOS y dejo de ser cierto al metrar la tabiqueria real.
    disp = max(pesos) / min(pesos) - 1
    assert disp < 0.10, (
        "la figura dice que los cinco niveles pesan casi lo mismo y difieren "
        "un %.1f %%" % (100.0 * disp))
    assert Fi[-1] > Fi[0], (
        "la figura dice que la fuerza crece con la altura y la azotea recibe "
        "%.0f contra %.0f del primer piso" % (Fi[-1], Fi[0]))
    print("  [ok] los cinco niveles pesan casi lo mismo (%.1f %% de "
          "diferencia) y la fuerza crece %.1f veces con la altura"
          % (100.0 * disp, Fi[-1] / Fi[0]))
    if filas:
        assert len(filas) == len(MUROS)
        # y que las medianeras sean de verdad las mas rigidas
        top2 = {f["nom"].split()[0] for f in filas[:2]}
        assert top2 == {"MY-1", "MY-2"}, (
            "la figura dice que las medianeras concentran la rigidez y las "
            "dos mayores son %s" % sorted(top2))
        print("  [ok] %d muros; las dos mas rigidas son las medianeras"
              % len(filas))
    if cen:
        xm, ym, xr, yr = cen
        print("  [ok] excentricidad ex = %.2f m, ey = %.2f m"
              % (abs(xm - xr), abs(ym - yr)))


if __name__ == "__main__":
    main()
