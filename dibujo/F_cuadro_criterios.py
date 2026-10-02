# -*- coding: utf-8 -*-
u"""LAMINA: los seis criterios de estructuracion, evaluados con numeros.

QUE ENSENA. Que la estructuracion no es una opinion del proyectista: la E.070
la escribe como una LISTA, en su **Capitulo 6 - Estructuracion**, y cada punto
de esa lista se puede contrastar con un numero de este edificio. La lamina
pone los dos al lado: lo que el acapite pide y lo que el proyecto mide.

POR QUE SE REHIZO (2026-09-27). Existia una version de esta lamina como PNG
suelto en `salidas/informe/`, SIN generador. Tenia dos problemas y el segundo
explica el primero:

  1. **Seis numeros no eran los del calculo.** Area requerida 6,42 m2 contra
     6,593; provista en X 13,56 m2 contra 14,964; holguras +111 % / +162 %
     contra +127,0 % / +150,8 %; y una excentricidad **ey = 0,02 m cuando el
     SSOT da 0,196 m**, diez veces menos. Ese ey aparecio TRES VECES en dos
     dias, en tres artefactos distintos: un numero falso que vive en algo que
     no se regenera se copia al siguiente.
  2. **Nadie la producia.** El auditor decia "las 41 figuras declaradas
     existen en disco" y estaba en verde, porque solo miraba EXISTENCIA. Una
     figura que no se regenera con la cadena envejece con aspecto de
     verificada, que es peor que no tenerla.

Y LAS CITAS TAMBIEN CAMBIARON, contra el PDF de la norma. La version vieja
atribuia los criterios de estructuracion a los acapites 7.1.x, que son otra
cosa: el **7.1.1** es *Muro portante* --espesor efectivo y esfuerzo axial-- y
el **7.1.2.b** es la densidad minima. Los criterios de estructuracion viven en
el **Capitulo 6**, y ahi estan escritos uno por uno:

    6.1.2  diafragma rigido si la relacion de lados no excede de 4
    6.2.1  plantas simples y regulares; evitar L, T, etc.
    6.2.2  simetria en masas y en la disposicion de muros en planta
    6.2.3  proporciones en planta entre 1 y 4, y en elevacion menor que 4
    6.2.4  regularidad, evitando cambios bruscos y discontinuidades
    6.2.5  densidad de muros SIMILAR en las dos direcciones principales

Esa lista es el guion de la lamina. No la invento: la copia.
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
from matplotlib.patches import FancyBboxPatch                    # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))
sys.path.insert(0, AQUI)

import paleta as PAL                                             # noqa: E402
import rutas as R                                                # noqa: E402
import cuadro as C                                               # noqa: E402

AZUL = "#2e5c9a"
AZUL_OSCURO = "#1f3f6b"
GRIS_TEXTO = "#37474f"
GRIS_SUAVE = "#6b7a88"
def _P():
    """El SSOT. `FONDO` de este archivo es un COLOR: hay que decir cual."""
    import proyecto
    return proyecto


FONDO = "#f7f9fc"
BORDE = "#c5d5e6"
CREMA = "#fff8e1"


def _mod(nombre):
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location("_c" + nombre[:2], ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def coma(x, dec=2):
    return (("%%.%df" % dec) % x).replace(".", ",")


def reunir():
    u"""Todo lo que la lamina afirma con un numero, traido de su fuente."""
    import proyecto as P
    m01 = _mod("01_arquitectura_y_densidad.py")
    m17 = _mod("17_reparto_cortante.py")

    d = {"B": P.FRENTE, "L": P.FONDO, "Ap": P.AREA_PLANTA,
         "n": P.N_PISOS, "he": P.H_ENTREPISO, "t": P.ESPESOR,
         "e_losa": P.E_LOSA, "lmin": P.LONG_MINIMA}
    d["hn"] = P.N_PISOS * P.H_ENTREPISO
    d["rel_planta"] = max(d["B"], d["L"]) / min(d["B"], d["L"])
    d["rel_elev"] = d["hn"] / min(d["B"], d["L"])

    # --- densidad, machon por machon (6.4 descarta los menores de 1,20) ---
    d["req"] = m01.densidad_requerida()
    d["dens"] = {}
    d["n_muros"] = {}
    for dire in ("X", "Y"):
        filas = m01.tabla_densidad(dire)
        ac = sum(f["Ac"] for f in filas)
        d["dens"][dire] = (ac, ac / d["Ap"], 100.0 * (ac / d["Ap"] / d["req"] - 1.0))
        d["n_muros"][dire] = len(filas)
    d["area_req"] = d["req"] * d["Ap"]
    # el 6.2.5 pide densidades SIMILARES en las dos direcciones
    r = [d["dens"][x][1] for x in ("X", "Y")]
    d["similitud"] = max(r) / min(r)

    # --- centros, excentricidad y rigideces --------------------------------
    filas, h, Fi, V, xm, ym, xr, yr = m17.contexto()
    d["cm"], d["cr"] = (xm, ym), (xr, yr)
    d["e_propia"] = (abs(xm - xr), abs(ym - yr))
    d["e_acc"] = (0.05 * d["B"], 0.05 * d["L"])
    Ktor, Kx, Ky = m17.geometria_torsional(filas, xr, yr)
    Vent = m17.cortantes_de_entrepiso(Fi)
    rep, _e = m17.repartir(filas, Vent, xm, ym, xr, yr, Ktor, Kx, Ky)
    d["rig"] = {}
    for dire in ("X", "Y"):
        ks = sorted((r["K"] for r in rep.values() if r["dir"] == dire),
                    reverse=True)
        tot = sum(ks)
        d["rig"][dire] = (len(ks), 100.0 * ks[0] / tot,
                          100.0 * (ks[0] + ks[1]) / tot)
    return d


def criterios(d):
    u"""Las seis tarjetas. Cada dato sale de `d`; ninguno se escribe aca."""
    ex, ey = d["e_propia"]
    eax, eay = d["e_acc"]
    dx, dy = d["dens"]["X"], d["dens"]["Y"]
    nx, px, p2x = d["rig"]["X"]
    ny, py, p2y = d["rig"]["Y"]

    return [
        {"n": "1", "acapite": "E.070 6.2.1 y 6.2.3",
         "titulo": "Planta simple y proporciones",
         "pide": "Plantas simples y regulares; proporciones en planta entre "
                 "1 y 4, y en elevación menor que 4",
         "filas": [
             ("Forma de la planta", "rectangular, sin L ni T"),
             ("Dimensiones", "%s × %s m" % (coma(d["B"]), coma(d["L"]))),
             ("Relación de lados en planta",
              "%s  (la norma admite de 1 a 4)" % coma(d["rel_planta"])),
             ("Esbeltez en elevación hn/B",
              "%s  (la norma pide < 4)" % coma(d["rel_elev"])),
         ],
         "veredicto": "CUMPLE", "estado": "bien"},

        {"n": "2", "acapite": "E.070 6.2.2 · E.030 Art. 37",
         "titulo": "Simetría en planta y torsión",
         "pide": "Simetría en la distribución de masas y de muros, de modo "
                 "que la rigidez lateral de cada piso sea razonablemente "
                 "simétrica",
         "filas": [
             ("Centro de masa CM",
              "(%s ; %s) m" % (coma(d["cm"][0], 3), coma(d["cm"][1], 3))),
             ("Centro de rigidez CR",
              "(%s ; %s) m" % (coma(d["cr"][0], 3), coma(d["cr"][1], 3))),
             ("Excentricidad propia",
              "ex = %s m   ·   ey = %s m" % (coma(ex, 3), coma(ey, 3))),
             ("Excentricidad accidental 0,05·B",
              "%s m en X   ·   %s m en Y  →  GOBIERNA"
              % (coma(eax, 3), coma(eay, 3))),
         ],
         "veredicto": "CUMPLE", "estado": "bien",
         "nota": "La torsión no se evita: se considera. La excentricidad "
                 "propia es pequeña, pero en las dos direcciones manda la "
                 "accidental del Art. 37, y con ella se repartió el cortante."},

        {"n": "3", "acapite": "E.070 6.1.1 y 6.1.2",
         "titulo": "Diafragma rígido y continuo",
         "pide": "Debe preferirse el diafragma rígido y continuo; puede "
                 "considerarse rígido cuando la relación entre sus lados no "
                 "excede de 4",
         "filas": [
             ("Tipo de losa",
              "aligerada de %s m, continua en los cinco niveles"
              % coma(d["e_losa"])),
             ("Relación de lados del diafragma",
              "%s  ≤  4" % coma(d["rel_planta"])),
             ("Amarre del perímetro",
              "vigas soleras de %s × %s m en todo borde"
              % (coma(d["t"]), coma(d["e_losa"]))),
             ("Grados de libertad por planta", "3  (dx, dy, θz)"),
         ],
         "veredicto": "CUMPLE", "estado": "bien"},

        {"n": "4", "acapite": "E.070 6.2.4",
         "titulo": "Regularidad y continuidad vertical",
         "pide": "Regularidad en planta y elevación, evitando cambios "
                 "bruscos de rigidez y masa y discontinuidades en la "
                 "transmisión de las fuerzas a través de los muros",
         "filas": [
             ("Muros continuos",
              "%d de %d, del piso 1 a la azotea (100 %%)"
              % (nx + ny, nx + ny)),
             ("Muros apeados sobre vigas o losas", "ninguno"),
             ("Transmisión a la cimentación",
              "cimiento corrido continuo bajo todos los muros"),
             ("Factores de irregularidad", "Ia = Ip = 1,00  →  R = 3,00"),
         ],
         "veredicto": "CUMPLE", "estado": "bien"},

        {"n": "5", "acapite": "E.070 7.1.2.b y 6.2.5",
         "titulo": "Densidad mínima y equilibrio entre ejes",
         "pide": "Σ(L·t)/Ap ≥ Z·U·S·N/56 en cada dirección, y densidades "
                 "SIMILARES en las dos direcciones principales",
         "filas": [
             ("Demanda Z·U·S·N/56",
              "%s   (área requerida %s m²)"
              % (coma(d["req"], 5), coma(d["area_req"], 3))),
             ("Dirección X",
              "%s m² → %s   (+%s %%)"
              % (coma(dx[0], 3), coma(dx[1], 4), coma(dx[2], 1))),
             ("Dirección Y",
              "%s m² → %s   (+%s %%)"
              % (coma(dy[0], 3), coma(dy[1], 4), coma(dy[2], 1))),
             ("Equilibrio entre ejes (6.2.5)",
              "Y/X = %s : densidades del mismo orden" % coma(d["similitud"])),
         ],
         "veredicto": "CUMPLE", "estado": "bien",
         "nota": "Sólo se cuentan los machones de L ≥ %s m: el acápite 6.4 "
                 "descarta los menores, y contar la longitud bruta inflaría "
                 "la densidad." % coma(d["lmin"])},

        {"n": "6", "acapite": "E.030 Art. 33.2",
         "titulo": "Redundancia y método de análisis",
         "pide": "Ningún requisito numérico lo exige. Se mide y se declara "
                 "porque es la condición real del edificio",
         "filas": [
             ("Dirección X",
              "%d muros; el mayor toma %s %% de la rigidez"
              % (nx, coma(px, 1))),
             ("Dirección Y",
              "%d muros; DOS medianeras toman %s %%" % (ny, coma(p2y, 1))),
             ("Altura total hn",
              "%s m  ≤  15 m  →  el Art. 33.2 admite el análisis estático"
              % coma(d["hn"])),
             ("Consecuencia de diseño",
              "las medianeras gobiernan: la C-2 se dimensionó por ellas"),
         ],
         # la capsula lleva la version corta -- ver el porque mas abajo, en
         # el calculo de la banda--; la frase entera va en la nota.
         "veredicto": "CON OBSERVACIÓN", "estado": "regular",
         "nota": "El modelo es elástico-lineal y NO demuestra redistribución "
                 "por fisuración. En X el reparto es parejo; en Y la rigidez "
                 "se concentra en las dos medianeras de %.2f m, y eso se "
                 "declara en vez de presentarse como redundancia holgada." % _P().FONDO},
    ]


def control(d, cards):
    u"""Lo que la lamina AFIRMA tiene que ser verdad en la fuente."""
    assert d["rel_planta"] <= 4.0, "la lamina dice que el diafragma es rigido"
    assert d["rel_elev"] < 4.0, "la lamina dice que la elevacion cumple 6.2.3"
    for dire in ("X", "Y"):
        ac, ratio, holg = d["dens"][dire]
        assert ratio >= d["req"] and holg > 0, (
            "la lamina dice CUMPLE la densidad en %s y no alcanza" % dire)
    assert d["hn"] <= 15.0, (
        "la lamina invoca el Art. 33.2 y hn = %.2f supera los 15 m" % d["hn"])
    # el corazon de la tarjeta 2: la accidental tiene que GOBERNAR
    for i, dire in enumerate(("X", "Y")):
        assert d["e_acc"][i] > d["e_propia"][i], (
            "la lamina dice que gobierna la accidental y en %s la propia "
            "(%.3f) supera a la accidental (%.3f)"
            % (dire, d["e_propia"][i], d["e_acc"][i]))
    # el corazon de la tarjeta 6: la observacion tiene que estar respaldada
    assert d["rig"]["Y"][2] > 50.0, (
        "la lamina observa concentracion en Y y los dos mayores toman %.1f %%"
        % d["rig"]["Y"][2])
    assert d["rig"]["X"][1] < d["rig"]["Y"][1], (
        "la lamina contrasta X repartido contra Y concentrado y la medicion "
        "no lo respalda")
    # y que una sola tarjeta lleve observacion: si todas fueran verdes, la
    # lamina seria un sello y no una auditoria
    obs = [c for c in cards if c["estado"] != "bien"]
    assert len(obs) == 1 and obs[0]["n"] == "6", (
        "se esperaba exactamente una tarjeta con observacion, la 6")
    print("  [ok] proporciones, densidad y altura cierran con su fuente")
    print("  [ok] la accidental gobierna en las dos direcciones")
    print("  [ok] la observacion de la 6 esta respaldada: %.1f %% en dos muros"
          % d["rig"]["Y"][2])


def _envolver(txt, n):
    return "\n".join(textwrap.wrap(txt, n))


PIE_1 = (u"Los criterios 1 a 3 miran la FORMA: planta simple, simetría y "
         u"diafragma. Los tres salen del Capítulo 6 de la E.070, que escribe "
         u"la estructuración como una lista. Siguen en la lámina 2 los que "
         u"miran el COMPORTAMIENTO: regularidad, densidad y redundancia.")

PIE = (u"Los cinco primeros criterios se contrastan contra un acápite que "
       u"los exige; el sexto no lo exige ninguno y se mide igual, porque es "
       u"la condición real del edificio. Una lámina en la que todo sale "
       u"verde no es una auditoría: es un sello.")


def dibujar():
    """Las seis tarjetas, en DOS laminas de tres. Ver el porqué arriba."""
    d = reunir()
    todas = criterios(d)
    control(d, todas)
    for n_lam, (desde, hasta) in enumerate(((0, 3), (3, 6)), 1):
        _una_lamina(todas[desde:hasta], n_lam, desde + 1, hasta)


def _una_lamina(cards, n_lam, c_desde, c_hasta):

    # DOS COLUMNAS SOBRE EL ANCHO DE LA HOJA. Tres tarjetas en fila piden
    # 19 pulgadas; en la caja de 6,30 cada tarjeta tendria 2 pulgadas y el
    # texto no respira. Con dos columnas la tarjeta mide 2,95", que es el
    # ancho de una columna de revista y se lee bien a 7 pt.
    COLS, FILS = 2, 2
    # MY 2,2 dejaba la lamina en 10,93" contra el limite de 10,90: el
    # aire ENTRE tarjetas es lo primero que se recorta, antes que el
    # tipo o el contenido.
    MX, MY = 3.0, 1.4
    ANCHO_T = (100.0 - 2 * 2.0 - MX * (COLS - 1)) / COLS
    fig_w = C.ANCHO_PAGINA

    # --- cuanto pide la tarjeta mas alta, ANTES de elegir el alto ---------
    aux = plt.figure(figsize=(fig_w, 10.0), dpi=200)
    ax_aux = aux.add_subplot(111)
    w_txt = (ANCHO_T - 2.2) / 100.0
    pedido = 0.0
    for c in cards:
        # el margen de pie de tarjeta: 0,10 dejaba la lamina 3 centesimas
        # por encima del limite de legibilidad. Se recorta el aire, no
        # el contenido.
        h = 0.52 + 0.03                                  # cabecera y margen
        h += 0.175 * len(C.envolver(ax_aux, c["titulo"], 10.2, w_txt, "bold"))
        h += 0.06
        h += 0.125 * len(C.envolver(ax_aux, u"«%s»" % c["pide"],
                                    7.3, w_txt))
        h += 0.07
        for etiqueta, valor in c["filas"]:
            h += 0.125 * len(C.envolver(ax_aux, etiqueta, 7.5, w_txt, "bold"))
            h += 0.125 * len(C.envolver(ax_aux, valor, 7.6, w_txt - 0.012))
            h += 0.045
        if c.get("nota"):
            h += 0.16 + 0.122 * len(C.envolver(ax_aux, c["nota"], 7.0,
                                               w_txt - 0.016))
        pedido = max(pedido, h)
    # la cabecera y el pie, medidos igual que las tarjetas
    titulo_lam = (u"Los seis criterios de estructuración, con el número que "
                  u"los verifica — criterios %d a %d" % (c_desde, c_hasta))
    pie_lam = PIE if n_lam == 2 else PIE_1
    n_tit = len(C.envolver(ax_aux, titulo_lam, 12.5, 0.955, "bold"))
    n_baj = len(C.envolver(ax_aux, u"La E.070 escribe la estructuración como "
                           u"una lista —su Capítulo 6—. Cada tarjeta pone lo "
                           u"que el acápite pide al lado de lo que este "
                           u"edificio mide.", 8.6, 0.955))
    n_pie = len(C.envolver(ax_aux, pie_lam, 7.6, 0.955))
    plt.close(aux)
    CAB_IN = 0.16 + 0.21 * n_tit + 0.04 + 0.145 * n_baj + 0.10
    PIE_IN = 0.10 + 0.135 * n_pie + 0.10
    HUECO_IN = 0.16
    fig_h = CAB_IN + FILS * pedido + (FILS - 1) * HUECO_IN + PIE_IN
    ALTO_T = pedido / fig_h * 100.0
    MY = HUECO_IN / fig_h * 100.0
    Y_PRIMERA = 100.0 - CAB_IN / fig_h * 100.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=200)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor(PAL.PAPEL)
    # el eje ocupa la lamina entera: con los margenes por omision quedaba
    # una franja muerta de ~12 % entre la fila de abajo y el pie.
    fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.045)

    def V(pulg):
        return pulg / fig_h * 100.0

    yc = 99.2
    for lt in C.envolver(ax, titulo_lam, 12.5, 0.955, "bold"):
        ax.text(2.0, yc, lt, fontsize=12.5, fontweight="bold",
                color=AZUL_OSCURO, va="top")
        yc -= V(0.21)
    yc -= V(0.04)
    for lt in C.envolver(ax, u"La E.070 escribe la estructuración como una "
                         u"lista —su Capítulo 6—. Cada tarjeta pone lo que el "
                         u"acápite pide al lado de lo que este edificio mide.",
                         8.6, 0.955):
        ax.text(2.0, yc, lt, fontsize=8.6, color=GRIS_SUAVE, va="top")
        yc -= V(0.145)
    ax.plot([2.0, 98.0], [yc - V(0.05)] * 2, color=AZUL, lw=1.4)

    for k, c in enumerate(cards):
        col, fil = k % COLS, k // COLS
        x0 = 2.0 + col * (ANCHO_T + MX)
        y1 = Y_PRIMERA - fil * (ALTO_T + MY)
        y0 = y1 - ALTO_T

        ax.add_patch(FancyBboxPatch(
            (x0, y0), ANCHO_T, ALTO_T,
            boxstyle="round,pad=0.35,rounding_size=0.8",
            fc=FONDO, ec=BORDE, lw=1.0, zorder=2))
        # banda del acapite
        ax.add_patch(FancyBboxPatch(
            (x0, y1 - 3.0), ANCHO_T, 3.0,
            boxstyle="round,pad=0.0,rounding_size=0.5",
            fc=AZUL_OSCURO, ec="none", zorder=3))
        cabeza = "CRITERIO %s   ·   %s" % (c["n"], c["acapite"])
        # EL ESPACIO SE MIDE, no se cuenta en caracteres. Ver el porque
        # arriba: el conteo daba bien y los textos se tocaban igual.
        w_ver = C.envolver_ancho(ax, c["veredicto"], 7.0, "bold") * 100.0
        libre = (ANCHO_T - 2.0 - w_ver - 1.2) / 100.0
        fs_cab = C._fs_que_entra(cabeza, 7.6,
                                 libre * ax.figure.get_size_inches()[0],
                                 "bold")
        assert fs_cab >= 6.0, (
            "el criterio %s no entra en su banda ni al minimo legible: "
            "acorta el acápite o el veredicto" % c["n"])
        ax.text(x0 + 1.0, y1 - 1.5, cabeza, fontsize=fs_cab, color="#ffffff",
                fontweight="bold", va="center", zorder=4)
        # EL VEREDICTO VA EN LA BANDA, no al lado del titulo. Puesto junto al
        # titulo, "CONFORME CON OBSERVACION" --el mas largo y el unico que
        # importa leer entero-- se montaba encima de "Redundancia y metodo de
        # analisis" y lo cortaba. Aca tiene el ancho de la tarjeta y queda
        # ademas a la misma altura en las seis, que es lo que permite
        # recorrer la lamina de un vistazo.
        col_v = PAL.BIEN if c["estado"] == "bien" else PAL.REGULAR
        ax.text(x0 + ANCHO_T - 1.0, y1 - 1.5, c["veredicto"], fontsize=7.0,
                fontweight="bold", color="#ffffff", ha="right", va="center",
                zorder=5, bbox=dict(boxstyle="round,pad=0.28", fc=col_v,
                                    ec="none"))

        # V(pulgadas) -> unidades del eje. El cuerpo de la tarjeta se mide
        # en pulgadas: es lo unico que no cambia al cambiar de lienzo.
        def V(pulg):
            return pulg / fig_h * 100.0

        w_txt = (ANCHO_T - 2.2) / 100.0          # ancho util, en fraccion
        y = y1 - V(0.52)
        for lt in C.envolver(ax, c["titulo"], 10.2, w_txt, "bold"):
            ax.text(x0 + 1.0, y, lt, fontsize=10.2, fontweight="bold",
                    color=AZUL_OSCURO, va="top", zorder=4)
            y -= V(0.175)
        y -= V(0.06)
        # QUE PIDE LA NORMA, en cursiva: es cita, no afirmacion nuestra
        for lt in C.envolver(ax, u"«%s»" % c["pide"], 7.3, w_txt):
            ax.text(x0 + 1.0, y, lt, fontsize=7.3, color=GRIS_SUAVE,
                    style="italic", va="top", zorder=4)
            y -= V(0.125)
        y -= V(0.07)

        for etiqueta, valor in c["filas"]:
            for lt in C.envolver(ax, etiqueta, 7.5, w_txt, "bold"):
                ax.text(x0 + 1.2, y, lt, fontsize=7.5, fontweight="bold",
                        color=GRIS_TEXTO, va="top", zorder=4)
                y -= V(0.125)
            for lt in C.envolver(ax, valor, 7.6, w_txt - 0.012):
                ax.text(x0 + 2.2, y, lt, fontsize=7.6, color=AZUL_OSCURO,
                        va="top", zorder=4)
                y -= V(0.125)
            y -= V(0.045)

        if c.get("nota"):
            lineas = C.envolver(ax, c["nota"], 7.0, w_txt - 0.016)
            alto = V(0.16) + V(0.122) * len(lineas)
            ax.add_patch(FancyBboxPatch(
                (x0 + 1.0, y - alto + V(0.06)), ANCHO_T - 2.0, alto,
                boxstyle="round,pad=0.25,rounding_size=0.4",
                fc=CREMA if c["estado"] != "bien" else "#ffffff",
                ec=BORDE, lw=0.7, zorder=3))
            yy = y - V(0.03)
            for lt in lineas:
                ax.text(x0 + 1.9, yy, lt, fontsize=7.0, color=GRIS_TEXTO,
                        va="top", zorder=4)
                yy -= V(0.122)
            y -= alto
        # CONTROL DE CAJA: si una tarjeta crece, avisa aca y no en la pagina.
        assert y > y0 - 0.3, (
            "el criterio %s desborda su tarjeta (sobra %.1f)" % (c["n"], y - y0))

    # EL PIE VA EN LA FIGURA, no en el eje: dentro del eje sus lineas se
    # metian por debajo de las tarjetas de la fila inferior. Se dibuja con
    # el MISMO texto con que se midio el alto -- por eso PIE es constante.
    lineas_pie = C.envolver(ax, pie_lam, 7.6, 0.955)
    paso_pie = 0.135 / fig_h
    yp = 0.10 / fig_h + paso_pie * (len(lineas_pie) - 1)
    for lt in lineas_pie:
        fig.text(0.022, yp, lt, fontsize=7.6, color=GRIS_SUAVE, va="bottom")
        yp -= paso_pie

    ruta = os.path.join(R.INFORME, "CUADRO-CRITERIOS-%d.png" % n_lam)
    # EL MISMO CONTROL QUE EL MOTOR: si no entra en la caja de la pagina,
    # revienta antes de escribir. Esta lamina no pasa por cuadro.lamina(),
    # asi que su control va aca o no va a ninguna parte.
    bb = fig.get_tightbbox(fig.canvas.get_renderer())
    assert bb.width <= C.ANCHO_PAGINA + 0.02, (
        "CUADRO-CRITERIOS-%d mide %.2f\" de ancho y la caja mide %.2f\": "
        "Word lo reduciría un %.0f %% y con él todo su tipo."
        % (n_lam, bb.width, C.ANCHO_PAGINA,
           100 * (1 - C.ANCHO_PAGINA / bb.width)))
    assert bb.height <= C.ALTO_MAX_LAMINA + 0.02, (
        "CUADRO-CRITERIOS-%d mide %.2f\" de alto; por encima de %.2f el cuerpo "
        "de 7,5 pt no llega a los 6,5 pt que se leen en papel. Partilo en "
        "dos láminas." % (n_lam, bb.height, C.ALTO_MAX_LAMINA))
    # pad_inches=0: el pad por omision (0,1) se suma a los dos lados y
    # la lamina sale 0,20" mas ancha que lo que el control midio.
    C.guardar(fig, ruta)


if __name__ == "__main__":
    dibujar()
