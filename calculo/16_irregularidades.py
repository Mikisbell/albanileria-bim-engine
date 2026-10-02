# -*- coding: utf-8 -*-
"""Ia e Ip: la única variable que todavía puede tumbar el trabajo entero

QUE SE JUEGA ACA
================
R = R0 x Ia x Ip. Hoy el proyecto SUPONE Ia = Ip = 1,00 y trabaja con R = 3,00.
Si aparece irregularidad torsional, Ip = 0,75, R cae a 2,25 y la fuerza sismica
sube 33 %: se rehace el analisis y probablemente el diseno de los 13 muros.

Por eso este script va ANTES que el reparto y que el diseno. Es el ultimo
eslabon que realimenta hacia atras; despues de el, el trabajo es lineal.

LAS DOS TABLAS, verificadas contra la IMAGEN del PDF (paginas 17 y 18; el texto
plano desalinea la columna de factores y los deja sin dueno):

  Tabla 11 - en ALTURA (Ia)          Tabla 12 - en PLANTA (Ip)
    piso blando / debil      0,75      torsional                0,75
    extrema rigidez / resist 0,50      torsional extrema        0,60
    masa o peso              0,90      esquinas entrantes       0,90
    geometrica vertical      0,90      discontinuidad diafragma 0,85
    discontinuidad sistemas  0,80      sistemas no paralelos    0,90
    discontinuidad extrema   0,60

  Art. 24.1 y 24.2: cada factor es el MENOR de los valores correspondientes a
  las irregularidades EXISTENTES. 24.3: si las dos direcciones dan distinto, se
  toma el MENOR de las dos.

EL GATILLO QUE CASI NADIE LEE
=============================
La irregularidad torsional trae una condicion de aplicabilidad, textual:

  "Este criterio SOLO SE APLICA en edificios con diafragmas rigidos y SOLO SI
   el maximo desplazamiento relativo de entrepiso es mayor que 50% del
   desplazamiento permisible indicado en la Tabla N.o 14"

Tabla 14, albanileria: 0,005. El 50 % es 0,0025. Si la distorsion maxima no
llega a 0,0025, el criterio NO SE EVALUA, por desbalanceada que este la planta.
Un edificio de albanileria con densidad de muros alta se mueve muy poco: por ahi
puede salir el veredicto.

POR QUE LA RELACION Dmax/Dprom NO DEPENDE DE LA FUERZA
======================================================
En un entrepiso con diafragma rigido, el desplazamiento de un extremo es la
traslacion mas el giro por su distancia al centro de rigidez:

    D_ext  = V/K  +  (V.e/Ktor) . d
    D_prom = V/K                       (dos extremos, uno + y otro -)

    Dmax / Dprom = 1 + e . d . K / Ktor

El cortante V se CANCELA. La relacion es pura geometria y rigidez: no depende
del sismo, ni de R, ni del peso. Eso es lo que la vuelve verificable AHORA,
antes de repartir nada, y lo que rompe la circularidad de tener que suponer R
para calcular R.
"""
import importlib.util
import os

from proyecto import (Z, U, S, R0, HN, C_T, T_P, N_PISOS, H_ENTREPISO, FRENTE,
                      FONDO, MUROS, EM, EXC_ACCIDENTAL, PANOS_Y, POZO_X0,
                      POZO_X1, POZO_Y0, POZO_Y1, AREA_PLANTA, AREA_EDIFICADA,
                      factor_C)

DERIVA_ADMISIBLE = 0.005      # no-ssot: E.030-2026 Tabla 14, albanileria
GATILLO_TORSION = 0.50        # no-ssot: Tabla 12, "50 % del permisible"
LIM_TORSIONAL = 1.3           # no-ssot: Tabla 12
LIM_TORSIONAL_EXTREMA = 1.5   # no-ssot: Tabla 12
F_DESPL_REGULAR = 0.75        # no-ssot: E.030-2026 Art. 50.1


def _cargar(nombre):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "mod", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R12 = _cargar("12_rigidez_lateral.py")
R15 = _cargar("15_centro_masa_y_rigidez.py")


def propiedades():
    """K, I, A_corte y posicion de cada muro. Todo viene de 12 y 15."""
    filas = []
    for nom, dire, L, t, vanos in MUROS:
        _A, I, Ac, _Ln = R12.seccion(nom, dire, L, t, vanos)
        K, _fl, _co = R12.rigidez(I, Ac)
        x, y = R15.posicion(nom, dire, L)
        filas.append({"nom": nom, "dir": dire, "K": K, "I": I, "Ac": Ac,
                      "x": x, "y": y})
    return filas


def sismo():
    """Periodo, exponente k y cortante basal del sismo SEVERO."""
    C, T = factor_C()          # devuelve (C, T): el periodo sale de ahi mismo
    k = 1.0 if T <= 0.5 else min(0.75 + 0.5 * T, 2.0)   # no-ssot: Art. 35.2
    W_tip, _x, _y, _d, _a, _b, _c = R15.centro_de_masa(False)
    W_azo, _x, _y, _d, _a, _b, _c = R15.centro_de_masa(True)
    pesos = [W_tip] * (N_PISOS - 1) + [W_azo]
    P = sum(pesos)
    R = R0 * 1.0 * 1.0            # con Ia = Ip = 1,00, que es lo que se verifica
    V = Z * U * C * S / R * P
    return T, k, C, pesos, P, V


def fuerzas(pesos, V, k):
    """Fi = alfa_i . V,  alfa_i = Pi.hi^k / suma(Pj.hj^k).  Art. 35.1"""
    h = [(i + 1) * H_ENTREPISO for i in range(N_PISOS)]
    num = [p * hi ** k for p, hi in zip(pesos, h)]
    den = sum(num)
    return h, [n / den * V for n in num], [n / den for n in num]


def desplazamientos(filas, dire, Fi, h):
    """Voladizo equivalente de la direccion: flexion + corte.

    Todos los muros de una direccion trabajan en paralelo unidos por el
    diafragma, asi que se suman sus EI y sus GA. Para una fuerza P aplicada a la
    altura a, el desplazamiento a la altura x de un voladizo es

        flexion:  x <= a  ->  P x^2 (3a - x) / (6 EI)
                  x >  a  ->  P a^2 (3x - a) / (6 EI)
        corte:    P . min(x, a) / GA

    y el total es la suma sobre todas las fuerzas de piso.
    """
    g = [f for f in filas if f["dir"] == dire]
    EI = EM * sum(f["I"] for f in g)                       # kgf.cm2
    GA = R12.GM * sum(f["Ac"] for f in g) / R12.F_CORTE     # kgf
    d = []
    for x in h:
        xc = x * 100.0
        s = 0.0
        for P, a in zip(Fi, h):
            ac = a * 100.0
            if xc <= ac:
                s += P * xc ** 2 * (3 * ac - xc) / (6.0 * EI)
            else:
                s += P * ac ** 2 * (3 * xc - ac) / (6.0 * EI)
            s += P * min(xc, ac) / GA
        d.append(s)
    return d, EI, GA


def derivas(d, R):
    """Distorsion de entrepiso, ya amplificada por 0,75 R (Art. 50.1)."""
    out = []
    prev = 0.0
    for x in d:
        delta = (x - prev) * F_DESPL_REGULAR * R
        out.append(delta / (H_ENTREPISO * 100.0))
        prev = x
    return out


def torsion(filas, xr, yr, xm, ym):
    """Dmax/Dprom por direccion. No depende del cortante (ver el docstring)."""
    Ktor = 0.0
    for f in filas:
        d = (f["x"] - xr) if f["dir"] == "Y" else (f["y"] - yr)
        Ktor += f["K"] * d ** 2
    Ky = sum(f["K"] for f in filas if f["dir"] == "Y")
    Kx = sum(f["K"] for f in filas if f["dir"] == "X")
    res = {}
    for dire, K, e, d_ext in (
            ("Y", Ky, abs(xm - xr) + EXC_ACCIDENTAL * FRENTE,
             max(xr, FRENTE - xr)),
            ("X", Kx, abs(ym - yr) + EXC_ACCIDENTAL * FONDO,
             max(yr, FONDO - yr))):
        res[dire] = {"e": e, "d": d_ext, "K": K,
                     "rel": 1.0 + e * d_ext * K / Ktor}
    return res, Ktor, Kx, Ky


def informe():
    filas = propiedades()
    T, k, C, pesos, P, V = sismo()
    h, Fi, alfa = fuerzas(pesos, V, k)
    _W, xm, ym, _d, _a, _b, _c = R15.centro_de_masa(False)
    xr, yr, _sy, _sx = R15.centro_de_rigidez({f["nom"]: f["K"] for f in filas})

    print("=" * 88)
    print("1. FUERZA SISMICA EN ALTURA  -  E.030-2026 Art. 34 y 35")
    print("=" * 88)
    print()
    print("  T = hn/CT = %.2f/%d = %.3f s   ->  C = %.2f   (Tp = %.2f)"
          % (HN, C_T, T, C, T_P))
    print("  T <= 0,5 s  ->  k = %.2f   (Art. 35.2.a)" % k)
    print("  V = ZUCS/R . P = %.4f x %.0f = %.0f kgf   (sismo SEVERO, R = %.2f)"
          % (Z * U * C * S / R0, P, V, R0))
    print()
    print("  %-6s %8s %12s %14s %8s %12s"
          % ("NIVEL", "hi (m)", "Pi (kgf)", "Pi.hi^k", "%", "Fi (kgf)"))
    print("  " + "-" * 64)
    for i in range(N_PISOS - 1, -1, -1):
        print("  %-6d %8.2f %12.0f %14.0f %7.1f%% %12.0f"
              % (i + 1, h[i], pesos[i], pesos[i] * h[i] ** k,
                 100 * alfa[i], Fi[i]))
    print("  " + "-" * 64)
    print("  %-6s %8s %12.0f %14s %7.1f%% %12.0f"
          % ("SUMA", "", P, "", 100 * sum(alfa), sum(Fi)))
    return filas, h, Fi, xm, ym, xr, yr, V


def deriva_y_gatillo(filas, h, Fi):
    print()
    print("=" * 88)
    print("2. DERIVAS  -  y el gatillo que decide si la torsional se evalua")
    print("=" * 88)
    print()
    R = R0
    peor = 0.0
    for dire in ("X", "Y"):
        d, EI, GA = desplazamientos(filas, dire, Fi, h)
        dv = derivas(d, R)
        peor = max(peor, max(dv))
        print("  DIRECCION %s     EI = %.3e kgf.cm2     GA = %.3e kgf"
              % (dire, EI, GA))
        print("     %-6s %14s %14s %12s" % ("nivel", "despl (cm)", "deriva",
                                            "vs 0,005"))
        for i in range(N_PISOS - 1, -1, -1):
            print("     %-6d %14.4f %14.6f %11.1f%%"
                  % (i + 1, d[i], dv[i], 100 * dv[i] / DERIVA_ADMISIBLE))
        print()
    lim = GATILLO_TORSION * DERIVA_ADMISIBLE
    print("  Deriva maxima del edificio: %.6f" % peor)
    print("  Admisible (Tabla 14, albanileria): %.6f  ->  se usa el %.1f %%"
          % (DERIVA_ADMISIBLE, 100 * peor / DERIVA_ADMISIBLE))
    print("  Gatillo de la Tabla 12: %.0f %% del admisible = %.6f"
          % (100 * GATILLO_TORSION, lim))
    print()
    aplica = peor > lim
    if aplica:
        print("  La deriva SUPERA el gatillo  ->  hay que evaluar la torsional.")
    else:
        print("  La deriva NO llega al gatillo  ->  el criterio de irregularidad")
        print("  TORSIONAL **no se aplica**, textual: \"solo si el maximo")
        print("  desplazamiento relativo de entrepiso es mayor que 50% del")
        print("  desplazamiento permisible\". Igual se calcula abajo, para dejar")
        print("  el numero y no esconderse detras de una exencion.")
    return aplica, peor


def veredicto_torsional(filas, xm, ym, xr, yr, aplica):
    print()
    print("=" * 88)
    print("3. RELACION Dmax/Dprom  -  se calcula igual, aplique o no")
    print("=" * 88)
    print()
    res, Ktor, Kx, Ky = torsion(filas, xr, yr, xm, ym)
    print("  Rigidez torsional Ktor = suma(Ki . di^2) = %.3e kgf.cm/rad" % Ktor)
    print()
    print("  %-10s %10s %10s %14s %12s %s"
          % ("direccion", "e (m)", "d (m)", "K (kgf/cm)", "Dmax/Dprom", "Tabla 12"))
    print("  " + "-" * 76)
    irregular = extrema = False
    for dire in ("X", "Y"):
        r = res[dire]
        v = r["rel"]
        if v > LIM_TORSIONAL_EXTREMA:
            estado, extrema = "EXTREMA <<<", True
        elif v > LIM_TORSIONAL:
            estado, irregular = "irregular <<<", True
        else:
            estado = "regular"
        print("  %-10s %10.3f %10.2f %14.0f %12.4f %s"
              % (dire, r["e"], r["d"], r["K"], v, estado))
    print()
    print("  Limites: %.1f irregular (Ip = 0,75)  ·  %.1f extrema (Ip = 0,60)"
          % (LIM_TORSIONAL, LIM_TORSIONAL_EXTREMA))
    print()
    if not aplica:
        print("  Y aun asi, el criterio NO SE APLICA: la condicion de")
        print("  aplicabilidad de la Tabla 12 no se cumple. Los dos caminos")
        print("  llevan al mismo lugar, que es la mejor forma de cerrarlo.")
    return irregular, extrema


def barrido(filas, pesos_iguales=True):
    """Las otras doce irregularidades, una por una. Ninguna se da por obvia."""
    print()
    print("=" * 88)
    print("4. BARRIDO DEL RESTO  -  Tabla 11 completa y Tabla 12 sin la torsional")
    print("=" * 88)
    print()
    items = []

    # ---- Tabla 11, en altura
    items.append(("Ia", "Rigidez / piso blando", 0.75, False,
                  "los 13 muros son CONTINUOS del 1.o al 5.o piso y con la misma "
                  "seccion: la rigidez de entrepiso no cambia entre niveles"))
    items.append(("Ia", "Resistencia / piso debil", 0.75, False,
                  "misma razon: misma albanileria, mismo espesor y misma longitud "
                  "en todos los niveles"))
    items.append(("Ia", "Extrema de rigidez o resistencia", 0.50, False,
                  "si no hay la simple, no hay la extrema"))
    W_tip, _a, _b, _c, _d, _e, _f = R15.centro_de_masa(False)
    W_azo, _a, _b, _c, _d, _e, _f = R15.centro_de_masa(True)
    rel_masa = W_tip / W_azo
    items.append(("Ia", "Masa o peso", 0.90, rel_masa > 1.5,  # no-ssot: factor de la Tabla 11/12, no phi ni Df ni Tp
                  "tipico/azotea = %.3f < 1,5; y el criterio NO se aplica en "
                  "azoteas, asi que ni siquiera contaria" % rel_masa))
    items.append(("Ia", "Geometrica vertical", 0.90, False,  # no-ssot: factor de la Tabla 11/12, no phi ni Df ni Tp
                  "la planta es la MISMA en los 5 pisos: %.2f x %.2f m"
                  % (FRENTE, FONDO)))
    items.append(("Ia", "Discontinuidad de sistemas resistentes", 0.80, False,
                  "ningun muro cambia de eje ni de orientacion; la E.070 6.4 "
                  "exige continuidad vertical hasta la cimentacion y se cumple"))
    items.append(("Ia", "Discontinuidad extrema", 0.60, False,  # no-ssot: factor de la Tabla 11/12, no phi ni Df ni Tp
                  "no hay elementos discontinuos"))

    # ---- Tabla 12, en planta (sin la torsional, que va aparte)
    ent_x = max(POZO_X0, FRENTE - POZO_X1)
    ent_y = max(POZO_Y0, FONDO - POZO_Y1)
    items.append(("Ip", "Esquinas entrantes", 0.90, False,  # no-ssot: factor de la Tabla 11/12, no phi ni Df ni Tp
                  "la planta es un RECTANGULO lleno de %.2f x %.2f m. El pozo es "
                  "un hueco INTERIOR, no una esquina entrante" % (FRENTE, FONDO)))
    area_pozo = (POZO_X1 - POZO_X0) * (POZO_Y1 - POZO_Y0)
    pct = 100.0 * area_pozo / AREA_EDIFICADA
    # seccion transversal mas debil del diafragma: la que corta el pozo
    neta_x = FRENTE - (POZO_X1 - POZO_X0)
    pct_x = 100.0 * neta_x / FRENTE
    neta_y = FONDO - (POZO_Y1 - POZO_Y0)
    pct_y = 100.0 * neta_y / FONDO
    mal = pct > 50.0 or pct_x < 50.0 or pct_y < 50.0
    items.append(("Ip", "Discontinuidad del diafragma", 0.85, mal,  # no-ssot: factor de la Tabla 11/12, no phi ni Df ni Tp
                  "abertura %.1f %% del area bruta (limite 50); seccion neta "
                  "minima %.1f %% en X y %.1f %% en Y (limite 50)"
                  % (pct, pct_x, pct_y)))
    items.append(("Ip", "Sistemas no paralelos", 0.90, False,  # no-ssot: factor de la Tabla 11/12, no phi ni Df ni Tp
                  "los 7 muros X son paralelos entre si y los 6 muros Y tambien; "
                  "las dos familias son ortogonales"))

    print("  %-4s %-38s %6s %s" % ("cual", "irregularidad", "factor", "veredicto"))
    print("  " + "-" * 80)
    ia = ip = 1.00
    for cual, nombre, factor, hay, razon in items:
        print("  %-4s %-38s %6.2f %s"
              % (cual, nombre, factor, "HAY <<<" if hay else "no"))
        print("       %s" % razon)
        if hay:
            if cual == "Ia":
                ia = min(ia, factor)
            else:
                ip = min(ip, factor)
    return ia, ip, items


def cierre(ia, ip, irregular, extrema, aplica):
    print()
    print("=" * 88)
    print("VEREDICTO  -  Ia, Ip y R")
    print("=" * 88)
    print()
    if aplica and extrema:
        ip = min(ip, 0.60)  # no-ssot: factor de la Tabla 11/12, no phi ni Df ni Tp
        nota = "irregularidad TORSIONAL EXTREMA"
    elif aplica and irregular:
        ip = min(ip, 0.75)
        nota = "irregularidad TORSIONAL"
    else:
        nota = ("sin irregularidad torsional" if not aplica else
                "la relacion no supera 1,3")
    R = R0 * ia * ip
    print("  Ia = %.2f     (Tabla 11, el menor de las existentes)" % ia)
    print("  Ip = %.2f     (Tabla 12, %s)" % (ip, nota))
    print()
    print("  R = R0 . Ia . Ip = %.2f x %.2f x %.2f = %.2f" % (R0, ia, ip, R))
    print()
    if abs(R - R0) < 1e-9:
        print("  **LA BOMBA NO EXPLOTA.** R se mantiene en %.2f, que es el valor" % R)
        print("  con el que viene calculado todo el proyecto. NO hay que rehacer")
        print("  el analisis: el reparto de cortante y el diseno del Capitulo 8")
        print("  pueden arrancar sobre lo que ya esta.")
        print()
        print("  Y la estructura queda REGULAR en los dos sentidos, lo que ademas")
        print("  habilita el Art. 50.1 (desplazamientos con 0,75 R y no 0,85 R),")
        print("  que es el que se uso arriba para las derivas.")
    else:
        print("  <<< R BAJA DE %.2f A %.2f. La fuerza sismica sube %.0f %% y hay"
              % (R0, R, 100 * (R0 / R - 1)))
        print("  que REHACER el analisis desde el cortante basal.")
    print()
    print("  QUE HABILITA ESTO: el reparto de cortante con torsion (etapa 07) y")
    print("  el diseno de muros (Cap. 8). Es el ultimo calculo que realimentaba")
    print("  hacia atras; de aca en adelante cada paso alimenta al siguiente y")
    print("  ninguno vuelve.")
    return ia, ip, R


if __name__ == "__main__":
    filas, h, Fi, xm, ym, xr, yr, V = informe()
    aplica, peor = deriva_y_gatillo(filas, h, Fi)
    irreg, extr = veredicto_torsional(filas, xm, ym, xr, yr, aplica)
    ia, ip, _items = barrido(filas)
    cierre(ia, ip, irreg, extr, aplica)
