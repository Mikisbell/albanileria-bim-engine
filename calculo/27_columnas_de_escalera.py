# -*- coding: utf-8 -*-
"""Columnas de la caja de escalera — E.070 Capítulo 9, acápite 9.1

POR QUE EXISTE ESTE ELEMENTO
============================
No es una decision de proyecto: lo manda la norma, y con nombre propio. La
E.070, Capitulo 9 "DISENO PARA CARGAS ORTOGONALES AL PLANO DEL MURO", acapite
9.1 "Especificaciones generales", parrafo de fuerzas concentradas, dice
textualmente:

    "Para el caso de fuerzas concentradas perpendiculares al plano de muros
     de albanileria simple, los muros deberan reforzarse con elementos de
     concreto armado que sean capaces de resistir el total de las cargas y
     trasmitirlas a la cimentacion. Tal es el caso, por ejemplo, de una
     escalera, el empuje causado por una escalera cuyo descanso apoya
     directamente sobre la albanileria, debera ser tomado por columnas."

Es una de las pocas veces en que la norma nombra un elemento constructivo
concreto para ilustrar una regla. Y la razon esta en el TITULO del capitulo:
son cargas ORTOGONALES al plano del muro. La albanileria fuera de su plano
casi no tiene resistencia -- es exactamente el mismo motivo por el que los
parapetos hay que arriostrarlos (script 25).

EL ERROR QUE ESTO CORRIGE
=========================
El metrado repartia el peso de la escalera entre MX-2 y MY-3a siguiendo la
trayectoria geometrica de cargas. Geometricamente era impecable; normativamente
estaba prohibido. Un metrado puede cerrar consigo mismo y aun asi apoyar una
escalera donde la norma no deja.

QUE SI BAJA POR EL MURO
=======================
La mitad de los tramos que llega a la LOSA DE PISO, porque eso ya no es "el
descanso apoyado sobre la albanileria" sino carga de losa, que baja como
cualquier otra carga del piso. Lo que no puede bajar por el muro es el
DESCANSO y la mitad de tramo que se apoya en el.
"""
import importlib.util
import os

from proyecto import (AREA_ESCALERA, peso_escalera_m2, SC_VIVIENDA, N_PISOS,
                      ESC_X0, ESC_X1, ESC_Y0, ESC_Y1, FC, FY, ESPESOR,
                      H_ENTREPISO)


def _cargar(nombre):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "e", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R11 = _cargar("11_metrado_muros.py")

# Cuatro columnas, una por esquina de la caja. Dos caen sobre el eje del muro
# longitudinal MY-3a (x = 3,30) y pueden resolverse engrosando su columna de
# confinamiento; las otras dos, en el borde libre x = 5,94, son NUEVAS.
N_COLUMNAS = 4
B_CE = ESPESOR            # ancho: el del muro, para que no sobresalga del paño
PERALTES = [0.25, 0.30, 0.35, 0.40]      # se prueban en orden   # no-ssot: peraltes candidatos en m, no Z ni el paso de escalera
VARILLAS = [("1/2\"", 1.29), ("5/8\"", 1.99), ("3/4\"", 2.84)]   # no-ssot: cm2, ASTM A615M Tabla 1, la misma del 19
N_BARRAS = 4              # minimo de la E.060 10.9.2 para estribos rectangulares
RHO_MIN, RHO_MAX = 0.01, 0.06            # E.060 10.9.1   # no-ssot: cuantia minima y maxima del E.060 10.9.1, no la junta
PHI_COMP = 0.65           # E.060 9.3.2.2, elementos en compresion con estribos


def cargas():
    """(CM, CV, Pu) que llegan a las columnas, en kgf. Los cinco niveles."""
    f = R11.fraccion_a_columnas()
    cm = AREA_ESCALERA * peso_escalera_m2() * N_PISOS * f
    cv = AREA_ESCALERA * SC_VIVIENDA * N_PISOS * f
    return cm, cv, 1.4 * cm + 1.7 * cv       # E.060 9.2.1


def resistencia(ag, ast):
    """phi.Pn de una columna con estribos. E.060 10.3.6.2.

    El 0,80 no es un coeficiente de seguridad mas: es la excentricidad MINIMA
    que la norma obliga a considerar aunque el calculo diga que la carga es
    axial pura. Una columna perfectamente centrada no existe en obra.
    """
    return 0.80 * PHI_COMP * (0.85 * FC * (ag - ast) + FY * ast)   # no-ssot: el 0,85 f'c del E.060 10.3.6.2, no phi de cortante


def disenar():
    cm, cv, pu = cargas()
    pu_col = pu / N_COLUMNAS

    print("=" * 84)
    print("COLUMNAS DE LA CAJA DE ESCALERA — E.070 Cap. 9, acapite 9.1")
    print("=" * 84)
    print("  La norma no admite que el descanso apoye sobre la albanileria:")
    print("  manda que el empuje lo tomen COLUMNAS y que estas lo lleven a la")
    print("  cimentacion. No es criterio de proyecto, es texto expreso.")
    print()
    print("  caja de escalera        %.2f x %.2f m  =  %.2f m2"
          % (ESC_X1 - ESC_X0, ESC_Y1 - ESC_Y0, AREA_ESCALERA))
    print("  fraccion que NO baja por muro   %.1f %%" % (100 * R11.fraccion_a_columnas()))
    print("  carga muerta   CM       %9.0f kgf   (%d niveles)" % (cm, N_PISOS))
    print("  sobrecarga     CV       %9.0f kgf" % cv)
    print("  amplificada    Pu = 1,4 CM + 1,7 CV = %.0f kgf" % pu)
    print("  por columna (%d)         %9.0f kgf" % (N_COLUMNAS, pu_col))
    print()

    # area estrictamente necesaria, con la cuantia minima
    print("  %-12s %10s %10s %10s %10s  %s"
          % ("seccion", "Ag (cm2)", "As min", "phi.Pn", "Pu/phi.Pn", "veredicto"))
    print("  " + "-" * 74)
    elegida = None
    for d in PERALTES:
        ag = B_CE * 100 * d * 100
        ast = RHO_MIN * ag
        pn = resistencia(ag, ast)
        uso = pu_col / pn
        ok = uso <= 1.0
        print("  %.2f x %.2f %10.0f %10.2f %10.0f %10.3f  %s"
              % (B_CE, d, ag, ast, pn, uso, "cumple" if ok else "NO cumple"))
        if ok and elegida is None:
            elegida = (d, ag, ast, pn, uso)
    assert elegida, "ninguna seccion de la lista resiste; ampliar PERALTES"

    d, ag, ast, pn, uso = elegida
    print()
    print("  GOBIERNA EL MINIMO, NO LA CARGA. La escalera de una vivienda")
    print("  unifamiliar no exige seccion: la exige el armado. Con la cuantia")
    print("  minima del 1 % (E.060 10.9.1) la columna mas chica ya sobra, y")
    print("  el uso queda en %.1f %% de su capacidad." % (100 * uso))
    print()

    # el armado: cuatro barras, la menor que llegue a la cuantia minima
    print("  ARMADO LONGITUDINAL — E.060 10.9.1 y 10.9.2")
    adoptada = None
    for nom, a1 in VARILLAS:
        As = N_BARRAS * a1
        rho = As / ag
        marca = ""
        if RHO_MIN - 1e-9 <= rho <= RHO_MAX and adoptada is None:
            adoptada = (nom, As, rho)
            marca = "  <== ADOPTADA"
        print("     %d o %-6s = %5.2f cm2   rho = %.4f   %s%s"
              % (N_BARRAS, nom, As, rho,
                 "cumple 1 % <= rho <= 6 %" if RHO_MIN <= rho <= RHO_MAX
                 else "por DEBAJO del 1 % minimo", marca))
    assert adoptada, "ninguna varilla de la lista llega a la cuantia minima"
    nom, As, rho = adoptada

    # estribos: el menor de los criterios del E.060 7.10.5
    s1 = 16 * (1.27 if "1/2" in nom else 1.59 if "5/8" in nom else 1.91)   # no-ssot: 16 DIAMETROS de la barra (E.060 7.10.5), no los contrapasos
    s2 = 48 * 0.95          # 48 diametros del estribo de 3/8"
    s3 = min(B_CE, d) * 100
    s = min(s1, s2, s3)
    print()
    print("  ESTRIBOS — E.060 7.10.5, se toma el MENOR de los tres:")
    print("     16 diametros de la barra longitudinal   %5.1f cm" % s1)
    print("     48 diametros del estribo (3/8\")          %5.1f cm" % s2)
    print("     la menor dimension de la columna         %5.1f cm" % s3)
    print("     -> s = %.0f cm" % (s // 5 * 5))
    print()
    print("  >> C-3 (caja de escalera): %.2f x %.2f m, %d o %s, [] o 3/8\" @ %.0f cm"
          % (B_CE, d, N_BARRAS, nom, s // 5 * 5))
    print("  >> Son %d, una por esquina de la caja. Las dos del eje x = %.2f"
          % (N_COLUMNAS, ESC_X0))
    print("     caen sobre el muro longitudinal y se resuelven engrosando su")
    print("     columna de confinamiento; las dos del borde libre x = %.2f son" % ESC_X1)
    print("     NUEVAS, y como la norma exige, bajan hasta la cimentacion.")
    return B_CE, d, nom, As, rho


def fila_cuadro():
    """La fila de la C-3 para el cuadro de columnas, SIN imprimir.

    Misma razon que en 19_confinamientos.cuadro_de_columnas(): el informe y el
    plano tienen que decir el mismo armado, y si cada uno lo arma por su lado
    se separan sin que nadie se entere. La C-3 nacio fuera del 19 -- no es de
    confinamiento, la exige el 9.1 -- y por eso el plano no la conocia: se
    dibujaban C-1 y C-2, y el elemento que la norma manda poner no figuraba.
    """
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        b, d, nom, As, _rho = disenar()
    s1 = 16 * (1.27 if "1/2" in nom else 1.59 if "5/8" in nom else 1.91)   # no-ssot: 16 DIAMETROS de la barra (E.060 7.10.5), no los contrapasos
    s = min(s1, 48 * 0.95, min(b, d) * 100)
    return {"tipo": "C-3", "b": b, "h": d,
            "n": N_BARRAS, "diam": nom, "area_barra": As / N_BARRAS,
            "As_req": None, "As_prov": As,
            "estribo": '[] 3/8" @ %.0f' % (s // 5 * 5)}


def control():
    print()
    print("=" * 84)
    print("CONTROL")
    print("=" * 84)
    cm, cv, pu = cargas()

    # 1. la carga tiene que cerrar con la del metrado: lo que toman las columnas
    #    mas lo que baja por el muro es TODA la escalera, ni mas ni menos.
    total = AREA_ESCALERA * (peso_escalera_m2() + SC_VIVIENDA) * N_PISOS
    a_muro = sum(
        AREA_ESCALERA * (peso_escalera_m2() + SC_VIVIENDA) * N_PISOS * f
        for f in R11.reparto_escalera().values())
    assert abs((cm + cv) + a_muro - total) < 1.0, (
        "la escalera no cierra: columnas %.0f + muro %.0f != total %.0f"
        % (cm + cv, a_muro, total))
    print("  [ok] columnas %.0f + muro %.0f = %.0f kgf, toda la escalera"
          % (cm + cv, a_muro, total))

    # 2. ningun muro de albanileria puede estar recibiendo el DESCANSO
    assert "MY-3a" not in R11.reparto_escalera(), (
        "MY-3a vuelve a recibir escalera: el 9.1 no lo permite")
    assert set(R11.reparto_escalera()) <= {"MX-2"}, (
        "solo la losa de piso puede bajar escalera a un muro")
    print("  [ok] ningun muro recibe el descanso; solo MX-2 recibe losa de piso")

    # 3. con la cuantia minima, la seccion mas chica de la lista ya resiste:
    #    si esto dejara de ser cierto, la escalera habria cambiado de escala
    #    y habria que volver a mirar el elemento, no solo subir un peralte.
    ag_min = B_CE * 100 * PERALTES[0] * 100
    assert resistencia(ag_min, RHO_MIN * ag_min) >= pu / N_COLUMNAS, (
        "la seccion minima ya no resiste: revisar el elemento, no el peralte")
    print("  [ok] la seccion se elige por el minimo de armado, no por la carga")

    # 4. POR QUE LOS ESTRIBOS SALEN DEL 7.10.5 Y NO DEL 21.4.5.
    #    El 21.4.5 pediria estribos @ 10 cm en una zona de confinamiento, y
    #    esta columna lleva @ 20 cm del 7.10.5. No es un olvido: el 21.4 no
    #    la alcanza, por dos razones independientes.
    #
    #    (a) ALCANCE. El 21.4.1 dice textual que "los requisitos de 21.4 se
    #        aplican a las vigas y columnas DEL SISTEMA SISMORRESISTENTE".
    #        El sistema sismorresistente de este edificio son los muros de
    #        albanileria confinada; la C-3 existe porque el 9.1 de la E.070
    #        prohibe que el descanso apoye en albanileria, no porque tome
    #        fuerza sismica de entrepiso.
    #
    #    (b) NIVEL DE CARGA. Aun tratandola como columna de portico, el
    #        21.4.3 deriva al 21.4.5 solo cuando Pu > 0,1 f'c Ag. Aqui no
    #        se llega, y el control de abajo lo mide en vez de afirmarlo.
    ag = B_CE * 100 * PERALTES[0] * 100
    umbral = 0.10 * FC * ag
    pu_col = pu / N_COLUMNAS
    assert pu_col <= umbral, (
        "Pu por columna (%.0f kgf) supera 0,1 f'c Ag (%.0f): el 21.4.3 manda "
        "detallar con el 21.4.5 y el estribaje de 20 cm ya no alcanza"
        % (pu_col, umbral))
    print("  [ok] Pu por columna %.0f kgf <= 0,1 f'c Ag = %.0f kgf: el 21.4.3"
          % (pu_col, umbral))
    print("       no deriva al 21.4.5, y el 21.4.1 tampoco alcanza a esta")
    print("       columna -- no es del sistema sismorresistente.")

    # 4. el peso de la escalera sigue en el peso SISMICO aunque no baje por muro
    print("  [i]  la masa de la escalera sigue contada en el peso sismico del")
    print("       script 15: cambiar su trayectoria no la hace desaparecer.")


if __name__ == "__main__":
    disenar()
    control()
