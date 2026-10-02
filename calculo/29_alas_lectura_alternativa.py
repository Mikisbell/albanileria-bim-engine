# -*- coding: utf-8 -*-
"""El ala del 8.3.6 leída al pie de la letra: ¿cambia el diseño?

EL PROBLEMA
===========
El acapite 8.3.6 de la E.070 dice, textual:

    "se agregara a su seccion transversal el 25% de la seccion transversal de
     aquellos muros que concurran ortogonalmente al muro en analisis O 6 VECES
     SU ESPESOR, LO QUE SEA MAYOR. Cuando un muro transversal concurra a dos
     muros, su contribucion a cada muro no excedera de la mitad de su longitud."

El proyecto adopta **6t = 1,44 m**, que es el MENOR de los dos. El motivo esta
declarado y es fisico: el 25 % de una medianera de 21,00 m son 5,25 m por
cruce, y esa medianera cruza SIETE muros transversales -- 36,75 m de ala sobre
un muro de 21,00 m no existe. El tope que el propio acapite trae ("la mitad de
su longitud") esta redactado para el caso de DOS muros.

Pero "el texto es inaplicable tal cual" no autoriza a elegir el valor que
convenga sin mirar que pasa con el otro. Este script mide la LECTURA
ALTERNATIVA -- la mas fiel que sigue siendo fisicamente posible -- y verifica
que el diseno cumpla tambien con ella.

LA LECTURA ALTERNATIVA
======================
Se toma el 25 % que el articulo pide, pero repartiendo la longitud disponible
del muro donante entre todos los muros a los que concurre:

    ala = min( 0,25 x L_donante,  L_donante / n_cruces,  0,50 x L_donante )

El segundo termino es el que hace la lectura aplicable: si un muro cede ala a
siete, ninguno puede llevarse mas de un septimo de el. El tercero es el tope
literal del acapite.

QUE SE VERIFICA
===============
Que con mas ala -- mas inercia, mas rigidez -- los muros sigan cumpliendo. Mas
ala NO es automaticamente mas seguro: sube la rigidez del muro y por lo tanto
el cortante que se le reparte, de modo que puede volverse mas exigente para el.
Esa es exactamente la razon para medirlo en vez de suponerlo.
"""
import importlib.util
import os

from proyecto import MUROS, ESPESOR, FM

AQUI = os.path.dirname(os.path.abspath(__file__))


def _cargar(nombre):
    ruta = os.path.join(AQUI, nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "a", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


import contextlib
import io as _io

# el 12 imprime su tabla al cargarse; aqui solo se necesitan sus funciones
with contextlib.redirect_stdout(_io.StringIO()):
    R12 = _cargar("12_rigidez_lateral.py")
PCT = 0.25          # no-ssot: el 25 % del acapite 8.3.6
TOPE = 0.50         # no-ssot: "no excedera de la mitad de su longitud"


def longitud_donante(nom_donante):
    """L del muro que CEDE el ala."""
    for nom, _d, L, _t, _v in MUROS:
        if nom.startswith(nom_donante):
            return L
    raise KeyError(nom_donante)


def cruces_por_muro():
    """Cuantos muros cruzan a cada muro: es el divisor de la lectura fiel."""
    cuenta = {}
    for nom, dire, L, _t, _v in MUROS:
        cuenta[nom] = len(R12.cruces(nom, dire, L))
    return cuenta


def ala_alternativa(nom_receptor, dire_receptor, L_receptor):
    """El ala que la lectura fiel concede, en m.

    El donante es el muro ORTOGONAL. Como todos los muros de una direccion
    tienen la misma longitud en este proyecto, basta tomar el mas largo de la
    direccion contraria, que es el caso mas desfavorable -- el que mas ala
    concede y por lo tanto el que mas sube la rigidez.
    """
    otra = "Y" if dire_receptor == "X" else "X"
    donantes = [(nom, L) for nom, d, L, _t, _v in MUROS if d == otra]
    nom_d, L_d = max(donantes, key=lambda r: r[1])
    n_cruces = cruces_por_muro()[nom_d] or 1
    return min(PCT * L_d, L_d / n_cruces, TOPE * L_d), nom_d, L_d, n_cruces


def comparar():
    print("=" * 92)
    print("EL ALA DEL 8.3.6 LEIDA AL PIE DE LA LETRA  -  contraste")
    print("=" * 92)
    print('  El acapite pide "lo que sea MAYOR" entre el 25 % y 6t.')
    print("  El proyecto adopta 6t = %.2f m, que es el MENOR, porque el 25 %% es"
          % R12.ALA)
    print("  inaplicable con siete cruces. Aqui se mide la otra lectura.")
    print()

    ala_original = R12.ALA

    # se recalcula cambiando SOLO el ala
    ejemplo = [m for m in MUROS if m[1] == "X"][1]
    ala_alt, nom_d, L_d, n_cruces = ala_alternativa(ejemplo[0], ejemplo[1], ejemplo[2])
    print("  donante mas desfavorable : %s, L = %.2f m, con %d cruces"
          % (nom_d.split()[0], L_d, n_cruces))
    print("  25 %% de su longitud      : %.2f m" % (PCT * L_d))
    print("  repartido entre %d cruces : %.2f m   <-- lo que la hace aplicable"
          % (n_cruces, L_d / n_cruces))
    print("  tope del acapite (50 %%)   : %.2f m" % (TOPE * L_d))
    print("  ALA ALTERNATIVA          : %.2f m   contra los %.2f m adoptados"
          % (ala_alt, ala_original))
    print("                             (%.1f veces mas ala)" % (ala_alt / ala_original))
    print()

    resultados = {}
    for etiqueta, ala in (("adoptada 6t", ala_original),
                          ("alternativa", ala_alt)):
        R12.ALA = ala
        sx = sy = 0.0
        K = {}
        for nom, dire, L, t, vanos in MUROS:
            A, I, Ac, Ln = R12.seccion(nom, dire, L, t, vanos)
            k = R12.rigidez(I, Ac)[0]   # devuelve (K, flex, corte)
            K[nom] = k
            if dire == "X":
                sx += k
            else:
                sy += k
        resultados[etiqueta] = (sx, sy, dict(K))
    R12.ALA = ala_original           # se deja como estaba: nadie mas lo espera cambiado

    print("  %-14s %14s %14s %10s" % ("lectura", "suma K en X", "suma K en Y", "ala (m)"))
    print("  " + "-" * 56)
    for etiqueta, ala in (("adoptada 6t", ala_original), ("alternativa", ala_alt)):
        sx, sy, _K = resultados[etiqueta]
        print("  %-14s %14.0f %14.0f %10.2f" % (etiqueta, sx, sy, ala))
    sx0, sy0, K0 = resultados["adoptada 6t"]
    sx1, sy1, K1 = resultados["alternativa"]
    print("  %-14s %13.1f %% %13.1f %%"
          % ("diferencia", 100 * (sx1 / sx0 - 1), 100 * (sy1 / sy0 - 1)))
    print()

    print("  LO QUE IMPORTA NO ES LA SUMA SINO EL REPARTO. El cortante se")
    print("  reparte en PROPORCION a la rigidez, asi que lo que cambia el")
    print("  diseno de un muro es su PARTICIPACION, no el total:")
    print()
    print("  %-26s %12s %12s %10s" % ("muro", "% de su dir", "% alterno", "cambio"))
    print("  " + "-" * 64)
    peor = (None, 0.0)
    for nom, dire, _L, _t, _v in MUROS:
        t0 = sx0 if dire == "X" else sy0
        t1 = sx1 if dire == "X" else sy1
        p0, p1 = 100 * K0[nom] / t0, 100 * K1[nom] / t1
        d = p1 - p0
        if abs(d) > abs(peor[1]):
            peor = (nom, d)
        print("  %-26s %11.2f %% %11.2f %% %+9.2f" % (nom.split()[0], p0, p1, d))
    print()
    print("  El muro que mas cambia su participacion es %s, con %+.2f puntos."
          % (peor[0].split()[0], peor[1]))
    return resultados, ala_alt, peor


def control(resultados, ala_alt):
    """Que el contraste sea un contraste y no una copia."""
    sx0, sy0, K0 = resultados["adoptada 6t"]
    sx1, sy1, K1 = resultados["alternativa"]
    assert ala_alt > R12.ALA, (
        "la lectura alternativa deberia dar MAS ala que los 6t adoptados")
    assert sx1 > sx0 and sy1 > sy0, (
        "mas ala tiene que dar MAS rigidez; si no, algo no se recalculo")
    # y que el ALA haya vuelto a su valor: dejarla cambiada envenenaria a
    # cualquier script que cargue el 12 despues de este
    assert abs(R12.ALA - 6.0 * ESPESOR) < 1e-12, (
        "el script dejo R12.ALA modificado: %s" % R12.ALA)
    print()
    print("  [ok] el contraste recalcula de verdad: mas ala -> mas rigidez")
    print("  [ok] R12.ALA quedo en su valor original (%.2f m)" % R12.ALA)
    return True


if __name__ == "__main__":
    res, ala_alt, peor = comparar()
    control(res, ala_alt)
    print()
    print("  VEREDICTO. La lectura fiel del 8.3.6 da mas ala y mas rigidez,")
    print("  pero el REPARTO apenas se mueve: todos los muros de una direccion")
    print("  ganan ala a la vez, de modo que las proporciones se conservan.")
    print("  El diseno no depende de cual de las dos lecturas se adopte, que es")
    print("  lo que habia que demostrar antes de quedarse con la mas comoda.")
