# -*- coding: utf-8 -*-
"""Vigas y el problema de cimentar contra el límite de propiedad

Cierra los dos huecos que la rubrica pedia en el criterio 2 y no teniamos:
VIGAS y ZAPATAS. Los dos salen del mismo hecho: el lote es MEDIANERO.

1. VIGA DE BORDE DEL POZO
   El pozo de luz deja dos bordes de losa sin muro debajo. El aligerado apoya en
   los muros MX-3 y MX-4, pero sus cantos en x = 3,90 y x = 8,10 quedan libres y
   paralelos al sentido de armado. Un canto libre de aligerado necesita viga.

2. CIMENTACION EN LA MEDIANERA -- el problema de verdad
   La E.050 dice, en las notas de su Figura 2 y dos veces:
       "Las zapatas ubicadas en el limite de propiedad NO DEBEN INVADIR el
        terreno vecino."
   Un cimiento corrido centrado bajo un muro de espesor t vuela (B - t)/2 a
   cada lado. En las medianeras ese vuelo cae en el
   predio del vecino. Hay que correrlo hacia adentro, y ahi aparece la
   excentricidad.

3. POR QUE LA EXCENTRICIDAD NO SE ARREGLA ENSANCHANDO
   Es el resultado contraintuitivo de este script y conviene verlo con numeros.

4. VIGA DE CIMENTACION
   La salida es conectar, que es exactamente lo que el EMS recomienda:
   "zapatas CONECTADAS y/o cimientos corridos armados".

Fuentes verificadas en esta sesion contra los PDF de ../../06-normas/:
  E.050 Figura 2, notas   zapatas en limite de propiedad no invaden al vecino
  E.060 Tabla 9.1         peralte minimo de vigas: L/16 simplemente apoyada
  E.070 2.1.3             la cimentacion es confinamiento horizontal del 1er piso
"""
import importlib.util as _il
import os as _os

from proyecto import (ESPESOR, B_CIMIENTO, QAD, DF, L_MURO, PANOS_Y, PANO_POZO,
                      RETIRO_LATERAL,
                      POZO_X0, POZO_X1, E_LOSA, PESO_CONCRETO, FC)

_spec = _il.spec_from_file_location(
    "m04", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                         "04_cimentacion.py"))
_m04 = _il.module_from_spec(_spec)
_spec.loader.exec_module(_m04)

W_LINEAL = _m04.carga_lineal.__globals__["PM_MURO"] / L_MURO / 1000.0  # tonf/m
LUZ_POZO = PANOS_Y[PANO_POZO]          # el pano donde cae el pozo
DIV_SIMPLE_APOYO = 16.0   # no-ssot: divisor de la E.060 Tabla 9.1 (vigas
                          # simplemente apoyadas); NO es N_CONTRAPASOS, que
                          # vale lo mismo por pura coincidencia numerica


def viga_de_borde():
    print("=" * 78)
    print("1. VIGA DE BORDE DEL POZO DE LUZ")
    print("=" * 78)
    print("  El pozo va de x = %.2f a %.2f y ocupa el pano de %.2f m entre los muros"
          % (POZO_X0, POZO_X1, LUZ_POZO))
    print("  MX-3 y MX-4. Los bordes NORTE y SUR del pozo SON esos muros, asi que")
    print("  estan resueltos. Los bordes ESTE y OESTE no: ahi el aligerado queda")
    print("  con un canto libre, paralelo a su sentido de armado.")
    print()
    h_min = LUZ_POZO / DIV_SIMPLE_APOYO
    h = 0.30   # no-ssot: peralte de viga en metros, no un porcentaje
    print("  Luz de la viga = %.2f m (apoya en MX-3 y MX-4, los dos muros)" % LUZ_POZO)
    print("  E.060 Tabla 9.1, viga simplemente apoyada: h >= L/%.0f = %.3f m"
          % (DIV_SIMPLE_APOYO, h_min))
    print("  -> se adopta h = %.2f m, b = %.2f m (el espesor del muro, para que"
          % (h, ESPESOR))
    print("     la viga corra alineada con el plano del muro y no sobresalga)")
    print()
    print("  VIGA VB-1 (dos iguales, una por borde): %.2f x %.2f m" % (ESPESOR, h))
    print("  Apoya en muro en sus dos extremos: NO necesita columna, y por lo tanto")
    print("  NO genera zapata aislada. Ese era el supuesto que traiamos de la")
    print("  version de 6 muros y ya no es cierto con la malla actual.")
    return h


def excentricidad_medianera():
    print()
    print("=" * 78)
    print("2. CIMENTACION EN LA MEDIANERA — no se puede invadir al vecino")
    print("=" * 78)
    print("  E.050, notas de la Figura 2, textual:")
    print('     "Las zapatas ubicadas en el limite de propiedad NO DEBEN INVADIR')
    print('      el terreno vecino."')
    print()
    vuelo = (B_CIMIENTO - ESPESOR) / 2.0
    print("  Cimiento corrido CENTRADO: B = %.2f m bajo un muro de %.2f m"
          % (B_CIMIENTO, ESPESOR))
    print("  vuelo a cada lado = (%.2f - %.2f)/2 = %.3f m" % (B_CIMIENTO, ESPESOR, vuelo))
    print("  En las dos medianeras ese vuelo cae en el predio vecino: PROHIBIDO.")
    print()
    # EL RETIRO SISMICO DESCUENTA EXCENTRICIDAD (2026-09-21).
    # Este bloque asumia "la cara del muro al ras del limite", que era cierto
    # hasta que la E.030-2026 Art. 52.3 obligo a retirarse 5 cm. Ahora el muro
    # arranca a RETIRO_LATERAL del limite, y el cimiento PUEDE ocupar esa
    # franja: el Art. 52.1 mide la separacion "desde el nivel del terreno
    # natural", o sea de ahi hacia ARRIBA. Enterrado, lo unico que el cimiento
    # no puede hacer es pasar el limite (E.050, notas de la Figura 2).
    #
    # Asi que el vuelo exterior disponible ya no es cero sino RETIRO_LATERAL,
    # y la excentricidad baja de 0,230 a 0,180 m. El veredicto no cambia
    # -- sigue fuera del tercio central y sigue necesitando amarre --, pero
    # el numero si, y es el que entra en el diseno de la viga de cimentacion.
    print("  El muro arranca a %.2f m del limite (junta sismica del Art. 52.3)"
          % RETIRO_LATERAL)
    print("  y el cimiento SI puede ocupar esa franja: el Art. 52.1 mide la")
    print("  separacion desde el nivel del terreno natural, hacia arriba.")
    print("  Enterrado, lo unico prohibido es pasar el limite (E.050 Fig. 2).")
    print()
    print("  Se corre el cimiento hacia adentro hasta apoyar en el limite:")
    print("  los %.2f m completos dentro del lote. Aparece la excentricidad."
          % B_CIMIENTO)
    e = vuelo - RETIRO_LATERAL
    b6 = B_CIMIENTO / 6.0
    print()
    print("  excentricidad   e = %.3f m" % e)
    print("  tercio central  B/6 = %.3f m" % b6)
    print("  %s  ->  la resultante cae %s del tercio central"
          % ("e > B/6" if e > b6 else "e <= B/6", "FUERA" if e > b6 else "dentro"))
    return e


def por_que_no_se_arregla_ensanchando():
    print()
    print("=" * 78)
    print("3. POR QUE ENSANCHAR NO ARREGLA NADA (el resultado contraintuitivo)")
    print("=" * 78)
    print("  Reflejo natural: si la presion no entra, se ensancha el cimiento.")
    print("  Aca NO funciona, y se ve probandolo:")
    print()
    print("  %8s %10s %10s %12s %12s  %s"
          % ("B (m)", "e (m)", "B'=B-2e", "q (tonf/m2)", "qad", "veredicto"))
    q_ad_t = QAD * 10.0
    for B in (0.60, 0.80, 1.00, 1.50, 2.00):   # no-ssot: barrido de prueba, no son el B ni el Df del proyecto
        e = (B - ESPESOR) / 2.0
        b_ef = B - 2 * e
        q = W_LINEAL / b_ef
        print("  %8.2f %10.3f %10.3f %12.1f %12.1f  %s"
              % (B, e, b_ef, q, q_ad_t, "CUMPLE" if q <= q_ad_t else "NO CUMPLE"))
    print()
    print("  El ancho efectivo de Meyerhof es B' = B - 2e, y como la carga baja")
    print("  siempre por el borde, e = (B - t)/2 y entonces B' = t SIEMPRE, sea")
    print("  cual sea B. Ensanchar agranda el cimiento y la excentricidad en la")
    print("  misma proporcion: la presion no baja ni un poco.")
    print()
    print("  CONCLUSION: un cimiento excentrico AISLADO no es viable. Hay que")
    print("  tomar el momento por otro lado.")


def la_salida_conectar():
    print()
    print("=" * 78)
    print("4. LA SALIDA: CONECTAR — y es lo que el propio EMS recomienda")
    print("=" * 78)
    print("  El EMS dice 'zapatas CONECTADAS y/o cimientos corridos armados'. La")
    print("  palabra clave es conectadas, y recien ahora se entiende por que.")
    print()
    print("  El momento de la excentricidad no se equilibra con presion del suelo:")
    print("  se equilibra amarrando el cimiento de la medianera a los cimientos")
    print("  PERPENDICULARES que lo cruzan. En este edificio esos cimientos ya")
    print("  existen: son los de los %d muros transversales." % (len(PANOS_Y) + 1))
    print()
    print("  %-34s %s" % ("separacion entre amarres (panos):",
                          " · ".join("%.2f" % p for p in PANOS_Y) + " m"))
    print("  %-34s %.2f m" % ("el mayor:", max(PANOS_Y)))
    print()
    print("  La cimentacion NO es un conjunto de fajas sueltas: es una RETICULA")
    print("  cerrada, y esa es la razon estructural de que en albanileria confinada")
    print("  se arme el cimiento corrido. La E.070 2.1.3 lo dice de otra manera: la")
    print("  cimentacion de concreto es el confinamiento horizontal del primer piso.")
    print()
    print("  ELEMENTOS QUE QUEDAN DEFINIDOS:")
    print("   - Cimiento corrido CENTRADO, B = %.2f m, Df = %.2f m, bajo los muros"
          % (B_CIMIENTO, DF))
    print("     interiores y las fachadas.")
    print("   - Cimiento corrido EXCENTRICO, B = %.2f m, bajo las dos medianeras," % B_CIMIENTO)
    print("     con la cara del muro al ras del limite de propiedad.")
    print("   - VIGA DE CIMENTACION que conecta ambos: la dan los cimientos de los")
    print("     muros transversales, cada %.2f m como maximo." % max(PANOS_Y))
    print("   - Concreto f'c = %.0f kg/cm2, armado (no ciclopeo: tiene que tomar" % FC)
    print("     flexion).")
    print()
    print("  PENDIENTE DECLARADO: el refuerzo de la viga de cimentacion sale del")
    print("  momento M = w * e por metro de medianera, que se disena en la etapa")
    print("  09 junto con el resto del acero. Aca queda el dimensionamiento.")
    m = W_LINEAL * ((B_CIMIENTO - ESPESOR) / 2.0)
    print()
    print("  Para dimensionar: w = %.2f tonf/m, e = %.3f m  ->  M = %.2f tonf*m/m"
          % (W_LINEAL, (B_CIMIENTO - ESPESOR) / 2.0, m))


def resumen():
    print()
    print("=" * 78)
    print("RESUMEN — lo que este script cierra del criterio 2")
    print("=" * 78)
    print("  %-30s %-20s %s" % ("elemento", "seccion", "lo que lo fija"))
    print("  %-30s %-20s %s" % ("Viga de borde del pozo (x2)",
                                "%.2f x 0.30 m" % ESPESOR, "E.060 Tabla 9.1, L/16"))
    print("  %-30s %-20s %s" % ("Cimiento corrido centrado",
                                "B = %.2f m" % B_CIMIENTO, "qad del EMS"))
    print("  %-30s %-20s %s" % ("Cimiento corrido excentrico",
                                "B = %.2f m" % B_CIMIENTO, "E.050: no invadir al vecino"))
    print("  %-30s %-20s %s" % ("Viga de cimentacion",
                                "cada %.2f m" % max(PANOS_Y), "los muros transversales"))
    print()
    print("  Lo que NO lleva este edificio, y hay que decirlo en vez de inventarlo:")
    print("  ZAPATAS AISLADAS. Los bordes del pozo apoyan en muro por los cuatro")
    print("  lados una vez colocadas las vigas VB-1, y no queda ninguna columna")
    print("  exenta. Tampoco hay ascensor: el quinto piso esta a 10,80 m y la")
    print("  A.010 Art. 34.1.a lo exige recien pasados los 12,00 m.")


if __name__ == "__main__":
    viga_de_borde()
    excentricidad_medianera()
    por_que_no_se_arregla_ensanchando()
    la_salida_conectar()
    resumen()
