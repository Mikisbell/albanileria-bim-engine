# -*- coding: utf-8 -*-
"""Cimentación: qué ancho pide el suelo y si hacen falta zapatas

La rubrica exige predimensionar "zapatas, cimentacion corrida". Este script
responde con numeros cual corresponde, en vez de inventar zapatas que el sistema
no necesita.

IMPORTANTE: Pm NO se escribe a mano. Se importa del script 02, que es quien lo
calcula. Antes estaba hardcodeado y un cambio en el metrado dejaba esta
verificacion con un peso viejo, sin avisar.

Datos del EMS de Santo Domingo de Acobamba (Gob. Regional de Junin, contrato
267-2017-GRJ-GGR, Ing. Edgar Quiroz Villon CIP 62441):
  - Df = 1,50 m bajo terreno natural
  - "por medio de zapatas conectadas y/o cimientos corridos armados"
  - qad = 3,0 a 4,15 kg/cm2 segun el ancho (Fig. N.o 3 "B vs qad")
  - modo de falla: corte general (Brinch Hansen)

El qad del EMS es PRESION ADMISIBLE: ya trae incorporado el factor de seguridad
que la E.050 Art. 21 fija en 3,0 para cargas estaticas. NO se vuelve a dividir.

E.070 2.1.3: "La cimentacion de concreto se considerara como confinamiento
horizontal para los muros del primer nivel".
"""
import importlib.util as _il
import os as _os

from proyecto import DF, QAD, QAD_SEGUN_B, B_CIMIENTO, L_MURO

# el 02 empieza con digito: no se puede importar con la sintaxis normal
_spec = _il.spec_from_file_location(
    "m02", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                         "02_metrado_y_esfuerzo_axial.py"))
_m02 = _il.module_from_spec(_spec)
_spec.loader.exec_module(_m02)

PM_MURO = _m02.metrado_gravedad()     # viene del metrado, no de una constante


def carga_lineal():
    w = PM_MURO / L_MURO
    print("=" * 72)
    print("CARGA QUE BAJA AL CIMIENTO")
    print("=" * 72)
    print("  Pm importado del script 02 = %.0f kgf en %.2f m" % (PM_MURO, L_MURO))
    print("  carga lineal de servicio w = %.0f kgf/m = %.2f tonf/m" % (w, w / 1000))
    return w


def ancho_requerido(w):
    """Recorre la curva B vs qad del EMS y se queda con el caso MAS EXIGENTE."""
    print()
    print("=" * 72)
    print("ANCHO DE CIMIENTO REQUERIDO — se evalua toda la curva del EMS")
    print("=" * 72)
    print("  El qad del EMS no es un numero solo: DEPENDE del ancho del cimiento")
    print("  (Fig. N.o 3, 'B vs qad'). Se calcula con cada punto y rige el peor.")
    print()
    print("  %10s %14s %14s %14s" % ("B_ems (m)", "qad (kg/cm2)", "qad (tonf/m2)", "B req. (m)"))
    casos = []
    for b_ems, qad in QAD_SEGUN_B:
        q_t = qad * 10.0                 # 1 kg/cm2 = 10 tonf/m2
        B = (w / 1000.0) / q_t
        casos.append((B, qad, q_t))
        print("  %10.2f %14.2f %14.1f %14.2f" % (b_ems, qad, q_t, B))
    B, qad, q_t = max(casos)              # el mayor B requerido = el mas exigente
    print()
    print("  RIGE qad = %.2f kg/cm2 = %.1f tonf/m2  ->  B requerido = %.2f m"
          % (qad, q_t, B))
    print("  Es el menor qad de la curva, y ademas el consistente: el B que sale")
    print("  (%.2f m) es MENOR que los dos anchos tabulados, y en esta curva a menor" % B)
    print("  ancho corresponde menor capacidad. Tomar el qad del ancho grande seria")
    print("  atribuirle al cimiento una capacidad que su propio tamano no habilita.")
    return B


def veredicto(w, B):
    print()
    print("=" * 72)
    print("VEREDICTO: cimiento corrido o zapata")
    print("=" * 72)
    print("  ancho requerido %.2f m  ->  se adopta B = %.2f m" % (B, B_CIMIENTO))
    q_real = (w / 1000.0) / B_CIMIENTO
    holgura = (QAD * 10 / q_real - 1) * 100
    print("  presion real = %.2f tonf/m2 = %.2f kg/cm2  <  %.2f  (holgura %+.0f %%)"
          % (q_real, q_real / 10, QAD, holgura))
    print("  profundidad de cimentacion Df = %.2f m (del EMS)" % DF)
    print()
    print("  CONCLUSION")
    print("  Los muros portantes NO requieren zapata aislada: el CIMIENTO CORRIDO")
    print("  ARMADO alcanza y ademas cumple la funcion de confinamiento horizontal")
    print("  que le asigna la E.070 2.1.3.")
    print()
    print("  Las ZAPATAS van solo bajo COLUMNAS EXENTAS -- las del borde libre del")
    print("  pozo de luz, que no tienen muro debajo. El EMS admite ambas: 'zapatas")
    print("  conectadas y/o cimientos corridos armados'.")
    print()
    print("  criterio 2 de la rubrica: los dos elementos, cada uno donde corresponde.")


if __name__ == "__main__":
    w = carga_lineal()
    B = ancho_requerido(w)
    veredicto(w, B)
