# -*- coding: utf-8 -*-
"""La CIRCULACION y los VANOS, verificados contra la distribución real.

POR QUE EXISTE ESTE SCRIPT
==========================
El 34 derivó QUÉ ambiente va en cada módulo. Nadie verificaba lo siguiente:
**cómo se entra**. Y ahí había cuatro defectos, todos con los doce
guardianes en verde, porque ninguno miraba la circulación:

  F1. EL EDIFICIO NO TENIA PUERTA DE INGRESO. `MUROS_CON_VENTANA` declaraba
      el tipo POR MURO, así que los cuatro vanos de la fachada frontal
      salían ventana. Dos de ellas abrían al núcleo: la escalera común
      tenía dos ventanas a la calle y ninguna puerta.

  F2. LA ZONA COMUN ESTABA PARTIDA EN DOS. El núcleo ocupaba x[3,25; 8,65]
      y[0; 3,36] y el pasaje x[10,70; 11,90] y[3,36; 10,92]: no compartían
      un solo centímetro de borde. Para subir a la vivienda del fondo había
      que cruzar dos ambientes privados de la del frente.

  F3. UN VANO COMUNICABA DOS VIVIENDAS DISTINTAS. MX-4 unía el dormitorio
      principal de una con el hall de la otra. Y MY-4a abría un dormitorio
      directo a la escalera común.

  F4. EL POZO NO TENIA CERRAMIENTO LATERAL. MY-3 y MY-4 se interrumpen en
      la franja del pozo -- 4,20 m por cara -- y el 31 no los metraba como
      tabique porque la coordenada coincide con un eje portante. Los dos
      ambientes que se iluminan por el pozo daban al vacío, sin cerramiento
      y sin ventana.

LA CAUSA, QUE ES UNA SOLA
=========================
`vanos_ubicados()` colocaba cada vano con un criterio PURAMENTE
ESTRUCTURAL -- «el más ancho al tramo más largo, pegado a la columna de la
izquierda» -- y ninguna regla lo obligaba a coincidir con lo que la
arquitectura necesita. El propio `proyecto.py` declaraba en un comentario
que «EL CUADRO DE VANOS SALE DE LA PLANTA, no al revés», y hacía lo
contrario. Una regla que nada hace cumplir la rompe quien la escribió.

QUE VERIFICA
============
  1. Hay una PUERTA de ingreso desde la vía pública a un hall.
  2. Todo recinto es ALCANZABLE desde la vía pública.
  3. Ningún vano comunica dos viviendas distintas.
  4. Ningún vano abre de la zona común a un dormitorio: la puerta de una
     vivienda da a circulación o a la sala-comedor.
  5. Si un muro portante CRUZA un recinto, ahí hay un vano: si no, el muro
     parte el recinto en dos y el modelo de rectángulos deja de valer.
  6. Dos piezas comunes separadas por un muro portante necesitan un vano
     entre ellas, o la zona común no es recorrible.
  7. El pozo tiene cerramiento en sus cuatro caras.
  8. Todo ambiente cuya única luz es el pozo tiene VENTANA al pozo (la
     A.010 Art. 36.2 admite luz prestada para servicios, NO para
     dormitorios ni sala).
  9. Lo declarado en `TRAMO_DE_VANO` coincide, muro por muro, con lo que la
     distribución pide.

CRITERIO DE ADMISIBILIDAD DE UN VANO, declarado
===============================================
  hall     <-> vía pública            el ingreso del edificio
  común    <-> común                  el hall cruzando un muro portante
  hall     <-> circulación de vivienda la puerta de la vivienda
  hall     <-> sala-comedor           idem, admitido: la sala es social
  dentro de la misma vivienda         puerta interior
  recinto  <-> el mismo recinto       el muro que lo cruza, con su paso
  ambiente <-> vía pública            ventana de fachada (solo ventana)
  ambiente <-> pozo                   ventana al pozo (solo ventana)

Cualquier otro par es una falla, no una preferencia.
"""
import contextlib
import importlib.util
import io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from proyecto import (FRENTE, FONDO, EJES_MX,                   # noqa: E402
                      POZO_X0, POZO_X1, POZO_Y0, POZO_Y1,
                      MUROS, TRAMO_DE_VANO, vanos_ubicados,
                      tipo_de_vano, ventanas_del_pozo,
                      CERRAMIENTO_POZO, ejes_de_columna,
                      ANCHO_VANO_EDIFICIO, ANCHO_VANO_VIVIENDA,
                      ANCHO_VANO_AMBIENTE, ANCHO_VANO_BANO)

TOL = 0.02              # no-ssot: m, tolerancia geometrica de coincidencia
ANCHO_PUERTA = 0.90     # no-ssot: el ancho de vano de puerta del SSOT


def _m34():
    """La distribucion arquitectonica del 34, sin su informe por pantalla."""
    ruta = os.path.join(AQUI, "34_distribucion_arquitectonica.py")
    spec = importlib.util.spec_from_file_location("_m34", ruta)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


M34 = _m34()


# ==========================================================================
# LAS PIEZAS DEL PISO
# ==========================================================================
def piezas():
    """Cada recinto del piso, con su vivienda y su clase."""
    viviendas, comun = M34.ambientes()
    out = []
    for n, amb in enumerate(viviendas):
        et = chr(ord("A") + n)
        for m in amb:
            out.append({"id": "%s:%s" % (et, m["nombre"]),
                        "dep": et, "clase": "ambiente",
                        "nombre": m["nombre"], "tipo": m["tipo"],
                        "luz": M34.tiene_luz(m), "uso": None,
                        "x0": m["x0"], "x1": m["x1"],
                        "y0": m["y0"], "y1": m["y1"]})
    for k, c in enumerate(comun, 1):
        uso = c.get("uso", "hall")
        out.append({"id": "COMUN:%s-%d" % (uso.upper(), k), "dep": None,
                    "clase": "comun", "nombre": uso.upper(),
                    "tipo": "circulacion", "luz": None, "uso": uso,
                    "x0": c["x0"], "x1": c["x1"],
                    "y0": c["y0"], "y1": c["y1"]})
    return out


def _sol(a0, a1, b0, b1):
    return min(a1, b1) - max(a0, b0)


def borde_comun(p, q):
    """Longitud del borde que comparten dos piezas; 0 si no se tocan."""
    if abs(p["x1"] - q["x0"]) < TOL or abs(q["x1"] - p["x0"]) < TOL:
        return max(0.0, _sol(p["y0"], p["y1"], q["y0"], q["y1"]))
    if abs(p["y1"] - q["y0"]) < TOL or abs(q["y1"] - p["y0"]) < TOL:
        return max(0.0, _sol(p["x0"], p["x1"], q["x0"], q["x1"]))
    return 0.0


# ==========================================================================
# LOS VANOS, EN COORDENADA DE PLANTA
# ==========================================================================
def _origen(nom, dire):
    """(x, y) del eje del muro. Misma regla que el plano E-01."""
    if dire == "X":
        return 0.0, EJES_MX[int(nom.split("-")[1][0]) - 1]
    x = {"MY-1": 0.0, "MY-2": FRENTE, "MY-3": POZO_X0, "MY-4": POZO_X1}[nom[:4]]
    return x, (POZO_Y1 if nom[4:5] == "b" else 0.0)


def vanos_en_planta():
    """Cada vano con su segmento absoluto y su tipo.

    Incluye las ventanas del CERRAMIENTO DEL POZO, que no viven en `MUROS`
    porque el cierre de las caras laterales del pozo es tabiqueria: ahi no
    hay losa de un lado, asi que ese paño no recibe diafragma en sus dos
    caras y no puede ser muro portante (E.070 9.3.1 admite la unidad hueca
    en tabiques). Un vano en tabique no le quita area de corte al edificio,
    pero SI es el vano por el que esos ambientes se iluminan, asi que el
    control tiene que verlo.
    """
    out = []
    for nom, dire, largo, _t, vs in MUROS:
        if not vs:
            continue
        ox, oy = _origen(nom, dire)
        for a, ancho in vanos_ubicados(nom, dire, largo, vs):
            if dire == "X":
                seg = {"dire": "X", "c": oy, "a": ox + a, "b": ox + a + ancho}
            else:
                seg = {"dire": "Y", "c": ox, "a": oy + a, "b": oy + a + ancho}
            seg.update({"muro": nom, "tipo": tipo_de_vano(nom, a),
                        "ancho": ancho, "portante": True})
            out.append(seg)
    for eje, c, a, ancho in ventanas_del_pozo():
        out.append({"dire": "Y" if eje == "x" else "X", "c": c,
                    "a": a, "b": a + ancho, "ancho": ancho,
                    "muro": "cerramiento del pozo", "tipo": "ventana",
                    "portante": False})
    return out


def da_al_exterior(v):
    """El vano cae sobre un limite del predio."""
    if v["dire"] == "X":
        return abs(v["c"]) < TOL or abs(v["c"] - FONDO) < TOL
    return abs(v["c"]) < TOL or abs(v["c"] - FRENTE) < TOL


def da_al_pozo(v):
    """El vano cae sobre una cara del pozo."""
    if v["dire"] == "X":
        return (POZO_X0 - TOL < v["a"] and v["b"] < POZO_X1 + TOL
                and (abs(v["c"] - POZO_Y0) < TOL
                     or abs(v["c"] - POZO_Y1) < TOL))
    return (POZO_Y0 - TOL < v["a"] and v["b"] < POZO_Y1 + TOL
            and (abs(v["c"] - POZO_X0) < TOL or abs(v["c"] - POZO_X1) < TOL))


def lados(v, ps):
    """Las piezas que el vano pone en contacto (por su borde)."""
    out = []
    for p in ps:
        if v["dire"] == "X":
            if not (p["x0"] - TOL < v["a"] and v["b"] < p["x1"] + TOL):
                continue
            if abs(p["y1"] - v["c"]) < TOL or abs(p["y0"] - v["c"]) < TOL:
                out.append(p)
        else:
            if not (p["y0"] - TOL < v["a"] and v["b"] < p["y1"] + TOL):
                continue
            if abs(p["x1"] - v["c"]) < TOL or abs(p["x0"] - v["c"]) < TOL:
                out.append(p)
    return out


def atraviesa(v, ps):
    """Las piezas por cuyo INTERIOR pasa el vano: el muro las cruza."""
    out = []
    for p in ps:
        if v["dire"] == "X":
            if (p["y0"] + TOL < v["c"] < p["y1"] - TOL
                    and p["x0"] - TOL < v["a"] and v["b"] < p["x1"] + TOL):
                out.append(p)
        else:
            if (p["x0"] + TOL < v["c"] < p["x1"] - TOL
                    and p["y0"] - TOL < v["a"] and v["b"] < p["y1"] + TOL):
                out.append(p)
    return out


def hay_muro(p, q):
    """El borde entre dos piezas cae sobre un muro portante del SSOT."""
    for nom, dire, largo, _t, _vs in MUROS:
        ox, oy = _origen(nom, dire)
        if dire == "X":
            toca = ((abs(p["y1"] - oy) < TOL and abs(q["y0"] - oy) < TOL)
                    or (abs(q["y1"] - oy) < TOL and abs(p["y0"] - oy) < TOL))
            if toca and _sol(max(p["x0"], q["x0"]), min(p["x1"], q["x1"]),
                             ox, ox + largo) > TOL:
                return True
        else:
            toca = ((abs(p["x1"] - ox) < TOL and abs(q["x0"] - ox) < TOL)
                    or (abs(q["x1"] - ox) < TOL and abs(p["x0"] - ox) < TOL))
            if toca and _sol(max(p["y0"], q["y0"]), min(p["y1"], q["y1"]),
                             oy, oy + largo) > TOL:
                return True
    return False


def muros_que_cruzan(p):
    """[(muro, dire, coordenada)] de los muros que parten el recinto.

    Un muro portante que pasa por el interior de un recinto lo parte en
    dos. Solo es admisible si ahi hay un vano que deje pasar: es el caso
    del hall, que cruza el muro MX-2 de adelante hacia atras.
    """
    out = []
    for nom, dire, largo, _t, _vs in MUROS:
        ox, oy = _origen(nom, dire)
        if dire == "X":
            if (p["y0"] + TOL < oy < p["y1"] - TOL
                    and _sol(p["x0"], p["x1"], ox, ox + largo) > TOL):
                out.append((nom, dire, oy))
        else:
            if (p["x0"] + TOL < ox < p["x1"] - TOL
                    and _sol(p["y0"], p["y1"], oy, oy + largo) > TOL):
                out.append((nom, dire, ox))
    return out


# ==========================================================================
# ADMISIBILIDAD DE UN VANO
# ==========================================================================
CIRCULACION = tuple(M34.CIRCULAR)
SOCIALES = tuple(M34.SOCIALES)


def admisible(v, toca, cruza):
    """None si el vano es admisible; el motivo de la falla si no lo es."""
    ext, pozo = da_al_exterior(v), da_al_pozo(v)
    if v["tipo"] == "ventana":
        if not (ext or pozo):
            return "ventana que no da ni a la via publica ni al pozo"
        if len(toca) != 1:
            return "ventana entre %d piezas" % len(toca)
        return None
    # de aca abajo, PUERTAS
    if ext:
        if len(toca) != 1:
            return "puerta de ingreso entre %d piezas" % len(toca)
        if toca[0].get("uso") != "hall":
            return ("puerta a la via publica desde %r, que no es un hall"
                    % toca[0]["id"])
        return None
    if pozo:
        return "puerta al pozo de luz: el pozo es un vacio, no un recinto"
    if not toca and len(cruza) == 1:
        return None                      # el muro cruza el recinto: es paso
    if len(toca) != 2:
        return "puerta entre %d piezas" % len(toca)
    p, q = toca
    if p["clase"] == "comun" and q["clase"] == "comun":
        return None
    for a, b in ((p, q), (q, p)):
        if a["clase"] == "comun" and b["clase"] == "ambiente":
            if a.get("uso") != "hall":
                return ("puerta de la escalera a %r: a una vivienda se entra "
                        "desde el hall, no desde la caja de la escalera"
                        % b["id"])
            if b["nombre"] in SOCIALES or b["nombre"] in CIRCULACION:
                return None
            return ("puerta del hall a %r: la puerta de una vivienda da a "
                    "circulacion o a la sala" % b["id"])
    if p["dep"] != q["dep"]:
        return ("puerta entre las viviendas %s y %s: son dos unidades "
                "independientes" % (p["dep"], q["dep"]))
    return None


# ==========================================================================
# EL ANCHO DE CADA VANO  -  A.020 Art. 12.2.b, Cuadro N.6
# ==========================================================================
# El cuadro fija el ancho minimo POR AMBIENTE SERVIDO, no por muro y no por
# gusto. El proyecto usaba 0,90 m en los diecinueve vanos interiores sin
# fundamento: 0,10 m de sobrancho por vano son 1,90 m de muro que no existe,
# y de la longitud neta salen la densidad, el esfuerzo axial y el corte.
#
# Un vano que separa un ambiente de un pasaje interior toma la exigencia del
# AMBIENTE, porque el cuadro no legisla la circulacion: se toma el mayor de
# los dos lados.
def minimo_del_cuadro(p, q, ext):
    """El ancho minimo que el Cuadro N.6 exige a ese vano, en m."""
    if ext:
        return ANCHO_VANO_EDIFICIO          # acceso principal al multifamiliar
    lados = [x for x in (p, q) if x is not None]
    if any(x["clase"] == "comun" for x in lados) and             any(x["clase"] == "ambiente" for x in lados):
        return ANCHO_VANO_VIVIENDA          # acceso a una unidad de vivienda
    if all(x["clase"] == "comun" for x in lados):
        # el paso entre las dos piezas comunes esta en la ruta de evacuacion;
        # se le da el ancho del acceso a una vivienda, que es el mayor de los
        # minimos que el cuadro fija para un vano interior
        return ANCHO_VANO_VIVIENDA
    req = 0.0
    for x in lados:
        nom = x["nombre"]
        if nom in SOCIALES or nom.startswith("DORM") or nom == "COCINA"                 or nom == "COMEDOR":
            req = max(req, ANCHO_VANO_AMBIENTE)   # descanso, reunion, comer
        elif nom in CIRCULACION:
            continue                              # el cuadro no la legisla
        else:
            req = max(req, ANCHO_VANO_BANO)       # aseo y servicios
    if req == 0.0:
        # los dos lados son circulacion interior de la vivienda: el Cuadro
        # N.6 no legisla ese vano, y lo que rige es la tabla del A.010
        # Art. 20 -- "pasajes de circulacion, interior de viviendas: 0,90 m".
        # Sin esta rama el control denunciaba como "sobrancho" el vano que
        # une el recibidor con el distribuidor, que es la espina de
        # circulacion de la vivienda y tiene que pasar 0,90.
        req = ANCHO_VANO_VIVIENDA
    return req


# ==========================================================================
# CERRAMIENTO DEL POZO
# ==========================================================================
def _cerramiento_declarado(eje, c):
    tot = 0.0
    for e, cc, a, b, _w in CERRAMIENTO_POZO:
        if e == eje and abs(cc - c) < TOL:
            tot += b - a
    return tot


def _cubierto_en_x(x):
    tot = 0.0
    for nom, dire, largo, _t, _vs in MUROS:
        if dire != "Y":
            continue
        ox, oy = _origen(nom, dire)
        if abs(ox - x) > TOL:
            continue
        tot += max(0.0, _sol(oy, oy + largo, POZO_Y0, POZO_Y1))
    return tot + _cerramiento_declarado("x", x)


def _cubierto_en_y(y):
    tot = 0.0
    for nom, dire, largo, _t, _vs in MUROS:
        if dire != "X":
            continue
        ox, oy = _origen(nom, dire)
        if abs(oy - y) > TOL:
            continue
        tot += max(0.0, _sol(ox, ox + largo, POZO_X0, POZO_X1))
    return tot + _cerramiento_declarado("y", y)


# ==========================================================================
# LO QUE LA DISTRIBUCION PIDE: EL ARBOL DE RECORRIDO
# ==========================================================================
def _tramos_de(nom, dire):
    largo = [m[2] for m in MUROS if m[0].startswith(nom[:5])][0]
    ejes = ejes_de_columna(nom, dire, largo)
    _ox, oy = _origen(nom, dire)
    base = oy if dire == "Y" else 0.0
    return [(i, base + ejes[i], base + ejes[i + 1])
            for i in range(len(ejes) - 1)]


def _muro_del_borde(p, q):
    """(muro, dire, a0, a1) del muro portante entre dos piezas, o None."""
    for nom, dire, largo, _t, _vs in MUROS:
        ox, oy = _origen(nom, dire)
        if dire == "X":
            toca = ((abs(p["y1"] - oy) < TOL and abs(q["y0"] - oy) < TOL)
                    or (abs(q["y1"] - oy) < TOL and abs(p["y0"] - oy) < TOL))
            a0, a1 = max(p["x0"], q["x0"]), min(p["x1"], q["x1"])
            if toca and _sol(a0, a1, ox, ox + largo) > TOL:
                return (nom, dire, a0, a1)
        else:
            toca = ((abs(p["x1"] - ox) < TOL and abs(q["x0"] - ox) < TOL)
                    or (abs(q["x1"] - ox) < TOL and abs(p["x0"] - ox) < TOL))
            a0, a1 = max(p["y0"], q["y0"]), min(p["y1"], q["y1"])
            if toca and _sol(a0, a1, oy, oy + largo) > TOL:
                return (nom, dire, a0, a1)
    return None


def _tramo_que_contiene(nom, dire, a0, a1):
    medio = (a0 + a1) / 2.0
    for i, t0, t1 in _tramos_de(nom, dire):
        if t0 - TOL <= medio <= t1 + TOL:
            return i
    return None


def _arbol(grupo, raiz):
    """Arbol de recorrido que PREFIERE tabiques: cuestan 0 area de corte."""
    dentro, fuera = {raiz}, set(range(len(grupo))) - {raiz}
    aristas = []
    while fuera:
        mejor = None
        for i in dentro:
            for j in fuera:
                if borde_comun(grupo[i], grupo[j]) < ANCHO_PUERTA - TOL:
                    continue
                mu = _muro_del_borde(grupo[i], grupo[j])
                peso = (1 if mu else 0, -borde_comun(grupo[i], grupo[j]))
                if mejor is None or peso < mejor[0]:
                    mejor = (peso, i, j, mu)
        if mejor is None:
            break
        _p, i, j, mu = mejor
        aristas.append((i, j, mu))
        dentro.add(j)
        fuera.discard(j)
    return aristas, sorted(fuera)


def vanos_necesarios():
    """{muro: [tramos]} que la distribucion EXIGE, mas los recintos sueltos.

    Se construye el arbol de recorrido de la zona comun y de cada vivienda
    -- prefiriendo los TABIQUES, que no le quitan area de corte a nada -- y
    se anota que conexion cruza que muro portante y en que tramo entre ejes
    de columna. Es de aca de donde sale `TRAMO_DE_VANO` del SSOT, y este
    control verifica que lo declarado alli coincida.
    """
    viviendas, comun = M34.ambientes()
    pedidos, sueltos = {}, []

    def anotar(mu):
        if mu is None:
            return
        nom, dire, a0, a1 = mu
        k = _tramo_que_contiene(nom, dire, a0, a1)
        pedidos.setdefault(nom, set()).add(k)

    com = [dict(c) for c in comun]
    halls = [i for i, c in enumerate(com) if c.get("uso") == "hall"]
    if halls:
        ar, sus = _arbol(com, halls[0])
        for _i, _j, mu in ar:
            anotar(mu)
        sueltos += ["pieza comun %d" % s for s in sus]
    for n, amb in enumerate(viviendas):
        et = chr(ord("A") + n)
        acc = [m for m in amb if m["acceso"]]
        if not acc:
            sueltos.append("la vivienda %s no tiene modulo de acceso" % et)
            continue
        # la puerta de la vivienda, desde el hall
        mejor = None
        for c in com:
            if c.get("uso") != "hall":
                continue
            L = borde_comun(acc[0], c)
            if L >= ANCHO_PUERTA - TOL and (mejor is None or L > mejor[0]):
                mejor = (L, c)
        if mejor:
            anotar(_muro_del_borde(acc[0], mejor[1]))
        raiz = [i for i, m in enumerate(amb) if m["acceso"]][0]
        ar, sus = _arbol(amb, raiz)
        for _i, _j, mu in ar:
            anotar(mu)
        sueltos += ["%s:%s" % (et, amb[s]["nombre"]) for s in sus]
    # la puerta de ingreso al edificio, en el hall que toca la fachada
    frente = [c for c in com if c.get("uso") == "hall" and c["y0"] <= TOL]
    if frente:
        h = frente[0]
        nom = [m[0] for m in MUROS if m[0].startswith("MX-1")][0]
        k = _tramo_que_contiene(nom, "X", h["x0"], h["x1"])
        pedidos.setdefault(nom, set()).add(k)
    # las ventanas de fachada: una por ambiente con luz de fachada
    for n, amb in enumerate(viviendas):
        for m in amb:
            luz = M34.tiene_luz(m) or ""
            if not luz.startswith("fachada"):
                continue
            nom = ("MX-1  fachada frontal" if m["y0"] <= TOL
                   else "MX-7  fachada posterior")
            nom = [x[0] for x in MUROS if x[0].startswith(nom[:4])][0]
            k = _tramo_que_contiene(nom, "X", m["x0"], m["x1"])
            pedidos.setdefault(nom, set()).add(k)
    # la ventana de la escalera, que tambien da a la fachada
    for c in com:
        if c.get("uso") == "escalera" and c["y0"] <= TOL:
            nom = [x[0] for x in MUROS if x[0].startswith("MX-1")][0]
            pedidos.setdefault(nom, set()).add(
                _tramo_que_contiene(nom, "X", c["x0"], c["x1"]))
    return dict((k, sorted(v)) for k, v in pedidos.items()), sueltos


# ==========================================================================
# CONTROL
# ==========================================================================
def _alcanzables(desde, aristas, ids):
    vistos, cola = set(desde), list(desde)
    while cola:
        u = cola.pop()
        for a, b in aristas:
            for x, y in ((a, b), (b, a)):
                if x == u and y not in vistos and y in ids:
                    vistos.add(y)
                    cola.append(y)
    return vistos


def control():
    fallas = []
    ps = piezas()
    ids = set(p["id"] for p in ps)
    vs = vanos_en_planta()

    # ---- 1. ingreso desde la via publica --------------------------------
    ingresos = [v for v in vs if v["tipo"] == "puerta" and da_al_exterior(v)]
    if not ingresos:
        fallas.append("el edificio no tiene PUERTA de ingreso desde la via "
                      "publica: los %d vanos de fachada son ventanas"
                      % sum(1 for v in vs if da_al_exterior(v)))

    # ---- 2. admisibilidad de cada vano ----------------------------------
    aristas = []
    for v in vs:
        toca, cruza = lados(v, ps), atraviesa(v, ps)
        motivo = admisible(v, toca, cruza)
        if motivo:
            fallas.append("%s (%s, %s %.2f-%.2f): %s"
                          % (v["muro"].split()[0], v["tipo"],
                             "x" if v["dire"] == "X" else "y",
                             v["a"], v["b"], motivo))
        if v["tipo"] == "puerta" and len(toca) == 2:
            aristas.append((toca[0]["id"], toca[1]["id"]))
        if v["tipo"] == "puerta" and len(toca) == 1 and da_al_exterior(v):
            aristas.append(("EXTERIOR", toca[0]["id"]))

    # ---- 2b. el ancho de cada vano, contra el Cuadro N.6 ---------------
    for v in vs:
        if v["tipo"] != "puerta":
            continue
        toca = lados(v, ps)
        ext = da_al_exterior(v)
        p0 = toca[0] if toca else None
        q0 = toca[1] if len(toca) > 1 else None
        req = minimo_del_cuadro(p0, q0, ext)
        if v["ancho"] < req - 1e-9:
            fallas.append("%s: el vano mide %.2f m y el Cuadro N.6 de la "
                          "A.020 pide %.2f para el ambiente que sirve"
                          % (v["muro"].split()[0], v["ancho"], req))
        if v["ancho"] > req + 0.05:
            fallas.append("%s: el vano mide %.2f m y el minimo del Cuadro N.6 "
                          "es %.2f; el sobrancho le quita area de corte al "
                          "muro sin fundamento"
                          % (v["muro"].split()[0], v["ancho"], req))

    # ---- 3. un muro que cruza un recinto necesita su paso ---------------
    for p in ps:
        for nom, dire, c in muros_que_cruzan(p):
            hay = False
            for v in vs:
                if v["muro"] != nom or v["tipo"] != "puerta":
                    continue
                if abs(v["c"] - c) > TOL or v["ancho"] < ANCHO_PUERTA - TOL:
                    continue
                if dire == "X" and p["x0"] - TOL < v["a"] \
                        and v["b"] < p["x1"] + TOL:
                    hay = True
                if dire == "Y" and p["y0"] - TOL < v["a"] \
                        and v["b"] < p["y1"] + TOL:
                    hay = True
            if not hay:
                fallas.append("el muro %s cruza %r y no hay vano: el muro "
                              "parte el recinto en dos"
                              % (nom.split()[0], p["id"]))

    # ---- 4. piezas que se tocan, con o sin muro de por medio ------------
    #  sin muro portante entre ellas, dos piezas son un solo espacio y no
    #  hace falta vano; con muro, hace falta y el vano ya se conto arriba
    for i, p in enumerate(ps):
        for q in ps[i + 1:]:
            if borde_comun(p, q) < ANCHO_PUERTA - TOL:
                continue
            if hay_muro(p, q):
                continue
            if p["clase"] == "comun" and q["clase"] == "comun":
                aristas.append((p["id"], q["id"]))
            elif p["dep"] is not None and p["dep"] == q["dep"]:
                aristas.append((p["id"], q["id"]))
            elif p["clase"] != q["clase"]:
                # hall y vivienda sin muro de por medio: es la puerta de la
                # vivienda, en tabique. Admisible si da a circulacion o sala
                com, amb = ((p, q) if p["clase"] == "comun" else (q, p))
                if com.get("uso") == "hall" and (
                        amb["nombre"] in SOCIALES
                        or amb["nombre"] in CIRCULACION):
                    aristas.append((p["id"], q["id"]))
    alc = _alcanzables(["EXTERIOR"], aristas, ids | {"EXTERIOR"})
    for p in ps:
        if p["id"] not in alc:
            fallas.append("%r no se alcanza desde la via publica" % p["id"])

    # ---- 5. el pozo tiene cerramiento en sus cuatro caras ---------------
    for x in (POZO_X0, POZO_X1):
        falta = POZO_Y1 - POZO_Y0 - _cubierto_en_x(x)
        if falta > TOL:
            fallas.append("la cara del pozo en x=%.2f tiene %.2f m sin "
                          "cerramiento" % (x, falta))
    for y in (POZO_Y0, POZO_Y1):
        falta = POZO_X1 - POZO_X0 - _cubierto_en_y(y)
        if falta > TOL:
            fallas.append("la cara del pozo en y=%.2f tiene %.2f m sin "
                          "cerramiento" % (y, falta))

    # ---- 6. el que se ilumina por el pozo, tiene ventana al pozo --------
    for p in ps:
        if p["clase"] != "ambiente" or p["tipo"] != "A":
            continue
        if not (p["luz"] or "").startswith("pozo"):
            continue
        tiene = any(p["id"] in [q["id"] for q in lados(v, ps)]
                    for v in vs
                    if v["tipo"] == "ventana" and da_al_pozo(v))
        if not tiene:
            fallas.append("%r se ilumina por el pozo y no tiene VENTANA al "
                          "pozo" % p["id"])

    # ---- 7. el SSOT declara lo que la planta pide -----------------------
    pedidos, sueltos = vanos_necesarios()
    for s in sueltos:
        fallas.append("%s no queda conectado por el arbol de recorrido" % s)
    for nom, dire, largo, _t, declarados in MUROS:
        pide = pedidos.get(nom, [])
        clave = [k for k in TRAMO_DE_VANO if nom.startswith(k)]
        tiene = TRAMO_DE_VANO[max(clave, key=len)] if clave else []
        if sorted(tiene) != sorted(pide):
            fallas.append("%s: el SSOT declara vanos en los tramos %s y la "
                          "distribucion pide %s"
                          % (nom.split()[0], sorted(tiene), sorted(pide)))
        if len(declarados) != len(tiene):
            fallas.append("%s: %d anchos de vano y %d tramos declarados"
                          % (nom.split()[0], len(declarados), len(tiene)))
    return fallas


def informe():
    ps = piezas()
    vs = vanos_en_planta()
    print("=" * 96)
    print("CIRCULACION Y VANOS  -  verificados contra la distribucion del 34")
    print("=" * 96)
    print()
    print("  piezas del piso: %d ambientes + %d de zona comun"
          % (sum(1 for p in ps if p["clase"] == "ambiente"),
             sum(1 for p in ps if p["clase"] == "comun")))
    print("  vanos          : %d  (%d puertas, %d ventanas; %d en tabique)"
          % (len(vs), sum(1 for v in vs if v["tipo"] == "puerta"),
             sum(1 for v in vs if v["tipo"] == "ventana"),
             sum(1 for v in vs if not v["portante"])))
    print()
    print("  %-8s %-8s %-12s %-26s %-26s"
          % ("muro", "tipo", "posicion", "conecta", "con"))
    print("  " + "-" * 86)
    for v in sorted(vs, key=lambda v: (v["muro"], v["a"])):
        nombres = [t["id"] for t in lados(v, ps)]
        if da_al_exterior(v):
            nombres = nombres + ["VIA PUBLICA"]
        elif da_al_pozo(v):
            nombres = nombres + ["POZO DE LUZ"]
        elif not nombres:
            cr = atraviesa(v, ps)
            if cr:
                nombres = [cr[0]["id"], "(el muro lo cruza)"]
        nombres = (nombres + ["-", "-"])[:2]
        print("  %-8s %-8s %s %5.2f-%5.2f %-26s %-26s"
              % (v["muro"].split()[0], v["tipo"],
                 "x" if v["dire"] == "X" else "y", v["a"], v["b"],
                 nombres[0][:26], nombres[1][:26]))
    print()
    pedidos, _s = vanos_necesarios()
    print("  LO QUE LA DISTRIBUCION PIDE, MURO POR MURO")
    for nom, _d, _l, _t, declarados in MUROS:
        pide = pedidos.get(nom, [])
        if not pide and not declarados:
            continue
        clave = [k for k in TRAMO_DE_VANO if nom.startswith(k)]
        tiene = sorted(TRAMO_DE_VANO[max(clave, key=len)]) if clave else []
        marca = "ok" if tiene == sorted(pide) else "NO COINCIDE"
        print("     %-8s declara tramos %-14s pide %-14s %s"
              % (nom.split()[0], tiene, sorted(pide), marca))
    print()
    fallas = control()
    if fallas:
        print("  FALLAS (%d):" % len(fallas))
        for f in fallas:
            print("   - %s" % f)
    else:
        print("  [ok] hay puerta de ingreso desde la via publica")
        print("  [ok] los %d recintos se alcanzan desde la calle" % len(ps))
        print("  [ok] los %d vanos son admisibles uno por uno" % len(vs))
        print("  [ok] ningun muro parte un recinto sin dejar paso")
        print("  [ok] el pozo tiene cerramiento en sus cuatro caras")
        print("  [ok] los ambientes con luz de pozo tienen ventana al pozo")
        print("  [ok] el SSOT declara exactamente los vanos que la planta pide")
        print("  [ok] cada vano cumple el ancho del Cuadro N.6 de la A.020")
    print("=" * 96)
    return fallas


def main():
    return 1 if informe() else 0


if __name__ == "__main__":
    sys.exit(main())
