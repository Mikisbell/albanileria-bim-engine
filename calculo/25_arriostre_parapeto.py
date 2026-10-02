# -*- coding: utf-8 -*-
"""Diseño del ARRIOSTRE del parapeto y los alféizares. E.070 9.3.5

QUE CIERRA
==========
El script 22 dejo una FALLA declarada: el parapeto de azotea (1,10 m en
voladizo) llega al 124 % del esfuerzo admisible y los alfeizares al 102 %.
Mikis decidio ARRIOSTRAR en vez de bajar la altura, que es lo correcto: bajar
el parapeto a 0,99 m lo deja al filo de la norma y ademas empeora la seguridad
de uso en una azotea.

Este script disena ese arriostre. El 9.3.5 lo exige expresamente:

    "Los arriostramientos seran disenados por metodos racionales de calculo,
     de modo que puedan soportar la carga sismica w especificada en 9.1.6
     actuante contra el plano del muro."

O sea que no alcanza con dibujar una columneta: hay que decir cada cuanto va y
verificar que resiste.

POR QUE EL PARAPETO NO SE PUEDE ARRIOSTRAR ARRIBA
=================================================
La via barata del 22 era pasar del CASO 4 (voladizo, m = 0,5) al CASO 3
(arriostrado en sus bordes horizontales, m = 0,125), que multiplica por dos la
altura admisible. Pero un parapeto de azotea **no tiene borde superior donde
amarrarse**: ES el borde del edificio. Por definicion queda libre arriba.

La salida es arriostrarlo VERTICALMENTE, con columnetas: el pano pasa al
CASO 2 de la Tabla 12 -- tres bordes arriostrados, con el borde libre arriba --
donde "a" es la longitud del borde libre, o sea LA SEPARACION ENTRE COLUMNETAS.
Ese es el numero que este script calcula.
"""
import importlib.util
import math
import os

from proyecto import (PARAPETO, ALFEIZAR, A_UNIDAD, E_TARRAJEO, FC,
                      FRENTE, FONDO, ESPESOR, H_LIBRE)

AQUI = os.path.dirname(os.path.abspath(__file__))


def _cargar(nombre):
    ruta = os.path.join(AQUI, nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "a", ruta)
    mod = importlib.util.module_from_spec(spec)
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


R22 = _cargar("22_tabiques_fuera_del_plano.py")

FY = 4200.0              # no-ssot: kgf/cm2, acero grado 60
PHI_FLEXION = 0.90       # no-ssot: E.060 9.3.2, flexion
B_COLUMNETA = 0.13       # no-ssot: m, ancho = espesor del tabique
H_COLUMNETA = 0.15       # no-ssot: m, peralte minimo de una columneta de amarre
# EL ARMADO ADOPTADO, como dato y no solo como mensaje: la lamina E-05 lo lee
# de aca (antes dibujaba otro: 15 x 15 con 4 o 3/8" bajo una solera).
N_BARRAS_COL = 2         # no-ssot: barras de 3/8" de la columneta
ESTRIBO_COL = "6 mm"     # no-ssot: diametro del estribo
PASO_ESTRIBO_COL = 20    # no-ssot: cm
ANCLAJE_COL = 30         # no-ssot: cm de penetracion en la losa de azotea
AREA_3_8 = 0.71          # no-ssot: cm2, varilla de 3/8"

# E.020 Articulo 8.2, Barandas y Parapetos. El texto es explicito en que el
# sismo NO es la unica carga:
#
#   "a) Las barandas y parapetos se disenaran para las fuerzas indicadas en la
#    NTE E.030 Diseno Sismorresistente, las cargas de viento cuando sean
#    aplicables Y LAS QUE SE INDICAN A CONTINUACION.
#    b) ... seran disenados para resistir la aplicacion simultanea o no de las
#    fuerzas indicadas en la Tabla 2, ambas aplicadas EN SU PARTE SUPERIOR,
#    tomandose LA COMBINACION MAS DESFAVORABLE."
#
# Tabla 2, fila "Pozo para escaleras, balcones y techos en general": carga
# horizontal 0,60 kN/m (60 kgf/m). La fila de 30 kgf/m es para VIVIENDAS
# UNIFAMILIARES y este edificio es MULTIFAMILIAR, asi que no aplica.
#
# ESTA VERIFICACION FALTABA. El parapeto se habia disenado solo con el sismo
# del 9.1.6, y el sismo NO gobierna: la carga del 8.2 da un 26 % mas de
# momento. Lo destapo auditar la Clase 02 contra la norma.
H_TABLA2 = 60.0          # no-ssot: kgf/m, E.020 Tabla 2, techos en general
V_TABLA2 = 60.0          # no-ssot: kgf/m, carga VERTICAL de la misma fila
MIN_TOTAL = 100.0        # no-ssot: kgf, "en ningun caso ... menores de 1,0 kN"


def w_equivalente_8_2(altura):
    """La carga LINEAL del 8.2 llevada a distribuida equivalente, en kgf/m2.

    La Tabla 2 da una fuerza por metro aplicada EN LA PARTE SUPERIOR del
    parapeto. Para compararla con la w distribuida del 9.1.6 se busca la
    distribuida que produce el MISMO momento en la base del voladizo:

        w_eq . h^2 / 2  =  H . h    ->    w_eq = 2H / h
    """
    return 2.0 * H_TABLA2 / altura


def carga_que_gobierna(altura, e_bruto):
    """(w, cual) -- la mayor entre el sismo del 9.1.6 y el 8.2 de la E.020."""
    w_sismo = R22.carga_w(e_bruto)
    w_8_2 = w_equivalente_8_2(altura)
    if w_8_2 > w_sismo:
        return w_8_2, "E.020 8.2 + Tabla 2"
    return w_sismo, "sismo E.070 9.1.6"


def separacion_maxima(a_altura, t, e_bruto, w_externa=None):
    """Separacion maxima de columnetas para que el pano CUMPLA el 9.3.3.

    CASO 2 de la Tabla 12: tres bordes arriostrados, borde libre ARRIBA.
      a = longitud del borde libre = separacion entre columnetas
      b = altura del pano
    Se barre la separacion y se toma la mayor que todavia cumple.
    """
    mejor = None
    s = 0.40
    while s <= 6.0:
        f = R22.verificar("x", 2, a=s, b=a_altura, t_efectivo=t,
                          e_bruto=e_bruto, w_externa=w_externa)
        if f["cumple"]:
            mejor = (s, f)
        else:
            break
        s += 0.05   # no-ssot: 5 cm de separacion constructiva, no la excentricidad accidental
    return mejor


def momento_en_columneta(w, s, altura):
    """La columneta recibe la carga de MEDIO pano a cada lado y trabaja en voladizo.

    Es el 9.3.5: el arriostre tiene que soportar la misma w. Se la trata como
    un voladizo empotrado en la losa de azotea, cargado con w por su ancho
    tributario (la separacion s).
    """
    w_lineal = w * s                      # kgf/m de altura de columneta
    return w_lineal * altura ** 2 / 2.0   # kgf.m, momento en la base


def acero_columneta(M_kgf_m, b, h):
    """As necesario por flexion. E.060: As = M/(phi fy jd), con jd ~ 0,9 d."""
    d = (h - 0.04) * 100.0                # cm, con 4 cm de recubrimiento   # no-ssot: 4 cm de recubrimiento de la columneta
    M_kgf_cm = M_kgf_m * 100.0
    return M_kgf_cm / (PHI_FLEXION * FY * 0.9 * d), d   # no-ssot: phi = 0,9 de flexion (E.060 9.3.2.1)


def informe():
    print("=" * 100)
    print("ARRIOSTRE DEL PARAPETO Y LOS ALFEIZARES  -  E.070 9.3.5")
    print("=" * 100)
    print()
    e_bruto = A_UNIDAD + 2 * E_TARRAJEO
    t = A_UNIDAD
    w_sismo = R22.carga_w(e_bruto)
    print("  DOS CARGAS COMPITEN, y el sismo NO es la que gobierna:")
    print()
    print("     E.070 9.1.6, sismo perpendicular   w = %.1f kgf/m2" % w_sismo)
    print("     E.020 Art. 8.2 + Tabla 2           H = %.0f kgf/m en la parte"
          % H_TABLA2)
    print("        superior; equivale a w = 2H/h distribuida")
    print()
    print("  El 8.2 dice que el parapeto se disena para las fuerzas de la")
    print("  E.030 'Y LAS QUE SE INDICAN A CONTINUACION', tomando 'la")
    print("  combinacion mas desfavorable'. La fila de 30 kgf/m de la Tabla 2")
    print("  es para VIVIENDAS UNIFAMILIARES; este edificio es MULTIFAMILIAR,")
    print("  asi que le corresponde 'techos en general' con %.0f kgf/m."
          % H_TABLA2)
    print()
    print("  Espesor efectivo t = %.2f m  ·  bruto e = %.3f m" % (t, e_bruto))
    print()
    print("  POR QUE COLUMNETAS Y NO AMARRE SUPERIOR: un parapeto de azotea no")
    print("  tiene borde de arriba donde amarrarse, ES el borde. Queda libre")
    print("  arriba por definicion, asi que se arriostra VERTICALMENTE y el")
    print("  pano pasa al CASO 2 de la Tabla 12 (tres bordes).")
    print()
    print("  %-26s %8s %10s %9s %9s %s"
          % ("elemento", "altura", "sep. max", "m", "fm", "9.3.3   gobierna"))
    print("  " + "-" * 82)
    out = []
    for nom, altura in (("parapeto de azotea", PARAPETO),
                        ("alfeizar de ventana", ALFEIZAR)):
        # el alfeizar NO es baranda ni parapeto de borde: el 8.2 no lo alcanza,
        # de modo que a el solo lo carga el sismo. Al parapeto de azotea SI.
        es_parapeto = nom.startswith("parapeto")
        w, cual = (carga_que_gobierna(altura, e_bruto) if es_parapeto
                   else (w_sismo, "sismo E.070 9.1.6"))
        r = separacion_maxima(altura, t, e_bruto, w_externa=w)
        assert r, "no hay separacion que haga cumplir a %s" % nom
        s, f = r
        # se adopta un valor redondeado hacia abajo, constructivo
        s_adopt = math.floor(s * 10) / 10.0
        fa = R22.verificar("x", 2, a=s_adopt, b=altura, t_efectivo=t,
                           e_bruto=e_bruto, w_externa=w)
        out.append((nom, altura, s_adopt, fa, w))
        print("  %-26s %8.2f %10.2f %9.4f %9.3f %s   %s"
              % (nom, altura, s_adopt, fa["m"], fa["fm"],
                 "cumple" if fa["cumple"] else "NO", cual))
    print()
    print("  (separacion ADOPTADA, redondeada hacia abajo desde la maxima que")
    print("   cumple, para que quede margen constructivo)")
    return out, w


def disenar_columnetas(out, w):
    print()
    print("=" * 100)
    print("LA COLUMNETA  -  el 9.3.5 pide disenarla, no solo dibujarla")
    print("=" * 100)
    print()
    print("  Se la trata como VOLADIZO empotrado en la losa, cargada con w por")
    print("  su ancho tributario (la separacion). Seccion %.2f x %.2f m."
          % (B_COLUMNETA, H_COLUMNETA))
    print()
    print("  %-26s %9s %12s %11s %11s %s"
          % ("elemento", "sep. (m)", "M base", "As req", "As 2o3/8\"", "veredicto"))
    print("  " + "-" * 88)
    filas = []
    for nom, altura, s, f, w_el in out:
        # LA CARGA DE CADA ELEMENTO, no la del ultimo evaluado. Usaba `w`, que
        # al salir de informe() es la del alfeizar (sismo, 86,4 kgf/m2), y al
        # parapeto lo gobierna la E.020 8.2 (109,1): el momento de su
        # columneta salia 125,5 kgf.m en vez de 158,4, del lado inseguro.
        M = momento_en_columneta(w_el, s, altura)
        As, d = acero_columneta(M, B_COLUMNETA, H_COLUMNETA)
        As_prov = N_BARRAS_COL * AREA_3_8
        ok = As_prov >= As
        filas.append((nom, s, M, As, As_prov, ok, d))
        print("  %-26s %9.2f %12.1f %11.3f %11.2f %s"
              % (nom, s, M, As, As_prov, "cumple" if ok else "NO <<<"))
    print()
    print("  ARMADO ADOPTADO: columneta de %.0f x %.0f cm con %d o 3/8\" y"
          % (B_COLUMNETA * 100, H_COLUMNETA * 100, N_BARRAS_COL))
    print("  estribos de %s cada %d cm, anclada en la losa de azotea con"
          % (ESTRIBO_COL, PASO_ESTRIBO_COL))
    print("  %.0f cm de penetracion." % ANCLAJE_COL)
    print()
    print("  CUANTAS HACEN FALTA, en este edificio:")
    per = 2 * (FRENTE + FONDO)
    for nom, altura, s, f, _w in out:
        if "parapeto" in nom:
            n = math.ceil(per / s) + 1
            print("     parapeto: perimetro de azotea %.2f m / %.2f m = %d columnetas"
                  % (per, s, n))
    return filas


def separacion_parapeto():
    """La separacion ADOPTADA de las columnetas del parapeto, sin imprimir."""
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        out, _w = informe()
    s = [x[2] for x in out if x[0].startswith("parapeto")]
    assert len(s) == 1, s
    return s[0]


def control(out, filas, w):
    print()
    print("=" * 100)
    print("CONTROL")
    print("=" * 100)
    # 1. con el arriostre, TODO cumple el 9.3.3
    for nom, altura, s, f, _w in out:
        assert f["cumple"], "%s sigue sin cumplir con separacion %.2f" % (nom, s)
    print("  [ok] los %d elementos cumplen el 9.3.3 una vez arriostrados" % len(out))
    # 2. la columneta resiste la misma w (9.3.5)
    for nom, s, M, As, As_prov, ok, d in filas:
        assert ok, "la columneta de %s no resiste: As %.3f > %.2f" % (nom, As, As_prov)
    print("  [ok] las columnetas resisten la carga w del 9.3.5 con 2 o 3/8\"")
    # 3. el arriostre MEJORA: sin el, el voladizo fallaba
    sin_arr = R22.verificar("x", 4, a=PARAPETO, b=0.0,
                            t_efectivo=A_UNIDAD,
                            e_bruto=A_UNIDAD + 2 * E_TARRAJEO)
    con_arr = [f for n, a, s, f, _w in out if "parapeto" in n][0]
    assert sin_arr["fm"] > con_arr["fm"], "el arriostre deberia BAJAR el esfuerzo"
    print("  [ok] el parapeto baja de %.3f a %.3f kgf/cm2 (%.0f %% menos)"
          % (sin_arr["fm"], con_arr["fm"],
             100 * (1 - con_arr["fm"] / sin_arr["fm"])))
    print("  [ok] la FALLA del 9.3.3 queda resuelta por diseno, no por excepcion")


if __name__ == "__main__":
    out, w = informe()
    filas = disenar_columnetas(out, w)
    control(out, filas, w)
