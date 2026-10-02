# -*- coding: utf-8 -*-
"""Los modos de vibración del edificio, resueltos con OpenSeesPy.

POR QUE ESTA FIGURA
===================
El análisis estático de la E.030 entrega un cortante basal y lo reparte con
una fórmula. No dice **cómo se mueve el edificio**, y esa es justamente la
pregunta que el docente pone en la Clase 05 al hablar del periodo
fundamental y de los criterios de estructuración.

El modal la contesta, y contesta dos cosas que ningún número del análisis
estático puede dar:

  1. **CUÁL es el primer modo.** Si el edificio girara antes de
     trasladarse —modo torsional primero— la estructuración sería mala y el
     reparto por rigidez relativa dejaría de ser representativo. Acá los
     dos primeros modos son traslacionales puros y el torsional viene
     tercero: es la señal de una planta bien resuelta, y se ve de un
     vistazo en la forma dibujada.
  2. **Cuánta masa mueve cada modo.** El Art. 40.2 pide que los modos
     considerados sumen al menos el 90 % de la masa.

Y permite verificar el periodo por TRES caminos: el empírico `hn/CT` del
Art. 36, el de Rayleigh sobre la deformada estática, y el modal. Los tres
caen por debajo de `Tp`, que es lo que sostiene el `C = 2,50` con el que se
diseñó.
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
import paleta as PAL                                           # noqa: E402
import matplotlib                                              # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402
import textwrap                                                # noqa: E402


def _envolver(txt, ancho):
    """Parte el pie en lineas: sin esto tight ensancha la figura."""
    return chr(10).join(textwrap.wrap(txt, ancho))

COLOR_MODO = ["#c62828", "#1565c0", "#00796b"]


def datos():
    ruta = os.path.join(AQUI, "..", "calculo", "20_modelo_opensees.py")
    spec = importlib.util.spec_from_file_location("_m20", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        try:
            spec.loader.exec_module(m)
        except SystemExit:
            pass
    import _puente_compute as P
    with contextlib.redirect_stdout(_io.StringIO()):
        d, filas, Fi, V, T_emp, pesos, xm, ym = m.armar()
        res = P.correr(d)
        _peor, T_emp2, T_mod = m.contraste_deriva(res, Fi, pesos)
    return res["modal"], T_emp2, T_mod


def main():
    from proyecto import N_PISOS, H_ENTREPISO, T_P, C_T, HN
    md, T_emp, T_mod = datos()
    M = md["masa_total"]
    modos = md["modos"]
    alturas = [0.0] + [(i + 1) * H_ENTREPISO for i in range(N_PISOS)]

    # DOS FILAS, no cinco paneles en linea. Con todo en una fila la figura
    # salia de proporcion 4:1 y, puesta a 16 cm de ancho en la pagina, los
    # modos quedaban de 4 cm de alto: ilegibles, que es justo el defecto
    # que esta tanda de trabajo vino a corregir.
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 8.30), dpi=200)
    fig.suptitle("Modos de vibración resueltos con OpenSeesPy  ·  los dos "
                 "primeros son traslacionales y el torsional viene tercero",
                 fontsize=11.2, fontweight="bold", color=E.TINTA,
                 wrap=True)

    # ---- (a) las formas de los tres primeros modos ---------------------
    for k in range(3):
        # las tres formas siguen en fila: son altas y angostas
        ax = fig.add_axes((0.085 + k * 0.300, 0.555, 0.235, 0.310))
        x = modos[k]
        mx = 100.0 * x["masa_efectiva"]["X"] / M
        my = 100.0 * x["masa_efectiva"]["Y"] / M
        comp = "ux" if mx > my else "uy"
        dire = "X" if mx > my else "Y"
        torsional = max(mx, my) < 50.0
        if torsional:
            comp, dire = "rz", "giro"
        vals = [0.0] + [p[comp] for p in x["forma"]]
        esc = max(abs(v) for v in vals) or 1.0
        vals = [v / esc for v in vals]
        # EL SIGNO DE UN AUTOVECTOR ES ARBITRARIO: el solver puede devolver
        # el modo y su opuesto indistintamente, y los dos son el mismo modo.
        # Sin normalizarlo, el modo 1 salia dibujado hacia la izquierda y
        # los otros dos hacia la derecha, como si fueran cosas distintas.
        if vals[-1] < 0:
            vals = [-v for v in vals]
        ax.plot([0, 0], [0, alturas[-1]], color="#cfd6db", lw=1.0)
        ax.plot(vals, alturas, "-o", color=COLOR_MODO[k], lw=2.1, ms=5.0,
                zorder=4)
        for i in range(1, N_PISOS + 1):
            ax.plot([0, vals[i]], [alturas[i]] * 2, color=COLOR_MODO[k],
                    lw=0.7, alpha=0.5)
        ax.set_ylim(-0.4, alturas[-1] + 0.9)
        ax.set_xlim(-1.35, 1.35)
        ax.set_yticks(alturas)
        ax.set_yticklabels(["%.2f" % a for a in alturas], fontsize=7.4)
        ax.set_xticks([])
        ax.grid(axis="y", color="#e2e8f0", lw=0.6)
        ax.set_axisbelow(True)
        for s in ("top", "right", "bottom"):
            ax.spines[s].set_visible(False)
        if k == 0:
            ax.set_ylabel("altura (m)", fontsize=9)
        # TRES PANELES EN 6,30 PULGADAS son 2,0 por panel, y el subtitulo
        # «traslacional Y-Y  (99 % de masa)» mide 1,8 a 9,2 pt: los titulos
        # vecinos se tocaban. A 8,2 pt mide 1,6 y queda aire entre los tres.
        ax.set_title("Modo %d  ·  T = %.3f s\n%s"
                     % (x["modo"], x["T"],
                        "TORSIONAL (giro)" if torsional
                        else "traslacional %s · %.0f %% de masa"
                        % (dire, max(mx, my))),
                     fontsize=8.2, color=COLOR_MODO[k], fontweight="bold",
                     pad=8)

    # ---- (b) masa participativa por modo -------------------------------
    # los dos graficos, apilados: cada uno con el ancho entero
    ax2 = fig.add_axes((0.175, 0.380, 0.770, 0.145))
    n = len(modos)
    idx = range(n)
    mxs = [100.0 * x["masa_efectiva"]["X"] / M for x in modos]
    mys = [100.0 * x["masa_efectiva"]["Y"] / M for x in modos]
    ax2.barh([i - 0.19 for i in idx], mxs, 0.34, color="#1565c0",
             label="dirección X")
    ax2.barh([i + 0.19 for i in idx], mys, 0.34, color="#00796b",
             label="dirección Y")
    ax2.axvline(90.0, color=PAL.GOBIERNA, lw=1.6, ls=(0, (5, 3)))
    # con el eje invertido, "arriba" es el indice menor: puesto en n-0.35
    # el rotulo caia encima de los numeros del eje x
    ax2.text(88.0, -0.35, "90 % del Art. 40.2", fontsize=7.8,
             color=PAL.GOBIERNA, fontweight="bold", ha="right", va="bottom")
    ax2.set_yticks(list(idx))
    ax2.set_yticklabels(["modo %d" % x["modo"] for x in modos], fontsize=8)
    ax2.invert_yaxis()
    ax2.set_xlabel("masa participativa (%)", fontsize=9)
    ax2.set_xlim(0, 105)
    ax2.legend(fontsize=7.8, loc="lower right")
    ax2.grid(axis="x", color="#e2e8f0", lw=0.6)
    ax2.set_axisbelow(True)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)
    ax2.set_title("(b)  Cuánta masa mueve cada modo", fontsize=9.6,
                  loc="left", color=E.TINTA, pad=8)

    # ---- (c) los tres periodos contra Tp -------------------------------
    # deja sitio abajo para su propia escala y el pie
    ax3 = fig.add_axes((0.175, 0.190, 0.770, 0.145))
    etiquetas = ["empírico\nhn/CT", "Rayleigh\nX", "Rayleigh\nY",
                 "modal\nmodo 1"]
    valores = [T_emp, T_mod["X"], T_mod["Y"], modos[0]["T"]]
    ax3.bar(range(4), valores, 0.6,
            color=["#94a3b8", "#94a3b8", "#94a3b8", "#c62828"])
    ax3.axhline(T_P, color=PAL.GOBIERNA, lw=1.7, ls=(0, (5, 3)))
    ax3.text(3.45, T_P * 0.97, "Tp = %.2f s" % T_P, fontsize=8.2,
             color=PAL.GOBIERNA, fontweight="bold", ha="right", va="top")
    for i, v in enumerate(valores):
        ax3.annotate("%.3f" % v, (i, v), xytext=(i, v + T_P * 0.03),
                     ha="center", fontsize=8, color="#55606a")
    ax3.set_xticks(range(4))
    ax3.set_xticklabels(etiquetas, fontsize=7.6)
    ax3.set_ylabel("periodo (s)", fontsize=9)
    ax3.set_ylim(0, T_P * 1.18)
    ax3.grid(axis="y", color="#e2e8f0", lw=0.6)
    ax3.set_axisbelow(True)
    for s in ("top", "right"):
        ax3.spines[s].set_visible(False)
    ax3.set_title("(c)  Tres caminos, un periodo", fontsize=9.6,
                  loc="left", color=E.TINTA, pad=8)

    acx = sum(mxs)
    acy = sum(mys)
    # EL PIE SE ENVUELVE. En una sola linea medía 450 caracteres, y
    # `bbox_inches="tight"` ensancha la figura para que el texto quepa:
    # la imagen salia de proporcion 3:1 por culpa del pie, no de los
    # paneles. Un pie sin envolver deforma la figura entera.
    pie = (
        "Los %d modos suman %.1f %% de la masa en X y %.1f %% en Y, por "
        "encima del 90 %% que pide el Art. 40.2. Los tres caminos del periodo "
        "caen bajo Tp = %.2f s, asi que C = 2,50 con cualquiera de ellos: el "
        "edificio es rigido y el analisis estatico del Art. 33.2 es aplicable. "
        "La forma de los dos primeros modos es una recta creciente con la "
        "altura, sin cambio de signo, que es el modo fundamental de un "
        "edificio de muros bien estructurado."
        % (len(modos), acx, acy, T_P))
    _axp = fig.add_axes((0, 0, 1, 1), frame_on=False)
    _axp.set_axis_off()
    _yp = 0.076
    for _l in C.envolver(_axp, " ".join(pie.split()), 7.8, 0.90):
        fig.text(0.055, _yp, _l, fontsize=7.8, color="#55606a",
                 va="top")
        _yp -= (7.8 * 1.45 / 72.0) / fig.get_size_inches()[1]

    out = os.path.join(R.INFORME, "MODOS-DE-VIBRACION.png")
    C.guardar(fig, out)
    print()
    control(md, T_emp, T_mod)


def control(md, T_emp, T_mod):
    """Lo que la figura afirma sale del modelo, no del dibujo."""
    from proyecto import T_P
    M = md["masa_total"]
    modos = md["modos"]
    mx = [100.0 * x["masa_efectiva"]["X"] / M for x in modos]
    my = [100.0 * x["masa_efectiva"]["Y"] / M for x in modos]
    # 1. LA AFIRMACION DEL TITULO: los dos primeros son traslacionales y el
    #    torsional viene tercero. Es lo que la figura ensena, asi que es lo
    #    que hay que verificar.
    assert max(mx[0], my[0]) > 50.0, "el modo 1 no es traslacional"
    assert max(mx[1], my[1]) > 50.0, "el modo 2 no es traslacional"
    assert max(mx[2], my[2]) < 50.0, (
        "el modo 3 mueve %.1f %% de masa: no es el torsional que la figura "
        "anuncia" % max(mx[2], my[2]))
    # 2. el pie afirma que se supera el 90 % del Art. 40.2
    assert sum(mx) >= 90.0 and sum(my) >= 90.0, (
        "la masa acumulada no llega al 90 %%: %.1f en X, %.1f en Y"
        % (sum(mx), sum(my)))
    # 3. y que los tres caminos caen bajo Tp
    for nom, T in (("empirico", T_emp), ("Rayleigh X", T_mod["X"]),
                   ("Rayleigh Y", T_mod["Y"]), ("modal", modos[0]["T"])):
        assert T < T_P, "el periodo %s (%.3f s) supera Tp" % (nom, T)
    # 4. la forma del modo 1 no puede cambiar de signo: la figura dice que
    #    es una recta creciente, y un modo con nodo intermedio no lo es
    comp = "ux" if mx[0] > my[0] else "uy"
    vals = [p[comp] for p in modos[0]["forma"]]
    signos = set(1 if v > 0 else -1 for v in vals if abs(v) > 1e-12)
    assert len(signos) == 1, (
        "el modo 1 cambia de signo en altura y la figura lo dibuja como "
        "recta creciente")
    print("  [ok] modos 1 y 2 traslacionales, modo 3 torsional")
    print("  [ok] masa acumulada %.1f %% en X y %.1f %% en Y (Art. 40.2: 90)"
          % (sum(mx), sum(my)))
    print("  [ok] los cuatro periodos caen bajo Tp = %.2f s" % T_P)
    print("  [ok] el modo 1 no cambia de signo en altura")
    return True


if __name__ == "__main__":
    main()
