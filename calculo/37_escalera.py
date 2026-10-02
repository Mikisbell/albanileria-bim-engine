# -*- coding: utf-8 -*-
u"""Predimensionamiento de la ESCALERA y de la viga de borde de su hueco.

POR QUE EXISTE (2026-09-27). Era el ultimo pendiente del criterio 2 y el
unico del tablero que no traia excusa al lado: "e4 -- predimensionado de la
escalera -- pendiente". El codigo lo confirmaba: el paso y el contrapaso
tenian su articulo y su verificacion, pero `E_LOSA_ESCALERA = 0,15` estaba
escrito con el comentario "losa inclinada" y nada mas. **Elegido, no
calculado.** Este script lo calcula, dimensiona la viga que faltaba en el
borde del hueco y declara lo que el metrado ya hacia sin decirlo.

TRES COSAS APARECIERON AL HACERLO, y ninguna se veia desde afuera:

1. **LA CITA DEL PASO Y EL CONTRAPASO ESTABA MAL ATRIBUIDA.** El SSOT decia
   "A.010 Art. 29: el paso no sera menor de 0,25 m ni el contrapaso mayor de
   0,18". En la A.010 de 2021 el **Articulo 29 es "Escaleras Abiertas (B3)"**;
   el paso y el contrapaso viven en el **Articulo 23.2**, incisos b) y c).
   El numero estaba bien y el articulo no. Es la misma familia del Art. 24.5
   de la E.070: una cita valida apuntando al lugar equivocado.

2. **EL ESPESOR DE 0,15 RESULTO SER EL CORRECTO**, pero por poco y por un
   camino que nadie habia escrito: con la luz de 2,76 m y la Tabla 9.1 de la
   E.060 para losa maciza simplemente apoyada, el minimo es L/20 = 0,138 m.
   Queda un 8,7 % de holgura. Si alguien hubiera puesto 0,12 "porque se ve
   bien", tambien habria parecido razonable y no habria cumplido.

3. **EL DESCANSO DEPENDE DE COMO SE LEA EL 23.2.a**, y las dos lecturas no
   dan lo mismo. Se reporta con las dos y se declara cual se adopta, en vez
   de elegir la que conviene y callar la otra.
"""
from __future__ import print_function

import contextlib
import importlib.util
import io as _io
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from proyecto import (ANCHO_TRAMO_ESCALERA, AREA_ESCALERA, CONTRAPASO_ESCALERA,
                      ESC_X0, ESC_X1, ESC_Y0, ESC_Y1, ESPESOR, E_LOSA,
                      E_LOSA_ESCALERA, H_ENTREPISO, N_CONTRAPASOS,
                      PASO_ESCALERA, PESO_CONCRETO, SC_VIVIENDA,
                      peso_escalera_m2)

# --- constantes de los acapites, con su origen -----------------------------
PASO_MINIMO = 0.25        # no-ssot: A.010 23.2.b, vivienda
CONTRAPASO_MAXIMO = 0.18  # no-ssot: A.010 23.2.c
PASOS_MAX_ENTRE_DESCANSOS = 17   # no-ssot: A.010 23.2.a
DIV_LOSA_MACIZA_SIMPLE = 20.0    # no-ssot: E.060 Tabla 9.1, losa maciza en una
                                 # direccion simplemente apoyada (L/20)
DIV_VIGA_SIMPLE = 16.0           # no-ssot: E.060 Tabla 9.1, viga simplemente
                                 # apoyada (L/16); el mismo divisor que el 08
                                 # usa para la VB-1 del pozo


def _mod(nombre):
    ruta = os.path.join(AQUI, nombre)
    spec = importlib.util.spec_from_file_location("_e" + nombre[:2], ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def geometria():
    u"""Lo que define la escalera, derivado del SSOT."""
    n_tramos = 2
    cp_por_tramo = N_CONTRAPASOS // n_tramos
    # un tramo con n contrapasos tiene n-1 pasos: el ultimo "paso" es el
    # descanso al que llega. Contar n pasos alarga el tramo 25 cm de mas y
    # es el error clasico de esta cuenta.
    pasos_por_tramo = cp_por_tramo - 1
    return {
        "n_tramos": n_tramos,
        "cp_por_tramo": cp_por_tramo,
        "pasos_por_tramo": pasos_por_tramo,
        "proyeccion_tramo": pasos_por_tramo * PASO_ESCALERA,
        "sube_tramo": cp_por_tramo * CONTRAPASO_ESCALERA,
        "ancho_caja": ESC_X1 - ESC_X0,
        "largo_caja": ESC_Y1 - ESC_Y0,
    }


# ==========================================================================
def arquitectura(g):
    print("=" * 78)
    print("1. GEOMETRIA DE LA ESCALERA  -  A.010 Art. 23.2")
    print("=" * 78)
    print("  OJO CON LA CITA: el SSOT decia 'A.010 Art. 29'. En la A.010 de")
    print("  2021 el Art. 29 es 'Escaleras Abiertas (B3)'; el paso y el")
    print("  contrapaso son el **Art. 23.2**, incisos b) y c).")
    print()
    print("  Caja                      %.2f x %.2f m   (%.2f m2)"
          % (g["ancho_caja"], g["largo_caja"], AREA_ESCALERA))
    print("  Tramos                    %d, de %d contrapasos cada uno"
          % (g["n_tramos"], g["cp_por_tramo"]))
    print("  Cada tramo sube           %.3f m  (media altura de entrepiso "
          "%.2f / 2 = %.3f)" % (g["sube_tramo"], H_ENTREPISO,
                                H_ENTREPISO / 2.0))
    print("  Proyeccion del tramo      %.2f m  (%d pasos, no %d: el ultimo"
          % (g["proyeccion_tramo"], g["pasos_por_tramo"], g["cp_por_tramo"]))
    print("                                   contrapaso llega al descanso)")
    print()
    print("  %-34s %10s %10s  %s" % ("condicion", "exige", "proyecto", "veredicto"))
    print("  " + "-" * 74)
    filas = [
        ("Paso minimo (23.2.b, vivienda)", PASO_MINIMO, PASO_ESCALERA,
         PASO_ESCALERA >= PASO_MINIMO, "m"),
        ("Contrapaso maximo (23.2.c)", CONTRAPASO_MAXIMO,
         CONTRAPASO_ESCALERA, CONTRAPASO_ESCALERA <= CONTRAPASO_MAXIMO, "m"),
        ("Pasos entre descansos (23.2.a)", PASOS_MAX_ENTRE_DESCANSOS,
         g["pasos_por_tramo"], g["pasos_por_tramo"] <= PASOS_MAX_ENTRE_DESCANSOS,
         ""),
    ]
    for nombre, exige, tiene, ok, u in filas:
        print("  %-34s %8.3f %s %8.3f %s  %s"
              % (nombre, exige, u or " ", tiene, u or " ",
                 "cumple" if ok else "*** NO CUMPLE ***"))
    return filas


def descanso(g):
    u"""23.2.a -- el acapite admite dos lecturas y hay que decir cual se usa.

    Texto literal: "Para escaleras LINEALES la LONGITUD minima del descanso
    es de 0,90 m y para otros tipos de escaleras el ANCHO del descanso es
    igual o mayor al del tramo".

    La norma usa dos palabras distintas a proposito: *longitud* para la
    dimension en el sentido del recorrido y *ancho* para la transversal. Esta
    escalera es de dos tramos --no lineal--, asi que le corresponde la
    condicion de ANCHO. Aun asi se reporta tambien la longitud, porque es la
    lectura que un revisor exigente puede pedir y conviene tener el numero.
    """
    print()
    print("=" * 78)
    print("2. EL DESCANSO  -  A.010 23.2.a, y sus dos lecturas")
    print("=" * 78)
    ancho_desc = g["ancho_caja"]
    largo_desc = g["largo_caja"] - g["proyeccion_tramo"]
    print("  El acapite distingue: para escaleras LINEALES pide LONGITUD")
    print("  minima de 0,90 m; para OTROS TIPOS pide que el ANCHO del")
    print("  descanso sea igual o mayor al del tramo. Son dos palabras")
    print("  distintas y no significan lo mismo.")
    print()
    print("  Esta escalera es de DOS TRAMOS: le corresponde la de ANCHO.")
    print()
    ok_ancho = ancho_desc >= ANCHO_TRAMO_ESCALERA
    ok_largo = largo_desc >= ANCHO_TRAMO_ESCALERA
    print("  LECTURA QUE CORRESPONDE  (ancho, transversal al recorrido)")
    print("    ancho del descanso %.2f m  >=  ancho del tramo %.2f m  -> %s"
          % (ancho_desc, ANCHO_TRAMO_ESCALERA,
             "CUMPLE" if ok_ancho else "NO CUMPLE"))
    print()
    print("  LECTURA MAS EXIGENTE  (longitud, en el sentido del recorrido)")
    print("    longitud del descanso %.2f m  contra %.2f m  -> %s"
          % (largo_desc, ANCHO_TRAMO_ESCALERA,
             "cumple" if ok_largo else "NO cumple, faltan %.2f m"
             % (ANCHO_TRAMO_ESCALERA - largo_desc)))
    if not ok_largo:
        y0_necesario = ESC_Y1 - g["proyeccion_tramo"] - ANCHO_TRAMO_ESCALERA
        print()
        print("    SE DECLARA, no se esconde: para satisfacer tambien esta")
        print("    lectura el borde de la caja tendria que correrse de")
        print("    y = %.2f a y = %.2f --%.0f cm-- contra la fachada. Es"
              % (ESC_Y0, y0_necesario, 100 * (ESC_Y0 - y0_necesario)))
        print("    geometricamente posible y NO se ejecuta aca: mover la caja")
        print("    cambia la planta, el metrado y el centro de masa, y eso es")
        print("    una decision de proyecto, no un ajuste de calculo.")
    return {"ancho": ancho_desc, "largo": largo_desc,
            "ok_ancho": ok_ancho, "ok_largo": ok_largo}


# ==========================================================================
def garganta(g):
    u"""El espesor de la losa inclinada, que estaba elegido y no calculado."""
    print()
    print("=" * 78)
    print("3. ESPESOR DE LA GARGANTA  -  E.060 Tabla 9.1")
    print("=" * 78)
    L = g["largo_caja"]
    h_min = L / DIV_LOSA_MACIZA_SIMPLE
    print("  La losa de escalera es una LOSA MACIZA ARMADA EN UNA DIRECCION,")
    print("  plegada, que salva la caja entre sus dos apoyos. La luz de")
    print("  calculo es la PROYECCION HORIZONTAL del recorrido completo")
    print("  --tramo mas descanso--, no la del tramo solo:")
    print()
    print("    L = %.2f + %.2f = %.2f m"
          % (g["proyeccion_tramo"], L - g["proyeccion_tramo"], L))
    print()
    print("    E.060 Tabla 9.1, losa maciza simplemente apoyada:")
    print("      h >= L/%.0f = %.2f / %.0f = %.3f m"
          % (DIV_LOSA_MACIZA_SIMPLE, L, DIV_LOSA_MACIZA_SIMPLE, h_min))
    print("      adoptado  e = %.2f m  ->  %s (holgura %+.1f %%)"
          % (E_LOSA_ESCALERA,
             "CUMPLE" if E_LOSA_ESCALERA >= h_min else "NO CUMPLE",
             100.0 * (E_LOSA_ESCALERA / h_min - 1.0)))
    print()
    # el peso ya lo calcula el SSOT: aca solo se muestra de donde sale
    cos_t = PASO_ESCALERA / math.hypot(PASO_ESCALERA, CONTRAPASO_ESCALERA)
    e_eq = E_LOSA_ESCALERA / cos_t + CONTRAPASO_ESCALERA / 2.0
    print("  PESO, visto en planta (lo calcula proyecto::peso_escalera_m2):")
    print("    inclinacion  cos t = %.3f  ->  la losa se ve %.3f m de espesor"
          % (cos_t, E_LOSA_ESCALERA / cos_t))
    print("    mas medio contrapaso de peldano macizo: + %.3f m"
          % (CONTRAPASO_ESCALERA / 2.0))
    print("    espesor equivalente %.3f m  ->  %.0f kgf/m2 de proyeccion"
          % (e_eq, peso_escalera_m2()))
    return {"L": L, "h_min": h_min, "e": E_LOSA_ESCALERA, "e_eq": e_eq}


# ==========================================================================
def viga_de_borde(g):
    u"""La viga que faltaba: el hueco de la escalera corta el aligerado.

    El hueco tiene cuatro bordes. El del fondo (y = 3,36) ES el muro MX-2 y
    esta resuelto. Los dos laterales corren PARALELOS a las viguetas y no
    cortan ninguna. El del frente (y = 0,60) las corta de plano: ahi el
    aligerado queda con un canto libre y necesita viga, igual que el pozo de
    luz en el script 08.
    """
    print()
    print("=" * 78)
    print("4. VIGA DE BORDE DEL HUECO  -  VB-2")
    print("=" * 78)
    m10 = _mod("10_metrado_losas.py")
    cm = m10.CM_TIPICO
    L = g["ancho_caja"]
    print("  El hueco tiene cuatro bordes:")
    print("    y = %.2f  ->  es el muro MX-2, resuelto" % ESC_Y1)
    print("    x = %.2f y x = %.2f  ->  PARALELOS a las viguetas, no cortan"
          % (ESC_X0, ESC_X1))
    print("    y = %.2f  ->  CORTA las viguetas: necesita viga" % ESC_Y0)
    print()
    # la franja entre la fachada y el hueco reparte mitad a cada apoyo
    franja = ESC_Y0
    trib = franja / 2.0
    w_losa = (cm + SC_VIVIENDA) * trib
    h_min = L / DIV_VIGA_SIMPLE
    h = E_LOSA if h_min <= E_LOSA else 0.05 * math.ceil(h_min / 0.05)
    w_propio = ESPESOR * h * PESO_CONCRETO
    w = w_losa + w_propio
    R = w * L / 2.0
    print("  Luz (el ancho de la caja)        %.2f m" % L)
    print("  Franja de losa entre la fachada y el hueco: %.2f m; la viga toma"
          % franja)
    print("  la mitad, %.2f m (la otra mitad baja por MX-1)" % trib)
    print("    w losa   = (%.0f + %.0f) x %.2f = %6.0f kgf/m"
          % (cm, SC_VIVIENDA, trib, w_losa))
    print("    w propio = %.2f x %.2f x %.0f = %6.0f kgf/m"
          % (ESPESOR, h, PESO_CONCRETO, w_propio))
    print("    reaccion en cada apoyo  %.0f kgf" % R)
    print()
    print("  E.060 Tabla 9.1, viga simplemente apoyada: h >= L/%.0f = %.3f m"
          % (DIV_VIGA_SIMPLE, h_min))
    print("  -> VB-2 de %.2f x %.2f m" % (ESPESOR, h))
    if abs(h - E_LOSA) < 1e-9:
        print("     Queda EMBEBIDA en la losa (viga chata) porque el minimo")
        print("     de la tabla es menor que el peralte del aligerado: no")
        print("     tiene sentido descolgarla bajo el cielo raso del hall.")
    print()
    print("  LA ESCALERA NO CARGA SOBRE ESTA VIGA. El 27 dimensiona las")
    print("  CUATRO COLUMNAS de la caja, que es lo que la E.070 9.1 manda")
    print("  --el descanso no puede apoyar en la albanileria-- y que se")
    print("  llevan el 68,3 % de su carga a la cimentacion.")
    return {"L": L, "h": h, "h_min": h_min, "R": R, "w": w}


# ==========================================================================
def metrado():
    u"""Lo que el metrado ya hacia y el registro no declaraba."""
    print()
    print("=" * 78)
    print("5. LA ESCALERA EN EL METRADO  -  ya estaba, faltaba decirlo")
    print("=" * 78)
    print("  El registro daba por pendiente 'escalera y tanque elevado en el")
    print("  metrado'. La escalera SI esta: el 11 la reparte a los muros con")
    print("  `reparto_escalera()` y el 15 la incluye en el centro de masa.")
    print()
    print("    area                  %.2f m2" % AREA_ESCALERA)
    print("    peso propio           %.0f kgf/m2 de proyeccion"
          % peso_escalera_m2())
    print("    sobrecarga            %.0f kgf/m2, en los CINCO niveles: es"
          % SC_VIVIENDA)
    print("                          circulacion y se sube hasta la azotea")
    print("    CM de los 5 niveles   %.0f kgf"
          % (AREA_ESCALERA * peso_escalera_m2() * 5))
    print()
    print("  Lo que sigue pendiente de ese renglon es el TANQUE ELEVADO, que")
    print("  es instalacion sanitaria y no estructura de albanileria.")


def control(g, filas, desc, gar, vb):
    print()
    print("=" * 78)
    print("CONTROLES")
    print("=" * 78)
    for nombre, exige, tiene, ok, _u in filas:
        assert ok, "no cumple: %s (exige %.3f, tiene %.3f)" % (nombre, exige,
                                                               tiene)
    assert abs(g["sube_tramo"] * g["n_tramos"] - H_ENTREPISO) < 1e-9, (
        "los %d tramos suben %.3f m y el entrepiso mide %.2f"
        % (g["n_tramos"], g["sube_tramo"] * g["n_tramos"], H_ENTREPISO))
    assert abs(g["proyeccion_tramo"] + desc["largo"] - g["largo_caja"]) < 1e-9, (
        "tramo mas descanso no dan el largo de la caja")
    assert gar["e"] >= gar["h_min"], (
        "la garganta adoptada (%.3f) no llega al minimo de la Tabla 9.1 (%.3f)"
        % (gar["e"], gar["h_min"]))
    assert desc["ok_ancho"], (
        "el descanso no cumple ni la lectura que le corresponde")
    assert vb["h"] >= vb["h_min"], "la VB-2 no llega al minimo de la tabla"
    # y el peso equivalente TIENE que superar al espesor recto: si no, la
    # funcion del SSOT dejo de contar la inclinacion o el peldano.
    assert gar["e_eq"] > gar["e"], (
        "el espesor equivalente (%.3f) no supera al de la garganta (%.3f): "
        "el peso no esta contando la inclinacion o el peldano macizo"
        % (gar["e_eq"], gar["e"]))
    print("  [ok] paso, contrapaso y pasos entre descansos cumplen el 23.2")
    print("  [ok] los %d tramos suman exactamente la altura de entrepiso"
          % g["n_tramos"])
    print("  [ok] garganta %.2f m >= L/%.0f = %.3f m (E.060 Tabla 9.1)"
          % (gar["e"], DIV_LOSA_MACIZA_SIMPLE, gar["h_min"]))
    print("  [ok] descanso: %.2f m de ancho >= %.2f m del tramo"
          % (desc["ancho"], ANCHO_TRAMO_ESCALERA))
    if not desc["ok_largo"]:
        print("  [--] la lectura mas exigente del 23.2.a NO se satisface por")
        print("       %.2f m, y queda DECLARADA arriba"
              % (ANCHO_TRAMO_ESCALERA - desc["largo"]))
    print("  [ok] VB-2 de %.2f x %.2f m >= L/%.0f"
          % (ESPESOR, vb["h"], DIV_VIGA_SIMPLE))


def main():
    g = geometria()
    filas = arquitectura(g)
    desc = descanso(g)
    gar = garganta(g)
    vb = viga_de_borde(g)
    metrado()
    control(g, filas, desc, gar, vb)


if __name__ == "__main__":
    main()
