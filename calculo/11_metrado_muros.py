# -*- coding: utf-8 -*-
"""Metrado de cargas de TODOS los muros portantes — criterio 4 de la rúbrica

La rubrica pide "el metrado de cargas de TODOS los muros portantes". El proyecto
venia calculando UNO -- el critico -- y declarando un programa de 10 viviendas.
Eso es una brecha entre lo que se afirma y lo que se verifica. Esto la cierra:
los trece muros, cada uno con su area tributaria, su peso propio y su esfuerzo
axial verificado.

IDEALIZACION — por que los muros en X y en Y no se metran igual
===============================================================
El aligerado arma sus viguetas en el sentido del FONDO (Y). Entonces:

  * los muros TRANSVERSALES (MX, corren en X) son los APOYOS de las viguetas:
    reciben media luz del pano de cada lado. Son los que cargan.
  * los muros LONGITUDINALES (MY, corren en Y) van PARALELOS a las viguetas:
    solo reciben la vigueta que queda sobre ellos. Se les asigna una franja de
    %.2f m (una separacion de viguetas), que es el criterio conservador
    corriente; cargan basicamente su propio peso.

Confundir esto es un error clasico: repartir la losa por igual entre los cuatro
lados de cada pano, como si estuviera armada en dos direcciones. No lo esta.

DOS METRADOS, NO UNO (E.070 7.1.1.b y E.030 Art. 31)
====================================================
  Pm = CM + 100 % CV   -> esfuerzo axial
  P  = CM +  25 % CV   -> peso sismico, y el Pg de la formula de Vm

EL PESO PROPIO NO ES SOLO LADRILLO
==================================
Cada muro lleva sus columnas de confinamiento (concreto, 2400 kgf/m3 contra los
1800 de la albanileria), su viga solera, y le faltan los vanos. Las tres cosas se
descuentan o se suman segun corresponda.
"""
import importlib.util as _il
import os as _os

from proyecto import (MUROS, EJES_MX, EJES_COLUMNAS_X, PANOS_Y, FRENTE, FONDO,
                      ESPESOR, H_LIBRE, E_LOSA, N_PISOS, LOSA_ALIGERADA,
                      PISO_TERMINADO, TABIQUERIA, SC_VIVIENDA, SC_AZOTEA,
                      PESO_ALBANILERIA, PESO_CONCRETO, PCT_CV_SISMO,
                      B_SOLERA, B_COLUMNA, H_COLUMNA, H_DINTEL_PUERTA,
                      vol_columnas, peso_tarrajeo,
                      LONG_MINIMA, FM, POZO_X0, POZO_X1, POZO_Y0, POZO_Y1,
                      ESC_X0, ESC_X1, ESC_Y0, ESC_Y1, tributaria_mx, machones, AREA_ESCALERA, peso_escalera_m2, volumen_de_vanos, N_CONTRAPASOS, PASO_ESCALERA, PARAPETO, A_UNIDAD)

_spec = _il.spec_from_file_location(
    "m02", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                         "02_metrado_y_esfuerzo_axial.py"))
_m02 = _il.module_from_spec(_spec)
_spec.loader.exec_module(_m02)
limite_axial = _m02.limite_axial

SEP_VIGUETAS = 0.40
CM_TIPICO = LOSA_ALIGERADA + PISO_TERMINADO + TABIQUERIA
CM_AZOTEA = LOSA_ALIGERADA + PISO_TERMINADO
H_VANO = H_LIBRE - H_DINTEL_PUERTA
EXTRA_SOLERA_M2 = E_LOSA * PESO_CONCRETO - LOSA_ALIGERADA   # concreto macizo vs aligerado


def solape(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def columnas_de(nom, dire, L):
    """Cuantas columnas de confinamiento lleva el muro."""
    if dire == "X":
        return len(EJES_COLUMNAS_X)          # cruza todos los ejes longitudinales
    # los MY llevan una columna en cada cruce con un muro transversal
    if "3a" in nom or "4a" in nom:
        return sum(1 for y in EJES_MX if y <= POZO_Y0 + 1e-9)
    if "3b" in nom or "4b" in nom:
        return sum(1 for y in EJES_MX if y >= POZO_Y1 - 1e-9)
    return len(EJES_MX)                      # medianeras: cruzan los siete


def tributaria_de(nom, dire, L_neta):
    """Area de losa que baja a este muro, por piso."""
    if dire == "X":
        for n, y, ancho, area in tributaria_mx():
            if nom.startswith(n):
                # descontar tambien el hueco de escalera que caiga en la franja
                y0 = y - (PANOS_Y[EJES_MX.index(y) - 1] / 2 if y > 0 else 0)
                y1 = y + (PANOS_Y[EJES_MX.index(y)] / 2 if y < FONDO else 0)
                return area - solape(y0, y1, ESC_Y0, ESC_Y1) * (ESC_X1 - ESC_X0)
        raise KeyError(nom)
    return SEP_VIGUETAS * L_neta             # paralelo a las viguetas


def reparto_escalera():
    """Fraccion del peso de la escalera que baja a cada MURO de albanileria.

    CORRECCION 2026-09-19 (Mikis, con la norma en la mano). La version previa
    repartia la escalera entre MX-2 y MY-3a siguiendo la trayectoria de cargas
    geometrica. Eso es lo que haria un metrado sin mirar la E.070, y la E.070
    lo PROHIBE expresamente. Capitulo 9, acapite 9.1, parrafo de fuerzas
    concentradas, textual:

        "Para el caso de fuerzas concentradas perpendiculares al plano de
         muros de albanileria simple, los muros deberan reforzarse con
         elementos de concreto armado que sean capaces de resistir el total
         de las cargas y trasmitirlas a la cimentacion. TAL ES EL CASO, POR
         EJEMPLO, DE UNA ESCALERA, EL EMPUJE CAUSADO POR UNA ESCALERA CUYO
         DESCANSO APOYA DIRECTAMENTE SOBRE LA ALBANILERIA, DEBERA SER TOMADO
         POR COLUMNAS."

    O sea que el descanso NO puede descargar en el muro: lo toman COLUMNAS de
    concreto armado que llevan la carga a la cimentacion. La razon fisica es
    la que la norma titula en su capitulo: son cargas ORTOGONALES AL PLANO del
    muro, y la albanileria fuera de su plano casi no tiene resistencia -- es
    el mismo motivo por el que los parapetos se arriostran.

    Lo que SI baja al muro es la mitad de los tramos que llega a la LOSA DE
    PISO, porque eso ya no es "el descanso apoyado sobre la albanileria" sino
    carga de losa, que es como baja cualquier otra carga del piso.
    """
    largo = ESC_Y1 - ESC_Y0
    l_tramo = (N_CONTRAPASOS // 2 - 1) * PASO_ESCALERA
    f_tramo = l_tramo / largo
    return {"MX-2": f_tramo / 2.0}          # el resto lo toman las columnas


def fraccion_a_columnas():
    """Lo que NO baja por los muros y tiene que tomar una columna (E.070 9.1)."""
    return 1.0 - sum(reparto_escalera().values())


def parapeto_de(nom, dire, L):
    """kgf de parapeto de azotea que baja a ESTE muro (UN solo nivel).

    AUDITORIA 2026-09-19. El parapeto no pesaba en ningun lado. Se levanta
    sobre la losa en el borde, alineado con el muro de abajo, y su carga baja
    por ese muro -- esta SI es carga en el plano, no ortogonal, asi que la
    toma el muro. Corre por el perimetro EXTERIOR y por el borde del POZO,
    donde el tramo que le toca a cada muro es el lado del pozo que bordea.

    Va una sola vez, no por los cinco niveles: hay un solo parapeto.
    """
    if nom.startswith(("MX-1", "MX-7", "MY-1", "MY-2")):
        tramo = L                                   # perimetro exterior
    elif nom.startswith(("MX-3", "MX-4")):
        tramo = POZO_X1 - POZO_X0                   # borde transversal del pozo
    elif nom.startswith(("MY-3", "MY-4")):
        # los dos tramos (frontal y posterior) comparten el lado del pozo
        tramo = (POZO_Y1 - POZO_Y0) / 2.0
    else:
        return 0.0
    area = tramo * PARAPETO
    return area * A_UNIDAD * PESO_ALBANILERIA + peso_tarrajeo(area, "medianera" in nom)


def escalera_de(nom, dire):
    """(CM, CV) por piso de la caja de escalera que baja a ESTE muro, en kgf.

    AUDITORIA C-4. tributaria_de() DESCUENTA el hueco de la escalera del area
    de los muros vecinos, y hasta la auditoria nadie devolvia el peso de la
    escalera que lo ocupa: el hueco restaba carga y la estructura que lo llena
    no la sumaba. Lo que vuelve por aca es SOLO la parte que baja por la losa
    de piso; el descanso lo toman columnas (ver reparto_escalera).

    La escalera es circulacion: lleva sobrecarga de vivienda en los cinco
    niveles, azotea incluida, porque se sube al tanque.
    """
    for clave, f in reparto_escalera().items():
        if nom.startswith(clave):
            return (AREA_ESCALERA * peso_escalera_m2() * f,
                    AREA_ESCALERA * SC_VIVIENDA * f)
    return 0.0, 0.0


def metrar():
    filas = []
    for nom, dire, L, t, vanos in MUROS:
        # AUDITORIA 2026-09-19. Este script calculaba L_neta = L - suma(vanos),
        # que NO es lo mismo que la suma de los machones: deja dentro el trozo
        # de 0,15 m que queda entre el extremo del muro y la cara del primer
        # vano. Ese trozo es una COLUMNA AISLADA -- 0,15 m < 1,20 m --, o sea
        # que por el 6.4 no es muro contribuyente. El 01 y el 18 ya usaban
        # machones(); este y el 02 no. Dos longitudes netas distintas para el
        # mismo muro en el mismo proyecto es justo lo que una fuente unica
        # existe para impedir.
        ms = [b - a_ for a_, b in machones(nom, dire, L, vanos)]
        L_neta = sum(ms)
        n_col = columnas_de(nom, dire, L)
        a_trib = tributaria_de(nom, dire, L_neta)

        vol_bruto = t * H_LIBRE * L
        # 2 extremas de peralte mayor + el resto interiores (Tabla 11 las separa)
        vol_col = vol_columnas(n_col, H_LIBRE)
        # AUDITORIA: las fachadas llevan VENTANAS, no puertas. Bajo cada una
        # queda un alfeizar de albanileria que pesa (ver proyecto.py).
        # Y desde el 2026-09-21 el descuento es VANO POR VANO: la fachada
        # frontal lleva tres ventanas y la PUERTA DE INGRESO, que no tiene
        # alfeizar debajo. Una sola altura para los cuatro falseaba el peso.
        vol_vanos = volumen_de_vanos(nom, dire, L, vanos, t)
        vol_alb = vol_bruto - vol_col - vol_vanos
        peso_propio = N_PISOS * (vol_alb * PESO_ALBANILERIA + vol_col * PESO_CONCRETO)
        # la solera corre CONTINUA sobre los vanos: sobre una puerta la solera
        # y el dintel son el mismo elemento. Va sobre la longitud BRUTA.
        extra_solera = N_PISOS * (B_SOLERA * L) * EXTRA_SOLERA_M2
        # revoque: la E.020 lo tabula aparte del 1800 de la albanileria
        tarrajeo = N_PISOS * peso_tarrajeo(L * H_LIBRE, "medianera" in nom)

        n_tip = N_PISOS - 1
        cm_esc, cv_esc = escalera_de(nom, dire)
        cm = (a_trib * (n_tip * CM_TIPICO + CM_AZOTEA) + peso_propio
              + extra_solera + tarrajeo + N_PISOS * cm_esc
              + parapeto_de(nom, dire, L))
        cv_100 = a_trib * (n_tip * SC_VIVIENDA + SC_AZOTEA) + N_PISOS * cv_esc
        pm = cm + cv_100
        p = cm + PCT_CV_SISMO * cv_100

        sigma = pm / (L_neta * 100 * t * 100)
        lim, _ = limite_axial(FM)
        filas.append({
            "nom": nom, "dir": dire, "L": L, "Ln": L_neta, "col": n_col,
            "trib": a_trib, "pp": peso_propio, "pm": pm, "p": p,
            # el 6.4 lo exige a CADA machon, no al promedio: un muro partido
            # en 0,80 y 3,00 m promedia 1,90 y aprobaria escondiendo el corto.
            "sigma": sigma, "lim": lim,
            "cuenta": bool(ms) and all(m >= LONG_MINIMA - 1e-9 for m in ms),
        })
    return filas


def informe(filas):
    print("=" * 96)
    print("METRADO DE LOS %d MUROS PORTANTES — criterio 4" % len(filas))
    print("=" * 96)
    print("  %-30s %3s %6s %6s %4s %8s %10s %10s %7s %7s  %s"
          % ("muro", "dir", "L", "L nta", "col", "A trib", "Pm (kgf)", "P (kgf)",
             "sigma", "limite", ""))
    for f in filas:
        print("  %-30s %3s %6.2f %6.2f %4d %8.2f %10.0f %10.0f %7.2f %7.2f  %s"
              % (f["nom"], f["dir"], f["L"], f["Ln"], f["col"], f["trib"],
                 f["pm"], f["p"], f["sigma"], f["lim"],
                 "CUMPLE" if f["sigma"] <= f["lim"] else "NO CUMPLE <<<"))
    print()
    print("  %-30s %3s %6s %6s %4s %8.2f %10.0f %10.0f"
          % ("SUMA", "", "", "", "", sum(f["trib"] for f in filas),
             sum(f["pm"] for f in filas), sum(f["p"] for f in filas)))
    return filas


def lectura(filas):
    print()
    print("=" * 96)
    print("LECTURA DE LA TABLA — que dice cada cosa")
    print("=" * 96)
    crit = max(filas, key=lambda f: f["sigma"])
    flojo = min(filas, key=lambda f: f["sigma"])
    print("  MURO CRITICO: %s, con sigma = %.2f kgf/cm2 contra un limite de %.2f"
          % (crit["nom"].split()[0], crit["sigma"], crit["lim"]))
    print("  (holgura %+.1f %%). Es un transversal interior, como se esperaba: son"
          % ((crit["lim"] / crit["sigma"] - 1) * 100))
    print("  los que reciben la losa.")
    print()
    print("  MURO MENOS CARGADO: %s, con sigma = %.2f. Es longitudinal: va"
          % (flojo["nom"].split()[0], flojo["sigma"]))
    print("  paralelo a las viguetas y practicamente solo carga su propio peso.")
    print()
    print("  %-40s %10.0f kgf" % ("Pm sumado de los 13 muros",
                                  sum(f["pm"] for f in filas)))
    print("  %-40s %10.0f kgf" % ("P (peso sismico) sumado",
                                  sum(f["p"] for f in filas)))
    print("  %-40s %9.1f %%" % ("Pm supera a P en",
                                (sum(f["pm"] for f in filas) /
                                 sum(f["p"] for f in filas) - 1) * 100))
    print()
    print("  CUIDADO AL USAR ESTA SUMA COMO PESO DEL EDIFICIO. Las areas")
    print("  tributarias de los muros en X ya cubren toda la losa; las franjas de")
    print("  %.2f m que se asignan a los muros en Y se SUPERPONEN con ellas." % SEP_VIGUETAS)
    print("  Para el peso sismico total hay que metrar por NIVEL, no sumando")
    print("  muros, y eso va en la etapa 05. Aca cada muro se metra para SU")
    print("  verificacion axial, que es lo que pide el criterio 4.")
    print()
    n_no = [f for f in filas if not f["cuenta"]]
    print("  Muros que NO cuentan para la resistencia horizontal (E.070 6.4,")
    print("  trozos menores a %.2f m): %s" % (LONG_MINIMA,
                                              "ninguno" if not n_no else
                                              ", ".join(f["nom"] for f in n_no)))
    malos = [f for f in filas if f["sigma"] > f["lim"]]
    print("  Muros que NO cumplen el esfuerzo axial: %s"
          % ("ninguno" if not malos else ", ".join(f["nom"] for f in malos)))


def cruce_con_02(filas):
    """Los dos scripts tienen que dar lo mismo para el muro critico.

    Que 02 modele un muro y 11 modele los trece no los exime de coincidir. La
    primera corrida de este cruce delato que 02 cargaba tabiqueria sobre la
    azotea: daba 8,22 contra 7,98.
    """
    print()
    print("=" * 96)
    print("CRUCE CON EL SCRIPT 02 — dos caminos, un solo numero")
    print("=" * 96)
    # AUDITORIA 2026-09-19. Este cruce exigia que el muro modelado por el 02
    # FUERA el critico, y reventaba en cuanto el critico cambiaba. Pero son dos
    # preguntas distintas y conviene no mezclarlas:
    #   (1) ¿los dos caminos dan el mismo numero para el MISMO muro? -> assert
    #   (2) ¿el muro del 02 sigue siendo el que gobierna?            -> aviso
    # La (1) es coherencia de calculo y no se negocia. La (2) es un RESULTADO
    # que cambia con cada correccion del metrado, y hacerla reventar convertia
    # un hallazgo legitimo en un error de ejecucion.
    mio = [f for f in filas if f["nom"].startswith(_m02.MURO_CRITICO)][0]
    crit = max(filas, key=lambda f: f["sigma"])
    pm02 = _m02.metrado_gravedad()
    s02 = _m02.sigma(pm02, _m02.L_NETA)
    print("  %-46s %10.0f kgf  sigma %.2f"
          % ("script 02 (%s, modelo simple)" % _m02.MURO_CRITICO, pm02, s02))
    print("  %-46s %10.0f kgf  sigma %.2f"
          % ("script 11 (%s, metrado completo)" % _m02.MURO_CRITICO,
             mio["pm"], mio["sigma"]))
    d = abs(mio["pm"] - pm02) / pm02 * 100
    print("  %-46s %9.2f %%  %s" % ("diferencia", d,
                                    "coinciden" if d < 0.5 else "REVISAR <<<"))
    assert d < 0.5, "02 y 11 discrepan %.2f %% en %s" % (d, _m02.MURO_CRITICO)
    print()
    if not crit["nom"].startswith(_m02.MURO_CRITICO):
        print("  AVISO: el muro que GOBIERNA el proyecto ya no es el que el 02")
        print("  modela. Es %s, con sigma = %.2f. El 02 conserva %s porque es"
              % (crit["nom"].split()[0], crit["sigma"], _m02.MURO_CRITICO))
        print("  el caso donde se explica el metrado -- un transversal interior --,")
        print("  pero la cifra que va al informe sale de ESTA tabla.")
    else:
        print("  El muro del 02 es tambien el que gobierna: %.2f kgf/cm2."
              % crit["sigma"])


if __name__ == "__main__":
    f = metrar()
    informe(f)
    lectura(f)
    cruce_con_02(f)
