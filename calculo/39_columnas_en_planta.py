# -*- coding: utf-8 -*-
u"""Que columna va en cada cruce de la malla: el 8.5.1.1, punto por punto.

LA PREGUNTA QUE LO ORIGINA (Mikis, 2026-09-27). La Tabla 11 distingue
columnas INTERIORES y EXTREMAS, y les da expresiones distintas: la extrema
recibe 1,5 veces el cortante y, sobre todo, es la unica que toma la traccion
`T = F - Pc` del momento. La interior casi siempre queda con refuerzo minimo.
El 19 disena las dos y adopta un tipo de cada una. **Pero la Tabla 11
clasifica la columna DENTRO DE UN MURO, y en una malla una misma columna
pertenece a dos muros a la vez.**

Ahi entra el **8.5.1.1**: *"Cuando se presenten muros que se intercepten
perpendicularmente, se tomara como elemento de refuerzo vertical comun a
ambos muros, en el punto de interseccion, al MAYOR elemento de refuerzo
proveniente del diseno independiente de ambos muros"*.

O sea: la clasificacion no se decide muro por muro, se decide EN EL CRUCE. Y
eso no estaba hecho. El plano asignaba los tipos con una regla puramente
geometrica --`extrema = j in (0, len(ejes)-1)`, es decir la primera y la
ultima columna de cada fila-- que es correcta para los muros X y **ciega para
los muros Y**: los extremos de MY-3a, MY-3b, MY-4a y MY-4b caen en posiciones
INTERMEDIAS de esa fila, y el plano las estaba dibujando como C-1.

Este script construye la malla, pregunta en cada cruce que muros concurren y
si la columna es extrema o interior de cada uno, aplica el 8.5.1.1 y compara
el resultado con lo que el plano asigna hoy.
"""
from __future__ import print_function

import contextlib
import importlib.util
import io as _io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from proyecto import (EJES_MX, ESPESOR, FONDO, FRENTE, MUROS, POZO_Y0,
                      POZO_Y1, ejes_de_columna, ejes_x_rotulados)

TOL = 0.06   # no-ssot: m. Los ejes de columna (3,25) y los de muro (3,30) no
             # coinciden exactamente: el eje de la columna esta corrido medio
             # espesor hacia adentro. 6 cm cubre ese corrimiento y nada mas.


def _mod(nombre):
    ruta = os.path.join(AQUI, nombre)
    spec = importlib.util.spec_from_file_location("_p" + nombre[:2], ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def geometria_de_muros():
    u"""Cada muro con su eje y las coordenadas de SUS columnas.

    Los muros X corren de fachada a fachada sobre un eje `y`; los muros Y
    corren sobre un eje `x` y algunos arrancan despues del pozo. El arranque
    se deriva del LARGO y de la geometria del pozo, no de una tabla aparte:
    una tabla paralela se desincroniza en cuanto alguien mueve un muro.
    """
    xs, _rot = ejes_x_rotulados()
    eje_de = {"MY-1": xs[0], "MY-3": xs[1], "MY-4": xs[3], "MY-2": xs[-1]}
    salida = []
    i_x = 0
    for nom, dire, L, t, vanos in MUROS:
        clave = nom.split()[0]
        locales = ejes_de_columna(nom, dire, L)
        if dire == "X":
            y = EJES_MX[i_x]
            i_x += 1
            puntos = [(x, y) for x in locales]
        else:
            x = eje_de[clave[:4]]
            # los posteriores arrancan al otro lado del pozo
            y0 = POZO_Y1 if clave.endswith("b") else 0.0
            puntos = [(x, y0 + yy) for yy in locales]
        salida.append({"nom": nom, "clave": clave, "dir": dire, "L": L,
                       "puntos": puntos,
                       "extremos": (puntos[0], puntos[-1])})
    return salida


def _mismo(p, q):
    return abs(p[0] - q[0]) <= TOL and abs(p[1] - q[1]) <= TOL


def malla(muros_geo, dis):
    u"""Cada cruce con los muros que concurren y el As que cada uno pide."""
    puntos = []
    for m in muros_geo:
        for p in m["puntos"]:
            if not any(_mismo(p, q["p"]) for q in puntos):
                puntos.append({"p": p, "concurren": []})
    for q in puntos:
        for m in muros_geo:
            for p in m["puntos"]:
                if _mismo(p, q["p"]):
                    extrema = _mismo(p, m["extremos"][0]) or \
                        _mismo(p, m["extremos"][1])
                    d = dis[m["nom"]]
                    q["concurren"].append({
                        "muro": m["clave"], "dir": m["dir"],
                        "extrema": extrema,
                        "As": d["dis_e"]["As"] if extrema else d["dis_i"]["As"],
                    })
                    break
        # EL 8.5.1.1: manda el MAYOR de los disenos que concurren
        q["As_req"] = max(c["As"] for c in q["concurren"])
        q["manda"] = max(q["concurren"], key=lambda c: c["As"])
        q["hay_extrema"] = any(c["extrema"] for c in q["concurren"])
    puntos.sort(key=lambda q: (-q["As_req"], q["p"][0], q["p"][1]))
    return puntos


def asignacion_del_plano(p):
    u"""Que tipo dibuja HOY el plano en ese punto.

    `L_planta_estructural.py::columnas` usa `extrema = j in (0, len-1)`: sólo
    la primera y la ultima columna de cada fila. Se reproduce esa regla para
    poder contrastarla, no para respaldarla.
    """
    xs, _r = ejes_x_rotulados()
    return "C-2" if (abs(p[0] - xs[0]) <= TOL or
                     abs(p[0] - xs[-1]) <= TOL) else "C-1"


AREA_5_8 = 1.99   # no-ssot: cm2, varilla de 5/8", ASTM A615M Tabla 1 (N.o 16 = 199 mm2).
                  # Decia 1,98 y el 27 usaba 2,00 para la misma varilla.
N_BARRAS_C4 = 8   # no-ssot: barras de la C-4. Ocho da un armado SIMETRICO
                  # --cuatro esquinas y cuatro medias caras--; siete cubriria
                  # el requerimiento pero reparte 3+3+1, y en una columna de
                  # confinamiento el armado asimetrico no es sano.


def tipo_c4(puntos, tipos):
    u"""El tercer tipo que la malla exige, dimensionado por el 8.5.1.1.

    LO QUE MANDA LA NORMA, y conviene ser exacto: el 8.5.1.1 pide el mayor de
    los disenos de **los dos muros que se interceptan**, no el mayor del
    edificio. Llevar los ocho cruces a C-2 tambien cumple --la excede-- pero
    eso es una decision del proyectista, no una exigencia, y como tal habria
    que declararla. El tipo de abajo es lo que el acapite pide.

    LA SECCION NO CAMBIA. El 8.6.3-a.1 pide Ac >= 15t = 360 cm2 y la seccion
    de la C-1, 24 x 25 = 600 cm2, ya lo cumple; el diseno de esos cuatro muros
    dio d = 25 cm. Asi que la C-3 comparte SECCION con la C-1 y solo cambia el
    armado: el encofrado es el mismo y en obra no hay una pieza de otra medida
    que equivocar, que era el unico argumento serio contra un tercer tipo.
    """
    faltantes = [q for q in puntos
                 if tipos[asignacion_del_plano(q["p"])] < q["As_req"] - 1e-9]
    if not faltantes:
        return None
    pide = max(q["As_req"] for q in faltantes)
    As = N_BARRAS_C4 * AREA_5_8
    assert As >= pide, (
        "la C-4 de %d o 5/8 da %.2f cm2 y la malla pide %.2f"
        % (N_BARRAS_C4, As, pide))
    return {"tipo": "C-4", "n": N_BARRAS_C4, "diam": '5/8"',
            "area_barra": AREA_5_8, "As_prov": As, "As_req": pide,
            "cruces": [q["p"] for q in faltantes]}


def informe(puntos, tipos):
    print("=" * 94)
    print("QUE COLUMNA VA EN CADA CRUCE  -  E.070 8.5.1.1 y Tabla 11")
    print("=" * 94)
    print("  La Tabla 11 clasifica la columna DENTRO DE UN MURO. En una malla")
    print("  una misma columna pertenece a dos muros, y el 8.5.1.1 manda tomar")
    print("  el MAYOR de los dos disenos independientes.")
    print()
    print("  %-14s %-26s %8s  %-6s %-6s %s"
          % ("cruce (x;y)", "lo que manda", "As req", "plano", "hace", "estado"))
    print("  " + "-" * 90)
    malos = []
    for q in puntos:
        x, y = q["p"]
        c = q["manda"]
        plano = asignacion_del_plano(q["p"])
        As_plano = tipos[plano]
        ok = As_plano >= q["As_req"] - 1e-9
        if not ok:
            malos.append(q)
        print("  (%5.2f;%5.2f) %-26s %7.2f  %-6s %6.2f %s"
              % (x, y,
                 "%s %s" % (c["muro"], "EXTREMA" if c["extrema"] else "interior"),
                 q["As_req"], plano, As_plano,
                 "ok" if ok else "*** FALTA %.2f cm2 ***"
                 % (q["As_req"] - As_plano)))
    return malos


def resumen(puntos, malos, tipos):
    print()
    print("=" * 94)
    print("  %d cruces en la malla" % len(puntos))
    n2 = sum(1 for q in puntos if asignacion_del_plano(q["p"]) == "C-2")
    print("  el plano asigna hoy: %d C-2 y %d C-1" % (n2, len(puntos) - n2))
    print()
    if malos:
        print("  %d CRUCES CON MENOS ACERO DEL QUE EL 8.5.1.1 PIDE:" % len(malos))
        for q in malos:
            c = q["manda"]
            print("    (%5.2f;%5.2f)  es EXTREMA de %s y el plano le pone %s: "
                  "%.2f contra %.2f"
                  % (q["p"][0], q["p"][1], c["muro"],
                     asignacion_del_plano(q["p"]), tipos[asignacion_del_plano(q["p"])],
                     q["As_req"]))
        print()
        print("  LA CAUSA es que la regla del plano --primera y ultima columna")
        print("  de cada fila-- describe los extremos de los muros X y NO VE")
        print("  los de los muros Y cortos, que caen en posiciones intermedias.")
    else:
        print("  [ok] ningun cruce recibe menos acero del que el 8.5.1.1 pide")
    print()
    # cuanto sobra, que tambien es informacion de proyecto
    sobra = [q for q in puntos
             if tipos[asignacion_del_plano(q["p"])] > q["As_req"] * 2.0]
    if sobra:
        print("  Y en %d cruces el plano pone MAS DEL DOBLE del requerido, que"
              % len(sobra))
        print("  es conservador y tiene un costo: uniformar hacia arriba es una")
        print("  decision legitima, pero conviene tomarla sabiendo cuanto pesa.")
    return len(malos)


def control(puntos, muros_geo):
    print()
    print("CONTROLES")
    print("-" * 94)
    # 1. la malla tiene que cubrir a TODOS los muros: si un muro no aparece
    #    en ningun cruce, la geometria se derivo mal y el analisis es humo.
    vistos = set()
    for q in puntos:
        for c in q["concurren"]:
            vistos.add(c["muro"])
    faltan = set(m["clave"] for m in muros_geo) - vistos
    assert not faltan, "estos muros no aparecen en ningun cruce: %s" % faltan
    # 2. cada muro tiene que aportar EXACTAMENTE dos extremas
    for m in muros_geo:
        n = sum(1 for q in puntos for c in q["concurren"]
                if c["muro"] == m["clave"] and c["extrema"])
        assert n == 2, (
            "%s aporta %d columnas extremas y tiene que aportar 2" % (m["clave"], n))
    # 3. y la malla no puede estar vacia ni tener un solo punto: un `for`
    #    sobre poco no falla, aprueba.
    assert len(puntos) >= len(EJES_MX), (
        "la malla trajo %d cruces y hay %d ejes de muro X: se derivo mal"
        % (len(puntos), len(EJES_MX)))
    print("  [ok] los %d muros aparecen en la malla, con 2 extremas cada uno"
          % len(muros_geo))
    print("  [ok] %d cruces derivados de la geometria, no de una lista a mano"
          % len(puntos))


def cuadro_completo():
    u"""El cuadro de columnas con TODOS los tipos, la C-4 incluida.

    El 19 no puede conocer la C-4: ese tipo no sale del diseno de un muro
    aislado sino de la MALLA --de preguntar en cada cruce que muros
    concurren, que es el 8.5.1.1-- y quien sabe de malla es este script. Asi
    que la fuente unica del cuadro pasa a ser esta funcion, y las figuras y
    el plano la consumen a ella en vez de al 19.

    Sin esto, la figura del cuadro de columnas mostraria cuatro tipos y el
    informe cinco: dos artefactos del mismo entregable contandose distinto.
    """
    m19 = _mod("19_confinamientos.py")
    with contextlib.redirect_stdout(_io.StringIO()):
        muros = m19.disenar()
        cuadro = m19.cuadro_de_columnas(muros)
    dis = {mu["nom"]: mu for mu in muros}
    tipos = {c["tipo"]: c["As_prov"] for c in cuadro if c.get("tipo")}
    puntos = malla(geometria_de_muros(), dis)
    c4 = tipo_c4(puntos, tipos)
    if c4:
        c4 = dict(c4)
        c4["b"], c4["h"] = ESPESOR, 0.25
        # la disposicion la calcula el 19 con la misma regla que a las
        # demas: con 4 barras por cara larga la C-4 daba 3,91 cm libres,
        # menos que los 40 mm de la E.060 7.6.3; el reparto valido es 3 y 3
        m19.completar_disposicion(c4)
        c4["estribo"] = m19._estribaje_texto(len(c4["disp"]["ganchos"]))
        cuadro = list(cuadro) + [c4]
    return cuadro


def m19_ac_min():
    return 15.0 * ESPESOR * 100.0


def main():
    m19 = _mod("19_confinamientos.py")
    with contextlib.redirect_stdout(_io.StringIO()):
        muros = m19.disenar()
        cuadro = m19.cuadro_de_columnas(muros)
    dis = {m["nom"]: m for m in muros}
    tipos = {c["tipo"]: c["As_prov"] for c in cuadro if c.get("tipo")}

    muros_geo = geometria_de_muros()
    puntos = malla(muros_geo, dis)
    malos = informe(puntos, tipos)
    c4 = tipo_c4(puntos, tipos)
    n = resumen(puntos, malos, tipos)
    if c4:
        print()
        print("  EL TIPO NUEVO QUE LA NORMA PIDE  --  8.5.1.1 y 8.6.3-a")
        print("  " + "-" * 88)
        print("    C-4  %.2f x %.2f m, la MISMA seccion de la C-1, con %d o %s"
              % (ESPESOR, 0.25, c4["n"], c4["diam"]))
        print("    As = %.2f cm2 sobre los %.2f que pide el cruce mas exigido "
              "(+%.0f %%)" % (c4["As_prov"], c4["As_req"],
                              100 * (c4["As_prov"] / c4["As_req"] - 1)))
        print("    va en los %d cruces que son extremos de los muros Y cortos"
              % len(c4["cruces"]))
        print()
        print("    La seccion no cambia porque el 8.6.3-a.1 pide Ac >= 15t =")
        print("    %.0f cm2 y la de la C-1 ya da %.0f: el encofrado es el mismo"
              % (m19_ac_min(), 24 * 25))
        print("    y en obra no hay una pieza de otra medida que equivocar.")
    control(puntos, muros_geo)
    return n


if __name__ == "__main__":
    main()
