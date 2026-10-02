# -*- coding: utf-8 -*-
"""GUARDIAN 17 - toda fila de TOTAL del borrador se vuelve a sumar.

POR QUE EXISTE. El 2026-09-27, con los dieciseis guardianes en verde, la
tabla de rigidez del apartado 3.5 publicaba `Sigma X-X = 728 351` y
`Sigma Y-Y = 849 696` sobre trece filas que sumaban 691 019 y 896 035. Las
trece filas estaban VIVAS -salen del script 12-; las dos sumas estaban
escritas a mano y envejecieron solas. Es el defecto mas barato de cazar que
existe -un jurado con calculadora lo ve en treinta segundos- y ninguno de los
dieciseis miraba ahi, porque todos auditan el CALCULO y este vive en el TEXTO.

En la misma corrida aparecio el segundo caso, y en una tabla GENERADA: el
Anexo B publicaba 115 + 0 + 6 contra un total de 133, porque listaba tres de
los cinco estados del registro. Doce filas sin explicacion. O sea que el
defecto no es de las tablas escritas a mano: es de toda tabla cuyo total no
tiene quien lo vuelva a sumar.

COMO AUDITA. Para cada fila rotulada Suma / Total / Sigma se re-suma cada
columna numerica. Una tabla puede traer VARIOS totales parciales -`Sigma X-X`
y `Sigma Y-Y` sobre las mismas trece filas-, asi que antes de denunciar se
prueba tambien el subconjunto que el propio rotulo nombra: si el rotulo dice
`X-X`, se suman solo las filas que traigan esa marca. Se denuncia unicamente
cuando NINGUNA lectura razonable cierra.

EL ROTULO ES UNA ETIQUETA, NO UNA FRASE. La primera version buscaba la
palabra en cualquier lado de las dos primeras celdas y tomo por fila de total
un renglon que decia "voladizo de altura TOTAL". Un rotulo de total es corto
y empieza por la palabra; una frase que la contiene, no.

LO QUE NO HACE. No verifica que los sumandos sean correctos -de eso se ocupan
los otros dieciseis-: verifica que la tabla cierre consigo misma. Una tabla
que no cierra consigo misma esta mal aunque todos sus numeros esten vivos.
"""
import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
BORRADOR = os.path.join(os.path.dirname(AQUI), "borrador")

TOLERANCIA = 0.012          # 1,2 %: absorbe el redondeo de las celdas
MIN_SUMANDOS = 2
LARGO_ROTULO = 46           # un rotulo de total no es un parrafo

ROTULO = re.compile(r"^(suma|total|acumulad|\u03a3)", re.I)
# un numero de celda: 385 094, 1 421,9, 0,572, -12
NUMERO = re.compile(
    r"^(-?\d{1,3}(?:[ \u2009\u00a0]\d{3})*(?:,\d+)?|-?\d+,\d+|-?\d+)$")
# marcas de direccion que un rotulo parcial puede nombrar: X, Y, X-X, Y-Y
MARCA = re.compile(r"(?<![A-Za-z])([XY])(?:[-\u2013]([XY]))?(?![A-Za-z])")
LIMPIA = re.compile(r"[*`]")


def valor(celda):
    """El numero de una celda, o None si la celda no es un numero."""
    c = LIMPIA.sub("", celda).strip().replace("\u2212", "-")
    m = NUMERO.match(c)
    if not m:
        return None
    s = m.group(1)
    for sep in ("\u2009", "\u00a0", " "):
        s = s.replace(sep, "")
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def celdas(linea):
    t = linea.strip()
    if not t.startswith("|"):
        return None
    return [c.strip() for c in t.strip("|").split("|")]


def es_separador(linea):
    return bool(re.match(r"^\s*\|[\s:\-|]+\|\s*$", linea))


def tablas(texto):
    """Cada bloque contiguo de lineas que empiezan con '|'."""
    lineas = texto.splitlines()
    i = 0
    while i < len(lineas):
        if not lineas[i].strip().startswith("|"):
            i += 1
            continue
        j = i
        bloque = []
        while j < len(lineas) and lineas[j].strip().startswith("|"):
            if not es_separador(lineas[j]):
                c = celdas(lineas[j])
                if c:
                    bloque.append((j + 1, c))
            j += 1
        if len(bloque) >= 3:
            yield bloque
        i = j


def rotulo_de_total(fila):
    """El rotulo si la fila ES una fila de total; None si no lo es."""
    for c in fila[:2]:
        t = LIMPIA.sub("", c).strip()
        if t and len(t) <= LARGO_ROTULO and ROTULO.match(t):
            return t
    return None


def subconjuntos(rotulo, datos):
    """Las lecturas razonables de un total: todas las filas, o las que el
    propio rotulo nombra. Un `Sigma X-X` sobre una tabla de trece muros suma
    siete, no trece, y denunciarlo por no sumar trece seria un falso rojo."""
    yield datos
    for m in MARCA.finditer(rotulo):
        base = m.group(1)
        pat = re.compile(r"^%s([-\u2013]%s)?$" % (base, base))
        sub = [f for f in datos
               if any(pat.match(LIMPIA.sub("", c).strip()) for c in f)]
        if MIN_SUMANDOS <= len(sub) < len(datos):
            yield sub


def auditar(ruta):
    texto = io.open(ruta, encoding="utf-8").read()
    rel = os.path.basename(ruta)
    fallas = []
    n_tablas = n_sumas = 0
    for bloque in tablas(texto):
        n_tablas += 1
        totales = [(n, c, rotulo_de_total(c)) for n, c in bloque]
        totales = [(n, c, r) for n, c, r in totales if r]
        if not totales:
            continue
        ids = set(n for n, _, _ in totales)
        datos = [c for n, c in bloque[1:] if n not in ids]
        if len(datos) < MIN_SUMANDOS:
            continue
        for n_tot, fila, rotulo in totales:
            for k, celda in enumerate(fila):
                declarado = valor(celda)
                if declarado is None or abs(declarado) < 1e-9:
                    continue
                cierra = False
                mejor = None
                for sub in subconjuntos(rotulo, datos):
                    col = [valor(f[k]) for f in sub if k < len(f)]
                    col = [v for v in col if v is not None]
                    if len(col) < MIN_SUMANDOS:
                        continue
                    s = sum(col)
                    if abs(s) < 1e-9:
                        continue
                    n_sumas += 1
                    if abs(declarado - s) / abs(s) <= TOLERANCIA:
                        cierra = True
                        break
                    if mejor is None or abs(declarado - s) < abs(declarado - mejor[0]):
                        mejor = (s, len(col))
                if not cierra and mejor is not None:
                    fallas.append((rel, n_tot, k + 1, rotulo,
                                   declarado, mejor[0], mejor[1]))
    return fallas, n_tablas, n_sumas


def co(x):
    if abs(x - round(x)) < 1e-9:
        return format(int(round(x)), ",").replace(",", " ")
    return ("%.3f" % x).rstrip("0").rstrip(".").replace(".", ",")


def main():
    if not os.path.isdir(BORRADOR):
        print("  [!] no existe %s" % BORRADOR)
        return 1
    print("=" * 78)
    print("AUDITORIA DE SUMAS DE TABLA  -  toda fila de total se vuelve a sumar")
    print("=" * 78)
    print("")
    fallas = []
    n_tablas = n_sumas = 0
    for f in sorted(os.listdir(BORRADOR)):
        if not f.endswith(".md"):
            continue
        fa, nt, ns = auditar(os.path.join(BORRADOR, f))
        fallas += fa
        n_tablas += nt
        n_sumas += ns
    print("  %d tablas recorridas, %d sumas contrastadas" % (n_tablas, n_sumas))
    print("")
    if not fallas:
        print("  [ok] toda fila de total cierra con su propia columna")
        print("")
        return 0
    print("  %d SUMA(S) QUE NO CIERRAN:" % len(fallas))
    print("")
    for rel, lin, col, rotulo, dice, real, n in fallas:
        print("   %s:%d  columna %d  (%s)" % (rel, lin, col, rotulo[:40]))
        print("      la fila dice %s  y sus %d sumandos dan %s"
              % (co(dice), n, co(real)))
    print("")
    return 1


if __name__ == "__main__":
    sys.exit(main())
