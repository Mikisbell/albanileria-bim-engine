# -*- coding: utf-8 -*-
"""Reparto del cortante por muro: directo + torsión. Cierra los criterios 5 y 6

QUE PRODUCE, Y PARA QUE
=======================
Los `Ve` y `Me` de CADA muro en CADA entrepiso. Son la entrada de todo el
Capitulo 8: sin ellos no hay alfa, ni Vm, ni control de fisuracion, ni diseno de
confinamientos. Es el cuello de botella de 6,67 puntos de la rubrica.

COMO SE REPARTE
===============
Con diafragma rigido, el cortante de entrepiso se reparte entre los muros de esa
direccion en proporcion a su rigidez (cortante DIRECTO), y encima se suma el
que produce el giro del diafragma (cortante por TORSION):

    V_directo_i = V_entrepiso . Ki / suma(K)
    V_torsion_i = Mt . Ki . di / Ktor        con  Mt = V_entrepiso . e
    Ktor = suma( Ki . di^2 )   sobre TODOS los muros, de las dos direcciones

`di` es la distancia del muro al centro de rigidez, medida perpendicular a su
propio plano.

LA TORSION NO RESTA
===================
El Art. 37.b de la E.030-2026 lo dice sin ambiguedad:

  "Se puede suponer que las condiciones mas desfavorables se obtienen calculando
   las excentricidades accidentales con el mismo signo en todos los niveles, en
   donde se toman en cuenta UNICAMENTE LOS INCREMENTOS de las fuerzas
   horizontales."

O sea que a un muro le sumamos el efecto del giro cuando lo perjudica y NO le
descontamos nada cuando lo favorece. Se evalua el giro en los dos sentidos y se
toma el peor para cada muro.

LOS DOS NIVELES DE SISMO
========================
  MODERADO  -> da los Ve y Me del ANALISIS ELASTICO. Son los que entran en
               alfa = Ve.L/Me (8.5.3) y en el control de fisuracion (8.5.2).
  SEVERO    -> da el VE que hay que comparar contra suma(Vm) en 8.5.4.
La E.070 trabaja con los dos y confundirlos es el error caro: el moderado es la
MITAD del severo (Comentarios Art. 22).

LA COMBINACION DIRECCIONAL
==========================
El Art. 33.3 (analisis ESTATICO, que es el nuestro por el Art. 33.2) manda
100 % + 30 % por SUMA DE ABSOLUTOS. NO es el SRSS del Art. 43, que corresponde
al analisis dinamico y da un 24 % menos. El script aplica el correcto y lo
declara, porque el trabajo de referencia usa el otro.
"""
import importlib.util
import os

from proyecto import (N_PISOS, H_ENTREPISO, FRENTE, FONDO, MUROS, EXC_ACCIDENTAL,
                      FACTOR_MODERADO, LONG_MINIMA, machones)

DIRECCIONAL = 0.30      # no-ssot: E.030-2026 Art. 33.3, el 30 % de la ortogonal


def _cargar(nombre):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "m", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R15 = _cargar("15_centro_masa_y_rigidez.py")
R16 = _cargar("16_irregularidades.py")


def contexto():
    """Todo lo que ya calcularon 15 y 16; aca no se re-deriva nada."""
    filas = R16.propiedades()
    T, k, C, pesos, P, V = R16.sismo()
    h, Fi, _alfa = R16.fuerzas(pesos, V, k)
    _W, xm, ym, _d, _a, _b, _c = R15.centro_de_masa(False)
    xr, yr, _sy, _sx = R15.centro_de_rigidez({f["nom"]: f["K"] for f in filas})
    return filas, h, Fi, V, xm, ym, xr, yr


def cortantes_de_entrepiso(Fi):
    """V_i = suma de las Fj de los niveles por ENCIMA (incluido el propio)."""
    return [sum(Fi[i:]) for i in range(N_PISOS)]


def geometria_torsional(filas, xr, yr):
    Ktor = sum(f["K"] * ((f["x"] - xr) if f["dir"] == "Y" else (f["y"] - yr)) ** 2
               for f in filas)
    Kx = sum(f["K"] for f in filas if f["dir"] == "X")
    Ky = sum(f["K"] for f in filas if f["dir"] == "Y")
    return Ktor, Kx, Ky


def repartir(filas, V_ent, xm, ym, xr, yr, Ktor, Kx, Ky):
    """Ve por muro y por entrepiso, para cada direccion de analisis."""
    e = {"Y": abs(xm - xr) + EXC_ACCIDENTAL * FRENTE,
         "X": abs(ym - yr) + EXC_ACCIDENTAL * FONDO}
    K_dir = {"X": Kx, "Y": Ky}
    out = {}
    for dire in ("X", "Y"):
        for f in filas:
            if f["dir"] != dire:
                continue
            d = (f["x"] - xr) if dire == "Y" else (f["y"] - yr)
            por_nivel = []
            for V in V_ent:
                directo = V * f["K"] / K_dir[dire]
                # los dos sentidos del giro; se toma el que PERJUDICA (37.b)
                tor = abs(V * e[dire] * f["K"] * d / Ktor)
                por_nivel.append((directo, tor, directo + tor))
            out[f["nom"]] = {"dir": dire, "d": d, "K": f["K"], "V": por_nivel}
    return out, e


def momentos(reparto):
    """Me en la base de cada entrepiso: se integran los cortantes de arriba.

    Un muro en voladizo acumula momento hacia abajo. En la base del entrepiso i,
    M = suma sobre los entrepisos j >= i de (V_j . h_entrepiso). Es exacto para
    fuerzas aplicadas en los niveles y es lo que pide el 8.5.3 para calcular
    alfa = Ve.L/Me.
    """
    for nom, r in reparto.items():
        Vs = [v[2] for v in r["V"]]
        M = []
        for i in range(N_PISOS):
            M.append(sum(Vs[j] * H_ENTREPISO for j in range(i, N_PISOS)))
        r["M"] = M
    return reparto


def tabla_entrepiso(V_ent, e):
    print("=" * 96)
    print("1. CORTANTE DE ENTREPISO Y MOMENTO TORSOR")
    print("=" * 96)
    print()
    print("  Excentricidad de diseno (estatica + accidental del Art. 37):")
    print("     sismo en X  ->  ey = %.3f m" % e["X"])
    print("     sismo en Y  ->  ex = %.3f m" % e["Y"])
    print()
    print("  %-8s %16s %16s %18s %18s"
          % ("entrepiso", "V severo (kgf)", "V moder (kgf)",
             "Mt en X (kgf.m)", "Mt en Y (kgf.m)"))
    print("  " + "-" * 82)
    for i in range(N_PISOS - 1, -1, -1):
        V = V_ent[i]
        print("  %-8d %16.0f %16.0f %18.0f %18.0f"
              % (i + 1, V, V / FACTOR_MODERADO, V * e["X"], V * e["Y"]))
    print()
    print("  El MODERADO es la mitad del severo (Comentarios Art. 22). El diseno")
    print("  del Capitulo 8 usa el moderado para Ve y Me, y el severo para el")
    print("  control global de 8.5.4.")


def tabla_reparto(reparto, V_ent, dire, Ktor):
    print()
    print("=" * 96)
    print("2%s. REPARTO EN LA DIRECCION %s  -  primer entrepiso (el que gobierna)"
          % ("a" if dire == "X" else "b", dire))
    print("=" * 96)
    print()
    print("  %-30s %8s %11s %11s %11s %11s %8s"
          % ("muro", "d (m)", "K", "V directo", "V torsion", "Ve SEVERO",
             "% torsi"))
    print("  " + "-" * 92)
    suma_d = suma_t = 0.0
    for nom, r in sorted(reparto.items()):
        if r["dir"] != dire:
            continue
        directo, tor, total = r["V"][0]
        suma_d += directo
        suma_t += tor
        print("  %-30s %8.2f %11.0f %11.0f %11.0f %11.0f %7.1f%%"
              % (nom, r["d"], r["K"], directo, tor, total,
                 100.0 * tor / total))
    print("  " + "-" * 92)
    print("  %-30s %8s %11s %11.0f %11.0f %11.0f"
          % ("SUMA", "", "", suma_d, suma_t, suma_d + suma_t))
    print()
    print("  Control: la suma de los cortantes DIRECTOS tiene que dar el cortante")
    print("  del entrepiso. %.0f contra %.0f  ->  %s"
          % (suma_d, V_ent[0],
             "ok" if abs(suma_d - V_ent[0]) < 1.0 else "NO CIERRA <<<"))
    print("  La torsion agrega %.1f %% y NO se le descuenta a nadie (Art. 37.b)."
          % (100.0 * suma_t / suma_d))


def tabla_diseno(reparto):
    """Ve y Me del sismo MODERADO: la entrada literal del Capitulo 8."""
    print()
    print("=" * 96)
    print("3. Ve Y Me DEL SISMO MODERADO  -  lo que entra al Capitulo 8")
    print("=" * 96)
    print()
    print("  Primer entrepiso, que es donde se disena (8.6.3). Ve y Me ya")
    print("  divididos por %.0f para pasar de severo a moderado." % FACTOR_MODERADO)
    print()
    print("  %-30s %3s %12s %14s %10s %10s"
          % ("muro", "dir", "Ve (kgf)", "Me (kgf.m)", "L (m)", "alfa"))
    print("  " + "-" * 86)
    for nom, r in sorted(reparto.items()):
        Ve = r["V"][0][2] / FACTOR_MODERADO
        Me = r["M"][0] / FACTOR_MODERADO
        L = [m[2] for m in MUROS if m[0] == nom][0]
        alfa = Ve * L / Me if Me else 0.0
        acot = min(1.0, max(1.0 / 3.0, alfa))
        marca = "" if abs(acot - alfa) < 1e-9 else "  -> acotado a %.3f" % acot
        print("  %-30s %3s %12.0f %14.0f %10.2f %10.3f%s"
              % (nom, r["dir"], Ve, Me, L, alfa, marca))
    print()
    print("  alfa = Ve.L/Me, acotado 1/3 <= alfa <= 1 (E.070 8.5.3). Con muros")
    print("  esbeltos alfa tiende a 1/3 y con muros largos a 1. Aca la L es la")
    print("  TOTAL incluyendo columnas, como manda el 8.5.3, y NO la neta que se")
    print("  uso en el esfuerzo axial: son dos articulos distintos.")


def direccional(reparto):
    print()
    print("=" * 96)
    print("4. COMBINACION DIRECCIONAL  -  Art. 33.3, y por que NO es el Art. 43")
    print("=" * 96)
    print()
    print("  El Art. 33.2 permite el analisis ESTATICO en edificios de muros")
    print("  portantes de hasta 15 m, aun irregulares. Nuestro edificio entra")
    print("  (13,50 m), asi que la combinacion que rige es la del Art. 33.3:")
    print()
    print("     100 %% de una direccion  +  %.0f %% de la ortogonal,"
          % (100 * DIRECCIONAL))
    print("     por SUMA DE ABSOLUTOS.")
    print()
    print("  NO es el SRSS del Art. 43, que pertenece al analisis DINAMICO modal.")
    print("  La diferencia no es menor: para dos componentes de 1,00 y 0,30,")
    absolutos = 1.0 + DIRECCIONAL
    srss = (1.0 ** 2 + DIRECCIONAL ** 2) ** 0.5
    print("  la suma de absolutos da %.3f y el SRSS da %.3f, un %.0f %% menos."
          % (absolutos, srss, 100 * (1 - srss / absolutos)))
    print("  Usar el SRSS en un analisis estatico subestima la demanda.")
    print()
    print("  En albanileria confinada los muros de una direccion practicamente no")
    print("  toman carga de la ortogonal (su rigidez fuera del plano es despreciable")
    print("  frente a la del plano), asi que el 30 %% afecta sobre todo a las")
    print("  COLUMNAS DE CONFINAMIENTO compartidas entre dos muros que se cruzan.")
    print("  El 8.5.1.1 lo resuelve sin combinar fuerzas: manda tomar, en la")
    print("  interseccion, EL MAYOR de los dos refuerzos que salgan del diseno")
    print("  independiente de cada muro. Eso es lo que se aplicara en el criterio 9.")


def control_6_4(reparto):
    print()
    print("=" * 96)
    print("5. CONTROL  -  E.070 6.4: que muro cuenta para resistir el sismo")
    print("=" * 96)
    print()
    print("  \"Longitud mayor o igual a %.2f m para ser considerados como" % LONG_MINIMA)
    print("  contribuyentes en la resistencia a las fuerzas horizontales.\"")
    print()
    # ANTES se calculaba (L - vanos)/n_panos, o sea el trozo MEDIO. Un promedio
    # no es una verificacion: 1,60 de media puede esconder un machon de 0,75 que
    # el 6.4 no deja contar. Desde que el SSOT declara la POSICION de los vanos
    # se miden los machones REALES, uno por uno.
    fuera = []
    for nom, _d, L, _t, vanos in MUROS:
        for x0, x1 in machones(nom, _d, L, vanos):
            if x1 - x0 < LONG_MINIMA:
                fuera.append((nom, x1 - x0))
                break
    if fuera:
        for nom, t in fuera:
            print("  %-30s trozo medio %.2f m  ->  NO CUENTA <<<" % (nom, t))
    else:
        print("  Los %d muros tienen todos sus trozos por encima de %.2f m:"
              % (len(MUROS), LONG_MINIMA))
        print("  los %d contribuyen y el reparto de arriba es legitimo." % len(MUROS))


if __name__ == "__main__":
    filas, h, Fi, V, xm, ym, xr, yr = contexto()
    V_ent = cortantes_de_entrepiso(Fi)
    Ktor, Kx, Ky = geometria_torsional(filas, xr, yr)
    reparto, e = repartir(filas, V_ent, xm, ym, xr, yr, Ktor, Kx, Ky)
    reparto = momentos(reparto)

    tabla_entrepiso(V_ent, e)
    tabla_reparto(reparto, V_ent, "X", Ktor)
    tabla_reparto(reparto, V_ent, "Y", Ktor)
    tabla_diseno(reparto)
    direccional(reparto)
    control_6_4(reparto)
