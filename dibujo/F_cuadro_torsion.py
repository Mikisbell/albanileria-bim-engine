# -*- coding: utf-8 -*-
"""Lámina-cuadro: centros, excentricidad y momento torsor (E.030 Art. 37).

POR QUE ESTA LAMINA
===================
El docente dedica media Clase 05 a la cadena que lleva del centro de masa
al momento torsor —«1. Determinamos el centro de rigidez · 2. El centro de
masa · 3. Momento torsor reglamentario · 4. Rigidez torsional»— y la
presenta como un bloque de casillas encadenadas. Es el paso que une el
cortante basal con el reparto por muro, y sin él la columna «V torsión» del
cuadro siguiente sale de la nada.

Aquí va como una tabla de dos columnas, una por dirección de análisis,
porque lo que hace tropezar es justamente eso: **para sismo en X la
excentricidad que importa es la de Y**, y la dimensión que entra en el
0,05·B es la PERPENDICULAR a la dirección de análisis. Puestas al lado, el
cruce se ve; en un texto corrido hay que leerlo dos veces.

LO QUE EL CUADRO DEJA VER
=========================
Que en este edificio **la excentricidad propia es casi nula** —las dos
medianeras son simétricas respecto del eje del lote, y dos rigideces
iguales a distancias iguales no corren el centroide: lo fijan— y que la que
gobierna es la **accidental**, la que la norma obliga a suponer aunque el
edificio salga perfecto.
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


def datos():
    ruta = os.path.join(AQUI, "..", "calculo", "17_reparto_cortante.py")
    spec = importlib.util.spec_from_file_location("_m17", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def croquis_de_centros(xm, ym, xr, yr, e):
    u"""El mecanismo: la excentricidad que manda NO es la que se calcula.

    POR QUE. La tabla trae `CM`, `CR` y su diferencia, y despues una columna
    `0,05 B` que aparece sin explicacion visible. El lector saca la conclusion
    natural --"los centros casi coinciden, entonces no hay torsion"-- y es
    justamente lo contrario de lo que ocurre.

    En esta planta los dos centros estan a **centimetros** uno del otro: 1 cm
    en X y 19,6 cm en Y. Pero el Art. 37 obliga a sumar una excentricidad
    ACCIDENTAL de 0,05 veces la dimension perpendicular, que aca vale 0,595 y
    1,050 m. **La accidental es entre tres y sesenta veces la propia**, de modo
    que el momento torsor del edificio lo fija la norma, no la geometria.

    Dibujado, se ve de una: dos puntos casi superpuestos, y alrededor la caja
    de la excentricidad reglamentaria, que es lo que de verdad se aplica.
    """
    import proyecto as P

    def dibujar(ax, x0, y0, ancho, alto):
        B, L = P.FRENTE, P.FONDO
        esc = min(ancho * 0.30 / B, alto * 0.92 / L)
        ox, oy = x0 + ancho * 0.06, y0 + alto * 0.04
        X = lambda u: ox + u * esc
        Y = lambda v: oy + v * esc

        ax.add_patch(Rectangle((X(0), Y(0)), B * esc, L * esc, fc="#fbfcfe",
                               ec="#dde5ee", lw=0.7, zorder=1))
        for yy in P.EJES_MX:
            ax.plot([X(0), X(B)], [Y(yy)] * 2, color=PAL.MURO, lw=1.7,
                    solid_capstyle="butt", zorder=3)
        for xx in P.ejes_x_rotulados()[0]:
            ax.plot([X(xx)] * 2, [Y(0), Y(L)], color=PAL.MURO, lw=1.1,
                    solid_capstyle="butt", zorder=3)

        # LA CAJA DE LA EXCENTRICIDAD ACCIDENTAL, que es lo que se aplica
        eax, eay = 0.05 * B, 0.05 * L
        ax.add_patch(Rectangle((X(xm - eax), Y(ym - eay)), 2 * eax * esc,
                               2 * eay * esc, fc=PAL.GOBIERNA, ec=PAL.GOBIERNA,
                               lw=1.2, ls=(0, (4, 2)), alpha=0.12, zorder=4))

        # los DOS centros, casi superpuestos
        ax.plot([X(xm)], [Y(ym)], "o", color=PAL.COTA, ms=7, mec="#ffffff",
                mew=1.2, zorder=6)
        ax.plot([X(xr)], [Y(yr)], "s", color=PAL.ALERTA, ms=6.5,
                mec="#ffffff", mew=1.2, zorder=6)
        ax.text(X(xm) - ancho * 0.010, Y(ym) - alto * 0.045, "CM",
                fontsize=7.6, color=PAL.COTA, fontweight="bold", ha="right",
                va="top", zorder=6)
        ax.text(X(xr) + ancho * 0.010, Y(yr) + alto * 0.030, "CR",
                fontsize=7.6, color=PAL.ALERTA, fontweight="bold", ha="left",
                va="bottom", zorder=6)
        # EL ROTULO DE LA CAJA, a su esquina INFERIOR: puesto al costado
        # quedaba a la altura de los dos centros y se montaba sobre "CR".
        ax.text(X(xm + eax) + ancho * 0.006, Y(ym - eay),
                "caja de la\naccidental\n0,05·B", fontsize=7.0,
                color=PAL.GOBIERNA, fontweight="bold", ha="left", va="top",
                zorder=6)

        propia_x, propia_y = abs(xm - xr), abs(ym - yr)
        tx = x0 + ancho * 0.40
        # OJO CON LA CONVENCION: la tabla de al lado indexa por DIRECCION
        # DE SISMO y la accidental usa la dimension PERPENDICULAR, asi que
        # su columna "Sismo en X" lleva 0,05 x 21,00. Decir aca "0,595 en X"
        # contradecia esa tabla dentro de la misma lamina. Se habla de las
        # DIMENSIONES del lote, que no dependen de la convencion.
        C.bloque_de_texto(
            ax, tx, y0 + alto * 0.96, (x0 + ancho) - tx - 0.01,
            u"La excentricidad que manda no es la que se calcula:",
            [u"Los dos centros están a centímetros: %s cm en X y %s cm en Y. "
             u"A esta escala son el mismo punto."
             % (_coma(100 * propia_x, 0), _coma(100 * propia_y, 0)),
             u"Pero el Art. 37 obliga a sumar una excentricidad ACCIDENTAL "
             u"de 0,05 veces la dimensión perpendicular al sismo: %s m sobre "
             u"el frente de %s m y %s m sobre el fondo de %s — la caja "
             u"punteada. Frente a una propia de %s y %s m, la accidental es "
             u"hasta %s veces mayor."
             % (_coma(0.05 * B, 3), _coma(B), _coma(0.05 * L, 3), _coma(L),
                _coma(propia_x, 3), _coma(propia_y, 3),
                _coma(0.05 * L / max(propia_x, 1e-9), 0)),
             u"El momento torsor de este edificio lo fija la NORMA, no la "
             u"geometría. Una planta simétrica no está exenta de torsión."])

        # CONTROLES: lo que el croquis afirma
        assert 0.05 * B > propia_x and 0.05 * L > propia_y, (
            "el croquis dice que la accidental gobierna y en alguna direccion "
            "no lo hace")
        assert propia_x < 0.50 and propia_y < 0.50, (
            "el croquis dice que los centros estan a centimetros y estan a "
            "%.2f / %.2f m" % (propia_x, propia_y))
    return dibujar


def _coma(x, d=2):
    return (("%%.%df" % d) % x).replace(".", ",")


def main():
    from proyecto import FRENTE, FONDO
    m = datos()
    with contextlib.redirect_stdout(_io.StringIO()):
        filas, h, Fi, V, xm, ym, xr, yr = m.contexto()
        V_ent = m.cortantes_de_entrepiso(Fi)
        Ktor, Kx, Ky = m.geometria_torsional(filas, xr, yr)
        _rep, e = m.repartir(filas, V_ent, xm, ym, xr, yr, Ktor, Kx, Ky)

    Ve = V_ent[0]
    # para sismo en X el brazo es en Y, y la dimensión del 0,05·B es la
    # PERPENDICULAR a la dirección de análisis
    prop = {"X": abs(ym - yr), "Y": abs(xm - xr)}
    B = {"X": FONDO, "Y": FRENTE}
    cm = {"X": ym, "Y": xm}
    cr = {"X": yr, "Y": xr}
    eje = {"X": "y", "Y": "x"}

    filas_t = []
    for etiqueta, val, dec, unidad in (
            ("Centro de masa  CM", cm, 3, "m"),
            ("Centro de rigidez  CR", cr, 3, "m"),
            ("Excentricidad propia  |CM − CR|", prop, 3, "m"),
            ("Dimensión perpendicular  B", B, 2, "m"),
            ("Excentricidad accidental  0,05·B",
             {d: 0.05 * B[d] for d in ("X", "Y")}, 3, "m"),
            ("Excentricidad de diseño  e", e, 3, "m")):
        filas_t.append([
            etiqueta,
            C.coma(val["X"], dec) + " " + unidad,
            C.coma(val["Y"], dec) + " " + unidad,
        ])
    filas_t.append(["Cortante del entrepiso  Ve",
                    C.miles(Ve) + " kgf", C.miles(Ve) + " kgf"])
    filas_t.append(["Momento torsor  Mt = Ve · e",
                    C.miles(Ve * e["X"]) + " kgf·m",
                    C.miles(Ve * e["Y"]) + " kgf·m"])

    bloques = [{
        "titulo": "Primer entrepiso  ·  el brazo del momento torsor",
        "cols": ["Magnitud", "Sismo en X-X\n(brazo en y)",
                 "Sismo en Y-Y\n(brazo en x)"],
        "filas": filas_t,
    }]

    comprobacion = [
        "Rigidez torsional  Ktor = Σ(Ki · Ri²) = %s kgf·cm/rad"
        % C.miles(Ktor),
        "En las dos direcciones la excentricidad ACCIDENTAL supera a la "
        "propia: es la que gobierna el momento torsor.",
    ]

    nota = (
        "El Art. 37 obliga a suponer una excentricidad accidental de 0,05 "
        "por la dimensión perpendicular a la dirección de análisis, y a "
        "sumarla a la propia en el sentido que resulte más desfavorable. No "
        "es una imprecisión del cálculo: cubre el reparto real de masas en "
        "servicio, que nadie controla.\n"
        "La excentricidad propia sale casi nula porque las dos medianeras "
        "son simétricas respecto del eje del lote: dos rigideces iguales a "
        "distancias iguales no corren el centro de rigidez, lo fijan. Por "
        "eso lo que reparte torsión en este edificio es la accidental.")

    out = os.path.join(R.INFORME, "CUADRO-TORSION.png")
    C.lamina(
        paso="Paso 5 — Centros, excentricidad y momento torsor",
        titulo="De dónde sale el brazo que alimenta la columna de torsión "
               "del reparto",
        formula=r"$e = |CM - CR| + 0{,}05\,B$"
                r"$\qquad\qquad$"
                r"$M_t = V_e\,e$"
                r"$\qquad\qquad$"
                r"$K_{tor} = \sum K_i\,R_i^{\,2}$",
        acapite="E.030  Art. 37",
        bloques=bloques,
        comprobacion=comprobacion,
        nota=nota,
        salida=out,
        croquis=croquis_de_centros(xm, ym, xr, yr, e),
        alto_croquis=3.0,
    )
    print()
    control(prop, B, e)


def control(prop, B, e):
    """Lo que la lámina afirma sale del cálculo, no del dibujo."""
    for d in ("X", "Y"):
        acc = 0.05 * B[d]
        # 1. e tiene que ser la suma que la fórmula escribe
        assert abs(e[d] - (prop[d] + acc)) < 1e-9, (
            "en %s la e de diseño no es propia + accidental" % d)
        # 2. LA AFIRMACION del pie y de la comprobación: que gobierna la
        #    accidental. Si la propia creciera --una planta asimétrica--
        #    dejaría de ser cierto y el texto tendría que cambiar.
        assert acc > prop[d], (
            "la lámina dice que gobierna la accidental y en %s la propia "
            "vale %.3f contra %.3f" % (d, prop[d], acc))
    print("  [ok] e = propia + accidental en las dos direcciones")
    print("  [ok] la accidental gobierna: X %.3f > %.3f  ·  Y %.3f > %.3f"
          % (0.05 * B["X"], prop["X"], 0.05 * B["Y"], prop["Y"]))
    return True


if __name__ == "__main__":
    main()
