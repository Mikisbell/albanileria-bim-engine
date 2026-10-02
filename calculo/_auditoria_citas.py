# -*- coding: utf-8 -*-
u"""GUARDIAN 15 - audita toda cita normativa contra el indice real del PDF.

POR QUE EXISTE. El 2026-09-26 se escribieron diez citas de la E.030 de
memoria y dos estaban mal: "el analisis estatico del **Art. 28**" --que es el
**33**, y el 28 son *Consideraciones generales para el analisis estructural*--
y "el 90 % de masa del **Art. 42**" --que es el **40.2**, y el 42 son
*Criterios de combinacion*--. La causa de fondo es que la E.030 **2026**
renumero respecto de la version anterior, donde el estatico SI era el 28: una
cita recordada de la norma vieja esta desplazada y suena perfectamente bien.

Lo cazo una verificacion manual. Lo manual no escala a 35 scripts, y una
leccion que no se vuelve un control se repite. De ahi este guardian.

DOS CAPAS, porque comprobar que el numero EXISTA no alcanza --el 28 existe--:

  A. EXISTENCIA. Todo "Art. N" y todo acapite "7.1.2" citado tiene que
     figurar en el indice extraido del PDF de esa norma.
  B. CONCEPTO. Si el contexto de la cita habla de un concepto del mapa de
     abajo, el articulo citado tiene que ser el canonico de ese concepto.
     Esta es la capa que caza los dos errores reales: el numero existia.

EL MAPA NO SE CREE A SI MISMO. Cada entrada declara la frase, el articulo y
una palabra que TIENE que aparecer en el titulo real del PDF; al arrancar, el
guardian verifica las tres cosas contra el indice. Si manana entra una E.030
renumerada, el mapa falla al arrancar en vez de aprobar citas viejas.

LO QUE NO CUBRE, Y SE DICE. Una cita sin norma identificable en su contexto
no se audita en la capa A --no hay contra que contrastarla-- y se cuenta
aparte. Un guardian que informa "todo ok" habiendo mirado la mitad es un
verde falso, que es justo lo que esta casa persigue.
"""
from __future__ import print_function

import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, ".."))
sys.path.insert(0, AQUI)

from _indice_normas import cargar, sin_tildes  # noqa: E402

# --------------------------------------------------------------------------
# MAPA DE CONCEPTOS. frase en el contexto -> (norma, articulo, palabra que
# debe estar en el titulo real). La tercera columna es la que impide que el
# mapa se vuelva folclore: la verifica el indice del PDF al arrancar.
# --------------------------------------------------------------------------
CONCEPTOS = [
    # --- metodo de analisis -----------------------------------------------
    (u"analisis estatico",               "E.030", "33", u"estatico"),
    (u"fuerzas estaticas equivalentes",  "E.030", "33", u"equivalentes"),
    (u"fuerzas equivalentes",            "E.030", "33", u"equivalentes"),
    # --- cortante y su reparto --------------------------------------------
    (u"cortante basal",                  "E.030", "34", u"cortante"),
    (u"fuerza cortante en la base",      "E.030", "34", u"base"),
    (u"cortante en la base",             "E.030", "34", u"base"),
    (u"distribucion de la fuerza",       "E.030", "35", u"altura"),
    (u"en altura",                       "E.030", "35", u"altura"),
    (u"fuerza sismica por nivel",        "E.030", "35", u"altura"),
    # --- periodo, torsion, peso -------------------------------------------
    (u"periodo fundamental",             "E.030", "36", u"periodo"),
    (u"excentricidad accidental",        "E.030", "37", u"xcentricidad"),
    (u"estimacion del peso",             "E.030", "31", u"peso"),
    (u"peso sismico",                    "E.030", "31", u"peso"),
    # --- lo dinamico, que es donde se cuela la numeracion vieja -----------
    (u"masa participativa",              "E.030", "40", u"modos"),
    (u"masas efectivas",                 "E.030", "40", u"modos"),
    (u"modos de vibracion",              "E.030", "40", u"modos"),
    # EL "90 %" A SECAS, porque asi es como se escribe de verdad. El error
    # que dio origen a este guardian decia "por encima del 90 % que pide el
    # Art. 42" y NO nombraba el concepto: ninguna frase del mapa lo tocaba y
    # la cita falsa pasaba limpia. En la E.030 ese numero tiene dos duenos
    # --el 40.2 para la masa participativa y el 44.1 para la cortante minima
    # de estructuras irregulares--, y los dos se aceptan.
    (u"90 %",                            "E.030", "40|44", u"modos"),
    (u"criterios de combinacion",        "E.030", "42", u"combinacion"),
    # LA COMBINACION DIRECCIONAL TIENE DOS ARTICULOS, segun el metodo: el
    # 33.3 para el estatico --que es el nuestro-- y el 43 para el modal
    # espectral. Los dos son correctos y el guardian acepta cualquiera.
    (u"combinacion direccional",         "E.030", "43|33", u"direccional"),
    (u"srss",                            "E.030", "43", u"direccional"),
    (u"cortante minima",                 "E.030", "44", u"minima"),
    (u"esfuerzos admisibles",            "E.030", "29", u"admisibles"),
]

# CUANTO CONTEXTO SE MIRA. La primera version usaba 240 caracteres y dio 15
# fallas, casi todas falsas: en "el cortante basal se reparte EN ALTURA
# (Art. 35)" la ventana veia "cortante basal" --que es el 34-- y denunciaba
# una cita correcta. Un guardian que grita en falso se termina ignorando, que
# es la peor forma de no tener guardian. Ahora la ventana es angosta y, si
# caen varios conceptos, GANA EL MAS CERCANO a la cita: en ese ejemplo "en
# altura" queda pegado al "(Art. 35)" y "cortante basal" a thirty y pico.
VENTANA_CONCEPTO = 95
# LA NORMA TIENE QUE ESTAR CERCA. Con 400 caracteres, una mencion suelta de
# la E.020 varias lineas antes se adjudicaba una cita al Art. 35 de la E.030
# y el guardian informaba "el E.020 no tiene Art. 35" sobre una cita correcta.
# Si la norma no esta a la vista de la cita, no se adivina: se declara que
# esa cita no se pudo contrastar.
VENTANA_NORMA = 90

_CITA_ART = re.compile(u"Art(?:\\.|[ií]culo)\\s*(\\d{1,3})(?:\\.(\\d{1,2}))?",
                       re.IGNORECASE)
# los numeros que siguen a "Art. N" unidos por "y" o coma: "Art. 34 y 35"
_COMPUESTA = re.compile(u"(?:\\s*(?:y|,|/)\\s*)(\\d{1,3})")
# la parte NUMERICA de una cita: "Art. 7.1.2.b" -> "7.1.2.b"
_SOLO_NUM = re.compile(u"(\d{1,3}(?:[.]\d{1,2})*)")
_NORMA = re.compile(u"\\b([EA])\\.?\\s?(\\d{3})\\b")
_ACAPITE_E070 = re.compile(u"E\\.?\\s?070[^\\n]{0,40}?(\\d\\.\\d(?:\\.\\d)?)")

# marca para eximir una linea que cita mal A PROPOSITO (contraejemplos)
MARCA_EXENTA = u"<!-- cita-ejemplo -->"

EXTENSIONES = (".py", ".md")
EXCLUIR = ("_legacy", ".git", "borrador_backup", "__pycache__",
           "indice_normas.json", "_auditoria_citas.py", "_indice_normas.py")


def _archivos():
    for base, dirs, nombres in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if not any(x in d for x in EXCLUIR)]
        if any(x in base for x in EXCLUIR):
            continue
        for n in nombres:
            if n.endswith(EXTENSIONES) and not any(x in n for x in EXCLUIR):
                yield os.path.join(base, n)


def _norma_de(texto, pos):
    u"""La norma vigente para una cita: la ultima nombrada antes de ella."""
    tramo = texto[max(0, pos - VENTANA_NORMA):pos]
    ms = list(_NORMA.finditer(tramo))
    if not ms:
        return None
    letra, num = ms[-1].group(1), ms[-1].group(2)
    return u"%s.%s" % (letra.upper(), num)


def _contexto_previo(plano, pos):
    u"""El contexto de una cita es SU ORACION, no 95 caracteres de atras.

    Sin este corte el guardian denunciaba tres citas CORRECTAS: el titulo de
    seccion "Periodo fundamental y cortante basal" caia dentro de la ventana
    del "Articulo 36" que venia debajo, y "cortante basal" ganaba por
    cercania sobre un articulo que si habla del periodo; y la frase de una
    vineta contaminaba la de la vineta siguiente. Un titulo de seccion y la
    oracion de al lado no son el contexto de la cita.

    Se corta en el ultimo limite de oracion: punto, cierre de pregunta,
    salto de parrafo, encabezado markdown, raya, punto y coma o dos puntos.
    """
    tramo = plano[max(0, pos - VENTANA_CONCEPTO):pos]
    marcas = [u". ", u".\n", u"\n\n", u"?", u"#",
              u"--", u";", u":"]
    k = max(tramo.rfind(x) for x in marcas)
    return tramo[k + 1:] if k >= 0 else tramo

def _titulo(indice, norma, art):
    u"""El titulo del articulo, recortado: el volcado arrastra el cuerpo."""
    t = indice.get(norma, {}).get("articulos", {}).get(art, u"?")
    return t if len(t) <= 62 else t[:59] + u"..."


def auditar(indice):
    u"""Devuelve (fallas, revisados, sin_norma)."""
    fallas, revisados, sin_norma, exentas, comentarios = [], 0, 0, 0, 0
    for ruta in _archivos():
        rel = os.path.relpath(ruta, RAIZ).replace("\\", "/")
        try:
            txt = io.open(ruta, encoding="utf-8").read()
        except (IOError, UnicodeDecodeError):
            continue
        plano = sin_tildes(txt)
        lineas = txt.split(chr(10))
        for m in _CITA_ART.finditer(txt):
            art = m.group(1)
            linea = txt.count("\n", 0, m.start()) + 1
            if MARCA_EXENTA in lineas[linea - 1]:
                exentas += 1
                continue
            revisados += 1
            norma = _norma_de(txt, m.start())
            previo_amplio = plano[max(0, m.start() - 320):m.start()]
            # CITAS COMPUESTAS. "Cortante basal y su distribucion en altura
            # (E.030 Art. 34 y 35)" cita DOS articulos con un solo "Art.".
            # Juzgar solo el primero denunciaba una cita correcta.
            acompanantes = set(_COMPUESTA.findall(
                txt[m.end():m.end() + 40].split(")")[0].split(".")[0]))

            # ---- capa A: el articulo existe en esa norma ------------------
            if norma is None or norma not in indice:
                sin_norma += 1
            elif indice[norma]["articulos"]:
                if art not in indice[norma]["articulos"]:
                    fallas.append((rel, linea, u"el %s no tiene Art. %s"
                                   % (norma, art)))
                    continue
            elif indice[norma]["acapites"]:
                # ---- capa C: la norma NO usa articulos, usa ACAPITES ------
                # La E.070, la E.060 y la E.020 se organizan en capitulos y
                # acapites (7.1.2.b, 8.6.1), no en articulos. Antes esta rama
                # no juzgaba nada, y por ese hueco paso una cita INVENTADA
                # que vivio en el proyecto desde el 15-sep y llego al
                # informe: "E.070 Art. 24.5" --repetida seis veces en una
                # figura, incluido su titulo--. La E.070 tiene DIEZ capitulos
                # y ningun 24. Lo que esa figura llamaba 24.5 a 24.8 son los
                # acapites 8.3.5 a 8.3.8: es la numeracion de la DIAPOSITIVA
                # citada como si fuera la norma. Regla de la casa: las
                # diapositivas mandan en COMO se presenta, la norma en QUE se
                # verifica y como se cita.
                # LOS COMENTARIOS NO SON LA NORMA, y numeran distinto.
                # Los *Comentarios a la E.070* (San Bartolome, SENCICO 2008)
                # --que la consigna enlaza-- comentan la version de 2006, que
                # estaba organizada en ARTICULOS: su "Art. 24.5" y su
                # "Art. 24.6" son, en la norma vigente, los acapites 8.3.5 y
                # 8.3.6. Una cita a los Comentarios es legitima y NO se juzga
                # contra el PDF de la Norma; lo que si es un defecto es
                # atribuirsela a la Norma, y eso lo delata la ausencia de la
                # palabra "Comentarios" en el contexto.
                if u"comentario" in previo_amplio:
                    comentarios += 1
                    continue
                pedido = m.group(0)
                num = _SOLO_NUM.search(pedido)
                num = num.group(1) if num else art
                # un acapite con letra -- 7.1.2.b -- se contrasta por su
                # parte numerica, que es lo que el indice del PDF registra.
                raiz = u".".join(num.split(".")[:3])
                if raiz not in indice[norma]["acapites"] and \
                        num.split(".")[0] not in indice[norma]["acapites"] and \
                        not any(a.startswith(raiz + ".")
                                for a in indice[norma]["acapites"]):
                    fallas.append((rel, linea,
                                   u"la %s no tiene %s: esa norma se organiza "
                                   u"en capítulos y acápites, y ese número no "
                                   u"figura en el PDF" % (norma, pedido)))
                    continue

            # ---- capa B: manda el concepto MAS CERCANO a la cita ---
            previo = _contexto_previo(plano, m.start())
            mejor = None          # (distancia, frase, norma, art esperado)
            for frase, nrm, esperado, _pal in CONCEPTOS:
                k = previo.rfind(frase)
                if k < 0:
                    continue
                dist = len(previo) - (k + len(frase))
                if mejor is None or dist < mejor[0]:
                    mejor = (dist, frase, nrm, esperado)
            validos = set(mejor[3].split("|")) if mejor else set()
            if mejor and art not in validos and not (acompanantes & validos):
                _d, frase, nrm, esperado = mejor
                fallas.append((rel, linea,
                               u"habla de «%s» y cita Art. %s; ese "
                               u"concepto es el Art. %s de %s (%s)"
                               % (frase, art, u" o ".join(esperado.split("|")),
                                  nrm, _titulo(indice, nrm,
                                               esperado.split("|")[0]))))

    return fallas, revisados, sin_norma, exentas, comentarios


def _validar_mapa(indice):
    u"""El mapa de conceptos se verifica contra el indice antes de usarlo."""
    arts = indice.get("E.030", {}).get("articulos", {})
    assert arts, "sin indice de la E.030: el guardian nace ciego"
    for frase, norma, art, palabra in CONCEPTOS:
        # un concepto puede tener mas de un articulo valido --la combinacion
        # direccional es el 33.3 en el estatico y el 43 en el modal--, y
        # entonces basta con que UNO de ellos hable de eso.
        acierta = False
        for alt in art.split("|"):
            tit = indice.get(norma, {}).get("articulos", {}).get(alt)
            assert tit, (u"el mapa apunta a %s Art. %s y ese articulo no "
                         u"existe en el indice del PDF" % (norma, alt))
            if sin_tildes(palabra) in sin_tildes(tit):
                acierta = True
        assert acierta, (
            u"el mapa dice que %s Art. %s trata de %r y ninguno de esos "
            u"articulos lo menciona en su titulo real: la norma cambio o el "
            u"mapa esta mal" % (norma, art, palabra))


def main():
    print("")
    print("=" * 74)
    print("GUARDIAN 15  -  citas normativas contra el indice real de los PDF")
    print("=" * 74)
    indice = cargar()
    _validar_mapa(indice)
    print("  [ok] las %d entradas del mapa de conceptos coinciden con el "
          "titulo\n       real de su articulo en el PDF" % len(CONCEPTOS))

    fallas, revisados, sin_norma, exentas, comentarios = auditar(indice)
    print("")
    print("  citas revisadas: %d   sin norma identificable en su contexto: %d"
          % (revisados, sin_norma))
    if comentarios:
        print("  citas a los COMENTARIOS a la E.070 (SENCICO 2008): %d --"
              % comentarios)
        print("   ese documento comenta la version de 2006, organizada en")
        print("   articulos, y numera distinto que la norma vigente.")
    if exentas:
        print("  exentas por marca de contraejemplo: %d -- lineas que citan"
              % exentas)
        print("   mal A PROPOSITO, para explicar un error. Se cuentan: una")
        print("   exencion que no se ve es la puerta por donde vuelve todo.")
    if sin_norma:
        print("  (esas %d NO se contrastaron en la capa de existencia: no hay"
              % sin_norma)
        print("   contra que hacerlo. Se declaran para no dar cobertura falsa.)")
    print("")
    if not fallas:
        print("  [ok] ninguna cita contradice el indice de su norma")
        print("")
        return 0
    print("  %d CITA(S) QUE NO CIERRAN:" % len(fallas))
    print("")
    for rel, linea, motivo in fallas:
        print("   %s:%d" % (rel, linea))
        print("      %s" % motivo)
    print("")
    return 1


if __name__ == "__main__":
    sys.exit(main())
