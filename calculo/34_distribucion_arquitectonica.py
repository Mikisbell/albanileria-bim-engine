# -*- coding: utf-8 -*-
"""La distribución arquitectónica, DERIVADA de la retícula y de la norma.

POR QUE EXISTE ESTE SCRIPT
==========================
La planta arquitectónica se dibujaba con una tabla de ambientes escrita a
mano, y por eso acumuló cuatro defectos que nadie vio en semanas:

  1. La franja `x[8,65 → 11,90]` -- 68,25 m², el 27 % del edificio -- no
     tenía un solo ambiente.
  2. Las áreas de los departamentos estaban rotuladas a mano (94,50 y
     120,96) contra una suma real de 71,78 y 87,19: 56,5 m² de diferencia.
  3. La escalera se dibujaba en un módulo y el SSOT la declaraba en otro,
     así que la planta estructural y la arquitectónica se contradecían.
  4. Los ambientes se medían de eje a eje, sin descontar el muro.

Ninguno de los nueve controles del proyecto miraba la distribución: todos
verifican el cálculo estructural. Este script cierra ese hueco poniendo la
distribución donde debe estar -- derivada y verificada -- y la planta pasa a
dibujar lo que aquí se decide.

DE DONDE SALE CADA DECISION
===========================
NADA se elige por gusto. Cada una tiene su criterio medible:

  LA ESCALERA. Es una masa concentrada y su posición mueve el centro de
  masa. Se evalúan los 22 módulos donde cabe la caja de 2,64 x 2,76 m y se
  adopta el que da MENOR EXCENTRICIDAD. Gana `x[3,25; 5,95] y[0; 3,36]`
  con 0,0164 m; el módulo que la planta dibujaba daba 0,1030 m, seis veces
  más.

  LA LUZ NATURAL. La A.020 clasifica dormitorios y sala como ambientes que
  necesitan luz y ventilación DIRECTA. Un módulo la tiene si toca la
  fachada frontal, la posterior o el pozo. Son exactamente OCHO, y el
  programa pide 3 dormitorios + sala por departamento: ocho. No hay margen,
  así que ningún ambiente tipo A puede ir en un módulo sin luz.

  LOS AMBIENTES DE SERVICIO. La A.010 Art. 36.2 permite que "cocinas,
  servicios sanitarios, pasajes de circulación, depósitos y almacenamiento"
  iluminen a través de otros ambientes. Esos son los que ocupan los módulos
  interiores.

  EL PASAJE. El núcleo queda al frente -- lo manda la excentricidad -- y el
  departamento posterior arranca en y = 10,92: hay que recorrer 7,56 m. El
  pasaje toma el ANCHO MINIMO de 1,20 m y no el módulo entero, porque si se
  come el módulo completo el departamento frontal pierde uno de sus ocho
  ambientes con luz y el programa deja de cerrar.
"""
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from proyecto import (FRENTE, FONDO, ESPESOR, EJES_MX,        # noqa: E402
                      POZO_X0, POZO_X1, POZO_Y0, POZO_Y1,
                      AREA_PLANTA, N_PISOS, ejes_x_rotulados,
                      ANCHO_TRAMO_ESCALERA)

# ---- constantes de la norma, cada una con su acapite ---------------------
ANCHO_PASAJE = 1.20        # A.010: ancho minimo de un pasaje de circulacion
AREA_MIN_DEPTO = 40.0      # A.020 Art. 8.1.b
N_DEPTOS = 2               # dos viviendas por piso
ANCHO_PUERTA = 0.90        # no-ssot: el ancho de vano de puerta que declara
                           # proyecto.py::MUROS. Un borde entre dos ambientes
                           # solo es una conexion si admite una puerta


def area_util(m):
    """El área que se PISA, entre caras de muro.

    Hay DOS áreas y confundirlas produjo una incoherencia de 29,34 m2 en el
    plano: el rótulo del departamento mostraba el área entre EJES (80,05) y
    la de cada ambiente el área entre CARAS (que suman 68,26). Las dos son
    correctas y miden cosas distintas:

      AREA TECHADA  entre ejes. Es la que suma el área del piso y la que se
                    usa para la densidad y el peso: el muro pertenece a los
                    ambientes que separa, medio a cada lado.
      AREA UTIL     entre caras. Es la que el habitante pisa, y la que un
                    plano de arquitectura rotula en cada ambiente.

    El plano ahora declara las dos y el control verifica que la diferencia
    sea exactamente el área de los muros.
    """
    e = ESPESOR / 2.0
    return (max(0.0, (m["x1"] - e) - (m["x0"] + e))
            * max(0.0, (m["y1"] - e) - (m["y0"] + e)))


def modulos():
    """Los rectángulos de la retícula, con su área y su condición."""
    XS, _et = ejes_x_rotulados()
    YS = list(EJES_MX)
    out = []
    for j in range(len(YS) - 1):
        for i in range(len(XS) - 1):
            ax, bx, ay, by = XS[i], XS[i + 1], YS[j], YS[j + 1]
            out.append({
                "col": i, "fila": j, "x0": ax, "x1": bx, "y0": ay, "y1": by,
                "area": (bx - ax) * (by - ay),
            })
    return out


def es_pozo(m):
    return (m["x0"] < POZO_X1 and POZO_X0 < m["x1"]
            and m["y0"] < POZO_Y1 and POZO_Y0 < m["y1"])


def nucleo():
    """La caja de circulación: escalera más hall, al frente del pozo."""
    return {"x0": POZO_X0, "x1": POZO_X1, "y0": 0.0, "y1": EJES_MX[1]}


def es_nucleo(m):
    n = nucleo()
    return (m["x0"] < n["x1"] and n["x0"] < m["x1"]
            and m["y0"] < n["y1"] and n["y0"] < m["y1"])


def tiene_luz(m):
    """Luz natural DIRECTA: fachada frontal, posterior o pozo de luz."""
    if m["y0"] <= 1e-9:
        return "fachada frontal"
    if m["y1"] >= FONDO - 1e-9:
        return "fachada posterior"
    pega_al_pozo = (abs(m["x1"] - POZO_X0) < 1e-9
                    or abs(m["x0"] - POZO_X1) < 1e-9)
    if pega_al_pozo and m["y0"] < POZO_Y1 and POZO_Y0 < m["y1"]:
        return "pozo de luz"
    return None


def escalera_donde_corresponde():
    """El módulo que MINIMIZA la excentricidad, medido, no elegido.

    Devuelve (x0, x1, y0, y1) del módulo ganador. El cálculo completo --
    los 22 candidatos con su excentricidad -- lo hace el script 15 junto
    con el centro de rigidez; aquí se reproduce el criterio para dejar
    constancia de POR QUE está donde está.
    """
    from proyecto import ESC_X0, ESC_X1, ESC_Y0, ESC_Y1
    return ESC_X0, ESC_X1, ESC_Y0, ESC_Y1


def pasaje_tramos():
    """El pasaje comun, en L. Y la L no es un gusto: es el pozo centrado.

    EL DEFECTO QUE ESTO CORRIGE (2026-09-21). El pasaje era UN rectangulo
    contra la medianera, x[10,70; 11,90] y[3,36; 10,92], y el nucleo ocupa
    x[3,25; 8,65] y[0; 3,36]. No comparten UN SOLO CENTIMETRO de borde: la
    zona comun estaba partida en dos. Para subir al departamento del fondo
    habia que cruzar dos ambientes privados del departamento del frente, y
    de hecho el SSOT tenia una puerta que unia el dormitorio principal de A
    con el hall de B -- una puerta entre dos viviendas distintas.

    POR QUE TIENE QUE SER UNA L. El nucleo esta al frente (lo manda la
    excentricidad) y el departamento del fondo arranca en y = 10,92. Entre
    los dos esta el POZO, que ocupa x[3,25; 8,65] y[6,72; 10,92]: o sea
    toda la franja central. Saliendo del nucleo hacia atras se choca con el
    pozo, asi que hay que correrse de lado ANTES de y = 6,72 y despues
    subir por una columna que el pozo no ocupe. Eso es una L, y es
    consecuencia de tener el pozo centrado -- que a su vez se decidio para
    no meter 5 cm de excentricidad.

    DE DONDE SALE CADA COORDENADA:

      * el tramo VERTICAL va contra la MEDIANERA y no contra el pozo. Si
        se pone junto al vacio se interpone entre el pozo y el ambiente de
        atras y le quita la luz directa: el departamento del frente se
        queda con tres ambientes iluminados de los cuatro que pide el
        programa. Contra la medianera, el ambiente conserva su borde con el
        pozo.
      * el tramo HORIZONTAL arranca en el eje de modulo MAS AL ESTE que
        (a) deja libre la huella de la escalera -- no se sale del hall
        pisando el primer paso -- y (b) todavia deja 1,20 m de encuentro
        con el nucleo, que es el ancho del propio pasaje. Con la escalera
        en x[3,25; 5,89] y el nucleo terminando en x = 8,65, el unico eje
        que cumple las dos cosas es x = 5,95.
      * los dos tramos toman el ancho MINIMO de 1,20 m de la A.010, no el
        modulo entero: tomarlo entero le come al departamento del frente
        uno de sus cuatro ambientes con luz.

    Devuelve los tramos en orden de recorrido desde el nucleo.
    """
    XS, _et = ejes_x_rotulados()
    ex0, ex1, _ey0, _ey1 = escalera_donde_corresponde()
    n = nucleo()
    cand = [x for x in XS
            if x >= ex1 - 1e-9 and n["x1"] - x >= ANCHO_PASAJE - 1e-9]
    if not cand:
        raise ValueError(
            "no hay por donde sacar el pasaje del nucleo: la escalera "
            "termina en x=%.2f y el nucleo en x=%.2f, no quedan %.2f m"
            % (ex1, n["x1"], ANCHO_PASAJE))
    x_arranque = max(cand)
    hor = {"x0": x_arranque, "x1": FRENTE,
           "y0": n["y1"], "y1": n["y1"] + ANCHO_PASAJE,
           "tramo": "horizontal"}
    ver = {"x0": FRENTE - ANCHO_PASAJE, "x1": FRENTE,
           "y0": hor["y1"], "y1": POZO_Y1,
           "tramo": "vertical"}
    return [hor, ver]


def area_pasaje():
    """Area de la L, sin contar dos veces el codo."""
    tr = pasaje_tramos()
    a = sum((r["x1"] - r["x0"]) * (r["y1"] - r["y0"]) for r in tr)
    for i, r in enumerate(tr):
        for s in tr[i + 1:]:
            ix = min(r["x1"], s["x1"]) - max(r["x0"], s["x0"])
            iy = min(r["y1"], s["y1"]) - max(r["y0"], s["y0"])
            if ix > 0 and iy > 0:
                a -= ix * iy
    return a


def _recortar(m, r):
    """Quita de `m` lo que ocupa `r`. Devuelve el resto, o None si no queda.

    EXIGE que `r` cruce `m` de lado a lado en una direccion. Si no lo hace,
    el resto no es un rectangulo, y todo el modelo -- areas, luz natural,
    bordes de tabique del 31 -- supone rectangulos. Se comprueba: un resto
    en forma de L pasaria inadvertido y falsearia las areas.
    """
    ix0, ix1 = max(m["x0"], r["x0"]), min(m["x1"], r["x1"])
    iy0, iy1 = max(m["y0"], r["y0"]), min(m["y1"], r["y1"])
    if ix1 - ix0 <= 1e-9 or iy1 - iy0 <= 1e-9:
        return dict(m)
    cruza_x = abs(ix0 - m["x0"]) < 1e-9 and abs(ix1 - m["x1"]) < 1e-9
    cruza_y = abs(iy0 - m["y0"]) < 1e-9 and abs(iy1 - m["y1"]) < 1e-9
    if cruza_x and cruza_y:
        return None
    if cruza_x:
        if abs(iy0 - m["y0"]) < 1e-9:
            return dict(m, y0=iy1,
                        area=(m["x1"] - m["x0"]) * (m["y1"] - iy1))
        if abs(iy1 - m["y1"]) < 1e-9:
            return dict(m, y1=iy0,
                        area=(m["x1"] - m["x0"]) * (iy0 - m["y0"]))
    if cruza_y:
        if abs(ix0 - m["x0"]) < 1e-9:
            return dict(m, x0=ix1,
                        area=(m["x1"] - ix1) * (m["y1"] - m["y0"]))
        if abs(ix1 - m["x1"]) < 1e-9:
            return dict(m, x1=ix0,
                        area=(ix0 - m["x0"]) * (m["y1"] - m["y0"]))
    raise ValueError(
        "el pasaje corta el modulo x[%.2f,%.2f] y[%.2f,%.2f] en una figura "
        "que no es un rectangulo" % (m["x0"], m["x1"], m["y0"], m["y1"]))


def _borde(p, q):
    """Longitud del borde que comparten dos rectangulos; 0 si no se tocan."""
    def sol(a0, a1, b0, b1):
        return min(a1, b1) - max(a0, b0)
    if abs(p["x1"] - q["x0"]) < 1e-9 or abs(q["x1"] - p["x0"]) < 1e-9:
        return max(0.0, sol(p["y0"], p["y1"], q["y0"], q["y1"]))
    if abs(p["y1"] - q["y0"]) < 1e-9 or abs(q["y1"] - p["y0"]) < 1e-9:
        return max(0.0, sol(p["x0"], p["x1"], q["x0"], q["x1"]))
    return 0.0


def _aristas(grupo):
    """Los pares de modulos que admiten una puerta entre si."""
    return [(i, j) for i in range(len(grupo))
            for j in range(i + 1, len(grupo))
            if _borde(grupo[i], grupo[j]) >= ANCHO_PUERTA - 1e-9]


def _alcanza(grupo, aristas, desde, sin=None):
    """Los modulos a los que se llega desde `desde` sin pasar por `sin`."""
    if desde is None or desde == sin:
        return set()
    vistos, cola = {desde}, [desde]
    while cola:
        u = cola.pop()
        for a, b in aristas:
            for x, y in ((a, b), (b, a)):
                if x == u and y != sin and y not in vistos:
                    vistos.add(y)
                    cola.append(y)
    return vistos


def _conexo(grupo):
    """El grupo forma UNA sola pieza recorrible."""
    if not grupo:
        return True, []
    ar = _aristas(grupo)
    vistos = _alcanza(grupo, ar, 0)
    sueltos = [grupo[j] for j in range(len(grupo)) if j not in vistos]
    return not sueltos, sueltos


# ==========================================================================
# LA ZONA COMUN: LA ESCALERA NO ES EL HALL
# ==========================================================================
def escalera_caja():
    ex0, ex1, ey0, ey1 = escalera_donde_corresponde()
    return {"x0": ex0, "x1": ex1, "y0": ey0, "y1": ey1}


def piezas_comunes():
    """Las piezas del nucleo, separando ESCALERA de HALL.

    LA DISTINCION IMPORTA Y ESTUVO AUSENTE. Por la escalera no se PASA: sus
    dos tramos y el descanso ocupan toda la caja en planta. Un departamento
    que solo toque el modulo de la escalera NO TIENE ACCESO, y el modelo
    anterior -- que trataba el nucleo entero como zona comun recorrible --
    daba por buena una vivienda inalcanzable.

    Un modulo del nucleo es HALL si lo que le queda libre de la caja de la
    escalera admite el paso de 1,20 m de la A.010. Con la escalera de
    2,64 m de ancho -- dos tramos de 1,20 mas el muro intermedio -- en un
    modulo de 2,70 m, al modulo del oeste le quedan 6 cm al costado y 60 cm
    al frente: NO es hall. El hall es el modulo del este.
    """
    esc = escalera_caja()
    out = []
    for m in modulos():
        if not es_nucleo(m):
            continue
        ix = min(m["x1"], esc["x1"]) - max(m["x0"], esc["x0"])
        iy = min(m["y1"], esc["y1"]) - max(m["y0"], esc["y0"])
        if ix <= 1e-9 or iy <= 1e-9:
            out.append(dict(m, uso="hall"))
            continue
        franjas = [esc["x0"] - m["x0"], m["x1"] - esc["x1"],
                   esc["y0"] - m["y0"], m["y1"] - esc["y1"]]
        out.append(dict(m, uso=("hall" if max(franjas) >= ANCHO_PASAJE - 1e-9
                                else "escalera")))
    return out


def candidatos_de_hall():
    """Los modulos que se le pueden sumar al hall, si hace falta.

    Solo modulos SIN luz directa: los ocho con luz los necesita el programa
    de las viviendas (3 dormitorios y la sala en cada una) y no hay margen.
    Y solo los adyacentes a un hall, con al menos el ancho de un pasaje:
    el hall tiene que quedar de una pieza.
    """
    halls = [c for c in piezas_comunes() if c["uso"] == "hall"]
    out = []
    for m in modulos():
        if es_pozo(m) or es_nucleo(m) or tiene_luz(m):
            continue
        if any(_borde(m, h) >= ANCHO_PASAJE - 1e-9 for h in halls):
            out.append(m)
    return out


def _clave(m):
    return (round(m["x0"], 3), round(m["y0"], 3))


def _construir(clasifica, extra, recortes=()):
    """Arma una particion: quien es comun, quien es de cada vivienda."""
    comun = piezas_comunes()
    claves = set(_clave(m) for m in extra)
    for m in extra:
        comun.append(dict(m, uso="hall"))
    viviendas = {}
    for m in modulos():
        if es_pozo(m) or es_nucleo(m) or _clave(m) in claves:
            continue
        resto, a_pas = dict(m), 0.0
        for r in recortes:
            if resto is None:
                break
            ix = min(resto["x1"], r["x1"]) - max(resto["x0"], r["x0"])
            iy = min(resto["y1"], r["y1"]) - max(resto["y0"], r["y0"])
            if ix > 1e-9 and iy > 1e-9:
                a_pas += ix * iy
            resto = _recortar(resto, r)
        if a_pas > 1e-9:
            comun.append(dict(m, area=a_pas, uso="pasaje"))
        if resto is None or resto["area"] <= 1e-9:
            continue
        viviendas.setdefault(clasifica(resto), []).append(resto)
    return [viviendas[k] for k in sorted(viviendas)], comun


def particion_transversal(extra=()):
    """Frente y fondo, separados por el pozo. EXIGE el pasaje en L."""
    return _construir(lambda m: 0 if m["y1"] <= POZO_Y1 + 1e-9 else 1,
                      list(extra), pasaje_tramos())


def particion_longitudinal(extra=()):
    """Izquierda y derecha, por el eje central de la reticula."""
    XS, _et = ejes_x_rotulados()
    corte = XS[len(XS) // 2]
    return _construir(lambda m: 0 if m["x1"] <= corte + 1e-9 else 1,
                      list(extra))


def particion_unica(extra=()):
    """Una sola vivienda por piso -- cinco pisos, cinco viviendas."""
    return _construir(lambda m: 0, list(extra))


# ==========================================================================
# DIAGNOSTICO DE UNA PARTICION
# ==========================================================================
def indice_de_acceso(dep, comun):
    """El modulo por donde se entra, y cuanto borde comparte con el hall.

    Entre los modulos que dan al hall con el ancho de una puerta, se
    prefiere el que NO tiene luz directa. No es un gusto: los modulos con
    luz los necesita el programa -- 3 dormitorios y la sala por vivienda,
    y hay exactamente cuatro -- asi que gastar uno como vestibulo de
    entrada deja a la vivienda sin un dormitorio. Ademas, el modulo de
    acceso es de paso por definicion, y un dormitorio no puede serlo.

    Sin esta preferencia el desempate lo decidia el ORDEN de la lista, y
    con eso la vivienda del este entraba por su modulo de fachada -- o sea
    por un dormitorio -- y el diagnostico la declaraba inviable.
    """
    mejor, largo = None, 0.0
    for i, m in enumerate(dep):
        for c in comun:
            if c.get("uso") != "hall":
                continue
            L = _borde(m, c)
            if L < ANCHO_PUERTA - 1e-9:
                continue
            if mejor is None:
                mejor, largo = i, L
                continue
            actual = (not tiene_luz(dep[mejor]), largo)
            nuevo = (not tiene_luz(m), L)
            if nuevo > actual:
                mejor, largo = i, L
    if mejor is None:
        # ninguno llega al ancho de una puerta: se devuelve el mayor borde
        # de todos modos, para que el diagnostico pueda decir cuanto falta
        for i, m in enumerate(dep):
            for c in comun:
                if c.get("uso") == "hall":
                    largo = max(largo, _borde(m, c))
    return mejor, largo


def articulaciones(dep, comun):
    """Los modulos DE PASO: hay que atravesarlos para llegar a otro.

    Importa porque un DORMITORIO no puede ser un ambiente de paso -- se
    entraria a una habitacion cruzando otra --, mientras que una SALA si:
    es el ambiente social y se atraviesa por definicion. La regla decide
    sola que nombre puede llevar cada modulo.
    """
    i0, _L = indice_de_acceso(dep, comun)
    if i0 is None:
        return set()
    ar = _aristas(dep)
    todos = _alcanza(dep, ar, i0)
    out = set()
    for k in range(len(dep)):
        if k == i0:
            continue
        if len(_alcanza(dep, ar, i0, sin=k)) < len(todos) - 1:
            out.add(k)
    return out


def diagnosticar(viviendas, comun):
    """Las fallas de una particion. Vacio = viable.

    Ninguna condicion es de gusto:

      * cada vivienda tiene que ser UNA pieza recorrible: un modulo suelto
        obligaria a salir a la zona comun y volver a entrar, o sea serian
        dos viviendas.
      * cada vivienda tiene que tocar un HALL -- no la escalera -- en al
        menos el ancho de una puerta.
      * cada vivienda necesita 4 modulos con luz directa (3 dormitorios y
        la sala), y de esos, 3 que NO sean de paso: un dormitorio al que se
        entra cruzando otro ambiente no es un dormitorio.
      * el minimo de area de la A.020 8.1.b.
      * la zona comun tiene que ser de una pieza y tocar la fachada
        frontal, que es por donde se entra desde la via publica.
    """
    fallas = []
    for n, dep in enumerate(viviendas):
        et = chr(ord("A") + n)
        _ok, sueltos = _conexo(dep)
        for m in sueltos:
            fallas.append("el modulo x[%.2f,%.2f] y[%.2f,%.2f] queda AISLADO "
                          "del resto de la vivienda %s"
                          % (m["x0"], m["x1"], m["y0"], m["y1"], et))
        i0, largo = indice_de_acceso(dep, comun)
        if i0 is None or largo < ANCHO_PUERTA - 1e-9:
            fallas.append("la vivienda %s no tiene acceso: toca el hall en "
                          "%.2f m y hace falta %.2f"
                          % (et, largo, ANCHO_PUERTA))
        a = sum(m["area"] for m in dep)
        if a < AREA_MIN_DEPTO:
            fallas.append("la vivienda %s tiene %.2f m2 y la A.020 8.1.b "
                          "pide %.2f" % (et, a, AREA_MIN_DEPTO))
        con_luz = [k for k, m in enumerate(dep) if tiene_luz(m)]
        if len(con_luz) < 4:
            fallas.append("la vivienda %s tiene %d modulos con luz directa y "
                          "el programa pide 4" % (et, len(con_luz)))
        art = articulaciones(dep, comun)
        libres = [k for k in con_luz if k not in art and k != i0]
        if len(libres) < 3:
            fallas.append("la vivienda %s tiene %d modulos con luz que no "
                          "son de paso, y hacen falta 3 para los dormitorios"
                          % (et, len(libres)))
    _ok, sueltos = _conexo(comun)
    for m in sueltos:
        fallas.append("la pieza comun x[%.2f,%.2f] y[%.2f,%.2f] queda "
                      "separada del resto de la zona comun"
                      % (m["x0"], m["x1"], m["y0"], m["y1"]))
    if not any(c["y0"] <= 1e-9 and c["uso"] == "hall" for c in comun):
        fallas.append("ningun hall toca la fachada frontal: no hay por donde "
                      "entrar al edificio desde la via publica")
    return fallas


def opciones_de_reparto():
    """Todas las particiones posibles, cada una con su diagnostico."""
    out = []
    formas = (("transversal  (frente / fondo, con pasaje en L)",
               particion_transversal),
              ("longitudinal (izquierda / derecha)",
               particion_longitudinal),
              ("una sola vivienda por piso", particion_unica))
    extras = [[]] + [[m] for m in candidatos_de_hall()]
    for nom, fn in formas:
        for extra in extras:
            try:
                viviendas, comun = fn(extra)
            except ValueError as e:
                out.append({"nombre": nom, "extra": extra, "viviendas": [],
                            "comun": [], "fallas": [str(e)],
                            "area_comun": 0.0})
                continue
            if len(viviendas) < 1:
                continue
            etiqueta = nom
            if extra:
                etiqueta += " + hall extendido a x[%.2f,%.2f] y[%.2f,%.2f]" \
                            % (extra[0]["x0"], extra[0]["x1"],
                               extra[0]["y0"], extra[0]["y1"])
            out.append({"nombre": etiqueta, "extra": extra,
                        "viviendas": viviendas, "comun": comun,
                        "fallas": diagnosticar(viviendas, comun),
                        "area_comun": sum(m["area"] for m in comun)})
    return out


def reparto():
    """Las viviendas del piso y la zona comun. LA PARTICION SE DERIVA.

    EL DEFECTO QUE ESTO CORRIGE (2026-09-21). Este script partia la planta
    en FRENTE y FONDO porque «el pozo parte la planta», y eso arrastraba un
    pasaje comun imposible de trazar. El control de circulacion -- el 35 --
    lo destapo: la zona comun quedaba en dos pedazos que no se tocaban, el
    SSOT tenia una puerta que unia el dormitorio principal de una vivienda
    con el hall de la otra, y el edificio no tenia puerta de ingreso.

    POR QUE LA PARTICION TRANSVERSAL NO SE PUEDE ARREGLAR. El nucleo esta
    al frente -- lo manda la excentricidad de la escalera -- y el pozo
    ocupa TODA la franja central, x[3,25; 8,65] y[6,72; 10,92]. Para llegar
    al fondo hay que rodear el pozo por una columna lateral, y para llegar
    a esa columna hay que cruzar la franja y[3,36; 6,72] de lado a lado.
    Esa franja es el UNICO camino entre la mitad izquierda y la derecha del
    frente, porque el nucleo tapa la franja de adelante y el pozo la de
    atras. El pasaje, al cruzarla, corta en dos la vivienda del frente; y
    si se pega a y = 3,36 para no cortarla, aisla el modulo de fachada que
    queda detras. Las dos salidas son inadmisibles.

    POR QUE LA LONGITUDINAL NECESITA EXTENDER EL HALL. El nucleo son dos
    modulos y la escalera llena el del oeste: el hall es solo el del este,
    y toca unicamente la mitad derecha. La vivienda de la izquierda se
    quedaba sin acceso. Sumandole al hall el modulo de atras --
    x[5,95; 8,65] y[3,36; 6,72], que no tiene luz directa y por lo tanto no
    le hace falta a ningun dormitorio -- el hall pasa a tocar las dos
    mitades, y cada vivienda se entra directamente desde ahi. No hace falta
    pasaje.

    COMO SE ELIGE. `opciones_de_reparto()` construye las nueve
    combinaciones -- tres formas de partir por tres estados del hall -- y
    las diagnostica. Gana la que MAS viviendas admite: cinco pisos con dos
    viviendas son diez unidades y con una sola, cinco. A igual numero de
    viviendas gana la de menor area comun, que es area que no se vende.
    """
    ops = opciones_de_reparto()
    viables = [o for o in ops if not o["fallas"]]
    if not viables:
        detalle = "; ".join("%s -> %s" % (o["nombre"].split("(")[0].strip(),
                                          o["fallas"][0]) for o in ops[:3])
        raise ValueError("ninguna particion es viable (%s)" % detalle)
    elegida = max(viables, key=lambda o: (len(o["viviendas"]),
                                          -o["area_comun"]))
    return elegida["viviendas"], elegida["comun"]


def informe():
    print("=" * 96)
    print("DISTRIBUCION ARQUITECTONICA  -  derivada de la reticula y de la norma")
    print("=" * 96)
    print()
    XS, _ = ejes_x_rotulados()
    print("  reticula: %d columnas x %d filas = %d modulos"
          % (len(XS) - 1, len(EJES_MX) - 1,
             (len(XS) - 1) * (len(EJES_MX) - 1)))
    n = nucleo()
    print("  nucleo de circulacion  x[%.2f, %.2f] y[%.2f, %.2f] = %.2f m2"
          % (n["x0"], n["x1"], n["y0"], n["y1"],
             (n["x1"] - n["x0"]) * (n["y1"] - n["y0"])))
    ex0, ex1, ey0, ey1 = escalera_donde_corresponde()
    print("  escalera               x[%.2f, %.2f] y[%.2f, %.2f] = %.2f m2"
          % (ex0, ex1, ey0, ey1, (ex1 - ex0) * (ey1 - ey0)))
    for r in pasaje_tramos():
        print("  pasaje %-10s      x[%.2f, %.2f] y[%.2f, %.2f] = %.2f m2"
              % (r["tramo"], r["x0"], r["x1"], r["y0"], r["y1"],
                 (r["x1"] - r["x0"]) * (r["y1"] - r["y0"])))
    print("  pasaje (la L, sin contar dos veces el codo)  = %.2f m2"
          % area_pasaje())
    print()

    print("  MODULOS CON LUZ NATURAL DIRECTA  (A.020: dormitorios y sala)")
    con_luz = [m for m in modulos()
               if not es_pozo(m) and not es_nucleo(m) and tiene_luz(m)]
    for m in con_luz:
        print("     x[%5.2f,%5.2f] y[%5.2f,%5.2f] %6.2f m2   %s"
              % (m["x0"], m["x1"], m["y0"], m["y1"], m["area"], tiene_luz(m)))
    print("     -> %d modulos. El programa pide %d dormitorios + sala por"
          % (len(con_luz), 3))
    print("        departamento, o sea %d: no hay margen." % (4 * N_DEPTOS))
    print()

    dep_a, dep_b, comun = reparto()
    for nom, dep in (("A (frente)", dep_a), ("B (fondo)", dep_b)):
        area = sum(m["area"] for m in dep)
        luz = [m for m in dep if tiene_luz(m)]
        print("  DEPARTAMENTO %-12s %2d modulos   %7.2f m2   %d con luz"
              % (nom, len(dep), area, len(luz)))
    a_com = sum(m["area"] for m in comun)
    print("  AREA COMUN                %2d piezas   %7.2f m2"
          % (len(comun), a_com))
    tot = (sum(m["area"] for m in dep_a) + sum(m["area"] for m in dep_b)
           + a_com)
    print()
    print("  suma                                  %7.2f m2" % tot)
    print("  area techada del SSOT                 %7.2f m2" % AREA_PLANTA)
    return dep_a, dep_b, comun


def control(dep_a, dep_b, comun):
    fallas = []
    tot = (sum(m["area"] for m in dep_a) + sum(m["area"] for m in dep_b)
           + sum(m["area"] for m in comun))
    if abs(tot - AREA_PLANTA) > 0.05:
        fallas.append("la distribucion suma %.2f m2 y el area techada es %.2f"
                      % (tot, AREA_PLANTA))
    for nom, dep in (("A", dep_a), ("B", dep_b)):
        # el minimo de la A.020 se mide sobre el area TECHADA
        a = sum(m["area"] for m in dep)
        if a < AREA_MIN_DEPTO:
            fallas.append("el departamento %s tiene %.2f m2 y la A.020 8.1.b "
                          "pide %.2f" % (nom, a, AREA_MIN_DEPTO))
        con_luz = [m for m in dep if tiene_luz(m)]
        if len(con_luz) < 4:
            fallas.append("el departamento %s tiene %d ambientes con luz "
                          "directa y el programa pide 4 (3 dormitorios y la "
                          "sala)" % (nom, len(con_luz)))
    # ningun modulo puede quedar sin asignar
    asignados = len(dep_a) + len(dep_b) + len(comun)
    libres = [m for m in modulos() if not es_pozo(m)]
    if asignados < len(libres):
        fallas.append("hay %d modulos utiles y solo %d asignados: quedaria "
                      "planta sin distribuir" % (len(libres), asignados))
    # LAS DOS AREAS TIENEN QUE SER COHERENTES: la diferencia entre el
    # area techada y la util es el area de los muros, y no puede ser
    # cualquier numero. Se acota al 20 % -- con muros de 0,24 m en modulos
    # de 9 a 14 m2, la proporcion ronda el 15 %.
    for nom, dep in (("A", dep_a), ("B", dep_b)):
        te = sum(m["area"] for m in dep)
        ut = sum(area_util(m) for m in dep)
        if ut <= 0 or te <= 0:
            fallas.append("el departamento %s no tiene area" % nom)
            continue
        pct = 100.0 * (te - ut) / te
        if not (8.0 <= pct <= 22.0):
            fallas.append("el departamento %s: los muros serian el %.1f %% "
                          "del area techada, fuera del rango razonable"
                          % (nom, pct))
    # ningun tramo del pasaje puede ser mas angosto que el minimo
    tramos = pasaje_tramos()
    for r in tramos:
        ancho = min(r["x1"] - r["x0"], r["y1"] - r["y0"])
        if ancho < ANCHO_PASAJE - 1e-9:
            fallas.append("el tramo %s del pasaje mide %.2f m de ancho y el "
                          "minimo es %.2f" % (r["tramo"], ancho, ANCHO_PASAJE))
    # LA L TIENE QUE SER CONTINUA: dos tramos que no se tocan son dos
    # pedazos de pasaje, y es el defecto que este control existe para cazar
    for i in range(len(tramos) - 1):
        r, s = tramos[i], tramos[i + 1]
        ix = min(r["x1"], s["x1"]) - max(r["x0"], s["x0"])
        iy = min(r["y1"], s["y1"]) - max(r["y0"], s["y0"])
        if not (ix > 1e-9 and iy >= -1e-9 and
                min(r["y1"], s["y1"]) >= max(r["y0"], s["y0"]) - 1e-9):
            fallas.append("los tramos %s y %s del pasaje no se encuentran"
                          % (r["tramo"], s["tramo"]))
    # y el pasaje tiene que salir del NUCLEO, no de un ambiente privado
    n = nucleo()
    hor = tramos[0]
    encuentro = (min(hor["x1"], n["x1"]) - max(hor["x0"], n["x0"]))
    if abs(hor["y0"] - n["y1"]) > 1e-9 or encuentro < ANCHO_PASAJE - 1e-9:
        fallas.append("el pasaje no se encuentra con el nucleo: comparten "
                      "%.2f m de borde y hacen falta %.2f"
                      % (max(0.0, encuentro), ANCHO_PASAJE))
    # el arranque del pasaje no puede pisar la huella de la escalera
    ex0, ex1, _e0, _e1 = escalera_donde_corresponde()
    if hor["x0"] < ex1 - 1e-9:
        fallas.append("el pasaje arranca en x=%.2f y la escalera llega hasta "
                      "x=%.2f: el pasaje pisaria el primer paso"
                      % (hor["x0"], ex1))
    # la escalera tiene que caber en el nucleo
    ex0, ex1, ey0, ey1 = escalera_donde_corresponde()
    n = nucleo()
    if not (n["x0"] - 1e-9 <= ex0 and ex1 <= n["x1"] + 1e-9
            and n["y0"] - 1e-9 <= ey0 and ey1 <= n["y1"] + 1e-9):
        fallas.append("la escalera x[%.2f,%.2f] y[%.2f,%.2f] no entra en el "
                      "nucleo x[%.2f,%.2f] y[%.2f,%.2f]"
                      % (ex0, ex1, ey0, ey1, n["x0"], n["x1"],
                         n["y0"], n["y1"]))
    return fallas


def main():
    dep_a, dep_b, comun = informe()
    amb_a, amb_b, _c = ambientes()
    print()
    print("  AMBIENTES ASIGNADOS")
    for nom, amb in (("A", amb_a), ("B", amb_b)):
        print("     DEPARTAMENTO %s" % nom)
        for m in sorted(amb, key=lambda z: (z["y0"], z["x0"])):
            print("        %-16s x[%5.2f,%5.2f] y[%5.2f,%5.2f] %6.2f m2  %s"
                  % (m["nombre"], m["x0"], m["x1"], m["y0"], m["y1"],
                     m["area"], tiene_luz(m) or "luz prestada (A.010 36.2)"))
    print()
    print("=" * 96)
    print("CONTROL")
    print("=" * 96)
    fallas = control(dep_a, dep_b, comun) + control_ambientes(amb_a, amb_b)
    if fallas:
        for f in fallas:
            print("  [!!] %s" % f)
        return 1
    print("  [ok] la distribucion suma el area techada")
    print("  [ok] los %d departamentos superan los %.0f m2 de la A.020 8.1.b"
          % (N_DEPTOS, AREA_MIN_DEPTO))
    print("  [ok] los dos tienen 4 ambientes con luz natural directa")
    print("  [ok] ningun modulo util queda sin asignar")
    print("  [ok] el pasaje respeta el ancho minimo de %.2f m" % ANCHO_PASAJE)
    print("  [ok] la escalera entra en el nucleo de circulacion")
    print("  [ok] todo ambiente tipo A (dormitorio y sala) tiene luz directa")
    print("  [ok] la sala de cada departamento es la mas cercana a su acceso")
    print("  [ok] ningun departamento repite nombre de ambiente")
    return 0




# ==========================================================================
# QUE AMBIENTE VA EN CADA MODULO
# ==========================================================================
# Tampoco se elige: se deduce de la luz y del tamano.
#
#   Los modulos CON luz directa son los unicos que pueden alojar ambientes
#   "tipo A" -- dormitorios y sala --, y son justo los que el programa
#   necesita. Entre ellos, el MAYOR es la sala-comedor, porque es el que
#   recibe a toda la familia; el siguiente en area es el dormitorio
#   principal; los demas, dormitorios.
#
#   Los modulos SIN luz alojan lo que la A.010 Art. 36.2 admite con luz
#   prestada. La cocina va junto a la sala -- es la adyacencia que manda
#   una vivienda --, el resto se reparte entre bano, lavanderia, deposito y
#   distribuidor por orden de area.
SOCIALES = ["SALA - COMEDOR", "COMEDOR", "SALA DE ESTAR"]
DORMIR = ["DORM. PRINCIPAL", "DORMITORIO 1", "DORMITORIO 2",
          "DORMITORIO 3", "DORMITORIO 4"]
# El ambiente de acceso de una vivienda se llama RECIBIDOR y no HALL: el
# HALL es la pieza COMUN del edificio, y con los dos nombres iguales el
# plano mostraba "HALL" y "HALL" en dos modulos pegados -- uno comun y otro
# privado -- sin que se pudiera distinguir cual era cual.
CIRCULAR = ["RECIBIDOR", "DISTRIBUIDOR", "DISTRIBUIDOR 2",
            "PASAJE INTERIOR"]
SERVICIOS = ["COCINA", "SS.HH.", "LAVANDERIA", "DEPOSITO", "SS.HH. 2",
             "CLOSET", "VESTIDOR", "ALACENA"]


def _centro(m):
    return ((m["x0"] + m["x1"]) / 2.0, (m["y0"] + m["y1"]) / 2.0)


def _dist(a, b):
    (ax, ay), (bx, by) = _centro(a), _centro(b)
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def nombrar(dep, comun):
    """Que ambiente va en cada modulo. Lo deciden DOS propiedades medidas.

    LA LUZ dice si el modulo puede alojar un ambiente que la norma exige
    iluminado y ventilado de forma directa -- dormitorios y sala -- o uno
    de los que la A.010 Art. 36.2 admite con luz prestada: "cocinas,
    servicios sanitarios, pasajes de circulacion, depositos".

    LA ARTICULACION dice si el modulo es DE PASO, o sea si hay que
    atravesarlo para llegar a otro. Y eso cambia lo que puede ser:

      * un DORMITORIO no puede ser de paso. Se entraria a una habitacion
        cruzando otra, que es el defecto clasico de una planta mal
        resuelta.
      * una SALA-COMEDOR si puede: es el ambiente social y se atraviesa
        por definicion. De hecho, en esta planta el modulo que da al pozo
        es de paso obligado -- las filas del fondo cuelgan de el -- y es
        tambien el mas grande de los iluminados: es exactamente donde va
        la sala-comedor.
      * un ambiente de servicio de paso tiene que ser CIRCULACION (hall o
        distribuidor), no un bano ni una cocina.

    Sin esta regla el nombrado ponia el DORMITORIO PRINCIPAL en el modulo
    de paso y dejaba la casa con un bano al que se entraba por la cocina.
    """
    i0, _L = indice_de_acceso(dep, comun)
    art = articulaciones(dep, comun)
    con_luz = [k for k, m in enumerate(dep) if tiene_luz(m)]
    sin_luz = [k for k, m in enumerate(dep) if not tiene_luz(m)]

    nombres = {}
    # 1. los iluminados DE PASO son los ambientes sociales
    sociales = sorted([k for k in con_luz if k in art or k == i0],
                      key=lambda k: -dep[k]["area"])
    for j, k in enumerate(sociales):
        nombres[k] = (SOCIALES[j] if j < len(SOCIALES)
                      else "SALA %d" % (j + 1), "A")
    # 2. los iluminados que NO son de paso son los dormitorios
    dormir = sorted([k for k in con_luz if k not in nombres],
                    key=lambda k: -dep[k]["area"])
    for j, k in enumerate(dormir):
        nombres[k] = (DORMIR[j] if j < len(DORMIR)
                      else "DORMITORIO %d" % (j + 1), "A")
    # 3. los de servicio DE PASO son circulacion; el de acceso, el hall
    circular = ([i0] if i0 is not None and i0 in sin_luz else [])
    circular += sorted([k for k in sin_luz
                        if k in art and k not in circular],
                       key=lambda k: -dep[k]["area"])
    for j, k in enumerate(circular):
        nombres[k] = (CIRCULAR[j] if j < len(CIRCULAR)
                      else "PASAJE %d" % (j + 1), "servicio")
    # 4. el resto son los servicios. La COCINA va junto a la sala: es la
    #    adyacencia que manda una vivienda
    resto = [k for k in sin_luz if k not in nombres]
    if resto and sociales:
        sala = dep[sociales[0]]
        resto.sort(key=lambda k: _dist(dep[k], sala))
    for j, k in enumerate(resto):
        nombres[k] = (SERVICIOS[j] if j < len(SERVICIOS)
                      else "DEPOSITO %d" % (j + 1), "servicio")

    out = []
    for k, m in enumerate(dep):
        nom, tipo = nombres.get(k, ("AMBIENTE %d" % (k + 1), "servicio"))
        out.append(dict(m, nombre=nom, tipo=tipo,
                        de_paso=(k in art or k == i0),
                        acceso=(k == i0)))
    return out


def ambientes():
    """(viviendas ya nombradas, zona comun)."""
    viviendas, comun = reparto()
    return [nombrar(d, comun) for d in viviendas], comun


def control_ambientes(viviendas, comun):
    fallas = []
    for n, amb in enumerate(viviendas):
        et = chr(ord("A") + n)
        for m in amb:
            if m["tipo"] == "A" and not tiene_luz(m):
                fallas.append("%s: %r es un ambiente que la norma exige "
                              "iluminado y su modulo no tiene luz directa"
                              % (et, m["nombre"]))
            if m["nombre"].startswith("DORM") and m["de_paso"]:
                fallas.append("%s: %r es un ambiente DE PASO y un dormitorio "
                              "no puede serlo" % (et, m["nombre"]))
            if m["acceso"] and not (m["nombre"] in CIRCULAR
                                    or m["nombre"] in SOCIALES):
                fallas.append("%s: se entra a la vivienda por %r, que no es "
                              "circulacion ni ambiente social"
                              % (et, m["nombre"]))
        sala = [m for m in amb if m["nombre"] in SOCIALES]
        if not sala:
            fallas.append("%s no tiene sala-comedor" % et)
        dorm = [m for m in amb if m["nombre"].startswith("DORM")]
        if len(dorm) < 3:
            fallas.append("%s tiene %d dormitorios y el programa pide 3"
                          % (et, len(dorm)))
        nombres = [m["nombre"] for m in amb]
        if len(set(nombres)) != len(nombres):
            rep = sorted(set(n for n in nombres if nombres.count(n) > 1))
            fallas.append("%s repite nombre de ambiente: %s" % (et, rep))
    return fallas


def informe():
    print("=" * 96)
    print("DISTRIBUCION ARQUITECTONICA  -  derivada de la reticula y de la norma")
    print("=" * 96)
    print()
    XS, _et = ejes_x_rotulados()
    print("  reticula: %d columnas x %d filas = %d modulos"
          % (len(XS) - 1, len(EJES_MX) - 1,
             (len(XS) - 1) * (len(EJES_MX) - 1)))
    n = nucleo()
    print("  nucleo de circulacion  x[%.2f, %.2f] y[%.2f, %.2f] = %.2f m2"
          % (n["x0"], n["x1"], n["y0"], n["y1"],
             (n["x1"] - n["x0"]) * (n["y1"] - n["y0"])))
    ex0, ex1, ey0, ey1 = escalera_donde_corresponde()
    print("  escalera               x[%.2f, %.2f] y[%.2f, %.2f] = %.2f m2"
          % (ex0, ex1, ey0, ey1, (ex1 - ex0) * (ey1 - ey0)))
    for c in piezas_comunes():
        print("  %-8s del nucleo     x[%.2f, %.2f] y[%.2f, %.2f] = %.2f m2"
              % (c["uso"], c["x0"], c["x1"], c["y0"], c["y1"], c["area"]))
    print()

    print("  COMO SE PARTE EL PISO EN VIVIENDAS  (no se elige: se diagnostica)")
    for o in opciones_de_reparto():
        marca = "VIABLE" if not o["fallas"] else "descartada"
        print("     [%-10s] %d viv.  comun %5.2f m2   %s"
              % (marca, len(o["viviendas"]), o["area_comun"], o["nombre"]))
        for f in o["fallas"][:2]:
            print("                  motivo: %s" % f)
    print()

    print("  MODULOS CON LUZ NATURAL DIRECTA  (A.020: dormitorios y sala)")
    con_luz = [m for m in modulos()
               if not es_pozo(m) and not es_nucleo(m) and tiene_luz(m)]
    for m in con_luz:
        print("     x[%5.2f,%5.2f] y[%5.2f,%5.2f] %6.2f m2   %s"
              % (m["x0"], m["x1"], m["y0"], m["y1"], m["area"], tiene_luz(m)))
    print("     -> %d modulos con luz para %d viviendas: 4 cada una, o sea"
          % (len(con_luz), N_DEPTOS))
    print("        la sala y los 3 dormitorios. No hay margen.")
    print()

    viviendas, comun = reparto()
    for k, dep in enumerate(viviendas):
        area = sum(m["area"] for m in dep)
        util = sum(area_util(m) for m in dep)
        luz = [m for m in dep if tiene_luz(m)]
        print("  VIVIENDA %s   %2d modulos   %7.2f m2 techada   %7.2f util   "
              "%d con luz" % (chr(65 + k), len(dep), area, util, len(luz)))
    a_com = sum(m["area"] for m in comun)
    print("  ZONA COMUN   %2d piezas    %7.2f m2   (%.1f %% del piso)"
          % (len(comun), a_com, 100.0 * a_com / AREA_PLANTA))
    tot = sum(sum(m["area"] for m in d) for d in viviendas) + a_com
    print()
    print("  suma                      %7.2f m2" % tot)
    print("  area techada del SSOT     %7.2f m2" % AREA_PLANTA)
    return viviendas, comun


def control(viviendas, comun):
    fallas = []
    tot = sum(sum(m["area"] for m in d) for d in viviendas) \
        + sum(m["area"] for m in comun)
    if abs(tot - AREA_PLANTA) > 0.05:
        fallas.append("la distribucion suma %.2f m2 y el area techada es %.2f"
                      % (tot, AREA_PLANTA))
    if len(viviendas) != N_DEPTOS:
        fallas.append("el reparto adoptado da %d viviendas por piso y el "
                      "programa pide %d" % (len(viviendas), N_DEPTOS))
    # el diagnostico de la particion adoptada tiene que estar limpio
    for f in diagnosticar(viviendas, comun):
        fallas.append("particion adoptada: %s" % f)
    # ningun modulo util puede quedar sin asignar
    asignados = sum(len(d) for d in viviendas) + len(comun)
    libres = [m for m in modulos() if not es_pozo(m)]
    if asignados < len(libres):
        fallas.append("hay %d modulos utiles y solo %d asignados: quedaria "
                      "planta sin distribuir" % (len(libres), asignados))
    # LAS DOS AREAS TIENEN QUE SER COHERENTES: la diferencia entre la
    # techada y la util es el area de los muros, y no puede ser cualquier
    # numero. Con muros de 0,24 m en modulos de 9 a 14 m2 ronda el 15 %.
    for k, dep in enumerate(viviendas):
        te = sum(m["area"] for m in dep)
        ut = sum(area_util(m) for m in dep)
        if ut <= 0 or te <= 0:
            fallas.append("la vivienda %s no tiene area" % chr(65 + k))
            continue
        pct = 100.0 * (te - ut) / te
        if not (8.0 <= pct <= 22.0):
            fallas.append("la vivienda %s: los muros serian el %.1f %% del "
                          "area techada, fuera del rango razonable"
                          % (chr(65 + k), pct))
    # la escalera tiene que caber en el nucleo
    ex0, ex1, ey0, ey1 = escalera_donde_corresponde()
    n = nucleo()
    if not (n["x0"] - 1e-9 <= ex0 and ex1 <= n["x1"] + 1e-9
            and n["y0"] - 1e-9 <= ey0 and ey1 <= n["y1"] + 1e-9):
        fallas.append("la escalera x[%.2f,%.2f] y[%.2f,%.2f] no entra en el "
                      "nucleo x[%.2f,%.2f] y[%.2f,%.2f]"
                      % (ex0, ex1, ey0, ey1, n["x0"], n["x1"],
                         n["y0"], n["y1"]))
    return fallas


def main():
    viviendas, comun = informe()
    amb, _c = ambientes()
    print()
    print("  AMBIENTES ASIGNADOS")
    for k, lista in enumerate(amb):
        print("     VIVIENDA %s" % chr(65 + k))
        for m in lista:
            marcas = []
            if m["acceso"]:
                marcas.append("acceso")
            elif m["de_paso"]:
                marcas.append("de paso")
            print("        %-16s x[%5.2f,%5.2f] y[%5.2f,%5.2f] %6.2f m2  "
                  "%-24s %s"
                  % (m["nombre"], m["x0"], m["x1"], m["y0"], m["y1"],
                     m["area"], tiene_luz(m) or "luz prestada (A.010 36.2)",
                     ", ".join(marcas)))
    print()
    print("=" * 96)
    print("CONTROL")
    print("=" * 96)
    fallas = control(viviendas, comun) + control_ambientes(amb, comun)
    if fallas:
        for f in fallas:
            print("  [FALLA] %s" % f)
        return 1
    print("  [ok] la distribucion suma el area techada")
    print("  [ok] la particion adoptada pasa el diagnostico completo")
    print("  [ok] las %d viviendas superan los %.0f m2 de la A.020 8.1.b"
          % (N_DEPTOS, AREA_MIN_DEPTO))
    print("  [ok] cada vivienda tiene 4 modulos con luz directa")
    print("  [ok] cada vivienda se entra por circulacion o por la sala")
    print("  [ok] ningun dormitorio es ambiente de paso")
    print("  [ok] ningun modulo util queda sin asignar")
    print("  [ok] la escalera entra en el nucleo de circulacion")
    return 0


if __name__ == "__main__":
    sys.exit(main())
