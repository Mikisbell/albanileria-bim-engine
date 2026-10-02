# -*- coding: utf-8 -*-
"""Los cuatro espaciamientos de estribo: cuál rige, y por qué cambia.

POR QUE ESTA FIGURA
===================
Es el hallazgo del proyecto, y se explicaba sólo con dos tablas de números.
El acápite 8.6.3-a.3 manda colocar **el menor** de cuatro espaciamientos, y
lo que hace tropezar es que **cuál es el menor DEPENDE del estribo que se
elija**:

  Con estribo de ø 6 mm rige `s1` — inconstruible, poco más de 4 cm.
  Se sube a ø 3/8" para poder ejecutarlo… y ahí está la trampa: `s1` y `s2`
  son proporcionales al área del estribo, pero **`s3 = d/4` no depende de
  ella**. Al cambiar el estribo, el que manda pasa a ser `s3`.

El proyecto recalculaba sólo `s1` y seguía adoptando el mínimo del final del
acápite —«1 @ 5, 4 @ 10, r @ 25»—, con estribos a 10 cm donde el cálculo
pedía menos: **no cumplía**, y con todos los guardianes en verde.

Dos juegos de barras, con el que rige marcado en cada uno, muestran el
cambio de criterio de un vistazo. Una tabla no lo muestra: hay que leerla
dos veces y comparar de memoria.
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

RIGE = "#b02a1f"
OTRO = "#9fb0bd"
ADOPTA = "#2e7d52"


def datos():
    """Los cuatro espaciamientos con cada estribo, del script 19."""
    ruta = os.path.join(AQUI, "..", "calculo", "19_confinamientos.py")
    spec = importlib.util.spec_from_file_location("_m19", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def main():
    m = datos()
    # el peralte de la C-2, que es donde el criterio cambia
    from proyecto import H_COLUMNA_EXT
    d_cm = H_COLUMNA_EXT * 100.0
    av6 = 3.1416 * 0.6 ** 2 / 4.0 * 2      # dos ramas de o 6 mm
    av38 = 3.1416 * 0.952 ** 2 / 4.0 * 2   # dos ramas de o 3/8"

    casos = []
    for nom, av in (('estribo ø 6 mm', av6), ('estribo ø 3/8"', av38)):
        s1, s2, s3, s4, _menor, _zona, _An, _tn = m.estribos(d_cm, av=av)
        casos.append((nom, [s1, s2, s3, s4]))

    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 6.60), dpi=200)
    m1 = min(range(4), key=lambda i: casos[0][1][i])
    m2 = min(range(4), key=lambda i: casos[1][1][i])
    y_ar, y_ab = C.marco(
        fig,
        u"E.070 8.6.3-a.3  ·  «deberá colocarse EL MENOR de los siguientes "
        u"espaciamientos»",
        pie=(u"Con el estribo de 6 mm rige s1 = %.2f cm: inconstruible. Se "
             u"sube a ø 3/8\" para ejecutarlo, y ahí está la trampa: s1 y s2 "
             u"son proporcionales al área del estribo, pero s3 = d/4 NO. Al "
             u"cambiar el estribo el criterio que manda pasa de s%d a s%d, y "
             u"hay que volver a preguntar cuál rige."
             % (casos[0][1][m1], m1 + 1, m2 + 1)))
    _h = (y_ar - y_ab - 0.06) / 2.0

    etiquetas = ["s1\n(confinamiento)", "s2\n(cuantía)",
                 "s3 = d/4\n(geométrico)", "s4\n(tope 10 cm)"]
    for k, (nom, ss) in enumerate(casos):
        # APILADOS: cada panel con el ancho entero de la pagina
        ax = fig.add_axes((0.115, y_ab + (1 - k) * (_h + 0.06),
                           0.855, _h * 0.78))
        menor = min(range(len(ss)), key=lambda i: ss[i])
        cols = [RIGE if i == menor else OTRO for i in range(len(ss))]
        ax.bar(range(len(ss)), ss, 0.62, color=cols)
        for i, v in enumerate(ss):
            ax.annotate("%.2f" % v, (i, v), xytext=(i, v + 0.35),
                        ha="center", fontsize=9,
                        fontweight=("bold" if i == menor else "normal"),
                        color=(RIGE if i == menor else "#55606a"))
        ax.annotate("RIGE", (menor, 0.55), ha="center", fontsize=9.5,
                    color="white", fontweight="bold")
        ax.set_xticks(range(len(ss)))
        ax.set_xticklabels(etiquetas, fontsize=8.5)
        ax.set_ylim(0, max(max(c[1]) for c in casos) * 1.22)
        ax.set_ylabel("espaciamiento (cm)", fontsize=9)
        ax.set_title("(%s)  %s   →   rige %s con %.2f cm"
                     % ("ab"[k], nom, etiquetas[menor].split("\n")[0],
                        ss[menor]),
                     fontsize=10, loc="left", color=E.TINTA, pad=8)
        ax.grid(axis="y", color="#dde3e8", lw=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    out = os.path.join(R.INFORME, "ESTRIBOS-CUAL-RIGE.png")
    C.guardar(fig, out)
    print()
    control(casos)


def control(casos):
    # la figura AFIRMA que el criterio que rige CAMBIA al cambiar el estribo.
    # Si no cambiara, la figura no enseñaria nada y el texto mentiria.
    m1 = min(range(4), key=lambda i: casos[0][1][i])
    m2 = min(range(4), key=lambda i: casos[1][1][i])
    assert m1 != m2, (
        "con los dos estribos rige el mismo criterio (s%d): la figura "
        "afirma que cambia" % (m1 + 1))
    for nom, ss in casos:
        assert len(ss) == 4, ("%s devolvio %d espaciamientos" % (nom, len(ss)))
        assert all(v > 0 for v in ss), ("%s tiene un espaciamiento nulo" % nom)
    print("  [ok] con 6 mm rige s%d y con 3/8\" rige s%d: el criterio CAMBIA"
          % (m1 + 1, m2 + 1))
    print("  [ok] los cuatro espaciamientos son positivos en los dos casos")


if __name__ == "__main__":
    main()
