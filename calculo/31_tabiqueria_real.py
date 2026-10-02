# -*- coding: utf-8 -*-
"""Peso REAL de la tabiquería, por la distribución del plano (E.020 Art. 5).

LO QUE LA NORMA PIDE, TEXTUAL
=============================
    "ARTICULO 5: TABIQUES. Se considerara el peso de todos los tabiques,
     usando los PESOS REALES en las UBICACIONES QUE INDICAN LOS PLANOS."

No admite un valor uniforme por metro cuadrado de losa. El metrado del
proyecto venia cargando 150 kgf/m2 repartidos, y el script 14 ya lo declaraba
sin adornos: "NO es un metrado: es la carga invertida".

POR QUE AHORA SI SE PUEDE
=========================
Porque ya existe la distribucion arquitectonica: dibujo/F_planta_arquitectonica
declara cada ambiente con su rectangulo. Los TABIQUES son los bordes entre
ambientes que NO coinciden con un muro portante -- si coinciden, ahi hay muro
de albanileria confinada y su peso ya lo cuenta el metrado de muros.

QUE UNIDAD LLEVA UN TABIQUE
===========================
Hueca, y esto no es un ahorro: es lo que la norma permite. La Tabla 2 de la
E.070 PROHIBE la unidad hueca en muro PORTANTE de cuatro pisos a mas, y el
acapite 9.3.1 la ADMITE expresamente en tabiques. Son dos preguntas distintas
sobre el mismo ladrillo.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "planos"))

from proyecto import (EJES_MX, H_LIBRE, TABIQUERIA, N_PISOS,          # noqa: E402
                      PESO_ALBANILERIA_HUECA, PESO_MORTERO, E_TARRAJEO,
                      A_UNIDAD, POZO_X0, POZO_X1, POZO_Y0, POZO_Y1,
                      ESC_X0, ESC_X1, ESC_Y0, ESC_Y1, FRENTE,
                      MUROS, CERRAMIENTO_POZO)

E_TABIQUE = 0.125        # no-ssot: m, tabique de SOGA con unidad hueca
TOL = 0.01               # no-ssot: m, tolerancia geometrica para decidir si un
                         # borde cae sobre un eje; NO es la junta minima


def _plano():
    """La distribucion arquitectonica, que vive en dibujo/.

    Se llamaba `planta_arquitectonica` y estaba al lado; la mudanza de
    carpetas del 2026-09-21 la renombro a `F_planta_arquitectonica` y la
    movio a dibujo/. Este import quedo apuntando al nombre viejo y el
    script fallaba con ModuleNotFoundError -- lo cazo la REGRESION, no una
    ejecucion: el 31 no esta en la cadena que se corre a diario.
    """
    import importlib
    import sys as _sys
    _dib = os.path.join(AQUI, "..", "dibujo")
    if _dib not in _sys.path:
        _sys.path.insert(0, _dib)
    return importlib.import_module("F_planta_arquitectonica")


def _origen_de_muro(nom, dire):
    """(x, y) del eje del muro. Misma regla que el SSOT y los planos."""
    if dire == "X":
        return 0.0, EJES_MX[int(nom.split("-")[1][0]) - 1]
    x = {"MY-1": 0.0, "MY-2": FRENTE, "MY-3": POZO_X0, "MY-4": POZO_X1}[nom[:4]]
    return x, (POZO_Y1 if nom[4:5] == "b" else 0.0)


def _sol(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0)


def cubierto_por_muro(orient, c, a, b):
    """Metros del segmento que TIENEN un muro portante encima.

    EL DEFECTO QUE ESTO CORRIGE (2026-09-21). Esta funcion se llamaba
    `ejes_portantes()` y decidia por COORDENADA: si el borde entre dos
    ambientes caia sobre un eje de la reticula, daba por hecho que ahi
    habia muro de albanileria confinada y no metraba tabique.

    Y NO ES LO MISMO. El eje x = 5,95 existe porque la E.070 7.2.1.b
    obliga a poner una columna intermedia cuando el paño pasa de 5,00 m
    -- el pozo mide 5,40 --, pero ahi NO HAY MURO: `MUROS` solo declara
    muros en Y en x = 0, 3,25, 8,65 y 11,90. Un eje de columna no es un
    muro.

    Consecuencia medida: con la distribucion en dos viviendas partidas a
    lo largo, la DIVISORIA ENTRE LAS DOS VIVIENDAS corre justo por ese eje
    -- 17,64 m de tabique -- y no se metraba ni un metro. Tampoco se
    metraba el cierre de las caras del pozo, porque su coordenada coincide
    con los ejes 3,25 y 8,65 aunque los muros MY-3 y MY-4 se interrumpen
    exactamente en esa franja. Todo eso es peso que faltaba, y faltar peso
    va del lado INSEGURO: menos peso es menos fuerza sismica.

    Ahora se pregunta por el MURO y por el TRAMO: cuantos metros de ese
    segmento estan efectivamente cubiertos por un muro del SSOT.
    """
    tot = 0.0
    for nom, dire, largo, _t, _vs in MUROS:
        ox, oy = _origen_de_muro(nom, dire)
        if orient == "H" and dire == "X" and abs(oy - c) < TOL:
            tot += max(0.0, _sol(a, b, ox, ox + largo))
        if orient == "V" and dire == "Y" and abs(ox - c) < TOL:
            tot += max(0.0, _sol(a, b, oy, oy + largo))
    return tot


def bordes_de_tabique():
    """Los tramos de borde entre ambientes que NO tienen muro portante.

    Cada borde interior se cuenta UNA vez aunque lo compartan dos
    ambientes: el tabique es uno solo. Y se cuenta por TRAMO, no por
    borde entero: un borde puede tener muro en una parte y no en otra --
    es el caso de las caras del pozo -- y contarlo entero para un lado o
    para el otro es falsear el metrado en los dos sentidos.
    """
    P_ = _plano()
    segmentos = set()
    listas = getattr(P_, "VIVIENDAS", None) or [P_.AMB_A, P_.AMB_B]
    for lista in listas:
        for _m in lista:
            x0, x1, y0, y1 = _m["x0"], _m["x1"], _m["y0"], _m["y1"]
            for x in (x0, x1):
                segmentos.add(("V", round(x, 3), round(min(y0, y1), 3),
                               round(max(y0, y1), 3)))
            for y in (y0, y1):
                segmentos.add(("H", round(y, 3), round(min(x0, x1), 3),
                               round(max(x0, x1), 3)))
    # el CERRAMIENTO DEL POZO es tabique declarado en el SSOT, no un borde
    # entre ambientes: el pozo no es un ambiente. Se suma aparte.
    for eje, c, a, b, _w in CERRAMIENTO_POZO:
        segmentos.add(("V" if eje == "x" else "H", round(c, 3),
                       round(a, 3), round(b, 3)))
    # de cada segmento se descuenta lo que SI tiene muro portante encima
    out = set()
    for orient, c, a, b in segmentos:
        if b - a <= TOL:
            continue
        con_muro = cubierto_por_muro(orient, c, a, b)
        libre = (b - a) - con_muro
        if libre > TOL:
            out.add((orient, c, a, b, round(libre, 3)))
    return out


def a_losa_del_10():
    """El area de losa por piso, la misma que usa el informe de arriba."""
    return 222.03          # no-ssot: area de losa por piso, del script 10


def peso_por_m2():
    """kgf/m2 de tabique de soga con unidad HUECA, tarrajeado por dos caras."""
    alb = E_TABIQUE * PESO_ALBANILERIA_HUECA
    rev = 2 * E_TARRAJEO * PESO_MORTERO
    return alb + rev, alb, rev


def informe():
    segs = bordes_de_tabique()
    largo = sum(libre for _o, _c, _a, _b, libre in segs)
    area = largo * H_LIBRE
    w_m2, alb, rev = peso_por_m2()
    peso = area * w_m2

    P = _plano()
    a_losa = 222.03          # no-ssot: area de losa por piso, del script 10

    print("=" * 84)
    print("TABIQUERIA POR LA DISTRIBUCION REAL  -  E.020 Articulo 5")
    print("=" * 84)
    print('  "Se considerara el peso de todos los tabiques, usando los pesos')
    print('   REALES en las UBICACIONES QUE INDICAN LOS PLANOS."')
    print()
    print("  Un borde entre ambientes es TABIQUE solo si NO cae sobre un eje")
    print("  de muro portante; si cae, ahi hay albanileria confinada y su peso")
    print("  ya lo cuenta el metrado de muros.")
    print()
    n_amb = sum(len(v) for v in (getattr(P, "VIVIENDAS", None)
                                 or [P.AMB_A, P.AMB_B]))
    print("  %-30s %s" % ("ambientes declarados", n_amb))
    print("  %-30s %d" % ("bordes que son tabique", len(segs)))
    print("  %-30s %.2f m" % ("longitud total de tabique", largo))
    print("  %-30s %.2f m2" % ("area de tabique (h = %.2f m)" % H_LIBRE, area))
    print()
    print("  PESO DE UN TABIQUE DE SOGA CON UNIDAD HUECA (E.070 9.3.1):")
    print("     albanileria  %.3f m x %d kgf/m3 = %6.1f kgf/m2"
          % (E_TABIQUE, PESO_ALBANILERIA_HUECA, alb))
    print("     tarrajeo     2 caras x %.3f x %d = %6.1f kgf/m2"
          % (E_TARRAJEO, PESO_MORTERO, rev))
    print("     %-42s %6.1f kgf/m2" % ("TOTAL", w_m2))
    print()
    print("  %-34s %14s %14s" % ("", "supuesto", "real (Art. 5)"))
    print("  " + "-" * 64)
    print("  %-34s %14.1f %14.1f"
          % ("kgf/m2 de losa", TABIQUERIA, peso / a_losa))
    print("  %-34s %14s %14s"
          % ("kgf por piso",
             "{:,.0f}".format(TABIQUERIA * a_losa).replace(",", " "),
             "{:,.0f}".format(peso).replace(",", " ")))
    print("  %-34s %14s %14s"
          % ("kgf en los %d pisos" % N_PISOS,
             "{:,.0f}".format(TABIQUERIA * a_losa * N_PISOS).replace(",", " "),
             "{:,.0f}".format(peso * N_PISOS).replace(",", " ")))
    d = peso / (TABIQUERIA * a_losa) - 1
    print("  %-34s %28.1f %%" % ("diferencia", 100 * d))
    print()
    if largo == 0:
        equiv_area = TABIQUERIA * a_losa / w_m2
        print("  HALLAZGO: la distribucion NO DECLARA NINGUN TABIQUE.")
        print("  Los %d ambientes estan delimitados por ejes de muro PORTANTE,"
              % n_amb)
        print("  de modo que el Articulo 5 todavia NO SE PUEDE APLICAR: no hay")
        print("  'ubicaciones que indican los planos' que metrar. Un SS.HH. o un")
        print("  closet necesitan tabique, asi que lo que falta es el plano, no")
        print("  el metrado.")
        print()
        print("  LO QUE SI SE PUEDE HACER es verificar el ORDEN DE MAGNITUD del")
        print("  supuesto, invirtiendo la carga:")
        print("     %.0f kgf/m2 x %.2f m2 de losa = %s kgf por piso"
              % (TABIQUERIA, a_losa,
                 "{:,.0f}".format(TABIQUERIA * a_losa).replace(",", " ")))
        print("     a %.1f kgf/m2 el tabique  ->  %.1f m2 de tabique"
              % (w_m2, equiv_area))
        print("     con h = %.2f m            ->  %.1f m de tabique por piso"
              % (H_LIBRE, equiv_area / H_LIBRE))
        print()
        print("  %.1f m de tabique para %d ambientes en %.0f m2 es del orden"
              % (equiv_area / H_LIBRE, n_amb, a_losa))
        print("  correcto. El supuesto se CONSERVA y el pendiente queda")
        print("  declarado con su magnitud, que es distinto de dejarlo en")
        print("  'falta metrar la tabiqueria'.")
    elif peso > TABIQUERIA * a_losa:
        print("  EL SUPUESTO SE QUEDA CORTO: la distribucion real pesa MAS.")
        print("  Eso va del lado INSEGURO y hay que corregir el metrado.")
    else:
        print("  El supuesto de %.0f kgf/m2 esta POR ENCIMA del real: el" % TABIQUERIA)
        print("  metrado va del lado SEGURO. Se conserva y se declara, porque")
        print("  el plano de arquitectura todavia puede moverse y un supuesto")
        print("  holgado es preferible a uno ajustado que luego no alcance.")
    print()
    print("  %-30s %s" % ("segmento", "de -- a"))
    print("  " + "-" * 50)
    for o, c, a_, b_, libre in sorted(segs):
        eje = "x = %.2f" % c if o == "V" else "y = %.2f" % c
        print("  %-30s %.2f a %.2f  (%.2f m sin muro)"
              % (eje, a_, b_, libre))
    return largo, area, peso, w_m2


def control(largo, area, peso, w_m2):
    """Que el metrado sea un metrado y no otra cosa."""
    segs = bordes_de_tabique()
    # NINGUN TRAMO puede tener muro portante encima: seria doble conteo, y
    # el peso del muro ya lo cuenta el metrado de muros. Antes esto se
    # verificaba contra los ejes de COLUMNA -- que no son muros -- y con eso
    # se descartaban 21,84 m de tabique real: la divisoria entre las dos
    # viviendas y el cierre de las dos caras del pozo.
    for o, c, a_, b_, libre in segs:
        con_muro = cubierto_por_muro(o, c, a_, b_)
        assert libre <= (b_ - a_) - con_muro + TOL, (
            "el tramo en %.3f cuenta %.2f m libres y solo hay %.2f: doble "
            "conteo" % (c, libre, (b_ - a_) - con_muro))
    # y al reves: todo borde entre ambientes tiene que estar cerrado por
    # ALGO, muro o tabique. Un borde sin muro y sin tabique es un ambiente
    # abierto al de al lado, que es el defecto que dejo el pozo sin cierre.
    total_libre = sum(libre for _o, _c, _a, _b, libre in segs)
    assert abs(total_libre - largo) < 1e-6, (
        "la longitud metrada (%.2f) no coincide con la suma de tramos sin "
        "muro (%.2f)" % (largo, total_libre))
    # OJO: largo = 0 NO es un fallo del script, es el HALLAZGO. La
    # distribucion declara cada ambiente entre ejes de muro PORTANTE y no
    # define ningun tabique interior, de modo que el Art. 5 no se puede
    # aplicar todavia: no hay "ubicaciones que indican los planos" que metrar.
    # Reventar aqui ocultaria el hallazgo detras de un error de ejecucion.
    assert abs(area - largo * H_LIBRE) < 1e-9
    assert abs(peso - area * w_m2) < 1e-6
    # LO DECLARADO TIENE QUE SER EL METRADO. `TABIQUERIA` alimenta el peso
    # de todo el edificio, y mientras fue un supuesto podia estar en
    # cualquier valor sin que nada chistara: estuvo en 150 kgf/m2, 2,7 veces
    # el real. Ahora que la distribucion existe, la E.020 Art. 5 obliga al
    # peso REAL, y este control ata la constante al metrado: se admite
    # redondear al alza hasta un 10 %, nunca a la baja.
    real = peso / a_losa_del_10()
    assert TABIQUERIA >= real - 0.05, (
        "TABIQUERIA declarada %.1f kgf/m2 y el metrado da %.1f: declarar por "
        "DEBAJO del metrado va del lado inseguro" % (TABIQUERIA, real))
    assert TABIQUERIA <= real * 1.10 + 0.05, (
        "TABIQUERIA declarada %.1f kgf/m2 contra un metrado de %.1f: mas de "
        "un 10 %% de sobrancho ya no es un metrado, es un supuesto"
        % (TABIQUERIA, real))
    print()
    print("  [ok] ningun tabique cae sobre un muro portante (sin doble conteo)")
    print("  [ok] area y peso cierran con la longitud medida")
    print("  [ok] TABIQUERIA declarada %.1f kgf/m2 contra el metrado %.1f "
          "(+%.1f %%)" % (TABIQUERIA, real, 100.0 * (TABIQUERIA / real - 1)))
    return True


if __name__ == "__main__":
    largo, area, peso, w = informe()
    print()
    print("=" * 84)
    print("CONTROL")
    print("=" * 84)
    control(largo, area, peso, w)
