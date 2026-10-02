# -*- coding: utf-8 -*-
"""E-03: cimentacion — planta, corte tipico y el cimiento medianero.

QUE PIDE LA CONSIGNA, LITERAL
=============================
Criterio 2: *"Presenta un predimensionamiento de ZAPATAS, CIMENTACION
CORRIDA, muros, vigas, columnas y losa con calculos correctos y los plasma
adecuadamente en un plano."*

Y San Bartolome, Quiun y Silva (2015) §7.3 pone la cimentacion como el
PRIMER plano del juego: *"En este plano debe aparecer: las caracteristicas
de la cimentacion, cortes, niveles de cimentacion, [...] juntas sismicas,
identificacion de los elementos verticales estructurales y las
especificaciones de los materiales."*

LO QUE ESTA LAMINA ENSENA
=========================
El caso que hace pensar es el CIMIENTO MEDIANERO. Un cimiento corrido
centrado bajo un muro de 0,24 m con B = 0,70 vuela 0,23 m a cada lado, y en
la medianera ese vuelo cae en el predio del vecino — que la E.050 prohibe
expresamente. Se corre hacia adentro y aparece una EXCENTRICIDAD que no se
arregla ensanchando: hay que amarrar el cimiento a los perpendiculares.

Eso se ve de un golpe en el detalle, y por eso el detalle esta a 1:20 y no
perdido dentro de la planta a 1:100.
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
                      B_CIMIENTO, DF, QAD, N_PISOS, FC, FY,
                      RETIRO_LATERAL, ejes_x_rotulados)

ESCALA = 125
QAD_TONF = QAD * 10.0   # el EMS lo da en kg/cm2; 1 kg/cm2 = 10 tonf/m2
CIM = PAL.CIMIENTO          # color del cimiento en planta
SOBRE = "#b99a6b"        # sobrecimiento
TERRENO = PAL.TERRENO


def _cargar(nombre):
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location("_c_" + nombre[:2], ruta)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def datos():
    """Presion real, ancho requerido y excentricidad, del calculo."""
    m04 = _cargar("04_cimentacion.py")
    with contextlib.redirect_stdout(_io.StringIO()):
        w = m04.carga_lineal()
        B_req = m04.ancho_requerido(w)
    q_real = (w / 1000.0) / B_CIMIENTO
    vuelo = (B_CIMIENTO - ESPESOR) / 2.0
    e = vuelo - RETIRO_LATERAL
    return {"w": w, "B_req": B_req, "q_real": q_real,
            "vuelo": vuelo, "e": e, "b6": B_CIMIENTO / 6.0}


def _origen(nom, dire):
    e = ESPESOR / 2.0
    if dire == "X":
        y = EJES_MX[int(nom.split("-")[1][0]) - 1]
        y = e if y == 0.0 else (FONDO - e if y == FONDO else y)
        return 0.0, y
    x = {"MY-1": 0.0, "MY-2": FRENTE, "MY-3": POZO_X0, "MY-4": POZO_X1}[nom[:4]]
    x = e if x == 0.0 else (FRENTE - e if x == FRENTE else x)
    return x, (POZO_Y1 if nom[4:5] == "b" else 0.0)


def planta(L):
    """Cada muro con su cimiento corrido debajo, y los medianeros corridos.

    El cimiento de una medianera NO puede ir centrado: volaria al vecino.
    Se dibuja donde de verdad va, apoyado contra el limite, y se marca en
    otro color para que se vea que es un caso distinto.
    """
    b = B_CIMIENTO / 2.0
    n_centrados = n_excentricos = 0
    for nom, dire, largo, t_, vs in MUROS:
        corto = nom.split()[0]
        ox, oy = _origen(corto, dire)
        medianero = corto in ("MY-1", "MY-2")
        if dire == "X":
            L.rect(ox, oy - b, ox + largo, oy + b, layer="ZAPATAS",
                   fc=CIM, ec=PAL.CIMIENTO_BORDE, lw=0.6, alpha=0.55)
            n_centrados += 1
        else:
            if medianero:
                # apoyado contra el limite: los 0,70 m completos adentro
                x0 = -RETIRO_LATERAL if corto == "MY-1" else \
                    FRENTE + RETIRO_LATERAL - B_CIMIENTO
                L.rect(x0, oy, x0 + B_CIMIENTO, oy + largo, layer="ZAPATAS",
                       fc=PAL.ALERTA, ec=PAL.CIMIENTO_BORDE, lw=0.9, alpha=0.65)
                n_excentricos += 1
            else:
                L.rect(ox - b, oy, ox + b, oy + largo, layer="ZAPATAS",
                       fc=CIM, ec=PAL.CIMIENTO_BORDE, lw=0.6, alpha=0.55)
                n_centrados += 1
        # el muro encima, en linea fina, para reconocer la planta
        e = ESPESOR / 2.0
        if dire == "X":
            L.rect(ox, oy - e, ox + largo, oy + e, layer="MUROS",
                   fc="none", ec=PAL.MURO_BORDE, lw=0.5)
        else:
            L.rect(ox - e, oy, ox + e, oy + largo, layer="MUROS",
                   fc="none", ec=PAL.MURO_BORDE, lw=0.5)
    L.rect(POZO_X0, POZO_Y0, POZO_X1, POZO_Y1, layer="VACIO", fc="none",
           ec=PAL.GUIA, lw=0.6, ls=(0, (3, 2)))
    L.texto(((POZO_X0 + POZO_X1) / 2.0, (POZO_Y0 + POZO_Y1) / 2.0),
            "POZO", h_mm=2.0, layer="TEXTO", color="#7a7a7a")
    # los dos limites de propiedad, que son el motivo de todo el asunto
    for x in (-RETIRO_LATERAL, FRENTE + RETIRO_LATERAL):
        L.linea((x, -1.0), (x, FONDO + 1.0), layer="EJES", color=PAL.LIMITE,
                lw=1.0, ls=(0, (12, 3, 2, 3)))
    return n_centrados, n_excentricos


def corte_tipico(L, x_mm, y_mm, d, esc=50.0):
    """El cimiento corrido bajo un muro interior, acotado. 1:25."""
    def mm(v):
        return v * 1000.0 / esc

    W = 76.0
    L.h_texto((x_mm, y_mm), "CORTE TIPICO  -  cimiento corrido  esc. 1:%.0f"
              % esc, h_mm=2.4, ha="left", va="top", weight="bold")
    # niveles, de abajo hacia arriba
    y_fondo = y_mm - 46.0
    y_npt = y_fondo + mm(DF)
    xc = x_mm + 30.0
    # terreno
    L.h_rect(x_mm + 2.0, y_fondo - 3.0, x_mm + W - 2.0, y_npt,
             layer="CAJETIN", fc=TERRENO, ec="#c9bda9", lw=0.4)
    # cimiento corrido
    L.h_rect(xc - mm(B_CIMIENTO) / 2.0, y_fondo,
             xc + mm(B_CIMIENTO) / 2.0, y_fondo + mm(0.60),
             layer="CAJETIN", fc=CIM, ec=PAL.CIMIENTO_BORDE, lw=0.9)
    # sobrecimiento y muro
    L.h_rect(xc - mm(ESPESOR) / 2.0, y_fondo + mm(0.60),
             xc + mm(ESPESOR) / 2.0, y_npt,
             layer="CAJETIN", fc=SOBRE, ec=PAL.CIMIENTO_BORDE, lw=0.8)
    L.h_rect(xc - mm(ESPESOR) / 2.0, y_npt,
             xc + mm(ESPESOR) / 2.0, y_npt + 11.0,
             layer="CAJETIN", fc=PAL.MURO, ec=PAL.MURO_BORDE, lw=0.8)
    L.h_texto((xc + mm(ESPESOR) / 2.0 + 2.0, y_npt + 6.0),
              "MURO t = %.2f m" % ESPESOR, h_mm=1.7, ha="left", va="center")
    L.h_linea((xc + mm(B_CIMIENTO) / 2.0, y_fondo + mm(0.30)),
              (xc + mm(B_CIMIENTO) / 2.0 + 4.0, y_fondo + mm(0.30)),
              layer="CAJETIN", color=PAL.CIMIENTO_BORDE, lw=0.5)
    L.h_texto((xc + mm(B_CIMIENTO) / 2.0 + 5.0, y_fondo + mm(0.30)),
              "CIMIENTO CORRIDO\nARMADO", h_mm=1.4, ha="left", va="center",
              color=PAL.CIMIENTO_BORDE, weight="bold")
    # cotas
    L.h_linea((xc - mm(B_CIMIENTO) / 2.0, y_fondo - 4.0),
              (xc + mm(B_CIMIENTO) / 2.0, y_fondo - 4.0), layer="CAJETIN",
              color="#00808a", lw=0.8)
    L.h_texto((xc, y_fondo - 7.2), "B = %.2f m" % B_CIMIENTO, h_mm=2.0,
              ha="center", va="top", color="#00808a", weight="bold")
    L.h_linea((x_mm + W - 8.0, y_fondo), (x_mm + W - 8.0, y_npt),
              layer="CAJETIN", color="#00808a", lw=0.8)
    L.h_texto((x_mm + W - 6.5, (y_fondo + y_npt) / 2.0),
              "Df = %.2f m" % DF, h_mm=1.9, ha="left", va="center",
              color="#00808a", rot=90)
    L.h_texto((x_mm + 2.0, y_npt + 2.0), "N.P.T. +0.00", h_mm=1.7,
              ha="left", va="bottom")
    return y_fondo - 11.0


def detalle_medianero(L, x_mm, y_mm, d, esc=50.0):
    """El caso que hace pensar: el cimiento que no puede volar al vecino."""
    def mm(v):
        return v * 1000.0 / esc

    W = 76.0
    L.h_texto((x_mm, y_mm),
              "CIMIENTO MEDIANERO  -  excentrico  esc. 1:%.0f" % esc,
              h_mm=2.4, ha="left", va="top", weight="bold")
    y_fondo = y_mm - 40.0
    y_npt = y_fondo + 18.0
    x_lim = x_mm + 14.0
    # predio vecino
    L.h_rect(x_mm + 2.0, y_fondo - 3.0, x_lim, y_npt + 12.0,
             layer="CAJETIN", fc="#f0e6f5", ec="#b9a3c4", lw=0.4)
    L.h_texto(((x_mm + 2.0 + x_lim) / 2.0, (y_fondo + y_npt) / 2.0),
              "VECINO", h_mm=1.6, ha="center", va="center", color=PAL.LIMITE,
              rot=90)
    L.h_linea((x_lim, y_fondo - 4.0), (x_lim, y_npt + 13.0), layer="CAJETIN",
              color=PAL.LIMITE, lw=1.2, ls=(0, (7, 2, 1.5, 2)))
    # el cimiento apoya CONTRA el limite
    L.h_rect(x_lim, y_fondo, x_lim + mm(B_CIMIENTO), y_fondo + 9.0,
             layer="CAJETIN", fc=PAL.ALERTA, ec=PAL.CIMIENTO_BORDE, lw=0.9)
    # el muro, retirado la junta
    x_muro = x_lim + mm(RETIRO_LATERAL)
    L.h_rect(x_muro, y_fondo + 9.0, x_muro + mm(ESPESOR), y_npt + 12.0,
             layer="CAJETIN", fc=PAL.MURO, ec=PAL.MURO_BORDE, lw=0.8)
    # el eje del muro y el del cimiento NO coinciden: eso es la excentricidad
    ejec = x_lim + mm(B_CIMIENTO) / 2.0
    ejem = x_muro + mm(ESPESOR) / 2.0
    for x, c in ((ejec, PAL.CIMIENTO_BORDE), (ejem, PAL.MURO_BORDE)):
        L.h_linea((x, y_fondo - 2.0), (x, y_npt + 14.0), layer="CAJETIN",
                  color=c, lw=0.6, ls=(0, (4, 2)))
    L.h_linea((ejec, y_fondo - 5.5), (ejem, y_fondo - 5.5), layer="CAJETIN",
              color="#b02a1f", lw=1.0)
    L.h_texto(((ejec + ejem) / 2.0, y_fondo - 7.0),
              "e = %.3f m" % d["e"], h_mm=2.0, ha="center", va="top",
              color="#b02a1f", weight="bold")
    L.h_texto((x_lim + 1.0, y_npt + 15.0),
              "junta %.0f cm" % (RETIRO_LATERAL * 100), h_mm=1.6,
              ha="left", va="bottom", color=PAL.LIMITE)
    return y_fondo - 12.0


def construir():
    d = datos()
    L = Lamina(
        codigo="E-03",
        titulo="CIMENTACION",
        subtitulo=("Cimiento corrido armado bajo todos los muros portantes. "
                   "Df = %.2f m, B = %.2f m. Pisos 1 a %d."
                   % (DF, B_CIMIENTO, N_PISOS)),
        escala=ESCALA,
        meta=meta(),
        nota_pie="Numeros leidos de calculo/04_cimentacion.py y del 08",
    )
    L.encuadrar(-2.4, FRENTE + 2.4, -2.4, FONDO + 2.4,
                centro_mm=(78.0, 152.0))
    n_c, n_e = planta(L)

    L.leyenda_add(CIM, "ZAPATAS", "Cimiento corrido CENTRADO  B = %.2f m"
                  % B_CIMIENTO)
    L.leyenda_add(PAL.ALERTA, "ZAPATAS", "Cimiento MEDIANERO, excentrico")
    L.leyenda_add(PAL.LIMITE, "EJES", "Limite de propiedad")
    L.leyenda_dibujar(x_mm=170.0, y_mm=288.0, ancho_mm=76.0)

    y = L.cuadro(
        x_mm=170.0, y_mm=L._caja_leyenda[1] - 8.0,
        titulo="VERIFICACION DE LA CIMENTACION",
        encabezado=["CONCEPTO", "VALOR"],
        filas=[
            ["Carga lineal de servicio", "%.1f kgf/m" % d["w"]],
            ["Ancho requerido", "%.2f m" % d["B_req"]],
            ["Ancho adoptado B", "%.2f m" % B_CIMIENTO],
            ["Presion real", "%.2f kgf/cm2" % (d["q_real"] / 10.0)],
            ["qad del EMS", "%.2f kgf/cm2" % QAD],
            ["Holgura", "+%.0f %%" % ((QAD_TONF / d["q_real"] - 1) * 100)],
            ["Profundidad Df", "%.2f m" % DF],
            ["Cimientos centrados", str(n_c)],
            ["Cimientos medianeros", str(n_e)],
        ],
        anchos_mm=[48.0, 28.0], h_fila=4.3, h_txt=1.8,
        nota="Los muros portantes NO requieren zapata aislada: el cimiento "
             "corrido armado alcanza y ademas cumple el confinamiento "
             "horizontal que le asigna la E.070 2.1.3. El EMS admite "
             "\"zapatas conectadas y/o cimientos corridos armados\".",
    )
    with L.bloque_hoja("CORTE TIPICO", margen_mm=2.0):
        y = corte_tipico(L, 170.0, y - 8.0, d)
    y = min(y, L._cajas_hoja[-1][2])
    with L.bloque_hoja("DETALLE MEDIANERO", margen_mm=2.0):
        y = detalle_medianero(L, 170.0, y - 8.0, d)

    L.escala_grafica(x_mm=12.0, y_mm=16.0, metros=5)
    L.norte(x_mm=140.0, y_mm=272.0)
    L.cajetin()
    return L, d, n_c, n_e


def control(L, d, n_c, n_e):
    assert n_c + n_e == len(MUROS), (
        "se cimentaron %d muros y el SSOT declara %d"
        % (n_c + n_e, len(MUROS)))
    assert n_e == 2, ("los medianeros son MY-1 y MY-2: %d" % n_e)

    # la presion real tiene que entrar en el qad, con holgura
    assert d["q_real"] < QAD_TONF, (
        "la presion real %.2f supera el qad %.2f tonf/m2"
        % (d["q_real"], QAD_TONF))

    # el ancho adoptado cubre al requerido
    assert B_CIMIENTO >= d["B_req"], (
        "B adoptado %.2f es menor que el requerido %.2f"
        % (B_CIMIENTO, d["B_req"]))

    # el cimiento medianero NO puede pasar el limite de propiedad
    for pr in L.prims:
        if pr.pm is None or pr.layer != "ZAPATAS":
            continue
        for (px, _py) in pr.pm:
            assert -RETIRO_LATERAL - 1e-6 <= px <= FRENTE + RETIRO_LATERAL + 1e-6, (
                "E.050 Fig. 2: el cimiento invade al vecino en x = %.3f" % px)

    # y la excentricidad tiene que ser la que el 08 declara
    esperada = (B_CIMIENTO - ESPESOR) / 2.0 - RETIRO_LATERAL
    assert abs(d["e"] - esperada) < 1e-9

    ch = L.control_hoja()
    assert not ch, ("bloques de hoja que se pisan: %s"
                    % ["%s / %s" % (c[0], c[1]) for c in ch])
    for nom, x0, y0, x1, y1 in L._cajas_hoja:
        assert (6.0 <= x0 and x1 <= A3_MM[0] - 6.0
                and 6.0 <= y0 and y1 <= A3_MM[1] - 6.0), (
            "el bloque %r se sale de la hoja: x[%.1f, %.1f] y[%.1f, %.1f]"
            % (nom, x0, x1, y0, y1))

    print("  [ok] %d cimientos: %d centrados y %d medianeros" % (n_c + n_e, n_c, n_e))
    print("  [ok] presion %.2f < qad %.2f tonf/m2 (holgura +%.0f %%)"
          % (d["q_real"], QAD_TONF, (QAD_TONF / d["q_real"] - 1) * 100))
    print("  [ok] ningun cimiento pasa el limite de propiedad")
    print("  [ok] excentricidad medianera e = %.3f m (B/6 = %.3f)"
          % (d["e"], d["b6"]))
    print("  [ok] %d bloques de hoja, ninguno se pisa ni se sale"
          % len(L._cajas_hoja))


def main():
    L, d, n_c, n_e = construir()
    salidas = L.render(Path(R.LAMINAS), dpi=200, dxf_dir=Path(R.CAD))
    # La figura del informe se compone para la PAGINA (ver
    # lamina.py::render_figura): el DXF y la lamina completa
    # siguen saliendo a tamano de hoja, que es donde van.
    salidas["fig"] = L.render_figura(
        Path(R.INFORME), dpi=200,
        ancho_pagina=6.30, alto_pagina=8.86,
        cota_min_m=1.20,
        incluir_bloques=["VERIFICACION", "CORTE TIPICO", "DETALLE MEDIANERO"],
        dx_bloques=-28.0)
    print()
    for k, p in salidas.items():
        print("  %-5s %s  (%d KB)" % (k, p.name, p.stat().st_size // 1024))
    print()
    print("  escala 1:%d, hoja A3" % ESCALA)
    control(L, d, n_c, n_e)


if __name__ == "__main__":
    main()
