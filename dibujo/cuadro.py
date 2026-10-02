# -*- coding: utf-8 -*-
"""El motor de las LAMINAS-CUADRO, con el patrón que usa la clase.

POR QUE EXISTE
==============
El docente revisó el informe y pidió **una imagen por tema, como las tablas
de sus diapositivas**. Al mirar sus clases 05 y 06 el patrón es siempre el
mismo, y es un patrón bueno:

    PASO N — nombre del paso
    la FORMULA normativa, grande, con su acápite al lado
    la TABLA con una columna por cada término de esa fórmula
    la fila Σ cuando la verificación es de suma
    la COMPROBACION escrita con sus números y el veredicto
    una nota de lectura

Lo que enseña no es la tabla: es que **cada columna de la tabla es un
término de la fórmula de arriba**, de modo que el lector puede rehacer la
cuenta con la vista. Una tabla de Word suelta no hace eso; hay que ir a
buscar la fórmula a otro párrafo.

Este módulo dibuja esa lámina. No calcula nada: recibe lo que los scripts
ya calcularon y lo compone. Así cinco láminas salen de una sola fuente y no
de cinco copias del mismo código de dibujo.

CRITERIO DE ESTILO
==================
Se conserva el **aire** de la clase —cabecera de tabla en azul, franja roja
bajo el título, Σ resaltada— porque es lo que el docente reconoce y lo que
pidió. Lo que NO se copia es el blanco y negro ni las tablas de Excel
pegadas: el color sale de `paleta.py`, que es la del resto del informe, y el
veredicto se pinta con el semáforo del proyecto.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import paleta as PAL                                           # noqa: E402
import matplotlib                                              # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402
import textwrap                                                # noqa: E402
from matplotlib.patches import Rectangle                       # noqa: E402

AZUL = "#2e5c9a"          # el azul de cabecera de la clase
AZUL_OSCURO = "#1f3f6b"
ROJO = "#c0392b"          # la franja bajo el título
FILA_A = "#ffffff"
FILA_B = "#f1f5f9"
SUMA_BG = "#dbe6f4"
BORDE = "#8fa6c0"
TINTA = "#1e293b"


# EL MINIMO DE ANCHO DE COLUMNA estaba calibrado para el lienzo de 13,6
# pulgadas de la diapositiva: 0,055 de fraccion daban 0,75" y sobraba. En la
# hoja, los mismos 0,055 dan 0,35" y "MX-1" se pega con "11,90". El minimo
# tiene que ser el que necesita el CONTENIDO, no una fraccion heredada.
# Ver el porque en el docstring de _ancho_pedido: el aire no era el
# problema -- la normalizacion lo encogia igual que al texto -- y subirlo a
# 0,13 solo conseguia que la tabla no entrara. 0,05" por lado, a 7 pt, es un
# espacio en blanco holgado.
PAD_CELDA = 0.05        # pulgadas de aire a cada lado del texto de una celda


def _ancho_col(cols, filas, minimo=0.055, ax=None, fs=8.2):
    """Ancho relativo de cada columna, MIDIENDO el texto de cada celda.

    Ver el porqué en el encabezado de este bloque: contar caracteres es una
    estimación, y con seis columnas en 6,30 pulgadas la estimación se come
    el aire entre columnas.
    """
    n = len(cols)
    if ax is not None:
        fig = ax.figure
        r = fig.canvas.get_renderer()

        def mide(s, peso="normal"):
            o = fig.text(0, 0, s, fontsize=fs, fontweight=peso)
            w = o.get_window_extent(renderer=r).width / float(fig.dpi)
            o.remove()
            return w

        largos = []
        for j in range(n):
            # la cabecera puede venir en dos renglones: manda el más ancho
            w = max(mide(x, "bold")
                    for x in str(cols[j]).split(chr(10)) or [""])
            for f in filas:
                w = max(w, mide(str(f[j])))
            largos.append(w + 2 * PAD_CELDA)
    else:
        largos = []
        for j in range(n):
            L = len(str(cols[j]).replace(chr(10), ""))
            for f in filas:
                L = max(L, len(str(f[j])))
            largos.append(max(L, 4))
    tot = float(sum(largos))
    w = [max(minimo, x / tot) for x in largos]
    # RENORMALIZAR. Sin esto, cada columna que toca el minimo empuja a la
    # suma por encima de 1 y las celdas se dibujan mas anchas que la tabla.
    s = sum(w)
    w = [x / s for x in w]
    assert abs(sum(w) - 1.0) < 1e-9, "los anchos de columna no suman 1"
    return w


def _ancho_pedido(cols, filas, ax, fs):
    """Las pulgadas que la tabla necesita: texto mas aire, sin normalizar."""
    fig = ax.figure
    r = fig.canvas.get_renderer()

    def mide(s, peso="normal"):
        o = fig.text(0, 0, s, fontsize=fs, fontweight=peso)
        w = o.get_window_extent(renderer=r).width / float(fig.dpi)
        o.remove()
        return w

    total = 0.0
    for j in range(len(cols)):
        w = max(mide(x, "bold") for x in str(cols[j]).split(chr(10)) or [""])
        for f in filas:
            w = max(w, mide(str(f[j])))
        total += w + 2 * PAD_CELDA
    return total


def tabla(ax, x0, y0, ancho, alto_fila, cols, filas, suma=None,
          titulo=None, resaltar=None, colores_fila=None, fs=8.2):
    """Dibuja una tabla y devuelve la Y de su borde inferior.

    `resaltar` es el índice de la columna de veredicto, que se pinta con el
    semáforo: lo que cumple en verde, lo que no en rojo. Un veredicto en
    negro obliga a leer la palabra; en color se ve de lejos, que es de lo
    que se trata.
    """
    # EL CUERPO BAJA HASTA QUE LA TABLA ENTRE. Ver el porque arriba.
    pulg = ancho * ax.figure.get_size_inches()[0]
    while fs > 6.0 and _ancho_pedido(cols, filas, ax, fs) > pulg:
        fs -= 0.2
    pedido = _ancho_pedido(cols, filas, ax, fs)
    assert pedido <= pulg + 0.02, (
        "la tabla pide %.2f\" y tiene %.2f\" ni bajando el cuerpo a %.1f pt: "
        "sacale una columna o partila en dos bloques" % (pedido, pulg, fs))
    anchos = [a * ancho for a in _ancho_col(cols, filas, ax=ax, fs=fs)]
    y = y0
    if titulo:
        ax.add_patch(Rectangle((x0, y - alto_fila), ancho, alto_fila,
                               fc=AZUL_OSCURO, ec=BORDE, lw=0.6, zorder=2))
        pulg_bloque = ancho * ax.figure.get_size_inches()[0] - 2 * PAD_CELDA
        ax.text(x0 + ancho / 2, y - alto_fila / 2, titulo, ha="center",
                va="center",
                fontsize=_fs_que_entra(titulo, fs + 0.8, pulg_bloque, "bold"),
                color="white", fontweight="bold", zorder=3)
        y -= alto_fila
    # cabecera
    x = x0
    n_lineas = max(str(c).count(chr(10)) + 1 for c in cols)
    alto_cab = alto_fila * (1.0 if n_lineas == 1 else 1.45)
    for j, c in enumerate(cols):
        ax.add_patch(Rectangle((x, y - alto_cab), anchos[j], alto_cab,
                               fc=AZUL, ec=BORDE, lw=0.6, zorder=2))
        ax.text(x + anchos[j] / 2, y - alto_cab / 2, str(c), ha="center",
                va="center", fontsize=fs, color="white", fontweight="bold",
                zorder=3, linespacing=1.25)
        x += anchos[j]
    y -= alto_cab
    # filas
    for i, f in enumerate(filas):
        x = x0
        base = FILA_A if i % 2 == 0 else FILA_B
        if colores_fila and colores_fila[i]:
            base = colores_fila[i]
        for j, v in enumerate(f):
            ax.add_patch(Rectangle((x, y - alto_fila), anchos[j], alto_fila,
                                   fc=base, ec=BORDE, lw=0.5, zorder=2))
            col, peso = TINTA, "normal"
            if resaltar is not None and j == resaltar:
                txt = str(v).lower()
                col = PAL.BIEN if ("cumple" in txt and "no" not in txt) \
                    or "conforme" in txt or txt == "ok" else PAL.ALERTA
                peso = "bold"
            ax.text(x + anchos[j] / 2, y - alto_fila / 2, str(v),
                    ha="center", va="center", fontsize=fs, color=col,
                    fontweight=peso, zorder=3)
            x += anchos[j]
        y -= alto_fila
    # fila de suma
    if suma is not None:
        x = x0
        for j, v in enumerate(suma):
            ax.add_patch(Rectangle((x, y - alto_fila), anchos[j], alto_fila,
                                   fc=SUMA_BG, ec=BORDE, lw=0.8, zorder=2))
            ax.text(x + anchos[j] / 2, y - alto_fila / 2, str(v),
                    ha="center", va="center", fontsize=fs, color=AZUL_OSCURO,
                    fontweight="bold", zorder=3)
            x += anchos[j]
        y -= alto_fila
    return y


# LA CAJA DE LA PAGINA, en pulgadas. Una A4 con margenes de 2,5 cm deja
# 16,0 x 24,0 cm. Es la unidad en la que se dibuja: una lamina se compone
# PARA la hoja, no se dibuja grande y se reduce despues -- reducir achica el
# tipo, que esta en puntos, y es como llegamos a rotulos de 2 pt.
ANCHO_PAGINA = 6.30
# 22,5 cm: lo que el armador le concede a una figura, dejando 2,2 para
# el caption. Es el alto REAL contra el que hay que componer, no los
# 24,7 de la caja de texto.
ALTO_PAGINA = 8.86
# El alto MAXIMO de una lamina no lo fija la hoja sino la legibilidad: a
# 10,9" Word la reduce a 0,87 y un cuerpo de 7,5 pt aterriza en 6,5, que es
# el minimo que se lee en papel. Mas alta, hay que partirla en dos.
ALTO_MAX_LAMINA = 10.20


def _envolver_medido(texto, fs, pulgadas, peso="normal"):
    """Parte `texto` en las lineas que hagan falta para no pasar de
    `pulgadas`, MIDIENDO el texto real con el renderer.

    No se estiman caracteres por pulgada: estas lineas estan hechas de
    simbolos -- sigma, flechas, el signo mayor-o-igual -- y una estimacion
    por caracteres falla justo ahi. Se mide sobre una figura de descarte,
    antes de construir la de verdad, porque el numero de lineas cambia el
    alto y el alto hay que conocerlo para dibujar.
    """
    if not texto:
        return []
    aux = plt.figure(figsize=(pulgadas, 1.0), dpi=200)
    r = aux.canvas.get_renderer()

    def ancho(s):
        obj = aux.text(0, 0, s, fontsize=fs, fontweight=peso)
        w = obj.get_window_extent(renderer=r).width / float(aux.dpi)
        obj.remove()
        return w

    if ancho(texto) <= pulgadas:
        plt.close(aux)
        return [texto]
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = (actual + " " + palabra).strip()
        if actual and ancho(prueba) > pulgadas:
            lineas.append(actual)
            actual = palabra
        else:
            actual = prueba
    if actual:
        lineas.append(actual)
    plt.close(aux)
    return lineas


def envolver(ax, texto, fs, ancho_frac, peso="normal"):
    """Las lineas en que hay que partir `texto` para ocupar `ancho_frac` del
    ancho de la figura. Para los CROQUIS, que dibujan en fraccion de eje.

    POR QUE ESTA. Los croquis traian sus parrafos PARTIDOS A MANO, en
    cadenas pensadas para un lienzo de 13,6 pulgadas. Una linea partida a
    mano no se reacomoda: al llevar la lamina a la hoja, esas lineas seguian
    midiendo lo mismo y eran las que se salian -- 0,28 pulgadas en la lamina
    de densidad, medido--. Se escriben como parrafos enteros y se parten
    aca, contra el ancho que de verdad hay.
    """
    pulgadas = ancho_frac * ax.figure.get_size_inches()[0]
    return _envolver_medido(texto, fs, pulgadas, peso)


def envolver_ancho(ax, texto, fs, peso="normal"):
    """Lo que mide `texto`, en FRACCION del ancho de la figura.

    Para los croquis, que reparten su geometria en fraccion de eje y tienen
    que reservar sitio a rotulos que estan en puntos.
    """
    fig = ax.figure
    r = fig.canvas.get_renderer()
    o = fig.text(0, 0, texto, fontsize=fs, fontweight=peso)
    w = o.get_window_extent(renderer=r).width / float(fig.dpi)
    o.remove()
    return w / fig.get_size_inches()[0]


def bloque_de_texto(ax, x, y_top, ancho_frac, titular, parrafos,
                    fs_tit=8.3, fs=7.6, paso=None, color_tit="#37474f",
                    color="#55606a"):
    """Titular en negrita + parrafos, envueltos al ancho disponible.

    `y_top` y `paso` van en unidades del eje (el croquis dibuja en 0..1 de
    la lamina). Si `paso` es None se deriva del cuerpo, que es lo correcto:
    un interlineado fijo deja de servir en cuanto cambia el alto del croquis.
    """
    alto_fig = ax.figure.get_size_inches()[1]
    if paso is None:
        paso = (fs * 1.55 / 72.0) / alto_fig      # pulgadas -> fraccion
    y = y_top
    if titular:
        for ln in envolver(ax, titular, fs_tit, ancho_frac, "bold"):
            ax.text(x, y, ln, fontsize=fs_tit, color=color_tit,
                    fontweight="bold", va="top", zorder=6)
            y -= paso * 1.06
        y -= paso * 0.35
    for par in parrafos:
        if not str(par).strip():
            y -= paso * 0.55
            continue
        for ln in envolver(ax, par, fs, ancho_frac):
            ax.text(x, y, ln, fontsize=fs, color=color, va="top", zorder=6)
            y -= paso
        y -= paso * 0.45
    return y


def _fs_que_entra(texto, fs, pulgadas, peso="normal"):
    """El cuerpo mas grande, hasta `fs`, con el que `texto` entra de una
    linea. Para la formula, que no se puede partir: o entra o encoge."""
    if not texto:
        return fs
    aux = plt.figure(figsize=(pulgadas, 1.0), dpi=200)
    r = aux.canvas.get_renderer()
    cuerpo = fs
    while cuerpo > 6.0:
        obj = aux.text(0, 0, texto, fontsize=cuerpo, fontweight=peso)
        w = obj.get_window_extent(renderer=r).width / float(aux.dpi)
        obj.remove()
        if w <= pulgadas:
            break
        cuerpo -= 0.5
    plt.close(aux)
    return cuerpo


def lamina(paso, titulo, formula, acapite, bloques, comprobacion=(),
           nota="", salida=None, ancho_fig=ANCHO_PAGINA, alto_fila_in=0.21,
           fs=8.2, croquis=None, alto_croquis=0.0):
    """Arma la lámina completa con el patrón de la clase.

    EL ALTO DE LA FIGURA SE DERIVA DEL CONTENIDO, no se pasa a mano. La
    primera versión recibía `alto_fig` y una altura de fila en FRACCION del
    lienzo: con trece muros la tabla se estiraba hasta el pie y la
    comprobación y la nota quedaban ENCIMA de ella. Ahora la fila mide lo
    mismo en pulgadas siempre --que es lo que hace legible una tabla-- y la
    figura crece con las filas que haya.

    `bloques` es una lista de dicts con las tablas que van lado a lado:
        {"titulo":..., "cols":[...], "filas":[[...]], "suma":[...] | None,
         "resaltar": int | None, "colores_fila": [...] | None}
    `comprobacion` son las líneas que rehacen la cuenta con los números.

    `croquis` es una función `(ax, x0, y0, ancho, alto)` que dibuja el
    MECANISMO en una banda propia bajo la fórmula, en coordenadas del eje
    (0..1). Existe porque una tabla enseña el CÁLCULO y no el fenómeno: el
    lector que ve una columna «Ri (m)» con valores de −10,76 a +10,24 tiene
    que imaginarse la planta para entenderla. San Bartolomé resuelve eso
    dibujando los parámetros al lado de la tabla --su Fig. 8.24 ilustra
    justamente los de la Tabla 11-- y es el recurso que a estas láminas les
    faltaba. `alto_croquis` es su alto en PULGADAS, y entra en la cuenta de
    la altura de la figura como cualquier otro bloque.
    """
    # --- cuántas filas de alto necesita la tabla más alta ---------------
    n_filas = 0
    for b in bloques:
        n = len(b["filas"]) + (1 if b.get("suma") is not None else 0)
        n += 1 if b.get("titulo") else 0
        n += 1.45 if max(str(c).count(chr(10)) + 1
                         for c in b["cols"]) > 1 else 1
        n_filas = max(n_filas, n)

    # LA NOTA SE ENVUELVE AL ANCHO DE LA LAMINA. Sin envolver, una nota de
    # 400 caracteres en una sola linea hace que `bbox_inches="tight"`
    # ensanche la figura para que el texto quepa: la lamina salia de
    # proporcion 3:1 por culpa del pie, no de la tabla, y puesta en la
    # pagina la tabla quedaba diminuta. Se mide en caracteres por pulgada
    # a la tipografia del pie.
    if nota:
        ancho_car = int((ancho_fig - 0.9) * 15.5)
        nota = chr(10).join(
            chr(10).join(textwrap.wrap(p, ancho_car)) if p.strip() else ""
            for p in nota.split(chr(10)))
    n_nota = 0 if not nota else nota.count(chr(10)) + 1

    # SUBTITULO Y COMPROBACION SE ENVUELVEN AL ANCHO DE LA HOJA. Eran las
    # tres lineas que, sin envolver, hacian que `bbox_inches="tight"`
    # ENSANCHARA la lamina de 6,30 a 9,11 pulgadas para que cupieran: la
    # figura salia un 45 % mas ancha que la pagina y Word la reducia
    # despues, achicando el tipo de toda la lamina. Tight crece y calla.
    util = ancho_fig - 0.16                       # los margenes de 0,035
    titulo_ls = _envolver_medido(titulo, 10.5, util, "bold")
    comp_ls = []
    for linea in comprobacion:
        comp_ls.append(_envolver_medido(linea, 10.5, util, "bold"))
    n_comp = sum(len(g) for g in comp_ls)
    # a la derecha de la formula vive la etiqueta del acapite: su ancho se
    # descuenta, o la formula se le monta encima (ver el porque arriba).
    util_formula = util
    if acapite:
        aux = plt.figure(figsize=(util, 1.0), dpi=200)
        _o = aux.text(0, 0, acapite, fontsize=9.5, fontweight="bold")
        util_formula = util - (_o.get_window_extent(
            renderer=aux.canvas.get_renderer()).width / float(aux.dpi)) - 0.30
        plt.close(aux)
    fs_formula = _fs_que_entra(formula, 14, util_formula) if formula else 14
    fs_paso = _fs_que_entra(paso.upper(), 14.5, util, "bold")

    # 0,95 quedaba corto por dos centesimas en la lamina de fuerzas y el
    # control de abajo lo cazo. 1,02 es el presupuesto que de verdad
    # ocupan la cabecera, la franja roja y el subtitulo.
    alto_fig = (1.02 + 0.22 * (len(titulo_ls) - 1)     # título y franja
                + (0.75 if formula else 0.0)           # la fórmula
                + n_filas * alto_fila_in               # la tabla
                + alto_croquis                         # el croquis
                + n_comp * 0.34                        # la comprobación
                + n_nota * 0.20 + 0.35)                # la nota y el margen
    alto_fila = alto_fila_in / alto_fig

    fig = plt.figure(figsize=(ancho_fig, alto_fig), dpi=200)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def _f(pulgadas):
        return pulgadas / alto_fig

    # --- título y franja, como la clase --------------------------------
    y = 1.0 - _f(0.34)
    ax.text(0.035, y, paso.upper(), fontsize=fs_paso, color=AZUL,
            fontweight="bold", va="top")
    y -= _f(0.30)
    ax.add_patch(Rectangle((0.035, y), 0.30, _f(0.055), fc=ROJO, ec="none"))
    ax.plot([0.335, 0.965], [y + _f(0.028)] * 2, color=ROJO, lw=0.8,
            alpha=0.55)
    y -= _f(0.10)
    for k, ln in enumerate(titulo_ls):
        ax.text(0.035, y - _f(0.22 * k), ln, fontsize=10.5, color=AZUL_OSCURO,
                fontweight="bold", va="top")
    y -= _f(0.34 + 0.22 * (len(titulo_ls) - 1))

    # --- la fórmula, grande y con su acápite ---------------------------
    if formula:
        # centro del ESPACIO LIBRE, no de la lamina (ver el porque arriba)
        cx = 0.035 + (util_formula / ancho_fig) / 2.0
        ax.text(cx, y, formula, fontsize=fs_formula, color=TINTA,
                ha="center", va="top")
        if acapite:
            ax.text(0.965, y - _f(0.06), acapite, fontsize=9.5, color=ROJO,
                    ha="right", va="top", fontweight="bold")
        y -= _f(0.70)

    # --- el croquis del mecanismo, si la lámina lo trae ----------------
    if croquis is not None and alto_croquis > 0:
        croquis(ax, 0.035, y - _f(alto_croquis), 0.93, _f(alto_croquis))
        y -= _f(alto_croquis + 0.10)

    # --- las tablas, lado a lado ---------------------------------------
    n = len(bloques)
    # el hueco entre bloques: con dos tablas al lado, 0,028 del ancho es
    # media pulgada que ninguna de las dos tiene para regalar.
    margen, hueco = 0.035, 0.014
    ancho_total = 1.0 - 2 * margen - hueco * (n - 1)
    pesos = [len(b["cols"]) for b in bloques]
    x = margen
    y_min = y
    for b, w in zip(bloques, pesos):
        anc = ancho_total * w / float(sum(pesos))
        yy = tabla(ax, x, y, anc, alto_fila, b["cols"], b["filas"],
                   suma=b.get("suma"), titulo=b.get("titulo"),
                   resaltar=b.get("resaltar"),
                   colores_fila=b.get("colores_fila"), fs=fs)
        y_min = min(y_min, yy)
        x += anc + hueco

    # --- la comprobación, con sus números ------------------------------
    yy = y_min - _f(0.30)
    for grupo in comp_ls:
        entera = " ".join(grupo)
        ok = "CUMPLE" in entera.upper() and "NO CUMPLE" not in entera.upper()
        col = PAL.BIEN if ok else (PAL.ALERTA if "NO CUMPLE" in entera.upper()
                                   else TINTA)
        peso = ("bold" if ok or "NO CUMPLE" in entera.upper() else "normal")
        for ln in grupo:
            ax.text(0.5, yy, ln, fontsize=10.5, color=col, ha="center",
                    va="top", fontweight=peso)
            yy -= _f(0.34)

    if nota:
        yy -= _f(0.06)
        ax.text(0.035, yy, nota, fontsize=8.4, color="#55606a", va="top",
                linespacing=1.45)
        yy -= _f(0.20 * n_nota)

    # EL CONTROL DEL MOTOR: si el contenido se sale por abajo, la lámina
    # tiene texto fuera del lienzo o encima de la tabla, que es el defecto
    # que este cálculo de alto existe para evitar. Que reviente es lo
    # correcto: una lámina ilegible publicada es peor que una que no sale.
    assert yy > -0.02, (
        "la lámina %r no entra: el contenido termina en y = %.3f. Sube "
        "ancho_fig o parte la tabla en dos bloques." % (paso, yy))

    if salida:
        # EL ANCHO SE MIDE ANTES DE ESCRIBIR. La primera version guardaba y
        # despues reventaba, asi que una lamina rechazada dejaba igual su
        # PNG malo en salidas/ y el informe lo tomaba.
        bb = fig.get_tightbbox(fig.canvas.get_renderer())
        ancho_real, alto_real = bb.width, bb.height
        assert alto_real <= ALTO_MAX_LAMINA + 0.02, (
            "la lámina %r mide %.2f\" de alto. En la caja de %.2f\" Word la "
            "reduciría a %.2f y su cuerpo de 7,5 pt aterrizaría en %.1f pt, "
            "por debajo de lo que se lee impreso. Partila en dos láminas o "
            "sacale la nota, que ya está en el cuerpo del informe."
            % (paso, alto_real, ALTO_PAGINA, ALTO_PAGINA / alto_real,
               7.5 * ALTO_PAGINA / alto_real))
        assert ancho_real <= ANCHO_PAGINA + 0.02, (
            "la lámina %r mide %.2f\" de ancho y la caja de la página mide "
            "%.2f\": Word la reduciría un %.0f %% y con ella todo su tipo. "
            "Escribí los párrafos del croquis enteros (C.envolver los parte), "
            "acortá el subtítulo o bajá una columna."
            % (paso, ancho_real, ANCHO_PAGINA,
               100 * (1 - ANCHO_PAGINA / ancho_real)))
        # SIN PAD: el pad de 0,10 se sumaba a los dos lados y la lamina
        # salia 0,20" mas ancha que su lienzo, o sea siempre por encima de
        # la caja. El aire ya lo dan los margenes de 0,035 del layout.
        fig.savefig(salida, dpi=200, facecolor="white", bbox_inches="tight",
                    pad_inches=0.0)
        plt.close(fig)
        from PIL import Image
        w, h = Image.open(salida).size
        print("  %s   %.2f x %.2f pulg"
              % (os.path.basename(salida), w / 200.0, h / 200.0))
    return fig


def marco(fig, titulo, pie="", subtitulo="", fs_tit=12.5, fs_pie=8.2,
          color_tit="#1b3a57", color_pie="#55606a"):
    """Titulo y pie envueltos; devuelve (y_arriba, y_abajo) para los ejes.

    Ver el porque en el bloque de arriba: una figura del informe no tiene
    donde escribir una linea suelta que ensanche el lienzo.
    """
    ax = fig.add_axes((0, 0, 1, 1), frame_on=False)
    ax.set_axis_off()
    alto = fig.get_size_inches()[1]
    y = 1.0 - 0.28 / alto
    for ln in envolver(ax, titulo, fs_tit, 0.93, "bold"):
        fig.text(0.5, y, ln, fontsize=fs_tit, fontweight="bold",
                 color=color_tit, ha="center", va="top")
        y -= (fs_tit * 1.35 / 72.0) / alto
    if subtitulo:
        y -= 0.06 / alto
        for ln in envolver(ax, subtitulo, fs_pie + 1.0, 0.91):
            fig.text(0.055, y, ln, fontsize=fs_pie + 1.0, color=color_tit,
                     va="top")
            y -= ((fs_pie + 1.0) * 1.35 / 72.0) / alto
    y_ab = 0.16 / alto
    if pie:
        lineas = envolver(ax, pie, fs_pie, 0.91)
        paso = (fs_pie * 1.45 / 72.0) / alto
        yp = 0.14 / alto + paso * (len(lineas) - 1)
        for ln in lineas:
            fig.text(0.055, yp, ln, fontsize=fs_pie, color=color_pie,
                     va="top")
            yp -= paso
        y_ab = 0.16 / alto + paso * len(lineas)
    # los numeros del eje y su titulo van POR DEBAJO del rectangulo del eje
    y_ab += 0.50 / alto
    return y - 0.10 / alto, y_ab


def guardar(fig, ruta, dpi=200, pad=0.02):
    """Guarda una figura del informe midiendo con que cuerpo se imprimira.

    Ver el porque en el bloque de arriba. Devuelve (ancho, alto, escala).
    """
    bb = fig.get_tightbbox(fig.canvas.get_renderer())
    w, h = bb.width + 2 * pad, bb.height + 2 * pad
    esc = min(ANCHO_PAGINA / w, ALTO_PAGINA / h, 1.0)
    fig.savefig(ruta, dpi=dpi, facecolor="white", bbox_inches="tight",
                pad_inches=pad)
    plt.close(fig)
    aviso = "" if esc >= 0.87 else "   <-- por debajo de 6,5 pt"
    print("  %s   %.2f x %.2f pulg  ->  7,5 pt salen a %.1f pt%s"
          % (os.path.basename(str(ruta)), w, h, 7.5 * esc, aviso))
    return w, h, esc


def coma(x, dec=2):
    """Número con coma decimal, que es como escribe el informe."""
    return ("%.*f" % (dec, x)).replace(".", ",")


def miles(x):
    """Entero con separador de millar fino, sin punto ni coma."""
    return ("{:,.0f}".format(x)).replace(",", " ")
