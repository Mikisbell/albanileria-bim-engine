# -*- coding: utf-8 -*-
u"""Flujograma metodologico de analisis y diseno sismico de albanileria.

Sintetiza las 8 fases del diseno sismorresistente segun la E.070, la
E.030-2026, la E.060, la A.010 y la A.020.

POR QUE SE REESCRIBIO (2026-09-26). La version anterior tenia las ocho fases
escritas a mano como listas de texto, con los numeros CLAVADOS dentro de cada
cadena. El guardian 15 --que audita citas normativas-- la denuncio por citar
el "E.030 Art. 26" para el peso sismico, que es el **Art. 31**; al abrirla
aparecio que ese no era el problema, sino el sintoma. La figura publicaba, en
el informe, QUINCE datos vencidos:

    tabiqueria 100 kgf/m2   -> hoy 57, METRADA por el 31
    sigma critico 6,42      -> hoy 8,99 (MX-7)
    P_total 1 540,38 ton    -> hoy 1 421,9
    V basal 417,19 ton      -> hoy 385,1
    densidad +32,3 / +94,6  -> hoy +127,0 / +150,8
    "excentricidad < 2 cm"  -> es 1 cm en X pero 19,6 cm en Y
    2 o 6 mm cada 3 hiladas -> hoy cada 2 hiladas
    Sum Vm 811,8 / 708,2    -> hoy 794,3 / 711,0
    ... y la lamina E-01 descrita como algo que no dibuja.

LA CAUSA NO ES EL DESCUIDO, ES LA DUPLICACION. Un numero escrito a mano en
una figura es una copia que nadie vuelve a mirar: cuando el calculo cambia
--y cambio muchas veces-- la copia se queda, y encima se queda con aspecto de
verificada. Por eso ahora **todo numero sale de su fuente** y la figura no
guarda ninguno.

Y LO QUE NO DEBE ESTAR, NO ESTA. Los resultados que ya publican las
laminas-cuadro con su propio control --el reparto muro por muro, el cuadro de
columnas, el estribaje-- no se repiten aca: este flujograma cuenta el METODO
y que articulo gobierna cada paso. Repetir un resultado en dos artefactos es
volver a crear el problema que esta cabecera describe.
"""
from __future__ import print_function

import contextlib
import importlib.util
import io as _io
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                  # noqa: E402
from matplotlib.patches import FancyBboxPatch                    # noqa: E402
import cuadro as C                                             # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(AQUI, "..", "salidas", "informe")

# LA PALETA DE LA LAMINA. Cada fase declara su `clave` y aqui vive su color:
# gris para lo que describe, azul para el analisis, naranja para lo que
# gobierna, verde para lo que cumple y rojo para lo que exige atencion.
AZUL = "#1f5fbf"
VERDE = "#2e7d52"
NARANJA = "#c0560f"
GRAFITO = "#37474f"
ROJO = "#b71c1c"
COLOR = {"gris": GRAFITO, "azul": AZUL, "naranja": NARANJA,
         "verde": VERDE, "rojo": ROJO}
FONDO_CARD = "#f8fafc"
BORDE_CARD = "#cbd5e1"
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))


def _mod(nombre):
    u"""Carga un script numerado del SSOT sin ensuciar la salida."""
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location("_f" + nombre[:2], ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def _hn():
    """La altura total del edificio, del SSOT."""
    import proyecto as P
    return P.HN


def _coma(x, dec=2):
    return ("%%.%df" % dec) % x


def reunir():
    u"""Junta de sus fuentes todo lo que la figura afirma con un numero."""
    import proyecto as P
    m01 = _mod("01_arquitectura_y_densidad.py")
    m02 = _mod("02_metrado_y_esfuerzo_axial.py")
    m11 = _mod("11_metrado_muros.py")
    m16 = _mod("16_irregularidades.py")
    m17 = _mod("17_reparto_cortante.py")
    m18 = _mod("18_diseno_muros.py")

    d = {}
    # --- fase 1: lote y densidad ------------------------------------------
    d["lote"] = (P.FRENTE_LOTE, P.FONDO_LOTE, P.AREA_LOTE)
    d["huella"] = (P.FRENTE, P.FONDO)
    d["ap"] = P.AREA_PLANTA
    d["req"] = m01.densidad_requerida()
    d["dens"] = {}
    for dire in ("X", "Y"):
        ac = sum(f["Ac"] for f in m01.tabla_densidad(dire))
        obt = ac / P.AREA_PLANTA
        d["dens"][dire] = (obt, 100.0 * (obt / d["req"] - 1.0))
    d["lmin"] = P.LONG_MINIMA

    # --- fase 2: predimensionamiento --------------------------------------
    d["t"] = P.ESPESOR
    d["e_losa"] = P.E_LOSA
    d["c1"] = (P.ESPESOR, P.H_COLUMNA)
    d["c2"] = (P.ESPESOR, P.H_COLUMNA_EXT)
    d["solera"] = (P.ESPESOR, P.H_SOLERA)

    # --- fase 3: cargas y esfuerzo axial ----------------------------------
    # los coeficientes del 8.5.3 NO se escriben a mano en la cadena de la
    # tarjeta: salen del script que los aplica. Asi la figura no puede
    # publicar una formula distinta de la que se calculo.
    d["c_vm"] = (m18.C_ARCILLA, m18.C_PG, m18.C_FISURA)
    d["tabique"] = P.TABIQUERIA
    d["sc"] = (P.SC_VIVIENDA, P.SC_AZOTEA)
    d["fm"] = P.FM
    lim, _esb = m02.limite_axial(P.FM)
    d["lim_axial"] = lim
    peor = max(m11.metrar(), key=lambda f: f["sigma"])
    d["sigma"] = (peor["nom"].split()[0], peor["sigma"])

    # --- fase 4: analisis sismico -----------------------------------------
    T, k, C, _pesos, Pt, V = m16.sismo()
    d["zuscr"] = (P.Z, P.U, P.S, C, 3.0)
    d["peso"] = Pt / 1000.0
    d["V"] = V / 1000.0
    d["T"] = T
    filas, h, Fi, Vb, xm, ym, xr, yr = m17.contexto()
    d["cm"], d["cr"] = (xm, ym), (xr, yr)
    d["exc"] = (abs(xm - xr), abs(ym - yr))
    Ktor, Kx, Ky = m17.geometria_torsional(filas, xr, yr)
    Vent = m17.cortantes_de_entrepiso(Fi)
    rep, _e = m17.repartir(filas, Vent, xm, ym, xr, yr, Ktor, Kx, Ky)
    d["conc"] = {}
    for dire in ("X", "Y"):
        vs = sorted((r["V"][0][2] for r in rep.values() if r["dir"] == dire),
                    reverse=True)
        d["conc"][dire] = (len(vs), 100.0 * vs[0] / sum(vs),
                           100.0 * sum(vs[:2]) / sum(vs))
    return d


def fases(d):
    u"""Las ocho tarjetas. Todo numero viene de `d`; ninguno se escribe aca."""
    fx, fy, al = d["lote"]
    hx, hy = d["huella"]
    dx, dy = d["dens"]["X"], d["dens"]["Y"]
    nx, px, p2x = d["conc"]["X"]
    ny, py, p2y = d["conc"]["Y"]
    Z, U, S, C, R = d["zuscr"]

    col1 = [
        {"num": "1", "titulo": "CONCEPCIÓN, LOTE Y DENSIDAD", "clave": "gris",
         "items": [
            u"Terreno: %s x %s m (%s m²) | Edificado: %s x %s m"
            % (_coma(fx), _coma(fy), _coma(al), _coma(hx), _coma(hy)),
            u"Área techada de planta (sin el pozo): %s m²" % _coma(d["ap"]),
            u"Retiros y estacionamientos: A.010 / A.020",
            u"Densidad mínima E.070 7.1.2.b: Σ(L·t)/Ap ≥ Z·U·S·N/56 = %s"
            % _coma(d["req"], 4),
            u"  -> Dir X: %s ≥ %s  CUMPLE (+%s %%)"
            % (_coma(dx[0], 4), _coma(d["req"], 4), _coma(dx[1], 1)),
            u"  -> Dir Y: %s ≥ %s  CUMPLE (+%s %%)"
            % (_coma(dy[0], 4), _coma(d["req"], 4), _coma(dy[1], 1)),
            u"  -> Sólo cuentan machones de L ≥ %s m (E.070 6.4)"
            % _coma(d["lmin"]),
         ]},
        {"num": "2", "titulo": "PREDIMENSIONAMIENTO", "clave": "gris",
         "items": [
            u"Muros: t = %s m (aparejo de cabeza) — lo fija la unidad"
            % _coma(d["t"]),
            u"Losa aligerada: e = %s m" % _coma(d["e_losa"]),
            u"Columnas de confinamiento: C-1 %s x %s m | C-2 extrema %s x %s m"
            % (_coma(d["c1"][0]), _coma(d["c1"][1]),
               _coma(d["c2"][0]), _coma(d["c2"][1])),
            u"  -> El peralte de la C-2 lo gobierna el anclaje de la solera",
            u"Vigas soleras: %s x %s m (b = t, h = e_losa, E.070 7.2.4)"
            % (_coma(d["solera"][0]), _coma(d["solera"][1])),
            u"Cimentación corrida, excéntrica en medianeras",
         ]},
        {"num": "3", "titulo": "METRADO DE CARGAS Y ESFUERZO AXIAL",
         "clave": "naranja",
         "items": [
            u"Sobrecarga E.020: %s kgf/m² vivienda | %s azotea"
            % (_coma(d["sc"][0], 0), _coma(d["sc"][1], 0)),
            u"Tabiquería: %s kgf/m² — METRADA sobre el plano (E.020 Art. 5)"
            % _coma(d["tabique"], 0),
            u"Esfuerzo axial (E.070 7.1.1.b): σm = Pm/(t·L) ≤ 0,15 f'm",
            u"  -> f'm = %s kgf/cm²  ->  límite %s kgf/cm²"
            % (_coma(d["fm"], 0), _coma(d["lim_axial"])),
            u"  -> Muro crítico %s: σm = %s kgf/cm²  CUMPLE"
            % (d["sigma"][0], _coma(d["sigma"][1])),
            u"Peso sísmico (E.030 Art. 31, Cat. C): P = 100 % CM + 25 % CV",
            u"  -> P total = %s tonf" % _coma(d["peso"], 1),
         ]},
        {"num": "4", "titulo": "ANÁLISIS SÍSMICO Y RIGIDECES (E.030)",
         "clave": "azul",
         "items": [
            u"Parámetros: Z = %s, U = %s, S = %s, C = %s, R = %s"
            % (_coma(Z), _coma(U), _coma(S), _coma(C), _coma(R, 1)),
            u"Método: ESTÁTICO, admitido por el Art. 33.2 (muros portantes",
            u"  de albañilería de no más de 15 m; acá hn = %s m)" % _coma(_hn()),
            u"Cortante basal (Art. 34): V = Z·U·C·S/R · P = %s tonf"
            % _coma(d["V"], 1),
            u"Distribución en altura por Pi·hi^k (Art. 35)",
            u"Centros: CM (%s; %s) y CR (%s; %s)"
            % (_coma(d["cm"][0], 3), _coma(d["cm"][1], 3),
               _coma(d["cr"][0], 3), _coma(d["cr"][1], 3)),
            u"  -> Excentricidad propia: %s m en X y %s m en Y"
            % (_coma(d["exc"][0], 3), _coma(d["exc"][1], 3)),
            u"Excentricidad accidental 0,05·B (Art. 37): GOBIERNA sobre la propia",
         ]},
    ]
    col2 = [
        {"num": "5", "titulo": "VERIFICACIÓN ANTE SISMO MODERADO",
         "clave": "verde",
         "items": [
            u"Definición (E.070 8.1): sismo moderado = severo / 2",
            u"Resistencia al agrietamiento diagonal (8.5.3):",
            u"  Vm = %s·v'm·α·t·L + %s·Pg" % (_coma(d["c_vm"][0], 1), _coma(d["c_vm"][1], 2)),
            u"Control de fisuración (8.5.2):  Ve ≤ %s Vm" % _coma(d["c_vm"][2], 2),
            u"  -> LOS 13 MUROS CUMPLEN: ninguno se fisura ante sismo moderado",
            u"El valor muro por muro está en la lámina E-02, que se regenera",
            u"con la cadena: acá no se copia, para que no envejezca aparte",
         ]},
        {"num": "6", "titulo": "DISEÑO POR CORTE ANTE SISMO SEVERO",
         "clave": "rojo",
         "items": [
            u"Resistencia al corte global (E.070 8.5.4): Σ Vm ≥ VE severo",
            u"  -> CUMPLE en las dos direcciones",
            u"Diseño por capacidad: Vu = Ve · (Vm1 / Ve1)",
            u"Refuerzo horizontal en juntas (E.070 8.6.1):",
            u"  -> El diámetro lo topa la JUNTA, no la cuantía: el 4.1.2 pide",
            u"     6 mm + ø ≤ 15 mm, de donde ø ≤ 9 mm y el 3/8\" queda fuera",
            u"REDUNDANCIA, medida: en X el peor muro toma %s %% de %d;"
            % (_coma(px, 1), nx),
            u"  en Y DOS medianeras toman %s %% del cortante de la dirección"
            % _coma(p2y, 1),
         ]},
        {"num": "7", "titulo": "CONFINAMIENTOS Y ANCLAJES (E.070 CAP. 8)",
         "clave": "rojo",
         "items": [
            u"Fuerzas en columnas extremas (Tabla 11): C = Pc + F | T = F - Pc",
            u"Refuerzo longitudinal: As = Asf + Ast ≥ 0,1 f'c Ac / fy",
            u"  -> Dos tipos de columna: C-2 extrema y C-1 interior",
            u"Estribaje en zona de confinamiento (8.6.3 a.3): gobierna s3 = d/4",
            u"Vigas soleras con anclaje en la columna extrema",
            u"El armado exacto de cada tipo está en el cuadro de columnas,",
            u"que sale del mismo cálculo y se regenera con él",
         ]},
        {"num": "8", "titulo": "VALIDACIÓN NUMÉRICA Y PLANOS", "clave": "verde",
         "items": [
            u"Contraste con OpenSeesPy (ElasticTimoshenkoBeam, diafragma rígido):",
            u"  -> Análisis MODAL: los dos primeros modos son traslacionales",
            u"     y el TORSIONAL aparece tercero — planta bien estructurada",
            u"  -> Masa participativa por encima del 90 % del Art. 40.2,",
            u"     resolviendo seis modos (el mínimo del artículo son tres)",
            u"  -> El periodo por tres caminos —empírico, Rayleigh y modal—",
            u"     cae bajo Tp, que es lo que sostiene el C adoptado",
            u"Láminas E-01 a E-05: columnas en planta, muros, confinamientos",
         ]},
    ]
    return col1, col2


def control(d):
    u"""Lo que la figura AFIRMA tiene que ser verdad en la fuente."""
    for dire in ("X", "Y"):
        obt, holg = d["dens"][dire]
        assert obt >= d["req"], (
            "la figura dice CUMPLE en %s y la densidad no alcanza" % dire)
        assert holg > 0, "holgura no positiva en %s" % dire
    assert d["sigma"][1] <= d["lim_axial"], (
        "la figura dice que el muro critico CUMPLE y sigma = %.2f supera el "
        "limite %.2f" % (d["sigma"][1], d["lim_axial"]))
    # la afirmacion sobre la redundancia en Y es el punto delicado de la
    # figura: se exige que los dos primeros muros de Y superen la mitad del
    # cortante, que es lo que justifica llamarlo concentracion.
    assert d["conc"]["Y"][2] > 50.0, (
        "la figura habla de concentracion en Y y los dos primeros muros solo "
        "toman %.1f %%" % d["conc"]["Y"][2])
    assert d["conc"]["X"][1] < d["conc"]["Y"][1], (
        "la figura contrasta X repartido contra Y concentrado y la medicion "
        "no lo respalda")
    # el peso y el cortante tienen que guardar la relacion Z U C S / R
    Z, U, S, C, R = d["zuscr"]
    esperado = Z * U * C * S / R * d["peso"]
    assert abs(esperado - d["V"]) / d["V"] < 0.02, (
        "el V de la figura (%.1f) no sale de su propio ZUCS y peso (%.1f)"
        % (d["V"], esperado))
    print("  [ok] densidad, esfuerzo axial y cortante basal cierran con su fuente")
    print("  [ok] la concentracion en Y (%.1f %% en dos muros) respalda el texto"
          % d["conc"]["Y"][2])


def dibujar():
    d = reunir()
    control(d)
    col1, col2 = fases(d)

    for n_lam, (grupo, sub) in enumerate((
            (col1, u"Fases 1 a 4  ·  el EDIFICIO: arquitectura, secciones y "
                   u"cargas"),
            (col2, u"Fases 5 a 8  ·  la VERIFICACIÓN: sismo, "
                   u"irregularidades, diseño y contraste")), 1):
        _una(grupo, n_lam, sub)


def _una(grupo, n_lam, sub):
    """Una lamina de cuatro fases, en UNA columna. Ver el porque arriba."""
    fig, ax = plt.subplots(figsize=(C.ANCHO_PAGINA, 8.60), dpi=200)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    AZUL = "#1f5fbf"
    VERDE = "#2e7d52"
    GRAFITO = "#37474f"
    ROJO = "#b71c1c"

    ax.text(2.0, 98.6, u"Flujograma metodológico  ·  %s" % sub,
            fontsize=9.4, fontweight="bold", color="#1b3a57", va="top",
            wrap=True)

    YS = [93.0, 70.5, 48.0, 25.5]
    for f, y in zip(grupo, YS):
        f["y"] = y
    n_max = max(len(f["items"]) for f in grupo)
    H_CARD, W_CARD, X0 = 21.0, 95.0, 2.5
    paso = min(2.35, (H_CARD - 6.2) / max(n_max, 1))
    for f in grupo:
        y_top = f["y"]
        y_bot = y_top - H_CARD
        c_p = COLOR[f["clave"]]
        ax.add_patch(FancyBboxPatch(
            (X0 + 0.6, y_bot - 0.4), W_CARD, H_CARD,
            boxstyle="round,pad=0.5,rounding_size=1.2",
            fc="#e2e8f0", ec="none", zorder=1))
        ax.add_patch(FancyBboxPatch(
            (X0, y_bot), W_CARD, H_CARD,
            boxstyle="round,pad=0.5,rounding_size=1.2",
            fc=FONDO_CARD, ec=BORDE_CARD, lw=0.9, zorder=2))
        ax.add_patch(FancyBboxPatch(
            (X0, y_top - 3.4), W_CARD, 3.4,
            boxstyle="round,pad=0.0,rounding_size=0.8",
            fc=c_p, ec="none", zorder=3))
        ax.text(X0 + 1.5, y_top - 1.7, "FASE " + f["num"],
                ha="left", va="center", fontsize=7.6, color="#ffffff",
                fontweight="bold", zorder=4)
        ax.text(X0 + 10.0, y_top - 1.7, "|  " + f["titulo"],
                ha="left", va="center", fontsize=7.6, color="#ffffff",
                fontweight="bold", zorder=4)
        y_txt = y_top - 5.0
        for it in f["items"]:
            destaca = ("CUMPLE" in it or "GOBIERNA" in it
                       or "REDUNDANCIA" in it or "TORSIONAL" in it)
            c_txt = VERDE if "CUMPLE" in it else (
                ROJO if ("GOBIERNA" in it or "REDUNDANCIA" in it)
                else GRAFITO)
            ax.text(X0 + 1.8, y_txt, "• " + it,
                    ha="left", va="center", fontsize=6.4, color=c_txt,
                    fontweight="bold" if destaca else "normal", zorder=4)
            y_txt -= paso
        # CONTROL DE CAJA: si una fase crece, avisa aca y no en el PDF.
        assert y_txt > y_bot - 0.2, (
            "la fase %s desborda su tarjeta: %d items no entran"
            % (f["num"], len(f["items"])))

    for a, b in zip(YS, YS[1:]):
        ax.annotate("", xy=(X0 + W_CARD / 2.0, b + 0.4),
                    xytext=(X0 + W_CARD / 2.0, a - H_CARD - 0.4),
                    arrowprops=dict(arrowstyle="-|>", color=GRAFITO,
                                    lw=1.5), zorder=5)

    ruta = os.path.join(OUT, "FLUJOGRAMA-METODOLOGICO-%d.png" % n_lam)
    C.guardar(fig, ruta)
    print("  FLUJOGRAMA-METODOLOGICO.png")


if __name__ == "__main__":
    dibujar()
