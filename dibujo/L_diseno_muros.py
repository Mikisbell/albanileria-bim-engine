# -*- coding: utf-8 -*-
"""E-02: diseno de muros — el plano que se LEE junto al calculo.

QUE PIDE LA RUBRICA, LITERAL
============================
Criterio 8: *"Disena los muros portantes de forma pertinentes y realiza las
verificaciones de forma completa. El diseno sera PLASMADO EN PLANOS."*

Y lo que castiga, repetido en tres criterios distintos: *"el plano carece de
una buena interpretacion"* y *"no se relaciona con su diseno"*.

Esas dos frases son el encargo de esta lamina, y son verificables:

  INTERPRETACION   se entiende mirando, sin que nadie lo explique. Cada muro
                   lleva su nombre sobre si mismo y su color dice como anda.

  SE RELACIONA     cada muro del dibujo tiene su fila en el cuadro, con los
                   numeros que salen del script 18: L, Ln, alfa, Vm1, Ve1 y
                   el cociente del 8.5.2. Nadie tiene que buscar en otro
                   documento de donde sale nada.

COMO SE LEE
===========
El color de cada muro es su Ve/(0,55 Vm) del 8.5.2 — cuanto le falta para
agrietarse bajo sismo moderado. Verde holgado, ambar ajustado, rojo si
incumpliera. El que GOBIERNA lleva marca: es el que decide si el edificio
pasa o no.
"""
import contextlib
import importlib.util
import io as _io
import os
import sys
from pathlib import Path

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))
sys.path.insert(0, AQUI)

import paleta as PAL
import rutas as R                                            # noqa: E402
from lamina import Lamina, A3_MM                             # noqa: E402
from meta import meta                                        # noqa: E402
from proyecto import (FRENTE, FONDO, ESPESOR, EJES_MX, MUROS,  # noqa: E402
                      POZO_X0, POZO_X1, POZO_Y0, POZO_Y1,
                      N_PISOS, RETIRO_LATERAL, FRENTE_LOTE)

ESCALA = 100   # a 1:150 sobraba un tercio de hoja

# Semaforo del 8.5.2. El limite normativo es 1,00; los cortes de color son
# de LECTURA, no de norma, y por eso se declaran acá y no en el SSOT.
VERDE = "#2e7d52"
AMBAR = "#c98a16"
ROJO = "#b02a1f"
CORTE_HOLGADO = 0.50     # por debajo: sobra resistencia
CORTE_AJUSTADO = 0.85    # entre 0,50 y 0,85: cumple pero sin lujo


def _cargar(nombre):
    """Importa un script de calculo que empieza con digito, sin imprimir."""
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location("_c_" + nombre[:2], ruta)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def datos():
    """Los muros ya disenados, con el cociente del 8.5.2 de cada uno."""
    m18 = _cargar("18_diseno_muros.py")
    with contextlib.redirect_stdout(_io.StringIO()):
        muros, _ad = m18.disenar()
    filas = []
    for mu in muros:
        Vm1 = mu["Vm1"]
        Ve1 = mu["Ve"][0]
        ratio = Ve1 / (0.55 * Vm1)
        filas.append({
            "nom": mu["nom"].split()[0],
            "dir": mu["dir"],
            "L": mu["L"], "Ln": mu["Ln"],
            "alfa": mu["alfa"][0], "Vm1": Vm1, "Ve1": Ve1,
            "ratio": ratio,
        })
    return filas


def color_de(ratio):
    if ratio >= 1.0:
        return ROJO
    if ratio >= CORTE_AJUSTADO:
        return AMBAR
    if ratio >= CORTE_HOLGADO:
        return AMBAR
    return VERDE


def _origen(nom, dire):
    """(x, y) del arranque del muro, encajado dentro del frente edificado."""
    e = ESPESOR / 2.0
    if dire == "X":
        y = EJES_MX[int(nom.split("-")[1][0]) - 1]
        y = e if y == 0.0 else (FONDO - e if y == FONDO else y)
        return 0.0, y
    x = {"MY-1": 0.0, "MY-2": FRENTE, "MY-3": POZO_X0, "MY-4": POZO_X1}[nom[:4]]
    x = e if x == 0.0 else (FRENTE - e if x == FRENTE else x)
    return x, (POZO_Y1 if nom[4:5] == "b" else 0.0)


def planta(L, filas):
    """La reticula pintada segun como anda cada muro en el 8.5.2."""
    por_nom = {f["nom"]: f for f in filas}
    gob = max(filas, key=lambda f: f["ratio"])
    # MY-1 y MY-2 son simetricas y dan EXACTAMENTE el mismo cociente.
    # Marcar solo una hacia preguntarse por que esa y no la otra: si
    # empatan, gobiernan las dos.
    gobiernan = {f["nom"] for f in filas
                 if abs(f["ratio"] - gob["ratio"]) < 1e-9}
    e = ESPESOR / 2.0
    for nom, dire, largo, t_, vs in MUROS:
        corto = nom.split()[0]
        f = por_nom[corto]
        ox, oy = _origen(corto, dire)
        col = color_de(f["ratio"])
        if dire == "X":
            L.rect(ox, oy - e, ox + largo, oy + e, layer="MUROS",
                   fc=col, ec=PAL.MURO_BORDE, lw=0.7)
            L.texto((ox + largo * 0.5, oy), corto, h_mm=2.0, layer="TEXTO",
                    color="white", weight="bold", zorder=20)
        else:
            L.rect(ox - e, oy, ox + e, oy + largo, layer="MUROS",
                   fc=col, ec=PAL.MURO_BORDE, lw=0.7)
            L.texto((ox, oy + largo * 0.5), corto, h_mm=2.0, layer="TEXTO",
                    rot=90, color="white", weight="bold", zorder=20)
        if corto in gobiernan:
            # el que decide: se marca, porque es el que hay que mirar
            if dire == "X":
                L.rect(ox - 0.18, oy - e - 0.18, ox + largo + 0.18,
                       oy + e + 0.18, layer="COTAS", fc="none",
                       ec=PAL.LIMITE, color=PAL.LIMITE, lw=1.6,
                       ls=(0, (5, 2)))
            else:
                L.rect(ox - e - 0.18, oy - 0.18, ox + e + 0.18,
                       oy + largo + 0.18, layer="COTAS", fc="none",
                       ec=PAL.LIMITE, color=PAL.LIMITE, lw=1.6,
                       ls=(0, (5, 2)))
    # el pozo, para que la planta se reconozca
    L.rect(POZO_X0, POZO_Y0, POZO_X1, POZO_Y1, layer="VACIO", fc="none",
           ec=PAL.GUIA, lw=0.6, ls=(0, (3, 2)))
    L.texto(((POZO_X0 + POZO_X1) / 2.0, (POZO_Y0 + POZO_Y1) / 2.0),
            "POZO", h_mm=2.0, layer="TEXTO", color="#7a7a7a")
    return gob, gobiernan


def cuadro_de_muros(L, filas, gobiernan, x_mm, y_mm):
    """Cada muro del dibujo, con los numeros que lo aprueban.

    Esta tabla es la respuesta literal a *"no se relaciona con su diseno"*:
    el nombre que esta pintado en la planta es el mismo de la primera
    columna, y de ahi para la derecha esta todo lo que hizo falta para
    decir que cumple.
    """
    fil = []
    for f in sorted(filas, key=lambda z: (z["dir"], z["nom"])):
        marca = " <" if f["nom"] in gobiernan else ""
        fil.append([f["nom"] + marca, f["dir"],
                    "%.2f" % f["L"], "%.2f" % f["Ln"],
                    "%.2f" % f["alfa"],
                    "%.0f" % (f["Vm1"] / 1000.0),
                    "%.0f" % (f["Ve1"] / 1000.0),
                    "%.3f" % f["ratio"]])
    return L.cuadro(
        x_mm=x_mm, y_mm=y_mm,
        titulo="VERIFICACION POR MURO      E.070 8.5.2",
        encabezado=["MURO", "D", "L", "Ln", "a", "Vm1", "Ve1", "Ve/0,55Vm"],
        filas=fil,
        anchos_mm=[16.0, 7.0, 12.0, 12.0, 10.0, 13.0, 13.0, 20.0],
        h_fila=4.3, h_txt=1.8,
        nota="L y Ln en m; Vm1 y Ve1 en toneladas-fuerza. Ln es la suma de "
             "los machones: el 6.4 hace que un vano parta el muro, y es Ln "
             "—no L— la que entra en Vm = 0,5 v'm a t Ln + 0,23 Pg. El "
             "cociente de la ultima columna es el control del 8.5.2: "
             "Ve <= 0,55 Vm, o sea que el muro NO se agrieta con el sismo "
             "moderado. Menor es mejor; el marcado con < es el que gobierna.",
    )


def guia_de_lectura(L, x_mm, y_mm, gob):
    """Como se lee esta lamina. Va en la hoja porque el plano viaja solo."""
    lineas = [
        "1.  El COLOR de cada muro es su Ve/(0,55 Vm) del 8.5.2: cuanto",
        "    le falta para agrietarse con el sismo moderado.",
        "2.  Los muros con marco punteado son los que GOBIERNAN, con",
        "    %.3f. Si esos cumplen, cumplen todos." % gob["ratio"],
        "3.  Cada muro pintado tiene su fila en el cuadro, con el mismo",
        "    nombre. De ahi sale cada numero que lo aprueba.",
        "4.  Los muros en Y son mas largos y por eso toman mas cortante:",
        "    las medianeras corren los %.2f m del fondo." % FONDO,
    ]
    L.h_texto((x_mm, y_mm), "COMO SE LEE ESTA LAMINA", h_mm=2.6,
              ha="left", va="top", weight="bold")
    for k, ln in enumerate(lineas):
        L.h_texto((x_mm, y_mm - 5.4 - k * 3.4), ln, h_mm=1.9, ha="left",
                  va="top")
    L._cajas_hoja.append(("GUIA DE LECTURA", x_mm, y_mm - 5.4 - len(lineas) * 3.4,
                          x_mm + 72.0, y_mm))
    return y_mm - 5.4 - len(lineas) * 3.4


def construir():
    filas = datos()
    L = Lamina(
        codigo="E-02",
        titulo="DISENO DE MUROS PORTANTES",
        subtitulo=("Verificacion del 8.5.2 muro por muro: el color dice como "
                   "anda cada uno y el cuadro dice por que. Pisos 1 a %d."
                   % N_PISOS),
        escala=ESCALA,
        meta=meta(),
        nota_pie="Numeros leidos de calculo/18_diseno_muros.py",
    )
    L.encuadrar(-2.2, FRENTE + 2.2, -2.2, FONDO + 2.2,
                centro_mm=(100.0, 150.0))
    gob, gobiernan = planta(L, filas)

    L.leyenda_add(VERDE, "MUROS", "Ve/0,55Vm < %.2f  holgado" % CORTE_HOLGADO)
    L.leyenda_add(AMBAR, "MUROS", "entre %.2f y 1,00  cumple ajustado"
                  % CORTE_HOLGADO)
    L.leyenda_add(ROJO, "MUROS", ">= 1,00  NO cumple el 8.5.2")
    L.leyenda_add(PAL.LIMITE, "COTAS",
                  "marco punteado = el muro que GOBIERNA")
    L.leyenda_dibujar(x_mm=196.0, y_mm=288.0, ancho_mm=72.0)

    y = L.cuadro(
        x_mm=196.0, y_mm=L._caja_leyenda[1] - 8.0,
        titulo="RESUMEN DEL CRITERIO 8",
        encabezado=["CONCEPTO", "VALOR"],
        filas=[
            ["Muros verificados", str(len(filas))],
            ["Cumplen el 8.5.2", str(sum(1 for f in filas
                                         if f["ratio"] < 1.0))],
            ["Muro(s) que gobierna(n)", ", ".join(sorted(gobiernan))],
            ["su Ve/(0,55 Vm)", "%.3f" % gob["ratio"]],
            ["Margen al limite", "%.1f %%" % ((1.0 - gob["ratio"]) * 100)],
        ],
        anchos_mm=[46.0, 26.0], h_fila=4.4, h_txt=1.85,
    )
    y = cuadro_de_muros(L, filas, gobiernan, 196.0, y - 8.0)
    guia_de_lectura(L, 196.0, y - 8.0, gob)

    L.escala_grafica(x_mm=12.0, y_mm=16.0, metros=5)
    L.norte(x_mm=160.0, y_mm=272.0)
    L.cajetin()
    return L, filas, gob, gobiernan


def control(L, filas, gob, gobiernan):
    """Que la lamina diga lo mismo que el calculo, y que se pueda leer."""
    assert len(filas) == len(MUROS), (
        "se verificaron %d muros y el SSOT declara %d"
        % (len(filas), len(MUROS)))

    # el gobernante es el de mayor cociente, no el que a uno le parezca
    peor = max(f["ratio"] for f in filas)
    esperados = {f["nom"] for f in filas if abs(f["ratio"] - peor) < 1e-9}
    assert gobiernan == esperados, (
        "se marcaron %s y los de mayor cociente son %s"
        % (sorted(gobiernan), sorted(esperados)))

    # y TODOS tienen que cumplir: si alguno no, la lamina no se emite
    malos = [f["nom"] for f in filas if f["ratio"] >= 1.0]
    assert not malos, ("estos muros no cumplen el 8.5.2: %s" % malos)

    # cada muro pintado tiene que tener su fila, y al reves
    pintados = {m[0].split()[0] for m in MUROS}
    tabulados = {f["nom"] for f in filas}
    assert pintados == tabulados, (
        "el dibujo y el cuadro no hablan del mismo conjunto: %s"
        % (pintados ^ tabulados))

    ch = L.control_hoja()
    assert not ch, ("bloques de hoja que se pisan: %s"
                    % ["%s / %s" % (c[0], c[1]) for c in ch])
    for nom, x0, y0, x1, y1 in L._cajas_hoja:
        assert (6.0 <= x0 and x1 <= A3_MM[0] - 6.0
                and 6.0 <= y0 and y1 <= A3_MM[1] - 6.0), (
            "el bloque %r se sale de la hoja: x[%.1f, %.1f] y[%.1f, %.1f]"
            % (nom, x0, x1, y0, y1))

    print("  [ok] %d muros verificados, %d cumplen el 8.5.2"
          % (len(filas), sum(1 for f in filas if f["ratio"] < 1.0)))
    print("  [ok] gobierna %s con %.3f (margen %.1f %%)"
          % (gob["nom"], gob["ratio"], (1.0 - gob["ratio"]) * 100))
    print("  [ok] %d bloques de hoja, ninguno se pisa ni se sale"
          % len(L._cajas_hoja))


def main():
    L, filas, gob, gobiernan = construir()
    salidas = L.render(Path(R.LAMINAS), dpi=200, dxf_dir=Path(R.CAD))
    # La figura del informe se compone para la PAGINA (ver
    # lamina.py::render_figura): el DXF y la lamina completa
    # siguen saliendo a tamano de hoja, que es donde van.
    salidas["fig"] = L.render_figura(
        Path(R.INFORME), dpi=200,
        ancho_pagina=6.30, alto_pagina=8.86,
        cota_min_m=1.20)
    print()
    for k, p in salidas.items():
        print("  %-5s %s  (%d KB)" % (k, p.name, p.stat().st_size // 1024))
    print()
    print("  escala 1:%d, hoja A3 (%.0f x %.0f mm)"
          % (ESCALA, A3_MM[0], A3_MM[1]))
    control(L, filas, gob, gobiernan)


if __name__ == "__main__":
    main()
