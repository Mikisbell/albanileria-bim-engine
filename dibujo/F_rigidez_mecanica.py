# -*- coding: utf-8 -*-
u"""LAMINA: por que un muro ancho y uno esbelto no se deforman igual.

QUE ENSENA, y por que hace falta. El reparto del cortante se hace por rigidez
relativa, y la rigidez de un muro en voladizo tiene DOS terminos --flexion y
corte-- cuyo peso depende solo de la esbeltez `h/L`. En un muro esbelto manda
la curvatura; en uno ancho manda la distorsion, y si se olvida el termino de
corte la rigidez de las medianeras sale gruesamente sobreestimada. La lamina
pone el mecanismo fisico al lado de la curva que lo cuantifica, y despues
muestra en que termina: la rigidez de la direccion Y concentrada en dos muros.

DE DONDE SALE CADA NUMERO. De `calculo/12_rigidez_lateral.py`, que es quien
arma la seccion de cada muro --con sus alas por cruce y sus columnas
transformadas-- y calcula `K`. Esta lamina no recalcula nada: pide.

POR QUE SE ESCRIBIO ESTE GENERADOR (2026-09-27). La figura existia como PNG
suelto en `salidas/informe/`, sin generador. Sus numeros estaban BIEN --se
verificaron uno por uno contra el SSOT-- pero nada lo garantizaba: el auditor
decia "las 41 figuras declaradas existen en disco" y estaba en verde porque
solo miraba existencia. Una figura que no se regenera envejece con aspecto de
verificada; en la tanda anterior otra lamina del mismo lote publicaba seis
numeros que ya no eran los del calculo.

Y LA CITA SE CORRIGIO. La version suelta titulaba "E.070 Art. 24.5" <!-- cita-ejemplo -->. **La
Norma E.070 tiene diez capitulos y ningun articulo 24 <!-- cita-ejemplo -->.** El 24.5 existe, pero
en los *Comentarios a la Norma Tecnica E.070* (San Bartolome, SENCICO 2008),
que comentan la version de 2006 --esa si organizada en articulos-- y que la
consigna enlaza. En la norma VIGENTE es el acapite 8.3.5, y la seccion
transformada del 24.6 es el 8.3.6. La cita era valida y estaba atribuida al
documento equivocado: un lector que busque el Art. 24.5 en la E.070 no lo
encuentra. Aca se citan los dos, que es lo que corresponde cuando el texto
que uno sigue y la norma vigente numeran distinto.
"""
from __future__ import print_function

import contextlib
import importlib.util
import io as _io
import math
import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                  # noqa: E402
from matplotlib.patches import Polygon, Rectangle                # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))
sys.path.insert(0, AQUI)

import paleta as PAL                                             # noqa: E402
import rutas as R                                                # noqa: E402
import cuadro as C                                             # noqa: E402

AZUL = "#2e5c9a"
AZUL_OSCURO = "#1f3f6b"
MORADO = "#7b3fa0"
CIAN = "#0277bd"
GRIS_TEXTO = "#37474f"
GRIS_SUAVE = "#6b7a88"
FONDO = "#f7f9fc"
BORDE = "#c5d5e6"


def _mod(nombre):
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location("_r" + nombre[:2], ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def coma(x, dec=2):
    return (("%%.%df" % dec) % x).replace(".", ",")


def miles(x, dec=0):
    u"""Separador de miles con espacio fino y coma decimal, como la casa.

    El operador `%` antiguo NO entiende la bandera de millares: hay que
    pasar por `format()`, que si la tiene.
    """
    s = format(round(x, dec), ",.%df" % dec)
    return s.replace(",", " ").replace(".", ",")


def reunir():
    u"""Pide al SSOT la seccion y la rigidez de los trece muros."""
    m12 = _mod("12_rigidez_lateral.py")
    import proyecto as P

    h_cm = m12.HN * 100.0
    muros = []
    for nom, dire, L, t, vanos in P.MUROS:
        A, I, Ac, Ln = m12.seccion(nom, dire, L, t, vanos)
        K, flex, corte = m12.rigidez(I, Ac)
        tot = flex + corte
        muros.append({
            "nom": nom.split()[0], "rotulo": nom, "dir": dire,
            "L": Ln, "K": K, "hL": h_cm / (Ln * 100.0),
            "p_flex": 100.0 * flex / tot, "p_corte": 100.0 * corte / tot,
        })
    d = {"muros": muros, "hn": m12.HN, "Em": m12.EM, "Gm": m12.GM,
         "Ec": m12.EC, "n": m12.N_TRANSF, "ala": m12.ALA, "fc": m12.FC,
         "fm": P.FM, "t": P.ESPESOR, "f_corte": m12.F_CORTE}

    # el cruce 50/50 es analitico y NO se escribe a mano: sale de igualar
    # los dos terminos de la formula compacta.  4x^3 = 3x  ->  x = raiz(3/4)
    d["cruce"] = math.sqrt(3.0 / 4.0)

    # el mas ancho y el mas esbelto, DERIVADOS: son los dos casos que el
    # panel (a) dibuja, y elegirlos a mano es como envejecen las figuras.
    d["ancho"] = min(muros, key=lambda x: x["hL"])
    d["esbelto"] = max(muros, key=lambda x: x["hL"])

    # reparto de rigidez en la direccion Y, que es donde se concentra
    d["rep"] = {}
    for dire in ("X", "Y"):
        ms = sorted((x for x in muros if x["dir"] == dire),
                    key=lambda x: -x["K"])
        tot = sum(x["K"] for x in ms)
        d["rep"][dire] = [(x, 100.0 * x["K"] / tot) for x in ms]
    d["conc_Y"] = sum(p for _m, p in d["rep"]["Y"][:2])
    d["max_X"] = d["rep"]["X"][0][1]
    return d


def p_flexion(x):
    u"""Fraccion de la deformacion que aporta la flexion, para h/L = x.

    Sale de la formula compacta: con I = t L^3/12, A_corte = t L y
    Gm = 0,40 Em, el cociente flexion/(flexion+corte) queda 4x^2/(4x^2+3),
    que no depende ni del modulo ni del espesor. Por eso la curva es UNA
    para todos los muros y cada uno solo elige su punto.
    """
    return 100.0 * 4.0 * x ** 2 / (4.0 * x ** 2 + 3.0)


def control(d):
    u"""Lo que la lamina AFIRMA tiene que ser verdad en la fuente."""
    # LA CURVA NO REPRODUCE EL SSOT, Y ESE ES EL PUNTO DE LA LAMINA.
    # La formula compacta vale para el ALMA RECTANGULAR. El SSOT arma la
    # seccion REAL --alas por cruce ortogonal (8.3.6) y columnas de
    # confinamiento transformadas-- y eso sube la inercia mucho mas de lo que
    # sube el area de corte: la fraccion de flexion BAJA. Medido en los trece
    # muros, la brecha va de 17 a 30 puntos y es SIEMPRE del mismo signo.
    # La version suelta de esta figura dibujaba el punto de cada muro SOBRE
    # la curva teorica y le ponia el rotulo del valor real --"MY-1 (82 %
    # corte)" sentado donde la curva da 65--: dos numeros incompatibles en el
    # mismo punto.
    for m in d["muros"]:
        m["p_flex_ideal"] = p_flexion(m["hL"])
        m["brecha"] = m["p_flex"] - m["p_flex_ideal"]
        assert m["brecha"] < 0.0, (
            "%s: la seccion real da MAS flexion (%.1f %%) que el alma "
            "rectangular (%.1f). Agregar alas y columnas solo puede subir la "
            "inercia, asi que la fraccion de flexion tiene que bajar: si sube "
            "hay un error en la seccion" % (m["nom"], m["p_flex"],
                                            m["p_flex_ideal"]))
    d["brecha_min"] = min(-m["brecha"] for m in d["muros"])
    d["brecha_max"] = max(-m["brecha"] for m in d["muros"])
    # y el orden por esbeltez tiene que sobrevivir: mas esbelto, mas flexion
    orden = sorted(d["muros"], key=lambda x: x["hL"])
    for a, b in zip(orden, orden[1:]):
        assert b["p_flex"] >= a["p_flex"] - 1e-6, (
            "el orden por esbeltez no se conserva: %s (h/L %.2f) da %.1f %% y "
            "%s (h/L %.2f) da %.1f" % (a["nom"], a["hL"], a["p_flex"],
                                       b["nom"], b["hL"], b["p_flex"]))
    assert abs(p_flexion(d["cruce"]) - 50.0) < 1e-9, (
        "el punto de cruce no reparte 50/50")
    # el mensaje central: en el ancho gobierna el corte, en el esbelto no
    assert d["ancho"]["p_corte"] > 50.0, (
        "la lamina dice que en el muro ancho gobierna el corte y aporta "
        "%.1f %%" % d["ancho"]["p_corte"])
    assert d["esbelto"]["p_flex"] > 50.0, (
        "la lamina dice que en el muro esbelto gobierna la flexion y aporta "
        "%.1f %%" % d["esbelto"]["p_flex"])
    assert d["ancho"]["hL"] < d["cruce"] < d["esbelto"]["hL"], (
        "los dos muros dibujados tienen que caer a lados distintos del cruce")
    # Gm = 0,40 Em es lo que hace valida la formula compacta (8.3.7)
    assert abs(d["Gm"] - 0.40 * d["Em"]) < 1e-6, (
        "la deduccion de la lamina supone Gm = 0,40 Em y el SSOT usa otro")
    assert d["conc_Y"] > 50.0, (
        "la lamina observa concentracion en Y y los dos mayores suman %.1f %%"
        % d["conc_Y"])
    print("  [ok] los 13 muros caen por DEBAJO del alma rectangular, entre "
          "%.0f y %.0f puntos" % (d["brecha_min"], d["brecha_max"]))
    print("  [ok] el orden por esbeltez se conserva en los 13")
    print("  [ok] el cruce 50/50 cae en h/L = %.4f = raiz(3/4)" % d["cruce"])
    print("  [ok] %s (h/L = %.2f) gobierna por CORTE con %.0f %%"
          % (d["ancho"]["nom"], d["ancho"]["hL"], d["ancho"]["p_corte"]))
    print("  [ok] %s (h/L = %.2f) gobierna por FLEXION con %.0f %%"
          % (d["esbelto"]["nom"], d["esbelto"]["hL"], d["esbelto"]["p_flex"]))


# --------------------------------------------------------------------------
# los cuatro paneles
# --------------------------------------------------------------------------
def _muro_deformado(ax, x0, ancho, alto, modo, color, rotulo, pie):
    u"""Dibuja un muro en voladizo deformado por flexion o por corte."""
    # el muro sin deformar, de referencia
    ax.add_patch(Rectangle((x0, 0), ancho, alto, fc="#e8edf3",
                           ec="#c5d5e6", lw=0.9, zorder=1))
    flecha = ancho * 0.42
    n = 40
    izq, der = [], []
    for i in range(n + 1):
        y = alto * i / float(n)
        s = y / alto
        # LA FORMA DE LA DEFORMADA NO ES DECORATIVA, es la del mecanismo:
        # en flexion, la elastica de un voladizo con carga en punta; en
        # corte, una distorsion de angulo constante, o sea una recta.
        dx = flecha * (1.5 * s ** 2 - 0.5 * s ** 3) if modo == "flexion" \
            else flecha * s
        izq.append((x0 + dx, y))
        der.append((x0 + ancho + dx, y))
    ax.add_patch(Polygon(izq + der[::-1], closed=True, fc=color, ec=color,
                         lw=1.4, alpha=0.30, zorder=2))
    ax.plot([p[0] for p in izq], [p[1] for p in izq], color=color, lw=1.6,
            zorder=3)
    ax.plot([p[0] for p in der], [p[1] for p in der], color=color, lw=1.6,
            zorder=3)
    # el empotramiento
    ax.add_patch(Rectangle((x0 - ancho * 0.18, -alto * 0.07),
                           ancho * 1.36, alto * 0.07, fc="#90a4ae",
                           ec="#607d8b", lw=0.8, zorder=4))
    # la fuerza en punta
    ax.annotate("", xy=(x0 + ancho + flecha, alto), zorder=5,
                xytext=(x0 + ancho + flecha + ancho * 0.55, alto),
                arrowprops=dict(arrowstyle="-|>", color=PAL.ALERTA, lw=1.8))
    ax.text(x0 + ancho + flecha + ancho * 0.62, alto, "V", fontsize=10,
            color=PAL.ALERTA, fontweight="bold", va="center", zorder=5)
    ax.text(x0 + ancho / 2.0, alto * 1.14, rotulo, fontsize=8.2,
            color=color, fontweight="bold", ha="center", va="bottom",
            zorder=5)
    ax.text(x0 + ancho / 2.0, -alto * 0.14, pie, fontsize=7.6,
            color=GRIS_TEXTO, ha="center", va="top", zorder=5,
            bbox=dict(boxstyle="round,pad=0.35", fc="#ffffff", ec=color,
                      lw=0.8))


def panel_mecanismos(ax, d):
    # 108 y no 100: la flecha de V y su letra viven mas alla del
    # segundo muro, y un dato fuera del xlim ensancha la figura.
    ax.set_xlim(0, 122)
    ax.set_ylim(-26, 108)
    ax.axis("off")
    ax.set_title("(a)  Los dos mecanismos de deformación en voladizo",
                 fontsize=10.2, fontweight="bold", color=AZUL_OSCURO,
                 loc="left", pad=8)
    e, a = d["esbelto"], d["ancho"]
    _muro_deformado(
        ax, 10, 14, 70, "flexion", MORADO,
        "MURO ESBELTO\n%s  (h/L = %s)" % (e["nom"], coma(e["hL"])),
        "Gobierna la FLEXIÓN (%s %%)\ncurvatura en altura\n"
        u"Δf = V·h³ / (3·Em·I)" % coma(e["p_flex"], 0))
    _muro_deformado(
        ax, 52, 34, 70, "corte", CIAN,
        "MURO ANCHO / MEDIANERA\n%s  (h/L = %s)" % (a["nom"], coma(a["hL"])),
        "Gobierna el CORTE (%s %%)\ndistorsión romboidal\n"
        u"Δv = 1,2·V·h / (Gm·Ac)" % coma(a["p_corte"], 0))


def panel_curva(ax, d):
    u"""La curva del alma rectangular, y donde caen los muros DE VERDAD."""
    xs = [0.02 + i * 0.03 for i in range(95)]
    ax.plot(xs, [100.0 - p_flexion(x) for x in xs], color=CIAN, lw=2.2,
            label="CORTE, alma rectangular")
    ax.plot(xs, [p_flexion(x) for x in xs], color=MORADO, lw=2.2,
            label="FLEXIÓN, alma rectangular")
    c = d["cruce"]
    ax.axvline(c, color=GRIS_SUAVE, lw=1.0, ls=(0, (5, 3)))
    ax.plot([c], [50.0], "o", color=PAL.ALERTA, ms=7, zorder=5)
    ax.annotate("cruce 50/50 en h/L = √0,75 = %s" % coma(c, 3),
                xy=(c, 50), xytext=(0.26, 66), fontsize=7.8,
                color=PAL.ALERTA, fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=PAL.ALERTA, lw=0.9))

    # LOS MUROS REALES, con el valor que calcula el SSOT --no el de la curva.
    # Caen sistematicamente por debajo porque su seccion NO es el alma sola:
    # lleva las alas del 8.3.6 y las columnas transformadas.
    vistos = set()
    for m in sorted(d["muros"], key=lambda x: x["hL"]):
        clave = coma(m["hL"], 2)
        if clave in vistos:
            continue
        vistos.add(clave)
        ax.plot([m["hL"], m["hL"]], [m["p_flex"], m["p_flex_ideal"]],
                color="#b0bec5", lw=1.0, ls=":", zorder=4)
        ax.plot([m["hL"]], [m["p_flex"]], "s", color=MORADO, ms=6.5,
                mec="#ffffff", mew=1.1, zorder=6)

    # LAS ETIQUETAS VAN A FRANJAS LIBRES. Con la morada subiendo y la azul
    # bajando, el area util no es el rectangulo del grafico: queda la banda
    # de abajo a la derecha y la de arriba a la izquierda. Puestas "al lado"
    # del punto, el auditor midio que las tapaban 6 y 8 piezas de dibujo.
    for m, dx, dy in ((d["ancho"], 0.72, -14), (d["esbelto"], 0.10, -46)):
        ax.annotate("%s: %s %% corte\n(h/L = %s)"
                    % (m["nom"], coma(m["p_corte"], 0), coma(m["hL"])),
                    xy=(m["hL"], m["p_flex"]),
                    xytext=(m["hL"] + dx, m["p_flex"] + dy),
                    fontsize=7.8, color=AZUL_OSCURO, fontweight="bold",
                    ha="center",
                    arrowprops=dict(arrowstyle="->", color=AZUL_OSCURO,
                                    lw=1.0))

    ax.plot([], [], "s", color=MORADO, ms=6.5, mec="#ffffff",
            label="FLEXIÓN, sección real del muro")
    ax.set_xlabel("esbeltez del muro en voladizo  h / L", fontsize=9)
    ax.set_ylabel("participación en la deformación (%)", fontsize=9)
    ax.set_ylim(0, 103)
    ax.set_xlim(0, 2.9)
    ax.grid(True, ls=":", lw=0.6, color="#cfd8dc")
    ax.legend(fontsize=7.6, loc="upper left", framealpha=0.95)
    ax.set_title("(b)  La curva de clase, y dónde cae cada muro de verdad",
                 fontsize=10.2, fontweight="bold", color=AZUL_OSCURO,
                 loc="left", pad=8)
    ax.tick_params(labelsize=8)
    # LA NOTA SALE DEL EJE. Dentro, se montaba sobre la curva de corte
    # y sobre la etiqueta del cruce: el area util de un grafico con dos
    # curvas que se cruzan es mucho menor de lo que aparenta.
    d["nota_b"] = ("Los trece muros caen entre %s y %s puntos POR DEBAJO "
                   "de la curva. No es error: la curva vale para el alma "
                   "sola, y la sección real lleva las alas por cruce "
                   "(8.3.6) y las columnas transformadas, que suben la "
                   "inercia más que el área de corte — así que el corte "
                   "pesa aún más."
                   % (coma(d["brecha_min"], 0), coma(d["brecha_max"], 0)))


def panel_reparto(ax, d):
    ms = d["rep"]["Y"]
    idx = list(range(len(ms)))
    ax.barh(idx, [p for _m, p in ms],
            color=[CIAN if p > 20 else "#7eb0dd" for _m, p in ms],
            height=0.62, zorder=3)
    for i, (m, p) in enumerate(ms):
        ax.text(p + 1.0, i, "%s %%   (%s kgf/cm)" % (coma(p, 1),
                                                     miles(m["K"])),
                fontsize=8.0, va="center", fontweight="bold",
                color=GRIS_TEXTO, zorder=4)
    ax.set_yticks(idx)
    ax.set_yticklabels([m["nom"] for m, _p in ms], fontsize=8.2)
    ax.invert_yaxis()
    ax.set_xlim(0, max(p for _m, p in ms) * 1.72)
    ax.set_xlabel("participación en la rigidez de la dirección Y (%)",
                  fontsize=9)
    ax.grid(True, axis="x", ls=":", lw=0.6, color="#cfd8dc")
    ax.set_title("(c)  En qué termina: la rigidez de Y, muro por muro",
                 fontsize=10.2, fontweight="bold", color=AZUL_OSCURO,
                 loc="left", pad=8)
    ax.tick_params(labelsize=8)


def panel_deduccion(ax, d):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.set_title("(d)  De dónde sale la fórmula, y con qué acápite",
                 fontsize=10.2, fontweight="bold", color=AZUL_OSCURO,
                 loc="left", pad=8)
    bloques = [
        ("1.  Desplazamiento del voladizo: los dos términos se suman",
         [u"Δ = Δf + Δv = V·h³/(3·Em·I)  +  1,2·V·h/(Gm·Ac)",
          "Comentarios a la E.070, Art. 24.5  ·  norma vigente 8.3.5"]),
        ("2.  Sustituyendo la sección rectangular (I = t·L³/12, Ac = t·L)",
         [u"término de flexión  →  4/(Em·t) · (h/L)³",
          u"término de corte    →  3/(Em·t) · (h/L)   [con Gm = 0,40 Em]"]),
        ("3.  La forma compacta que se usa en clase",
         [u"K = V/Δ = (Em·t) / [ 4(h/L)³ + 3(h/L) ]",
          "El SSOT lo comprueba como IDENTIDAD, no lo supone: si alguien "
          "toca Gm o el factor de corte, el control falla"]),
        ("4.  Parámetros de este proyecto, con su acápite",
         [u"Em = 500 f'm = %s kgf/cm²   ·   Gm = 0,40 Em = %s   (8.3.7)"
          % (miles(d["Em"]), miles(d["Gm"])),
          u"Ec = 15 000√f'c = %s kgf/cm²   ·   n = Ec/Em = %s   (E.060)"
          % (miles(d["Ec"]), coma(d["n"])),
          u"Ala por cruce ortogonal: 6·t = %s m   (8.3.6)" % coma(d["ala"])]),
    ]
    y = 96.0
    for titulo, lineas in bloques:
        ax.text(1.0, y, titulo, fontsize=8.4, fontweight="bold",
                color=AZUL_OSCURO, va="top")
        y -= 5.0
        for ln in lineas:
            envuelto = textwrap.wrap(ln, 86)
            ax.text(3.2, y, "\n".join(envuelto), fontsize=7.8,
                    color=GRIS_TEXTO, va="top", linespacing=1.35)
            y -= 5.8 * len(envuelto)
        y -= 2.0
    assert y > -2.0, "la deducción del panel (d) desborda su caja"


def dibujar():
    d = reunir()
    control(d)

    _dos_laminas(d)


def _dos_laminas(d):
    """Mecanismo y consecuencia, una lamina cada una. Ver el porque arriba."""
    pie_a = ("El término de corte no es un refinamiento: en las medianeras "
             "aporta el %s %% de la deformación, y omitirlo sobreestimaría "
             "su rigidez —y con ella el cortante que se les asigna—. La "
             "curva es una sola porque el reparto 4x²/(4x²+3) no depende del "
             "módulo ni del espesor: cada muro sólo elige su punto."
             % coma(d["ancho"]["p_corte"], 0))
    pie_b = (u"OBSERVACIÓN DE REDUNDANCIA: las dos medianeras concentran "
             u"el %s %% de la rigidez en Y, mientras que en X —%d muros— el "
             u"reparto es parejo y ninguno pasa del %s %%. Se declara "
             u"CONFORME CON OBSERVACIÓN, no conforme a secas: el modelo es "
             u"elástico-lineal y NO demuestra que la rigidez se redistribuya "
             u"al fisurarse. El panel de abajo muestra de dónde sale la "
             u"fórmula con que se reparte el cortante."
             % (coma(d["conc_Y"], 1), len(d["rep"]["X"]),
                coma(d["max_X"], 1)))
    for n_lam, (paneles, titulo, sub, pie) in enumerate((
            ((panel_mecanismos, panel_curva),
             u"Mecánica de la rigidez lateral: por qué un muro ancho y uno "
             u"esbelto no se deforman igual",
             u"Reparto flexión / corte según la esbeltez h/L", pie_a),
            ((panel_reparto, panel_deduccion),
             u"Consecuencia: la concentración de rigidez en la dirección Y",
             u"A quién le toca el cortante, y de dónde sale la fórmula",
             pie_b)), 1):
        fig = plt.figure(figsize=(C.ANCHO_PAGINA, 8.30), dpi=200)
        fig.patch.set_facecolor(PAL.PAPEL)
        y_ar, y_ab = C.marco(fig, titulo,
                             pie=pie + '  Base: Comentarios a la E.070 24.5–24.8, hoy 8.3.5–8.3.8.', subtitulo=sub,
                             fs_tit=11.5, color_tit=AZUL_OSCURO)
        gs = fig.add_gridspec(2, 1, left=0.115, right=0.975, top=y_ar,
                              bottom=y_ab, hspace=0.42)
        for k, panel in enumerate(paneles):
            panel(fig.add_subplot(gs[k, 0]), d)
        C.guardar(fig, os.path.join(R.INFORME,
                                    "RIGIDEZ-MECANICA-%d.png" % n_lam))
    return


if __name__ == "__main__":
    dibujar()
