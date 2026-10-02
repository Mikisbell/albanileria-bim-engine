# -*- coding: utf-8 -*-
"""Metrado de cargas de TODAS las losas — criterio 3 de la rúbrica

La rubrica pide, textual: "Idealiza y realiza el metrado de cargas de TODAS las
losas, considera el efecto de TODAS las solicitaciones actuantes". Hasta ahora el
proyecto solo tenia la franja tributaria del muro critico, que es un muro de
trece. Esto lo cierra.

IDEALIZACION
============
El aligerado es una losa NERVADA ARMADA EN UNA DIRECCION: las viguetas corren en
el sentido del FONDO (Y), salvando de muro transversal a muro transversal, y se
apoyan en ellos. Los muros longitudinales (Y) corren PARALELOS a las viguetas y
por eso casi no reciben carga de losa: solo la vigueta que queda sobre ellos.

  * viguetas de 0,10 m de ancho a 0,40 m entre ejes (la configuracion que la
    E.020 tabula para el peso de 300 kgf/m2 con h = 0,20 m)
  * continuidad: los panos 1 y 6 apoyan contra fachada por un lado -> UN solo
    extremo continuo; los panos 2 a 5 son continuos por los dos
  * dos huecos que descuentan area y cortan viguetas: el POZO DE LUZ y la CAJA
    DE ESCALERA. Los dos necesitan viga de borde (ver 08)

SOLICITACIONES (E.020)
======================
  peso propio del aligerado h = 0,20 m      300 kgf/m2   anexo 1
  piso terminado                            100 kgf/m2   SUPUESTO declarado
  tabiqueria                                150 kgf/m2   SUPUESTO conservador
                                            ----------
  CARGA MUERTA                              550 kgf/m2

  sobrecarga piso tipico (vivienda)         200 kgf/m2   tabla 1
  sobrecarga azotea                         100 kgf/m2   art. 7.1.a

NOTA SOBRE LA AZOTEA: no lleva tabiqueria (no hay ambientes) pero si piso
terminado, porque es transitable para mantenimiento del tanque.
"""
from proyecto import (PANOS_Y, EJES_MX, FRENTE, LOSA_ALIGERADA, PISO_TERMINADO,
                      TABIQUERIA, SC_VIVIENDA, SC_AZOTEA, N_PISOS, PANO_POZO,
                      POZO_X0, POZO_X1, POZO_Y0, POZO_Y1,
                      ESC_X0, ESC_X1, ESC_Y0, ESC_Y1, AREA_PLANTA, AREA_EDIFICADA)

SEP_VIGUETAS = 0.40      # m entre ejes, E.020 anexo 1
CM_TIPICO = LOSA_ALIGERADA + PISO_TERMINADO + TABIQUERIA
CM_AZOTEA = LOSA_ALIGERADA + PISO_TERMINADO          # sin tabiqueria


def solape(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def panos():
    """Geometria de cada pano, con los huecos descontados."""
    filas = []
    for i, L in enumerate(PANOS_Y):
        y0, y1 = EJES_MX[i], EJES_MX[i + 1]
        bruta = L * FRENTE
        h_pozo = solape(y0, y1, POZO_Y0, POZO_Y1) * (POZO_X1 - POZO_X0)
        h_esc = solape(y0, y1, ESC_Y0, ESC_Y1) * (ESC_X1 - ESC_X0)
        extremo = (i == 0 or i == len(PANOS_Y) - 1)
        filas.append({
            "n": i + 1, "L": L, "y0": y0, "y1": y1,
            "bruta": bruta, "pozo": h_pozo, "esc": h_esc,
            "neta": bruta - h_pozo - h_esc,
            "apoyo": "un extremo continuo" if extremo else "ambos continuos",
        })
    return filas


def geometria(filas):
    print("=" * 78)
    print("1. IDEALIZACION Y GEOMETRIA DE LOS PANOS")
    print("=" * 78)
    print("  Viguetas armadas en Y, de %.2f m entre ejes, apoyadas en los muros"
          % SEP_VIGUETAS)
    print("  transversales. Frente del pano = %.2f m." % FRENTE)
    print()
    print("  %-5s %6s %14s %9s %9s %9s %9s  %s"
          % ("pano", "L (m)", "y (m)", "bruta", "- pozo", "- escal.", "NETA", "apoyo"))
    for f in filas:
        print("  %-5d %6.2f %6.2f-%-6.2f %9.2f %9.2f %9.2f %9.2f  %s"
              % (f["n"], f["L"], f["y0"], f["y1"], f["bruta"], f["pozo"],
                 f["esc"], f["neta"], f["apoyo"]))
    tot = sum(f["neta"] for f in filas)
    print("  %-5s %6s %13s %9.2f %9.2f %9.2f %9.2f"
          % ("", "", "SUMA", sum(f["bruta"] for f in filas),
             sum(f["pozo"] for f in filas), sum(f["esc"] for f in filas), tot))
    print()
    print("  Control: suma de brutas = %.2f m2 = huella edificada  ->  %s"
          % (sum(f["bruta"] for f in filas),
             "ok" if abs(sum(f["bruta"] for f in filas) - AREA_EDIFICADA) < 1e-6
             else "REVISAR <<<"))
    print("  Area de losa por piso = %.2f m2 (el area techada %.2f menos la"
          % (tot, AREA_PLANTA))
    print("  caja de escalera, que tambien es hueco).")
    return tot


def cargas(filas, area_losa):
    print()
    print("=" * 78)
    print("2. METRADO POR PANO — piso tipico")
    print("=" * 78)
    print("  CM = %.0f + %.0f + %.0f = %.0f kgf/m2     CV = %.0f kgf/m2"
          % (LOSA_ALIGERADA, PISO_TERMINADO, TABIQUERIA, CM_TIPICO, SC_VIVIENDA))
    print()
    print("  %-5s %9s %11s %11s %13s %12s"
          % ("pano", "area m2", "CM kgf", "CV kgf", "servicio kgf", "w vigueta"))
    tcm = tcv = 0.0
    for f in filas:
        cm = f["neta"] * CM_TIPICO
        cv = f["neta"] * SC_VIVIENDA
        tcm += cm
        tcv += cv
        w = (CM_TIPICO + SC_VIVIENDA) * SEP_VIGUETAS
        print("  %-5d %9.2f %11.0f %11.0f %13.0f %9.0f kgf/m"
              % (f["n"], f["neta"], cm, cv, cm + cv, w))
    print("  %-5s %9.2f %11.0f %11.0f %13.0f" % ("SUMA", area_losa, tcm, tcv, tcm + tcv))
    print()
    print("  La carga por vigueta es la misma en todos los panos: el ancho")
    print("  tributario de una vigueta es su separacion, %.2f m, y no depende de la"
          % SEP_VIGUETAS)
    print("  luz. Lo que cambia entre panos es la LUZ, y por lo tanto el momento.")
    return tcm, tcv


def azotea(filas):
    print()
    print("=" * 78)
    print("3. METRADO POR PANO — azotea")
    print("=" * 78)
    print("  CM = %.0f + %.0f = %.0f kgf/m2 (SIN tabiqueria)     CV = %.0f kgf/m2"
          % (LOSA_ALIGERADA, PISO_TERMINADO, CM_AZOTEA, SC_AZOTEA))
    print()
    area = sum(f["neta"] for f in filas)
    cm, cv = area * CM_AZOTEA, area * SC_AZOTEA
    print("  %-22s %9.2f m2" % ("area de losa", area))
    print("  %-22s %11.0f kgf" % ("carga muerta", cm))
    print("  %-22s %11.0f kgf" % ("sobrecarga", cv))
    print("  %-22s %11.0f kgf" % ("servicio", cm + cv))
    print()
    print("  La azotea pesa %.0f kgf menos que un piso tipico: %.0f kgf/m2 menos de"
          % ((CM_TIPICO + SC_VIVIENDA - CM_AZOTEA - SC_AZOTEA) * area,
             CM_TIPICO + SC_VIVIENDA - CM_AZOTEA - SC_AZOTEA))
    print("  carga. Confundirla con un piso tipico infla el peso sismico un %.1f %%."
          % (((CM_TIPICO + SC_VIVIENDA) / (CM_AZOTEA + SC_AZOTEA) - 1) * 100))
    return cm, cv


def totales(tcm, tcv, acm, acv):
    print()
    print("=" * 78)
    print("4. TOTAL DEL EDIFICIO — solo losas")
    print("=" * 78)
    n_tip = N_PISOS - 1
    print("  %d pisos tipicos + 1 azotea" % n_tip)
    print()
    print("  %-30s %13s %13s %13s" % ("", "CM (kgf)", "CV (kgf)", "servicio"))
    print("  %-30s %13.0f %13.0f %13.0f"
          % ("pisos tipicos (x%d)" % n_tip, tcm * n_tip, tcv * n_tip,
             (tcm + tcv) * n_tip))
    print("  %-30s %13.0f %13.0f %13.0f" % ("azotea", acm, acv, acm + acv))
    CM = tcm * n_tip + acm
    CV = tcv * n_tip + acv
    print("  %-30s %13.0f %13.0f %13.0f" % ("TOTAL LOSAS", CM, CV, CM + CV))
    print()
    print("  Estas cifras son SOLO de losa. Al peso del edificio hay que sumarle")
    print("  muros, columnas, soleras, escalera y tanque -- eso va en el script 11.")
    print("  Separarlos permite ver de donde viene cada kilo en vez de un numero")
    print("  unico que nadie puede auditar.")
    return CM, CV


if __name__ == "__main__":
    f = panos()
    a = geometria(f)
    tcm, tcv = cargas(f, a)
    acm, acv = azotea(f)
    totales(tcm, tcv, acm, acv)
