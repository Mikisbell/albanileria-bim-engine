# -*- coding: utf-8 -*-
"""Análisis sísmico en sus DOS niveles y elección de la unidad de albañilería

Toda constante viene de `proyecto.py`.

Los dos niveles (Comentarios a la E.070, Articulo 22):
  SISMO SEVERO   = el de la E.030 con R (= R0 * Ia * Ip)
  SISMO MODERADO = la mitad del severo. "Equivale a emplear R = 6 en un analisis
                   elastico" CUANDO R vale 3; lo que manda es el /2.

Y la advertencia del mismo texto, que conviene respetar: "No es conveniente
realizar el analisis con el sismo severo porque podria obtenerse cortantes (Vu)
que superen a la resistencia al agrietamiento diagonal". El analisis elastico
-- rigideces, centro de rigidez, torsion, reparto -- va con el MODERADO.

A que nivel corresponde cada verificacion:
  8.5.2  control de fisuracion     Ve <= 0,55 Vm      -> MODERADO
  8.5.4  resistencia del edificio  sum(Vmi) >= VEi    -> SEVERO
  8.6    fuerzas de diseno         Vu = Ve*(Vm1/Ve1)  -> 2 <= f <= 3
"""
from proyecto import (Z, U, S, R, R0, IA, IP, HN, C_T, T_P, FM, VM,
                      FACTOR_MODERADO, factor_C, cortante_unitario)

# (denominacion, f'm, v'm, es solida?, admitida por Tabla 2 en 4+ pisos?)
UNIDADES = [
    ("King Kong Artesanal (arcilla)",  35.0, 5.1, True,  False),
    ("King Kong Industrial 18 huecos", 65.0, 8.1, False, False),   # no-ssot: otra unidad
    ("SOLIDO industrial de arcilla",     FM,  VM, True,  True),
    ("Rejilla Industrial",             85.0, 9.2, False, False),
    ("King Kong Normal (silice-cal)", 110.0, 9.7, True,  True),
]


def cortante_basal():
    C, T = factor_C()
    print("=" * 74)
    print("CORTANTE BASAL EN SUS DOS NIVELES (E.030-2026)")
    print("=" * 74)
    print("  hn = %.2f m   T = hn/CT = %.2f/%d = %.3f s  <  TP = %.1f s  ->  C = %.2f"
          % (HN, HN, C_T, T, T_P, C))
    print("  ZUCS = %.2f x %.2f x %.2f x %.2f = %.4f" % (Z, U, C, S, Z * U * C * S))
    print()
    print("  R = R0 x Ia x Ip = %.2f x %.2f x %.2f = %.2f   (E.030 Art. 26)"
          % (R0, IA, IP, R))
    print("     R0 sale de la Tabla N.o 10. Ia e Ip valen 1,00 por SUPUESTO de")
    print("     regularidad: se verifican con los resultados del analisis, y si")
    print("     fallan, R baja y todo esto se rehace.")
    print()
    sev, mod = cortante_unitario(True), cortante_unitario(False)
    print("  sismo SEVERO    V/P = %.4f   (%.1f %% del peso)" % (sev, sev * 100))
    print("  sismo MODERADO  V/P = %.4f   (%.1f %% del peso)" % (mod, mod * 100))
    print()
    print("  moderado = severo / %.0f = %.4f" % (FACTOR_MODERADO, mod))
    print("  Con R = 3 eso equivale a dividir entre 6, pero lo que manda es el /2:")
    print("  si una irregularidad bajara R a 2,25, el moderado saldria con 4,50.")
    return sev, mod


def eleccion_de_unidad():
    print()
    print("=" * 74)
    print("ELECCION DE LA UNIDAD — filtro en dos pasos")
    print("=" * 74)
    print("  %-32s %6s %6s %8s %9s  %s" % ("denominacion", "f'm", "v'm", "solida", "Tabla 2", ""))
    for nom, fm, vm, solida, adm in UNIDADES:
        print("  %-32s %6.0f %6.1f %8s %9s  %s"
              % (nom[:32], fm, vm, "si" if solida else "NO", "si" if adm else "no",
                 "OK" if (solida and adm) else "DESCARTADA"))
    print()
    print("  Motivos de descarte:")
    print("   - Artesanal: es solida, pero la Tabla 2 prohibe el ARTESANAL en muro")
    print("     portante de 4 pisos a mas (zonas sismicas 2 y 3).")
    print("   - King Kong 18 huecos y Rejilla: ~46 % de vacios en el producto")
    print("     tipico -> no son solidas (2.1.26 exige area neta >= 70 %). La")
    print("     Fig. 1.12 de los Comentarios las lista como NO APTAS. El script")
    print("     13 lo verifica sobre fichas reales: 1 de 4 marcas califica.")
    print()
    print("  ADOPTADA: ladrillo SOLIDO industrial de arcilla, clase IV o superior.")
    print("  f'm y v'm: la Tabla 9 no tabula esa denominacion y el Art. 5.1.9 manda")
    print("  ensayar. Se adoptan 65 y 8,1 kgf/cm2 como REFERENCIA DECLARADA, y el")
    print("  proyecto exige el ensayo de pilas y muretes (5.1.7) antes de ejecutar.")


if __name__ == "__main__":
    cortante_basal()
    eleccion_de_unidad()
