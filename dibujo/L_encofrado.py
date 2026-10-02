# -*- coding: utf-8 -*-
"""E-04: encofrado de losa, vigas y soleras.

QUE PIDE LA CONSIGNA, LITERAL
=============================
Criterio 2: *"Presenta un predimensionamiento de zapatas, cimentacion
corrida, muros, VIGAS, columnas y LOSA con calculos correctos y los plasma
adecuadamente en un plano."*

Y San Bartolome, Quiun y Silva (2015) §7.3, plano de encofrados: *"Deben
proporcionarse las caracteristicas de la losa de techo y el detalle de su
refuerzo. Asimismo, deben identificarse las VIGAS SOLERAS (Si), efectuando
cortes y elevaciones que muestren sus caracteristicas."*

LO QUE ESTA LAMINA ENSENA
=========================
Dos cosas que en una planta de arquitectura no se ven:

  EL SENTIDO DE ARMADO. El aligerado arma sus viguetas en el sentido del
  FONDO (Y), salvando de muro transversal a muro transversal. Eso decide
  que muro recibe carga de losa y cual no, y por eso esta dibujado con las
  viguetas, no escrito en una nota.

  QUE HAY SOBRE CADA MURO. Sobre todos corre la viga solera VS-1, que es el
  confinamiento horizontal del 7.2.1.a. En los dos bordes libres del pozo
  no hay muro: ahi va la viga VB-1, que el calculo dimensiono con la Tabla
  9.1 de la E.060.
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

import rutas as R                                            # noqa: E402
from lamina import Lamina, A3_MM                             # noqa: E402
from meta import meta                                        # noqa: E402
from proyecto import (FRENTE, FONDO, ESPESOR, EJES_MX, MUROS,  # noqa: E402
                      POZO_X0, POZO_X1, POZO_Y0, POZO_Y1,
                      E_LOSA, H_SOLERA, N_PISOS, PANOS_Y,
                      ESC_X0, ESC_X1, ESC_Y0, ESC_Y1)

ESCALA = 125
SEP_VIGUETAS = 0.40      # m entre ejes, E.020 anexo 1 (el mismo del 10)
E_LOSETA = 0.05          # m, losa superior del aligerado
B_ALMA = 0.10            # m, ancho del alma de la vigueta
VIGA_B, VIGA_H = 0.24, 0.30      # VB-1, del script 08
LOSA = "#dfe6ec"
VIGUETA = "#aebfcc"
SOLERA_C = "#1e7a46"
VIGA_C = "#c0560f"


def paños_de_losa():
    """Los rectangulos de losa entre muros transversales, sin el pozo.

    La losa NO es un rectangulo unico: el pozo y la caja de escalera son
    huecos, y el sentido de armado se dibuja pano por pano.
    """
    out = []
    for k in range(len(EJES_MX) - 1):
        y0, y1 = EJES_MX[k], EJES_MX[k + 1]
        out.append((0.0, y0, FRENTE, y1, y1 - y0))
    return out


def losa(L):
    """Los panos con sus viguetas dibujadas en el sentido real."""
    n_pan = n_vig = 0
    for x0, y0, x1, y1, luz in paños_de_losa():
        L.rect(x0, y0, x1, y1, layer="LOSA", fc=LOSA, ec="#9fb0bd", lw=0.4)
        n_pan += 1
        # las viguetas, en el sentido del FONDO (Y)
        x = x0 + SEP_VIGUETAS / 2.0
        while x < x1 - 1e-9:
            def _solapa(a0, a1, b0, b1):
                return a0 < b1 - 1e-9 and b0 < a1 - 1e-9

            en_pozo = (POZO_X0 <= x <= POZO_X1
                       and _solapa(y0, y1, POZO_Y0, POZO_Y1))
            en_esc = (ESC_X0 <= x <= ESC_X1
                      and _solapa(y0, y1, ESC_Y0, ESC_Y1))
            if not en_pozo and not en_esc:
                L.linea((x, y0), (x, y1), layer="LOSA", color="#7e91a1",
                        lw=0.35)
                n_vig += 1
            x += SEP_VIGUETAS
        L.texto((x0 + (x1 - x0) * 0.07, (y0 + y1) / 2.0),
                "L = %.2f m" % luz, h_mm=1.9, layer="TEXTO",
                color="#4a5a68", ha="left")
    # los huecos
    for a, b, c, d, txt in ((POZO_X0, POZO_Y0, POZO_X1, POZO_Y1, "POZO"),
                            (ESC_X0, ESC_Y0, ESC_X1, ESC_Y1, "ESCALERA")):
        L.rect(a, b, c, d, layer="VACIO", fc="white", ec="#6b7075", lw=0.8)
        L.texto(((a + c) / 2.0, (b + d) / 2.0), txt, h_mm=2.0, layer="TEXTO",
                color="#6b7075")
    return n_pan, n_vig


def soleras_y_vigas(L):
    """VS-1 sobre cada muro; VB-1 en los dos bordes libres del pozo."""
    e = ESPESOR / 2.0
    n_s = 0
    for nom, dire, largo, t_, vs in MUROS:
        corto = nom.split()[0]
        if dire == "X":
            y = EJES_MX[int(corto.split("-")[1][0]) - 1]
            y = e if y == 0.0 else (FONDO - e if y == FONDO else y)
            L.rect(0.0, y - e, largo, y + e, layer="VIGAS", fc="none",
                   ec=SOLERA_C, lw=1.3)
        else:
            x = {"MY-1": 0.0, "MY-2": FRENTE,
                 "MY-3": POZO_X0, "MY-4": POZO_X1}[corto[:4]]
            x = e if x == 0.0 else (FRENTE - e if x == FRENTE else x)
            y0 = POZO_Y1 if corto[4:5] == "b" else 0.0
            L.rect(x - e, y0, x + e, y0 + largo, layer="VIGAS", fc="none",
                   ec=SOLERA_C, lw=1.3)
        n_s += 1
    # VB-1: los bordes ESTE y OESTE del pozo, donde no hay muro
    n_v = 0
    for x in (POZO_X0, POZO_X1):
        L.rect(x - VIGA_B / 2.0, POZO_Y0, x + VIGA_B / 2.0, POZO_Y1,
               layer="VIGAS", fc=VIGA_C, ec="#7a3609", lw=1.0, alpha=0.8)
        L.texto((x, (POZO_Y0 + POZO_Y1) / 2.0), "VB-1", h_mm=1.9,
                layer="TEXTO", rot=90, color="white", weight="bold",
                zorder=20)
        n_v += 1
    return n_s, n_v


def corte_vigueta(L, x_mm, y_mm, esc=12.5):
    """La seccion del aligerado, acotada. Es el detalle que la rubrica pide."""
    def mm(v):
        return v * 1000.0 / esc

    L.h_texto((x_mm, y_mm), "CORTE DEL ALIGERADO  esc. 1:%.0f" % esc,
              h_mm=2.4, ha="left", va="top", weight="bold")
    y0 = y_mm - 30.0
    x = x_mm + 4.0
    # dos viguetas con su ladrillo
    for k in range(2):
        xa = x + k * mm(SEP_VIGUETAS)
        # alma
        L.h_rect(xa, y0, xa + mm(B_ALMA), y0 + mm(E_LOSA - E_LOSETA),
                 layer="CAJETIN", fc=VIGUETA, ec="#5b6c7a", lw=0.7)
        # ladrillo de techo
        L.h_rect(xa + mm(B_ALMA), y0,
                 xa + mm(SEP_VIGUETAS), y0 + mm(E_LOSA - E_LOSETA),
                 layer="CAJETIN", fc="#efe3cf", ec="#b9a888", lw=0.5)
    # la loseta superior, continua
    L.h_rect(x, y0 + mm(E_LOSA - E_LOSETA),
             x + 2 * mm(SEP_VIGUETAS), y0 + mm(E_LOSA),
             layer="CAJETIN", fc=VIGUETA, ec="#5b6c7a", lw=0.7)
    # cotas
    L.h_linea((x, y0 - 3.0), (x + mm(SEP_VIGUETAS), y0 - 3.0),
              layer="CAJETIN", color="#00808a", lw=0.8)
    L.h_texto((x + mm(SEP_VIGUETAS) / 2.0, y0 - 4.2),
              "%.2f" % SEP_VIGUETAS, h_mm=1.8, ha="center", va="top",
              color="#00808a")
    L.h_linea((x + 2 * mm(SEP_VIGUETAS) + 3.0, y0),
              (x + 2 * mm(SEP_VIGUETAS) + 3.0, y0 + mm(E_LOSA)),
              layer="CAJETIN", color="#00808a", lw=0.8)
    L.h_texto((x + 2 * mm(SEP_VIGUETAS) + 4.5, y0 + mm(E_LOSA) / 2.0),
              "h = %.2f" % E_LOSA, h_mm=1.8, ha="left", va="center",
              color="#00808a")
    L.h_texto((x, y0 + mm(E_LOSA) + 3.0),
              "loseta %.2f  -  alma %.2f  -  ladrillo de techo"
              % (E_LOSETA, B_ALMA), h_mm=1.7, ha="left", va="bottom")


def construir():
    L = Lamina(
        codigo="E-04",
        titulo="ENCOFRADO DE LOSA, VIGAS Y SOLERAS",
        subtitulo=("Aligerado h = %.2f m armado en el sentido del fondo. "
                   "Viga solera VS-1 sobre cada muro y viga VB-1 en los "
                   "bordes libres del pozo. Pisos 1 a %d."
                   % (E_LOSA, N_PISOS)),
        escala=ESCALA,
        meta=meta(),
        nota_pie="Numeros leidos de calculo/10_metrado_losas.py y del 08",
    )
    L.encuadrar(-2.4, FRENTE + 2.4, -2.4, FONDO + 2.4,
                centro_mm=(78.0, 152.0))
    n_pan, n_vig = losa(L)
    n_s, n_v = soleras_y_vigas(L)

    L.leyenda_add(LOSA, "LOSA", "Losa aligerada h = %.2f m" % E_LOSA)
    L.leyenda_add(SOLERA_C, "VIGAS", "Viga solera VS-1 (%.2f x %.2f m)"
                  % (ESPESOR, H_SOLERA))
    L.leyenda_add(VIGA_C, "VIGAS", "Viga VB-1 (%.2f x %.2f m)"
                  % (VIGA_B, VIGA_H))
    L.leyenda_add("white", "VACIO", "Hueco: pozo de luz y escalera")
    L.leyenda_dibujar(x_mm=170.0, y_mm=288.0, ancho_mm=76.0)

    y = L.cuadro(
        x_mm=170.0, y_mm=L._caja_leyenda[1] - 8.0,
        titulo="CUADRO DE ELEMENTOS HORIZONTALES",
        encabezado=["ELEM", "SECCION", "DONDE", "CRITERIO"],
        filas=[
            ["VS-1", "%.2f x %.2f" % (ESPESOR, H_SOLERA),
             "sobre cada muro", "7.2.4: h >= e losa"],
            ["VB-1", "%.2f x %.2f" % (VIGA_B, VIGA_H),
             "bordes del pozo", "E.060 T. 9.1: L/16"],
            ["Losa", "h = %.2f" % E_LOSA, "todos los panos",
             "luz maxima %.2f m" % max(PANOS_Y)],
        ],
        anchos_mm=[12.0, 16.0, 22.0, 26.0], h_fila=4.3, h_txt=1.7,
        nota="La VS-1 no es una viga de carga: es el CONFINAMIENTO "
             "HORIZONTAL que el 7.2.1.a exige para que el muro cuente como "
             "confinado, y por eso corre sobre todos. La VB-1 si carga: "
             "toma el canto libre del aligerado en los dos bordes del pozo "
             "donde no hay muro, con luz de %.2f m apoyada en MX-3 y MX-4."
             % (POZO_Y1 - POZO_Y0),
    )
    with L.bloque_hoja("CORTE ALIGERADO", margen_mm=2.0):
        corte_vigueta(L, 170.0, y - 8.0)

    L.escala_grafica(x_mm=12.0, y_mm=16.0, metros=5)
    L.norte(x_mm=140.0, y_mm=272.0)
    L.cajetin()
    return L, n_pan, n_vig, n_s, n_v


def control(L, n_pan, n_vig, n_s, n_v):
    assert n_pan == len(EJES_MX) - 1, (
        "se dibujaron %d panos y los ejes transversales dan %d"
        % (n_pan, len(EJES_MX) - 1))
    assert n_s == len(MUROS), (
        "hay %d soleras para %d muros: el 7.2.1.a las pide sobre TODOS"
        % (n_s, len(MUROS)))
    assert n_v == 2, ("las VB-1 son dos, una por borde libre: %d" % n_v)
    assert n_vig > 0, "no se dibujo ninguna vigueta"

    # la luz de la VB-1 tiene que ser la del pano del pozo
    luz = POZO_Y1 - POZO_Y0
    assert abs(luz - PANOS_Y[2]) < 1e-9, (
        "la luz de la VB-1 (%.2f) no es la del pano del pozo (%.2f)"
        % (luz, PANOS_Y[2]))
    # y su peralte, el de la Tabla 9.1 para simplemente apoyada
    assert VIGA_H >= luz / 16.0 - 1e-9, (
        "VB-1 con h = %.2f no llega al L/16 = %.3f de la Tabla 9.1"
        % (VIGA_H, luz / 16.0))
    # la solera, al menos el espesor de la losa (7.2.4)
    assert H_SOLERA >= E_LOSA - 1e-9, (
        "la solera h = %.2f no llega al espesor de losa %.2f (7.2.4)"
        % (H_SOLERA, E_LOSA))

    ch = L.control_hoja()
    assert not ch, ("bloques de hoja que se pisan: %s"
                    % ["%s / %s" % (c[0], c[1]) for c in ch])
    for nom, x0, y0, x1, y1 in L._cajas_hoja:
        assert (6.0 <= x0 and x1 <= A3_MM[0] - 6.0
                and 6.0 <= y0 and y1 <= A3_MM[1] - 6.0), (
            "el bloque %r se sale de la hoja" % nom)

    print("  [ok] %d panos de losa con %d viguetas en el sentido del fondo"
          % (n_pan, n_vig))
    print("  [ok] %d soleras VS-1 (una por muro, 7.2.1.a) y %d vigas VB-1"
          % (n_s, n_v))
    print("  [ok] VB-1 h = %.2f >= L/16 = %.3f (E.060 Tabla 9.1)"
          % (VIGA_H, luz / 16.0))
    print("  [ok] %d bloques de hoja, ninguno se pisa ni se sale"
          % len(L._cajas_hoja))


def main():
    L, n_pan, n_vig, n_s, n_v = construir()
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
    print("  escala 1:%d, hoja A3" % ESCALA)
    control(L, n_pan, n_vig, n_s, n_v)


if __name__ == "__main__":
    main()
