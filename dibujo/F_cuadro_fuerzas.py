# -*- coding: utf-8 -*-
"""Lámina-cuadro: cortante basal y su distribución en altura (E.030 Art. 35).

POR QUE ESTA LAMINA
===================
Es el cuadro que el docente arma en la Clase 05 («Esquemas finales»:
NIVEL · Hi · Wi · (Hi·Wi)^k · % · Fi). Aquí va con los cinco niveles de
este edificio y con dos columnas más que su ejemplo no lleva y que hacen
falta para leer el diseño: el **cortante de entrepiso** acumulado, que es
lo que cada nivel tiene que transmitir hacia abajo, y el peso acumulado.

LO QUE EL CUADRO DEJA VER
=========================
Que el peso es casi el mismo en los cinco niveles y la fuerza NO: crece con
la altura porque el Art. 35 reparte por `Pi·hi^k`. El que manda es el
brazo, no la masa. En una lista de números eso hay que deducirlo; con las
dos columnas al lado se ve.

Y deja ver algo que sorprende y es real: **la azotea es el nivel más
pesado**, no el más liviano. No lleva tabiquería, pero lleva parapeto, y el
parapeto pesa más que la tabiquería que le falta.
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
    ruta = os.path.join(AQUI, "..", "calculo", "16_irregularidades.py")
    spec = importlib.util.spec_from_file_location("_m16", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def croquis_de_elevacion(pesos, h, Fi):
    u"""El mecanismo: lo que reparte la fuerza no es el peso, es el BRAZO.

    POR QUE. La tabla trae la columna `Pi` y la columna `Fi`, y el lector
    supone que el nivel mas pesado recibe la mayor fuerza. En este edificio
    los cinco niveles pesan **practicamente lo mismo** --282 523 kgf los
    cuatro tipicos y 291 795 la azotea, un 3 % mas-- y sin embargo la azotea
    recibe **5,2 veces** la fuerza del primer piso.

    La razon esta en la formula del Art. 35: `Fi = Pi.hi^k / sum(Pj.hj^k) . V`.
    Con pesos iguales, el reparto queda gobernado por `hi`: el ultimo nivel
    esta a 13,50 m y el primero a 2,70, y la relacion 13,50/2,70 = 5 es casi
    exactamente la relacion entre sus fuerzas.

    Dibujado en elevacion se entiende de un vistazo: cinco masas iguales, y
    las flechas creciendo con la altura.
    """
    import proyecto as P

    def dibujar(ax, x0, y0, ancho, alto):
        n = len(Fi)
        H = h[-1]
        esc_v = alto * 0.80 / H
        base_y = y0 + alto * 0.10
        # SE RESERVA A LA IZQUIERDA lo que mide el rotulo mas largo, no una
        # fraccion del ancho: el rotulo esta en puntos y no encoge con la
        # lamina. Ver el porque arriba.
        rot = ["%s kgf" % _miles(v) for v in Fi]
        w_rot = max(C.envolver_ancho(ax, s, 7.2) for s in rot)
        largo_max = ancho * 0.16
        eje_x = x0 + w_rot + largo_max + ancho * 0.03
        ancho_edif = ancho * 0.10
        Fmax = max(Fi)

        # el edificio, cinco niveles
        for i in range(n):
            yb = base_y + (h[i] - P.H_ENTREPISO) * esc_v
            ax.add_patch(Rectangle((eje_x, yb), ancho_edif,
                                   P.H_ENTREPISO * esc_v, fc="#f2f5f9",
                                   ec=PAL.MURO, lw=0.9, zorder=2))
        # el suelo
        ax.plot([eje_x - ancho * 0.02, eje_x + ancho_edif + ancho * 0.02],
                [base_y] * 2, color="#78909c", lw=2.2, zorder=3)

        w_pi = max(C.envolver_ancho(ax, "%s kgf" % _miles(v), 6.9)
                   for v in pesos)
        x_cota = eje_x + ancho_edif + ancho * 0.010 + w_pi + ancho * 0.030
        for i in range(n):
            yy = base_y + h[i] * esc_v
            largo = largo_max * Fi[i] / Fmax
            # la FUERZA, de largo proporcional
            ax.annotate("", xy=(eje_x, yy),
                        xytext=(eje_x - largo, yy), zorder=5,
                        arrowprops=dict(arrowstyle="-|>", color=PAL.ALERTA,
                                        lw=1.8))
            ax.text(eje_x - largo - ancho * 0.008, yy,
                    "%s kgf" % _miles(Fi[i]), fontsize=7.2,
                    color=PAL.ALERTA, ha="right", va="center",
                    fontweight="bold", zorder=5)
            # el PESO del nivel, a la derecha: casi iguales
            ax.text(eje_x + ancho_edif + ancho * 0.010, yy - alto * 0.028,
                    "%s kgf" % _miles(pesos[i]), fontsize=6.9,
                    color="#78909c", ha="left", va="center", zorder=5)
            # el BRAZO
            ax.plot([x_cota] * 2, [base_y, yy], color=PAL.COTA, lw=0.7,
                    ls=":", zorder=4)

        # la cota del brazo total, PASADA la columna de pesos (ver arriba)
        ax.annotate("", xy=(x_cota, base_y),
                    xytext=(x_cota, base_y + H * esc_v),
                    arrowprops=dict(arrowstyle="<->", color=PAL.COTA, lw=1.0),
                    zorder=5)
        ax.text(x_cota + ancho * 0.018, base_y + H * esc_v / 2.0,
                "hn = %s m" % _coma(H), fontsize=7.4, color=PAL.COTA,
                fontweight="bold", va="center", ha="center", rotation=90,
                rotation_mode="anchor", zorder=5)
        ax.text(eje_x - largo_max - ancho * 0.008, base_y - alto * 0.055,
                "Fi", fontsize=7.6, color=PAL.ALERTA, fontweight="bold",
                ha="right", va="top")
        ax.text(eje_x + ancho_edif + ancho * 0.010, base_y - alto * 0.055,
                "Pi", fontsize=7.6, color="#78909c", fontweight="bold",
                ha="left", va="top")

        # arranca despues de la cota, no en la mitad de la lamina
        tx = max(x0 + ancho * 0.48, x_cota + ancho * 0.055)
        rel_F = Fi[-1] / Fi[0]
        rel_P = max(pesos) / min(pesos)
        C.bloque_de_texto(
            ax, tx, y0 + alto * 0.96, (x0 + ancho) - tx - 0.01,
            u"El nivel más pesado no es el más solicitado:",
            [u"Los cinco niveles pesan casi lo mismo: entre el más liviano y "
             u"el más pesado hay un %s %%. Y sin embargo la azotea recibe %s "
             u"veces la fuerza del primer piso."
             % (_coma(100 * (rel_P - 1), 1), _coma(rel_F, 1)),
             u"Lo que reparte no es el peso: es el BRAZO. Con pesos iguales "
             u"la fórmula del Art. 35 queda gobernada por hi, y %s / %s = %s "
             u"— casi exactamente la relación entre las dos fuerzas."
             % (_coma(h[-1]), _coma(h[0]), _coma(h[-1] / h[0], 1))])

        # CONTROLES de lo que el croquis afirma
        assert rel_P < 1.10, (
            "el croquis dice que los niveles pesan casi lo mismo y difieren "
            "un %.0f %%" % (100 * (rel_P - 1)))
        assert rel_F > 3.0, (
            "el croquis dice que la azotea recibe varias veces la fuerza del "
            "primer piso y la relacion es %.2f" % rel_F)
        assert abs(rel_F - h[-1] / h[0]) / rel_F < 0.15, (
            "el croquis atribuye el reparto al brazo y la relacion de fuerzas "
            "(%.2f) no sigue a la de alturas (%.2f)" % (rel_F, h[-1] / h[0]))
    return dibujar


def _miles(x):
    return format(int(round(x)), ",").replace(",", " ")


def _coma(x, d=2):
    return (("%%.%df" % d) % x).replace(".", ",")


def main():
    from proyecto import Z, U, S, N_PISOS, H_ENTREPISO
    m = datos()
    with contextlib.redirect_stdout(_io.StringIO()):
        T, k, Cs, pesos, P, V = m.sismo()
        h, Fi, frac = m.fuerzas(pesos, V, k)
    R_red = V / (Z * U * Cs * S * P) and (Z * U * Cs * S / (V / P))

    # de arriba hacia abajo, como el cuadro de la clase
    orden = list(range(N_PISOS - 1, -1, -1))
    filas = []
    acum_V, acum_W = 0.0, 0.0
    cortantes = []
    for i in orden:
        acum_V += Fi[i]
        cortantes.append(acum_V)
    for j, i in enumerate(orden):
        acum_W += pesos[i]
        filas.append([
            "%d%s" % (i + 1, "  (azotea)" if i == N_PISOS - 1 else ""),
            C.coma(h[i]),
            C.miles(pesos[i]),
            C.miles(pesos[i] * h[i] ** k),
            C.coma(100.0 * frac[i], 1) + " %",
            C.miles(Fi[i]),
            C.miles(cortantes[j]),
        ])

    bloques = [{
        "titulo": "Distribución de la fuerza sísmica en altura  ·  "
                  "k = %s  (T = %s s ≤ 0,5 s)" % (C.coma(k), C.coma(T, 3)),
        "cols": ["Nivel", "hi\n(m)", "Pi\n(kgf)", "Pi·hi^k\n(kgf·m)",
                 "αi", "Fi\n(kgf)", "Vi entrepiso\n(kgf)"],
        "filas": filas,
        "suma": ["Σ", "", C.miles(P), "", "100,0 %", C.miles(V), ""],
    }]

    comprobacion = [
        "V = Z·U·C·S/R · P = %s·%s·%s·%s/%s × %s = %s kgf   (sismo severo)"
        % (C.coma(Z), C.coma(U), C.coma(Cs), C.coma(S), C.coma(3.0),
           C.miles(P), C.miles(V)),
        "La azotea recibe %s veces la fuerza del primer piso pesando sólo un "
        "%s %% más: reparte el BRAZO, no la masa."
        % (C.coma(Fi[-1] / Fi[0]),
           C.coma(100.0 * (max(pesos) / min(pesos) - 1), 1)),
    ]

    nota = (
        "Fi = αi·V con αi = Pi·hi^k / Σ(Pj·hj^k), Art. 35 de la E.030. El "
        "exponente k vale 1,00 porque T ≤ 0,5 s (Art. 35.2.a): la "
        "distribución es lineal con la altura.\n"
        "El cortante de entrepiso Vi se acumula de arriba hacia abajo, así "
        "que el del primer entrepiso es el cortante basal completo. Es la "
        "columna que alimenta el reparto por muro del paso siguiente.")

    out = os.path.join(R.INFORME, "CUADRO-FUERZAS-NIVEL.png")
    C.lamina(
        paso="Paso 3 — Cortante basal y fuerza por nivel",
        titulo="Distribución en altura del cortante basal y cortante "
               "acumulado de cada entrepiso",
        formula=r"$V = \dfrac{Z\,U\,C\,S}{R}\,P$"
                r"$\qquad\qquad$"
                r"$F_i = \dfrac{P_i\,h_i^{\,k}}{\sum P_j\,h_j^{\,k}}\;V$",
        acapite="E.030  Art. 34 y 35",
        bloques=bloques,
        comprobacion=comprobacion,
        nota=nota,
        salida=out,
        croquis=croquis_de_elevacion(pesos, h, Fi),
        alto_croquis=2.6,
    )
    print()
    control(pesos, Fi, V, P, frac)


def control(pesos, Fi, V, P, frac):
    """Lo que la lámina afirma sale del script 16, no del dibujo."""
    # 1. la suma de las fuerzas tiene que dar el cortante basal
    assert abs(sum(Fi) - V) < 1.0, (
        "las fuerzas suman %.0f y el cortante basal es %.0f" % (sum(Fi), V))
    assert abs(sum(pesos) - P) < 1.0, (
        "los pesos suman %.0f y el peso sismico es %.0f" % (sum(pesos), P))
    assert abs(sum(frac) - 1.0) < 1e-6, "los alfa no suman 1"
    # 2. LA AFIRMACION CENTRAL: la fuerza crece con la altura mientras el
    #    peso es casi el mismo. Si dejara de ser cierto, el pie mentiría.
    assert Fi[-1] > Fi[0], "la lamina dice que la fuerza crece con la altura"
    disp = max(pesos) / min(pesos) - 1
    assert disp < 0.10, (
        "la lamina dice que los niveles pesan casi lo mismo y difieren "
        "%.1f %%" % (100 * disp))
    print("  [ok] las fuerzas suman el cortante basal (%.0f kgf)" % V)
    print("  [ok] los pesos suman el peso sismico (%.0f kgf)" % P)
    print("  [ok] la fuerza crece %.1f veces con la altura y los pesos "
          "difieren %.1f %%" % (Fi[-1] / Fi[0], 100 * disp))
    return True


if __name__ == "__main__":
    main()
