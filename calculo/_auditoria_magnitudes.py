# -*- coding: utf-8 -*-
"""GUARDIAN 18 - el numero PARECIDO: una cifra vieja al lado de la viva.

POR QUE EXISTE. El 2026-09-27, con diecisiete guardianes en verde, el informe
publicaba la densidad de muros DOS VECES con numeros distintos: el apartado
3.1 decia 14,676 m2 y +122,6 %, el 3.3 decia 14,964 m2 y +127,0 %. La viva es
la segunda. Lo mismo pasaba con la rigidez (dos tablas del 3.5), con el
reparto del modelo (todo el 3.9) y con el periodo. Ninguno de los diecisiete
lo veia, y la razon es estructural:

  - el de CONSTANTES mira los .py, no el borrador;
  - el de CIFRAS RETIRADAS solo caza lo que alguien se acordo de dar de alta;
  - el de SUMAS solo mira filas de total;
  - la REGRESION compara el informe contra si mismo, asi que un numero viejo
    que no cambia queda "identico" para siempre.

O sea que el defecto no es que falte un control: es que ninguno contrastaba
el TEXTO contra el CALCULO. Este lo hace, y al reves de como parece natural:
no busca el numero que falta, busca el que SOBRA por parecido.

COMO AUDITA. Toma las magnitudes vivas -las que los scripts calculan hoy- y
recorre el borrador buscando numeros que se le PAREZCAN sin ser iguales:
entre 0 y 2 % de diferencia. Un numero identico esta bien; uno lejano habla
de otra cosa; uno a un 3 % es casi siempre el mismo numero de una corrida
anterior, que es el defecto mas dificil de ver a ojo porque se lee correcto.

CONTRA EL RUIDO, tres filtros, y los tres nacieron de falsos positivos reales:
  (1) solo numeros de TRES o mas cifras significativas -un "6" suelto se
      parece a 5,94 por casualidad, no por vejez;
  (2) la marca <!-- h --> exime una linea, igual que en el guardian 3, y las
      exenciones SE CUENTAN;
  (3) las magnitudes se declaran con nombre, de modo que el reporte dice cual
      es la viva y el que lo lee puede juzgar en un segundo.
"""
import contextlib
import importlib
import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
BORRADOR = os.path.join(os.path.dirname(AQUI), "borrador")

# LA VENTANA, MEDIDA Y NO ELEGIDA. Se probaron 2 %, 8 % y 3 %.
#   con 2 % se escapaba la densidad vieja por muy poco margen;
#   con 8 % entraban OCHO falsos rojos, y los ocho por la misma razon: este
#     informe publica a proposito numeros a pocos puntos de los vivos -las
#     sensibilidades del ala y del tanque, el reparto del modelo, la lectura
#     alternativa-. Ensanchar la ventana los denuncia a todos.
#   con 3 % caza el defecto real y no denuncia ninguno de esos.
# Lo que queda FUERA de la ventana no queda sin vigilancia: las cifras
# retiradas del guardian 3 cubren el tramo largo, una por una y con nombre.
TOLERANCIA = 0.03
MIN_CIFRAS = 3             # un "15" no se parece a 14,964: coincide
MARCA_EXENTA = "<!-- h -->"
VENTANA_UNIDAD = 14        # cuanto texto se mira detras del numero

# LA UNIDAD ES LA QUE DESAMBIGUA. Sin esto el guardian comparaba 6,72 -que es
# la longitud de un muro- contra los 6,593 m2 de seccion requerida, y 226,4
# -un cortante en toneladas- contra los 227,22 m2 de planta. Dieciocho de sus
# veinte primeros avisos eran de esa clase. Un numero sin unidad no se puede
# contrastar con nada: se deja pasar.
UNIDADES = {
    "m2": r"(?<![A-Za-z])m(?:²|2)",
    "kgf/cm2": r"kgf/cm(?:²|2)",
    "kgf": r"kgf",
    "kgf/cm": r"kgf/cm(?!²|2)",
    "s": r"s",
    "%": r"%",
    "": r"",
}

NUMERO = re.compile(
    r"(?<![\w.,])(\d{1,3}(?:[   ]\d{3})+(?:,\d+)?|\d+,\d+)(?![\w])")


def vivas():
    """Las magnitudes que el proyecto calcula hoy, con su nombre.

    Se importan con la salida silenciada: estos scripts imprimen su informe
    al importarse y si no se calla, el reporte del guardian queda sepultado.
    """
    import proyecto as P
    with contextlib.redirect_stdout(io.StringIO()):
        m01 = importlib.import_module("01_arquitectura_y_densidad")
        m11 = importlib.import_module("11_metrado_muros")
        m12 = importlib.import_module("12_rigidez_lateral")
        m16 = importlib.import_module("16_irregularidades")
        T, k, C, pesos, Pt, V = m16.sismo()
        # tabla() tambien imprime: fuera del redirect, el informe del script 12
        # tapaba el reporte de este guardian.
        t12 = m12.tabla()
    req = m01.densidad_requerida() * P.AREA_PLANTA
    ac = dict((d, sum(f["Ac"] for f in m01.tabla_densidad(d))) for d in "XY")
    peor = max(m11.metrar(), key=lambda f: f["sigma"])
    v = {
        "seccion de muro en X": (ac["X"], "m2"),
        "seccion de muro en Y": (ac["Y"], "m2"),
        "seccion requerida": (req, "m2"),
        "holgura de densidad en X": (100 * (ac["X"] / req - 1), "%"),
        "holgura de densidad en Y": (100 * (ac["Y"] / req - 1), "%"),
        "esfuerzo axial critico": (peor["sigma"], "kgf/cm2"),
        "peso sismico": (Pt, "kgf"),
        "cortante basal": (V, "kgf"),
        "periodo empirico": (T, "s"),
        "suma K en X": (sum(f["K"] for f in t12 if f["dir"] == "X"), "kgf/cm"),
        "suma K en Y": (sum(f["K"] for f in t12 if f["dir"] == "Y"), "kgf/cm"),
        "Ec": (m12.EC, "kgf/cm2"),
        "area de planta": (P.AREA_PLANTA, "m2"),
    }
    for f in t12:
        v["K de %s" % f["nom"].split()[0]] = (f["K"], "kgf/cm")
    return v


def redondea_a(s, viv):
    """El publicado es el vivo escrito con MENOS decimales? Entonces esta bien.

    8,99 no es una cifra vieja de 8,9873: es la misma, redondeada. Sin este
    control el guardian denuncia el redondeo, que es la forma normal de
    publicar un numero en un informe.
    """
    dec = len(s.split(",")[1]) if "," in s else 0
    return abs(round(viv, dec) - valor(s)) < 10.0 ** (-dec) / 2.0


def cifras(s):
    return len(re.sub(r"[^\d]", "", s).lstrip("0"))


def valor(s):
    s = s.replace(" ", "").replace(" ", "").replace(" ", "")
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def main():
    if not os.path.isdir(BORRADOR):
        print("  [!] no existe %s" % BORRADOR)
        return 1
    print("=" * 78)
    print("AUDITORIA DE MAGNITUDES  -  el numero PARECIDO al vivo pero distinto")
    print("=" * 78)
    print("")
    VIVAS = vivas()
    fallas = []
    exentas = 0
    n_num = 0
    for f in sorted(os.listdir(BORRADOR)):
        if not f.endswith(".md"):
            continue
        encabezado = None
        for i, linea in enumerate(io.open(os.path.join(BORRADOR, f),
                                          encoding="utf-8"), 1):
            # EN UNA TABLA LA UNIDAD ESTA EN EL ENCABEZADO. La celda trae
            # "728 351" pelado y la columna se llama "K (kgf/cm)"; sin esto el
            # guardian quedaba ciego justo en las tablas.
            if linea.strip().startswith("|"):
                if encabezado is None:
                    encabezado = linea
            else:
                encabezado = None
            marcada = MARCA_EXENTA in linea
            for m in NUMERO.finditer(linea):
                s = m.group(1)
                if cifras(s) < MIN_CIFRAS:
                    continue
                x = valor(s)
                if x is None:
                    continue
                n_num += 1
                cola = linea[m.end():m.end() + VENTANA_UNIDAD]
                if any(abs(x - w) < 1e-9 or redondea_a(s, w)
                       for w, _u in VIVAS.values()):
                    continue          # ES una magnitud viva, exacta
                for nom, (viv, uni) in VIVAS.items():
                    if abs(viv) < 1e-12:
                        continue
                    d = abs(x - viv) / abs(viv)
                    if d <= 1e-9 or d > TOLERANCIA:
                        continue
                    pegada = re.match(r"\s*(" + UNIDADES[uni] + r")", cola)
                    en_cabecera = (encabezado is not None and uni
                                   and re.search(UNIDADES[uni], encabezado))
                    if not (pegada or en_cabecera):
                        continue
                    if redondea_a(s, viv):
                        continue
                    if marcada:
                        exentas += 1
                        continue
                    fallas.append((f, i, s, nom, viv, 100 * d))
                    break
    print("  %d magnitudes vivas contrastadas contra %d numeros del borrador"
          % (len(VIVAS), n_num))
    if exentas:
        print("  exentas por marca <!-- h -->: %d  -- se cuentan: una exencion"
              % exentas)
        print("   que no se ve es la puerta por donde vuelve todo.")
    print("")
    if not fallas:
        print("  [ok] ningun numero del borrador se parece a un vivo sin serlo")
        print("")
        return 0
    print("  %d NUMERO(S) QUE SE PARECEN A UNO VIVO SIN SERLO:" % len(fallas))
    print("")
    for f, i, s, nom, viv, d in fallas:
        print("   %s:%d  dice %s" % (f, i, s))
        print("      el vivo %s vale %s  (%.2f %% de diferencia)"
              % (nom, ("%.4f" % viv).rstrip("0").rstrip(".").replace(".", ","),
                 d))
    print("")
    return 1


if __name__ == "__main__":
    sys.exit(main())
