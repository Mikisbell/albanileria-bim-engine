# -*- coding: utf-8 -*-
u"""Los acapites de MURO PORTANTE y CONFINAMIENTO que faltaban cerrar.

POR QUE EXISTE (2026-09-27). Mikis pregunto si el predimensionamiento estaba
completo y la respuesta honesta era NO. Al recorrer el Capitulo 7 de la E.070
acapite por acapite contra el proyecto aparecieron cinco huecos, y ninguno era
de calculo grueso: eran de SUSTENTO. El calculo estaba; lo que faltaba era la
verificacion que lo obliga y el numero que la cierra.

    7.1.1.c  APLASTAMIENTO -- declarado pendiente, sin calcular
    7.1.2.a  MUROS A REFORZAR -- no existia en ningun script ni en el registro
    7.2.1.b  paño maximo entre columnas -- calculado, nunca declarado
    7.2.1.f  f'c minimo del confinamiento -- nunca contrastado
    7.2.2    punzonamiento del paño simple -- nunca declarado

EL 7.1.2.a NO ES UN TRAMITE, y es el hallazgo de este script. El 7.1.2.b mide
la densidad de "muros REFORZADOS", asi que antes de sumar un muro a la
densidad hay que poder decir por que esta reforzado. El proyecto refuerza los
trece y contaba los trece, pero la cadena que lo justifica no estaba escrita
en ninguna parte. Medida, cierra por DOS caminos distintos y complementarios:

    * 11 muros superan sigma >= 0,05 f'm y el **8.6.1** los obliga;
    * los 2 que no --MY-1 y MY-2, a 1,2 % del umbral-- son medianeras, o sea
      muros perimetrales de cierre, y el **7.1.2.a** los obliga por eso.

No hay ningun muro reforzado "de mas" ni ninguno contado sin derecho. Y la
densidad aguanta incluso la lectura mas estricta que se pueda hacer.
"""
from __future__ import print_function

import contextlib
import importlib.util
import io as _io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from proyecto import (AREA_PLANTA, ESPESOR, FM, FC, H_LIBRE, MUROS,
                      PANOS_Y, PANO_POZO, POZO_ANCHO, SC_VIVIENDA,
                      PESO_CONCRETO, LONG_MINIMA)

# La carga muerta tipica NO vive en el SSOT: la arma el script 10 sumando
# aligerado + piso terminado + tabiqueria METRADA. Se importa de ahi en vez
# de rehacer la suma, que es como se separan dos numeros que deben ser uno.

# --- constantes de los acapites, con su origen -----------------------------
FACTOR_APLASTAMIENTO = 0.375   # no-ssot: 7.1.1.c, coeficiente de f'm
ANCHO_A_CADA_LADO = 2.0        # no-ssot: 7.1.1.c, "dos veces el espesor efectivo"
FACTOR_REFUERZO_861 = 0.05     # no-ssot: 8.6.1, coeficiente de f'm
FRACCION_SISMO_712A = 0.10     # no-ssot: 7.1.2.a, "el 10 % o mas"
PANO_MAX_ABSOLUTO = 5.00       # no-ssot: 7.2.1.b, metros
FACTOR_PANO_ALTURA = 2.0       # no-ssot: 7.2.1.b, "dos veces la distancia"
FC_MIN_CONFINAMIENTO = 175.0   # no-ssot: 7.2.1.f, kgf/cm2 (17,15 MPa)
H_VIGA_BORDE = 0.30            # no-ssot: peralte de la VB-1 adoptado en el 08


def _mod(nombre):
    ruta = os.path.join(AQUI, nombre)
    spec = importlib.util.spec_from_file_location("_m" + nombre[:2], ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def cm_tipico():
    u"""La carga muerta del piso tipico, traida del script 10."""
    return _mod("10_metrado_losas.py").CM_TIPICO


def datos():
    u"""Lo que hace falta de los otros scripts, sin recalcular nada."""
    m01 = _mod("01_arquitectura_y_densidad.py")
    m11 = _mod("11_metrado_muros.py")
    m12 = _mod("12_rigidez_lateral.py")
    m17 = _mod("17_reparto_cortante.py")

    sigma = {f["nom"]: f["sigma"] for f in m11.metrar()}
    filas, h, Fi, V, xm, ym, xr, yr = m17.contexto()
    Ktor, Kx, Ky = m17.geometria_torsional(filas, xr, yr)
    rep, _e = m17.repartir(filas, m17.cortantes_de_entrepiso(Fi),
                           xm, ym, xr, yr, Ktor, Kx, Ky)
    cortante = {}
    for dire in ("X", "Y"):
        ms = [(n, r) for n, r in rep.items() if r["dir"] == dire]
        tot = sum(r["V"][0][2] for _n, r in ms)
        for n, r in ms:
            cortante[n] = r["V"][0][2] / tot
    return m01, m12, sigma, cortante


# ==========================================================================
def aplastamiento():
    u"""7.1.1.c -- carga concentrada de la VB-1 sobre el muro que la recibe.

    La UNICA carga concentrada en el plano de la albañileria de este edificio
    son las dos vigas de borde del pozo de luz (VB-1, ver el script 08), que
    apoyan en MX-3 y MX-4. El resto del aligerado entrega carga REPARTIDA a
    lo largo del muro, que es lo que ya verifica el 7.1.1.b.

    El ancho efectivo NO es el ancho de apoyo: el acapite manda sumarle dos
    veces el espesor efectivo A CADA LADO. Usar solo el ancho de apoyo
    triplicaria el esfuerzo y haria fallar una verificacion que cumple.
    """
    print("=" * 78)
    print("1. APLASTAMIENTO POR CARGA CONCENTRADA  -  E.070 7.1.1.c")
    print("=" * 78)
    luz = PANOS_Y[PANO_POZO]
    # la VB-1 recibe medio pano de aligerado a cada lado del canto libre; del
    # lado del pozo NO hay losa, asi que solo carga de un lado.
    ancho_trib = POZO_ANCHO / 2.0
    cm = cm_tipico()
    w_losa = (cm + SC_VIVIENDA) * ancho_trib
    w_propio = ESPESOR * H_VIGA_BORDE * PESO_CONCRETO
    w = w_losa + w_propio
    R = w * luz / 2.0                       # reaccion en cada apoyo, kgf
    print("  La unica carga CONCENTRADA en el plano del muro son las dos vigas")
    print("  de borde del pozo (VB-1, script 08), que apoyan en MX-3 y MX-4.")
    print()
    print("  Luz de la VB-1               %6.2f m" % luz)
    print("  Ancho tributario de losa     %6.2f m  (medio pozo; del otro lado"
          % ancho_trib)
    print("                                       no hay losa)")
    print("  w losa    = (%.0f + %.0f) x %.2f = %8.0f kgf/m"
          % (cm, SC_VIVIENDA, ancho_trib, w_losa))
    print("  w propio  = %.2f x %.2f x %.0f  = %8.0f kgf/m"
          % (ESPESOR, H_VIGA_BORDE, PESO_CONCRETO, w_propio))
    print("  REACCION en cada apoyo  R = w L / 2 = %.0f kgf" % R)
    print()
    t_cm = ESPESOR * 100.0
    ancho_apoyo = t_cm                      # la viga apoya con su ancho b = t
    ancho_efectivo = ancho_apoyo + 2.0 * ANCHO_A_CADA_LADO * t_cm
    area = ancho_efectivo * t_cm
    sigma = R / area
    limite = FACTOR_APLASTAMIENTO * FM
    print("  ANCHO EFECTIVO (el acapite lo define, no se elige):")
    print("    ancho de apoyo + 2t a CADA lado = %.0f + 2 x %.0f x %.0f = %.0f cm"
          % (ancho_apoyo, ANCHO_A_CADA_LADO, t_cm, ancho_efectivo))
    print("    area de compresion = %.0f x %.0f = %.0f cm2"
          % (ancho_efectivo, t_cm, area))
    print()
    print("    sigma = R / A = %.0f / %.0f = %.2f kgf/cm2" % (R, area, sigma))
    print("    limite 0,375 f'm = 0,375 x %.0f = %.2f kgf/cm2" % (FM, limite))
    print("    -> %s   (usa el %.1f %% del admisible)"
          % ("CUMPLE" if sigma <= limite else "NO CUMPLE",
             100.0 * sigma / limite))
    print()
    print("  El resto del aligerado entrega carga REPARTIDA a lo largo del")
    print("  muro: eso es el 7.1.1.b y ya esta verificado en el 11.")
    return {"R": R, "sigma": sigma, "limite": limite, "area": area,
            "ancho_efectivo": ancho_efectivo, "luz": luz}


# ==========================================================================
def muros_a_reforzar(sigma, cortante):
    u"""7.1.2.a -- por que cada muro esta reforzado, y por lo tanto cuenta.

    El 7.1.2.b mide la densidad de muros REFORZADOS. Antes de sumar un muro a
    esa densidad hay que poder decir QUE acapite obliga a reforzarlo. Son dos,
    y se complementan: el 8.6.1 por esfuerzo axial y el 7.1.2.a por
    participacion sismica o por ser perimetral de cierre.
    """
    print()
    print("=" * 78)
    print("2. QUE MUROS HAY QUE REFORZAR  -  E.070 7.1.2.a y 8.6.1")
    print("=" * 78)
    umbral_s = FACTOR_REFUERZO_861 * FM
    print("  El 7.1.2.b mide la densidad de muros REFORZADOS. Antes de contar")
    print("  un muro hay que decir por que esta reforzado. Hay dos caminos:")
    print()
    print("    8.6.1    sigma >= 0,05 f'm = %.2f kgf/cm2" % umbral_s)
    print("    7.1.2.a  lleva el 10 % o mas de la fuerza sismica, O es muro")
    print("             perimetral de cierre")
    print()
    print("  %-30s %4s %7s %6s %8s %6s  %s"
          % ("muro", "dir", "sigma", "8.6.1", "% sismo", "7.1.2a", "obliga"))
    print("  " + "-" * 76)
    filas = []
    for nom, dire, L, t, vanos in MUROS:
        s = sigma.get(nom, 0.0)
        frac = cortante.get(nom, 0.0)
        perimetral = _es_perimetral(nom)
        por_861 = s >= umbral_s
        por_712a = frac >= FRACCION_SISMO_712A or perimetral
        motivos = []
        if por_861:
            motivos.append("8.6.1")
        if frac >= FRACCION_SISMO_712A:
            motivos.append("7.1.2.a sismo")
        if perimetral:
            motivos.append("7.1.2.a perimetral")
        filas.append({"nom": nom, "dir": dire, "sigma": s, "frac": frac,
                      "perimetral": perimetral, "por_861": por_861,
                      "por_712a": por_712a, "motivos": motivos})
        print("  %-30s %4s %7.2f %6s %7.1f %% %6s  %s"
              % (nom[:30], dire, s, "SI" if por_861 else "no", 100 * frac,
                 "SI" if por_712a else "no", " + ".join(motivos) or "NINGUNO"))
    n861 = sum(1 for f in filas if f["por_861"])
    n712 = sum(1 for f in filas if f["por_712a"])
    ninguno = [f for f in filas if not f["motivos"]]
    print()
    print("  Obligados por el 8.6.1 (esfuerzo axial):        %2d de %d"
          % (n861, len(filas)))
    print("  Obligados por el 7.1.2.a (sismo o perimetral):  %2d de %d"
          % (n712, len(filas)))
    print("  Sin ninguna obligacion:                          %2d"
          % len(ninguno))
    print()
    solo_712 = [f["nom"].split()[0] for f in filas
                if f["por_712a"] and not f["por_861"]]
    if solo_712:
        print("  LOS QUE SALVA EL 7.1.2.a: %s." % ", ".join(solo_712))
        for f in filas:
            if f["nom"].split()[0] in solo_712:
                print("    %-8s sigma = %.2f, a %.1f %% del umbral del 8.6.1, "
                      "pero es" % (f["nom"].split()[0], f["sigma"],
                                   100.0 * (1 - f["sigma"] / umbral_s)))
                print("             perimetral de cierre y lleva el %.1f %% "
                      "del sismo." % (100 * f["frac"]))
    print()
    print("  CONCLUSION: los %d muros estan obligados a reforzarse, cada uno"
          % len(filas))
    print("  por su acapite, y por lo tanto los %d cuentan en la densidad."
          % len(filas))
    return filas


def _es_perimetral(nom):
    u"""Muro perimetral de cierre: fachadas y medianeras.

    Se deriva del ROTULO, que es donde el SSOT declara la posicion de cada
    muro --"fachada frontal", "medianera izquierda"--, en vez de llevar una
    lista paralela que hay que mantener a mano. Una lista escrita aparte se
    desincroniza del dato en cuanto alguien renombra un muro.
    """
    bajo = nom.lower()
    return "fachada" in bajo or "medianera" in bajo


# ==========================================================================
def densidad_estricta(m01, filas):
    u"""La densidad contada SOLO con lo que el 7.1.2.a obliga sin el 8.6.1.

    Es la lectura mas exigente que alguien puede hacer en una sustentacion:
    "¿y si solo cuenta los muros que el 7.1.2.a obliga?". Conviene tener el
    numero ANTES de que lo pregunten.
    """
    print()
    print("=" * 78)
    print("3. LA DENSIDAD BAJO LA LECTURA MAS ESTRICTA  -  E.070 7.1.2.b")
    print("=" * 78)
    req = m01.densidad_requerida()
    print("  Demanda Z.U.S.N/56 = %.5f     area requerida = %.3f m2"
          % (req, req * AREA_PLANTA))
    print()
    print("  %-6s %14s %10s %14s %10s" % ("dir", "todos (m2)", "holgura",
                                          "solo 7.1.2.a", "holgura"))
    print("  " + "-" * 60)
    salida = {}
    for dire in ("X", "Y"):
        tabla = m01.tabla_densidad(dire)
        ac_total = sum(f["Ac"] for f in tabla)
        obligados = set(f["nom"] for f in filas
                        if f["dir"] == dire and f["por_712a"])
        ac_estricto = sum(f["Ac"] for f in tabla if f["nom"] in obligados)
        h_tot = 100.0 * (ac_total / AREA_PLANTA / req - 1.0)
        h_est = 100.0 * (ac_estricto / AREA_PLANTA / req - 1.0)
        salida[dire] = (ac_total, h_tot, ac_estricto, h_est)
        print("  %-6s %14.3f %+9.1f %% %14.3f %+9.1f %%"
              % (dire, ac_total, h_tot, ac_estricto, h_est))
    print()
    print("  Aun descartando todo muro que no obligue el 7.1.2.a por si solo,")
    print("  las dos direcciones siguen CUMPLIENDO. La densidad de este")
    print("  edificio no depende de como se lea el acapite.")
    return salida


# ==========================================================================
def confinamiento(m12):
    u"""7.2.1.b, 7.2.1.f y 7.2.2 -- lo que se cumplia sin estar declarado."""
    print()
    print("=" * 78)
    print("4. REQUISITOS DEL CONFINAMIENTO  -  E.070 7.2.1 y 7.2.2")
    print("=" * 78)
    tope = min(PANO_MAX_ABSOLUTO, FACTOR_PANO_ALTURA * H_LIBRE)
    print("  7.2.1.b  La distancia centro a centro entre columnas sera 2 veces")
    print("           la distancia entre los elementos horizontales y no mayor")
    print("           que 5 m.")
    print("           2 x %.2f = %.2f m   y   5,00 m   ->  manda %.2f m"
          % (H_LIBRE, FACTOR_PANO_ALTURA * H_LIBRE, tope))
    print()
    peor, peor_nom = 0.0, ""
    for nom, dire, L, t, vanos in MUROS:
        n = len(m12.columnas(nom, dire, L))
        pano = L / max(1, n - 1) if n > 1 else L
        if pano > peor:
            peor, peor_nom = pano, nom
    print("           Paño mayor del edificio: %.2f m en %s"
          % (peor, peor_nom.split()[0]))
    print("           -> %s, con el %.0f %% del tope"
          % ("CUMPLE" if peor <= tope else "NO CUMPLE", 100.0 * peor / tope))
    print()
    print("           CONSECUENCIA que el acapite concede: cumplido esto y el")
    print("           espesor minimo del 7.1.1.a, la albañileria NO necesita")
    print("           diseñarse ante acciones sismicas ortogonales a su plano.")
    print()
    print("  7.2.1.f  f'c minimo en los elementos de confinamiento: %.0f kgf/cm2"
          % FC_MIN_CONFINAMIENTO)
    print("           El proyecto usa f'c = %.0f  ->  %s (%+.0f %%)"
          % (FC, "CUMPLE" if FC >= FC_MIN_CONFINAMIENTO else "NO CUMPLE",
             100.0 * (FC / FC_MIN_CONFINAMIENTO - 1.0)))
    print()
    print("  7.2.2    El paño de albañileria simple NO soporta punzonamiento")
    print("           por cargas concentradas. En este edificio no hay ninguna")
    print("           carga concentrada PERPENDICULAR al plano de los muros:")
    print("           la VB-1 apoya EN EL PLANO (verificado arriba por el")
    print("           7.1.1.c) y no hay vigas que crucen un paño apoyandose")
    print("           fuera de columna. El acapite no se infringe.")
    return {"pano": peor, "pano_nom": peor_nom, "tope": tope}


# ==========================================================================
def control(apl, filas, dens, conf):
    print()
    print("=" * 78)
    print("CONTROLES")
    print("=" * 78)
    assert apl["sigma"] <= apl["limite"], (
        "el aplastamiento (%.2f) supera 0,375 f'm (%.2f)"
        % (apl["sigma"], apl["limite"]))
    # el ancho efectivo tiene que ser el del acapite y no el de apoyo: si
    # alguien lo "simplifica", el resultado cambia por un factor 5.
    esperado = ESPESOR * 100.0 * (1.0 + 2.0 * ANCHO_A_CADA_LADO)
    assert abs(apl["ancho_efectivo"] - esperado) < 1e-9, (
        "el ancho efectivo no es el del 7.1.1.c")
    sin_motivo = [f["nom"] for f in filas if not f["motivos"]]
    assert not sin_motivo, (
        "estos muros se cuentan en la densidad y ningun acapite obliga a "
        "reforzarlos: %s" % ", ".join(sin_motivo))
    # la densidad tiene que aguantar la lectura estricta: si no, el informe
    # no puede afirmar que no depende de como se lea el acapite.
    for dire, (_a, _h, _ae, h_est) in dens.items():
        assert h_est > 0.0, (
            "en %s la densidad NO cumple contando solo lo que obliga el "
            "7.1.2.a (holgura %.1f %%)" % (dire, h_est))
    assert conf["pano"] <= conf["tope"], "el paño supera el tope del 7.2.1.b"
    assert FC >= FC_MIN_CONFINAMIENTO, "f'c por debajo del 7.2.1.f"
    # y los muros que se cuentan son los mismos que el 6.4 admite
    for nom, dire, L, t, vanos in MUROS:
        assert L >= LONG_MINIMA, (
            "%s mide %.2f m y el 6.4 pide %.2f" % (nom, L, LONG_MINIMA))
    print("  [ok] aplastamiento %.2f <= %.2f kgf/cm2 (7.1.1.c)"
          % (apl["sigma"], apl["limite"]))
    print("  [ok] los %d muros tienen acapite que obliga su refuerzo (7.1.2.a"
          % len(filas))
    print("       y 8.6.1): ninguno se cuenta en la densidad sin derecho")
    print("  [ok] la densidad cumple tambien con la lectura estricta: "
          "%+.1f %% en X y %+.1f %% en Y" % (dens["X"][3], dens["Y"][3]))
    print("  [ok] paño mayor %.2f m <= %.2f m (7.2.1.b)"
          % (conf["pano"], conf["tope"]))
    print("  [ok] f'c = %.0f >= %.0f del 7.2.1.f" % (FC, FC_MIN_CONFINAMIENTO))


def main():
    m01, m12, sigma, cortante = datos()
    apl = aplastamiento()
    filas = muros_a_reforzar(sigma, cortante)
    dens = densidad_estricta(m01, filas)
    conf = confinamiento(m12)
    control(apl, filas, dens, conf)


if __name__ == "__main__":
    main()
