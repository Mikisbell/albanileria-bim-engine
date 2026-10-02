import re
# -*- coding: utf-8 -*-
"""Elementos de confinamiento: secciones con su armado — criterio 9.

QUE PIDE LA RUBRICA
===================
*"Diseña los elementos de confinamiento de forma pertinentes y realiza las
verificaciones de forma completa. El diseño será PLASMADO EN PLANOS."*

Lo que hay que plasmar es el ARMADO: qué sección tiene cada tipo, cuántas
varillas lleva, de qué diámetro, y cómo van los estribos. Eso es un detalle
de sección, no una planta: en una planta las columnas son cuadraditos de
24 cm y no se ve nada.

QUE MUESTRA, Y POR QUE ASI
==========================
Las secciones al mismo tamaño, una al lado de otra, con las varillas
en su posición real dentro del núcleo. Comparar es el punto: se ve de un
golpe que la C-2 extrema lleva doce varillas de 3/4" y la C-1 interior seis
de 1/2", porque la Tabla 11 de la E.070 les da fuerzas muy distintas.

Debajo, el desarrollo del estribado con su zona de confinamiento acotada,
que es donde el acápite 8.6.3-a.3 concentra los estribos.

Todo sale de calculo/19_confinamientos.py: ninguna cifra se teclea.
"""
import contextlib
import importlib.util
import io as _io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))
sys.path.insert(0, AQUI)

import rutas as R                                        # noqa: E402

import cuadro as C
import estilo as E                                                 # noqa: E402
from matplotlib.patches import Rectangle, Circle                   # noqa: E402
from proyecto import ESPESOR, FC, FY, H_ENTREPISO                  # noqa: E402

RECUB = 2.5          # no-ssot: cm, el mismo del script 19


def _cargar(nombre):
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "f", ruta)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def datos():
    """El cuadro de elementos, tal como lo calcula el criterio 9."""
    R19 = _cargar("19_confinamientos.py")
    with contextlib.redirect_stdout(_io.StringIO()):
        # EL CUADRO SALE DEL 39, no del 19: la C-4 no la conoce el 19
        # porque no sale del diseno de un muro aislado sino de la malla.
        # Tomarlo del 19 dejaba la figura con cuatro tipos y el informe con
        # cinco.
        cuadro = _cargar("39_columnas_en_planta.py").cuadro_completo()
        s, zona, n_est = R19.estribaje_adoptado(
            [R19.H_COLUMNA * 100.0, R19.H_COLUMNA_EXT * 100.0],
            2 * R19.AREA_3_8)
    return cuadro, s, zona, n_est, R19


def seccion(ax, fila, x, ancho_total):
    """Una sección de confinamiento, con su núcleo, estribo y varillas."""
    b = fila["b"] * 100.0
    h = fila["h"] * 100.0
    y0 = 0.0
    # concreto
    ax.add_patch(Rectangle((x, y0), b, h, fc=E.CONCRETO, ec=E.BORDE_CON,
                           lw=1.2))
    # núcleo confinado por el estribo
    ax.add_patch(Rectangle((x + RECUB, y0 + RECUB), b - 2 * RECUB,
                           h - 2 * RECUB, fc="none", ec=E.ACERO, lw=1.6))
    # DONDE VA CADA VARILLA LO DICE EL 19, no esta figura. Antes aca habia
    # una regla propia que con 11 barras dejaba una suelta en el CENTRO del
    # nucleo, sin estribo que la tomara (E.060 7.10.5.3).
    d = fila["disp"]
    for (ga, gb) in d["ganchos"]:
        ax.plot([x + ga[0], x + gb[0]], [y0 + ga[1], y0 + gb[1]],
                color=E.ACERO, lw=1.3, zorder=4)
    for px, py in d["puntos"]:
        ax.add_patch(Circle((x + px, y0 + py), d["db"] / 2.0 + 0.25,
                            fc=E.ACERO, ec="k", lw=0.5, zorder=5))
    n = len(d["puntos"])

    ax.text(x + b / 2.0, h + 6.6, fila["tipo"], ha="center", fontsize=11,
            fontweight="bold", color=E.TINTA)
    # LA SECCION VA ACOTADA, no rotulada. Decia "24 x 30 cm" como texto
    # suelto encima: eso informa, pero no es una cota -- no dice QUE mide
    # cada lado ni permite verificar el dibujo contra el numero. Mikis pidio
    # el 2026-09-21 la medida acotada en las dos direcciones.
    E.cota_h(ax, y0 - 3.4, x, x + b, "%.0f" % b, fs=8, remate=0.8)
    E.cota_v(ax, x + b + 2.0, y0, y0 + h, "%.0f" % h, fs=8, remate=0.8)
    # y el recubrimiento, que es lo que define el nucleo confinado
    E.cota_h(ax, y0 + h + 1.3, x, x + RECUB, "", fs=7, remate=0.5,
             color=E.GUIA)
    # EL RECUBRIMIENTO SE DICE UNA VEZ, EN EL TITULO DEL PANEL. Escrito
    # en las cinco secciones, el rotulo caia sobre el nombre del elemento
    # -- cinco solapes, uno por seccion -- y ademas repetia cinco veces el
    # mismo 2,5 cm. La cota guia se queda: es la que muestra el nucleo.
    # EL ACERO NO SE ESCRIBE ACA. Ver el porque en la cabecera: los
    # cuatro rotulos apilados bajo cada seccion eran los 19 solapes de
    # esta figura. Van al cuadro del panel (b).
    return n


def _cm(v):
    """5 -> «5»; 52.5 -> «52,5». La coma del informe, sin decimales de mas."""
    return C.coma(v, 0) if abs(v - round(v)) < 1e-9 else C.coma(v, 1)


def desarrollo(ax, s, zona, n_est, fila, primero):
    """El estribado, dibujado ACOSTADO y con corte de eje.

    A escala real una columna de 24 x 270 cm es una tira de la que no se lee
    nada. Se dibuja horizontal -- aprovecha el ancho de la pagina -- y con un
    CORTE DE EJE en el tramo central, que es como se dibuja un elemento largo
    en un plano: lo que importa son los dos extremos, donde el 8.6.3-a.3
    concentra los estribos.
    """
    b = fila["b"] * 100.0
    cubierta = primero + (n_est - 1) * s
    visible = cubierta + 40.0        # zona de confinamiento + algo del resto
    corte = 26.0                     # ancho del quiebre

    for x0 in (0.0, visible + corte):
        ax.add_patch(Rectangle((x0, 0), visible, b, fc=E.CONCRETO,
                               ec=E.BORDE_CON, lw=1.0))
    # el quiebre: dos zetas que dicen "aqui el elemento sigue"
    xm = visible
    for yy in (0.0, b):
        ax.plot([xm, xm + corte * 0.35, xm + corte * 0.65, xm + corte],
                [yy, yy, yy, yy], color=E.BORDE_CON, lw=1.0)
    for dx in (corte * 0.40, corte * 0.60):
        ax.plot([xm + dx - 3, xm + dx + 3], [-2.5, b + 2.5],
                color=E.GUIA, lw=1.0)

    # estribos: apretados en la zona de confinamiento, amplios en el resto
    resto = 25.0
    for base, signo, x_ini in ((0.0, 1, 0.0), (0.0, -1, 2 * visible + corte)):
        for k in range(n_est):
            # el primero a `primero` del borde (1 @ 5), no al recubrimiento
            x = x_ini + signo * (primero + k * s)
            ax.plot([x, x], [1.5, b - 1.5], color=E.ACERO, lw=1.6)
        x = x_ini + signo * (cubierta + resto)
        # CADA EXTREMO EN SU PIEZA. El limite era el dibujo entero, asi que
        # los estribos amplios de un extremo cruzaban el corte y caian dentro
        # de la zona de confinamiento del otro, entre los de 5 cm.
        lim = (0.0, visible) if signo > 0 else (visible + corte, 2 * visible + corte)
        while lim[0] <= x <= lim[1]:
            ax.plot([x, x], [1.5, b - 1.5], color=E.ACERO, lw=1.0, alpha=0.8)
            x += signo * resto

    # LA COTA SIN SU TEXTO ENCIMA.  escribe el rotulo pegado a la
    # linea, y con 52 cm de zona el rotulo es mas largo que la cota: se
    # montaba sobre su propia flecha. Va aparte, arriba.
    # LA COTA ES LO CUBIERTO, Y EL ROTULO DICE LAS DOS COSAS. Decia «52 cm»:
    # lo exigido (52,5) redondeado hacia abajo, que es justo el lado que no.
    E.cota_h(ax, b + 6.0, 0.0, cubierta, "", color=E.ROJO, fs=8.5, remate=1.6)
    ax.text(cubierta / 2.0, b + 8.4,
            "zona de confinamiento\n%s cm ≥ %s cm exigidos" % (_cm(cubierta), _cm(zona)),
            ha="center", fontsize=8.5, color=E.ROJO, linespacing=1.15)
    ax.text(cubierta / 2.0, -7.5, "%d estribos @ %s cm" % (n_est, _cm(s)),
            ha="center", fontsize=8.5, color=E.ROJO, fontweight="bold")
    # EN OTRO RENGLON, NO AL LADO. Los dos rotulos del paso compartian la
    # linea -7,5 y el primero mide 1,5 pulgadas: se pisaban siempre, con
    # cualquier zona de confinamiento. Bajar el segundo lo resuelve para
    # todo valor, que es lo que distingue arreglar de correr el problema.
    # EN EL OTRO EXTREMO. Bajo el primero se montaba sobre el rotulo rojo;
    # el tramo con paso amplio del extremo derecho esta libre.
    ax.text(visible + corte + 20.0, -7.5,
            "resto @ %s cm" % _cm(resto),
            ha="center", fontsize=8.5, color=E.GUIA)
    E.cota_v(ax, -8.0, 0, b, "%.0f cm" % b, color=E.AZUL, fs=8,
             remate=1.6, lado=-1)
    ax.text(xm + corte / 2.0, b + 4.0, "entrepiso\n%.0f cm" % (H_ENTREPISO * 100),
            ha="center", fontsize=8, color=E.GUIA)
    ax.text(2 * visible + corte + 4, b / 2.0,
            "el mismo detalle\nen los dos extremos", fontsize=8,
            color=E.GUIA, va="center")


def formatear_estribo(s):
    s = s.replace('"', "''")
    if " (" in s and ")" in s:
        antes, resto = s.split(" (", 1)
        adentro, despues = resto.split(")", 1)
        adentro = adentro.replace(" junto a puerta", " (puerta)").replace(" junto a ventana", " (ventana)").replace(", ", " · ")
        adentro = "junto a vano: " + adentro
        return antes + despues + "\n" + adentro
    return s

def cuadro_de_columnas(ax, cuadro):
    """El cuadro de columnas: lo que antes se apilaba bajo cada sección.

    La columna del As dice provisto y requerido juntos, porque lo que se
    verifica es la desigualdad, no cada número por su lado. Donde el
    acápite no exige As (la solera y la columna interior sin tracción) se
    escribe «no exigido» y no un guion, que se lee como dato perdido.
    """
    filas = []
    for f in cuadro:
        if f.get("As_req"):
            veredicto = "%s ≥ %s" % (C.coma(f["As_prov"], 2),
                                     C.coma(f["As_req"], 2))
        else:
            veredicto = "%s  ·  no exigido" % C.coma(f["As_prov"], 2)
        filas.append([f["tipo"],
                      "%.0f × %.0f" % (f["b"] * 100, f["h"] * 100),
                      "%d ø %s" % (f["n"], f["diam"]),
                      formatear_estribo(f["estribo"]),
                      veredicto])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    C.tabla(ax, 0.02, 0.97, 0.96, 0.135,
            ["Elemento", "b × h\n(cm)", "Refuerzo\nlongitudinal",
             "Estribos", "As provisto ≥ requerido\n(cm²)"],
            filas, fs=8.0)


def main():
    cuadro, s, zona, n_est, R19 = datos()
    fig, (ax1, ax3, ax2) = E.figura(
        "Elementos de confinamiento  ·  secciones y armado  —  E.070 8.6.3",
        alto=8.50, filas=3, cols=1)

    # EL CONTEO SE DERIVA Y LA FRASE SE ACORTA: decia «cinco» mientras el
    # titulo decia «cuatro», y era tan larga que se cortaba en «cr».
    E.panel(ax1, "a", ("Las %s secciones a igual escala · r = %s cm al "
                      "estribo (E.070 4.2.10)"
                      % ({4: "cuatro", 5: "cinco", 6: "seis"}.get(len(cuadro),
                                                              len(cuadro)),
                         _cm(RECUB))))
    x, paso, total = 0.0, 48.0, 0
    for fila in cuadro:
        total += seccion(ax1, fila, x, paso)
        x += paso
    E.limpiar(ax1, xlim=(-10, x + 6), ylim=(-8, 46))

    E.panel(ax3, "b", "Cuadro de columnas: el acero que lleva cada una")
    cuadro_de_columnas(ax3, cuadro)

    extrema = cuadro[0]
    E.panel(ax2, "c", "Estribado en altura de la C-2 (E.070 8.6.3-a.3: "
                      "rige s3 = d/4)")
    desarrollo(ax2, s, zona, n_est, extrema, R19.S3_MIN)
    cubierta = R19.S3_MIN + (n_est - 1) * s
    E.limpiar(ax2, xlim=(-18, 2 * (cubierta + 40.0) + 26 + 64), ylim=(-16, 50))

    # «NO LOS 10 CM DEL MINIMO» era falso: 10 cm es s4, el TOPE del acapite.
    zona_c1 = R19.estribos(R19.H_COLUMNA * 100.0, 2 * R19.AREA_3_8)[5]
    n_est_c1 = int(zona_c1 / s)
    ganchos = len(extrema["disp"]["ganchos"])
    E.pie(fig,
          "El acápite manda EL MENOR de s1..s4; con ø 3/8\" rige s3 = d/4, y el "
          "paso de %s cm queda bajo s4 = %s cm, el tope. La C-1 y la C-4 llevan "
          "%d @ %s, que cubren sus %s cm; junto a un vano, la zona se mide desde "
          "el fondo del dintel. La C-2 lleva %d gancho en cada estribo "
          "para la barra central de las caras largas (E.060 7.10.5.3)."
          % (_cm(s), _cm(R19.S4), n_est_c1, _cm(s), _cm(zona_c1), ganchos))
    ruta, peso = E.guardar(fig, os.path.join(R.INFORME, "CONFINAMIENTOS.png"))
    return ruta, peso, cuadro, total, s, zona, n_est


def control(cuadro, total, s, zona, n_est):
    """Que la figura dibuje el armado que el script 19 calcula."""
    esperadas = sum(f["n"] for f in cuadro)
    assert total == esperadas, (
        "la figura dibuja %d varillas y el cuadro declara %d"
        % (total, esperadas))
    for f in cuadro:
        assert f["n"] >= 4, (
            "%s con %d varillas: el 8.6.3-a.2 exige un minimo de 4"
            % (f["tipo"], f["n"]))
        if f.get("As_req"):
            assert f["As_prov"] >= f["As_req"], (
                "%s: el armado provisto (%.1f) no llega al requerido (%.1f)"
                % (f["tipo"], f["As_prov"], f["As_req"]))
    # lo cubierto se mide como se arma: el primero a 5 cm y los demas al paso
    primero = _cargar("19_confinamientos.py").S3_MIN
    cubierta = primero + (n_est - 1) * s
    assert cubierta >= zona - 1e-9, (
        "los %d estribos a %.1f cm cubren %.1f cm y la zona es de %.1f"
        % (n_est, s, cubierta, zona))
    for f in cuadro:
        d = f["disp"]
        assert d["libre"] >= d["exigido"] - 1e-9, (
            "%s: %.2f cm libres entre barras, la E.060 7.6.3 pide %.2f"
            % (f["tipo"], d["libre"], d["exigido"]))
    print("  [ok] %d varillas dibujadas, las que declara el cuadro" % total)
    print("  [ok] las %d secciones llevan 4 varillas o mas (8.6.3-a.2)"
          % len(cuadro))
    print("  [ok] %d estribos @ %.1f cm cubren %.1f cm >= %.1f cm de zona"
          % (n_est, s, cubierta, zona))
    print("  [ok] distancia libre entre barras >= E.060 7.6.3 en las %d"
          % len(cuadro))
    return True


if __name__ == "__main__":
    ruta, peso, cuadro, total, s, zona, n_est = main()
    print("=" * 78)
    print("ELEMENTOS DE CONFINAMIENTO  -  criterio 9 de la rubrica")
    print("=" * 78)
    print()
    print("  archivo : %s  (%.1f KB)" % (os.path.basename(ruta), peso / 1024.0))
    for f in cuadro:
        print("     %-6s %.0f x %.0f cm   %2d o %-6s  %s"
              % (f["tipo"], f["b"] * 100, f["h"] * 100, f["n"], f["diam"],
                      f["estribo"]))

    control(cuadro, total, s, zona, n_est)
