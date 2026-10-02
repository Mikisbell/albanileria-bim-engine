# -*- coding: utf-8 -*-
"""El lenguaje visual de las figuras del informe, en un solo lugar.

DE DONDE SALE
=============
De `seccion_transformada.py`, que es la figura que quedó bien y que Mikis
señaló como el estándar. Lo que la hace legible no es el dibujo sino el
CONTRATO:

  - un título arriba, en negrita, que dice qué se está mirando
  - paneles rotulados (a), (b), (c), alineados a la izquierda
  - una paleta corta y consistente: cada material siempre del mismo color
  - anotaciones con línea guía fina, no cotas por todos lados
  - una nota al pie en cursiva con LO ÚNICO que hay que entender
  - `axis off` y `aspect equal`: es un dibujo técnico, no un gráfico

POR QUE UN MODULO Y NO COPIAR Y PEGAR
=====================================
Porque el informe tiene que leerse como un solo documento. Con cinco
archivos definiendo su propio azul, la tercera figura ya no combina con la
primera, y eso se nota antes que cualquier error de cálculo.

LA REGLA DE LAS COTAS
=====================
Se acota lo que el lector NO puede deducir mirando. Una figura con veinte
cotas no informa veinte cosas: tapa las tres que importaban. Si un valor ya
está en la tabla del capítulo, en la figura va como anotación, no como cota.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                    # noqa: E402

# --- materiales. Cada uno SIEMPRE del mismo color en todo el informe.
ALBANILERIA = "#d9c9a3"     # el alma de albañilería
CONCRETO = "#9aa7b1"        # columnas, soleras, cimiento
ALA = "#c5d8c5"             # el ala que cede el muro ortogonal
TRANSFORMADA = "#e8dcc0"    # albañilería equivalente
ACERO = "#34495e"           # varillas y estribos
TERRENO = "#e8e2d5"
VACIO = "#ffffff"

# --- tinta
TINTA = "#333333"
GUIA = "#8a8a8a"            # líneas de guía y auxiliares
AZUL = "#2e6da4"            # cotas y datos
ROJO = "#c0392b"            # lo crítico, lo que gobierna
VERDE = "#1e8449"           # lo que cumple, lo normativo

# --- bordes de material
BORDE_ALB = "#6b5b3e"
BORDE_CON = "#43505a"
BORDE_ALA = "#4a6b4a"

TIT = 13                    # tamaño del título de la figura
PANEL = 10                  # título de cada panel
ANOT = 9                    # anotaciones
PIE = 9                     # nota al pie


ANCHO_PAGINA = 6.30      # pulgadas utiles de una A4 con 2,5 cm
ALTO_PAGINA = 8.86


def figura(titulo, ancho=None, alto=7.6, filas=1, cols=1):
    """Abre la figura con su título, y devuelve (fig, [ejes]).

    `ancho=None` toma el de la caja de la página: ver el porqué arriba. El
    título va con `wrap`, que es lo que impide que una frase entera en una
    línea ensanche el lienzo sin avisar.
    """
    fig = plt.figure(figsize=(ancho or ANCHO_PAGINA, alto))
    fig.suptitle(titulo, fontsize=min(TIT, 11.5), fontweight="bold",
                 color=TINTA, wrap=True)
    ejes = [fig.add_subplot(filas, cols, k + 1) for k in range(filas * cols)]
    return fig, ejes


def panel(ax, letra, titulo):
    """El rótulo de panel: '(a)  Lo que se está mirando'."""
    ax.set_title("(%s)  %s" % (letra, titulo), fontsize=PANEL, loc="left",
                 color=TINTA)


def anotar(ax, texto, xy, xytext, color=AZUL, fs=ANOT):
    """Anotación con línea guía fina. Sustituye a la cota cuando alcanza."""
    ax.annotate(texto, xy=xy, xytext=xytext, fontsize=fs, color=color,
                arrowprops=dict(arrowstyle="->", color=color, lw=0.9))


def cota_h(ax, y, x0, x1, texto, color=AZUL, fs=8, remate=0.12):
    """Cota horizontal, con sus dos remates."""
    ax.annotate("", (x0, y), (x1, y),
                arrowprops=dict(arrowstyle="<->", color=color, lw=0.9))
    for x in (x0, x1):
        ax.plot([x, x], [y - remate, y + remate], color=color, lw=0.7)
    ax.text((x0 + x1) / 2.0, y + remate * 1.4, texto, color=color,
            fontsize=fs, ha="center")


def cota_v(ax, x, y0, y1, texto, color=AZUL, fs=8, remate=0.12, lado=1):
    """Cota vertical. `lado` = 1 escribe a la derecha, -1 a la izquierda."""
    ax.annotate("", (x, y0), (x, y1),
                arrowprops=dict(arrowstyle="<->", color=color, lw=0.9))
    for y in (y0, y1):
        ax.plot([x - remate, x + remate], [y, y], color=color, lw=0.7)
    ax.text(x + lado * remate * 1.6, (y0 + y1) / 2.0, texto, color=color,
            fontsize=fs, va="center",
            ha="left" if lado > 0 else "right")


def limpiar(ax, xlim=None, ylim=None, igual=True):
    """Deja el eje como dibujo técnico: sin marcos, sin ticks, a escala."""
    if xlim:
        ax.set_xlim(*xlim)
    if ylim:
        ax.set_ylim(*ylim)
    if igual:
        ax.set_aspect("equal")
    ax.axis("off")


def pie(fig, texto, rect=(0, 0.04, 1, 0.95)):
    """La nota al pie: LO ÚNICO que el lector tiene que llevarse.

    Se envuelve al ancho de la figura. Sin envolver, una nota de 200
    caracteres ensancha el lienzo para que quepa -- `bbox_inches="tight"`
    no recorta, crece -- y con él se achica todo el tipo al imprimir.
    """
    import textwrap
    anc_in = fig.get_size_inches()[0] * 0.92
    # a PIE puntos, un caracter ocupa aprox. 0,50 em de avance
    n_car = max(30, int(anc_in * 72.0 / (PIE * 0.50)))
    lineas = []
    for par in str(texto).split(chr(10)):
        lineas += textwrap.wrap(par, n_car) or [""]
    paso = (PIE * 1.45 / 72.0) / fig.get_size_inches()[1]
    y = 0.015 + paso * (len(lineas) - 1)
    for ln in lineas:
        fig.text(0.5, y, ln, ha="center", fontsize=PIE, style="italic",
                 color="#444")
        y -= paso
    base = 0.035 + paso * len(lineas)
    fig.tight_layout(rect=(rect[0], base, rect[2], rect[3]))


def guardar(fig, ruta, dpi=170):
    """Guarda MIDIENDO con que cuerpo se va a imprimir. Ver el porque arriba."""
    import os
    bb = fig.get_tightbbox(fig.canvas.get_renderer())
    w, h = bb.width, bb.height
    esc = min(ANCHO_PAGINA / w, ALTO_PAGINA / h, 1.0)
    fig.savefig(ruta, dpi=dpi, facecolor="white")
    plt.close(fig)
    aviso = "" if esc >= 0.87 else "   <-- por debajo de 6,5 pt"
    print("  %s   %.2f x %.2f pulg  ->  7,5 pt salen a %.1f pt%s"
          % (os.path.basename(str(ruta)), w, h, 7.5 * esc, aviso))
    return ruta, os.path.getsize(ruta)


# ===========================================================================
# COMPONENTES DE LAMINA TECNICA
# ===========================================================================
# Lo que separa una figura de una LAMINA. Estaban dibujados a mano en cada
# archivo, o directamente ausentes: por eso las figuras se veian pobres al
# lado de una lamina de verdad. Aca viven una sola vez.

from matplotlib.patches import Circle, Rectangle, FancyBboxPatch  # noqa: E402

BURBUJA = "#1f5fa9"          # el azul de los ejes estructurales
COTA = "#00a0a8"             # el turquesa de las cotas, como en un plano
NIVEL = "#5b4636"            # el marron del simbolo de NPT


def burbuja(ax, x, y, texto, r=0.42, color=BURBUJA, fs=9):
    """La burbuja de eje: circulo con su letra o numero.

    Es lo primero que un corrector busca en una planta, porque es lo que
    permite decir "la columna del eje B-2" sin senalar con el dedo.
    """
    ax.add_patch(Circle((x, y), r, fc="white", ec=color, lw=1.2, zorder=8))
    ax.text(x, y, texto, ha="center", va="center", fontsize=fs,
            color=color, fontweight="bold", zorder=9)


def ejes_con_burbujas(ax, xs, ys, etiquetas_x, etiquetas_y,
                      fuera=1.3, r=0.42, color=BURBUJA):
    """Los ejes estructurales punteados, con burbuja a los CUATRO lados."""
    y0, y1 = min(ys) - fuera, max(ys) + fuera
    x0, x1 = min(xs) - fuera, max(xs) + fuera
    for x, et in zip(xs, etiquetas_x):
        ax.plot([x, x], [y0, y1], color=color, lw=0.7, ls=(0, (7, 4)),
                alpha=0.75, zorder=1)
        burbuja(ax, x, y0 - r * 1.6, et, r, color)
        burbuja(ax, x, y1 + r * 1.6, et, r, color)
    for y, et in zip(ys, etiquetas_y):
        ax.plot([x0, x1], [y, y], color=color, lw=0.7, ls=(0, (7, 4)),
                alpha=0.75, zorder=1)
        burbuja(ax, x0 - r * 1.6, y, et, r, color)
        burbuja(ax, x1 + r * 1.6, y, et, r, color)


def nivel(ax, x, y, texto, color=NIVEL, fs=8.5, lado=1, tam=0.28):
    """El simbolo de nivel: triangulo relleno con su cota de NPT."""
    ax.plot([x - tam, x + tam, x, x - tam], [y + tam, y + tam, y, y + tam],
            color=color, lw=1.0, zorder=7)
    ax.fill([x - tam, x + tam, x], [y + tam, y + tam, y], color=color,
            zorder=7)
    ax.text(x + lado * tam * 1.8, y + tam * 0.6, texto, fontsize=fs,
            color=color, va="center", fontweight="bold",
            ha="left" if lado > 0 else "right", zorder=7)


def cadena(ax, y, cortes, etiquetas=None, color=COTA, fs=8, ext=0.45,
           vertical=False):
    """Cota ENCADENADA: tramo a tramo, con sus lineas de extension.

    Un plano no cota el total y se olvida de los tramos: cota la cadena, y
    el total aparte. Es lo que permite replantear en obra.
    """
    cortes = sorted(cortes)
    for c in cortes:
        if vertical:
            ax.plot([y - ext, y], [c, c], color=color, lw=0.7, alpha=0.9)
        else:
            ax.plot([c, c], [y, y + ext], color=color, lw=0.7, alpha=0.9)
    for k in range(len(cortes) - 1):
        a, b = cortes[k], cortes[k + 1]
        txt = etiquetas[k] if etiquetas else "%.2f" % (b - a)
        if vertical:
            ax.annotate("", (y, a), (y, b),
                        arrowprops=dict(arrowstyle="<->", color=color, lw=0.9))
            ax.text(y - 0.18, (a + b) / 2.0, txt, color=color, fontsize=fs,
                    ha="right", va="center", rotation=90)
        else:
            ax.annotate("", (a, y), (b, y),
                        arrowprops=dict(arrowstyle="<->", color=color, lw=0.9))
            ax.text((a + b) / 2.0, y - 0.22, txt, color=color, fontsize=fs,
                    ha="center", va="top")


def leyenda(ax, items, x, y, titulo="LEYENDA", ancho=3.6, alto_fila=0.42,
            fs=8):
    """Recuadro de leyenda con muestra de color y su significado.

    `items` es [(color, borde, texto)]; el borde None dibuja solo una linea,
    que es como se anota un eje o una linea de nivel.
    """
    n = len(items)
    # EL ALTO DE FILA SE DERIVA DEL CUERPO Y DE LA ESCALA. Ver el porque
    # en el bloque de arriba: una distancia en metros no sabe nada del
    # tamano del texto, que esta en puntos.
    fig = ax.figure
    alto_ejes_in = ax.get_position().height * fig.get_size_inches()[1]
    span_y = abs(ax.get_ylim()[1] - ax.get_ylim()[0]) or 1.0
    m_por_pulgada = span_y / max(alto_ejes_in, 0.01)
    alto_fila = max(alto_fila, (fs * 1.55 / 72.0) * m_por_pulgada)
    h = alto_fila * (n + 1.9)
    ax.add_patch(FancyBboxPatch((x, y - h), ancho, h,
                                boxstyle="round,pad=0.10",
                                fc="white", ec=GUIA, lw=0.8, zorder=10))
    ax.text(x + ancho / 2.0, y - alto_fila * 0.6, titulo, ha="center",
            fontsize=fs + 0.5, color=TINTA, zorder=11,
            fontweight="bold")
    for k, (col, borde, texto) in enumerate(items):
        yy = y - alto_fila * (k + 2.1)
        if col is None:
            ax.plot([x + 0.18, x + 0.78], [yy + alto_fila * 0.15] * 2,
                    color=borde, lw=1.2, ls=(0, (5, 3)), zorder=11)
        else:
            ax.add_patch(Rectangle((x + 0.18, yy), 0.60, alto_fila * 0.55,
                                   fc=col, ec=borde or GUIA, lw=0.8,
                                   zorder=11))
        ax.text(x + 0.92, yy + alto_fila * 0.25, texto, fontsize=fs,
                va="center", color=TINTA, zorder=11)


def notas(ax, lineas, x, y, ancho=5.0, fs=7.5, titulo=None):
    """Bloque de notas en monoespaciada, como en una lamina."""
    txt = ("\n".join(lineas))
    if titulo:
        txt = titulo + "\n" + txt
    ax.text(x, y, txt, fontsize=fs, family="monospace", va="top",
            color=TINTA, zorder=11,
            bbox=dict(boxstyle="round,pad=0.5", fc="#fbfbf9", ec=GUIA,
                      lw=0.8))


def norte(ax, x, y, r=0.75, color=NIVEL):
    """La rosa de los vientos. Una planta sin norte esta incompleta."""
    ax.add_patch(Circle((x, y), r, fc="white", ec=color, lw=1.0, zorder=10))
    ax.fill([x, x - r * 0.28, x, x + r * 0.28],
            [y + r * 0.82, y, y - r * 0.18, y], color=color, zorder=11)
    ax.fill([x, x - r * 0.28, x, x + r * 0.28],
            [y - r * 0.82, y, y + r * 0.18, y], color="white",
            ec=color, lw=0.7, zorder=11)
    ax.text(x, y + r * 1.35, "N", ha="center", fontsize=9.5, color=color,
            fontweight="bold", zorder=11)


def subtitulo(ax, texto, escala=None, fs=9.5):
    """El subtitulo del panel, con su ESCALA declarada."""
    t = texto if escala is None else "%s    Esc. %s" % (texto, escala)
    ax.set_title(t, fontsize=fs, loc="left", color=GUIA, pad=14)
