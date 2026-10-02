# -*- coding: utf-8 -*-
"""Especificaciones técnicas del plano — E.060 1.2.2.4 y E.070 4.2 / 4.3.

QUE ES ESTO Y POR QUE EXISTE
============================
La E.060, en su acapite 1.2.2.4, no deja a criterio del proyectista lo que un
plano de estructuras debe decir: lo enumera.

    "Los planos del proyecto estructural deberan contener como minimo la
     siguiente informacion:
     (a) Relacion de las Normas empleadas en el diseno.
     (b) Carga viva y otras cargas utilizadas en el diseno.
     (c) Resistencia especificada a la compresion del concreto.
     (d) Resistencia especificada o tipo de acero del refuerzo.
     (e) Tamano, localizacion y refuerzo de todos los elementos estructurales.
     (f) Detalles de anclajes y empalmes del refuerzo.
     (g) Ubicacion y detallado de todas las juntas de separacion con
         edificaciones vecinas.
     (h) Caracteristicas de la albanileria, mortero y los detalles de refuerzo
         de acuerdo a la NTE E.070."

Nuestro plano cubria (a), (c), (d) y (e). Los otros cuatro no estaban. Este
script los DERIVA del SSOT y de la norma, para que el plano los imprima sin
que nadie teclee una cifra, y ademas VERIFICA dos cosas que la norma exige y
que nadie habia comprobado.

LAS DOS VERIFICACIONES
======================
1. ANCLAJE DE LA SOLERA EN LA COLUMNA DEL LIMITE DE PROPIEDAD (E.070 7.1.4).
   La norma dice: "En el caso que se discontinuen las vigas soleras, [...]
   porque el muro llega a un limite de propiedad, el peralte minimo de la
   columna de confinamiento respectiva debera ser suficiente como para
   permitir el anclaje de la parte recta del refuerzo longitudinal existente
   en la viga solera mas el recubrimiento respectivo."

   Este edificio es MEDIANERO: los muros MY-1 y MY-2 llegan al limite en las
   dos caras laterales, y ahi las soleras de los muros transversales se
   discontinuan. Hay que comprobar que el peralte de la C-2 alcanza.

2. PROHIBICION DE EMPALMAR EN EL PRIMER ENTREPISO (E.070 4.3.1).
   "No se permitira el traslape del refuerzo vertical en el primer entrepiso,
   tampoco en las zonas confinadas ubicadas en los extremos de soleras y
   columnas."

FUENTES DE CADA CIFRA
=====================
  45 db ....... E.070 4.3.1, traslape de refuerzo horizontal o vertical
  60 db ....... E.070 4.3.2, empalme del refuerzo vertical por traslape
  90 db ....... E.070 4.3.2, empalme alternado en muros con rotulas plasticas
  chicotes .... E.070 4.2.2, conexion a ras: 6 mm, 40 cm + 12,5 cm + 10 cm
  diente ...... E.070 4.2.2, conexion dentada: saliente no mayor que 5 cm
  ldh ......... E.060 12.5.2, longitud de desarrollo con gancho estandar
"""
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from proyecto import (FC, FY, ESPESOR, H_COLUMNA, H_COLUMNA_EXT,   # noqa: E402
                      LOSA_ALIGERADA, PISO_TERMINADO, TABIQUERIA,
                      SC_VIVIENDA, SC_AZOTEA, PESO_ALBANILERIA,
                      PESO_CONCRETO, FM, VM, A_UNIDAD, H_UNIDAD,
                      JUNTA_MIN, JUNTA_MAX, E_LOSA, N_PISOS, Z, S, HN)

# --- constantes de la norma, cada una con su acapite -----------------------
TRASLAPE_DB = 45.0        # E.070 4.3.1
EMPALME_DB = 60.0         # E.070 4.3.2
EMPALME_ALT_DB = 90.0     # E.070 4.3.2, alternado
CHICOTE_DIAM = 0.6        # cm, E.070 4.2.2
CHICOTE_ALB = 40.0        # cm dentro de la albanileria
CHICOTE_COL = 12.5        # cm dentro de la columna
CHICOTE_DOBLEZ = 10.0     # cm de doblez vertical a 90 grados
CHICOTE_CUANTIA = 0.001   # E.070 4.2.2
DIENTE_MAX = 5.0          # cm, E.070 4.2.2 conexion dentada
RECUB = 2.5               # cm, recubrimiento de columna (el del script 19)
PERALTE_MIN_COL = 15.0    # cm, E.070 7.1.4
# Deficit de anclaje ya DECLARADO en ESTADO.md y pendiente de
# decision de proyecto. Si crece, el script revienta.
DEFICIT_DECLARADO = 0.15  # cm

# diametros comerciales, en cm
DIAM = {'6 mm': 0.60, '1/4"': 0.635, '8 mm': 0.80, '3/8"': 0.952,
        '1/2"': 1.27, '5/8"': 1.588, '3/4"': 1.905}

# lo que lleva cada elemento (sale del script 19; se declara el nombre, no la
# cifra, y el control de abajo comprueba que coincida)
REFUERZO = [("C-2", "3/4\"", 12), ("C-1", "1/2\"", 6),
            ("VS-1", "1/2\"", 4), ("C-3", "5/8\"", 4),
            ("C-4", "5/8\"", 8)]   # la C-4 faltaba: nacio en el 39 y aca no entro


def ldh(db_cm, factor_recub=1.0):
    u"""Longitud de desarrollo en traccion con gancho estandar de 90 grados.

    E.060 12.5.2, en unidades kgf-cm:  ldh = 0,075 fy db / raiz(f'c)
    con los minimos de 12.5.1: no menor que 8 db ni que 15 cm.

    `factor_recub` es la reduccion de 12.5.3.a (0,7) cuando el recubrimiento
    lateral es >= 6,5 cm y el recubrimiento mas alla del gancho >= 5 cm. Por
    defecto NO se aplica: una columna de 24 cm de ancho no da 6,5 cm de
    recubrimiento lateral a cada lado del gancho.
    """
    valor = 0.075 * FY * db_cm / math.sqrt(FC) * factor_recub
    return max(valor, 8.0 * db_cm, 15.0)


def anclaje_en_columna_de_limite():
    u"""E.070 7.1.4: la C-2 del limite debe anclar la parte recta de la solera.

    Se compara la parte recta disponible dentro de la columna -- su peralte
    menos los dos recubrimientos -- contra la que el gancho necesita.
    """
    db = DIAM['1/2"']                       # el refuerzo de la VS-1
    requerida = ldh(db)
    # UN recubrimiento, no dos. La norma dice "la parte recta de la longitud
    # de anclaje [...] mas el recubrimiento respectivo": la seccion critica
    # esta en la CARA de la columna por donde entra la barra, y lo que hay
    # que descontar es el recubrimiento de la cara OPUESTA, donde termina el
    # gancho. Restar los dos daba 25,0 cm y un deficit de 2,6 cm; el numero
    # correcto es 27,5 y el deficit, 1 mm. El veredicto no cambia, pero la
    # magnitud si -- y de la magnitud depende si esto se arregla con un
    # redondeo constructivo o con un rediseno.
    disponible = H_COLUMNA_EXT * 100.0 - RECUB
    return db, requerida, disponible, disponible >= requerida


def cargas():
    u"""(b) Cargas de diseno, en kgf/m2. Muertas y vivas por separado."""
    return [
        ("Losa aligerada h = %.2f m" % E_LOSA, LOSA_ALIGERADA, "muerta"),
        ("Piso terminado", PISO_TERMINADO, "muerta"),
        ("Tabiqueria", TABIQUERIA, "muerta"),
        ("Sobrecarga de vivienda", SC_VIVIENDA, "viva"),
        ("Sobrecarga de azotea", SC_AZOTEA, "viva"),
    ]


def materiales():
    u"""(c) (d) (h) Resistencias y caracteristicas de los materiales."""
    return [
        ("Concreto de elementos de confinamiento",
         "f'c = %.0f kgf/cm2" % FC),
        ("Acero de refuerzo",
         "fy = %.0f kgf/cm2 (grado 60, ASTM A615)" % FY),
        ("Albanileria: resistencia a compresion",
         "f'm = %.0f kgf/cm2" % FM),
        ("Albanileria: resistencia al corte",
         "v'm = %.1f kgf/cm2" % VM),
        ("Unidad de arcilla solida, dimensiones",
         "%.0f x %.0f cm, muro t = %.2f m" % (A_UNIDAD * 100,
                                              H_UNIDAD * 100, ESPESOR)),
        ("Mortero: espesor de junta",
         "%.0f a %.0f mm (E.070 4.1.3)" % (JUNTA_MIN * 1000,
                                           JUNTA_MAX * 1000)),
        ("Peso unitario albanileria / concreto",
         "%.0f / %.0f kgf/m3" % (PESO_ALBANILERIA, PESO_CONCRETO)),
    ]


def anclajes_y_empalmes():
    u"""(f) Los detalles que el plano debe declarar, con su acapite."""
    filas = []
    for tipo, diam, n in REFUERZO:
        db = DIAM[diam]
        filas.append((tipo, diam, n,
                      TRASLAPE_DB * db, EMPALME_DB * db, ldh(db)))
    return filas


def junta_sismica():
    u"""(g) E.030-2026 Art. 52. Separacion del limite de propiedad."""
    s = max(0.02 * Z * S * HN, 0.03)
    return s, s / 2.0


def imprimir():
    print("=" * 84)
    print("ESPECIFICACIONES DEL PLANO  -  checklist E.060 1.2.2.4")
    print("=" * 84)
    print()
    print("(b) CARGAS DE DISENO")
    for nom, v, tipo in cargas():
        print("      %-38s %6.0f kgf/m2   (%s)" % (nom, v, tipo))
    print()
    print("(c) (d) (h) MATERIALES")
    for nom, v in materiales():
        print("      %-38s %s" % (nom, v))
    print()
    print("(f) ANCLAJES Y EMPALMES     E.070 4.3.1 (45 db) y 4.3.2 (60 db)")
    print("      %-6s %-7s %4s %10s %10s %10s"
          % ("TIPO", "BARRA", "n", "traslape", "empalme", "ldh gancho"))
    for tipo, diam, n, tr, em, lg in anclajes_y_empalmes():
        print("      %-6s %-7s %4d %8.0f cm %8.0f cm %8.0f cm"
              % (tipo, diam, n, tr, em, lg))
    print()
    print("      Conexion columna-albanileria (E.070 4.2.2), a eleccion:")
    print("        dentada  -  diente saliente no mayor que %.0f cm"
          % DIENTE_MAX)
    print("        a ras    -  chicotes de %.0f mm @ cuantia %.3f, con"
          % (CHICOTE_DIAM * 10, CHICOTE_CUANTIA))
    print("                    %.0f cm en la albanileria + %.1f cm en la "
          "columna + %.0f cm de doblez"
          % (CHICOTE_ALB, CHICOTE_COL, CHICOTE_DOBLEZ))
    print()
    print("      PROHIBIDO empalmar el refuerzo vertical en el PRIMER")
    print("      entrepiso, y en las zonas confinadas de los extremos de")
    print("      soleras y columnas (E.070 4.3.1).")
    print()
    s, s2 = junta_sismica()
    print("(g) JUNTA DE SEPARACION SISMICA     E.030-2026 Art. 52")
    print("      s = 0,02 Z S h = 0,02 x %.2f x %.2f x %.2f = %.1f cm"
          % (Z, S, HN, s * 100))
    print("      s/2 (Art. 52.3, vecino con junta reglamentaria) = %.1f cm"
          % (s2 * 100))
    print()
    print("=" * 84)
    print("VERIFICACION E.070 7.1.4  -  columna del limite de propiedad")
    print("=" * 84)
    db, req, disp, ok = anclaje_en_columna_de_limite()
    print("  El edificio es MEDIANERO: los muros MY-1 y MY-2 llegan al limite,")
    print("  y ahi las soleras de los muros transversales se discontinuan. La")
    print("  norma pide que el peralte de esa columna permita anclar la parte")
    print("  recta del refuerzo de la solera mas el recubrimiento.")
    print()
    print("      refuerzo de la VS-1 .................. o 1/2\" (db = %.2f cm)"
          % db)
    print("      ldh con gancho estandar (E.060 12.5.2)  %.1f cm" % req)
    print("      peralte de la C-2 ....................  %.0f cm"
          % (H_COLUMNA_EXT * 100))
    print("      menos 1 recubrimiento de %.1f cm ......  %.1f cm disponible"
          % (RECUB, disp))
    print()
    print("      %s" % ("CUMPLE" if ok else "NO CUMPLE con gancho recto"))
    return ok, req, disp


def control():
    u"""Las comprobaciones que tienen que morder."""
    fallas = []

    # 1. el peralte de toda columna supera el minimo del 7.1.4
    for nom, h in (("C-1", H_COLUMNA), ("C-2", H_COLUMNA_EXT)):
        if h * 100.0 < PERALTE_MIN_COL - 1e-9:
            fallas.append("%s tiene peralte %.0f cm < %.0f cm (E.070 7.1.4)"
                          % (nom, h * 100, PERALTE_MIN_COL))

    # 2. ldh crece con el diametro: un error de tabla se ve al instante
    prev = 0.0
    for nom in ('6 mm', '3/8"', '1/2"', '5/8"', '3/4"'):
        v = ldh(DIAM[nom])
        if v < prev - 1e-9:
            fallas.append("ldh de %s (%.1f) es menor que la anterior (%.1f)"
                          % (nom, v, prev))
        prev = v

    # 3. el empalme siempre es mayor que el traslape (60 db > 45 db)
    for tipo, diam, n, tr, em, lg in anclajes_y_empalmes():
        if em <= tr:
            fallas.append("%s: empalme %.0f no supera traslape %.0f"
                          % (tipo, em, tr))

    # 4. el refuerzo declarado acá tiene que ser el del CUADRO DE COLUMNAS.
    # AUDITORIA 2026-09-30: este control comparaba REFUERZO contra otro
    # literal escrito al lado -- "C-2": 12 contra "C-2": 12 -- y anunciaba
    # "coincide con el cuadro del script 19" mientras el cuadro decia 11.
    # Un control que se compara consigo mismo no mira nada. Ahora lee el
    # cuadro de verdad (39::cuadro_completo, que incluye la C-4).
    import contextlib
    import importlib.util
    import io as _io
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "39_columnas_en_planta.py")
    spec = importlib.util.spec_from_file_location("m39_33", ruta)
    m39 = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m39)
        cuadro = {f["tipo"]: f for f in m39.cuadro_completo()}
    for tipo, diam, n in REFUERZO:
        f = cuadro.get(tipo)
        if f is None:
            fallas.append("%s no esta en el cuadro de columnas" % tipo)
        elif (f["n"], f["diam"]) != (n, diam):
            fallas.append("%s declara %d o %s y el cuadro dice %d o %s"
                          % (tipo, n, diam, f["n"], f["diam"]))
    for tipo in sorted(set(cuadro) - {r[0] for r in REFUERZO}):
        fallas.append("%s esta en el cuadro y no tiene anclaje declarado" % tipo)
    return fallas


def main():
    ok_anclaje, req, disp = imprimir()
    print()
    fallas = control()
    if fallas:
        print("  HALLAZGOS:")
        for f in fallas:
            print("     - %s" % f)
        return 1
    print("  [ok] peraltes sobre el minimo de 15 cm (E.070 7.1.4)")
    print("  [ok] ldh crece con el diametro")
    print("  [ok] el empalme de 60 db supera al traslape de 45 db")
    print("  [ok] el refuerzo coincide con el cuadro de columnas (39)")
    if not ok_anclaje:
        print()
        print("  HALLAZGO DECLARADO Y PENDIENTE DE DECISION -- ver ESTADO.md")
        print("  El anclaje de la solera no entra en la C-2 del limite con")
        print("  gancho estandar recto: faltan %.1f cm de %.1f requeridos."
              % (req - disp, req))
        print("  Salidas posibles: peraltar la C-2 del limite a 35 cm, o")
        print("  anclaje mecanico. NO se decide desde el script.")
        # Sale 0 A PROPOSITO. El hallazgo esta declarado y contabilizado:
        # un rojo permanente se normaliza igual que un verde falso, y en
        # dos dias nadie lo mira. Lo que SI revienta es un hallazgo NUEVO,
        # o que el deficit crezca por encima del declarado.
        if req - disp > DEFICIT_DECLARADO + 1e-6:
            print()
            print("  !! el deficit crecio: %.2f cm contra los %.2f declarados"
                  % (req - disp, DEFICIT_DECLARADO))
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
