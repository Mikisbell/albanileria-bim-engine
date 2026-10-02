# -*- coding: utf-8 -*-
"""Elevación frontal — criterio 1 de la rúbrica.

QUE LE FALTABA A LA VERSION ANTERIOR
====================================
Era una figura, no una LAMINA. Comparada con una lámina de verdad le
faltaba todo el repertorio que la hace leerse como un documento técnico:

  - leyenda en recuadro, con muestra de color y su significado
  - burbujas de eje a los cuatro lados, que es como se nombra una posición
  - cotas ENCADENADAS con líneas de extensión, no solo el total
  - el símbolo ▼ de NPT en cada nivel, no un texto suelto
  - un bloque de notas con niveles y cuadro de vanos
  - la ESCALA declarada en el subtítulo

Nada de eso es adorno: es lo que permite que alguien lea el dibujo sin que
se lo expliquen.

TODO SALE DEL SSOT
==================
Los veinte vanos están en la posición que declara `vanos_ubicados()`, los
niveles son `k · H_ENTREPISO`, el parapeto y el alféizar son constantes de
`proyecto.py`. Ninguna cota se teclea.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))
sys.path.insert(0, AQUI)

import rutas as R                                        # noqa: E402

import cuadro as C
import meta as META                                                 # noqa: E402
import matplotlib.pyplot as plt                                    # noqa: E402
import estilo as E                                                 # noqa: E402
from matplotlib.patches import Rectangle                           # noqa: E402
from proyecto import (FRENTE, ESPESOR, E_LOSA, H_ENTREPISO, N_PISOS,  # noqa: E402
                      HN, PARAPETO, DF, B_CIMIENTO, ALFEIZAR, MUROS,
                      vanos_ubicados, altura_de_vano, H_DINTEL_VENTANA,
                      tipo_de_vano,
                      ejes_x_rotulados, H_LIBRE, H_DINTEL_PUERTA, ALTO_PUERTA)

MURO_F = "#f2efe9"       # paramento de fachada
PARAP = "#fadfc2"        # el parapeto, destacado
VENT = "#cfe2f3"         # ventana


def _ejes_de_fachada():
    """Los ejes verticales que se ven en la fachada, con su letra."""
    from proyecto import POZO_X0, POZO_X1
    return ejes_x_rotulados()


def dibujar(ax):
    fila = [m for m in MUROS if m[0].startswith("MX-1")][0]
    nom, dire, L, t, vanos = fila
    puestos = vanos_ubicados(nom, dire, L, vanos)

    # --- terreno y cimiento
    ax.add_patch(Rectangle((-2.0, -DF - 0.4), FRENTE + 4.0, DF + 0.4,
                           fc=E.TERRENO, ec="none", zorder=0))
    ax.plot([-2.0, FRENTE + 2.0], [0, 0], color="#6b6b6b", lw=1.1, zorder=1)
    ax.add_patch(Rectangle((-B_CIMIENTO / 2.0, -DF), FRENTE + B_CIMIENTO,
                           DF - 0.3, fc=E.CONCRETO, ec="k", lw=0.7,
                           hatch="///", zorder=1))

    # --- paramento y parapeto
    ax.add_patch(Rectangle((0, 0), FRENTE, HN, fc=MURO_F, ec="k", lw=1.1,
                           zorder=2))
    ax.add_patch(Rectangle((0, HN), FRENTE, PARAPETO, fc=PARAP,
                           ec="#d98c3f", lw=1.1, zorder=2))
    # AFUERA Y A LA IZQUIERDA. Afuera y a la derecha se montaba sobre la
    # cota «+14.60 (tope parapeto)» -- el 94 % de su caja -- porque las dos
    # ocupan la misma banda. A la izquierda la unica vecina es la cota
    # vertical del 1,10 y hay mas de un metro de dibujo libre.
    ax.annotate("PARAPETO h = %.2f m" % PARAPETO,
                xy=(FRENTE * 0.40, HN + PARAPETO * 0.75),
                xytext=(FRENTE * 0.22, HN + PARAPETO + 1.05),
                ha="left", va="center", fontsize=7.6, color="#a5642a",
                fontweight="bold", zorder=6,
                arrowprops=dict(arrowstyle="->", color="#a5642a", lw=0.9))

    # --- líneas de nivel y símbolo de NPT
    for k in range(N_PISOS + 1):
        y = k * H_ENTREPISO
        ax.plot([0, FRENTE], [y, y], color=E.GUIA, lw=0.7, ls=(0, (6, 4)),
                zorder=3)
        etiqueta = ("+%.2f (techo P%d)" % (y, k) if 0 < k < N_PISOS
                    else ("+%.2f (azotea)" % y if k == N_PISOS
                          else "± 0.00 (P1)"))
        E.nivel(ax, FRENTE + 0.55, y, etiqueta, fs=8)
    E.nivel(ax, FRENTE + 0.55, HN + PARAPETO,
            "+%.2f (tope parapeto)" % (HN + PARAPETO), fs=8)

    # --- los vanos, en su posición real
    # CADA VANO CON SU TIPO. La fachada frontal no son cuatro ventanas:
    # son tres ventanas y la PUERTA DE INGRESO al hall, que nace en el piso
    # y no sobre un alfeizar. El dibujo lo tomaba del muro y por eso el
    # edificio aparecia sin puerta.
    n_v = 0
    for k in range(N_PISOS):
        for j, (x0, ancho) in enumerate(puestos):
            # PUERTA SOLO EN EL PRIMER PISO, Y DE SU ALTO REAL. Ver el
            # porque en la cabecera del arreglo: `tipo_de_vano` no sabe de
            # que piso se trata y `altura_de_vano` devuelve la altura de
            # METRADO -- 1,00 m, porque en cuatro de los cinco pisos ese
            # vano es la ventana del hall. Tomadas las dos al pie de la
            # letra, la elevacion dibujaba una puerta de ingreso de un
            # metro de alto, cinco veces.
            es_vent = tipo_de_vano(nom, x0) == "ventana" or k > 0
            h_v = altura_de_vano(nom, x0) if es_vent else ALTO_PUERTA
            base = k * H_ENTREPISO + (ALFEIZAR if es_vent else 0.0)
            if es_vent:
                col, borde = VENT, "#2e6da4"
            else:
                col, borde = "#bcaaa4", "#5d4037"
            ax.add_patch(Rectangle((x0, base), ancho, h_v, fc=col,
                                   ec=borde, lw=0.9, zorder=4))
            # las dos hojas, que es como se dibuja una ventana o una puerta
            ax.plot([x0 + ancho / 2.0] * 2, [base, base + h_v],
                    color=borde, lw=0.6, zorder=5)
            if es_vent:
                ax.plot([x0, x0 + ancho], [base + h_v / 2.0] * 2,
                        color=borde, lw=0.6, zorder=5)
            if k == N_PISOS - 1 and es_vent:
                ax.text(x0 + ancho / 2.0, base + h_v + 0.22,
                        "V-%d" % (1 if ancho > 1.4 else 2), ha="center",
                        fontsize=7.5, color=borde, fontweight="bold")
            if k == 0 and not es_vent:
                ax.text(x0 + ancho / 2.0, base + h_v + 0.22, "P-ING",
                        ha="center", fontsize=7.5, color=borde,
                        fontweight="bold")
            n_v += 1

    # --- ejes con burbuja
    xs, ets = _ejes_de_fachada()
    for x, et in zip(xs, ets):
        ax.plot([x, x], [-DF - 0.9, HN + PARAPETO + 0.6], color=E.BURBUJA,
                lw=0.7, ls=(0, (7, 4)), alpha=0.8, zorder=1)
        E.burbuja(ax, x, -DF - 1.6, et)

    # --- cotas encadenadas
    E.cadena(ax, -DF - 2.9, xs, ["%.2f" % (xs[i + 1] - xs[i])
                                 for i in range(len(xs) - 1)])
    E.cota_h(ax, -DF - 4.8, 0.0, FRENTE, "%.2f m (frente)" % FRENTE,
             color=E.COTA, fs=8.5, remate=0.18)
    niveles = [k * H_ENTREPISO for k in range(N_PISOS + 1)] + [HN + PARAPETO]
    E.cadena(ax, -1.5, niveles, vertical=True,
             etiquetas=["%.2f" % H_ENTREPISO] * N_PISOS + ["%.2f" % PARAPETO])
    E.cota_v(ax, -3.6, 0.0, HN + PARAPETO,
             "%.2f m (total)" % (HN + PARAPETO), color=E.COTA, fs=8.5,
             remate=0.18, lado=-1)

    # --- cotas del vano tipo: se acota una VENTANA, que es lo repetitivo
    vents = [(x0, a) for x0, a in puestos
             if tipo_de_vano(nom, x0) == "ventana"]
    x0, ancho = vents[0]
    h_vano = altura_de_vano(nom, x0)
    E.cota_h(ax, ALFEIZAR - 0.42, x0, x0 + ancho, "%.2f" % ancho,
             color=E.VERDE, fs=7.5)
    E.cota_v(ax, x0 - 0.40, 0.0, ALFEIZAR, "alféizar %.2f" % ALFEIZAR,
             color=E.VERDE, fs=7.5, lado=-1)
    E.cota_v(ax, x0 + ancho + 0.40, ALFEIZAR, ALFEIZAR + h_vano,
             "%.2f" % h_vano, color=E.VERDE, fs=7.5)
    # y la puerta de ingreso, que es unica, con su propia cota
    puertas = [(a, b) for a, b in puestos
               if tipo_de_vano(nom, a) == "puerta"]
    for px, pa in puertas:
        E.cota_v(ax, px + pa + 0.40, 0.0, altura_de_vano(nom, px),
                 "%.2f" % altura_de_vano(nom, px), color="#5d4037", fs=7.5)
    return n_v, puestos, h_vano


def _pie_de_vanos():
    """Los datos de los vanos, que es lo único que la ficha aportaba."""
    fila = [m for m in MUROS if m[0].startswith("MX-1")][0]
    nom_f, dire_f, L_f, _t, vanos_f = fila
    puestos = vanos_ubicados(nom_f, dire_f, L_f, vanos_f)
    vents = [(x, a) for x, a in puestos
             if tipo_de_vano(nom_f, x) == "ventana"]
    anchos = sorted({a for _x, a in vents}, reverse=True)
    h_vano = altura_de_vano(nom_f, vents[0][0])
    ings = [(x, a) for x, a in puestos if tipo_de_vano(nom_f, x) == "puerta"]
    a_ing = ings[0][1] if ings else 0.0
    # LA ALTURA DE OBRA, no la de metrado. Ver el arreglo del dibujo.
    h_ing = ALTO_PUERTA
    assert h_ing > altura_de_vano(nom_f, ings[0][0]), (
        "la puerta de ingreso quedo de %.2f m y la altura de metrado es "
        "%.2f: alguien volvio a tomar una por la otra"
        % (h_ing, altura_de_vano(nom_f, ings[0][0])))
    n_v = len(puestos) * N_PISOS
    tipo_uni, vacios = _unidad()
    return ("Fachada principal al %s, a la calle municipal, sobre el muro "
            "portante MX-1 de %s m de espesor (albañilería sólida Tipo %s, "
            "%.0f %% de vacíos) con tarrajeo exterior. Lleva %d vanos: la V-1 "
            "de %s × %s m y la V-2 de %s × %s m, las dos con alféizar de %s m "
            "y dintel de %s m, más la puerta de ingreso P-ING de %s × %s m, "
            "que existe sólo en el primer piso: en los cuatro de arriba ese "
            "mismo vano es la ventana del hall. Son %d ventanas por piso en "
            "los niveles 2 a %d y %d en el primero, iluminación y ventilación "
            "conformes al RNE A.020. El parapeto de azotea de %s m va "
            "arriostrado por el acápite 9.3.5 de la E.070. Los muros "
            "medianeros no llevan ningún vano: por eso la dirección Y "
            "concentra la rigidez, y por eso la longitud neta de MX-1 es la "
            "que se recorta."
            % (META.ORIENTACION_FACHADA, C.coma(ESPESOR, 2), tipo_uni, vacios,
               n_v, C.coma(anchos[0], 2), C.coma(h_vano, 2),
               C.coma(anchos[-1], 2), C.coma(h_vano, 2), C.coma(ALFEIZAR, 2),
               C.coma(H_DINTEL_VENTANA, 2), C.coma(a_ing, 2),
               C.coma(h_ing, 2), len(puestos), N_PISOS, len(vents),
               C.coma(PARAPETO, 2)))


def _unidad():
    """La unidad ADOPTADA, del script 13: sólida Tipo V, 30 % de vacíos.

    Viene de la ficha que el panel (c) de los cortes traía y que este pie
    hereda. No se teclea: el proyecto auditó seis fichas de fábrica para
    descartar la Tipo IV con 40 % de vacíos, que es la que la Tabla 2
    prohíbe en zona 2, y esa decisión vive en `calculo/13`.
    """
    import contextlib
    import importlib
    import io as _io6
    with contextlib.redirect_stdout(_io6.StringIO()):
        m13 = importlib.import_module("13_unidad_albanileria")
    solidas = [f for f in m13.FICHAS if f[1] == "SOLIDO"]
    tipos = set(f[8] for f in solidas)
    assert len(tipos) == 1, "las fichas solidas declaran tipos distintos"
    return tipos.pop(), m13.VACIOS_MAXIMOS


def main():
    """La elevación, con la ficha DEBAJO y no al costado.

    POR QUÉ SE REHIZO. La leyenda y la ficha de niveles se colocaban a la
    derecha del edificio, en `x = FRENTE + 10,2`: el lienzo pasaba de los
    11,90 m del frente a 28 m de ancho, y como el dibujo va con aspecto
    igual, la fachada terminaba ocupando poco más de un tercio de la hoja.
    De ahí salían los catorce solapes que contaba el auditor —la leyenda
    encima de las cotas de nivel, el rótulo del parapeto sobre el
    «+14.60»— y de ahí salía también que un edificio de cinco pisos se
    leyera del tamaño de un sello.

    Puesta la ficha debajo, el lienzo se acota al edificio y la fachada se
    dibuja al ancho entero de la página. Y la ficha, que era un bloque de
    texto monoespaciado imitando una tabla, pasa a ser una tabla.
    """
    alto_fig = 8.62
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, alto_fig), dpi=200)
    y_ar, y_ab = C.marco(
        fig, "Elevación frontal de la edificación  —  eje 1, frente a la vía",
        subtitulo="fachada frontal al %s  ·  ejes %s a %s  ·  escala 1:75"
                  % (META.ORIENTACION_FACHADA,
                     ejes_x_rotulados()[1][0],
                     ejes_x_rotulados()[1][-1]),
        pie=_pie_de_vanos())

    # LA BANDA DE LA LEYENDA SE MIDE, NO SE TANTEA. `E.leyenda` deriva el
    # alto de fila del cuerpo y de la escala del eje, y arma un recuadro de
    # alto_fila x (n + 1,9). Para que ese recuadro ENTRE hace falta que la
    # banda mida al menos (fs x 1,55 / 72) x (n + 1,9) pulgadas: con tres
    # renglones a 8 pt son 0,85. Puesta mas baja, el recuadro se dibujaba
    # mas alto que su propio eje y las dos ultimas muestras de color se
    # perdian por debajo -- que es exactamente lo que pasaba.
    # EL PISO DE 0,42 DE `alto_fila` MANDABA. La funcion toma el MAYOR
    # entre el alto que le pasan y el que deriva de la escala: con la banda
    # a una pulgada, el derivado da 0,17 y el piso por omision 0,42 -- o
    # sea que el recuadro salia 2,5 veces mas alto que su propio eje. Se le
    # pasa un piso chico para que mande el medido, y se hace que el eje
    # tenga tantas unidades de Y como pulgadas: asi metro y pulgada
    # coinciden y la cuenta de abajo es directa.
    FILA_LEY = 8.0 * 1.55 / 72.0
    ALTO_BANDA = FILA_LEY * (3 + 1.9) + 0.16
    y_banda = y_ab + 0.005
    h_banda = ALTO_BANDA / alto_fig

    # ---- (a) la fachada, con lo que quede de hoja ----------------------
    y_dib = y_banda + h_banda + 0.010
    alto_a = (y_ar - 0.010) - y_dib
    ax = fig.add_axes((0.045, y_dib, 0.915, alto_a))
    n_v, puestos, _h = dibujar(ax)
    E.limpiar(ax, xlim=(-4.6, FRENTE + 3.4),
              ylim=(-DF - 4.7, HN + PARAPETO + 1.2))

    # ---- (b) la leyenda, en dos columnas ------------------------------
    axl = fig.add_axes((0.045, y_banda, 0.915, h_banda))
    axl.set_xlim(0, 10.0)
    axl.set_ylim(0, ALTO_BANDA)
    axl.axis("off")
    izq = [(MURO_F, "k", "Paramento de fachada"),
           (PARAP, "#d98c3f", "Parapeto h = %s m (azotea)" % C.coma(PARAPETO, 2)),
           (VENT, "#2e6da4", "Ventana de fachada (V-1 / V-2)")]
    der = [(E.CONCRETO, "k", "Cimiento corrido B = %s m" % C.coma(B_CIMIENTO, 2)),
           (None, E.GUIA, "Línea de nivel (N.P.T.)"),
           (None, E.BURBUJA, "Eje estructural")]
    E.leyenda(axl, izq, x=0.10, y=ALTO_BANDA - 0.04, ancho=4.75,
              titulo="LEYENDA", alto_fila=0.05)
    E.leyenda(axl, der, x=5.15, y=ALTO_BANDA - 0.04, ancho=4.75, titulo=" ", alto_fila=0.05)

    ruta, peso = C.guardar(fig, os.path.join(R.INFORME, "ELEVACION.png")), 0
    ruta = os.path.join(R.INFORME, "ELEVACION.png")
    peso = os.path.getsize(ruta)
    return ruta, peso, n_v


def control(n_v):
    fila = [m for m in MUROS if m[0].startswith("MX-1")][0]
    esperados = len(fila[4]) * N_PISOS
    assert n_v == esperados, (
        "la elevacion dibuja %d vanos y el SSOT declara %d" % (n_v, esperados))
    medianeras = [m for m in MUROS if m[0].startswith(("MY-1", "MY-2"))]
    for m in medianeras:
        assert not m[4], "%s es medianera y tiene vanos declarados" % m[0]
    print("  [ok] %d vanos, los que declara el SSOT" % n_v)
    print("  [ok] las dos medianeras siguen sin vanos")
    return True


if __name__ == "__main__":
    ruta, peso, n_v = main()
    print("=" * 74)
    print("ELEVACION FRONTAL  -  criterio 1")
    print("=" * 74)
    print()
    print("  archivo : %s  (%.1f KB)" % (os.path.basename(ruta), peso / 1024.0))
    print("  %d vanos en %d pisos, ejes %s a %s"
          % (n_v, N_PISOS, ejes_x_rotulados()[1][0],
             ejes_x_rotulados()[1][-1]))
    print()
    control(n_v)
