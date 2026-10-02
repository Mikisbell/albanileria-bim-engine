# -*- coding: utf-8 -*-
"""Modelo computacional: qué aporta el modelo que el cálculo manual no ve.

QUE PIDE LA RUBRICA
===================
Criterio 7, *"Herramientas modernas"*, 2 puntos. La sección tenía 1 791
palabras y **ni un gráfico**, que es justo lo que la ingeniera valora.

QUE MUESTRA, Y POR QUE ASI
==========================
El hallazgo de esta sección es contraintuitivo y merece verse, no leerse:

  **El reparto manual SUBESTIMA a seis muros.** El manual reparte el
  cortante por rigidez relativa y le suma torsión; el modelo no reparte
  nada, resuelve el equilibrio del conjunto con los cinco diafragmas
  puestos, y el reparto es lo que sale. A MY-3a y MY-4a el modelo les pide
  **+72 %** más cortante.

  **Y aun así los trece cumplen.** Esa es la conclusión que hace válido el
  diseño, y por eso el panel de la derecha la muestra: el `Ve/(0,55 Vm)`
  calculado con el cortante del modelo sigue por debajo de 1,00.

El gráfico de barras pareadas es el formato que deja ver las dos cosas a la
vez: dónde difieren y si eso importa.
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

MANUAL = "#5b7fa6"
MODELO = "#c0560f"
LIMITE = "#b02a1f"


def datos():
    """(nom, dir, manual, modelo, %) por muro, llamando a la API del 20.

    La primera version PARSEABA el stdout del script y fallaba: el formato de
    una tabla impresa no es una interfaz. El 20 ya expone `contraste_reparto`,
    que devuelve exactamente estas filas.
    """
    ruta = os.path.join(AQUI, "..", "calculo", "20_modelo_opensees.py")
    spec = importlib.util.spec_from_file_location("_m20", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
        dat, filas, Fi, V, T_emp0, pesos, xm, ym = m.armar()
        res = m._puente_compute.correr(dat)
        filas_out, _rep, _V = m.contraste_reparto(dat, res, filas, Fi, xm, ym)
        # y el USO REAL del 8.5.2 con el cortante del modelo, que es la
        # conclusion que valida el diseno. La primera version graficaba el
        # cociente modelo/manual con una linea roja rotulada "limite del
        # 8.5.2": ese cociente NO tiene relacion con el 8.5.2, que es
        # Ve <= 0,55 Vm. Un grafico que ensena algo falso es peor que no
        # tenerlo, y este iba a un informe que se califica por lo didactico.
        R18 = m.R18
        muros, _V = R18.datos()
        mm = {mu["nom"]: mu for mu in muros}
        usos = {}
        for nom, dire, man, mod in filas_out:
            mu = mm[nom]
            Vm = R18.resistencia(mu, 0)
            Ve_mod = mod / R18.FACTOR_MODERADO
            usos[nom] = Ve_mod / (0.55 * Vm)
    return [(nom.split()[0], dire, man, mod,
             100.0 * (mod - man) / man, usos[nom])
            for nom, dire, man, mod in filas_out]


def main():
    filas = datos()

    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 7.60), dpi=200)
    y_ar, y_ab = C.marco(
        fig, u"Modelo computacional  ·  qué agrega sobre el cálculo manual",
        pie=(u"El manual reparte por rigidez relativa y suma torsión; el "
             u"modelo no reparte: resuelve el equilibrio del conjunto con "
             u"los cinco diafragmas puestos, y el reparto es lo que sale. "
             u"Los %d muros cumplen el 8.5.2 TAMBIÉN con el cortante del "
             u"modelo." % len(filas)))
    _h = (y_ar - y_ab - 0.07) / 2.0

    # ---- (a) barras pareadas: manual contra modelo -----------------------
    # APILADOS: el (a) son trece muros pareados y pide el ancho
    # entero; el (b) va debajo.
    ax = fig.add_axes((0.125, y_ab + _h + 0.07, 0.84, _h * 0.74))
    n = len(filas)
    xs = range(n)
    w = 0.38
    ax.bar([x - w / 2 for x in xs], [f[2] / 1000.0 for f in filas], w,
           color=MANUAL, label="reparto MANUAL (rigidez + torsión)")
    ax.bar([x + w / 2 for x in xs], [f[3] / 1000.0 for f in filas], w,
           color=MODELO, label="reparto del MODELO (equilibrio)")
    for k, f in enumerate(filas):
        if abs(f[4]) >= 10.0:
            ax.annotate("%+.0f%%" % f[4],
                        (k, max(f[2], f[3]) / 1000.0), ha="center",
                        va="bottom", fontsize=7.5,
                        color=(MODELO if f[4] > 0 else MANUAL),
                        fontweight="bold")
    ax.set_xticks(list(xs))
    ax.set_xticklabels([f[0] for f in filas], rotation=45, ha="right",
                       fontsize=8)
    ax.set_ylabel("cortante del 1.er entrepiso  (tonf)", fontsize=9)
    ax.legend(fontsize=8.5, frameon=False, loc="upper left")
    ax.set_title("(a)  El manual subestima a seis muros: el modelo les pide "
                 "más", fontsize=10, loc="left", color=E.TINTA, pad=8)
    ax.grid(axis="y", color="#dde3e8", lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    # ---- (b) y aun asi todos cumplen ------------------------------------
    ax2 = fig.add_axes((0.125, y_ab, 0.84, _h * 0.74))
    usos = [f[5] for f in filas]
    ax2.axhline(1.0, color=LIMITE, lw=1.6, ls="--")
    ax2.annotate("límite del 8.5.2  (Ve = 0,55 Vm)", (len(filas) / 2.0, 1.0),
                 xytext=(len(filas) / 2.0, 1.04), ha="center", fontsize=8.5,
                 color=LIMITE, fontweight="bold")
    ax2.bar(range(len(filas)), usos, 0.7,
            color=["#2e7d52" if u < 1.0 else LIMITE for u in usos])
    peor = max(range(len(filas)), key=lambda k: usos[k])
    _et = filas[peor][0] + chr(10) + ("%.2f" % usos[peor])
    ax2.annotate(_et,
                 (peor, usos[peor]), xytext=(peor, usos[peor] + 0.05),
                 ha="center", fontsize=8, color=E.TINTA, fontweight="bold")
    ax2.set_xticks([])
    ax2.set_ylim(0, 1.25)
    ax2.set_ylabel("Ve del modelo / (0,55 Vm)", fontsize=9)
    ax2.set_title("(b)  Y aun así los 13 cumplen", fontsize=10, loc="left",
                  color=E.TINTA, pad=8)
    ax2.grid(axis="y", color="#dde3e8", lw=0.6)
    ax2.set_axisbelow(True)
    for s in ("top", "right"):
        ax2.spines[s].set_visible(False)


    out = os.path.join(R.INFORME, "MODELO-COMPUTACIONAL.png")
    C.guardar(fig, out)
    print()
    control(filas)
    periodo()


def control(filas):
    assert len(filas) == 13, (
        "se leyeron %d muros del reparto y son 13" % len(filas))
    # el modelo tiene que pedir MAS a alguno: si no, la figura no dice nada
    subestimados = [f[0] for f in filas if f[4] > 10.0]
    assert subestimados, "ningun muro sale subestimado: revisar la lectura"
    # y las dos columnas tienen que ser numeros distintos de cero
    for nom, dire, man, mod, pct, uso in filas:
        assert man > 0 and mod > 0, ("%s tiene un cortante nulo" % nom)
        assert uso < 1.0, (
            "%s usa el %.2f de su limite del 8.5.2 con el cortante del "
            "modelo: la figura afirmaria algo falso" % (nom, uso))
    print("  [ok] %d muros leidos del reparto del script 20" % len(filas))
    print("  [ok] %d muros que el manual subestima mas del 10 %%: %s"
          % (len(subestimados), ", ".join(subestimados)))
    print("  [ok] el mayor desvio es %+.1f %%"
          % max(f[4] for f in filas))
    print("  [ok] el mas exigido con el modelo usa el %.0f %% del 8.5.2"
          % (100.0 * max(f[5] for f in filas)))




# ======================================================================
def periodo():
    """El periodo empírico de la norma contra el del modelo.

    Es lo que valida el contraste: si el modelo diera un periodo muy
    distinto del empírico, habría que dudar del modelo o de la norma. Y
    hay un dato que importa para el diseño: los tres caen por debajo de
    Tp = 0,60 s, o sea en la meseta del espectro donde C = 2,50.
    """
    ruta = os.path.join(AQUI, "..", "calculo", "20_modelo_opensees.py")
    spec = importlib.util.spec_from_file_location("_m20p", ruta)
    m = importlib.util.module_from_spec(spec)
    buf = _io.StringIO()
    with contextlib.redirect_stdout(buf):
        spec.loader.exec_module(m)
        dat, filas, Fi, V, T_emp, pesos, xm, ym = m.armar()
        res = m._puente_compute.correr(dat)
        peor_d, T_emp2, T_mod = m.contraste_deriva(res, Fi, pesos)
    Tx, Ty = T_mod["X"], T_mod["Y"]
    Tp = 0.60          # E.030, suelo S2: la meseta del espectro llega a Tp

    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 5.10), dpi=200)
    y_ar, y_ab = C.marco(
        fig, u"Periodo fundamental  ·  la norma contra el modelo",
        pie=(u"El modelo da un periodo %.0f %% menor que el "
             u"empírico: el edificio es más rígido de lo que la "
             u"fórmula de la norma supone, que es lo esperable en "
             u"albañilería. Los tres valores caen por debajo de Tp, "
             u"así que el diseño usa C = 2,50 con cualquiera de ellos "
             u"y el contraste no cambia una sola cifra."
             % (100.0 * (1 - min(Tx, Ty) / T_emp))))
    ax = fig.add_axes((0.135, y_ab, 0.83, y_ar - y_ab - 0.04))
    ns = ["E.030 Art. 36\nempírico  hn/CT", "modelo\nRayleigh en X",
          "modelo\nRayleigh en Y"]
    vs = [T_emp, Tx, Ty]
    ax.bar(range(3), vs, 0.5, color=["#5b7fa6", MODELO, "#8d6e3a"])
    for i, v in enumerate(vs):
        ax.annotate("%.3f s" % v, (i, v), xytext=(i, v + 0.012),
                    ha="center", fontsize=10, color=E.TINTA,
                    fontweight="bold")
    ax.axhline(Tp, color=LIMITE, lw=1.8, ls="--")
    ax.annotate("Tp = %.2f s  ·  fin de la meseta del espectro (C = 2,50)"
                % Tp, (1, Tp), xytext=(-0.42, Tp * 0.90), fontsize=9,
                color=LIMITE, fontweight="bold")
    ax.set_xticks(range(3))
    ax.set_xticklabels(ns, fontsize=9)
    ax.set_ylabel("periodo fundamental  T  (s)", fontsize=9)
    ax.set_ylim(0, Tp * 1.15)
    ax.grid(axis="y", color="#dde3e8", lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    out = os.path.join(R.INFORME, "PERIODO-NORMA-MODELO.png")
    C.guardar(fig, out)
    print("  PERIODO-NORMA-MODELO.png")
    assert max(T_emp, Tx, Ty) < Tp, (
        "la figura dice que los tres periodos caen bajo Tp = %.2f y el "
        "mayor es %.3f" % (Tp, max(T_emp, Tx, Ty)))
    print("  [ok] los tres periodos caen bajo Tp = %.2f s: C = 2,50" % Tp)
    return T_emp, Tx, Ty

if __name__ == "__main__":
    main()
