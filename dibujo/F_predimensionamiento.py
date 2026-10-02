# -*- coding: utf-8 -*-
"""Las secciones adoptadas, dibujadas a escala y con el artículo que las fija.

DISEÑO SENIOR Y LEGIBILIDAD
===========================
Muestra las siete secciones de superestructura a la misma escala modular
compartiendo el ancho del muro (b = 0,24 m según E.070 7.1.1.a) y el cimiento
corrido a escala propia con su profundidad Df y base B (E.050 / EMS).
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
import matplotlib.patches as patches                           # noqa: E402
from matplotlib.patches import Rectangle                       # noqa: E402
import textwrap                                                # noqa: E402

COLOR = {
    "Losa aligerada": ("#e2e8f0", "#475569"),
    "Muro portante": ("#334155", "#0f172a"),
    "Viga solera VS-1": ("#0d9488", "#115e59"),
    "Columna C-1 interior": ("#ea580c", "#9a3412"),
    "Columna C-2 extrema": ("#c2410c", "#7c2d12"),
    "Dintel sobre puerta VD-1": ("#d97706", "#92400e"),
    "Dintel sobre ventana VD-2": ("#b45309", "#78350f"),
}


def datos():
    """El cuadro del script 06, que es la fuente de la tabla del informe."""
    ruta = os.path.join(AQUI, "..", "calculo", "06_predimensionamiento.py")
    spec = importlib.util.spec_from_file_location("_m06", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def _presion_de_cimiento():
    """La presion real bajo el cimiento y la admisible, del script 04.

    El pie decia «no excede la presion admisible de 1,05 kgf/cm²». Lo
    escribi copiandolo del banner que estaba reemplazando, y no sale de
    ningun lado del proyecto de hoy: el EMS da 3,00 kg/cm² -- `QAD`, el
    punto mas desfavorable del grafico «B vs qad» de su Fig. N.o 3 -- y la
    presion real bajo el cimiento adoptado es 2,36.
    """
    import contextlib
    import importlib
    import io as _io5
    from proyecto import B_CIMIENTO, QAD
    with contextlib.redirect_stdout(_io5.StringIO()):
        m04 = importlib.import_module("04_cimentacion")
        w = m04.carga_lineal()
    q = (w / 1000.0) / B_CIMIENTO / 10.0
    assert q < QAD, "la presion real %.2f supera la admisible %.2f" % (q, QAD)
    return q, QAD


def main():
    """Las ocho secciones adoptadas: el dibujo, el cuadro y el cimiento.

    POR QUÉ SE REHIZO. Esta figura era de antes del armador: llamaba a
    `savefig(bbox_inches="tight")` por su cuenta, se ponía su propio título
    y metía la fundamentación en un banner dentro del lienzo. El resultado,
    medido: el título se salía del ancho de la página, los siete nombres de
    sección se escribían uno encima de otro —«Losa AligeradaMuro
    PortanteViga Solera…»— porque cada nombre es tres veces más ancho que
    su sección, y los rótulos del cimiento quedaban recortados por las
    propias piezas que nombraban. El auditor contaba siete pares pisándose
    y a ojo eran más.

    Se rehace con el mismo criterio que el resto: el DIBUJO lleva la
    geometría con una etiqueta corta, el CUADRO lleva los nombres, las
    medidas y el acápite, y la fundamentación baja al pie del marco, que
    es quien sabe cuánto alto reservarle.
    """
    from proyecto import ESPESOR
    m = datos()
    filas = m.cuadro()

    secciones = [f for f in filas if f[0] != "Cimiento corrido"]
    cimiento = [f for f in filas if f[0] == "Cimiento corrido"][0]
    _q_real, _q_adm = _presion_de_cimiento()

    # ETIQUETA CORTA PARA EL DIBUJO, NOMBRE ENTERO PARA EL CUADRO. A la
    # escala que admite la hoja cada sección mide 0,43 pulgadas: «Losa
    # Aligerada (h = 0,20 m)» mide 1,4 y por eso se montaba sobre las dos
    # vecinas. La etiqueta es el nombre con que la nombra el cuadro.
    ETIQUETA = {
        "Losa aligerada": "LOSA",
        "Muro portante": "MURO",
        "Viga solera VS-1": "VS-1",
        "Columna C-1 interior": "C-1",
        "Columna C-2 extrema": "C-2",
        "Dintel sobre puerta VD-1": "VD-1",
        "Dintel sobre ventana VD-2": "VD-2",
    }

    alto_fig = 9.60
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, alto_fig), dpi=220,
                     facecolor="white")
    y_ar, y_ab = C.marco(
        fig,
        "Predimensionamiento de las secciones  ·  E.070, E.060 y E.050",
        subtitulo=("las siete secciones de superestructura comparten el "
                   "ancho del muro, b = %s m (E.070 7.1.1.a)"
                   % C.coma(ESPESOR, 2)),
        pie=("El ancho común elimina mochetas, estandariza el encofrado y "
             "da continuidad vertical a la transmisión de axiales y "
             "cortantes. La C-1 interior sale del mínimo Ac ≥ 15·t = 600 cm² "
             "del acápite 7.2.5; la C-2 extrema no —la fija la longitud de "
             "anclaje de la viga solera en esquinas y bordes de lote "
             "(7.1.4)—, y por eso es la más peraltada de las dos. El "
             "cimiento de %s × %s m es el que mantiene la presión bajo "
             "el muro más cargado en %s kg/cm², por debajo de los %s que "
             "admite el EMS."
             % (C.coma(cimiento[1], 2), C.coma(cimiento[2], 2),
                C.coma(_q_real, 2), C.coma(_q_adm, 2))))

    # ---- (a) las siete secciones, a la misma escala --------------------
    alto_a = 1.45 / alto_fig
    ax = fig.add_axes((0.075, y_ar - alto_a - 0.030, 0.875, alto_a))
    x, paso = 0.0, 0.42
    h_max = max(f[2] for f in secciones)
    for nom, b, h, _art in secciones:
        ancho = ESPESOR if b is None else b
        fc, ec = COLOR[nom]
        ax.add_patch(Rectangle((x, 0), ancho, h, fc=fc, ec=ec, lw=1.2,
                               zorder=3))
        ax.text(x + ancho / 2.0, -0.045, ETIQUETA[nom], ha="center", va="top",
                fontsize=8.2, fontweight="bold", color="#0f172a", zorder=5)
        ax.text(x + ancho / 2.0, -0.115, C.coma(h, 2), ha="center", va="top",
                fontsize=7.4, color="#475569", zorder=5)
        x += paso

    # LA COTA DEL ANCHO COMUN, sin el cartel que la tapaba. El banner
    # «ANCHO COMUN b = 0,24 m EN LAS 7 SECCIONES» se dibujaba justo encima
    # de la cota que ilustraba: el 72 % de su caja pisaba el rotulo «b».
    # Lo que decia el cartel ahora es el subtitulo del marco.
    y_c = h_max + 0.075
    ax.plot([0.0, ESPESOR], [y_c, y_c], color="#4338ca", lw=1.6, zorder=4)
    for xx in (0.0, ESPESOR):
        ax.plot([xx, xx], [y_c - 0.022, y_c + 0.022], color="#4338ca", lw=1.6,
                zorder=4)
    ax.text(ESPESOR / 2.0, y_c + 0.030, "b = %s" % C.coma(ESPESOR, 2),
            ha="center", va="bottom", fontsize=8.0, fontweight="bold",
            color="#312e81", zorder=5)
    ax.annotate("", xy=(x - paso + ESPESOR, y_c), xytext=(ESPESOR + 0.03, y_c),
                arrowprops=dict(arrowstyle="->", color="#4338ca", lw=1.1,
                                ls="--"), zorder=4)
    ax.set_xlim(-0.06, x - paso + ESPESOR + 0.06)
    ax.set_ylim(-0.22, h_max + 0.16)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("(a)  Las siete secciones, a la misma escala",
                 fontsize=9.5, fontweight="bold", loc="left", color="#0f172a",
                 pad=6)

    # ---- (b) el cuadro de secciones ------------------------------------
    alto_fila = 0.235
    alto_b = (alto_fila * (len(filas) + 2)) / alto_fig
    y_b = y_ar - alto_a - 0.030 - 0.055
    axt = fig.add_axes((0.0, 0.0, 1.0, 1.0), zorder=0)
    axt.set_xlim(0, 1)
    axt.set_ylim(0, 1)
    axt.axis("off")
    fig.text(0.075, y_b + 0.004,
             "(b)  El cuadro: qué es cada una y qué acápite la fija",
             fontsize=9.5, fontweight="bold", color="#0f172a", va="bottom")
    tabla_filas = []
    for nom, b, h, art in filas:
        ancho = ESPESOR if b is None else b
        tabla_filas.append([nom, C.coma(ancho, 2), C.coma(h, 2), art])
    y_fin = C.tabla(axt, 0.075, y_b - 0.006, 0.875, alto_fila / alto_fig,
                    ["Elemento", "b (m)", "h (m)", "Lo fija"],
                    tabla_filas, fs=7.8)

    # ---- (c) el cimiento corrido ---------------------------------------
    _n, bc, dfc, artc = cimiento
    # EL PANEL SE LLEVA LO QUE SOBRA. Pedirle 2,45 pulgadas sin mirar lo
    # que quedaba hizo que el cimiento se dibujara ENCIMA del pie del
    # marco. Con `aspect=equal` un rectangulo mas bajo no recorta: encoge
    # el dibujo y deja aire a los lados, que es lo correcto.
    y_c0 = y_ab + 0.012
    # SIN PISO: si no entra, que se vea que no entra. El titulo del
    # panel vive en y_fin - 0,028 y mide 0,12 pulgadas; el eje arranca
    # debajo de el y punto.
    alto_c = y_fin - 0.055 - y_c0
    assert alto_c * alto_fig > 1.20, (
        "al detalle del cimiento le quedan %.2f pulgadas: subile el "
        "alto a la figura" % (alto_c * alto_fig))
    ax2 = fig.add_axes((0.075, y_c0, 0.875, alto_c))
    # EL LIENZO TOMA LA RELACION DEL HUECO. Ver el porque arriba: se mide
    # el recuadro en pulgadas y se despeja el ancho de datos que lo llena.
    _w_in = 0.875 * fig.get_size_inches()[0]
    _h_in = alto_c * alto_fig
    _span_y = (0.90 + dfc + 0.40)
    _span_x = max(_span_y * _w_in / max(_h_in, 0.01), 4.2)
    ax2.set_xlim(-_span_x / 2.0, _span_x / 2.0)
    ax2.add_patch(Rectangle((-_span_x * 0.14, -0.15),
                            _span_x * 0.14 - ESPESOR / 2.0, 0.15,
                            fc="#e2e8f0", ec="#94a3b8", lw=0.9, hatch="//",
                            zorder=1))
    ax2.add_patch(Rectangle((ESPESOR / 2.0, -0.15),
                            _span_x * 0.14 - ESPESOR / 2.0, 0.15,
                            fc="#e2e8f0",
                            ec="#94a3b8", lw=0.9, hatch="//", zorder=1))
    ax2.add_patch(Rectangle((-ESPESOR / 2.0, 0.0), ESPESOR, 0.40, fc="#334155",
                            ec="#0f172a", lw=1.2, zorder=3))
    ax2.add_patch(Rectangle((-ESPESOR / 2.0, -0.15), ESPESOR, 0.15,
                            fc="#64748b", ec="#334155", lw=1.2, zorder=3))
    ax2.add_patch(Rectangle((-bc / 2.0, -dfc), bc, dfc - 0.15, fc="#854d0e",
                            ec="#451a03", lw=1.4, zorder=2))

    # LOS ROTULOS, FUERA DE LAS PIEZAS. Escritos adentro quedaban
    # recortados por el propio rectangulo -- «ento Cor / reto Cicl» -- y
    # «Sobrecimiento» se montaba sobre «NPT ±0.00». Van a la izquierda,
    # con su linea guia, que es donde hay hoja.
    for texto, y_pieza in (("Muro de albañilería, %s m" % C.coma(ESPESOR, 2),
                            0.20),
                           ("Sobrecimiento", -0.075),  # su guia sale por la izquierda
                           ("Cimiento corrido de concreto\nciclópeo "
                            "(1:10 + 30 % P.G.)", -dfc / 2.0 - 0.05)):
        ax2.annotate(texto, xy=(-ESPESOR / 2.0 - 0.02, y_pieza),
                     xytext=(-_span_x * 0.16, y_pieza), ha="right", va="center",
                     fontsize=8.0, color="#1e293b", linespacing=1.25,
                     arrowprops=dict(arrowstyle="-", color="#94a3b8", lw=0.8))
    ax2.text(_span_x * 0.16, -0.075, "NPT ± 0,00", fontsize=8.0, fontweight="bold",
             color="#475569", va="center", ha="left")
    ax2.annotate("", xy=(-bc / 2.0, -dfc - 0.12), xytext=(bc / 2.0, -dfc - 0.12),
                 arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.1),
                 zorder=5)
    ax2.text(0, -dfc - 0.19, "B = %s m" % C.coma(bc, 2), ha="center", va="top",
             fontsize=8.4, fontweight="bold", color="#0f172a", zorder=5)
    ax2.annotate("", xy=(bc / 2.0 + 0.16, 0.0), xytext=(bc / 2.0 + 0.16, -dfc),
                 arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.1),
                 zorder=5)
    ax2.text(bc / 2.0 + 0.22, -dfc / 2.0, "Df = %s m" % C.coma(dfc, 2),
             va="center", ha="left", rotation=90, fontsize=8.4,
             fontweight="bold", color="#0f172a", zorder=5)
    # AIRE ARRIBA: con `aspect=equal` el recuadro se encoge y el dibujo
    # queda pegado al titulo del panel. Un techo mas alto lo baja.
    # EL AIRE DE ARRIBA separa al dibujo del titulo del panel: el eje
    # llega pegado a la tabla, asi que el hueco lo pone la ylim.
    ax2.set_ylim(-dfc - 0.40, 0.90)
    ax2.set_aspect("equal")
    ax2.axis("off")
    fig.text(0.075, y_fin - 0.028,
             "(c)  El cimiento corrido  ·  %s" % artc,
             fontsize=9.5, fontweight="bold", color="#0f172a",
             va="top")

    out = os.path.join(R.INFORME, "PREDIMENSIONAMIENTO-SECCIONES.png")
    C.guardar(fig, out)
    print()
    control(filas)


def control(filas):
    """Lo que la figura afirma tiene que salir del cuadro, no del dibujo."""
    from proyecto import ESPESOR
    assert len(filas) == 8, "el cuadro trae %d elementos y la figura dibuja 8" % len(filas)
    anchos = [(b if b is not None else ESPESOR) for n, b, _h, _a in filas
              if n != "Cimiento corrido"]
    assert all(abs(a - ESPESOR) < 1e-9 for a in anchos), (
        "la figura afirma que las siete secciones comparten el ancho del "
        "muro y los anchos son %s" % anchos)
    for nom, _b, _h, art in filas:
        assert art and art.strip(), "%r no declara el articulo que lo fija" % nom
    print("  [ok] las 8 secciones salen del cuadro del script 06")
    print("  [ok] las 7 de superestructura comparten el ancho de %.2f m"
          % ESPESOR)
    print("  [ok] cada una declara el articulo que la fija")
    return True


if __name__ == "__main__":
    main()
