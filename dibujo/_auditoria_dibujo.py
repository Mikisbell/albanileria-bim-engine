# -*- coding: utf-8 -*-
"""Guardián de las láminas: textos que se pisan y glifos que no se dibujan.

POR QUE HACE FALTA UN GUARDIAN MAS
==================================
Los cinco guardianes de `calculo/` verifican los NUMEROS. Una lamina puede
tener todos sus numeros correctos y ser ilegible: dos rotulos encimados, una
cota tapada por una leyenda, un simbolo que la fuente no dibuja. Nada de eso
aparece en el .dxf -- ahi el texto esta entero y en su sitio --, y a ojo solo
se ven los escandalosos.

QUE MIDE
========
1. SOLAPES. Cada texto se modela como un rectangulo (ancho estimado por el
   mismo factor que usa el membrete, alto = su altura) y se buscan pares que
   compartan mas del umbral de area. Al estrenarse encontro 17 en las seis
   laminas, de los cuales uno tapaba por completo el titulo del plano.

2. GLIFOS. Que no quede ningun caracter fuera del repertorio que la fuente
   de plano dibuja. El saneo lo hace `dxf_membrete.sanear_texto()` al
   generar; esto lo COMPRUEBA sobre el archivo ya escrito, que es lo que se
   entrega.

EL UMBRAL
=========
0,35 del area del texto mas chico. Por debajo de eso son roces de una letra
con una linea de cota, que en el plano no molestan; un control que grita en
falso deja de mirarse.
"""
import glob
import sys
import os
import sys

import ezdxf

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

F_ANCHO = 0.95          # no-ssot: el mismo factor calibrado en dxf_membrete
MIN_SOLAPE = 0.35       # no-ssot: fraccion del area del texto mas chico
EXTRA_OK = "°"     # el grado; verificado que la fuente lo dibuja


def cajas(msp):
    """Cada TEXT como (x0, y0, x1, y1, texto, altura)."""
    out = []
    for e in msp.query("TEXT"):
        t = e.dxf.text
        if not t.strip():
            continue
        h = e.dxf.height
        p = e.dxf.insert
        out.append((p.x, p.y, p.x + len(t) * h * F_ANCHO, p.y + h, t, h))
    return out


def fraccion_solapada(a, b):
    ix = min(a[2], b[2]) - max(a[0], b[0])
    iy = min(a[3], b[3]) - max(a[1], b[1])
    if ix <= 0 or iy <= 0:
        return 0.0
    menor = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
    return (ix * iy) / menor if menor else 0.0


def solapes(ruta):
    cs = cajas(ezdxf.readfile(ruta).modelspace())
    malos = []
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            f = fraccion_solapada(cs[i], cs[j])
            if f >= MIN_SOLAPE:
                malos.append((f, cs[i][4], cs[j][4], cs[i][0], cs[i][1]))
    malos.sort(reverse=True)
    return malos


DENSIDAD = 6        # no-ssot: entidades de dibujo bajo un texto para
                    # considerarlo TAPADO. Por debajo son rotulos que
                    # legitimamente van dentro de un dibujo (ESCALERA, POZO).


def texto_sobre_dibujo(ruta):
    """Textos que caen encima de geometria densa.

    El control de solapes mide texto contra TEXTO. Un rotulo escrito encima
    del rayado de una elevacion, o sobre el recuadro de un membrete, no lo
    ve: ahi el texto choca con LINEAS. Es exactamente lo que hacia que una
    lamina ilegible se reportara como limpia.

    Se cuenta cuantas entidades de dibujo solapan la caja de cada texto; por
    encima del umbral, el texto esta sobre un dibujo y no se lee.
    """
    doc = ezdxf.readfile(ruta)
    msp = doc.modelspace()
    textos, dibujo = [], []
    for e in msp:
        if e.dxftype() == "TEXT":
            t = e.dxf.text
            if t.strip():
                h, p = e.dxf.height, e.dxf.insert
                textos.append((p.x, p.y, p.x + len(t) * h * F_ANCHO,
                               p.y + h, t))
        elif e.dxftype() in ("LINE", "LWPOLYLINE", "CIRCLE", "ARC"):
            try:
                b = ezdxf.bbox.extents([e], fast=True)
                dibujo.append((b.extmin.x, b.extmin.y, b.extmax.x, b.extmax.y))
            except Exception:
                pass
    malos = []
    for tx in textos:
        n = 0
        for d in dibujo:
            if (min(tx[2], d[2]) - max(tx[0], d[0]) > 0
                    and min(tx[3], d[3]) - max(tx[1], d[1]) > 0):
                n += 1
        if n >= DENSIDAD:
            malos.append((n, tx[4], tx[0], tx[1]))
    malos.sort(reverse=True)
    return malos


def glifos(ruta):
    fuera = set()
    for e in ezdxf.readfile(ruta).modelspace().query("TEXT MTEXT"):
        t = e.dxf.text if e.dxftype() == "TEXT" else e.text
        for ch in t:
            if not (32 <= ord(ch) <= 126) and ch not in EXTRA_OK:
                fuera.add((ch, t[:40]))
    return sorted(fuera)


def main():
    print("=" * 96)
    print("AUDITORIA DE LAMINAS  -  textos que se pisan y glifos que no se dibujan")
    print("=" * 96)
    print()
    tot_s = tot_g = tot_d = 0
    import rutas as R
    dxfs = sorted(glob.glob(os.path.join(R.CAD, "*.dxf")))
    assert dxfs, ("no se hallo ningun .dxf en %s: este guardian estaria "
                  "dando verde sobre la nada" % R.CAD)
    for f in dxfs:
        s, g, d = solapes(f), glifos(f), texto_sobre_dibujo(f)
        tot_s += len(s)
        tot_g += len(g)
        tot_d += len(d)
        estado = ("limpia" if not s and not g and not d
                  else "%d solape(s), %d glifo(s), %d tapado(s)"
                  % (len(s), len(g), len(d)))
        print("  %-28s %s" % (os.path.basename(f), estado))
        for frac, t1, t2, x, y in s[:10]:
            print("      %3.0f%%  (%7.2f,%7.2f)  %r" % (100 * frac, x, y, t1[:36]))
            print("      %s  pisa  %r" % (" " * 22, t2[:36]))
        for ch, ctx in g:
            print("      U+%04X %r  en  %r" % (ord(ch), ch, ctx))
        for n, txt, x, y in d[:8]:
            print("      TAPADO por %2d entidades  (%7.2f,%7.2f)  %r"
                  % (n, x, y, txt[:40]))
    print()
    print("  %-34s %d" % ("textos que se pisan", tot_s))
    print("  %-34s %d" % ("glifos fuera del repertorio", tot_g))
    print("  %-34s %d" % ("textos tapados por el dibujo", tot_d))
    return tot_s + tot_g + tot_d


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
