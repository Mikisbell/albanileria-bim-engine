# -*- coding: utf-8 -*-
u"""Control mecanico: ningun generador puede tener SU PROPIA lista de ejes.

POR QUE EXISTE
==============
El 2026-09-21 se descubrio que CUATRO archivos de dibujo escribian a mano
`[0.0, POZO_X0, POZO_X1, FRENTE]` -- los cuatro sin el eje 6,00 --, mientras
el calculo usaba `EJES_COLUMNAS_X`, que tiene CINCO. El proyecto dibujaba
cuatro ejes y calculaba con cinco; los vanos, que si salen del SSOT, ya
estaban ubicados con los cinco, asi que el plano se contradecia consigo
mismo.

Es el mismo patron que ya habia mordido tres veces en este proyecto: un dato
del SSOT copiado al lado del SSOT. Documentarlo no alcanzo -- ya estaba
documentado --; lo que impide que vuelva es que un control falle.

QUE PROHIBE
===========
Cualquier literal que reconstruya la lista de ejes longitudinales, y
cualquier lista literal de etiquetas de eje. La forma correcta es
`from proyecto import ejes_x_rotulados`.
"""
import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
DIB = AQUI

# patrones que reconstruyen a mano lo que el SSOT ya da
PROHIBIDOS = [
    (re.compile(r"\[\s*0(?:\.0+)?\s*,\s*POZO_X0\s*,\s*POZO_X1\s*,\s*FRENTE\s*\]"),
     "lista de ejes longitudinales sin el eje 6,00"),
    (re.compile(r'\[\s*"A"\s*,\s*"B"\s*,\s*"C"\s*,\s*"D"\s*\]'),
     "etiquetas de eje escritas a mano (quedan 4 para 5 ejes)"),
    (re.compile(r'ejes\s+A\s+a\s+D'),
     "texto 'ejes A a D' fijo: la letra final sale del SSOT"),
]

# los legacy quedan fuera: se retiran cuando E-05/E-06/E-07 existan
EXENTOS = ("_legacy",)


def archivos():
    for nom in sorted(os.listdir(DIB)):
        if not nom.endswith(".py") or nom.startswith("_auditoria"):
            continue
        p = os.path.join(DIB, nom)
        if os.path.isfile(p):
            yield p


def main():
    hallazgos = []
    for p in archivos():
        if any(e in p for e in EXENTOS):
            continue
        txt = io.open(p, encoding="utf-8").read()
        for k, linea in enumerate(txt.splitlines(), 1):
            # una linea de comentario puede NOMBRAR el patron para explicarlo
            desnuda = linea.strip()
            if desnuda.startswith("#"):
                continue
            for rx, motivo in PROHIBIDOS:
                if rx.search(linea):
                    hallazgos.append((os.path.basename(p), k, motivo,
                                      desnuda[:70]))

    print("=" * 78)
    print("EJES LONGITUDINALES: una sola fuente")
    print("=" * 78)
    n = sum(1 for _ in archivos())
    print("  %d archivos revisados" % n)
    if not hallazgos:
        print("  [ok] ninguno reconstruye la lista de ejes a mano")
        return 0
    for nom, k, motivo, linea in hallazgos:
        print("  %s:%d  %s" % (nom, k, motivo))
        print("        %s" % linea)
    print()
    print("  %d hallazgo(s). Usar: from proyecto import ejes_x_rotulados"
          % len(hallazgos))
    return len(hallazgos)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
