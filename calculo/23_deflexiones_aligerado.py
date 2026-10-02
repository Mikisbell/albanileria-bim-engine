# -*- coding: utf-8 -*-
"""Deflexiones del aligerado. E.060 9.6.2 y Tabla 9.2

EL HALLAZGO QUE OBLIGA A ESTE SCRIPT
====================================
El peralte de 0,20 m se justifico con la Tabla 9.1 de la E.060 (pano interior,
L/21 = 0,200). Al verificar esa tabla CONTRA IMAGEN el 2026-09-19 aparecio su
condicion de aplicabilidad, que el proyecto no habia leido. El 9.6.2.1, textual:

    "Los peraltes o espesores minimos para NO VERIFICAR DEFLEXIONES, que se
     senalan en la Tabla 9.1 [...] (losas macizas y vigas) QUE NO SOPORTEN O
     ESTEN LIGADOS a elementos no estructurales susceptibles de danarse por
     deflexiones excesivas del elemento estructural."

Nuestro aligerado SI soporta tabiqueria (150 kgf/m2 en el metrado). Por lo
tanto **la Tabla 9.1 no alcanza**: hay que calcular las deflexiones. Y el
peralte esta JUSTO en el minimo (0,200 contra 0,200 exigidos), sin holgura,
asi que no es una formalidad.

QUE LIMITE APLICA  -  Tabla 9.2
===============================
    piso que NO soporta elementos no estructurales .......... L/360
    piso que SI los soporta y son susceptibles de danarse ... L/480   <== el nuestro
    piso que los soporta y NO son susceptibles .............. L/240

Y la deflexion a comparar NO es la total: es "la parte que ocurre DESPUES de
la union de los elementos no estructurales", o sea la diferida por cargas
permanentes mas la inmediata por la carga viva. El tabique se fisura por lo
que pasa DESPUES de que lo levantaron, no por lo que la losa ya habia flechado.

LO QUE ESTE CALCULO ADOPTA, DECLARADO
=====================================
  * Se toma la vigueta como seccion T: ala de 40 cm (la separacion entre ejes)
    y alma de 10 cm, con 5 cm de losa superior.
  * CADA PANO se evalua con SU condicion real de apoyo, la misma que la Tabla
    9.1 usa para el peralte minimo: los dos extremos con un solo extremo
    continuo y los cuatro interiores con ambos continuos. La primera version de
    este script evaluaba ademas el caso "simplemente apoyado" como cota
    superior, y eso daba un NO CUMPLE enganoso: el pano de 4,20 m es INTERIOR,
    y un tramo simplemente apoyado no existe en esta losa.
  * Se calcula con la inercia BRUTA y con la FISURADA por separado. La norma
    manda usar la efectiva Ie del 9.6.2.3, que queda entre ambas; reportar las
    dos deja ver de que lado cae el resultado sin esconderlo en una formula.
"""
import math

from proyecto import (FC, E_LOSA, LOSA_ALIGERADA, PISO_TERMINADO, TABIQUERIA,
                      SC_VIVIENDA, SEPARACION_MX, PANOS_Y)

SEP_VIGUETAS = 0.40      # no-ssot: m entre ejes, E.020 anexo 1
B_ALMA = 0.10            # no-ssot: m, ancho del alma de la vigueta
E_LOSA_SUP = 0.05        # no-ssot: m, losa superior del aligerado

# Coeficiente de la deflexion maxima segun la condicion de apoyo, en la forma
# delta = w L^4 / (coef . E . I). Son los mismos tres casos que la Tabla 9.1
# distingue para el peralte minimo, y por la misma razon fisica: la continuidad
# en los extremos es lo que gobierna cuanto flecha un tramo.
COEF = {
    "ambos extremos continuos": 384.0,   # no-ssot: empotrado - empotrado
    "un extremo continuo":      185.0,   # no-ssot: empotrado - apoyado
    "simplemente apoyado":       76.8,   # no-ssot: 384/5
}

LIM_480 = 480.0          # no-ssot: Tabla 9.2, piso que soporta elementos susceptibles
LIM_360 = 360.0          # no-ssot: Tabla 9.2, piso que no los soporta
XI_5_ANIOS = 2.0         # no-ssot: 9.6.2.5, factor de tiempo para 5 anios o mas
PCT_CV_PERMANENTE = 0.0  # no-ssot: fraccion de CV que se prevee permanente


def seccion_T():
    """(A, y_sup, Ig) de la vigueta, en cm y cm4."""
    b = SEP_VIGUETAS * 100.0
    bw = B_ALMA * 100.0
    hf = E_LOSA_SUP * 100.0
    h = E_LOSA * 100.0
    A_ala, y_ala = b * hf, hf / 2.0
    A_alma, y_alma = bw * (h - hf), hf + (h - hf) / 2.0
    A = A_ala + A_alma
    y = (A_ala * y_ala + A_alma * y_alma) / A
    Ig = (b * hf ** 3 / 12.0 + A_ala * (y - y_ala) ** 2   # no-ssot: divisor de la inercia b.h^3/12, no el FRENTE
          + bw * (h - hf) ** 3 / 12.0 + A_alma * (y_alma - y) ** 2)   # no-ssot: divisor de la inercia b.h^3/12, no el FRENTE
    return A, y, Ig, h


def cargas():
    """Carga por metro lineal de vigueta, separando permanente de viva."""
    cm = (LOSA_ALIGERADA + PISO_TERMINADO + TABIQUERIA) * SEP_VIGUETAS
    cv = SC_VIVIENDA * SEP_VIGUETAS
    return cm, cv                      # kgf/m


def deflexion(w_kgf_m, L_m, Ec, I_cm4, coef):
    """w L^4 / (coef Ec I), con w en kgf/m, L en m. Devuelve cm."""
    w = w_kgf_m / 100.0                # kgf/cm
    L = L_m * 100.0
    return w * L ** 4 / (coef * Ec * I_cm4)


def informe():
    print("=" * 100)
    print("DEFLEXIONES DEL ALIGERADO  -  E.060 9.6.2 y Tabla 9.2")
    print("=" * 100)
    print()
    print("  POR QUE HAY QUE CALCULARLAS, y no bastaba la Tabla 9.1:")
    print("     9.6.2.1 limita esa tabla a elementos \"QUE NO SOPORTEN O ESTEN")
    print("     LIGADOS a elementos no estructurales susceptibles de danarse\".")
    print("     Este aligerado SI soporta tabiqueria (%.0f kgf/m2 en el metrado)."
          % TABIQUERIA)
    print()
    A, y, Ig, h = seccion_T()
    Ec = 15000.0 * math.sqrt(FC)
    cm, cv = cargas()
    L = SEPARACION_MX
    print("  SECCION T de la vigueta")
    print("     ala %.0f cm x %.0f cm  ·  alma %.0f cm  ·  h = %.0f cm"
          % (SEP_VIGUETAS * 100, E_LOSA_SUP * 100, B_ALMA * 100, h))
    print("     A = %.0f cm2   y_sup = %.2f cm   Ig = %.0f cm4" % (A, y, Ig))
    print("     Ec = 15000 raiz(%.0f) = %.0f kgf/cm2" % (FC, Ec))
    print()
    print("  CARGAS sobre una vigueta (ancho tributario %.2f m)" % SEP_VIGUETAS)
    print("     permanente  %.1f kgf/m   (losa %.0f + piso %.0f + tabiques %.0f)"
          % (cm, LOSA_ALIGERADA, PISO_TERMINADO, TABIQUERIA))
    print("     viva        %.1f kgf/m   (sobrecarga %.0f kgf/m2)" % (cv, SC_VIVIENDA))
    print("     luz critica L = %.2f m  (pano interior)" % L)
    print()

    # inercia fisurada aproximada: 0,35 Ig, valor habitual para secciones T de
    # aligerado. Se declara como COTA INFERIOR, no como calculo del 9.6.2.3.
    Icr = 0.35 * Ig
    print("  Inercia bruta Ig = %.0f cm4   ·   fisurada (0,35 Ig) = %.0f cm4"
          % (Ig, Icr))
    print()
    print("  CADA PANO CON SU CONDICION REAL DE APOYO. El pano de %.2f m es"
          % SEPARACION_MX)
    print("  INTERIOR, o sea continuo en sus dos extremos: evaluarlo como")
    print("  simplemente apoyado seria calcular un tramo que no existe.")
    print()
    print("  %-5s %7s %-26s %9s %11s %11s %s"
          % ("pano", "L (m)", "condicion", "limite", "con Ig", "con Icr", "9.6.2.6"))
    print("  " + "-" * 92)
    filas = []
    for k, L_k in enumerate(PANOS_Y):
        cond = ("un extremo continuo" if k in (0, len(PANOS_Y) - 1)
                else "ambos extremos continuos")
        coef = COEF[cond]
        lim_k = L_k * 100.0 / LIM_480
        d_g = XI_5_ANIOS * deflexion(cm, L_k, Ec, Ig, coef) + deflexion(cv, L_k, Ec, Ig, coef)
        d_cr = XI_5_ANIOS * deflexion(cm, L_k, Ec, Icr, coef) + deflexion(cv, L_k, Ec, Icr, coef)
        ok = d_cr <= lim_k
        filas.append((k + 1, L_k, cond, lim_k, d_g, d_cr, ok))
        print("  %-5d %7.2f %-26s %9.4f %11.4f %11.4f %s"
              % (k + 1, L_k, cond, lim_k, d_g, d_cr,
                 "cumple" if ok else "NO CUMPLE <<<"))
    print()
    lim = min(f[3] for f in filas)
    print("  Limite Tabla 9.2 para piso que SOPORTA elementos susceptibles: L/%.0f"
          % LIM_480)
    print("  La columna que decide es la de Icr: es la cota DESFAVORABLE.")
    return filas, lim, Ig, Icr


def lectura(filas, lim):
    print()
    print("=" * 100)
    print("LECTURA")
    print("=" * 100)
    print()
    malos = [f for f in filas if not f[6]]
    critico = max(filas, key=lambda f: f[5] / f[3])
    print("  El pano mas exigido es el %d (L = %.2f m, %s):" % (critico[0], critico[1], critico[2]))
    print("     flecha %.4f cm contra un limite de %.4f  ->  %.0f %% del admisible"
          % (critico[5], critico[3], 100 * critico[5] / critico[3]))
    print()
    if not malos:
        print("  LOS %d PANOS CUMPLEN, y cumplen con la inercia FISURADA, que es la" % len(filas))
        print("  hipotesis desfavorable. El peralte de %.2f m que salio de la Tabla" % E_LOSA)
        print("  9.1 resiste tambien la verificacion de deflexiones que el 9.6.2.1")
        print("  exige cuando la losa soporta tabiques. El predimensionamiento")
        print("  queda confirmado por los dos caminos.")
    else:
        print("  NO CUMPLEN %d pano(s) con inercia fisurada:" % len(malos))
        for f in malos:
            print("     pano %d (L = %.2f m): %.4f contra %.4f" % (f[0], f[1], f[5], f[3]))
        print()
        print("  Antes de subir el peralte corresponde calcular la inercia EFECTIVA")
        print("  Ie del 9.6.2.3, que queda ENTRE la bruta y la fisurada: acotar por")
        print("  la fisurada es conservador y puede estar exigiendo de mas.")
    print()
    print("  POR QUE ESTA VERIFICACION NO ESTABA: la Tabla 9.1 se aplico sin leer")
    print("  su condicion de aplicabilidad. El 9.6.2.1 la limita a elementos que")
    print("  NO soporten tabiques susceptibles de danarse, y este aligerado los")
    print("  soporta. Es el mismo patron de siempre: el error no fue un calculo")
    print("  mal hecho sino una verificacion que faltaba.")


def control(filas, lim, Ig, Icr):
    print()
    print("=" * 100)
    print("CONTROL")
    print("=" * 100)
    assert Icr < Ig, "la inercia fisurada tiene que ser menor que la bruta"
    print("  [ok] I fisurada (%.0f) < I bruta (%.0f)" % (Icr, Ig))
    # el pano interior debe flechar mas que un extremo de igual luz
    assert COEF["ambos extremos continuos"] > COEF["un extremo continuo"], (
        "un tramo con dos extremos continuos deberia flechar MENOS")
    print("  [ok] mas continuidad en los extremos -> menos flecha")
    for f in filas:
        assert f[5] > f[4], "con inercia fisurada tiene que flechar MAS (pano %d)" % f[0]
    print("  [ok] los %d panos flechan mas con inercia fisurada que con bruta" % len(filas))
    A, y, Ig2, h = seccion_T()
    assert 0 < y < h, "el centroide cae fuera de la seccion"
    print("  [ok] el centroide de la seccion T cae dentro del peralte (%.2f de %.0f cm)"
          % (y, h))
    malos = [f for f in filas if not f[6]]
    assert not malos, ("hay %d pano(s) que no cumplen el 9.6.2.6 ni con la "
                       "hipotesis desfavorable" % len(malos))
    print("  [ok] los %d panos cumplen el 9.6.2.6 con inercia fisurada" % len(filas))


if __name__ == "__main__":
    f, lim, Ig, Icr = informe()
    lectura(f, lim)
    control(f, lim, Ig, Icr)
