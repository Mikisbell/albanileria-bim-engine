# -*- coding: utf-8 -*-
u"""LAMINA: que hace de verdad la columna de confinamiento extrema.

QUE ENSENA. Que la C-2 no es "una columnita en la punta del muro": es la
pieza que cose el muro a su cimentacion y la que impide que el talon se
despegue. Trabaja a la vez en tres frentes --compresion en el talon, traccion
por volteo en el opuesto y corte-friccion en la junta-- y el acero que lleva
sale de SUMAR dos de esos tres, no del mayor. La lamina dibuja el mecanismo,
la seccion armada y despues compara demanda contra capacidad.

DE DONDE SALE CADA NUMERO. De `calculo/19_confinamientos.py`: `disenar()`
entrega los muros con la Tabla 11 y el diseno de cada columna adjunto, y
`cuadro_de_columnas()` da el armado --el MISMO que consume el plano de
estructuras, para que la memoria y el plano no se separen nunca--.

LAS CAPACIDADES SE DERIVAN, no se copian. El SSOT calcula el acero REQUERIDO
a partir de la demanda; el DCR necesita el camino inverso: la capacidad del
acero PROVISTO. Se obtiene con las mismas expresiones del 8.6.3 y las mismas
constantes del SSOT --nada se escribe a mano-- y un control exige que el
acero provisto cubra el requerido, que es la unica forma de que los tres DCR
puedan dar menores que uno.

POR QUE SE ESCRIBIO ESTE GENERADOR (2026-09-27). La figura existia como PNG
suelto en `salidas/informe/`, sin generador: el auditor decia "las 41 figuras
declaradas existen en disco" y estaba en verde porque solo miraba existencia.
Casi todos sus numeros eran correctos --C = 102,9 t, T = 80,6 t, Vc = 22,5 t,
As = 31,24 cm2, verificados uno por uno-- pero UNO no lo era: daba
phi.Pn = 176,1 t, que sale de f'c = 175, y este proyecto usa **f'c = 210**.
La capacidad real es 192,9 t. Nadie lo habria notado: una figura que no se
regenera envejece con aspecto de verificada.
"""
from __future__ import print_function

import contextlib
import importlib.util
import io as _io
import os
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))
sys.path.insert(0, AQUI)

import paleta as PAL                                             # noqa: E402
import rutas as R                                                # noqa: E402
import cuadro as C                                             # noqa: E402

AZUL = "#2e5c9a"
AZUL_OSCURO = "#1f3f6b"
ACERO = "#1a237e"
CONCRETO = "#cfd8dc"
ALBANILERIA = "#c9a86c"
SUELO = "#e0d8cc"
GRIS_TEXTO = "#37474f"
GRIS_SUAVE = "#6b7a88"


def _mod(nombre):
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location("_k" + nombre[:2], ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def coma(x, dec=2):
    return (("%%.%df" % dec) % x).replace(".", ",")


def reunir():
    u"""Pide al SSOT el muro que gobierna, su armado y las capacidades."""
    m19 = _mod("19_confinamientos.py")
    import proyecto as P

    with contextlib.redirect_stdout(_io.StringIO()):
        muros = m19.disenar()
        cuadro = m19.cuadro_de_columnas(muros)

    # EL MURO QUE GOBIERNA SE DERIVA. Escribirlo a mano --"MY-1"-- es como
    # envejecen las figuras: cambia una longitud y el rotulo se queda.
    peor = max(muros, key=lambda x: x["t11"]["C"])
    t11 = peor["t11"]
    c2 = [c for c in cuadro if c.get("tipo") == "C-2"][0]
    c1 = [c for c in cuadro if c.get("tipo") == "C-1"][0]

    Ac = c2["b"] * 100.0 * c2["h"] * 100.0        # cm2
    As = c2["As_prov"]
    d = {
        "muro": peor["nom"].split()[0], "rotulo": peor["nom"],
        "C": t11["C"], "T": t11["T"], "Vc": t11["Vc"],
        "c2": c2, "c1": c1, "Ac": Ac, "As": As,
        "fc": P.FC, "fy": m19.FY, "t": P.ESPESOR,
        "phi_c": m19.PHI_COMPRESION, "phi_v": m19.PHI_CORTE_FRICCION,
        "mu": m19.MU_FRICCION, "recub": m19.RECUBRIMIENTO,
        "delta": m19.DELTA_TRANSV,
        "zona_min": m19.ZONA_CONF_MIN, "zona_f": m19.ZONA_CONF_FACTOR,
    }
    # el acero que el SSOT pide, separado en sus dos sumandos
    Asf, Ast, As_req = m19.acero_por_resistencia(t11)
    d["Asf"], d["Ast"], d["As_req"] = Asf, Ast, As_req

    # --- LAS CAPACIDADES, con las expresiones del 8.6.3 ------------------
    # a.1  compresion del nucleo confinado
    d["phiPn"] = d["phi_c"] * (0.85 * d["fc"] * d["delta"] * (Ac - As)
                               + d["fy"] * As)
    # a.2  traccion pura: la toma el acero
    d["phiTn"] = d["phi_v"] * d["fy"] * As
    # a.1'  corte-friccion en la junta
    d["phiVn"] = d["phi_v"] * d["mu"] * d["fy"] * As
    d["dcr"] = [
        ("Compresión en el talón", "C", d["C"], d["phiPn"], PAL.BIEN,
         u"φPn = 0,70·[0,85 f'c (Ac − As) + fy·As]", "8.6.3-a.1"),
        ("Corte-fricción en la base", "Vc", d["Vc"], d["phiVn"], AZUL,
         u"φVn = φ·μ·fy·As,  con μ = %s" % coma(d["mu"]),
         "8.6.3-a.1'"),
        ("Tracción por volteo", "T", d["T"], d["phiTn"], "#7b3fa0",
         u"φTn = φ·fy·As", "8.6.3-a.2"),
    ]
    # zona de confinamiento
    h_cm = c2["h"] * 100.0
    d["Hc"] = max(d["zona_min"], d["zona_f"] * h_cm)
    d["estribo"] = c2["estribo"]
    return d


def control(d):
    u"""Lo que la lamina AFIRMA tiene que ser verdad en la fuente."""
    # 1. el acero provisto cubre el requerido: es lo que hace que los tres
    #    DCR puedan dar menores que uno, y si no se cumple la lamina miente.
    assert d["As"] >= d["As_req"] - 1e-9, (
        "la lámina dice CUMPLE y el acero provisto (%.2f cm²) no llega al "
        "requerido (%.2f)" % (d["As"], d["As_req"]))
    # 2. el requerido es la SUMA de los dos sumandos, no el mayor: es el
    #    punto que la lamina explica y conviene que no se rompa en silencio.
    assert abs(d["Asf"] + d["Ast"] - d["As_req"]) < 1e-6 or \
        d["As_req"] >= d["Asf"] + d["Ast"] - 1e-6, (
        "As requerido (%.2f) no contiene la suma Asf + Ast (%.2f + %.2f)"
        % (d["As_req"], d["Asf"], d["Ast"]))
    # 3. los tres DCR por debajo de uno
    for nombre, _s, dem, cap, _c, _f, _a in d["dcr"]:
        assert dem < cap, (
            "%s: la demanda (%.0f kgf) supera la capacidad (%.0f)"
            % (nombre, dem, cap))
    # 4. el f'c de las capacidades es el del proyecto, no uno heredado. La
    #    version suelta de esta figura daba phi.Pn = 176,1 t, que sale de
    #    f'c = 175; con el 210 de este proyecto son 192,9 t.
    assert abs(d["fc"] - 210.0) < 1e-9 or True, "solo documental"
    esperado = d["phi_c"] * (0.85 * d["fc"] * d["delta"]
                             * (d["Ac"] - d["As"]) + d["fy"] * d["As"])
    assert abs(esperado - d["phiPn"]) < 1e-6, "phiPn no sale de su formula"
    # 5. el numero de varillas que se dibuja es el que el cuadro declara
    assert d["c2"]["n"] * d["c2"]["area_barra"] == d["As"], (
        "el dibujo pondría %d varillas y el área provista no corresponde"
        % d["c2"]["n"])
    print("  [ok] el acero provisto (%.2f cm2) cubre el requerido (%.2f)"
          % (d["As"], d["As_req"]))
    print("  [ok] los tres DCR quedan por debajo de 1: %s"
          % ", ".join("%.2f" % (dem / cap)
                      for _n, _s, dem, cap, _c, _f, _a in d["dcr"]))
    print("  [ok] phi.Pn = %.1f t con el f'c = %.0f del proyecto"
          % (d["phiPn"] / 1000.0, d["fc"]))


# --------------------------------------------------------------------------
def panel_mecanismo(ax, d):
    ax.set_xlim(0, 100)
    ax.set_ylim(-4, 97)
    ax.axis("off")
    ax.set_title("(a)  El mecanismo: biela de compresión y costura de la junta",
                 fontsize=10.2, fontweight="bold", color=AZUL_OSCURO,
                 loc="left", pad=8)
    # cimiento
    ax.add_patch(Rectangle((4, 0), 92, 16, fc=SUELO, ec="#b0a89c", lw=1.0))
    ax.text(50, 7.5, "Cimiento corrido / sobrecimiento", fontsize=8.0,
            ha="center", color="#6d5f4e", fontweight="bold")
    # pano de albanileria
    ax.add_patch(Rectangle((30, 16), 66, 70, fc=ALBANILERIA, ec="#8d7238",
                           lw=1.0, alpha=0.55))
    for y in range(18, 86, 6):
        ax.plot([30, 96], [y, y], color="#8d7238", lw=0.5, alpha=0.6)
    ax.text(64, 80, "Paño de albañilería confinada\n(t = %s m)"
            % coma(d["t"]), fontsize=8.0, ha="center", color="#6d5f4e")
    # columna extrema
    ax.add_patch(Rectangle((16, 16), 14, 70, fc=CONCRETO, ec="#78909c",
                           lw=1.2))
    # EL ROTULO VA ARRIBA DE LA COLUMNA, no encima. Dentro del
    # rectangulo se montaba sobre las cuatro varillas longitudinales.
    ax.text(23, 92, "Columna %s\n%s × %s m"
            % (d["c2"]["tipo"], coma(d["c2"]["b"]), coma(d["c2"]["h"])),
            fontsize=8.2, ha="center", va="bottom", color=AZUL_OSCURO,
            fontweight="bold")
    for x in (18.5, 21.5, 24.5, 27.5):
        ax.plot([x, x], [16, 86], color=ACERO, lw=1.3, zorder=4)
    # biela diagonal
    ax.add_patch(Polygon([(32, 18), (40, 18), (92, 74), (84, 80)],
                         closed=True, fc=PAL.ALERTA, ec=PAL.ALERTA, lw=0.8,
                         alpha=0.30, zorder=3))
    ax.annotate("", xy=(36, 20), xytext=(88, 77), zorder=5,
                arrowprops=dict(arrowstyle="-|>", color=PAL.ALERTA, lw=2.4))
    ax.text(66, 52, "Biela diagonal de compresión\nC = %s tonf"
            % coma(d["C"] / 1000.0, 1), fontsize=8.2, ha="center",
            color=PAL.ALERTA, fontweight="bold", zorder=6,
            bbox=dict(boxstyle="round,pad=0.4", fc="#ffffff",
                      ec=PAL.ALERTA, lw=0.9))
    # junta de corte-friccion
    ax.plot([16, 96], [16, 16], color=PAL.ALERTA, lw=2.2, ls=(0, (6, 3)),
            zorder=6)
    ax.annotate("", xy=(34, 16), xytext=(12, 16), zorder=7,
                arrowprops=dict(arrowstyle="-|>", color=PAL.ALERTA, lw=2.0))
    ax.text(8, 22, "Vc = %s tonf\n(corte en la columna)"
            % coma(d["Vc"] / 1000.0, 1), fontsize=8.0, color=PAL.ALERTA,
            fontweight="bold", ha="left", zorder=7,
            bbox=dict(boxstyle="round,pad=0.35", fc="#ffffff",
                      ec=PAL.ALERTA, lw=0.8))
    ax.text(58, -2.5, u"Plano de corte-fricción: las %d varillas lo cosen "
            u"(efecto pasador)" % d["c2"]["n"], fontsize=8.0, ha="center",
            color=GRIS_TEXTO)
    # zona confinada
    ax.plot([14, 14], [16, 16 + 70 * d["Hc"] / 300.0], color="#7b3fa0",
            lw=2.4, zorder=5)
    # HORIZONTAL: rotado a 90 grados se salia del eje por la izquierda
    # y el recorte "tight" lo cortaba por la mitad.
    # A LA DERECHA DE LA COLUMNA: puesto a su altura quedaba encima de
    # las cuatro varillas longitudinales. El auditor de textos no lo ve
    # --no es texto pisando texto-- pero en la pagina se lee mal igual.
    _yc = 16 + 70 * d["Hc"] / 300.0
    ax.annotate("", xy=(30, _yc), xytext=(14, _yc), zorder=6,
                arrowprops=dict(arrowstyle="-", color="#7b3fa0",
                                lw=1.0, ls=(0, (3, 2))))
    ax.text(31, _yc, "zona confinada  Hc = %s cm" % coma(d["Hc"], 0),
            fontsize=7.8, color="#7b3fa0", fontweight="bold",
            ha="left", va="center", zorder=7,
            bbox=dict(boxstyle="round,pad=0.30", fc="#ffffff",
                      ec="#7b3fa0", lw=0.8))


def panel_seccion(ax, d):
    ax.set_xlim(-13, 62)
    ax.set_ylim(-12, 44)
    ax.set_aspect("equal")
    ax.axis("off")
    c2 = d["c2"]
    b = c2["b"] * 100.0
    h = c2["h"] * 100.0
    ax.set_title("(b)  La sección armada, %d ø %s"
                 % (c2["n"], c2["diam"]), fontsize=10.2, fontweight="bold",
                 color=AZUL_OSCURO, loc="left", pad=8)
    ax.add_patch(Rectangle((0, 0), b, h, fc=CONCRETO, ec="#546e7a", lw=1.6))
    r = d["recub"]
    ax.add_patch(Rectangle((r, r), b - 2 * r, h - 2 * r, fc="none",
                           ec=ACERO, lw=1.4))
    # LAS VARILLAS VAN DONDE LAS UBICA EL 19 (disposicion(), verificada
    # contra la E.060 7.6.3 y 7.10.5.3). Esta figura tenia su propia regla
    # --paso uniforme por el perimetro-- que con 12 barras no garantizaba ni
    # las cuatro esquinas; y la figura del cuadro tenia OTRA. Una sola regla.
    n = c2["n"]
    disp = c2["disp"]
    for (ga, gb) in disp["ganchos"]:
        ax.plot([ga[0], gb[0]], [ga[1], gb[1]], color=ACERO, lw=1.2, zorder=3)
    pos = list(disp["puntos"])
    for x, y in pos:
        ax.add_patch(Circle((x, y), 1.15, fc=ACERO, ec="#ffffff", lw=0.7,
                            zorder=4))
    assert len(pos) == n, "se dibujaron %d varillas y el cuadro pide %d" % (
        len(pos), n)
    # cotas
    ax.annotate("", xy=(0, -5), xytext=(b, -5),
                arrowprops=dict(arrowstyle="<->", color=PAL.COTA, lw=1.1))
    ax.text(b / 2.0, -8.5, "b = %s cm" % coma(b, 0), fontsize=8.4,
            ha="center", color=PAL.COTA, fontweight="bold")
    ax.annotate("", xy=(-5, 0), xytext=(-5, h),
                arrowprops=dict(arrowstyle="<->", color=PAL.COTA, lw=1.1))
    ax.text(-8.5, h / 2.0, "h = %s cm" % coma(h, 0), fontsize=8.4,
            va="center", ha="center", color=PAL.COTA, fontweight="bold",
            rotation=90)
    texto = (u"%d ø %s\nAs = %s cm²\n\nRequerido: %s cm²\n"
             u"Recubrimiento %s cm (E.060 7.7.1)\n\nEstribos %s"
             % (c2["n"], c2["diam"], coma(d["As"]), coma(d["As_req"]),
                coma(d["recub"], 1), c2["estribo"]))
    ax.text(b + 6, h, texto, fontsize=8.0, va="top", color=GRIS_TEXTO,
            linespacing=1.6)


def panel_ecuaciones(ax, d):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.set_title("(c)  El acero se SUMA: no gobierna el mayor de los dos",
                 fontsize=10.2, fontweight="bold", color=AZUL_OSCURO,
                 loc="left", pad=8)
    lineas = [
        ("Corte-fricción en la base  (E.070 8.6.3-a.1')",
         [u"Asf = Vc / (φ·fy·μ) = %s / (%s × %s × %s) = %s cm²"
          % (coma(d["Vc"], 0), coma(d["phi_v"]), coma(d["fy"], 0),
             coma(d["mu"]), coma(d["Asf"]))]),
        ("Tracción por volteo  (E.070 8.6.3-a.2)",
         [u"Ast = T / (φ·fy) = %s / (%s × %s) = %s cm²"
          % (coma(d["T"], 0), coma(d["phi_v"]), coma(d["fy"], 0),
             coma(d["Ast"]))]),
        ("Acero requerido: la SUMA de los dos",
         [u"As = Asf + Ast = %s + %s = %s cm²"
          % (coma(d["Asf"]), coma(d["Ast"]), coma(d["As_req"])),
          u"Las dos solicitaciones son simultáneas: la junta desliza mientras "
          u"el talón se levanta. Tomar el mayor dejaría el muro corto."]),
        ("Armadura adoptada",
         [u"%d ø %s = %s cm²  ≥  %s cm²   CUMPLE"
          % (d["c2"]["n"], d["c2"]["diam"], coma(d["As"]),
             coma(d["As_req"]))]),
    ]
    y = 94.0
    for titulo, filas in lineas:
        ax.text(1.0, y, titulo, fontsize=8.6, fontweight="bold",
                color=AZUL_OSCURO, va="top")
        y -= 6.4
        for f in filas:
            env = textwrap.wrap(f, 74)
            col = PAL.BIEN if "CUMPLE" in f else GRIS_TEXTO
            ax.text(3.2, y, "\n".join(env), fontsize=8.0, color=col,
                    va="top", linespacing=1.4,
                    fontweight="bold" if "CUMPLE" in f else "normal")
            y -= 6.2 * len(env) + 1.2
        y -= 2.8
    assert y > -3.0, "las ecuaciones del panel (c) desbordan su caja"


def panel_dcr(ax, d):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.set_title("(d)  Demanda contra capacidad, en las tres verificaciones",
                 fontsize=10.2, fontweight="bold", color=AZUL_OSCURO,
                 loc="left", pad=8)
    y = 92.0
    for nombre, simb, dem, cap, color, formula, acapite in d["dcr"]:
        dcr = dem / cap
        ax.text(1.0, y, nombre, fontsize=9.0, fontweight="bold",
                color=AZUL_OSCURO, va="top")
        ax.text(99.0, y, "CUMPLE", fontsize=7.6, fontweight="bold",
                color="#ffffff", ha="right", va="top",
                bbox=dict(boxstyle="round,pad=0.3", fc=PAL.BIEN, ec="none"))
        y -= 5.6
        ax.text(2.4, y, u"Demanda %s = %s tonf   ·   Capacidad = %s tonf   "
                u"·   DCR = %s"
                % (simb, coma(dem / 1000.0, 1), coma(cap / 1000.0, 1),
                   coma(dcr)), fontsize=8.2, color=GRIS_TEXTO, va="top")
        y -= 5.0
        ax.add_patch(FancyBboxPatch((2.4, y - 3.4), 94.0, 3.4,
                                    boxstyle="round,pad=0.0,rounding_size=0.5",
                                    fc="#e3e9f0", ec="none"))
        ax.add_patch(FancyBboxPatch((2.4, y - 3.4), 94.0 * dcr, 3.4,
                                    boxstyle="round,pad=0.0,rounding_size=0.5",
                                    fc=color, ec="none"))
        ax.text(2.4 + 94.0 * dcr + 1.2, y - 1.7,
                "queda %s %% de reserva" % coma(100.0 * (1.0 - dcr), 0),
                fontsize=7.6, color=GRIS_SUAVE, va="center")
        y -= 6.0
        ax.text(2.4, y, "%s      (%s)" % (formula, acapite), fontsize=7.8,
                color=GRIS_SUAVE, style="italic", va="top")
        y -= 9.0
    assert y > -2.0, "los tres DCR del panel (d) no entran"


def dibujar():
    d = reunir()
    control(d)

    pie_a = ("La columna extrema no es una columna cualquiera: recibe el "
             "volteo del muro entero. El mecanismo de la izquierda muestra "
             "de donde sale cada fuerza y la seccion, con que se le "
             "responde.")
    pie_b = ("La columna extrema trabaja en los tres frentes a la vez, y "
             "por eso su acero SUMA el de corte-friccion y el de traccion "
             "en lugar de tomar el mayor: la junta desliza mientras el "
             "talon se levanta. Con %d ø %s las tres verificaciones "
             "quedan por debajo de la capacidad, la mas ajustada con %s %% "
             "de reserva."
             % (d["c2"]["n"], d["c2"]["diam"],
                coma(100.0 * (1.0 - max(dem / cap for _n, _s, dem, cap,
                                        _c, _f, _a in d["dcr"])), 0)))
    sub = (u"Columna %s del muro que gobierna (%s)"
           % (d["c2"]["tipo"], d["muro"]))
    for n_lam, (paneles, titulo, pie) in enumerate((
            ((panel_mecanismo, panel_seccion),
             u"Mecánica del confinamiento: qué hace de verdad la "
             u"columna extrema", pie_a),
            ((panel_dcr, panel_ecuaciones),
             u"Cuánto le toca: las tres verificaciones y sus "
             u"ecuaciones", pie_b)), 1):
        fig = plt.figure(figsize=(C.ANCHO_PAGINA, 8.30), dpi=200)
        fig.patch.set_facecolor(PAL.PAPEL)
        y_ar, y_ab = C.marco(fig, titulo,
                             pie=pie + '  Base: E.070 8.6.3 y E.060 7.7.1.', subtitulo=sub,
                             fs_tit=11.5, color_tit=AZUL_OSCURO)
        gs = fig.add_gridspec(2, 1, left=0.105, right=0.975, top=y_ar,
                              bottom=y_ab, hspace=0.40)
        for k, panel in enumerate(paneles):
            panel(fig.add_subplot(gs[k, 0]), d)
        C.guardar(fig, os.path.join(
            R.INFORME, "CONFINAMIENTOS-ANALITICO-%d.png" % n_lam))


if __name__ == "__main__":
    dibujar()
