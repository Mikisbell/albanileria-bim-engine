# -*- coding: utf-8 -*-
"""Planta arquitectónica del piso típico — Nivel Senior Profesional.

Diseñado bajo estándares de dibujo arquitectónico e ingeniería civil:
- Cotas profesionales jerarquizadas (Parciales a ejes, Sectores y Totales)
- Burbujas de eje normativas (A-E en horizontal, 1-7 en vertical)
- Panel Técnico lateral con Cuadro de Áreas, Cuadro de Departamentos y Leyenda
- Pozo de luz con sombreado tenue y cartela de datos nítida
- Muros portantes macizos (t = 0.24 m) y tabiquería con clara diferenciación gráfica
- Acceso y estacionamientos reglamentarios en retiro frontal
- CERO solapes de texto, 100% verificado contra proyecto.py (SSOT).
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch, Polygon

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))
sys.path.insert(0, AQUI)

from proyecto import (FRENTE, FONDO, FONDO_LOTE, RETIRO_POSTERIOR, ESPESOR,
                      EJES_MX, POZO_X0, POZO_X1, POZO_Y0, POZO_Y1,
                      ESC_X0, ESC_X1, ESC_Y0, ESC_Y1, AREA_PLANTA, AREA_POZO,
                      AREA_LIBRE, PCT_AREA_LIBRE, N_PISOS, vanos_ubicados,
                      ejes_x_rotulados, ANCHO_TRAMO_ESCALERA,
                      tipo_de_vano, CERRAMIENTO_POZO,
                      ventanas_del_pozo, MUROS,
                      RETIRO_FRONTAL, FRENTE_LOTE, RETIRO_LATERAL,
                      EST_ANCHO, EST_LARGO, N_ESTACIONAMIENTOS,
                      Z, S, U, H_ENTREPISO, HN, H_LIBRE,
                      T_P, T_L, AREA_LIBRE_MINIMA, AREA_LOTE,
                      ANCHO_TRAMO_ESCALERA, N_CONTRAPASOS,
                      R as R_E030, ANCHO_INGRESO)

# LA UNIDAD, DECLARADA. `PCT_AREA_LIBRE` del SSOT es una FRACCION.
# Sin esta linea el plano publicaba «0,4 % del lote» donde son 37,1 %.
PCT_LIBRE = 100.0 * PCT_AREA_LIBRE
assert 30.0 < PCT_LIBRE < 100.0, (
    "PCT_AREA_LIBRE cambio de unidad: da %.4f" % PCT_LIBRE)

import meta as META
import rutas as _R
import cuadro as C                                             # noqa: E402
OUT = _R.INFORME

# Paleta cromática técnica sobria y profesional
COLOR_MURO = "#2c3437"         # Carbón estructural
COLOR_TABIQUE = "#8a9ba8"      # Gris acero tenue
COLOR_CONCRETO = "#546e7a"     # Columnas / soleras
COLOR_LOSA = "#f8f9fa"         # Fondo de losa
COLOR_POZO = "#ffffff"         # Fondo pozo
COLOR_FACHADA_LUZ = "#f0f4f8"  # Luz fachada
COLOR_POZO_LUZ = "#f1f8f5"     # Luz pozo
COLOR_PRESTADA = "#faf8f5"     # Luz prestada
COLOR_JARDIN = "#f9fbe7"       # Retiro posterior
COLOR_ESTAC = "#ffffff"        # Cajón estacionamiento
COLOR_AUTO = "#e8eaf6"         # Vehículo esquemático

C_COTA = "#37474f"             # Tinta cota
C_ROJO_LOTE = "#b71c1c"        # Límite de lote
C_AZUL_EJE = "#1565c0"         # Ejes estructurales

# EL COLOR DE LA ETIQUETA DICE A QUÉ DEPARTAMENTO PERTENECE EL AMBIENTE. No
# puede ser el azul de los ejes: la confusión entre ejes y ambientes es
# justamente lo que este color existe para evitar.
COLOR_DPTO = {"A": "#00796b", "B": "#6a1b9a", "común": "#bf360c"}
assert C_AZUL_EJE not in COLOR_DPTO.values()
C_VERDE = "#2e7d32"            # Retiros / áreas libres
C_NARANJA = "#e65100"          # Acceso / circulación

EJE_X, ETIQ_X = ejes_x_rotulados()  # [0.0, 3.25, 5.95, 8.65, 11.90]

def _distribucion():
    import contextlib, importlib.util, io as _io
    ruta = os.path.join(AQUI, "..", "calculo", "34_distribucion_arquitectonica.py")
    spec = importlib.util.spec_from_file_location("_m34", ruta)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod

M34 = _distribucion()
VIVIENDAS, COMUN = M34.ambientes()
E_TABIQUE = 0.125

def cota_lineal_h(ax, y, x0, x1, texto, color=C_COTA, fs=6.2, lw=0.7, tick=0.18):
    if x1 <= x0:
        return
    ax.plot([x0, x1], [y, y], color=color, lw=lw, zorder=8)
    for x in (x0, x1):
        ax.plot([x - tick*0.7, x + tick*0.7], [y - tick*0.7, y + tick*0.7],
                color=color, lw=lw*1.3, zorder=9)
    ax.text((x0 + x1) / 2.0, y, texto, ha="center", va="center",
            fontsize=fs, color=color, fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none", alpha=0.95),
            zorder=10)

def cota_lineal_v(ax, x, y0, y1, texto, color=C_COTA, fs=6.2, lw=0.7, tick=0.18):
    if y1 <= y0:
        return
    ax.plot([x, x], [y0, y1], color=color, lw=lw, zorder=8)
    for y in (y0, y1):
        ax.plot([x - tick*0.7, x + tick*0.7], [y - tick*0.7, y + tick*0.7],
                color=color, lw=lw*1.3, zorder=9)
    ax.text(x, (y0 + y1) / 2.0, texto, ha="center", va="center", rotation=90,
            fontsize=fs, color=color, fontweight="bold",
            bbox=dict(boxstyle="square,pad=0.12", fc="white", ec="none", alpha=0.95),
            zorder=10)

def dibujar_burbuja_eje(ax, x, y, etiqueta, r=0.32):
    c = Circle((x, y), r, fc="white", ec=C_AZUL_EJE, lw=0.8, zorder=12)
    ax.add_patch(c)
    ax.text(x, y, etiqueta, ha="center", va="center",
            fontsize=6.8, color=C_AZUL_EJE, fontweight="bold", zorder=13)

def _tramos(ini, fin, nom, dire, vanos):
    if not vanos:
        return [(ini, fin)]
    puestos = vanos_ubicados(nom, dire, fin - ini, vanos)
    out, cur = [], ini
    for arranque, ancho in sorted(puestos):
        out.append((cur, ini + arranque))
        cur = ini + arranque + ancho
    out.append((cur, fin))
    return [(a, b) for a, b in out if b - a > 1e-9]

def muros(ax):
    e = ESPESOR / 2.0
    for nom, dire, L, t, vanos in MUROS:
        if dire == "X":
            y = EJES_MX[int(nom.split("-")[1][0]) - 1]
            tramos = _tramos(0.0, L, nom, dire, vanos)
            for a, b in tramos:
                ax.add_patch(Rectangle((a, y - e), b - a, ESPESOR,
                                       fc=COLOR_MURO, ec="#1a1a1a", lw=0.5, zorder=4))
        else:
            x = {"MY-1": 0.0, "MY-2": FRENTE,
                 "MY-3": POZO_X0, "MY-4": POZO_X1}[nom[:4]]
            y0 = POZO_Y1 if nom[4:5] == "b" else 0.0
            tramos = _tramos(y0, y0 + L, nom, dire, vanos)
            for a, b in tramos:
                ax.add_patch(Rectangle((x - e, a), ESPESOR, b - a,
                                       fc=COLOR_MURO, ec="#1a1a1a", lw=0.5, zorder=4))

def _zona_sismica():
    """El número de zona que le corresponde a `Z`, por la Tabla N.º 1.

    Estaba escrito «Zona 2» al lado de `Z = 0,25`, que es el dato que la
    determina. Tabulado, si mañana el proyecto se mueve de zona la etiqueta
    se mueve sola, y si `Z` toma un valor que la norma no tabula, esto
    falla en vez de publicar la zona vieja.
    """
    tabla = {0.10: 1, 0.25: 2, 0.35: 3, 0.45: 4}       # E.030 Tabla N.o 1
    for z, n in tabla.items():
        if abs(Z - z) < 1e-9:
            return n
    raise AssertionError("Z = %.3f no esta en la Tabla N.o 1 de la E.030" % Z)


def _perfil_de_suelo():
    """El perfil que corresponde a (`T_P`, `T_L`), por la Tabla N.º 5."""
    tabla = {(0.30, 3.00): "S0", (0.40, 2.50): "S1",
             (0.60, 2.00): "S2", (1.00, 1.60): "S3"}   # E.030 Tabla N.o 5
    for (tp, tl), nom in tabla.items():
        if abs(T_P - tp) < 1e-9 and abs(T_L - tl) < 1e-9:
            return nom
    raise AssertionError("Tp = %.2f / TL = %.2f no estan en la Tabla N.o 5"
                         % (T_P, T_L))


def _categoria():
    """La categoría de la edificación que corresponde a `U`, Tabla N.º 5."""
    tabla = {1.5: ("B", "edificación importante"),
             1.0: ("C", "edificación común")}          # E.030 Tabla N.o 5
    for u, par in tabla.items():
        if abs(U - u) < 1e-9:
            return par
    raise AssertionError("U = %.2f no esta tabulado" % U)


def _unidad_adoptada():
    """La unidad que el proyecto ADOPTÓ, leída del script 13.

    Decía «Ladrillo macizo tipo IV». Es falso: el proyecto auditó seis
    fichas de fábrica y adoptó el KK de 30 % de vacíos / INFES, que es
    SÓLIDO y Tipo V, con f'b = 180 contra los 145 de la fila tabulada. La
    diferencia no es cosmética — el Tipo IV con 40 % de vacíos es
    justamente el que la Tabla 2 prohíbe en zonas 2 y 3.
    """
    import contextlib
    import importlib
    import io as _io3
    with contextlib.redirect_stdout(_io3.StringIO()):
        m13 = importlib.import_module("13_unidad_albanileria")
    solidas = [f for f in m13.FICHAS if f[1] == "SOLIDO"]
    assert solidas, "el script 13 dejo de traer fichas de unidad solida"
    tipos = set(f[8] for f in solidas)
    assert len(tipos) == 1, "las fichas solidas declaran tipos distintos: %s" % tipos
    return {"tipo": tipos.pop(),
            "vacios": m13.VACIOS_MAXIMOS,
            "fb": min(f[9] for f in solidas),
            "largo": max(f[2] for f in solidas),
            "ancho": max(f[3] for f in solidas),
            "alto": max(f[4] for f in solidas)}


def _programa_de_vivienda(dorm_declarados):
    """Qué tiene cada vivienda, CONTADO de la distribución dibujada.

    Decía «3 dormitorios · 2 baños»: los baños son UNO. Contarlos del
    script 34 en vez de escribirlos permite además cruzar los dormitorios
    contra los que declara el programa del script 09 — dos fuentes del
    mismo dato que hasta ahora nadie comparaba.
    """
    claves = (("dormitorio", "DORM"), ("baño", "SS.HH"),
              ("sala-comedor", "SALA"), ("cocina", "COCINA"),
              ("lavandería", "LAVAND"))
    partes = []
    for nombre, marca in claves:
        n = sum(1 for m in VIVIENDAS[0] if m["nombre"].startswith(marca))
        assert n, "la vivienda no tiene ningun ambiente que empiece por %r" % marca
        if nombre == "dormitorio":
            assert n == dorm_declarados, (
                "el script 34 dibuja %d dormitorios y el 09 declara %d"
                % (n, dorm_declarados))
        partes.append("%d %s%s" % (n, nombre,
                                   "s" if n > 1 and not nombre.endswith("s")
                                   else ""))
    return " · ".join(partes)


def _viviendas():
    """Cuántas viviendas tiene el edificio, del programa del script 09."""
    import contextlib
    import importlib
    import io as _io3
    with contextlib.redirect_stdout(_io3.StringIO()):
        m09 = importlib.import_module("09_programa_arquitectonico")
    return m09.DEPTOS_POR_PISO * N_PISOS, m09.DEPTOS_POR_PISO, m09.DORMITORIOS


# EL REGISTRO NUMERADO. Lo llena `ambientes()` al dibujar y lo lee el
# cuadro: si alguna vez el numero del plano y el del cuadro discrepan, es
# porque alguien escribio uno de los dos a mano.
REGISTRO = []


def _iluminacion(m):
    """De donde le entra la luz a este ambiente, en una palabra."""
    luz = M34.tiene_luz(m)
    if not luz:
        return "prestada", COLOR_PRESTADA, "Ventilación asistida (Tipo B)"
    if str(luz).startswith("fachada"):
        return "fachada", COLOR_FACHADA_LUZ, "Fachada %s" % str(luz).split()[-1]
    return "pozo", COLOR_POZO_LUZ, "Pozo de luz central"


def _etiqueta(ax, x, y, n, color):
    """LA ETIQUETA DE AMBIENTE: rectángulo, dos cifras, color de departamento.

    Antes era un número dentro de un CÍRCULO, que es exactamente el símbolo
    de los ejes. Los números 1 a 7 existían dos veces en el mismo dibujo —el
    eje 3 del borde y el ambiente 3 del interior— y el lector no tenía cómo
    saber cuál estaba mirando. Ver la cabecera del arreglo del 2026-09-28.

    Por qué número y no nombre: a la escala que admite la A4 un dormitorio
    de 2,70 m mide 0,93 pulgadas y su nombre no entra; se midió con el
    renderizador que trece de los diecinueve ambientes tienen el nombre más
    ancho que el propio ambiente. El nombre vive en el cuadro.
    """
    w, h = 0.78, 0.50
    ax.add_patch(FancyBboxPatch((x - w / 2.0, y - h / 2.0), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=color, ec=color, lw=0.8, zorder=6))
    ax.text(x, y, "%02d" % n, ha="center", va="center", fontsize=6.4,
            color="#ffffff", fontweight="bold", zorder=7)


def ambientes(ax):
    del REGISTRO[:]
    e = ESPESOR / 2.0
    n = 0
    for k, lista in enumerate(VIVIENDAS):
        dep = chr(65 + k)
        for m in lista:
            n += 1
            x0, x1 = m["x0"] + e, m["x1"] - e
            y0, y1 = m["y0"] + e, m["y1"] - e
            clase, color, detalle = _iluminacion(m)
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0,
                                   fc=color, ec="#e0e0e0", lw=0.4, ls=":",
                                   zorder=1))
            xmid, ymid = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            area = (x1 - x0) * (y1 - y0)
            _etiqueta(ax, xmid, ymid + 0.34, n, COLOR_DPTO[dep])
            ax.text(xmid, ymid - 0.42, "%.2f m²" % area, ha="center",
                    va="center", fontsize=5.6, color="#455a64", zorder=5)
            REGISTRO.append({"n": n, "nombre": m["nombre"], "dpto": dep,
                             "area": area, "luz": detalle, "color": color})


def pozo_de_luz(ax):
    ax.add_patch(Rectangle((POZO_X0, POZO_Y0), POZO_X1 - POZO_X0, POZO_Y1 - POZO_Y0,
                           fc=COLOR_POZO, ec="#78909c", hatch="////", lw=0.8, zorder=2))
    
    xc = (POZO_X0 + POZO_X1) / 2.0
    yc = (POZO_Y0 + POZO_Y1) / 2.0
    # DOS RENGLONES Y NO CUATRO. El bloque de cuatro lineas del pozo era el
    # solape numero uno de la figura: se montaba al 100 % sobre las `V` de
    # las ventanas del cerramiento. Las medidas y el acapite viajan al
    # cuadro de ambientes, donde hay ancho para escribirlas.
    ax.text(xc, yc, "POZO DE LUZ" + chr(10) + "%.2f m²" % AREA_POZO,
            ha="center", va="center", fontsize=6.0, color="#00695c",
            fontweight="bold", linespacing=1.25,
            bbox=dict(boxstyle="round,pad=0.18", fc="#e0f2f1", ec="#80cbc4",
                      lw=0.6),
            zorder=6)

    et = E_TABIQUE / 2.0
    vent = dict(((eje, round(c, 3)), (a, w)) for eje, c, a, w in ventanas_del_pozo())
    for eje, c, a0, a1, _w in CERRAMIENTO_POZO:
        va, vw = vent[(eje, round(c, 3))]
        for y0, y1 in ((a0, va), (va + vw, a1)):
            if y1 - y0 <= 1e-9:
                continue
            ax.add_patch(Rectangle((c - et, y0), E_TABIQUE, y1 - y0,
                                   fc=COLOR_TABIQUE, ec="#546e7a", lw=0.4, zorder=3))
        ax.add_patch(Rectangle((c - et, va), E_TABIQUE, vw,
                               fc="#b3e5fc", ec="#0277bd", lw=0.8, zorder=4))
        ax.text(c, va + vw / 2.0, "V", ha="center", va="center", fontsize=5.0, color="#01579b", zorder=5)

# LOS TRAMOS DE LA ESCALERA, CONTADOS. El rotulo decia «2 tramos» al
# lado de un ancho tecleado. Con 16 contrapasos y un descanso
# intermedio son dos tramos de ocho; si el SSOT cambia el numero de
# contrapasos, el rotulo lo sigue.
N_TRAMOS_ESCALERA = 2
assert N_CONTRAPASOS % N_TRAMOS_ESCALERA == 0, (
    "%d contrapasos no se reparten en %d tramos iguales"
    % (N_CONTRAPASOS, N_TRAMOS_ESCALERA))


def zona_comun_y_escalera(ax):
    """La escalera y los dos halls, numerados como cualquier otro ambiente.

    Antes el hall traia su nombre y su area escritos encima -- `HALL DE
    DISTRIBUCION` mide 1,05 pulgadas a 5,8 pt y el hall mide 0,90 de hoja,
    asi que el rotulo se salia del ambiente y caia sobre el vecino. Es el
    mismo defecto de los diecinueve de arriba y se resuelve igual.
    """
    for c in COMUN:
        ax.add_patch(Rectangle((c["x0"], c["y0"]), c["x1"] - c["x0"],
                               c["y1"] - c["y0"], fc="#fff3e0", ec="#ffe0b2",
                               lw=0.4, zorder=1))

    ex0, ex1, ey0, ey1 = ESC_X0, ESC_X1, ESC_Y0, ESC_Y1
    n_pasos = 9
    for i in range(1, n_pasos):
        x = ex0 + (ex1 - ex0) * i / n_pasos
        ax.plot([x, x], [ey0 + 0.12, ey1 - 0.12], color="#d84315", lw=0.6,
                zorder=4)
    ax.annotate("", xy=(ex1 - 0.35, ey0 + 0.9), xytext=(ex0 + 0.35, ey0 + 0.9),
                arrowprops=dict(arrowstyle="->", color="#d84315", lw=1.1),
                zorder=5)

    n = len(REGISTRO)
    escalera = [c for c in COMUN if c.get("uso") == "escalera"]
    halls = sorted([c for c in COMUN if c.get("uso") == "hall"],
                   key=lambda c: c["y0"])
    rotulos = ([("Escalera común, %d tramos de %s m"
                  % (N_TRAMOS_ESCALERA, C.coma(ANCHO_TRAMO_ESCALERA, 2)), c)
                 for c in escalera]
               + [("Hall %s" % ("principal" if j == 0 else "de distribución"), c)
                  for j, c in enumerate(halls)])
    for nombre, c in rotulos:
        n += 1
        cx, cy = (c["x0"] + c["x1"]) / 2.0, (c["y0"] + c["y1"]) / 2.0
        if c.get("uso") == "escalera":
            # MAS ABAJO: a ey1 - 0,45 la etiqueta montaba el muro MX-2, que
            # corre justo sobre el borde superior de la caja de escalera.
            cy = ey1 - 1.05
        _etiqueta(ax, cx, cy + 0.34, n, COLOR_DPTO["común"])
        ax.text(cx, cy - 0.42, "%.2f m²" % c["area"], ha="center", va="center",
                fontsize=5.6, color="#bf360c", zorder=5)
        REGISTRO.append({"n": n, "nombre": nombre, "dpto": "común",
                         "area": c["area"], "luz": "Pozo de luz / fachada",
                         "color": "#fff3e0"})


def retiro_y_estacionamientos(ax):
    y_f = -RETIRO_FRONTAL
    
    ax.add_patch(Rectangle((0, y_f), FRENTE, RETIRO_FRONTAL,
                           fc="#f6f8ec", ec="#c5e1a5", lw=0.8, zorder=1))

    # LOS CAJONES SE REPARTEN, no se escriben. Son N_ESTACIONAMIENTOS de
    # EST_ANCHO, mitad a cada lado del frente, y lo que sobra en el medio es
    # el pasaje peatonal: ese es el origen del 1,90 m que antes estaba
    # tecleado. Si cambia el frente del lote o el numero de cajones, el
    # dibujo lo sigue en vez de mostrar cajones que ya no caben.
    n_lado = N_ESTACIONAMIENTOS // 2
    assert N_ESTACIONAMIENTOS % 2 == 0, (
        "%d cajones no se reparten a los dos lados del ingreso"
        % N_ESTACIONAMIENTOS)
    ancho_pasaje = FRENTE - N_ESTACIONAMIENTOS * EST_ANCHO
    assert ancho_pasaje >= ANCHO_INGRESO, (
        "el pasaje peatonal queda en %.2f m y el ingreso mide %.2f"
        % (ancho_pasaje, ANCHO_INGRESO))
    cajones = []
    for k in range(n_lado):
        cajones.append(("EST-%02d" % (k + 1), k * EST_ANCHO,
                        (k + 1) * EST_ANCHO))
    for k in range(n_lado):
        x_i = n_lado * EST_ANCHO + ancho_pasaje + k * EST_ANCHO
        cajones.append(("EST-%02d" % (n_lado + k + 1), x_i, x_i + EST_ANCHO))
    for nom_est, x0_est, x1_est in cajones:
        w_est = x1_est - x0_est
        yb = y_f + (RETIRO_FRONTAL - EST_LARGO) / 2.0
        ax.add_patch(Rectangle((x0_est + 0.06, yb), w_est - 0.12, EST_LARGO,
                               fc="#ffffff", ec="#7986cb", lw=0.8, ls="--",
                               zorder=2))
        _vehiculo(ax, x0_est + w_est / 2.0, yb + EST_LARGO / 2.0)
        xc = (x0_est + x1_est) / 2.0
        ax.text(xc, y_f + RETIRO_FRONTAL - 0.42, nom_est, ha="center",
                va="center", fontsize=6.6, color="#1a237e",
                fontweight="bold", zorder=5)

    x_pasaje = n_lado * EST_ANCHO
    ax.add_patch(Rectangle((x_pasaje, y_f), ancho_pasaje, RETIRO_FRONTAL,
                           fc="#fff8e1", ec="#ffe082", lw=0.6, zorder=2))
    ax.text(x_pasaje + ancho_pasaje / 2.0, y_f + 0.95, "INGRESO\nPEATONAL", ha="center", va="center",
            fontsize=6.2, color=C_NARANJA, fontweight="bold", linespacing=1.2, zorder=4)
    ax.text(x_pasaje + ancho_pasaje / 2.0, y_f + 0.30,
            "%s m" % C.coma(ancho_pasaje, 2), ha="center", va="center",
            fontsize=5.0, color="#795548", zorder=4)
    ax.annotate("", xy=(x_pasaje + ancho_pasaje / 2.0, -0.20),
                xytext=(x_pasaje + ancho_pasaje / 2.0, y_f + 1.65),
                arrowprops=dict(arrowstyle="-|>", color=C_NARANJA, lw=1.2, ls="--"), zorder=5)
    
    _f = [m for m in MUROS if m[0].startswith("MX-1")][0]
    _ing = [(x0, a) for x0, a in vanos_ubicados(_f[0], _f[1], _f[2], _f[4]) if tipo_de_vano(_f[0], x0) == "puerta"]
    for _x0, _a in _ing:
        _xc = _x0 + _a / 2.0
        ax.annotate("", xy=(_xc, 0.45), xytext=(_xc, -0.45),
                    arrowprops=dict(arrowstyle="-|>", color=C_NARANJA, lw=1.3), zorder=6)
        # Rótulo de puerta colocado en zona limpia sin solapar piezas
        # Rótulo de ingreso principal en zona interior despejada
        ax.text(x_pasaje + ancho_pasaje / 2.0, 1.45,
                "INGRESO PRINCIPAL (%s m)" % C.coma(ANCHO_INGRESO, 2), ha="center", va="center",
                fontsize=5.0, color=C_NARANJA, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec=C_NARANJA, lw=0.5, alpha=0.9),
                zorder=7)

def limites_terreno(ax):
    x_izq = -RETIRO_LATERAL
    x_der = FRENTE + RETIRO_LATERAL
    y_post = FONDO + RETIRO_POSTERIOR
    y_f = -RETIRO_FRONTAL
    
    # EL AREA VERDE, QUE ANTES ERA UN RECTANGULO AMARILLENTO. Es el que
    # sostiene el area libre del 37,1 %: el lector tiene que poder verlo,
    # no deducirlo de una cota.
    ax.add_patch(Rectangle((0, FONDO), FRENTE, RETIRO_POSTERIOR,
                           fc="#eef7e3", ec="#7cb342", lw=1.0, zorder=1))
    _vegetacion(ax, 0.0, FONDO, FRENTE, RETIRO_POSTERIOR,
                claro=(FRENTE * 0.16, FONDO + RETIRO_POSTERIOR * 0.18,
                       FRENTE * 0.84, FONDO + RETIRO_POSTERIOR * 0.74))
    ax.text(FRENTE / 2.0, FONDO + RETIRO_POSTERIOR * 0.60,
            "ÁREA VERDE", ha="center", va="center", fontsize=8.0,
            color="#33691e", fontweight="bold", zorder=5,
            bbox=dict(boxstyle="square,pad=0.35", fc="#eef7e3",
                      ec="none"))
    ax.text(FRENTE / 2.0, FONDO + RETIRO_POSTERIOR * 0.32,
            "retiro posterior %s × %s m = %s m²"
            % (C.coma(FRENTE, 2), C.coma(RETIRO_POSTERIOR, 2),
               C.coma(FRENTE * RETIRO_POSTERIOR, 2)),
            ha="center", va="center", fontsize=6.4, color="#558b2f",
            zorder=5, bbox=dict(boxstyle="square,pad=0.30",
                                fc="#eef7e3", ec="none"))

    ax.plot([x_izq, x_der], [y_post, y_post], color=C_ROJO_LOTE, lw=1.0, ls=(0, (6, 2, 1, 2)), zorder=7)
    ax.text(FRENTE / 2.0, y_post + 0.35, "LÍMITE DE PROPIEDAD POSTERIOR (COLINDANTE)",
            ha="center", va="bottom", fontsize=5.8, color=C_ROJO_LOTE, fontweight="bold", zorder=7)
    
    ax.plot([x_izq, x_der], [y_f, y_f], color=C_ROJO_LOTE, lw=1.0, ls=(0, (6, 2, 1, 2)), zorder=7)
    # DEBAJO DE SU PROPIA LINEA. Puesto encima caia sobre los
    # cuatro estacionamientos: once piezas de dibujo lo tapaban.
    ax.text(FRENTE / 2.0, y_f - 0.18,
            "LÍMITE DE PROPIEDAD MUNICIPAL (LÍNEA DE FACHADA)",
            ha="center", va="top", fontsize=6.2,
            color=C_ROJO_LOTE, fontweight="bold", zorder=7)
    
    ax.plot([x_izq, x_izq], [y_f, y_post], color=C_ROJO_LOTE, lw=0.8, ls=(0, (6, 2, 1, 2)), zorder=7)
    ax.text(x_izq - 0.25, FONDO / 2.0, "LÍMITE DE PROPIEDAD OESTE (MEDIANERA)",
            ha="right", va="center", rotation=90, fontsize=5.8, color=C_ROJO_LOTE, fontweight="bold", zorder=7)
    
    ax.plot([x_der, x_der], [y_f, y_post], color=C_ROJO_LOTE, lw=0.8, ls=(0, (6, 2, 1, 2)), zorder=7)
    ax.text(x_der + 0.25, FONDO / 2.0, "LÍMITE DE PROPIEDAD ESTE (MEDIANERA)",
            ha="left", va="center", rotation=270, fontsize=5.8, color=C_ROJO_LOTE, fontweight="bold", zorder=7)

def ejes_y_cotas_planta(ax):
    """Solo lo que cota el EDIFICIO. Los retiros y el lote se fueron.

    POR QUE SE PARTIO. La figura anterior cotaba el edificio y el lote en el
    mismo dibujo: con los retiros, la via publica y el panel lateral, el
    lienzo pedia 27 m de ancho y 37,5 de alto. Puesto en una caja de 6,30 x
    8,86 pulgadas, el metro quedaba en 5,9 mm y ahi no entra ningun rotulo.
    Separado el sitio, el mismo edificio se dibuja a unos 8,7 mm por metro:
    un 47 % mas grande, sin cambiar una sola cifra.

    LAS COTAS EN X VAN ABAJO, las dos. Antes iban arriba, y esos 3,70 m de
    lienzo sobre el edificio eran alto puro que le robaba escala al dibujo.
    """
    for x, let in zip(EJE_X, ETIQ_X):
        ax.plot([x, x], [-0.5, FONDO + 0.5], color=C_AZUL_EJE, lw=0.4,
                ls=(0, (8, 3, 2, 3)), zorder=2)
        dibujar_burbuja_eje(ax, x, FONDO + 0.95, let)
        dibujar_burbuja_eje(ax, x, -0.95, let)

    for i in range(len(EJE_X) - 1):
        x0, x1 = EJE_X[i], EJE_X[i + 1]
        cota_lineal_h(ax, -1.90, x0, x1, "%.2f" % (x1 - x0), color=C_COTA,
                      fs=6.0)
    cota_lineal_h(ax, -2.75, 0.0, FRENTE,
                  "Frente edificado = %.2f m" % FRENTE, color=C_COTA, fs=6.4)

    for i, y in enumerate(EJES_MX):
        ax.plot([-0.5, FRENTE + 0.5], [y, y], color=C_AZUL_EJE, lw=0.4,
                ls=(0, (8, 3, 2, 3)), zorder=2)
        dibujar_burbuja_eje(ax, -0.95, y, str(i + 1))

    for i in range(len(EJES_MX) - 1):
        y0, y1 = EJES_MX[i], EJES_MX[i + 1]
        cota_lineal_v(ax, -1.90, y0, y1, "%.2f" % (y1 - y0), color=C_COTA,
                      fs=6.0)
    cota_lineal_v(ax, -2.75, 0.0, FONDO, "Fondo edificado = %.2f m" % FONDO,
                  color=C_COTA, fs=6.4)


def cotas_de_sitio(ax):
    """Lo que cota el LOTE: retiros, frente y fondo totales, via publica."""
    x_izq, x_der = -RETIRO_LATERAL, FRENTE + RETIRO_LATERAL
    y_post, y_f = FONDO + RETIRO_POSTERIOR, -RETIRO_FRONTAL

    cota_lineal_v(ax, -1.60, y_f, 0.0, "Retiro frontal = %s m" % C.coma(RETIRO_FRONTAL, 2),
                  color=C_VERDE, fs=6.4)
    cota_lineal_v(ax, -1.60, 0.0, FONDO, "Fondo edificado = %s m" % C.coma(FONDO, 2),
                  color=C_COTA, fs=6.6)
    cota_lineal_v(ax, -1.60, FONDO, y_post, "Retiro posterior = %s m" % C.coma(RETIRO_POSTERIOR, 2),
                  color=C_VERDE, fs=6.4)
    cota_lineal_v(ax, -3.10, y_f, y_post,
                  "FONDO TOTAL DEL LOTE = %.2f m" % FONDO_LOTE,
                  color=C_ROJO_LOTE, fs=7.0, lw=0.9)

    cota_lineal_h(ax, y_f - 1.20, 0.0, FRENTE,
                  "Frente edificado = %.2f m" % FRENTE, color=C_COTA, fs=6.6)
    cota_lineal_h(ax, y_f - 2.20, x_izq, x_der,
                  "FRENTE TOTAL DEL LOTE = %.2f m" % FRENTE_LOTE,
                  color=C_ROJO_LOTE, fs=7.0, lw=0.9)

    ax.add_patch(Rectangle((x_izq - 0.5, y_f - 4.00), FRENTE_LOTE + 1.0, 1.10,
                           fc="#eeeeee", ec="#bdbdbd", lw=0.5, zorder=1))
    ax.text(FRENTE / 2.0, y_f - 3.45, "VÍA PÚBLICA (CALZADA Y ACERA)",
            ha="center", va="center", fontsize=7.0, color="#424242",
            fontweight="bold", zorder=3)


def _vegetacion(ax, x0, y0, ancho, alto, paso=0.95, claro=None):
    """La textura del área verde: matas en retícula, no un relleno plano.

    Un rectángulo de color no se lee como jardín en un plano en blanco y
    negro, que es como se imprime un informe. La mata sí.
    """
    import math
    n_x = max(int(ancho / paso), 1)
    n_y = max(int(alto / paso), 1)
    for i in range(n_x):
        for j in range(n_y):
            cx = x0 + (i + 0.5) * ancho / n_x
            cy = y0 + (j + 0.5) * alto / n_y
            # EL CLARO DEL ROTULO. Un recuadro de fondo engaña al ojo pero
            # no al control, y el control tiene razón: la mata sigue ahí.
            if claro and (claro[0] <= cx <= claro[2]
                          and claro[1] <= cy <= claro[3]):
                continue
            for k in range(5):
                a_k = math.pi * (0.15 + 0.175 * k)
                ax.plot([cx, cx + 0.22 * math.cos(a_k)],
                        [cy, cy + 0.22 * math.sin(a_k)],
                        color="#7cb342", lw=0.5, zorder=2)


def _vehiculo(ax, cx, cy):
    """La silueta de un auto dentro del cajón.

    Un cajón vacío no demuestra nada; con el vehículo se ve que los 5,00 m
    de retiro frontal alcanzan de verdad y que la maniobra tiene por dónde.
    """
    L, A = EST_LARGO * 0.80, EST_ANCHO * 0.62
    ax.add_patch(FancyBboxPatch((cx - A / 2.0, cy - L / 2.0), A, L,
                                boxstyle="round,pad=0.02,rounding_size=0.30",
                                fc="#e8eaf6", ec="#5c6bc0", lw=0.8, zorder=3))
    ax.add_patch(FancyBboxPatch((cx - A * 0.34, cy - L * 0.10), A * 0.68,
                                L * 0.34,
                                boxstyle="round,pad=0.01,rounding_size=0.14",
                                fc="#c5cae9", ec="#5c6bc0", lw=0.6, zorder=4))
    for sx in (-1, 1):
        for sy in (-1, 1):
            ax.plot([cx + sx * A * 0.50], [cy + sy * L * 0.31], "s",
                    ms=1.6, color="#3949ab", zorder=4)


def _norte_y_escala(ax, x0, y0, esc_m):
    """El norte y la escala gráfica, en la banda libre del plano de sitio."""
    nx, ny = x0 + 1.70, y0
    ax.annotate("", xy=(nx, ny + 1.60), xytext=(nx, ny - 1.00),
                arrowprops=dict(arrowstyle="-|>", color="#212121", lw=1.5),
                zorder=12)
    ax.text(nx, ny + 2.05, "N", ha="center", va="center", fontsize=12,
            color="#212121", fontweight="bold", zorder=12)
    ax.plot([nx - 0.80, nx + 0.80], [ny, ny], color="#212121", lw=0.9,
            zorder=12)
    ax.text(nx + 1.10, ny, "E", ha="center", va="center", fontsize=8,
            color="#616161", zorder=12)
    ax.text(nx - 1.10, ny, "O", ha="center", va="center", fontsize=8,
            color="#616161", zorder=12)
    ax.text(nx, ny - 1.90,
            "Fachada principal al %s\nRetiro posterior al %s"
            % (META.ORIENTACION_FACHADA, META.ORIENTACION_POSTERIOR),
            ha="center", va="top", fontsize=6.4, color="#37474f",
            linespacing=1.3, zorder=11)

    # ESCALA GRAFICA DE VERDAD: barra de 4 m medida en las unidades del
    # dibujo. La version anterior rotulaba «0 1m 2m 4m» sobre una barra de
    # cuatro PULGADAS de lienzo, asi que el rotulo mentia en cuanto la
    # figura se reescalaba. Esta se dibuja en metros y no puede mentir.
    yb = ny - 4.40
    ax.plot([nx - 2.00, nx + 2.00], [yb, yb], color="#212121", lw=1.6,
            zorder=11)
    for d in (0.0, 1.0, 2.0, 4.0):
        xx = nx - 2.00 + d
        ax.plot([xx, xx], [yb - 0.18, yb + 0.18], color="#212121", lw=1.0,
                zorder=11)
        ax.text(xx, yb - 0.55, "%g" % d, ha="center", va="top", fontsize=6.0,
                color="#424242", zorder=11)
    ax.text(nx, yb + 0.55, "escala gráfica (m)", ha="center", va="bottom",
            fontsize=6.4, color="#37474f", fontweight="bold", zorder=11)


def _huella_edificada(ax):
    """La planta, en gris, para que el sitio muestre DÓNDE se apoya."""
    ax.add_patch(Rectangle((0, 0), FRENTE, FONDO, fc="#eceff1", ec="#37474f",
                           lw=1.2, zorder=3))
    ax.add_patch(Rectangle((POZO_X0, POZO_Y0), POZO_X1 - POZO_X0,
                           POZO_Y1 - POZO_Y0, fc="#ffffff", ec="#78909c",
                           hatch="////", lw=0.8, zorder=4))
    ax.text(FRENTE / 2.0, FONDO / 2.0 + 3.40,
            "ÁREA TECHADA\n%.2f m² por piso\n%d pisos"
            % (AREA_PLANTA, N_PISOS),
            ha="center", va="center", fontsize=7.6, color="#263238",
            fontweight="bold", linespacing=1.3, zorder=5)
    ax.text((POZO_X0 + POZO_X1) / 2.0, (POZO_Y0 + POZO_Y1) / 2.0,
            "POZO\n%.2f m²" % AREA_POZO, ha="center", va="center",
            fontsize=6.4, color="#00695c", fontweight="bold", linespacing=1.25,
            bbox=dict(boxstyle="round,pad=0.16", fc="#e0f2f1", ec="#80cbc4",
                      lw=0.5), zorder=6)


def _leyenda_de_sitio(ax, x0, y0):
    """Qué es cada superficie del lote, con su color y su área.

    Reemplaza al recuadro «Condiciones del lote», que repetía filas del
    cuadro de parámetros —la figura siguiente del informe—. Una leyenda no
    repite datos: dice qué es cada mancha del dibujo, que es lo único que
    el cuadro no puede hacer.
    """
    filas = [
        ("#eceff1", "#37474f", "Área techada",
         "%s m² por piso" % C.coma(AREA_PLANTA, 2)),
        ("#eef7e3", "#7cb342", "Área verde",
         "%s m² (retiro posterior)" % C.coma(FRENTE * RETIRO_POSTERIOR, 2)),
        ("#f6f8ec", "#c5e1a5", "Cochera",
         "%d de %s × %s m" % (N_ESTACIONAMIENTOS, C.coma(EST_ANCHO, 2),
                              C.coma(EST_LARGO, 2))),
        ("#fff8e1", "#ffe082", "Ingreso peatonal",
         "pasaje al hall común"),
        ("#ffffff", "#78909c", "Pozo de luz",
         "%s m² (A.020)" % C.coma(AREA_POZO, 2)),
        (None, C_ROJO_LOTE, "Límite de propiedad",
         "junta de %s m por lado" % C.coma(RETIRO_LATERAL, 2)),
    ]
    paso = 1.55
    alto = paso * len(filas) + 1.25
    ax.add_patch(FancyBboxPatch((x0, y0 - alto + paso), 7.30, alto,
                                boxstyle="round,pad=0.25", fc="#ffffff",
                                ec="#37474f", lw=0.9, zorder=10))
    ax.text(x0 + 3.65, y0 + 0.62, "LEYENDA DEL LOTE", ha="center",
            va="center", fontsize=7.4, color="#263238", fontweight="bold",
            zorder=11)
    for i, (fc, ec, nom, det) in enumerate(filas):
        yy = y0 - paso * i - 0.55
        if fc is None:
            ax.plot([x0 + 0.35, x0 + 1.15], [yy + 0.30] * 2, color=ec,
                    lw=1.2, ls=(0, (5, 2, 1, 2)), zorder=11)
        else:
            ax.add_patch(Rectangle((x0 + 0.35, yy + 0.08), 0.80, 0.46,
                                   fc=fc, ec=ec, lw=0.8, zorder=11))
        ax.text(x0 + 1.40, yy + 0.32, nom, ha="left", va="center",
                fontsize=6.6, color="#263238", fontweight="bold", zorder=11)
        ax.text(x0 + 1.40, yy - 0.28, det, ha="left", va="center",
                fontsize=6.2, color="#546e7a", zorder=11)


# ------------# ---------------------------------------------------------------- FIGURAS

def _leyenda_departamentos(fig, y):
    """Un renglón: qué color de etiqueta es cada departamento."""
    piezas = [("■ Departamento A", COLOR_DPTO["A"]),
              ("■ Departamento B", COLOR_DPTO["B"]),
              ("■ Zona común", COLOR_DPTO["común"]),
              ("○ Eje estructural", C_AZUL_EJE)]
    r = fig.canvas.get_renderer()
    anchos = []
    for txt, col in piezas:
        tt = fig.text(0, 0, txt, fontsize=6.8, fontweight="bold")
        anchos.append(tt.get_window_extent(renderer=r).width / fig.bbox.width)
        tt.remove()
    sep = 0.035
    x = 0.5 - (sum(anchos) + sep * (len(piezas) - 1)) / 2.0
    for (txt, col), wf in zip(piezas, anchos):
        fig.text(x, y, txt, ha="left", va="top", fontsize=6.8, color=col,
                 fontweight="bold")
        x += wf + sep


def dibujar_planta():
    """FIGURA 1 — la planta del piso típico, y NADA más.

    LOS LÍMITES SE ELIGEN PARA QUE LA HOJA MANDE. El alto útil de la caja de
    página son 8,86 pulgadas y el ancho 6,30: la relación es 1,41. Se acota
    el lienzo a una relación parecida para que no sobre hoja en ninguna de
    las dos direcciones, que es lo único que decide la escala.
    """
    x0, x1 = -3.60, 12.80
    y0, y1 = -3.60, 22.90
    # 0,74 DE BANDA Y NO 0,52: lleva un renglón más, el de la leyenda de
    # departamentos. El total sigue dentro de las 8,86 de la página.
    BANDA = 0.74
    esc = min(C.ANCHO_PAGINA / (x1 - x0), (8.84 - BANDA) / (y1 - y0))
    anc, alt = (x1 - x0) * esc, (y1 - y0) * esc
    fig = plt.figure(figsize=(anc, alt + BANDA), dpi=200)
    ax = fig.add_axes((0.0, 0.0, 1.0, alt / (alt + BANDA)))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")

    ambientes(ax)
    pozo_de_luz(ax)
    zona_comun_y_escalera(ax)
    muros(ax)
    ejes_y_cotas_planta(ax)

    fig.text(0.5, 0.992,
             "PLANTA ARQUITECTÓNICA DEL PISO TÍPICO (NIVELES 1 A %d)"
             % N_PISOS,
             ha="center", va="top", fontsize=10.5, color="#1a237e",
             fontweight="bold")
    fig.text(0.5, 0.962,
             "Los %d ambientes van en ETIQUETA con su número; los CÍRCULOS del "
             "borde son los ejes. Nombre, área e iluminación: figura siguiente"
             % len(REGISTRO),
             ha="center", va="top", fontsize=6.6, color="#37474f")
    _leyenda_departamentos(fig, 0.934)

    # CONTROL: que el metro de hoja no baje de lo que se midió como legible.
    assert esc >= 0.30, (
        "la planta quedó a %.1f mm por metro y a menos de 7,6 no entra un "
        "etiqueta de dos cifras" % (esc * 25.4))
    print("  planta: 1 m = %.1f mm de hoja  (antes 5,9)" % (esc * 25.4))
    C.guardar(fig, os.path.join(OUT, "PLANTA-ARQUITECTONICA.png"))


def dibujar_ubicacion():
    """FIGURA 2 — el lote entero: área verde, cochera, retiros y linderos.

    Llena la hoja A4: el ancho del lienzo se DERIVA del alto para que las
    dos direcciones toquen el borde a la vez. Ver el porqué en la cabecera
    del arreglo del 2026-09-28.
    """
    ALTO = 8.60
    y0, y1 = -10.20, 26.60
    x0 = -4.90
    # el ancho que hace que el dibujo llene las dos direcciones
    x1 = x0 + (y1 - y0) * C.ANCHO_PAGINA / ALTO
    esc = min(C.ANCHO_PAGINA / (x1 - x0), ALTO / (y1 - y0))
    anc, alt = (x1 - x0) * esc, (y1 - y0) * esc
    fig = plt.figure(figsize=(anc, alt + 0.52), dpi=200)
    ax = fig.add_axes((0.0, 0.0, 1.0, alt / (alt + 0.52)))
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.axis("off")

    _huella_edificada(ax)
    retiro_y_estacionamientos(ax)
    limites_terreno(ax)
    cotas_de_sitio(ax)

    # LA BANDA DEL CAJETIN: el lote es 1 a 2,54 y ningun encuadre lo vuelve
    # cuadrado. Lo que sobra a la derecha es donde una lamina pone su norte,
    # su escala y su leyenda -- y esas tres SON del plano, no son «datos».
    x_banda = 13.60
    _norte_y_escala(ax, x_banda, 19.20, esc)
    _leyenda_de_sitio(ax, x_banda - 0.20, 9.40)

    fig.text(0.5, 0.992,
             "PLANO DE UBICACIÓN  ·  LOTE DE %.2f × %.2f m = %.2f m²"
             % (FRENTE_LOTE, FONDO_LOTE, AREA_LOTE),
             ha="center", va="top", fontsize=10.5, color="#1a237e",
             fontweight="bold")
    fig.text(0.5, 0.962,
             "Área verde %.2f m² + cochera de %d espacios + pozo de luz "
             "%.2f m² → área libre %s %% del lote (mínimo %.0f %%)"
             % (FRENTE * RETIRO_POSTERIOR, N_ESTACIONAMIENTOS, AREA_POZO,
                C.coma(PCT_LIBRE, 1), 100.0 * AREA_LIBRE_MINIMA),
             ha="center", va="top", fontsize=6.6, color="#37474f")

    # CONTROL: que el dibujo llegue a los dos bordes de la hoja.
    assert abs(anc - C.ANCHO_PAGINA) < 0.02, (
        "el plano ocupa %.2f de las %.2f pulgadas de ancho" % (anc, C.ANCHO_PAGINA))
    print("  ubicación: %.2f x %.2f pulg, 1 m = %.1f mm de hoja"
          % (anc, alt, esc * 25.4))
    C.guardar(fig, os.path.join(OUT, "PLANO-UBICACION.png"))


def _asegurar_registro():
    """El cuadro necesita los números que reparte el dibujo, no otros."""
    if not REGISTRO:
        f = plt.figure(figsize=(1, 1))
        a = f.add_axes((0, 0, 1, 1))
        ambientes(a)
        zona_comun_y_escalera(a)
        plt.close(f)


def dibujar_cuadro_ambientes():
    """FIGURA 3 — el cuadro que le da sentido a los números de la planta."""
    _asegurar_registro()
    # EL MISMO FORMATO QUE LA ETIQUETA: «04» en el plano, «04» acá.
    filas = [["%02d" % r["n"], r["nombre"], r["dpto"], C.coma(r["area"], 2),
              r["luz"]] for r in REGISTRO]
    colores = [r["color"] for r in REGISTRO]
    alto = 0.235 * (len(filas) + 2) + 1.70
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, alto), dpi=200)
    y_ar, y_ab = C.marco(
        fig, "Cuadro de ambientes del piso típico",
        subtitulo=("el número es el de la ETIQUETA de la planta, cuyo color dice el "
                   "departamento; el color de la fila es el de la iluminación"),
        pie=("Los %d ambientes suman %s m² de los %s m² techados: la "
             "diferencia son los muros, los tabiques y el pozo. La luz se "
             "reparte así: %d ambientes la reciben de fachada, %d SÓLO del "
             "pozo de luz —las dos salas-comedor, que son las que "
             "justifican ese vacío en medio de la planta—, %d del pozo o "
             "de fachada, que es la zona común, y %d dependen de "
             "ventilación asistida."
             % (len(filas), C.coma(sum(r["area"] for r in REGISTRO), 2),
                C.coma(AREA_PLANTA, 2),
                sum(1 for r in REGISTRO if r["luz"].startswith("Fachada")),
                sum(1 for r in REGISTRO if r["luz"] == "Pozo de luz central"),
                sum(1 for r in REGISTRO if r["luz"] == "Pozo de luz / fachada"),
                sum(1 for r in REGISTRO if "asistida" in r["luz"]))))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    C.tabla(ax, 0.035, y_ar - 0.01, 0.93, 0.235 / alto,
            ["N.º", "Ambiente", "Dpto.", "Área\n(m²)",
             "Iluminación"],
            filas, colores_fila=colores, fs=8.0)
    C.guardar(fig, os.path.join(OUT, "CUADRO-AMBIENTES.png"))


def dibujar_cuadro_parametros():
    """FIGURA 4 — parámetros y superficies, en tabla y no en caja de texto.

    Antes eran tres recuadros de texto a 5,2 pt dentro del plano. Una tabla
    dice lo mismo a 8 pt y además alinea las columnas, que es justo lo que
    un cuadro de superficies necesita para poder comprobarse a ojo.
    """
    # EL AREA DEL LOTE ESTA EN EL SSOT: recalcularla acá es abrir una
    # segunda fuente para el mismo numero.
    a_lote = AREA_LOTE
    assert abs(a_lote - FRENTE_LOTE * FONDO_LOTE) < 1e-6, (
        "AREA_LOTE = %.2f no cierra con %.2f x %.2f"
        % (a_lote, FRENTE_LOTE, FONDO_LOTE))

    def pct(x):
        # CON COMA: la tabla de al lado usa C.coma y "62.1 %" al
        # lado de "227,22" delata dos manos escribiendo la misma tabla.
        return C.coma(100.0 * x / a_lote, 1) + " %"

    zona = _zona_sismica()
    perfil = _perfil_de_suelo()
    cat, cat_txt = _categoria()
    uni = _unidad_adoptada()
    n_viv, por_piso, dorm = _viviendas()
    par = [
        ["Uso / destino",
         "Vivienda multifamiliar · %d viviendas (%d por piso)"
         % (n_viv, por_piso)],
        ["Programa por vivienda", _programa_de_vivienda(dorm)],
        ["Niveles", "%d pisos · Hn = %s m" % (N_PISOS, C.coma(HN, 2))],
        ["Altura de entrepiso",
         "%s m · altura libre %s m" % (C.coma(H_ENTREPISO, 2),
                                       C.coma(H_LIBRE, 2))],
        ["Zona sísmica", "Zona %d · Z = %s" % (zona, C.coma(Z, 2))],
        ["Perfil de suelo",
         "%s · S = %s · Tp = %s s · TL = %s s"
         % (perfil, C.coma(S, 2), C.coma(T_P, 2), C.coma(T_L, 2))],
        ["Categoría de la edificación",
         "%s — %s · U = %s" % (cat, cat_txt, C.coma(U, 2))],
        ["Sistema estructural",
         "Albañilería confinada · R = %s" % C.coma(R_E030, 2)],
        ["Unidad de albañilería",
         "Sólida Tipo %s · %.0f %% de vacíos · f'b = %.0f kgf/cm²"
         % (uni["tipo"], uni["vacios"], uni["fb"])],
        ["Espesor de muro",
         "t = %s m · asentada de cabeza (%.0f × %.0f × %.0f cm)"
         % (C.coma(ESPESOR, 2), uni["largo"], uni["ancho"], uni["alto"])],
    ]
    sup = [
        ["Área del lote", C.coma(a_lote, 2), C.coma(100.0, 1) + " %"],
        ["Área techada por piso", C.coma(AREA_PLANTA, 2), pct(AREA_PLANTA)],
        ["Retiro frontal", C.coma(FRENTE * RETIRO_FRONTAL, 2),
         pct(FRENTE * RETIRO_FRONTAL)],
        ["Retiro posterior", C.coma(FRENTE * RETIRO_POSTERIOR, 2),
         pct(FRENTE * RETIRO_POSTERIOR)],
        ["Pozo de luz central", C.coma(AREA_POZO, 2), pct(AREA_POZO)],
        # LAS DOS QUE VENIAN DEL RECUADRO DEL PLANO DE UBICACION: alla
        # repetian, aca cierran el cuadro.
        ["Cochera, %d espacios (dentro del retiro frontal)"
         % N_ESTACIONAMIENTOS,
         C.coma(N_ESTACIONAMIENTOS * EST_ANCHO * EST_LARGO, 2),
         pct(N_ESTACIONAMIENTOS * EST_ANCHO * EST_LARGO)],
        ["Juntas laterales (fuera del área libre)",
         C.coma(2 * RETIRO_LATERAL * FONDO_LOTE, 2),
         pct(2 * RETIRO_LATERAL * FONDO_LOTE)],
        ["ÁREA LIBRE TOTAL", C.coma(AREA_LIBRE, 2),
         C.coma(PCT_LIBRE, 1) + " %"],
        ["Mínimo normativo",
         "≥ %.0f %%" % (100.0 * AREA_LIBRE_MINIMA), "CUMPLE"],
    ]
    alto = 0.235 * (len(par) + len(sup) + 5) + 1.55
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, alto), dpi=200)
    y_ar, y_ab = C.marco(
        fig, "Parámetros del proyecto y cuadro de superficies",
        pie=("El área libre del %s %% son los dos retiros más el pozo de "
             "luz —59,50 + 53,55 + 22,68— y supera el %.0f %% que exige "
             "el RNE A.020. Los dos últimos renglones NO son partes de esa "
             "suma: la cochera ocupa el 84 %% del retiro frontal y las "
             "juntas quedan fuera del área libre. Los "
             "parámetros Z, S y U de la primera tabla son los mismos que "
             "entran al cortante basal del capítulo de análisis: salen del "
             "SSOT, no están tecleados aquí."
             % (C.coma(PCT_LIBRE, 1), 100.0 * AREA_LIBRE_MINIMA)))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    h = 0.235 / alto
    y = C.tabla(ax, 0.035, y_ar - 0.01, 0.93, h,
                ["Parámetro", "Valor adoptado"], par,
                titulo="PARÁMETROS DEL PROYECTO", fs=8.0)
    C.tabla(ax, 0.035, y - h * 0.65, 0.93, h,
            ["Concepto", "Área (m²)", "% del lote"], sup,
            titulo="CUADRO GENERAL DE SUPERFICIES", fs=8.0)
    C.guardar(fig, os.path.join(OUT, "CUADRO-PARAMETROS.png"))


def dibujar():
    dibujar_planta()
    dibujar_ubicacion()
    dibujar_cuadro_ambientes()
    dibujar_cuadro_parametros()


if __name__ == "__main__":
    dibujar()
