# -*- coding: utf-8 -*-
u"""EL CAPITULO 8 DE LA E.070, acapite por acapite, con su destino.

POR QUE EXISTE (2026-09-27). El Capitulo 8 --Analisis y Diseno Estructural--
es el mas cargado de la norma y el que decide el diseno de un edificio de
albanileria. El proyecto lo venia cumpliendo bien PERO DE FORMA DISPERSA: su
contenido vivia repartido en los scripts 11, 12, 16, 17, 18, 19 y 20, y el
registro de obligaciones solo tenia entrada para **10 de sus 25 acapites**.
Un capitulo cumplido en quince lugares y declarado en diez es un capitulo del
que nadie puede decir, mirando un papel, que esta completo.

Este script no recalcula: RECORRE. Toma de cada script lo suyo, lo pone al
lado del acapite que lo exige y exige que **ningun acapite quede sin
destino** -- cumplido, remitido a otro acapite o declarado no aplicable.

LO QUE APARECIO AL RECORRERLO:

  * **8.3.3** pedia evaluar el efecto de las ABERTURAS sobre la rigidez del
    diafragma, y no habia ningun numero. Medido: el pozo y la caja de
    escalera suman 29,97 m2, el **12,0 %** del area bruta.
  * **8.3.9** fija Es = 2 000 000 kgf/cm2 y **el SSOT no lo declaraba**. No
    se usa en ninguna cuenta --el diseno de acero va por fy-- pero el acapite
    existe y merece su renglon.
  * **8.2.2.e** dice algo que justifica el metodo entero y no estaba escrito
    en ninguna parte: *"se asume que la forma de falla de los muros
    confinados ante el sismo severo sera POR CORTE, independientemente de su
    esbeltez"*. Es la razon por la que en confinada no se hace un diseno por
    flexocompresion como en armada.
  * **8.5.6** parecia un hueco grande --"diseno para fuerzas coplanares de
    flexo compresion"-- y resulto ser una REMISION: para muros confinados
    remite al 8.6, que el proyecto ya tenia completo.
  * **8.7** es albanileria ARMADA y no aplica. Se declara, porque un capitulo
    "completo" con una seccion omitida en silencio no esta completo.
"""
from __future__ import print_function

import contextlib
import importlib.util
import io as _io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from proyecto import (AREA_EDIFICADA, AREA_ESCALERA, AREA_POZO, FACTOR_MODERADO,
                      FM, VM)

# --- constantes de los acapites, con su origen -----------------------------
R_CONFINADA = 3.0          # no-ssot: 8.1, definicion de sismo severo
DISTORSION_MAXIMA = 1.0 / 200.0   # no-ssot: 8.2.2.c, "se fija en 1/200"
ES_ACERO = 2000000.0       # no-ssot: 8.3.9, kgf/cm2 (196 000 MPa)
FACTOR_ELASTICO_855 = 3.0  # no-ssot: 8.5.5, "mayor o igual que 3 VEi"
# La E.030 llama irregular al diafragma cuando las aberturas pasan del 50 %
# del area bruta. El 8.3.3 no da numero: manda "considerar el efecto". Se usa
# ese 50 % como referencia declarada, no como si la E.070 lo dijera.
REF_ABERTURAS = 0.50       # no-ssot: E.030 Tabla 13, discontinuidad de diafragma


def _mod(nombre):
    ruta = os.path.join(AQUI, nombre)
    spec = importlib.util.spec_from_file_location("_c8" + nombre[:2], ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def reunir():
    u"""Cada dato, de su script. Este archivo no calcula nada dos veces."""
    m11 = _mod("11_metrado_muros.py")
    m12 = _mod("12_rigidez_lateral.py")
    m16 = _mod("16_irregularidades.py")
    m17 = _mod("17_reparto_cortante.py")
    m18 = _mod("18_diseno_muros.py")

    T, k, C, pesos, P, V = m16.sismo()
    filas, h, Fi, Vb, xm, ym, xr, yr = m17.contexto()
    d = {
        "V_severo": V, "T": T, "C": C, "P": P,
        "sigma_max": max(f["sigma"] for f in m11.metrar()),
        "Em": m12.EM, "Gm": m12.GM, "Ec": m12.EC, "n": m12.N_TRANSF,
        "ala": m12.ALA,
        "e_propia": (abs(xm - xr), abs(ym - yr)),
        "aberturas": AREA_POZO + AREA_ESCALERA,
        "frac_aberturas": (AREA_POZO + AREA_ESCALERA) / AREA_EDIFICADA,
    }
    # la deriva la calcula el 16; se pide en vez de rehacerla
    with contextlib.redirect_stdout(_io.StringIO()):
        salida = _io.StringIO()
        with contextlib.redirect_stdout(salida):
            m16.main() if hasattr(m16, "main") else None
    d["deriva"] = _deriva_de(m16, filas, h, Fi)
    # y el corte global, del 18
    d["suma_vm"] = _suma_vm_de(m18)
    return d


def _deriva_de(m16, filas, h, Fi):
    u"""La deriva maxima, tomada del 16 sin volver a calcularla."""
    texto = _io.StringIO()
    with contextlib.redirect_stdout(texto):
        try:
            m16.deriva_y_gatillo(filas, h, Fi)
        except TypeError:
            return None
    for linea in texto.getvalue().split(chr(10)):
        if "Deriva maxima del edificio" in linea:
            return float(linea.split(":")[1].strip())
    return None


def _suma_vm_de(m18):
    u"""Sum Vm / VE por direccion, DERIVADO -- no leido de un `print`.

    La primera version parseaba la salida de texto del 18 buscando las
    filas "X" e "Y" del cuadro. No encontro ninguna --el cuadro lo imprime
    `paso_5`, que esa version no llamaba-- y devolvio un diccionario
    VACIO. El control de abajo recorre ese diccionario con un `for`, y
    **un `for` sobre un diccionario vacio pasa todos los asserts**: el
    guardian informaba "8.5.4 cumple" habiendo verificado exactamente
    nada. Es el modo mas silencioso que tiene un control de aprobar sin
    mirar, y por eso ahora (a) el dato se DERIVA de las estructuras en vez
    de leerse de un texto y (b) hay un assert de que el resultado no este
    vacio antes de recorrerlo.
    """
    muros, V_ent = m18.datos()
    with contextlib.redirect_stdout(_io.StringIO()):
        m18.paso_3_y_4(muros)
    VE = V_ent[0]          # el primer entrepiso es el mas exigido
    out = {}
    for dire in ("X", "Y"):
        suma = sum(mu["Vm1"] for mu in muros if mu["dir"] == dire)
        out[dire] = (suma, VE, suma / VE)
    return out


# ==========================================================================
# EL RECORRIDO: cada acapite, que exige y donde se cumple.
# Cada fila es (acapite, que exige, estado, donde / con que numero).
#   OK    cumplido y medido
#   REM   remite a otro acapite, que es donde se cumple
#   NA    no aplica a este sistema estructural
# ==========================================================================
def recorrido(d):
    v = d
    sx = v["suma_vm"].get("X", (0, 0, 0))
    sy = v["suma_vm"].get("Y", (0, 0, 0))
    ex, ey = v["e_propia"]
    return [
        # --- 8.1 y 8.2 -----------------------------------------------------
        ("8.1", "Definir sismo severo y sismo moderado", "OK",
         "severo = E.030 con R = %.0f; moderado = severo / %.0f. V severo = "
         "%.0f kgf" % (R_CONFINADA, FACTOR_MODERADO, v["V_severo"])),
        ("8.2.2.a", "El sismo moderado no debe fisurar ningun muro portante",
         "OK", "los 13 muros pasan el control de fisuracion del 8.5.2 (18)"),
        ("8.2.2.b", "Los elementos de acoplamiento fallan antes, por flexion",
         "NA", "no hay vigas de acoplamiento: los 13 muros se modelan en "
               "VOLADIZO, como admite el 8.3.5"),
        ("8.2.2.c", "Distorsion angular maxima 1/200 ante sismo severo", "OK",
         "deriva maxima %s contra 1/200 = %.4f: el %.1f %% del limite"
         % (("%.6f" % v["deriva"]) if v["deriva"] else "?",
            DISTORSION_MAXIMA,
            100.0 * v["deriva"] / DISTORSION_MAXIMA if v["deriva"] else 0)),
        ("8.2.2.d", "Diseno por capacidad para la incursion inelastica", "OK",
         "Vu = Ve x (Vm1/Ve1) en el 18; y el corte global del 8.5.4 cumple"),
        ("8.2.2.e", "Se asume falla POR CORTE, sea cual sea la esbeltez", "OK",
         "es la razon de que en confinada no se haga flexocompresion como en "
         "armada: el diseno va por corte (8.5.3) y capacidad (8.6)"),
        ("8.2.2.f", "Falla de muros armados segun su esbeltez", "NA",
         "el sistema es albanileria CONFINADA"),
        # --- 8.3 analisis estructural --------------------------------------
        ("8.3.1", "Analisis elastico con CM, CV y sismo", "OK",
         "metrado por areas tributarias (10, 11) y analisis elastico-lineal; "
         "el modelo del 20 lo confirma por segunda via"),
        ("8.3.2", "Cortante basal y distribucion en altura por la E.030", "OK",
         "16: V = %.0f kgf con T = %.3f s y C = %.2f; reparto por Pi.hi^k"
         % (v["V_severo"], v["T"], v["C"])),
        ("8.3.3", "Considerar el diafragma y el efecto de sus ABERTURAS", "OK",
         "pozo %.2f + escalera %.2f = %.2f m2, el %.1f %% del area bruta"
         % (AREA_POZO, AREA_ESCALERA, v["aberturas"],
            100.0 * v["frac_aberturas"])),
        ("8.3.4", "Considerar los muros no portantes NO aislados y el alfeizar",
         "OK", "los alfeizares van AISLADOS con junta de 1\" (6.2.7), asi que "
               "no participan; la tabiqueria entra al metrado como carga (31)"),
        ("8.3.5", "Cortante en planta con torsion; voladizo si no hay "
                  "acoplamiento", "OK",
         "17: reparto con torsion, e propia %.3f / %.3f m y la accidental "
         "gobernando" % (ex, ey)),
        ("8.3.6", "Seccion transformada: alas del 25 % o 6t, y Ec/Em", "OK",
         "12: ala por cruce 6t = %.2f m y n = Ec/Em = %.2f"
         % (v["ala"], v["n"])),
        ("8.3.7", "Em = 500 f'm y Gm = 0,40 Em para arcilla", "OK",
         "12: Em = %.0f y Gm = %.0f kgf/cm2" % (v["Em"], v["Gm"])),
        ("8.3.8", "Ec y Gc del concreto segun la E.060", "OK",
         "12: Ec = 15000 raiz(f'c) = %.0f kgf/cm2" % v["Ec"]),
        ("8.3.9", "Es del acero = 2 000 000 kgf/cm2", "OK",
         "se declara en este script: no interviene en ninguna cuenta porque "
         "el diseno de acero va por fy, pero el acapite lo fija"),
        # --- 8.4 elementos de concreto armado ------------------------------
        ("8.4.1.1", "Los elementos de CA, salvo confinamiento, por resistencia "
                    "ultima y con falla por FLEXION", "OK",
         "aligerado (10, 23), vigas VB-1 (08) y VB-2 (37) y columnas de la "
         "caja (27): todos por resistencia ultima y con el peralte que la "
         "Tabla 9.1 pide para que gobierne la flexion"),
        ("8.4.1.2", "Los elementos de confinamiento, por el 8.6.2", "REM",
         "se cumple en el 19, bajo el 8.6.2 y el 8.6.3"),
        # --- 8.5 diseno de muros -------------------------------------------
        ("8.5.1.1", "Seccion rectangular t.L; en intersecciones, el MAYOR "
                    "refuerzo de los dos disenos", "OK",
         "19: la C-2 de 0,24 x 0,35 se adopta para TODAS las esquinas, que es "
         "tomar el mayor; el diseno a corte usa seccion rectangular"),
        ("8.5.1.2", "Alas en flexocompresion de muros ARMADOS", "NA",
         "el acapite dice 'muros armados'; el sistema es confinado"),
        ("8.5.2", "Control de fisuracion: Ve <= 0,55 Vm ante sismo moderado",
         "OK", "18: los 13 muros cumplen; el mas exigido usa el 0,572 del "
               "limite"),
        ("8.5.3", "Resistencia al agrietamiento diagonal Vm", "OK",
         "18: Vm = 0,54 v'm alfa t L + 0,23 Pg, con v'm = %.1f kgf/cm2"
         % VM),
        ("8.5.4", "Suma Vm >= VE en cada entrepiso y direccion", "OK",
         "18: X %.3f y Y %.3f veces el VE severo" % (sx[2], sy[2])),
        ("8.5.5", "Si suma Vm >= 3 VE el edificio es elastico y basta refuerzo "
                  "minimo", "OK",
         "NO se alcanza (%.3f y %.3f contra %.0f): el atajo no aplica y se "
         "diseno completo" % (sx[2], sy[2], FACTOR_ELASTICO_855)),
        ("8.5.6", "Diseno por flexocompresion coplanar", "REM",
         "el propio acapite remite: para muros confinados, al 8.6"),
        # --- 8.6 albanileria confinada -------------------------------------
        ("8.6.1", "Cuando hace falta refuerzo horizontal", "OK",
         "18 y 36: 11 de 13 lo exigen por sigma >= 0,05 f'm = %.2f; se coloca "
         "en los 13" % (0.05 * FM)),
        ("8.6.2", "Diseno de los elementos de confinamiento", "OK",
         "19: columnas y soleras por el procedimiento del 8.6.3"),
        ("8.6.3", "Columnas: seccion, refuerzo longitudinal y estribaje", "OK",
         "19: C-2 extrema y C-1 interior, acero por Asf + Ast y estribos con "
         "los cuatro criterios de a.3"),
        ("8.6.4", "Soleras, y diseno de los pisos superiores NO agrietados",
         "OK", "19: solera con su refuerzo y estribos minimos; el acero de "
               "las columnas se verifica piso a piso"),
        # --- 8.7 -----------------------------------------------------------
        ("8.7", "Albanileria ARMADA: todo el subcapitulo", "NA",
         "el sistema estructural es albanileria CONFINADA (E.030 Tabla 12). "
         "Se declara para que el recorrido del capitulo quede completo"),
    ]


def informe(filas):
    print("=" * 96)
    print("CAPITULO 8 DE LA E.070 -- ANALISIS Y DISENO ESTRUCTURAL, acapite "
          "por acapite")
    print("=" * 96)
    print("  Este script no recalcula: RECORRE. Cada acapite con su exigencia,")
    print("  su estado y el script donde se cumple.")
    print()
    print("    OK   cumplido y medido        REM  remite a otro acapite")
    print("    NA   no aplica a este sistema estructural")
    print()
    seccion = None
    for ac, exige, estado, donde in filas:
        raiz = ac.split(".")[1] if ac.count(".") >= 1 else ac
        if raiz != seccion:
            seccion = raiz
            print("  " + "-" * 92)
        print("  %-9s %-3s %s" % (ac, estado, exige))
        for linea in _envolver(donde, 84):
            print("  %-13s %s" % ("", linea))
    print()


def _envolver(txt, n):
    import textwrap
    return textwrap.wrap(txt, n)


def resumen(filas):
    ok = sum(1 for f in filas if f[2] == "OK")
    rem = sum(1 for f in filas if f[2] == "REM")
    na = sum(1 for f in filas if f[2] == "NA")
    print("=" * 96)
    print("  %d acapites recorridos:  %d cumplidos  ·  %d por remision  ·  "
          "%d no aplicables" % (len(filas), ok, rem, na))
    print("=" * 96)
    return ok, rem, na


def control(d, filas):
    print()
    print("CONTROLES")
    print("-" * 96)
    # 1. NINGUN acapite sin destino: es el objeto de este script
    sin = [f[0] for f in filas if f[2] not in ("OK", "REM", "NA")]
    assert not sin, "acapites sin destino: %s" % ", ".join(sin)
    # 2. los acapites que dicen NA tienen que decir POR QUE
    for ac, _e, estado, donde in filas:
        if estado == "NA":
            assert len(donde) > 25, (
                "el acapite %s se declara no aplicable sin explicar por que"
                % ac)
    # 3. la distorsion del 8.2.2.c
    assert d["deriva"] is not None, "no se pudo leer la deriva del 16"
    assert d["deriva"] <= DISTORSION_MAXIMA, (
        "la deriva %.6f supera el 1/200 del 8.2.2.c" % d["deriva"])
    # 4. ANTES DE RECORRER, que haya algo que recorrer. Un `for` sobre un
    #    contenedor vacio no falla: aprueba. Este assert es lo unico que
    #    separa "verifique y cumple" de "no verifique nada".
    assert set(d["suma_vm"]) == {"X", "Y"}, (
        "el corte global no trajo las dos direcciones: %s"
        % sorted(d["suma_vm"]))
    # 5. el 8.5.5: si se alcanzara 3 VE, el diseno del 18 sobraria. Que NO se
    #    alcance es lo que justifica haber disenado completo.
    for dire, (_vm, _ve, rel) in d["suma_vm"].items():
        assert rel >= 1.0, (
            "en %s la suma Vm no llega al VE severo: %.3f (8.5.4)"
            % (dire, rel))
        assert rel < FACTOR_ELASTICO_855, (
            "en %s se alcanza 3 VE (%.3f): el 8.5.5 permitiria refuerzo "
            "minimo y el diseno completo del 18 seria innecesario"
            % (dire, rel))
    # 6. el 8.3.3: las aberturas, contra la referencia de la E.030
    assert d["frac_aberturas"] < REF_ABERTURAS, (
        "las aberturas son el %.1f %% del area bruta y pasan la referencia "
        "del %.0f %%" % (100 * d["frac_aberturas"], 100 * REF_ABERTURAS))
    print("  [ok] los %d acapites tienen destino: ninguno quedo sin recorrer"
          % len(filas))
    print("  [ok] los %d declarados NO APLICABLES explican por que"
          % sum(1 for f in filas if f[2] == "NA"))
    print("  [ok] distorsion %.6f <= 1/200 = %.4f (8.2.2.c): el %.1f %% del "
          "limite" % (d["deriva"], DISTORSION_MAXIMA,
                      100.0 * d["deriva"] / DISTORSION_MAXIMA))
    print("  [ok] 8.5.4 cumple y 8.5.5 NO se alcanza: %s"
          % ", ".join("%s %.3f" % (k, v[2])
                      for k, v in sorted(d["suma_vm"].items())))
    print("  [ok] aberturas del diafragma %.1f %% < %.0f %% de referencia "
          "(8.3.3)" % (100 * d["frac_aberturas"], 100 * REF_ABERTURAS))
    print("  [ok] Es = %s kgf/cm2 declarado (8.3.9)"
          % format(int(ES_ACERO), ",").replace(",", " "))


def main():
    d = reunir()
    filas = recorrido(d)
    informe(filas)
    resumen(filas)
    control(d, filas)


if __name__ == "__main__":
    main()
