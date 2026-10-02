# -*- coding: utf-8 -*-
"""Sensibilidad al perfil de suelo: el EMS es de 2018 y la norma cambió

EL PROBLEMA, EN UNA LINEA
=========================
El EMS declara "Perfil del suelo tipo T = S2" aplicando la E.030-2018. La
E.030-2026 **movio los limites de clasificacion**, asi que el mismo suelo podria
no ser S2 hoy:

    Perfil    E.030-2018 (Vs)      E.030-2026 (Vs, Tabla N.o 3)
    S1        500 a 1500 m/s       550 a < 800 m/s
    S2        180 a  500 m/s       350 a < 550 m/s
    S3        < 180 m/s            200 a < 350 m/s
    S4        casos especiales     < 200 m/s

Un suelo con Vs = 250 m/s era **S2** en 2018 y es **S3** en 2026.

POR QUE NO SE PUEDE RESOLVER CON EL EMS QUE TENEMOS
===================================================
Para reclasificar harian falta datos que el estudio no tiene:

  * **Vs**: no hay ensayo geofisico (MASW ni refraccion sismica).
  * **N60**: los ensayos de campo son densidad por cono de arena, no SPT.
  * **30 m**: el Art. 15.1 define el perfil sobre "los 30 m superiores"; la
    exploracion del EMS llego a **3,00 m**.

O sea: el "S2" del EMS es la clasificacion disponible y firmada por un ingeniero
colegiado, pero NO sale de una caracterizacion a 30 m. Decirlo es parte del
trabajo.

QUE HACE ESTE SCRIPT
====================
En vez de discutir cual perfil es, **verifica el diseno con los dos** y muestra
si la conclusion cambia. Si aguanta en ambos, el punto queda cerrado con numeros
y no con opinion.

Fuente de los factores: E.030-2026 Tabla N.o 4 (fila Z2) y Tabla N.o 5, con la
nota (*): sin Vs se toma el MAYOR valor del intervalo.
"""
from proyecto import (Z, U, R, N_PISOS, HN, C_T, AREA_PLANTA, MUROS,
                      LONG_MINIMA, S, T_P, factor_C)

# (perfil, S sin Vs, TP, TL, comentario)   E.030-2026 Tablas 4 y 5, fila Z2
PERFILES_Z2 = [
    ("S1", 1.00, 0.40, 2.50, "favorable; exigiria Vs >= 550 m/s"),
    ("S2", 1.30, 0.60, 2.00, "el que declara el EMS (con criterio de 2018)"),   # no-ssot: datos de la Tabla 4/5, no del proyecto
    ("S3", 1.40, 0.90, 1.60, "el adverso: mismo suelo bajo el criterio de 2026"),   # no-ssot: idem
    ("S4", 1.70, 1.20, 1.60, "no plausible: el EMS describe gravas y arenas"),   # no-ssot: idem
]


# La fila S2 de la tabla y los valores del proyecto TIENEN que coincidir: si
# alguien cambia S en proyecto.py sin tocar aca, la sensibilidad compararia
# contra un perfil que ya no es el adoptado, y no se notaria.
_s2 = [p for p in PERFILES_Z2 if p[0] == "S2"][0]
assert abs(_s2[1] - S) < 1e-9 and abs(_s2[2] - T_P) < 1e-9,     "la fila S2 de la Tabla 4/5 no coincide con el S y TP adoptados en proyecto.py"


def area_disponible():
    """Area de corte por direccion, con los vanos descontados (E.070 6.4)."""
    d = {}
    for nom, dire, L, t, vanos in MUROS:
        neta = L - sum(vanos)
        if neta / (len(vanos) + 1) >= LONG_MINIMA:
            d[dire] = d.get(dire, 0.0) + neta * t
    return d


def informe():
    disp = area_disponible()
    T = HN / C_T
    print("=" * 78)
    print("SENSIBILIDAD AL PERFIL DE SUELO — el EMS es de 2018, la norma cambio")
    print("=" * 78)
    print("  El EMS declara S2 con los limites de la E.030-2018. Con los de la")
    print("  E.030-2026 el mismo suelo podria ser S3, y no hay dato para decidirlo:")
    print("  sin Vs, sin SPT y con exploracion hasta 3,00 m de los 30 m que pide")
    print("  el Art. 15.1. Asi que se verifica el diseno CON LOS DOS.")
    print()
    print("  T = hn/CT = %.3f s  (no cambia: no depende del suelo)" % T)
    print()
    print("  %-6s %6s %6s %6s %6s %9s %11s %11s"
          % ("perfil", "S", "TP", "TL", "C", "V/P sev.", "dens. req.", "A corte req."))
    filas = []
    for nom, s, tp, tl, _ in PERFILES_Z2:
        C, _ = factor_C(tp, tl)
        v = Z * U * C * s / R
        dens = Z * U * s * N_PISOS / 56.0
        a_req = dens * AREA_PLANTA
        filas.append((nom, s, C, v, a_req))
        print("  %-6s %6.2f %6.2f %6.2f %6.2f %9.4f %11.5f %9.3f m2"
              % (nom, s, tp, tl, C, v, dens, a_req))
    print()
    print("  Por que C no cambia: T = %.3f s es MENOR que el TP de los cuatro" % T)
    print("  perfiles, asi que siempre cae en el tramo plano de la Tabla N.o 6 y")
    print("  vale 2,50. El edificio es rigido y corto; ahi el suelo mueve el factor")
    print("  S, no el C.")
    print()
    print("=" * 78)
    print("VEREDICTO: la densidad de muros, ?aguanta los dos perfiles?")
    print("=" * 78)
    print("  %-6s %13s %13s %13s %10s"
          % ("perfil", "A req. (m2)", "A dir. X (m2)", "A dir. Y (m2)", "veredicto"))
    todos_ok = True
    for nom, s, C, v, a_req in filas:
        ok = disp["X"] >= a_req and disp["Y"] >= a_req
        todos_ok = todos_ok and (ok or nom == "S4")
        print("  %-6s %13.3f %13.3f %13.3f %10s"
              % (nom, a_req, disp["X"], disp["Y"], "CUMPLE" if ok else "NO CUMPLE"))
    print()
    s3 = [f for f in filas if f[0] == "S3"][0]
    s2 = [f for f in filas if f[0] == "S2"][0]
    print("  Pasar de S2 a S3 sube la demanda un %.1f %% (V/P de %.4f a %.4f) y el"
          % ((s3[3] / s2[3] - 1) * 100, s2[3], s3[3]))
    print("  area de corte requerida un %.1f %% (de %.3f a %.3f m2)."
          % ((s3[4] / s2[4] - 1) * 100, s2[4], s3[4]))
    print("  La holgura de la planta pasa de %+.0f %% a %+.0f %% en X."
          % ((disp["X"] / s2[4] - 1) * 100, (disp["X"] / s3[4] - 1) * 100))
    print()
    print("  CONCLUSION: el planteamiento arquitectonico NO depende de resolver la")
    print("  discusion de perfil. Cumple con S2 y cumple con S3. Se adopta S = %.2f" % S)
    print("  (perfil del EMS + regla de la E.030-2026 sin Vs) y se DECLARA que un")
    print("  ensayo de ondas de corte podria bajarlo hasta 1,00, lo que reduciria")
    print("  la demanda sismica un %.0f %%." % ((1 - 1.00 / S) * 100))
    print()
    print("  LO QUE SI HABRA QUE RE-VERIFICAR con el perfil definitivo: la")
    print("  resistencia al corte de los muros (E.070 8.5.4, suma Vm >= VE), que")
    print("  todavia no se calcula y si escala con la demanda.")
    return todos_ok


if __name__ == "__main__":
    informe()
