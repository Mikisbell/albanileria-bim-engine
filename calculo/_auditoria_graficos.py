# -*- coding: utf-8 -*-
u"""Control: toda seccion TECNICA del informe tiene que llevar figura.

POR QUE
=======
Mikis, 2026-09-21: *"cuando te digo didactico es lo que valora mas la
ingeniera: los graficos explicitos"*. Y la rubrica lo respalda: castiga, en
tres criterios distintos, que *"el plano carece de una buena interpretacion"*
y que *"no se relaciona con su diseno"*.

Al medirlo aparecio que CUATRO de las nueve secciones tecnicas no tenian ni
un grafico -- entre ellas la del modelo computacional, que es el criterio 7
y vale 2 puntos --, y ninguna de las once pasadas de auditoria anteriores lo
habia notado, porque ningun control preguntaba por eso.

Documentarlo no alcanza: lo que impide que vuelva a pasar es que falle.
"""
import io
import struct
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
BORRADOR = os.path.join(RAIZ, "borrador")
FIGURAS = os.path.join(RAIZ, "salidas", "informe")
GENERADOR = os.path.join(RAIZ, "generar_docx.py")

# las secciones que exponen calculo y por lo tanto deben ilustrarse. La
# caratula, el resumen, la introduccion, los objetivos, las referencias y
# los anexos no llevan figura por naturaleza.
PREFIJO_TECNICO = "04-"

# Mikis, 2026-09-21: *"solo 17 figuras para tan inmenso trabajo me parece
# pobre"*, y *"el ojo humano aprende mas viendo que leyendo"*. Exigir UNA
# figura por seccion era el minimo, no la didactica: con una figura y 2 069
# palabras la seccion sigue siendo un muro de texto. Se exige DENSIDAD.
MAX_PALABRAS_POR_FIGURA = 1100


def figuras_por_seccion():
    """Lee de generar_docx.py que figura va a que .md."""
    src = io.open(GENERADOR, encoding="utf-8").read()
    pares = re.findall(
        r'\("([^"]+\.png)",\s*\n?\s*"(?:[^"]*"\s*\n?\s*"?)*?[^"]*",'
        r'\s*\n?\s*"([^"]+\.md)"\)', src)
    out = {}
    for png, md in pares:
        out.setdefault(md, []).append(png)
    return out


def orden_de_figuras():
    """Las figuras tienen que ir en el orden de las secciones.

    El numero de figura lo asigna el ORDEN de la lista, no la seccion. Al
    agregar tandas al principio, la Figura 1 del informe termino siendo un
    detalle de escalera -- de la ultima lamina -- antes de que el lector
    hubiera visto la planta del edificio. Se vio recien al mirar el PDF.
    """
    src = io.open(GENERADOR, encoding="utf-8").read()
    i0 = src.index("FIGURAS_DOC = [")
    i1 = src.index(chr(10) + "]", i0)
    mds = re.findall(r'"([^"]+\.md)"\)', src[i0:i1])
    fuera = []
    for k in range(len(mds) - 1):
        if mds[k] > mds[k + 1]:
            fuera.append((k + 1, mds[k], mds[k + 1]))
    return mds, fuera


def _tiene_generador(png):
    u"""True si algun .py del proyecto nombra esa figura y por tanto la crea.

    Se busca el nombre SIN extension: un generador puede componer la ruta
    (`os.path.join(OUT, "X" + ".png")`) o escribirla entera. Se excluye el
    propio auditor y el legacy, que no producen nada.
    """
    clave = png[:-4] if png.lower().endswith(".png") else png
    # LAS LAMINAS COMPONEN SU NOMBRE. `lamina.py` arma el archivo como
    # "<codigo>_<slug del titulo>_fig.png", asi que el nombre literal NO
    # aparece en ningun .py y las cinco laminas del juego CAD salian
    # denunciadas aunque se regeneran perfectamente. Cuando el nombre tiene
    # forma de lamina se busca su CODIGO, que si esta escrito (codigo="E-01").
    claves = [clave]
    if re.match(r"^[A-Z]-\d{2}_", clave):
        claves.append('codigo="%s"' % clave.split("_")[0])
    # UNA SERIE NUMERADA se compone: "CUADRO-CRITERIOS-%d.png" % n. El
    # literal que SI esta escrito es el nombre sin el numero.
    m_serie = re.match(r"^(.*)-(?:\d+|[A-Z])$", clave)
    if m_serie:
        claves.append(m_serie.group(1) + "-%d")
        claves.append(m_serie.group(1) + "-%s")
    for base in ("dibujo", "figuras", "planos", "calculo"):
        d = os.path.join(RAIZ, base)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if not f.endswith(".py") or f.startswith("_auditoria"):
                continue
            try:
                _txt = io.open(os.path.join(d, f),
                               encoding="utf-8").read()
                if any(k in _txt for k in claves):
                    return True
            except (IOError, UnicodeDecodeError):
                continue
    return False


def main():
    dest = figuras_por_seccion()
    secs = sorted(s for s in os.listdir(BORRADOR)
                  if s.endswith(".md") and s.startswith(PREFIJO_TECNICO))
    print("=" * 74)
    print("GRAFICOS POR SECCION TECNICA")
    print("=" * 74)
    sin = []
    for s in secs:
        n = len(dest.get(s, []))
        palabras = len(io.open(os.path.join(BORRADOR, s),
                               encoding="utf-8").read().split())
        if n == 0 or palabras / n > MAX_PALABRAS_POR_FIGURA:
            sin.append((s, palabras, n))
        print("  %-42s %d figura(s)  %5d palabras  %6s pal/fig"
              % (s, n, palabras, ("%.0f" % (palabras / n)) if n else "--"))
    print()
    # y que cada figura declarada EXISTA en disco
    faltan = []
    informe = os.path.join(RAIZ, "salidas", "informe")
    legacy = os.path.join(RAIZ, "dibujo", "_legacy")
    for md, pngs in dest.items():
        for png in pngs:
            if not (os.path.isfile(os.path.join(informe, png))
                    or os.path.isfile(os.path.join(legacy, png))):
                faltan.append(png)
    if faltan:
        print("  figuras declaradas que NO existen en disco:")
        for f in faltan:
            print("     %s" % f)
    if sin:
        print("  SECCIONES POR DEBAJO DEL CRITERIO (1 figura cada %d palabras):"
              % MAX_PALABRAS_POR_FIGURA)
        for s, pal, n in sin:
            print("     %-42s %d fig para %d palabras" % (s, n, pal))
        print()
        print("  La rubrica castiga en tres criterios que el trabajo no se")
        print("  ilustre. Una seccion de calculo sin figura es un hueco.")
    else:
        _tot = sum(len(v) for v in dest.values())
        _pal = sum(len(io.open(os.path.join(BORRADOR, s),
                               encoding="utf-8").read().split())
                   for s in os.listdir(BORRADOR) if s.endswith(".md"))
        print("  [ok] las %d secciones tecnicas cumplen la densidad "
              "(1 figura cada %d palabras o menos)"
              % (len(secs), MAX_PALABRAS_POR_FIGURA))
        print("  [ok] el informe entero va a 1 figura cada %.0f palabras"
              % (_pal / _tot))
    if not faltan:
        print("  [ok] las %d figuras declaradas existen en disco"
              % sum(len(v) for v in dest.values()))

    # --- que EXISTAN no alcanza: tienen que ser REGENERABLES --------------
    # Este control nacio el 2026-09-27. El informe habia sumado tres figuras
    # excelentes --las mejores del proyecto en valor didactico-- que NO tenian
    # generador: PNG sueltos en `salidas/informe/`. El auditor decia
    # "las 41 figuras declaradas existen en disco" y estaba en verde, porque
    # solo miraba existencia. Una figura que no se regenera con la cadena es
    # PEOR que ninguna: cuando el calculo cambia, ella se queda con el numero
    # viejo y con aspecto de verificada. El proyecto ya lo habia sufrido con
    # las laminas legacy --publicaban Ve/0,55Vm = 0,63 cuando el vivo era
    # 0,572-- y con el flujograma, que llego a tener QUINCE datos vencidos.
    # Medido el mismo dia: de las tres nuevas, una publicaba seis numeros que
    # no eran los del calculo, incluida una excentricidad diez veces menor
    # que la real.
    huerfanas = sorted(set(
        png for pngs in dest.values() for png in pngs
        if not _tiene_generador(png)))
    if huerfanas:
        print()
        print("  FIGURAS SIN GENERADOR (existen en disco y NADIE las produce):")
        for png in huerfanas:
            print("     %s" % png)
        print("  No se regeneran con la cadena, ningun control las mide y")
        print("  envejecen con aspecto de verificadas. Cada una necesita su")
        print("  generador en dibujo/, derivando del SSOT.")
    else:
        print("  [ok] las %d figuras se REGENERAN: cada una tiene su generador"
              % sum(len(v) for v in dest.values()))
    mds, desorden = orden_de_figuras()
    if desorden:
        print()
        print("  FIGURAS FUERA DE ORDEN (el numero lo da la posicion):")
        for k, a, b in desorden:
            print("     posicion %d: %s viene antes que %s" % (k, a, b))
    else:
        print("  [ok] las %d figuras van en el orden de las secciones"
              % len(mds))
    _tamano_en_la_pagina(dest)
    # las huerfanas SUMAN al exit code: una figura del informe que nadie
    # regenera es deuda real, y un guardian que la reporta sin fallar deja
    # la cadena en verde sobre un defecto vivo.
    return len(sin) + len(faltan) + len(desorden) + len(huerfanas)


CAJA_W, CAJA_H = 6.30, 8.86      # pulgadas utiles de una A4 con 2,5 cm
CUERPO_BASE = 7.5                # el cuerpo tipico de un rotulo de figura
CUERPO_MIN = 6.5                 # lo minimo que se lee impreso


def _dpi_del_png(datos):
    """El dpi con que se guardo, leido del chunk pHYs."""
    i = 8
    while i < len(datos) - 8:
        largo = struct.unpack(">I", datos[i:i + 4])[0]
        tipo = datos[i + 4:i + 8]
        if tipo == b"pHYs":
            px, _py, u = struct.unpack(">IIB", datos[i + 8:i + 17])
            return px * 0.0254 if u == 1 else None
        if tipo == b"IDAT":
            return None
        i += 12 + largo
    return None


def _tamano_en_la_pagina(dest):
    """Con que cuerpo se imprime el rotulo de cada figura. Ver el docstring
    del bloque de arriba."""
    filas = []
    for figs in dest.values():
        for nom in figs:
            ruta = os.path.join(FIGURAS, nom)
            if not os.path.exists(ruta):
                continue
            d = io.open(ruta, "rb").read()
            if d[:8] != bytes([137, 80, 78, 71, 13, 10, 26, 10]):
                continue
            w, h = struct.unpack(">II", d[16:24])
            dpi = _dpi_del_png(d)
            if not dpi:
                continue
            nat_w, nat_h = w / dpi, h / dpi
            esc = min(CAJA_W / nat_w, CAJA_H / nat_h, 1.0)
            filas.append((esc * CUERPO_BASE, nom, nat_w, nat_h))
    if not filas:
        return
    filas.sort()
    malas = [f for f in filas if f[0] < CUERPO_MIN]
    print()
    print("  TAMANO CON QUE SE IMPRIME CADA FIGURA")
    print("  un rotulo de %.1f pt aterriza por debajo de %.1f en %d de %d:"
          % (CUERPO_BASE, CUERPO_MIN, len(malas), len(filas)))
    for cuerpo, nom, nw, nh in malas[:12]:
        print("     %-46s %5.1f x %4.1f pulg  ->  %.1f pt"
              % (nom[:46], nw, nh, cuerpo))
    if len(malas) > 12:
        print("     ... y %d mas" % (len(malas) - 12))
    if not malas:
        print("     [ok] ninguna: las %d se leen en la hoja" % len(filas))


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
