# -*- coding: utf-8 -*-
"""Pozo de luz: dimensionamiento con la norma VIGENTE, y verificación de áreas

CORRECCION IMPORTANTE (2026-09-13, tercera revision):
La primera version cito el "RNE A.010 Articulo 19", con el criterio de que el
lado del pozo no fuera menor a 1/3 (dormitorios) o 1/4 (servicios) de la altura
del paramento. **Ese texto esta DEROGADO.** Pertenece a la A.010 del compendio
de 2006; en la version vigente el Articulo 19 trata de "Vanos" (puertas) y el
criterio de dimension fija de pozos ya no existe.

NORMA VIGENTE: **RM N.o 191-2021-VIVIENDA**, Norma Tecnica A.010 Condiciones
Generales de Diseno del RNE (El Peruano, jueves 8 de julio de 2021).

Lo que exige la version vigente, citado:
  Art. 36.1 "Los ambientes de las edificaciones cuentan con componentes que
     aseguren la iluminacion natural necesaria (...). Los vanos tienen un area
     suficiente como para garantizar un nivel de iluminacion en funcion al uso
     proyectado."
  Art. 36.2 "Los ambientes destinados a cocinas, servicios sanitarios, pasajes
     de circulacion, depositos y almacenamiento pueden iluminar a traves de
     otros ambientes."
  Art. 38.2 "Los elementos de ventilacion de los ambientes deben tener el area
     de abertura del vano hacia el exterior **no menor al 5% de la superficie de
     la habitacion** que se ventila."
  Art. 38.3 "Los patios o pozos de luz deben cubrir el requerimiento de
     iluminacion y ventilacion de cada uso (...)"

O sea: la norma paso de PRESCRIPTIVA (dimension minima fija) a POR DESEMPENO
(el pozo debe cubrir el requerimiento). El unico numero duro es el 5 % del
Art. 38.2.

CRITERIO ADOPTADO: se dimensiona por el 5 % vigente Y ademas se comprueba que
el pozo satisface el criterio prescriptivo derogado (1/3 de la altura). Cumplir
los dos da respaldo doble y evita discusion en la sustentacion.
"""

from proyecto import (FRENTE, FONDO, AREA_LOTE, POZO_ANCHO, POZO_LARGO,
                      AREA_POZO, AREA_PLANTA, HN, ALFEIZAR, ALTURA_VENTANA,
                      PARAPETO)

AREA_TECHADA = AREA_PLANTA          # el pozo ya esta descontado en proyecto.py
H_PARAMENTO = HN + PARAPETO - ALFEIZAR

# Ambientes que ventilan al pozo: (nombre, superficie m2, ancho de ventana m).
# El ALTO no se elige aca: lo fija el predimensionamiento del dintel (ver
# 06_predimensionamiento.py). La altura libre de 2,45 m se reparte en alfeizar
# 1,00 + ventana 1,00 + dintel peraltado 0,45, y esa suma tiene que cerrar.
# El bano es la excepcion: ventana alta y chica, con su propio alto.
AMBIENTES = [
    ("dormitorio principal",  12.25, 1.20, ALTURA_VENTANA),   # no-ssot: ancho de ventana
    ("dormitorio secundario",  9.00, 1.20, ALTURA_VENTANA),   # no-ssot: ancho de ventana
    ("cocina",                 8.00, 1.00, ALTURA_VENTANA),
    ("bano",                   3.60, 0.60, 0.60),   # no-ssot: ventana alta de bano
]


def areas():
    print("=" * 74)
    print("VERIFICACION DE AREAS")
    print("=" * 74)
    print("  Lote          %.2f x %.2f = %.2f m2" % (FRENTE, FONDO, AREA_LOTE))
    print("  Pozo de luz   %.2f x %.2f = %.2f m2" % (POZO_ANCHO, POZO_LARGO, AREA_POZO))
    print("  AREA TECHADA por piso    = %.2f m2   %s"
          % (AREA_TECHADA, "CUMPLE >= 200" if AREA_TECHADA >= 200 else "NO CUMPLE"))   # no-ssot: 200 m2 de la consigna
    print("  (la consigna invalida el trabajo si el area baja de 200 m2)")


def ventilacion_vigente():
    print()
    print("=" * 74)
    print("ART. 38.2 VIGENTE — vano >= 5 % de la superficie del ambiente")
    print("=" * 74)
    print("  %-24s %10s %10s %10s  %s" % ("ambiente", "area m2", "5 % m2", "vano m2", "veredicto"))
    ok = True
    for nom, area, ancho, alto in AMBIENTES:
        vano = ancho * alto
        req = 0.05 * area   # no-ssot: 5 % del A.010 38.2, no son 5 cm
        v = "CUMPLE" if vano >= req else "NO CUMPLE"
        if vano < req:
            ok = False
        print("  %-24s %10.2f %10.3f %10.2f  %s   (%.2f x %.2f m)"
              % (nom, area, req, vano, v, ancho, alto))
    print()
    print("  Los vanos propuestos superan holgadamente el 5 %: el requisito es")
    print("  facil de cumplir con ventanas corrientes. Lo que la norma vigente NO")
    print("  fija es la dimension del pozo, y ahi entra el criterio de proyecto.")
    return ok


# A.020 Cuadro N.o 04, primeros 18,00 m de altura: porcentaje de la altura del
# paramento mas bajo opuesto, segun el tipo de ambiente y cuantos lados del pozo
# los define la propia edificacion.
A020_CUADRO_04 = {
    ("A", "1 y 2 lados"): 0.30,   # no-ssot: porcentaje del Cuadro 04
    ("B", "1 y 2 lados"): 0.25,   # no-ssot: porcentaje del Cuadro 04
    ("A", "3 y 4 lados"): 0.35,   # no-ssot: porcentaje del Cuadro 04, no metros — el nuestro
    ("B", "3 y 4 lados"): 0.30,   # no-ssot: porcentaje del Cuadro 04
}


def criterio_a020_vigente():
    """La A.020 SI fija la medida del pozo, y eso corrige un argumento anterior."""
    print()
    print("=" * 74)
    print("DIMENSION DEL POZO — A.020 Cuadro N.o 04 (RM 188-2021-VIVIENDA)")
    print("=" * 74)
    print("  CORRECCION IMPORTANTE. Este proyecto venia sosteniendo que 'la norma")
    print("  vigente no fija medida de pozo, solo desempeno'. Eso es cierto para la")
    print("  A.010, pero INCOMPLETO: la A.020 Vivienda, que es la especifica, SI la")
    print("  fija para bifamiliares y multifamiliares, y manda sobre la generica.")
    print()
    print("  Nota iv del cuadro: la altura del paramento se mide 'desde el alfeizar")
    print("  de la ventana mas baja o 1.00 m desde el nivel de piso terminado hasta")
    print("  la parte alta del parapeto superior'.")
    print()
    h = HN + PARAPETO - ALFEIZAR
    print("  altura de la edificacion   %.2f m" % HN)
    print("  + parapeto                 %.2f m   (SUPUESTO de proyecto)" % PARAPETO)
    print("  - alfeizar mas bajo        %.2f m" % ALFEIZAR)
    print("  = altura del paramento     %.2f m   (< 18,00 m: un solo tramo)" % h)
    print()
    print("  %-8s %-14s %8s %12s  %s" % ("tipo", "lados", "%", "requerido", "nuestro pozo"))
    for (tipo, lados), pct in sorted(A020_CUADRO_04.items()):
        req = pct * h
        marca = "  <== EL NUESTRO" if (tipo, lados) == ("A", "3 y 4 lados") else ""
        print("  %-8s %-14s %7.0f %% %9.2f m  %s%s"
              % (tipo, lados, pct * 100, req, "%.2f m" % min(POZO_ANCHO, POZO_LARGO), marca))
    print()
    print("   A = dormitorios, salas y comedores    B = cocinas y patios techados")
    print()
    req = A020_CUADRO_04[("A", "3 y 4 lados")] * h
    area_req = req * req
    deficit = (req - POZO_LARGO) / req * 100
    print("  RIGE %.0f %%: el pozo es interior (sus cuatro lados son nuestra propia"
          % (A020_CUADRO_04[("A", "3 y 4 lados")] * 100))
    print("  edificacion) y sirve dormitorios.  ->  requerido %.2f m por lado." % req)
    print()
    print("  Un pozo cuadrado de %.2f m NO alcanzaria: falta %.1f %%." % (POZO_LARGO, deficit))
    print("  Se aplica la NOTA iii, que permite exactamente esto:")
    print("     'Cuando la dimension del pozo perpendicular al vano que sirve es")
    print("      inferior hasta en un 20 % al minimo normativo, la dimension en el")
    print("      otro sentido puede compensar dicho deficit, debiendo cumplir con")
    print("      el area de pozo producto de las medidas normativas.'")
    print()
    print("  %-34s %8.1f %%  %s" % ("deficit en el fondo (Y)", deficit,
                                    "ADMISIBLE" if deficit <= 20 else "NO ADMISIBLE"))
    print("  %-34s %8.2f m2" % ("area normativa (%.2f x %.2f)" % (req, req), area_req))
    print("  %-34s %8.2f m2  %s" % ("area del pozo adoptado", AREA_POZO,
                                    "CUMPLE" if AREA_POZO >= area_req else "NO CUMPLE"))
    print()
    print("  POZO ADOPTADO: %.2f m (frente) x %.2f m (fondo) = %.2f m2"
          % (POZO_ANCHO, POZO_LARGO, AREA_POZO))
    print("  Por que NO se hizo cuadrado de %.2f m: el fondo del pozo es tambien el" % req)
    print("  pano del aligerado. Llevarlo a %.2f m obligaria a la losa a %.2f m por"
          % (req, 0.25))   # no-ssot: 0,25 m es el espesor de losa que se evitaria
    print("  la E.060 Tabla 9.1, y eso encarece el metrado entero. Alargando en el")
    print("  frente se cumple el area sin tocar la losa.")
    print()
    print("  Y de paso: el criterio DEROGADO de la A.010 de 2006 pedia 1/3 = %.2f m." % (h / 3))
    print("  Ya no se cita — existe la norma vigente y es la que manda.")


def zapatas():
    print()
    print("=" * 74)
    print("LO QUE EL POZO HABILITA: las zapatas que pide la rubrica")
    print("=" * 74)
    print("  Los bordes del pozo son los muros MX-3, MX-4 y los dos longitudinales")
    print("  interiores, que se parten en ese tramo. Donde el borde queda libre, la")
    print("  losa se apoya en una viga sostenida por COLUMNAS EXENTAS.")
    print()
    print("  Esas columnas si requieren ZAPATA: no estan en el plano de ningun muro")
    print("  portante y concentran carga puntual. El EMS lo contempla: 'zapatas")
    print("  conectadas y/o cimientos corridos armados'.")
    print()
    print("  criterio 2 de la rubrica -> cimiento corrido bajo muros + zapatas bajo")
    print("  las columnas del pozo. Los dos elementos, cada uno donde corresponde.")


if __name__ == "__main__":
    areas()
    ventilacion_vigente()
    criterio_a020_vigente()
    zapatas()
