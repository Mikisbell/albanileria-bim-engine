# -*- coding: utf-8 -*-
"""Muros NO portantes ante sismo PERPENDICULAR a su plano. E.070 9.1.6 / 9.1.7 / 9.3.3

QUE PENDIENTE CIERRA
====================
`verificaciones.py` declaraba desde el principio:

    (2, "E.070 9.3.3", "tabique fuera del plano: 6Ms/t2 <= 1,5", PENDIENTE,
        "el tabique hoy es solo una carga de 150 kgf/m2; falta su Ms (Tabla 12)")

Faltaba la Tabla 12. Mikis la aportó en imagen el 2026-09-19 y con ella se
puede cerrar. Es una verificacion REAL, no un tramite: un tabique que se cae
fuera de su plano mata gente aunque la estructura no se haya movido.

LAS DOS NUMERACIONES DE LA E.070 — leer antes de citar
====================================================
Circulan dos ediciones y numeran distinto. Las formulas de aca son
**9.1.6 y 9.1.7** en el compendio RNE de 55 pp. (el PDF de `06-normas/`, que es
el que este proyecto cita) y **29.6 y 29.7** en la edicion de El Peruano. El
contenido es identico; se verifico contra las dos. Si el corrector usa la otra
edicion, la equivalencia esta declarada en el informe.

LA CADENA DE CALCULO
====================
    w  = 0,8 . Z . U . C1 . gamma . e         (9.1.6)  carga por m2 de muro
    Ms = m . w . a^2                          (9.1.7)  momento por metro
    fm = 6 Ms / t^2  <=  ft' = 1,5 kgf/cm2    (9.3.3)  el veredicto

DE DONDE SALE C1, QUE ES EL DATO QUE FALTABA
============================================
La E.070 dice "coeficiente sismico especificado en la NTE E.030" y no da valor.
La E.030-2026 lo trae en el **Articulo 57, Tabla N.o 15**: para "muros y
tabiques dentro de una edificacion", **C1 = 2,0**. Conviene notar que la
E.030-2026 reformulo el capitulo de elementos no estructurales (Arts. 55 a 57)
respecto de ediciones anteriores, asi que este valor hay que leerlo de la
edicion vigente y no de memoria.

EL CASO DE LA TABLA 12 ES LO QUE DECIDE
=======================================
El coeficiente "m" cambia por un factor de CUATRO segun como este arriostrado
el pano: 0,125 si lo sujetan arriba y abajo, y **0,5 si esta en voladizo**. Por
eso el parapeto y el alfeizar aislado son los criticos, y no el tabique
interior, que es el que uno mira primero.
"""
from proyecto import (Z, U, PESO_ALBANILERIA_HUECA, E_TARRAJEO, A_UNIDAD,
                      H_LIBRE, PARAPETO, ALFEIZAR)

C1 = 2.0            # no-ssot: E.030-2026 Art. 57, Tabla 15, "muros y tabiques"
FT_ADM = 1.5        # no-ssot: kgf/cm2, esfuerzo admisible en traccion por flexion
C_096 = 0.8         # no-ssot: el 0,8 de la formula 9.1.6

# TABLA 12 de la E.070, transcrita de la imagen del 2026-09-19.
CASO_1 = [(1.0, 0.0479), (1.2, 0.0627), (1.4, 0.0755), (1.6, 0.0862),   # no-ssot: relaciones b/a de la Tabla 12 de la E.070
          (1.8, 0.0948), (2.0, 0.1017), (3.0, 0.118), (float("inf"), 0.125)]
CASO_2 = [(0.5, 0.060), (0.6, 0.074), (0.7, 0.087), (0.8, 0.097), (0.9, 0.106),   # no-ssot: relaciones b/a de la Tabla 12 de la E.070
          (1.0, 0.112), (1.5, 0.128), (2.0, 0.132), (float("inf"), 0.133)]   # no-ssot: relaciones b/a de la Tabla 12 de la E.070
M_CASO_3 = 0.125    # arriostrado solo en sus bordes horizontales; a = altura
M_CASO_4 = 0.5      # muro en VOLADIZO; a = altura


def m_interpolado(tabla, ba):
    """m de la Tabla 12 para una relacion b/a, interpolando entre filas.

    La tabla da valores discretos. Se interpola linealmente y, fuera de rango,
    se toma el extremo: por debajo del primer b/a el m solo puede ser menor
    (mas favorable), y tomar el primero es conservador.
    """
    if ba <= tabla[0][0]:
        return tabla[0][1]
    for (x0, m0), (x1, m1) in zip(tabla, tabla[1:]):
        if ba <= x1:
            if x1 == float("inf"):
                return m1
            return m0 + (m1 - m0) * (ba - x0) / (x1 - x0)
    return tabla[-1][1]


def carga_w(e_bruto, gamma=PESO_ALBANILERIA_HUECA):
    """9.1.6: w = 0,8 Z U C1 gamma e, en kgf/m2 de muro."""
    return C_096 * Z * U * C1 * gamma * e_bruto


def verificar(nombre, caso, a, b, t_efectivo, e_bruto,
              gamma=PESO_ALBANILERIA_HUECA, w_externa=None):
    """Devuelve el dict con toda la cadena, para poder auditarla paso a paso."""
    if caso == 1:
        m = m_interpolado(CASO_1, b / a)
    elif caso == 2:
        m = m_interpolado(CASO_2, b / a)
    elif caso == 3:
        m = M_CASO_3
    else:
        m = M_CASO_4
    # w_externa permite meter una carga que NO es la sismica del 9.1.6 --
    # el caso concreto es la del Art. 8.2 de la E.020 para parapetos, que
    # resulta MAYOR que el sismo y por lo tanto gobierna. Por defecto no
    # cambia nada.
    w = carga_w(e_bruto, gamma) if w_externa is None else w_externa
    Ms = m * w * a ** 2                      # kgf.m/m
    # fm = 6 Ms / t^2. Ms en kgf.m/m y t en m dan kgf/m2; /1e4 -> kgf/cm2
    fm = 6.0 * Ms / (t_efectivo ** 2) / 1.0e4
    return {"nombre": nombre, "caso": caso, "m": m, "a": a, "b": b,
            "t": t_efectivo, "e": e_bruto, "w": w, "Ms": Ms, "fm": fm,
            "cumple": fm <= FT_ADM, "uso": fm / FT_ADM}


def elementos():
    """Los tres elementos no portantes de este proyecto, con su arriostre real."""
    e_bruto = A_UNIDAD + 2 * E_TARRAJEO      # tabique de soga, con tarrajeo
    t = A_UNIDAD                              # el espesor efectivo, SIN tarrajeo
    h = H_LIBRE
    return [
        # tabique interior de un ambiente: lo sujetan la losa arriba, el piso
        # abajo y los muros portantes a los lados -> CUATRO bordes.
        verificar("tabique interior (4 bordes)", 1, a=h, b=3.36, t_efectivo=t, e_bruto=e_bruto),
        # tabique largo sin muro a un lado: tres bordes, el libre es el vertical
        verificar("tabique con un borde libre", 2, a=h, b=3.36, t_efectivo=t, e_bruto=e_bruto),
        # alfeizar bajo ventana: la ventana lo deja LIBRE arriba -> voladizo
        verificar("alfeizar aislado (voladizo)", 4, a=ALFEIZAR, b=0.0, t_efectivo=t, e_bruto=e_bruto),
        # parapeto de azotea: libre arriba por definicion -> voladizo
        verificar("parapeto de azotea (voladizo)", 4, a=PARAPETO, b=0.0, t_efectivo=t, e_bruto=e_bruto),
    ]


def informe():
    print("=" * 100)
    print("MUROS NO PORTANTES ANTE SISMO PERPENDICULAR  -  E.070 9.1.6 / 9.1.7 / 9.3.3")
    print("=" * 100)
    print()
    e_bruto = A_UNIDAD + 2 * E_TARRAJEO
    print("  DATOS")
    print("     Z = %.2f   U = %.2f   C1 = %.1f  (E.030-2026 Art. 57, Tabla 15)"
          % (Z, U, C1))
    print("     gamma = %.0f kgf/m3 (arcilla HUECA: el tabique va con la unidad"
          % PESO_ALBANILERIA_HUECA)
    print("     local, que el 9.3.1 admite en muros no portantes)")
    print("     espesor bruto e = %.2f + 2 x %.3f = %.3f m  (con tarrajeo, 9.1.6)"
          % (A_UNIDAD, E_TARRAJEO, e_bruto))
    print("     espesor efectivo t = %.2f m  (SIN tarrajeo: el mortero de"
          % A_UNIDAD)
    print("     revoque no se cuenta como seccion resistente)")
    print()
    print("     w = 0,8 x %.2f x %.2f x %.1f x %.0f x %.3f = %.1f kgf/m2"
          % (Z, U, C1, PESO_ALBANILERIA_HUECA, e_bruto, carga_w(e_bruto)))
    print()
    print("  %-30s %4s %7s %6s %10s %9s %8s %s"
          % ("elemento", "caso", "m", "a (m)", "Ms (kgf.m/m)", "fm", "uso", "9.3.3"))
    print("  " + "-" * 96)
    filas = elementos()
    for f in filas:
        print("  %-30s %4d %7.4f %6.2f %10.1f %9.3f %7.0f%% %s"
              % (f["nombre"], f["caso"], f["m"], f["a"], f["Ms"], f["fm"],
                 100 * f["uso"], "cumple" if f["cumple"] else "NO CUMPLE <<<"))
    print()
    print("  Limite: ft' = %.1f kgf/cm2 (esfuerzo admisible en traccion por flexion)"
          % FT_ADM)
    return filas


def lectura(filas):
    print()
    print("=" * 100)
    print("LECTURA  -  el arriostre decide, no el espesor")
    print("=" * 100)
    print()
    v = [f for f in filas if f["caso"] == 4]
    a4 = [f for f in filas if f["caso"] == 1][0]
    print("  El mismo tabique, con el mismo espesor y el mismo ladrillo, pasa de")
    print("  m = %.4f con cuatro bordes arriostrados a m = %.1f en voladizo: un"
          % (a4["m"], M_CASO_4))
    print("  factor de %.0f. Por eso los criticos no son los tabiques interiores"
          % (M_CASO_4 / a4["m"]))
    print("  sino los elementos LIBRES ARRIBA, que uno tiende a no mirar.")
    print()
    malos = [f for f in filas if not f["cumple"]]
    if malos:
        print("  NO CUMPLEN:")
        for f in malos:
            print("     %-32s fm = %.3f contra %.1f  (%.0f %% del limite)"
                  % (f["nombre"], f["fm"], FT_ADM, 100 * f["uso"]))
        print()
        print("  QUE HACER, en orden de costo:")
        print("   1. ARRIOSTRAR. Una columneta o viga de amarre cambia el caso de")
        print("      la Tabla 12 y con el la m. Es lo mas barato: no toca el muro.")
        print("   2. REDUCIR a. El momento va con a AL CUADRADO, asi que bajar la")
        print("      altura del parapeto rinde el doble que engrosarlo.")
        print("   3. ENGROSAR. fm va con 1/t^2, pero w va con e: engrosar sube la")
        print("      carga y baja el esfuerzo a la vez, y gana el 1/t^2.")
        print("   4. ARMARLO. Con refuerzo deja de ser albanileria simple y el")
        print("      9.3.3 ya no aplica: pasa a disenarse como armada.")
    else:
        print("  Los cuatro elementos cumplen.")
    print()
    print("  LO QUE ESTA VERIFICACION NO CUBRE: el anclaje del propio")
    print("  arriostre. El 9.3.5 pide disenar los arriostramientos para la misma")
    print("  carga w. Queda declarado como pendiente de detalle.")


def solucion(filas):
    """No alcanza con decir que no cumple: hay que decir CUANTO hay que cambiar."""
    import math
    print()
    print("=" * 100)
    print("SOLUCION DIMENSIONADA  -  cuanto arriostre hace falta, con numero")
    print("=" * 100)
    print()
    e_bruto = A_UNIDAD + 2 * E_TARRAJEO
    w = carga_w(e_bruto)
    t_cm = A_UNIDAD

    # (1) altura maxima que aguanta un elemento EN VOLADIZO sin arriostrar
    #     fm = 6 m w a^2 / t^2 / 1e4 <= ft'  ->  a <= raiz(ft' t^2 1e4 /(6 m w))
    a_max = math.sqrt(FT_ADM * t_cm ** 2 * 1.0e4 / (6.0 * M_CASO_4 * w))
    print("  (1) VOLADIZO SIN ARRIOSTRAR: altura maxima admisible")
    print("      a_max = raiz(ft' t^2 . 1e4 / (6 m w)) = %.2f m" % a_max)
    print("      parapeto actual %.2f m  ->  %s" % (PARAPETO,
          "cumple" if PARAPETO <= a_max else "EXCEDE en %.0f cm" % ((PARAPETO - a_max) * 100)))
    print("      alfeizar actual %.2f m  ->  %s" % (ALFEIZAR,
          "cumple" if ALFEIZAR <= a_max else "EXCEDE en %.0f cm" % ((ALFEIZAR - a_max) * 100)))
    print()

    # (2) el mismo elemento, pero ARRIOSTRADO arriba (caso 3: m = 0,125)
    a_max3 = math.sqrt(FT_ADM * t_cm ** 2 * 1.0e4 / (6.0 * M_CASO_3 * w))
    print("  (2) ARRIOSTRADO ARRIBA Y ABAJO (caso 3, m = %.3f)" % M_CASO_3)
    print("      a_max sube a %.2f m: el arriostre multiplica por %.1f la altura"
          % (a_max3, a_max3 / a_max))
    print("      admisible SIN tocar el espesor ni el ladrillo. Es la via barata.")
    print()

    # (3) separacion de columnetas para el tabique de tres bordes
    print("  (3) TABIQUE LARGO: separacion de columnetas")
    print("      Con columnetas a ambos lados el pano pasa al CASO 1 (4 bordes),")
    print("      donde m depende de b/a. Se busca la separacion b que cumple:")
    print()
    print("      %8s %8s %10s %9s %s" % ("b (m)", "b/a", "m", "fm", "9.3.3"))
    print("      " + "-" * 48)
    h = H_LIBRE
    b_ok = None
    for b in (1.5, 2.0, 2.5, 3.0, 3.36, 4.0):   # no-ssot: relacion b/a de la Tabla 12, no Df
        f = verificar("x", 1, a=h, b=b, t_efectivo=t_cm, e_bruto=e_bruto)
        if f["cumple"] and b_ok is None:
            b_ok = b
        print("      %8.2f %8.2f %10.4f %9.3f %s"
              % (b, b / h, f["m"], f["fm"], "cumple" if f["cumple"] else "NO"))
    print()
    print("      OJO con la lectura: en el caso 1 la dimension critica \"a\" es la")
    print("      MENOR del pano. Con %.2f m de altura libre, cualquier b mayor" % h)
    print("      que eso deja a = altura, y aumentar b solo empeora (mas m).")
    print("      Conclusion: el tabique alto no se arregla acercando columnetas")
    print("      si ya son mas anchas que altas; se arregla ARRIOSTRANDOLO")
    print("      ARRIBA contra la losa, que es el caso (2).")
    print()
    print("  RECOMENDACION DEL PROYECTO")
    print("   - Parapeto de azotea: arriostrar con columnetas de amarre a la")
    print("     solera de azotea, o bajarlo a %.2f m. Se adopta ARRIOSTRARLO."
          % a_max)
    print("   - Alfeizares: van AISLADOS de la estructura por decision sismica")
    print("     (para no acortar la columna), asi que quedan en voladizo. Se")
    print("     arman con una columneta central o se reducen a %.2f m." % a_max)
    print("   - Tabiques: se conectan a la losa superior con conexion flexible")
    print("     que arriostre sin transmitir carga vertical (caso 3).")
    return a_max, a_max3


def control(filas):
    """Aserciones sobre la cadena de calculo, no sobre el resultado."""
    print()
    print("=" * 100)
    print("CONTROL")
    print("=" * 100)
    # 1. la Tabla 12 esta completa y es monotona creciente en b/a
    for nom, tabla in (("caso 1", CASO_1), ("caso 2", CASO_2)):
        ms = [m for _b, m in tabla]
        assert ms == sorted(ms), "la %s de la Tabla 12 no es monotona" % nom
    print("  [ok] la Tabla 12 es monotona creciente en b/a en los dos casos")
    # 2. el voladizo es SIEMPRE el peor caso
    #
    # AUDITORIA 2026-09-19: este assert pedia M_CASO_3 > max(CASO_1) y por lo
    # tanto NUNCA pudo pasar: los dos valen 0,125. Y valen lo mismo por una
    # razon fisica, no por casualidad -- un pano apoyado en cuatro bordes pero
    # muy alargado (b/a -> infinito) deja de sentir los bordes cortos y trabaja
    # como uno apoyado en dos, que es el caso 3. La Tabla 12 lo refleja
    # haciendo converger el caso 1 al valor del caso 3. El control estaba mal
    # escrito, no la tabla; el script reventaba al final y nadie lo veia porque
    # estaba FUERA del registro de _regresion.py.
    peor_tabulado = max([m for _b, m in CASO_1] + [m for _b, m in CASO_2]
                        + [M_CASO_3])
    assert M_CASO_4 > peor_tabulado, (
        "el voladizo deberia ser el caso mas desfavorable de la Tabla 12")
    assert M_CASO_3 >= max(m for _b, m in CASO_1) - 1e-12, (
        "el caso 3 deberia ser la asintota del caso 1, no quedar por debajo")
    print("  [ok] el voladizo (m = %.1f) es el caso mas desfavorable; el peor"
          % M_CASO_4)
    print("       valor tabulado de los otros tres es %.3f" % peor_tabulado)
    # 3. interpolacion: en los nodos debe devolver el valor tabulado
    for b, m in CASO_1[:-1]:
        assert abs(m_interpolado(CASO_1, b) - m) < 1e-12, (
            "la interpolacion no reproduce el nodo b/a = %.1f" % b)
    print("  [ok] la interpolacion reproduce los nodos tabulados")
    # 4. coherencia fisica: mas altura, mas momento
    bajo = verificar("x", 4, 0.5, 0, A_UNIDAD, A_UNIDAD + 2 * E_TARRAJEO)
    alto = verificar("x", 4, 1.5, 0, A_UNIDAD, A_UNIDAD + 2 * E_TARRAJEO)   # no-ssot: relacion b/a de la Tabla 12, no Df
    assert alto["fm"] > bajo["fm"], "un parapeto mas alto deberia exigir mas"
    print("  [ok] el esfuerzo crece con la altura (va con a al cuadrado)")
    n_mal = len([f for f in filas if not f["cumple"]])
    print("  [i]  %d de %d elementos NO cumplen el 9.3.3" % (n_mal, len(filas)))


if __name__ == "__main__":
    f = informe()
    lectura(f)
    solucion(f)
    control(f)
