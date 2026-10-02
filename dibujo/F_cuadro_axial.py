# -*- coding: utf-8 -*-
"""Lámina-cuadro: esfuerzo axial máximo en los trece muros (E.070 7.1.1.b).

POR QUE ESTA LAMINA
===================
Es el «Paso 4» del ejemplo de clase, con el formato que el docente usa: la
fórmula arriba, una columna por cada término, los DOS límites del acápite
uno al lado del otro y la columna de veredicto. Lo que su lámina muestra
con diez filas anónimas, ésta lo muestra con los trece muros de este
proyecto y sus nombres.

LO QUE LA TABLA DEJA VER Y UN PARRAFO NO
========================================
El acápite pide el MENOR de dos límites, y con la esbeltez de este
edificio —h = 2,50 m y t = 0,24 m— el que manda es siempre `0,15 f'm`. Eso
se afirma en una línea de texto y se cree o no se cree; en la tabla se ve,
porque las dos columnas están al lado y una es siempre menor que la otra.

Y deja ver lo otro: la longitud que entra al denominador es la NETA. Un
vano parte el muro (6.4) y la carga baja por los machones, así que dividir
por la longitud bruta reparte el peso sobre una sección que no existe.
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
import paleta as PAL                                           # noqa: E402
from matplotlib.patches import Rectangle                       # noqa: E402


def _cargar(nombre):
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location("_" + nombre[:2], ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def croquis_de_tributarias(filas):
    u"""El mecanismo: el muro MAS CARGADO del edificio NO es el critico.

    POR QUE. La tabla trae la columna `Pm` y la columna `sigma`, y el lector
    supone que la mayor carga da el mayor esfuerzo. **No es asi, y en este
    edificio se ve con claridad:** MX-2 recibe 188 773 kgf y trabaja a 8,50;
    MX-7 recibe 132 653 --un 30 % menos-- y trabaja a 8,99, que es el maximo
    del edificio. La diferencia no esta en el numerador sino en el
    DENOMINADOR: el 7.1.1.b divide por la longitud NETA, y MX-7 conserva 6,15 m
    contra los 9,25 de MX-2.

    El croquis pone las dos franjas tributarias al lado y deja ver que la mas
    ancha no es la que gobierna. Un lector que salga de aca sabiendo eso
    entendio el acapite; uno que salga creyendo que basta mirar la carga, no.
    """
    import proyecto as P

    def dibujar(ax, x0, y0, ancho, alto):
        B, L = P.FRENTE, P.FONDO
        esc = min(ancho * 0.28 / B, alto * 0.92 / L)
        ox, oy = x0 + ancho * 0.05, y0 + alto * 0.05
        X = lambda u: ox + u * esc
        Y = lambda v: oy + v * esc

        critico = max(filas, key=lambda f: f["sigma"])
        cargado = max(filas, key=lambda f: f["pm"])
        trib = {n: (y, a) for n, y, a, _ar in P.tributaria_mx()}

        ax.add_patch(Rectangle((X(0), Y(0)), B * esc, L * esc, fc="#fbfcfe",
                               ec="#dde5ee", lw=0.7, zorder=1))

        # LAS DOS FRANJAS, la del mas cargado y la del critico
        for f, color, alfa in ((cargado, PAL.COTA, 0.22),
                               (critico, PAL.ALERTA, 0.26)):
            clave = f["nom"].split()[0]
            if clave not in trib:
                continue
            yy, anc = trib[clave]
            ax.add_patch(Rectangle((X(0), Y(yy - anc / 2.0)), B * esc,
                                   anc * esc, fc=color, ec="none",
                                   alpha=alfa, zorder=2))
            ax.annotate("", xy=(X(B * 0.86), Y(yy - anc / 2.0)),
                        xytext=(X(B * 0.86), Y(yy + anc / 2.0)),
                        arrowprops=dict(arrowstyle="<->", color=color, lw=1.0),
                        zorder=5)

        # los muros, encima de las franjas
        for k, yy in enumerate(P.EJES_MX):
            ax.plot([X(0), X(B)], [Y(yy)] * 2, color=PAL.MURO, lw=1.9,
                    solid_capstyle="butt", zorder=4)
        for xx in P.ejes_x_rotulados()[0]:
            ax.plot([X(xx)] * 2, [Y(0), Y(L)], color=PAL.MURO, lw=1.2,
                    solid_capstyle="butt", zorder=4)

        tx = x0 + ancho * 0.38
        cc, cr = cargado, critico
        C.bloque_de_texto(
            ax, tx, y0 + alto * 0.96, (x0 + ancho) - tx - 0.01,
            u"El muro MÁS CARGADO no es el crítico:",
            [u"%s recibe %s kgf sobre una franja de %s m y trabaja a %s. "
             u"%s recibe %s kgf —un %s %% menos— y trabaja a %s, que es el "
             u"máximo del edificio."
             % (cc["nom"].split()[0], _miles(cc["pm"]),
                _coma(trib.get(cc["nom"].split()[0], (0, 0))[1]),
                _coma(cc["sigma"]), cr["nom"].split()[0], _miles(cr["pm"]),
                _coma(100 * (1 - cr["pm"] / cc["pm"]), 0),
                _coma(cr["sigma"])),
             u"La diferencia no está en la carga sino en el DENOMINADOR: el "
             u"acápite 7.1.1.b divide por la longitud NETA, y %s conserva "
             u"%s m contra los %s de %s. Más vanos, menos longitud, más "
             u"esfuerzo."
             % (cr["nom"].split()[0], _coma(cr["Ln"]), _coma(cc["Ln"]),
                cc["nom"].split()[0])])

        # EL CONTROL: que lo que el croquis afirma sea cierto
        assert cr["sigma"] > cc["sigma"], (
            "el croquis dice que el mas cargado NO es el critico y aca si lo es")
        assert cr["Ln"] < cc["Ln"], (
            "el croquis atribuye el esfuerzo a la longitud neta y %s no es "
            "mas corto que %s" % (cr["nom"], cc["nom"]))
    return dibujar


def _miles(x):
    return format(int(round(x)), ",").replace(",", " ")


def _coma(x, d=2):
    return (("%%.%df" % d) % x).replace(".", ",")


def main():
    from proyecto import FM, H_LIBRE, ESPESOR
    m11 = _cargar("11_metrado_muros.py")
    m02 = _cargar("02_metrado_y_esfuerzo_axial.py")
    filas_m = m11.metrar()
    lim, esbeltez = m02.limite_axial(FM)
    lim_1 = 0.20 * FM * (1 - esbeltez)
    lim_2 = 0.15 * FM

    peor = max(filas_m, key=lambda f: f["sigma"])
    bloques = []
    for dire, rotulo in (("X", u"Dirección X-X"), ("Y", u"Dirección Y-Y")):
        filas, colores = [], []
        for f in filas_m:
            if f.get("dir") != dire:
                continue
            cumple = f["sigma"] <= f["lim"] + 1e-9
            filas.append([
                f["nom"].split()[0],
                C.miles(f["pm"]),
                C.coma(f["Ln"]),
                C.coma(f["sigma"]),
                "CUMPLE" if cumple else "NO CUMPLE",
            ])
            colores.append("#fff4e5" if f is peor else None)
        bloques.append({
            "titulo": u"%s  ·  σm = Pm / (L neta · t)" % rotulo,
            "cols": ["Muro", "Pm{n}(kgf)".format(n=chr(10)),
                     "L neta{n}(m)".format(n=chr(10)),
                     u"σm{n}(kgf/cm²)".format(n=chr(10)),
                     "Veredicto"],
            "filas": filas,
            "resaltar": 4,
            "colores_fila": colores,
        })
    # CONTROL: los trece muros tienen que caer en alguno de los dos bloques.
    # Repartir por una clave que no existe deja la lamina a medias y EN
    # SILENCIO: la tabla se veria perfecta con seis muros.
    assert sum(len(b["filas"]) for b in bloques) == len(filas_m), (
        "el reparto por direccion perdio muros: %d de %d"
        % (sum(len(b["filas"]) for b in bloques), len(filas_m)))

    comprobacion = [
        "Rige el MENOR de los dos límites:   %s  <  %s   →   σm admisible = "
        "%s kgf/cm²" % (C.coma(lim_2), C.coma(lim_1), C.coma(lim)),
        "El muro más exigido es %s con σm = %s   ≤   %s   →   CUMPLE  "
        "(holgura +%s %%)"
        % (peor["nom"].split()[0], C.coma(peor["sigma"]), C.coma(lim),
           C.coma((lim / peor["sigma"] - 1) * 100, 1)),
    ]

    nota = (
        "Pm lleva el 100 %% de la sobrecarga: es carga de gravedad de "
        "servicio, no peso sísmico (ahí la E.030 Art. 31 reduce al 25 %%). "
        "La longitud del denominador es la NETA: un vano parte el muro "
        "(6.4) y la carga baja por los machones, así que dividir por la "
        "bruta reparte el peso sobre sección que no existe.\n"
        "Con h = %s m y t = %s m la esbeltez (h/35t)² vale %s, de modo que "
        "el primer límite queda en %s y el que gobierna es siempre "
        "0,15 f'm = %s. La fila en crema es el muro que gobierna."
        % (C.coma(H_LIBRE), C.coma(ESPESOR), C.coma(esbeltez, 4),
           C.coma(lim_1), C.coma(lim_2)))

    out = os.path.join(R.INFORME, "CUADRO-ESFUERZO-AXIAL.png")
    C.lamina(
        paso="Paso 2 — Esfuerzo axial máximo",
        titulo="Verificación muro por muro contra los dos límites del "
               "acápite, con la longitud neta en el denominador",
        formula=r"$\sigma_m = \dfrac{P_m}{L \cdot t} \;\leq\; "
                r"0{,}20\,f'_m\left[1-\left(\dfrac{h}{35\,t}\right)^{2}"
                r"\right] \;\leq\; 0{,}15\,f'_m$",
        acapite="E.070  7.1.1.b",
        bloques=bloques,
        comprobacion=comprobacion,
        nota=nota,
        salida=out,
        croquis=croquis_de_tributarias(filas_m),
        alto_croquis=2.5,
    )
    print()
    control(filas_m, lim, lim_1, lim_2, peor)


def control(filas_m, lim, lim_1, lim_2, peor):
    """Lo que la lámina afirma sale del metrado, no del dibujo."""
    # 1. LA AFIRMACION CENTRAL del pie: que el que gobierna es 0,15 f'm.
    #    Si la esbeltez creciera --muro más alto o más delgado-- podría
    #    invertirse, y entonces el pie estaría enseñando algo falso.
    assert lim_2 < lim_1, (
        "la lámina afirma que gobierna 0,15 f'm = %.2f y el otro límite da "
        "%.2f" % (lim_2, lim_1))
    assert abs(lim - lim_2) < 1e-9, "el límite adoptado no es el menor"
    # 2. el veredicto escrito en cada fila tiene que ser cierto
    malos = [f for f in filas_m if f["sigma"] > f["lim"] + 1e-9]
    assert not malos, ("la lámina escribe CUMPLE en muros que no cumplen: %s"
                       % [f["nom"] for f in malos])
    # 3. y el que se marca en crema tiene que ser el mayor de verdad
    assert peor["sigma"] == max(f["sigma"] for f in filas_m), (
        "la fila en crema no es la del muro más exigido")
    print("  [ok] gobierna 0,15 f'm = %.2f sobre %.2f del primer límite"
          % (lim_2, lim_1))
    print("  [ok] los %d muros cumplen el 7.1.1.b" % len(filas_m))
    print("  [ok] el muro marcado (%s, sigma = %.2f) es el mas exigido"
          % (peor["nom"].split()[0], peor["sigma"]))
    return True


if __name__ == "__main__":
    main()
