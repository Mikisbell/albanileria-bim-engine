# -*- coding: utf-8 -*-
u"""Extrae el INDICE DE ARTICULOS de los PDF de norma y lo cachea.

POR QUE EXISTE (2026-09-26). Se escribieron diez citas normativas de memoria
y dos estaban mal: se dijo "el analisis estatico del Art. 28" cuando el
metodo de fuerzas estaticas equivalentes es el **Art. 33** de la E.030-2026
--el 28 son *Consideraciones generales para el analisis estructural*--, y se
dijo "el 90 % de masa del Art. 42" cuando eso es el **Art. 40.2** --el 42 son
*Criterios de combinacion*--.

El patron delator vale mas que los dos errores: **los scripts VIEJOS del
proyecto citaban bien y los escritos ese dia citaban mal.** Los viejos se
habian contrastado contra el PDF; los nuevos salieron de la cabeza. La E.030
**2026** renumero respecto de la version anterior, donde el analisis estatico
SI era el Art. 28: toda cita recordada de la norma vieja esta desplazada.

Lo cazo una verificacion manual, y lo manual no escala a 35 scripts. De ahi
este modulo: el indice no se escribe a mano, se EXTRAE del PDF, y el
guardian `_auditoria_citas.py` audita contra el.

FORMATOS. Las normas no rotulan igual:
  - E.030, E.050, A.010, A.020 -> "Articulo N.- Titulo"
  - E.020                      -> "ARTICULO N: TITULO" (en linea corrida)
  - E.060, E.070               -> no usan articulos, sino acapites (7.1.2.b)
Por eso se extraen las DOS cosas: articulos con titulo y acapites presentes.

EL CACHE SE FIRMA. Cada entrada guarda el sha1 del PDF del que salio. Si el
PDF cambia --una norma nueva entra por `_ENTRADA-normas-nuevas/`-- el indice
queda marcado como vencido y hay que regenerarlo. Un indice que no sabe de
que archivo salio es un indice en el que no se puede confiar.
"""
from __future__ import print_function

import hashlib
import io
import json
import os
import re
import subprocess
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
NORMAS = os.path.normpath(os.path.join(AQUI, "..", "..", "06-normas"))
CACHE = os.path.join(AQUI, "indice_normas.json")

# que PDF corresponde a que norma. La clave es como la cita el proyecto.
PDFS = {
    "E.030": "E030-2026-sismorresistente.pdf",
    "E.020": "E020-cargas.pdf",
    "E.050": "E050-suelos-cimentaciones.pdf",
    "E.060": "E060-concreto-armado.pdf",
    "E.070": "Norma E.070 Albanileria (1).pdf",
    "A.010": "A010-condiciones-generales-diseno-2021.pdf",
    "A.020": "A020-vivienda-RM188-2021.pdf",
}

# "Articulo 33.- Titulo" / "ARTICULO 5: TITULO". Se acepta el numero seguido
# de punto-guion, dos puntos o punto solo, y se corta el titulo en el primer
# punto seguido de mayuscula o en un largo razonable.
_ART = re.compile(
    u"ART[IÍ]CULO\\s+(\\d{1,3})\\s*(?:\\.-|:|\\.\\s|\\s-)\\s*([^\\n]{0,160})",
    re.IGNORECASE)
# acapites tipo 7.1.2 / 8.5.4 / 9.2.1, con o sin letra final
_ACA = re.compile(u"(?<![\\d.])(\\d{1,2}(?:\\.\\d{1,2}){1,3})(?![\\d])")


# tabla 1 a 1: cada caracter acentuado va a UNO sin acento, para que la
# normalizacion no cambie la longitud de la cadena.
_TILDES = {ord(a): b for a, b in zip(
    u"áéíóúüñ"
    u"ÁÉÍÓÚÜÑ",
    u"aeiouun" u"AEIOUUN")}


def sin_tildes(s):
    u"""Quita tildes y baja a minuscula, para comparar titulos sin tropezar.

    El titulo sale del PDF con tildes y la cita del codigo suele escribirse
    sin ellas --la consola de esta maquina es cp1252 y la convencion de la
    casa es ASCII en los `print`--. Comparar en crudo hace fallar controles
    que son correctos.
    """
    # LA LONGITUD TIENE QUE SOBREVIVIR. La primera version hacia
    # `encode("ascii","ignore")`, que ELIMINA lo que no mapea: el texto
    # normalizado quedaba mas corto que el original y los indices dejaban de
    # corresponder. El guardian de citas leia entonces una ventana CORRIDA y
    # denunciaba conceptos que estaban en otro parrafo. Se traduce 1 a 1.
    return s.translate(_TILDES).lower()


def _texto(pdf):
    u"""Vuelca el PDF a texto. Devuelve None si el archivo no esta."""
    if not os.path.exists(pdf):
        return None
    try:
        salida = subprocess.check_output(
            ["pdftotext", "-enc", "UTF-8", pdf, "-"],
            stderr=subprocess.PIPE)
    except (OSError, subprocess.CalledProcessError):
        return None
    return salida.decode("utf-8", "replace")


def _sha1(ruta):
    h = hashlib.sha1()
    with open(ruta, "rb") as f:
        for tramo in iter(lambda: f.read(65536), b""):
            h.update(tramo)
    return h.hexdigest()


def _titulo_limpio(bruto):
    u"""Recorta el titulo al enunciado, sin arrastrar el cuerpo del articulo.

    El volcado de texto pega el titulo con el primer parrafo. Se corta en el
    primer numeral de acapite --"33.1."--, que es donde empieza el cuerpo, o
    en el primer punto seguido de espacio y mayuscula.
    """
    t = u" ".join(bruto.split())
    corte = re.search(u"\\s\\d{1,2}\\.\\d", t)
    if corte:
        t = t[:corte.start()]
    corte = re.search(u"\\.\\s+[A-ZÁÉÍÓÚÑ]", t)
    if corte:
        t = t[:corte.start()]
    return t.strip(" .-:")


def construir():
    u"""Recorre los PDF y arma el indice. Devuelve (indice, faltantes)."""
    indice, faltantes = {}, []
    for norma, nombre in sorted(PDFS.items()):
        ruta = os.path.join(NORMAS, nombre)
        if not os.path.exists(ruta):
            # el nombre del E.070 trae una enie en disco; se busca por prefijo
            cands = [x for x in os.listdir(NORMAS)
                     if x.lower().startswith(nombre.split()[0].lower())
                     and x.lower().endswith(".pdf")] if os.path.isdir(NORMAS) else []
            if len(cands) == 1:
                ruta = os.path.join(NORMAS, cands[0])
            else:
                faltantes.append((norma, nombre))
                continue
        txt = _texto(ruta)
        if txt is None:
            faltantes.append((norma, nombre))
            continue
        arts = {}
        for m in _ART.finditer(txt):
            n, tit = m.group(1), _titulo_limpio(m.group(2))
            # se queda con el titulo MAS LARGO visto para ese numero: el
            # indice del principio del PDF lo trunca con puntos suspensivos.
            tit = tit.replace(u".", u" ").strip() if set(tit) <= set(u". ") else tit
            if n not in arts or len(tit) > len(arts[n]):
                arts[n] = tit
        acs = sorted(set(_ACA.findall(txt)))
        indice[norma] = {
            "pdf": os.path.basename(ruta),
            "sha1": _sha1(ruta),
            "articulos": arts,
            "acapites": acs,
        }
    return indice, faltantes


def cargar(regenerar=False):
    u"""Devuelve el indice, regenerandolo si falta o si algun PDF cambio."""
    if not regenerar and os.path.exists(CACHE):
        try:
            ind = json.load(io.open(CACHE, encoding="utf-8"))
        except ValueError:
            ind = None
        if ind:
            vencidas = []
            for norma, d in ind.items():
                ruta = os.path.join(NORMAS, d.get("pdf", ""))
                if os.path.exists(ruta) and _sha1(ruta) != d.get("sha1"):
                    vencidas.append(norma)
            if not vencidas:
                return ind
            print("  [aviso] el PDF cambio en %s: se regenera el indice"
                  % ", ".join(sorted(vencidas)))
    ind, faltantes = construir()
    for norma, nombre in faltantes:
        print("  [aviso] sin PDF para %s (%s): esa norma no se audita"
              % (norma, nombre))
    tmp = CACHE + ".tmp"
    io.open(tmp, "w", encoding="utf-8").write(
        json.dumps(ind, ensure_ascii=False, indent=1, sort_keys=True))
    os.replace(tmp, CACHE)
    return ind


def main():
    ind = cargar(regenerar="--regenerar" in sys.argv)
    print("INDICE DE NORMAS  ->  %s" % os.path.basename(CACHE))
    print("")
    for norma in sorted(ind):
        d = ind[norma]
        print("  %-6s %-46s %3d articulos  %4d acapites"
              % (norma, d["pdf"][:46], len(d["articulos"]), len(d["acapites"])))
    print("")
    # CONTROL: la E.030 es la norma que mas se cita y la que renumero. Si su
    # indice no trae los articulos que el proyecto usa, el guardian nace ciego.
    e030 = ind.get("E.030", {}).get("articulos", {})
    assert e030, "sin indice de la E.030: el guardian no puede auditar nada"
    for n, clave in (("33", "estatico"), ("34", "cortante"), ("35", "altura"),
                     ("36", "odo"), ("37", "xcentricidad"), ("40", "odos"),
                     ("42", "ombinaci"), ("31", "eso")):
        tit = e030.get(n, "")
        assert sin_tildes(clave) in sin_tildes(tit), (
            "el Art. %s de la E.030 se leyo como %r y deberia hablar de %r"
            % (n, tit, clave))
    print("  [ok] los 8 articulos de control de la E.030 leen su titulo real")
    print("  [ok] Art. 33 = %s" % e030["33"])
    print("  [ok] Art. 40 = %s" % e030["40"])


if __name__ == "__main__":
    main()
