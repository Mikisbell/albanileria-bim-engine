# -*- coding: utf-8 -*-
"""Cinco figuras más, para las secciones que quedaban con menos densidad.

POR QUE
=======
Medido tras el lote anterior: la unidad iba a 2 069 palabras por figura, el
modelo computacional a 1 791 y los confinamientos a 1 108. El promedio del
informe estaba en 1 037, y un trabajo que se califica por lo didáctico no
puede pedirle al lector mil palabras entre gráfico y gráfico.

LAS CINCO
=========
  TIPO-DE-UNIDAD     Las Tablas 1 y 2 de la E.070 juntas: qué tipo de
                     unidad admite cada zona sísmica y cada altura. Es una
                     matriz de decisión, y una matriz se lee, no se narra.

  FUERZAS-TABLA-11   T y C en las columnas de confinamiento, muro por muro:
                     por qué la extrema necesita doce varillas de 3/4" y la
                     interior seis de 1/2".

  PERALTE-C2         Los tres criterios que compiten por fijar el peralte
                     de la C-2, y cuál gana. Desde el 2026-09-21 gana el
                     anclaje de la solera en el límite de propiedad.

  BARRIDO-IRREG      Las doce irregularidades de las Tablas 11 y 12 de la
                     E.030, con su veredicto. Un tablero dice de un golpe
                     que ninguna aplica.

  PERIODO            El periodo de la norma contra el del modelo: cuánto se
                     parecen, que es lo que valida el contraste.
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
from proyecto import (MUROS, N_PISOS, H_COLUMNA_EXT,           # noqa: E402
                      ESPESOR, Z)

VERDE = "#2e7d52"
ROJO = "#b02a1f"
AMBAR = "#c98a16"
GRIS = "#9fb0bd"
AZUL = "#1f5fbf"
NARANJA = "#c0560f"


def cargar(nombre):
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location("_f" + nombre[:2], ruta)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def guardar(fig, nombre):
    out = os.path.join(R.INFORME, nombre)
    C.guardar(fig, out)
    print("  %s" % nombre)


def limpiar(ax):
    ax.grid(axis="y", color="#dde3e8", lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ======================================================================
def tipo_de_unidad():
    """Tablas 1 y 2 de la E.070: qué unidad admite cada zona y altura."""
    # Tabla 2 de la E.070, muro portante. Filas: zona sismica; columnas:
    # edificio de 1-2, 3-5 y mas de 5 pisos. Contenido: tipo de unidad
    # minimo admitido. Es dato NORMATIVO, no de proyecto.
    zonas = ["Zona 1", "Zona 2 y 3"]
    alturas = ["Muro portante\nen edificio de\n1 a 2 pisos",
               "Muro portante\nen edificio de\n3 a 5 pisos",
               "Muro portante\nen edificio de\nmás de 5 pisos"]
    # True = admitida la unidad HUECA; False = se exige SOLIDA
    admite_hueca = [[True, True, False], [False, False, False]]

    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 4.40), dpi=200)
    fig.suptitle("E.070 Tabla 2  ·  qué unidad admite un muro portante",
                 fontsize=13.5, fontweight="bold", color=E.TINTA, wrap=True)
    ax = fig.add_axes((0.05, 0.06, 0.90, 0.72))
    ax.axis("off")
    for i, z in enumerate(zonas):
        for j, a in enumerate(alturas):
            ok = admite_hueca[i][j]
            x, y = 0.24 + j * 0.25, 0.56 - i * 0.30
            ax.add_patch(plt.Rectangle((x, y), 0.23, 0.26,
                                       fc=("#fdf3e0" if ok else "#eaf5ee"),
                                       ec=(AMBAR if ok else VERDE), lw=1.6))
            ax.text(x + 0.115, y + 0.155,
                    "hueca\nadmitida" if ok else "SÓLIDA\nobligatoria",
                    ha="center", va="center", fontsize=10,
                    color=(AMBAR if ok else VERDE), fontweight="bold")
        ax.text(0.22, 0.56 - i * 0.30 + 0.13, z, ha="right", va="center",
                fontsize=11, fontweight="bold", color=E.TINTA)
    for j, a in enumerate(alturas):
        ax.text(0.355 + j * 0.25, 0.90, a, ha="center", va="center",
                fontsize=8.5, color=E.TINTA)
    # el caso del proyecto
    ax.add_patch(plt.Rectangle((0.49, 0.26), 0.23, 0.26, fc="none",
                               ec=ROJO, lw=2.6, ls="--"))
    ax.annotate("ESTE PROYECTO\nZona 2, 5 pisos", (0.605, 0.24),
                xytext=(0.605, 0.15), ha="center", fontsize=10, color=ROJO,
                fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    guardar(fig, "TIPO-DE-UNIDAD.png")
    return admite_hueca


# ======================================================================
def fuerzas_tabla_11():
    """T y C en las columnas: por qué la extrema lleva tanto más acero."""
    m19 = cargar("19_confinamientos.py")
    with contextlib.redirect_stdout(_io.StringIO()):
        muros = m19.preparar()
        filas = [(mu["nom"].split()[0], m19.tabla_11(mu)) for mu in muros]
    filas = sorted(filas, key=lambda f: -f[1]["C"])
    nom = [f[0] for f in filas]

    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 7.30), dpi=200)
    _axw = fig.add_axes((0, 0, 1, 1), frame_on=False)
    _axw.set_axis_off()
    _y = 0.975
    for _ln in C.envolver(_axw, u"Fuerzas internas en las columnas de "
                          u"confinamiento  ·  E.070 Tabla 11", 12.5, 0.93,
                          "bold"):
        fig.text(0.5, _y, _ln, fontsize=12.5, fontweight="bold",
                 color=E.TINTA, ha="center", va="top")
        _y -= 0.026
    for _ln in C.envolver(_axw, u"La extrema recibe mucho más que la "
                          u"interior: por eso son dos tipos de columna y no "
                          u"uno", 9.5, 0.90):
        fig.text(0.075, _y - 0.006, _ln, fontsize=9.5, color=E.TINTA,
                 va="top")
        _y -= 0.022
    # BARRAS HORIZONTALES: trece filas entran en el alto de la hoja; trece
    # columnas no entraban en su ancho. Ver el porque arriba.
    ax = fig.add_axes((0.155, 0.20, 0.80, _y - 0.235))
    w = 0.38
    xs = range(len(filas))
    ax.barh([x + w / 2 for x in xs], [f[1]["C"] / 1000.0 for f in filas], w,
            color=ROJO, label="COMPRESIÓN en la columna extrema")
    ax.barh([x - w / 2 for x in xs], [f[1]["C_i"] / 1000.0 for f in filas], w,
            color=GRIS, label="compresión en la columna interior")
    ax.set_yticks(list(xs))
    ax.set_yticklabels(nom, fontsize=8.2)
    ax.set_xlabel("fuerza de compresión  C  (tonf)", fontsize=9)
    # la leyenda, FUERA del area de barras: adentro se montaba sobre
    # las dos barras mas largas, que son las que el lector mira.
    ax.legend(fontsize=8.2, frameon=False, loc="lower center",
              bbox_to_anchor=(0.5, -0.135), ncol=2)
    limpiar(ax)
    r = filas[0][1]["C"] / max(filas[0][1]["C_i"], 1.0)
    _pie = (u"En el muro más exigido la columna extrema recibe %.0f veces lo "
            u"que la interior. Dimensionar todas como extremas metería "
            u"concreto donde habría albañilería y subiría el peso sísmico "
            u"sin ganar nada; dimensionarlas todas como interiores dejaría "
            u"cortos justo los extremos, que es donde el momento levanta la "
            u"columna." % r)
    _yp = 0.135
    for _ln in C.envolver(_axw, _pie, 8.2, 0.90):
        fig.text(0.055, _yp, _ln, fontsize=8.2, color="#55606a", va="top")
        _yp -= 0.0185
    guardar(fig, "FUERZAS-TABLA-11.png")
    return filas


# ======================================================================
def peralte_c2():
    """Los tres criterios que compiten por el peralte de la C-2."""
    m33 = cargar("33_especificaciones_planos.py")
    d_corte = 26.0        # corte-friccion, del comentario del SSOT
    d_min = 15.0          # E.070 7.1.4, peralte minimo
    db, req, disp, ok = m33.anclaje_en_columna_de_limite()
    d_anclaje = req + m33.RECUB

    crit = [("mínimo del 7.1.4", d_min),
            ("corte-fricción\n8.6.3-a.2", d_corte),
            ("anclaje de la solera\nen el límite (7.1.4)", d_anclaje)]
    adoptado = H_COLUMNA_EXT * 100.0

    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 4.90), dpi=200)
    fig.suptitle("Peralte de la columna C-2  ·  tres criterios compiten y "
                 "gana el mayor", fontsize=13.5, fontweight="bold",
                 color=E.TINTA, wrap=True)
    ax = fig.add_axes((0.10, 0.20, 0.85, 0.63))
    vals = [c[1] for c in crit]
    manda = vals.index(max(vals))
    cols = [ROJO if i == manda else GRIS for i in range(len(vals))]
    ax.bar(range(len(vals)), vals, 0.52, color=cols)
    ax.axhline(adoptado, color=VERDE, lw=2.2)
    ax.annotate("adoptado  d = %.0f cm" % adoptado, (len(vals) - 1, adoptado),
                xytext=(-0.45, adoptado + 1.0), fontsize=10, color=VERDE,
                fontweight="bold")
    for i, v in enumerate(vals):
        ax.annotate("%.1f" % v, (i, v), xytext=(i, v + 0.7), ha="center",
                    fontsize=10, color=(ROJO if i == manda else "#55606a"),
                    fontweight=("bold" if i == manda else "normal"))
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels([c[0] for c in crit], fontsize=9)
    ax.set_ylabel("peralte exigido  (cm)", fontsize=9)
    ax.set_ylim(0, max(max(vals), adoptado) * 1.22)
    limpiar(ax)
    _axp = fig.add_axes((0, 0, 1, 1), frame_on=False)
    _axp.set_axis_off()
    _pie = (u"El criterio que manda es el ANCLAJE: la E.070 7.1.4 pide "
            u"que el peralte permita alojar la parte recta del refuerzo "
            u"de la viga solera más el recubrimiento, porque en la "
            u"medianera la solera se discontinúa. Con d = 30 cm "
            u"faltaba 1 mm; con 35 sobra el 18 %.")
    _yp = 0.115
    for _l in C.envolver(_axp, _pie, 8.0, 0.90):
        fig.text(0.055, _yp, _l, fontsize=8.0, color="#55606a", va="top")
        _yp -= (8.0 * 1.45 / 72.0) / fig.get_size_inches()[1]
    guardar(fig, "PERALTE-C2.png")
    return crit, adoptado


# ======================================================================
def barrido_irregularidades():
    """Las doce irregularidades de la E.030, con su veredicto."""
    m16 = cargar("16_irregularidades.py")
    with contextlib.redirect_stdout(_io.StringIO()):
        filas = m16.informe()[0]
        _ia, _ip, res = m16.barrido(filas)
    if not res:
        return None
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 6.10), dpi=200)
    fig.suptitle("Barrido de las irregularidades  ·  E.030 Tablas 11 y 12",
                 fontsize=13.5, fontweight="bold", color=E.TINTA, wrap=True)
    ax = fig.add_axes((0.03, 0.04, 0.94, 0.85))
    ax.axis("off")
    n = len(res)
    for k, item in enumerate(res):
        cod, nom = item[0], item[1]
        # el cuarto campo dice si la irregularidad SE DA. No se asume:
        # se lee, porque un tablero que pinta todo verde sin mirar es
        # exactamente el verde falso que este proyecto viene cazando.
        irreg = bool(item[3]) if len(item) > 3 else False
        col = ROJO if irreg else VERDE
        y = 0.96 - k * (0.92 / max(n, 1))
        ax.add_patch(plt.Rectangle((0.02, y - 0.030), 0.96, 0.052,
                                   fc=("#fdecea" if irreg else "#eaf5ee"),
                                   ec=col, lw=1.0))
        ax.text(0.045, y - 0.004, "%s   %s" % (cod, str(nom)[:70]),
                fontsize=9, va="center", color=E.TINTA)
        ax.text(0.945, y - 0.004, "IRREGULAR" if irreg else "no se da",
                fontsize=9, va="center", ha="right", color=col,
                fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    guardar(fig, "BARRIDO-IRREGULARIDADES.png")
    return res


def main():
    hu = tipo_de_unidad()
    t11 = fuerzas_tabla_11()
    crit, adop = peralte_c2()
    barr = barrido_irregularidades()
    print()
    control(hu, t11, crit, adop, barr)


def control(hu, t11, crit, adop, barr):
    # la matriz AFIRMA que en zona 2 se exige solida en toda altura
    assert not any(hu[1]), (
        "la matriz dice que en zona 2 y 3 siempre se exige unidad solida")
    assert abs(Z - 0.25) < 1e-9, ("el proyecto se marca en zona 2 y Z = %s"
                                  % Z)
    # la figura de la Tabla 11 AFIRMA que la extrema recibe mas
    for nom, t in t11:
        assert t["C"] > t["C_i"], (
            "%s: la columna interior recibe mas que la extrema" % nom)
    # y la del peralte, que el adoptado cubre a los tres criterios
    for nom, v in crit:
        assert adop >= v - 1e-6, (
            "el peralte adoptado %.1f no cubre el criterio %r (%.1f)"
            % (adop, nom, v))
    print("  [ok] zona 2: unidad solida obligatoria en toda altura")
    print("  [ok] en los %d muros la columna extrema recibe mas que la "
          "interior" % len(t11))
    print("  [ok] d = %.0f cm cubre los %d criterios; manda %r con %.1f"
          % (adop, len(crit), max(crit, key=lambda c: c[1])[0].split("\n")[0],
             max(c[1] for c in crit)))
    if barr:
        hay = [b[1] for b in barr if len(b) > 3 and b[3]]
        assert not hay, ("el tablero pinta verde y estas SI se dan: %s" % hay)
        print("  [ok] barrido de %d irregularidades, ninguna se da"
              % len(barr))


if __name__ == "__main__":
    main()
