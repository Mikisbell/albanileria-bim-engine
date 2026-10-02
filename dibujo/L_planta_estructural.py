# -*- coding: utf-8 -*-
"""Lámina E-01 — planta estructural típica.

CON EL MOTOR `lamina.py`, NO A MANO
===================================
Este archivo NO calcula coordenadas de hoja ni inventa un membrete. Declara
QUÉ se dibuja, en metros, y el motor se encarga de la escala, el cajetín, la
leyenda, el norte y la doble salida PNG + PDF + DXF.

Eso importa por una razón concreta: el rótulo «ESC. 1:75» del cajetín es
CIERTO, porque la transformación es literalmente `mm = x_m · 1000 / S`. Y el
DXF sale del mismo árbol de primitivas que el PNG, así que el plano en CAD y
la figura del informe no pueden decir cosas distintas.

QUÉ MUESTRA
===========
La retícula que el cálculo verificó: siete muros transversales, seis
longitudinales, sus columnas de confinamiento en cada extremo e
intersección, el pozo de luz y la caja de escalera. Con sus ejes, sus cotas
encadenadas y el cuadro de muros al costado.
"""
import os
import math
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "calculo"))

import paleta as PAL                                       # noqa: E402
from lamina import Lamina, A3_MM                                          # noqa: E402
from meta import meta


def _especificaciones():
    """Carga calculo/33_especificaciones_planos.py (empieza con digito)."""
    import importlib.util
    ruta = os.path.join(AQUI, "..", "calculo",
                        "33_especificaciones_planos.py")
    spec = importlib.util.spec_from_file_location("_esp33", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod                                              # noqa: E402
from proyecto import (FRENTE, FONDO, ESPESOR, EJES_MX, MUROS,      # noqa: E402
                      POZO_X0, POZO_X1, POZO_Y0, POZO_Y1,
                      ESC_X0, ESC_X1, ESC_Y0, ESC_Y1,
                      H_COLUMNA, H_COLUMNA_EXT, N_PISOS,
                      vanos_ubicados, AREA_PLANTA,
                      MUROS_CON_VENTANA, ALTO_PUERTA, tipo_de_vano,
                      ALTURA_VENTANA, machones,
                      LONG_MINIMA, SEPARACION_VANO_COLUMNA,
                      ejes_x_rotulados, FRENTE_LOTE,
                      RETIRO_LATERAL, Z, S, HN, ANCHO_VANO_VIVIENDA, FONDO_LOTE)

# EL TOPE DEL 7.2.1.b, NOMBRADO. Estaba escrito tres veces -- dos en la
# condicion y una en el mensaje-- y el mensaje podia dejar de decir lo
# que la condicion comprueba.
TOPE_TRAMO = 5.00   # m, E.070 7.2.1.b: centro a centro entre columnas

ESCALA = 100
COL_X = 248.0        # mm, columna de cuadros de la hoja
Y_LEYENDA = 288.0    # mm, tope de la columna de la hoja
SEP_BLOQUE = 8.0     # mm entre bloques de hoja
COTA_MURO = PAL.COTA   # cota de tramo: se distingue de la de eje      # a 1:75 la planta no entra en el A3: el
                  # propio motor lo denuncia con el numero


def ejes_x():
    """Los ejes verticales: los que ocupan los muros longitudinales."""
    return ejes_x_rotulados()


def ejes_y():
    """Los ejes horizontales: uno por muro transversal."""
    return list(EJES_MX), [str(k + 1) for k in range(len(EJES_MX))]


# EL LIMITE DE PROPIEDAD NO SE INVADE.
# El eje estructural de un muro PERIMETRAL no puede ir sobre el limite: si
# el muro se centra ahi, su paramento sobresale medio espesor y se mete
# 0,12 m en el predio del vecino por los laterales y 0,12 m en el retiro
# por el frente y el fondo. Materialmente no se puede construir.
#
# El criterio es: la CARA EXTERIOR del muro perimetral coincide con el
# limite, y su eje queda medio espesor hacia adentro. Los interiores si van
# centrados en su eje.
#
# El calculo no se toca: las longitudes son de borde a borde del edificio y
# el pano critico (4,20 m, el del pozo) es interior. Los panos extremos
# bajan de 3,36 a 3,24, que va del lado seguro.
LIMITES_X = (0.0, FRENTE)
LIMITES_Y = (0.0, FONDO)


def _hacia_adentro(v, limites, medio=None):
    """Corre el centro de una pieza para que NO pase del limite.

    `medio` es la mitad de la dimension de la pieza en ese sentido. Para un
    muro es medio espesor; para una columna puede ser mas, porque su
    peralte (0,30 m en la C-2) supera al espesor del muro y en las esquinas
    sobresale aunque el muro ya este encajado. El control lo caza: al
    corregir solo los muros quedaban 16 puntos de columna fuera, 3 cm.
    """
    e = ESPESOR / 2.0 if medio is None else medio
    if v - e < limites[0] - 1e-9:
        return limites[0] + e
    if v + e > limites[1] + 1e-9:
        return limites[1] - e
    return v


def _origen(nom, dire):
    """(x, y) del eje del muro, ya corrido si es perimetral."""
    if dire == "X":
        y = EJES_MX[int(nom.split("-")[1][0]) - 1]
        return 0.0, _hacia_adentro(y, LIMITES_Y)
    x = {"MY-1": 0.0, "MY-2": FRENTE,
         "MY-3": POZO_X0, "MY-4": POZO_X1}[nom[:4]]
    return _hacia_adentro(x, LIMITES_X), (POZO_Y1 if nom[4:5] == "b" else 0.0)


def es_ventana(nom, x0):
    """El tipo es POR VANO, no por muro.

    `MUROS_CON_VENTANA` declara el tipo del MURO, y con eso los cuatro
    vanos de la fachada frontal se dibujaban como ventanas: el plano
    mostraba un edificio sin puerta de ingreso. La excepcion la declara
    `PUERTA_INGRESO` en el SSOT y la resuelve `tipo_de_vano()`.
    """
    return tipo_de_vano(nom, x0) == "ventana"


def muros(L):
    """Cada muro con su espesor real, sus vanos abiertos y SU COLOR.

    EL MURO CON VENTANA VA EN OTRO TONO, y no es cosmetica: es el tema del
    informe. La longitud que cuenta para densidad (7.1.2.b) y para esfuerzo
    axial (7.1.1.b) es la NETA, y lo que la recorta son los vanos. MX-1 mide
    11,90 m y solo cuentan 6,15 -- el 52 % -- porque es fachada con
    ventanas; MY-1 mide 21,00 y cuentan los 21,00 porque es medianera ciega.
    Dibujar las dos igual obliga al lector a ir a la tabla para enterarse de
    la diferencia mas importante de la planta.

    Se usa el MISMO grafito dos tonos mas claro, no un color ajeno: sigue
    siendo muro portante y tiene que leerse como tal.
    """
    e = ESPESOR / 2.0
    n_tramos = 0
    con_ventana = []
    for nom, dire, largo, t, vanos in MUROS:
        puestos = vanos_ubicados(nom, dire, largo, vanos)
        # el color lo decide el SSOT, vano por vano, no una lista aparte
        tiene_ventana = any(tipo_de_vano(nom, x0) == "ventana"
                            for x0, _a in puestos)
        fc = PAL.MURO_VENTANA if tiene_ventana else PAL.MURO
        if tiene_ventana:
            con_ventana.append(nom.split()[0])
        # los tramos macizos que quedan entre vano y vano
        cortes = [0.0]
        for x0, ancho in sorted(puestos):
            cortes += [x0, x0 + ancho]
        cortes.append(largo)
        tramos = [(cortes[i], cortes[i + 1]) for i in range(0, len(cortes), 2)]
        ox, oy = _origen(nom, dire)
        if dire == "X":
            y = oy
            for a, b in tramos:
                if b - a > 1e-9:
                    L.rect(a, y - e, b, y + e, layer="MUROS", fc=fc)
                    n_tramos += 1
        else:
            x, y0 = ox, oy
            for a, b in tramos:
                if b - a > 1e-9:
                    L.rect(x - e, y0 + a, x + e, y0 + b, layer="MUROS",
                           fc=fc)
                    n_tramos += 1
    # CONTROL: los muros pintados como perforados tienen que ser EXACTAMENTE
    # los que el SSOT declara con ventana. Un color que no corresponde a un
    # dato es peor que no tener color: miente con autoridad de plano.
    esperados = sorted(m[0].split()[0] for m in MUROS
                       if any(tipo_de_vano(m[0], x0) == "ventana"
                              for x0, _a in vanos_ubicados(m[0], m[1], m[2],
                                                           m[4])))
    assert sorted(con_ventana) == esperados, (
        "los muros dibujados con ventana (%s) no son los que declara el SSOT "
        "(%s)" % (sorted(con_ventana), esperados))
    return n_tramos


def vanos(L):
    """Puertas con su hoja y su barrido; ventanas con su antepecho.

    Un vano dibujado como hueco blanco no dice nada. La puerta lleva hoja y
    arco -- que muestra hacia donde abre y si choca con algo -- y la ventana
    lleva las dos lineas de antepecho, que es como se distinguen en planta.
    """
    e = ESPESOR / 2.0
    n_p = n_v = 0
    for nom, dire, largo, t_, vs in MUROS:
        if not vs:
            continue
        ox, oy = _origen(nom, dire)
        for a, ancho in vanos_ubicados(nom, dire, largo, vs):
            vent = es_ventana(nom, a)
            if dire == "X":
                x0, x1, y0, y1 = ox + a, ox + a + ancho, oy - e, oy + e
            else:
                x0, x1, y0, y1 = ox - e, ox + e, oy + a, oy + a + ancho
            if vent:
                # ventana: el vano con sus dos lineas de antepecho
                L.rect(x0, y0, x1, y1, layer="VENTANA", fc=PAL.VENTANA)
                if dire == "X":
                    for yy in (y0 + e * 0.5, y1 - e * 0.5):
                        L.linea((x0, yy), (x1, yy), layer="VENTANA", lw=0.6)
                else:
                    for xx in (x0 + e * 0.5, x1 - e * 0.5):
                        L.linea((xx, y0), (xx, y1), layer="VENTANA", lw=0.6)
                n_v += 1
            else:
                # puerta: hoja abatida 90 grados y arco de barrido
                L.rect(x0, y0, x1, y1, layer="PUERTA", fc="white")
                # HACIA DONDE ABRE. Barriendo siempre al mismo lado, las
                # puertas de los muros del pozo abrian sobre el vacio. Se
                # abre hacia el lado que NO es pozo ni escalera.
                if dire == "X":
                    hacia = -1.0 if POZO_Y0 <= oy <= POZO_Y1 else 1.0
                    hacia = -1.0 if oy > FONDO / 2.0 else 1.0
                    L.rect(x0, y0, x0 + ESPESOR * 0.35,
                           y0 + hacia * ancho, layer="PUERTA", fc=PAL.PUERTA)
                    L.arco((x0, y0), ancho,
                           0.0 if hacia > 0 else 270.0,
                           90.0 if hacia > 0 else 360.0, layer="PUERTA")
                else:
                    hacia = -1.0 if ox > FRENTE / 2.0 else 1.0
                    L.rect(x0, y0, x0 + hacia * ancho,
                           y0 + ESPESOR * 0.35, layer="PUERTA", fc=PAL.PUERTA)
                    L.arco((x0, y0), ancho,
                           0.0 if hacia > 0 else 90.0,
                           90.0 if hacia > 0 else 180.0, layer="PUERTA")
                n_p += 1
    return n_p, n_v


def _clave(x, y):
    """Los cruces se identifican redondeados: los ejes de columna y los de
    muro difieren en medio espesor y no coinciden al centimetro."""
    return (round(x, 1), round(y, 1))


def _asignacion_por_cruce():
    """El tipo de cada cruce, calculado por el 39 sobre la malla real."""
    import contextlib
    import importlib.util
    import io as _io
    import os as _os
    ruta = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                         "..", "calculo", "39_columnas_en_planta.py")
    spec = importlib.util.spec_from_file_location("_m39", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
        m19 = m._mod("19_confinamientos.py")
        muros = m19.disenar()
        cuadro = m19.cuadro_de_columnas(muros)
        dis = {mu["nom"]: mu for mu in muros}
        tipos = {c["tipo"]: c["As_prov"] for c in cuadro if c.get("tipo")}
        puntos = m.malla(m.geometria_de_muros(), dis)
        c4 = m.tipo_c4(puntos, tipos)
    de_c4 = set(_clave(*p) for p in (c4["cruces"] if c4 else []))
    salida = {}
    for q in puntos:
        k = _clave(*q["p"])
        if k in de_c4:
            salida[k] = "C-4"
        elif q["hay_extrema"] and q["As_req"] > tipos.get("C-1", 0):
            salida[k] = "C-2"
        else:
            salida[k] = "C-1"
    return salida


def columnas(L):
    """El tipo de cada columna, por el 8.5.1.1 y no por su posicion.

    LA REGLA VIEJA ERA `extrema = j in (0, len(xs0)-1)`: la primera y la
    ultima columna de cada fila. Describe bien los extremos de los muros X
    --que van de fachada a fachada-- y es CIEGA a los muros Y cortos, cuyos
    extremos caen en posiciones INTERMEDIAS de esa fila. Ocho cruces que son
    extremos de MY-3a, MY-3b, MY-4a y MY-4b salian dibujados como C-1 cuando
    el 8.5.1.1 pide entre 10,20 y 12,37 cm2 y la C-1 da 7,74.

    El texto del informe decia bien la regla --"C-2 en los dos extremos de
    cada muro"-- y la traducia mal: "o sea todo el perimetro". El plano
    implemento la traduccion. Ahora la asignacion la resuelve el 39, que
    construye la malla y pregunta en cada cruce que muros concurren.

    En el cruce de los ejes YA CORRIDOS: una columna sobre el limite
    invadiria igual que el muro.
    """
    xs0, _ = ejes_x()
    asign = _asignacion_por_cruce()
    n_ext = n_int = n_c4 = 0
    for y0 in EJES_MX:
        for j, x0 in enumerate(xs0):
            tipo = asign.get(_clave(x0, y0), "C-1")
            extrema = tipo == "C-2"
            h = H_COLUMNA_EXT if extrema else H_COLUMNA
            # el PERALTE de la columna corre a lo largo del muro
            # transversal, que es el que la Tabla 11 gobierna; su ancho es
            # el espesor del muro. Y cada eje se encaja con la mitad que
            # de verdad ocupa la pieza en ese sentido.
            x = _hacia_adentro(x0, LIMITES_X, h / 2.0)
            y = _hacia_adentro(y0, LIMITES_Y, ESPESOR / 2.0)
            # a 1:100 una C-2 mide 2,4 x 3,0 mm en la hoja: sin borde
            # oscuro se pierde contra el muro y no se detecta al ojo
            L.rect(x - h / 2.0, y - ESPESOR / 2.0, x + h / 2.0,
                   y + ESPESOR / 2.0, layer="COLUMNAS", fc=PAL.COLUMNA,
                   ec=PAL.MURO_BORDE, lw=1.1, zorder=20)
            if tipo == "C-2":
                n_ext += 1
            elif tipo == "C-4":
                n_c4 += 1
            else:
                n_int += 1
    return n_ext, n_int, n_c4


def pozo_y_escalera(L):
    L.rect(POZO_X0, POZO_Y0, POZO_X1, POZO_Y1, layer="VACIO", fc="none",
           hatch="xx")
    # el rotulo iba sobre el rayado y no se leia: se saca a un costado,
    # con su linea de guia, que es como se anota un vacio en un plano
    cx, cy = (POZO_X0 + POZO_X1) / 2.0, (POZO_Y0 + POZO_Y1) / 2.0
    L.linea((cx, cy), (FRENTE + 1.6, cy + 1.2), layer="TEXTO", lw=0.35)
    L.texto((FRENTE + 1.7, cy + 1.45), "POZO DE LUZ", h_mm=2.6,
            layer="TEXTO", weight="bold", ha="left")
    L.texto((FRENTE + 1.7, cy + 0.75),
            "%.2f x %.2f m" % (POZO_X1 - POZO_X0, POZO_Y1 - POZO_Y0),
            h_mm=2.2, layer="TEXTO", ha="left")
    L.rect(ESC_X0, ESC_Y0, ESC_X1, ESC_Y1, layer="ESCALERA", fc=PAL.ESCALERA)
    L.texto(((ESC_X0 + ESC_X1) / 2.0, (ESC_Y0 + ESC_Y1) / 2.0), "ESCALERA",
            h_mm=2.4, layer="ESCALERA", weight="bold")


def _zonas_ocupadas():
    """Rectangulos del modelo donde un rotulo quedaria ilegible.

    El pozo y la escalera llevan trama; cada vano lleva su hoja de puerta y
    su barrido, que son las piezas que tapaban MY-3a y MY-4a.
    """
    z = [(POZO_X0, POZO_Y0, POZO_X1, POZO_Y1),
         (ESC_X0, ESC_Y0, ESC_X1, ESC_Y1)]
    for nom, dire, largo, _t, vs in MUROS:
        ox, oy = _origen(nom, dire)
        for x0, anc in vanos_ubicados(nom, dire, largo, vs):
            # el barrido de una puerta invade el ancho del vano hacia dentro
            r = anc
            if dire == "X":
                z.append((ox + x0 - 0.05, oy - r, ox + x0 + anc + 0.05, oy + r))
            else:
                z.append((ox - r, oy + x0 - 0.05, ox + r, oy + x0 + anc + 0.05))
    return z


# 10 mm de HOJA y no 5: la figura del informe comprime la geometria a la
# mitad y deja el texto en su cuerpo, asi que la separacion util alli es
# la mitad de la de la hoja. Pedir 10 deja 5 donde de verdad aprieta.
def _libre(L, p, zonas, ocupados_mm, sep_mm=10.0):
    """True si el punto no cae en zona ocupada del modelo ni a menos de
    `sep_mm` milimetros de HOJA de un texto ya puesto. Ver el porque arriba.
    """
    x, y = p
    for x0, y0, x1, y1 in zonas:
        if x0 - 0.05 <= x <= x1 + 0.05 and y0 - 0.05 <= y <= y1 + 0.05:
            return False
    hx, hy = L.T(p)
    for qx, qy in ocupados_mm:
        if abs(qx - hx) < sep_mm and abs(qy - hy) < sep_mm:
            return False
    return True


def _buscar(L, zonas, ocupados_mm, candidatos):
    """El primer candidato libre, aflojando la separacion por pasos.

    Devuelve (punto, separacion_conseguida). Ver el porque arriba.
    """
    for sep in (10.0, 8.0, 6.0, 4.5):
        for q in candidatos:
            if _libre(L, q, zonas, ocupados_mm, sep_mm=sep):
                return q, sep
    return None, 0.0


def rotulos_de_muro(L):
    """El nombre de cada muro, colocado donde no pise a otro.

    Los de X iban todos a la misma abscisa y los de Y a su punto medio:
    MX-2 (y = 3,36) caia exactamente sobre MY-3a, cuyo medio es tambien
    3,36. Los de X se llevan al tercio izquierdo y los de Y a un tercio de
    su largo, que son franjas que no se cruzan.
    """
    puestos = []
    zonas = _zonas_ocupadas()
    sep_min = 99.0
    # TODO texto ya dibujado, en milimetros de hoja: los del modelo (cotas
    # de tramo, llamados) y los de hoja (las cadenas de cota generales),
    # que en metros de modelo no se podian comparar.
    ocupados_mm = []
    for pr in L.prims:
        if pr.kind != "text":
            continue
        ocupados_mm.append(L.T(pr.pm[0]) if pr.pm else pr.ph[0])
    for nom, dire, largo, t_, vs in MUROS:
        corto = nom.split()[0]
        ox, oy = _origen(nom, dire)
        if dire == "X":
            # el rotulo iba ARRIBA del muro, que es donde ahora corre la
            # cadena de cotas de tramo: "MX-7" quedaba entre 1.70 y 1.20
            # LOS DE X TAMBIEN BUSCAN SITIO. Iban a una abscisa fija y
            # por eso MX-1 caia sobre la cota 3.25 del pie.
            p, sep = _buscar(
                L, zonas, ocupados_mm,
                # primero DENTRO de la planta; si no hay sitio, AFUERA por
                # la izquierda, alineado con su muro, que es donde un plano
                # pone el rotulo de un muro de fachada.
                [(FRENTE * f, oy + lado * ESPESOR * k)
                 for k in (1.6, 2.6, 3.8) for lado in (-1, +1)
                 for f in (0.17, 0.30, 0.45, 0.60, 0.75, 0.88, 0.06)]
                + [(-1.15, oy), (FRENTE + 1.15, oy)])
            assert p is not None, (
                "el rotulo de %s no encuentra sitio libre" % corto)
            sep_min = min(sep_min, sep)
            ocupados_mm.append(L.T(p))
            L.texto(p, corto, h_mm=3.0, layer="TEXTO", weight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#1e293b", lw=0.7))
        else:
            # 0,33 del largo caia dentro de la escalera y del pozo. Con
            # 0,12 mejora pero MY-3a sigue entrando en la escalera: el lado
            # se decide COMPROBANDO la geometria, no bajando el punto.
            # el 0,45 del largo cae sobre el borde del pozo en MY-3a y
            # MY-4a: se mide contra el pozo, no se elige a ojo
            # SE BUSCA UN SITIO LIBRE, no se elige uno y se parchea. Ver
            # el porque en _zonas_ocupadas().
            p, sep = _buscar(
                L, zonas, ocupados_mm,
                [(ox + lado * ESPESOR * k, oy + largo * f)
                 for k in (1.6, 2.6, 3.8) for lado in (+1, -1)
                 for f in (0.45, 0.30, 0.60, 0.18, 0.72, 0.08, 0.86)])
            assert p is not None, (
                "el rotulo de %s no encuentra un sitio libre: quedaria "
                "tapado, y un rotulo ilegible es un dato perdido" % corto)
            sep_min = min(sep_min, sep)
            ocupados_mm.append(L.T(p))
            L.texto(p, corto, h_mm=3.0, layer="TEXTO", rot=90, weight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#1e293b", lw=0.7))
        puestos.append((corto, p))
    # CONTROL: ningun par de rotulos puede quedar a menos de 0,55 m
    for i in range(len(puestos)):
        for j in range(i + 1, len(puestos)):
            (na, pa), (nb, pb) = puestos[i], puestos[j]
            d = ((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2) ** 0.5
            assert d > 0.55, (
                "los rotulos %s y %s quedan a %.2f m: se pisan" % (na, nb, d))
    print("  separacion minima conseguida entre rotulo y texto: %.1f mm"
          % sep_min)
    return len(puestos)


def cotas_de_muro(L):
    """Cadena de cotas por muro: machon, vano, machon... hasta cerrar en L.

    Los cortes salen de `machones()` y `vanos_ubicados()` del SSOT, que son
    las funciones que usa el calculo. Asi la cota del plano y el numero que
    entra en `Vm = 0,5 v'm alfa t Ln + 0,23 Pg` no pueden divergir.

    Los muros sin vano (las dos medianeras) no llevan cadena: su unica cota
    es el total, y esa ya la da la cadena de ejes. Repetirla seria ruido.
    """
    n_cadenas = n_cotas = 0
    dibujado = {}          # corto -> [(a, b, es_vano)] REALMENTE cotados
    for nom, dire, largo, t_, vs in MUROS:
        if not vs:
            continue
        corto = nom.split()[0]
        ox, oy = _origen(corto, dire)
        # los cortes: 0, cada borde de vano, y L
        cortes = [0.0]
        for a, ancho in vanos_ubicados(corto, dire, largo, vs):
            cortes += [a, a + ancho]
        cortes.append(largo)
        cortes = sorted(set(round(c, 4) for c in cortes))

        vanos_set = {(round(a, 4), round(a + w, 4))
                     for a, w in vanos_ubicados(corto, dire, largo, vs)}
        # un tramo menor que la media columna no es albanileria: el SSOT lo
        # descarta del machon y acá se cota igual, porque la cadena tiene
        # que CERRAR en L para que sirva de replanteo
        # La cadena va del lado del muro donde NO hay pozo: sobre MX-3 y
        # MX-4, que bordean el vacio, el numero caia sobre el hachurado y
        # no se leia. Se elige el lado mirando la geometria, no a ojo.
        off = 4.2 if dire == "X" else 7.0
        if dire == "X" and POZO_Y0 - 1e-9 <= oy <= POZO_Y1 + 1e-9:
            off = -4.2 if abs(oy - POZO_Y0) < 1e-9 else 4.2
        elif dire == "Y":
            # Para muros en Y, si están en el eje del pozo o derecho, cotamos hacia la izquierda
            # para no chocar con las cotas horizontales de los dormitorios
            if abs(ox - POZO_X0) < 0.3:
                off = -7.0
            elif abs(ox - POZO_X1) < 0.3 or abs(ox - 8.65) < 0.3:
                off = -7.0
            else:
                off = 7.0
        for k in range(len(cortes) - 1):
            a, b = cortes[k], cortes[k + 1]
            d = b - a
            es_vano = (a, b) in vanos_set
            if d < 0.10:
                continue                      # no entra el numero; se omite
            dibujado.setdefault(corto, []).append((a, b, es_vano))
            txt = "%.2f" % d
            # Un tramo corto no tiene ancho para su numero: a 1:100, 0,15 m
            # son 1,5 mm y el texto mide 8. Se ESCALONA a una segunda linea,
            # que es como un plano resuelve una cota que no entra, en vez de
            # dejarla encimada con la vecina.
            # Escalonamiento progresivo: tramos muy cortos (<0.30 m) necesitan más despeje
            # para no quedar encima del dibujo de esquinas o columnas concurrentes
            if d < 0.25:
                extra = 7.5
            elif d < 0.60:
                extra = 3.2
            else:
                extra = 0.0
            o = off + (extra * (1 if off > 0 else -1))
            # Correr la cota en X no sirve: la cadena del muro X recorre
            # TODO el ancho, asi que el cruce se repite mas alla. Lo que hay
            # que mover es el texto A LO LARGO del tramo, que es el unico
            # grado de libertad que de verdad lo saca de la banda.
            pos = 0.5
            if dire == "Y":
                ym = oy + (a + b) / 2.0
                # Si el tramo corto (machón extremo de 0.15 m) cae dentro del espesor
                # del muro transversal en EJES_MX, corremos su texto a lo largo hacia
                # el vano adyacente para sacarlo de la franja del muro
                if d < 0.25 and any(abs(ym - ye) < 0.25 for ye in EJES_MX):
                    pos = 1.8
                else:
                    for ye in EJES_MX:
                        ye2 = (ESPESOR / 2.0 if ye == 0.0
                               else (FONDO - ESPESOR / 2.0 if ye == FONDO else ye))
                        if ye2 + 0.25 <= ym <= ye2 + 0.85:
                            pos = 0.78 if (b - a) > 0.7 else 0.5
                            break
            col = "#8d6e3a" if es_vano else COTA_MURO
            if dire == "X":
                L.cota((ox + a, oy), (ox + b, oy), txt=txt, off_mm=o,
                       h_mm=1.6, color=col, pos_txt=pos)
            else:
                L.cota((ox, oy + a), (ox, oy + b), txt=txt, off_mm=o,
                       vert=True, h_mm=1.6, color=col, pos_txt=pos)
            n_cotas += 1
        n_cadenas += 1
    return n_cadenas, n_cotas, dibujado


def especificaciones(L, y):
    """E.060 1.2.2.4: lo que un plano de estructuras DEBE decir.

    El acapite no lo deja a criterio del proyectista, lo enumera. Este plano
    cubria (a), (c), (d) y (e); faltaban (b) cargas, (f) anclajes y
    empalmes, (g) juntas de separacion y (h) caracteristicas de la
    albanileria y el mortero. Las cuatro se agregan acá, derivadas del SSOT.
    """
    esp = _especificaciones()

    # --- (b) cargas de diseno
    y = L.cuadro(
        x_mm=COL_X, y_mm=y,
        titulo="(b)  CARGAS DE DISENO      E.020",
        encabezado=["CONCEPTO", "kgf/m2", "TIPO"],
        filas=[[n, "%.0f" % v, t_.upper()[:1]] for n, v, t_ in esp.cargas()],
        anchos_mm=[48.0, 14.0, 10.0], h_fila=4.4, h_txt=1.85,
    )

    # --- (c) (d) (h) materiales
    y = L.cuadro(
        x_mm=COL_X, y_mm=y - SEP_BLOQUE,
        titulo="(c)(d)(h)  MATERIALES      E.070 / E.060",
        encabezado=["CONCEPTO", "ESPECIFICACION"],
        filas=[[n, v] for n, v in esp.materiales()],
        anchos_mm=[40.0, 32.0], h_fila=4.4, h_txt=1.75,
    )

    # --- (f) anclajes y empalmes
    # AGRUPADAS POR DIAMETRO: el anclaje depende de la barra, no del
    # elemento. Con una fila por elemento, la C-4 (quinta fila, 2026-09-30)
    # empujaba el detalle (g) contra el pie de la hoja; y la C-3 y la C-4
    # repetian la misma fila de 5/8".
    grupos = []
    for tipo, diam, n_, tr, em, lg in esp.anclajes_y_empalmes():
        clave = (diam, round(tr), round(em), round(lg))
        for g in grupos:
            if g[0] == clave:
                g[1].append(tipo)
                break
        else:
            grupos.append((clave, [tipo]))
    filas = [[", ".join(tipos), d, "%.0f" % tr, "%.0f" % em, "%.0f" % lg]
             for (d, tr, em, lg), tipos in grupos]
    y = L.cuadro(
        x_mm=COL_X, y_mm=y - SEP_BLOQUE,
        titulo="(f)  ANCLAJES Y EMPALMES (cm)      E.070 4.3",
        encabezado=["ELEMENTOS", "BARRA", "45db", "60db", "ldh"],
        filas=filas,
        anchos_mm=[20.0, 13.0, 13.0, 13.0, 13.0], h_fila=4.4, h_txt=1.85,
        nota="Traslape 45 db (4.3.1) y empalme vertical 60 db (4.3.2). "
             "PROHIBIDO empalmar el refuerzo vertical en el primer "
             "entrepiso ni en las zonas confinadas de extremos de soleras "
             "y columnas. Conexion columna-albanileria (4.2.2): dentada con "
             "diente no mayor que %.0f cm, o a ras con chicotes de %.0f mm "
             "que penetren %.0f cm en la albanileria y %.1f cm en la "
             "columna mas doblez de %.0f cm."
             % (esp.DIENTE_MAX, esp.CHICOTE_DIAM * 10, esp.CHICOTE_ALB,
                esp.CHICOTE_COL, esp.CHICOTE_DOBLEZ),
    )
    return y


def limite_de_propiedad(L):
    """El limite del lote y la junta sismica lateral, acotada.

    E.060 1.2.2.4 (g) pide "ubicacion y DETALLADO" de las juntas de
    separacion con edificaciones vecinas: una nota al pie las declara,
    pero no las ubica. La exige la E.030-2026 Art. 52.3; hasta el
    2026-09-21 no existia y el paramento apoyaba sobre el limite.
    """
    r = RETIRO_LATERAL
    x0, x1 = -r, FRENTE + r          # los 12,00 m del lote
    for x in (x0, x1):
        L.linea((x, -1.2), (x, FONDO + 1.2), layer="EJES",
                color=PAL.LIMITE, lw=1.0, ls=(0, (12, 3, 2, 3)))
    for x, lado in ((x0 - 0.42, "izq"), (x1 + 0.42, "der")):
        L.texto((x, FONDO * 0.42), "LIMITE DE PROPIEDAD", h_mm=1.9,
                layer="TEXTO", rot=90, color=PAL.LIMITE)
    for xa, xb in ((x0, 0.0), (FRENTE, x1)):
        L.cota((xa, FONDO * 0.80), (xb, FONDO * 0.80), txt="",
               off_mm=7.0, h_mm=1.7, color=PAL.LIMITE)
    # EL LOTE, EN UN RENGLON. Como cota no entra -- el control de la lamina
    # lo freno: pedia 3,3 m de dibujo por debajo de las burbujas de eje y la
    # A3 no los tiene --. Y lo que el lector necesita no es una segunda
    # linea de cota sino saber que el 11,90 es lo EDIFICADO y donde estan
    # los 10 cm que faltan para el lote.
    assert abs(FRENTE + 2 * r - FRENTE_LOTE) < 1e-9, (
        "la cota afirma que %.2f + 2 x %.2f cierra en %.2f y no cierra"
        % (FRENTE, r, FRENTE_LOTE))
    # el rotulo de la junta vive en el DETALLE ampliado, no aca: a
    # FONDO + 2,1 caia sobre las burbujas de los ejes B, C y D


def detalle_junta(L, x_mm, y_mm, esc=20.0):
    """La junta a escala 1:20, donde SI se lee.

    Era 1:10, con la banda de 14 mm fijos: el muro de 0,24 m se dibujaba
    mas ancho que la C-2 del mismo espesor. Con la banda a escala real, a
    1:10 el detalle no entra sobre el pie de la hoja; 1:20 es una escala
    normalizada y la junta de 5 cm (2,5 mm) la lleva su cota.

    A 1:100 una junta de 5 cm son 0,5 mm de hoja: esta dibujada y no
    se ve. La E.060 1.2.2.4 (g) pide "ubicacion y DETALLADO", y el
    detallado es esto. Se dibuja en coordenadas de HOJA porque no
    pertenece a la planta: es un corte a otra escala.
    """
    def mm(v_m):
        return v_m * 1000.0 / esc

    r = RETIRO_LATERAL
    W = 72.0
    x_lim = x_mm + 8.0                 # el limite de propiedad
    x_par = x_lim + mm(r)              # la cara del muro
    # LA BANDA MIDE EL ESPESOR REAL DEL MURO. Medía 14 mm fijos --0,14 m a
    # 1:10-- y la C-2, que tiene el mismo ancho que el muro, salía más angosta
    # que él: el muro de 24 mm sobresalía 5 mm por lado, tapaba el renglón del
    # artículo y escondía su propio rótulo.
    y1 = y_mm - 10.5
    y0 = y1 - mm(ESPESOR)

    L.h_texto((x_mm, y_mm - 2.0),
              "(g)  DETALLE DE JUNTA SISMICA   esc. 1:%.0f" % esc,
              h_mm=2.4, ha="left", va="top", weight="bold")

    # el terreno del vecino, rayado
    L.h_rect(x_mm + 1.0, y0, x_lim, y1, layer="CAJETIN",
             fc="#f0e6f5", ec="#b9a3c4", lw=0.4)
    L.h_texto(((x_mm + 1.0 + x_lim) / 2.0, (y0 + y1) / 2.0), "LOTE",
              h_mm=1.7, ha="center", va="center", color=PAL.LIMITE)
    L.h_texto(((x_mm + 1.0 + x_lim) / 2.0, (y0 + y1) / 2.0 - 3.2),
              "VECINO", h_mm=1.7, ha="center", va="center",
              color=PAL.LIMITE)

    # la linea de propiedad
    L.h_linea((x_lim, y0 - 3.0), (x_lim, y1 + 3.0), layer="CAJETIN",
              color=PAL.LIMITE, lw=1.2, ls=(0, (7, 2, 1.5, 2)))

    # la columna C-2 y el muro, con su espesor real a esta escala
    L.h_rect(x_par, y0, x_par + mm(H_COLUMNA_EXT), y1,
             layer="CAJETIN", fc=PAL.COLUMNA, ec=PAL.MURO_BORDE, lw=0.8)
    L.h_texto((x_par + mm(H_COLUMNA_EXT) / 2.0, (y0 + y1) / 2.0),
              "C-2", h_mm=1.8, ha="center", va="center", color="white",
              weight="bold")
    L.h_rect(x_par + mm(H_COLUMNA_EXT), y0,
             x_mm + W - 1.0, y1,
             layer="CAJETIN", fc=PAL.MURO, ec=PAL.MURO_BORDE, lw=0.6)
    L.h_texto((x_par + mm(H_COLUMNA_EXT) + 9.0, (y0 + y1) / 2.0),
              "MURO t = %.2f m" % ESPESOR, h_mm=1.6, ha="left",
              va="center", color="white")

    # la cota de la junta: a 1:20 mide 2,5 mm y la cota la hace legible
    L.h_linea((x_lim, y1 + 1.5), (x_par, y1 + 1.5), layer="CAJETIN",
              color=PAL.LIMITE, lw=0.8)
    for x in (x_lim, x_par):
        L.h_linea((x, y1 + 0.6), (x, y1 + 2.4), layer="CAJETIN",
                  color=PAL.LIMITE, lw=0.8)
    L.h_texto(((x_lim + x_par) / 2.0, y1 + 3.0), "%.0f" % (r * 100),
              h_mm=2.0, ha="center", va="bottom", color=PAL.LIMITE,
              weight="bold")
    L.h_texto((x_par + 3.0, y1 + 3.0), "cm de junta", h_mm=1.7,
              ha="left", va="bottom", color=PAL.LIMITE)

    _s = max(0.02 * Z * S * HN, 0.03)
    L.h_texto((x_mm, y0 - 3.0),
              "s = 0,02 Z S h = %.1f cm  ->  s/2 = %.1f cm  (Art. 52.2 y 52.3)"
              % (_s * 100, _s * 50), h_mm=1.75, ha="left", va="top")
    L.h_texto((x_mm, y0 - 5.8),
              "Se adopta 5 cm. La junta queda LIBRE de todo material en toda"
              , h_mm=1.75, ha="left", va="top")
    L.h_texto((x_mm, y0 - 8.6),
              "la altura, desde el nivel del terreno natural (Art. 52.1)."
              , h_mm=1.75, ha="left", va="top")
    L._cajas_hoja.append(("(g) DETALLE JUNTA", x_mm, y0 - 10.4,
                          x_mm + W, y_mm))
    return y0 - 10.4


def construir():
    L = Lamina(
        codigo="E-01",
        titulo="PLANTA ESTRUCTURAL TIPICA",
        subtitulo=("Reticula de muros portantes, columnas de confinamiento, "
                   "pozo de luz y caja de escalera. Pisos 1 a %d."
                   % N_PISOS),
        escala=ESCALA,
        meta=meta(),
        nota_pie="Generado desde calculo/proyecto.py",
    )
    gx, etx = ejes_x()
    gy, ety = ejes_y()
    # encuadre: la planta mas el aire de los ejes y las cotas
    L.encuadrar(-3.8, FRENTE + 3.4, -3.2, FONDO + 3.4,
                centro_mm=(118.0, 148.0))

    L.ejes(gx, gy, etx, ety, ext_mm=25.0)
    n_tramos = muros(L)
    n_p, n_v = vanos(L)
    n_ext, n_int, n_c4 = columnas(L)
    pozo_y_escalera(L)
    limite_de_propiedad(L)

    # cotas encadenadas en las dos direcciones (jerarquizadas sin solape con burbujas)
    L.cadena_cotas(gx, 0.0, off_mm=-10.0, rotulo_total=None)
    L.cadena_cotas(gy, 0.0, off_mm=-12.0, vert=True, sep_mm=6.5,
                   rotulo_total=None)

    # y la cota de CADA muro, tramo a tramo, con los numeros del calculo
    n_cad, n_cot, cotado = cotas_de_muro(L)

    # LOS ROTULOS, AL FINAL: son los que esquivan (ver rotulos_de_muro).
    n_rot = rotulos_de_muro(L)

    L.leyenda_add(PAL.MURO, "MUROS", "Muro portante ciego t = %.2f m"
                  % ESPESOR)
    L.leyenda_add(PAL.MURO_VENTANA, "MUROS",
                  "Muro portante con ventana (menor longitud neta)")
    L.leyenda_add("#b02a1f", "COLUMNAS",
                  "Columna de confinamiento (C-1 / C-2)")
    L.leyenda_add(PAL.PUERTA, "PUERTA", "Puerta %.2f m (con barrido)" % ANCHO_VANO_VIVIENDA)
    L.leyenda_add(PAL.VENTANA, "VENTANA", "Ventana de fachada")
    L.leyenda_add(PAL.ESCALERA, "ESCALERA", "Caja de escalera")
    L.leyenda_add("linea", "VACIO", "Pozo de luz (vacio)")
    L.leyenda_add("trazos", "EJES", "Eje estructural")
    L.leyenda_add("linea", "COTAS", "Cota (m)")
    # a x=12 tapaba la burbuja del eje A-7: va a la franja libre
    L.leyenda_dibujar(x_mm=COL_X, y_mm=Y_LEYENDA, ancho_mm=72.0)

    L.norte(x_mm=222.0, y_mm=252.0)
    L.escala_grafica(x_mm=12.0, y_mm=20.0, metros=5)

    L.cajetin()

    # El tope de la pila se DERIVA del pie de la leyenda. Estaba escrito a
    # mano (262 mm) y la leyenda bajaba hasta 235: 30,5 mm de solape, con
    # todos los guardianes en verde porque ninguno miraba la hoja.
    y_col = L.cuadro(
        x_mm=COL_X, y_mm=L._caja_leyenda[1] - SEP_BLOQUE,
        titulo="RESUMEN DE LA RETICULA",
        encabezado=["CONCEPTO", "VALOR"],
        filas=[
            ["Muros transversales (X)", str(len([m for m in MUROS if m[1] == "X"]))],
            ["Muros longitudinales (Y)", str(len([m for m in MUROS if m[1] == "Y"]))],
            ["Columnas C-2 extremas", str(n_ext)],
            ["Columnas C-1 interiores", str(n_int)],
            ["Puertas por piso", str(n_p)],
            ["Ventanas por piso", str(n_v)],
            ["Espesor de muro", "%.2f m" % ESPESOR],
            ["Area techada por piso", "%.2f m2" % AREA_PLANTA],
        ],
        anchos_mm=[46.0, 26.0], h_fila=4.4, h_txt=1.85,
        nota="La reticula la fija la densidad minima del 7.1.2.b, no el "
             "reves: por eso son siete muros en X y no seis.",
    )

    y_col = especificaciones(L, y_col - SEP_BLOQUE)

    # --- (g) juntas de separacion con edificaciones vecinas
    # Ya no es un parrafo: es un DETALLE a escala, que es lo que el
    # acapite llama "detallado".
    # El hueco se MIDE, no se adivina: bajo el ultimo cuadro de la
    # columna quedan 72 x 48 mm libres y el detalle mide 72 x 35. La
    # primera version fue a parar encima de la planta.
    # 2026-09-30: DERIVADO del pie de (f). El 52 mm estaba medido con cuatro
    # filas de anclajes; al entrar la C-4 (quinta fila) el hueco se achico y
    # (g) quedo 1,9 mm debajo de (f). Un hueco medido a mano envejece igual
    # que un numero tecleado. El control de la hoja dice si todavia entra.
    detalle_junta(L, COL_X, y_col - (SEP_BLOQUE - 1.0))

    return L, n_tramos, n_ext, n_int, n_c4, n_p, n_v, n_cad, n_cot, cotado


def _extremos_compartidos():
    """Cuantos extremos de muro caen en el MISMO cruce que otro.

    Los 13 muros aportan 26 extremos, pero varios coinciden: la esquina del
    edificio es extremo de una fachada Y de una medianera a la vez. Se cuenta
    la diferencia para que el control compare manzanas con manzanas.
    """
    import contextlib
    import importlib.util
    import io as _io
    import os as _os
    ruta = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                         "..", "calculo", "39_columnas_en_planta.py")
    spec = importlib.util.spec_from_file_location("_x39", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
        m19 = m._mod("19_confinamientos.py")
        muros = m19.disenar()
        dis = {mu["nom"]: mu for mu in muros}
        puntos = m.malla(m.geometria_de_muros(), dis)
    con_extrema = sum(1 for q in puntos if q["hay_extrema"])
    return 2 * len(MUROS) - con_extrema


def control(L, n_tramos, n_ext, n_int, n_c4, n_p, n_v, n_cad, n_cot,
            cotado):
    """Que la lamina dibuje la reticula que el SSOT declara.

    Y que NADA se salga del limite de propiedad: es el control que faltaba.
    Lo encontro Mikis mirando el dibujo -- "eso invade la calle e incluso la
    propiedad del vecino" -- y tenia razon: con los muros perimetrales
    centrados en el limite, el paramento sobresalia 0,12 m por los cuatro
    lados. No es un defecto de dibujo: es un edificio que no se puede
    construir.
    """
    fuera = []
    for pr in L.prims:
        if pr.pm is None or pr.layer in ("EJES", "COTAS", "TEXTO", "CAJETIN"):
            continue
        # un ARCO guarda solo su centro: si se mide ese punto, el control
        # da verde aunque el barrido de la puerta salga a la calle. Se
        # muestrea el arco de verdad.
        if pr.kind == "arc":
            cx, cy = pr.pm[0]
            r = pr.opts["r"]
            a0, a1 = pr.opts["a0"], pr.opts["a1"]
            pasos = [a0 + (a1 - a0) * k / 12.0 for k in range(13)]
            puntos = [(cx + r * math.cos(math.radians(a)),
                       cy + r * math.sin(math.radians(a))) for a in pasos]
        else:
            puntos = pr.pm
        for (px, py) in puntos:
            # el limite es el del LOTE; el edificio va retirado de el
            if (px < -RETIRO_LATERAL - 1e-6
                    or px > FRENTE + RETIRO_LATERAL + 1e-6
                    or py < -1e-6 or py > FONDO + 1e-6):
                fuera.append((pr.layer, round(px, 3), round(py, 3)))
    assert not fuera, (
        "hay %d punto(s) FUERA del limite de propiedad (%.2f x %.2f): el "
        "muro invadiria al vecino o el retiro. Primeros: %s"
        % (len(fuera), FRENTE, FONDO, fuera[:4]))
    print("  [ok] nada se sale del limite de propiedad %.2f x %.2f m"
          % (FRENTE_LOTE, FONDO))

    # Y QUE LA JUNTA EXISTA DE VERDAD. El control anterior solo miraba
    # que nada se saliera; con el edificio APOYADO sobre el limite
    # tambien daba verde, porque tocar no es salirse. El Art. 52.3 pide
    # SEPARACION, asi que hay que medir la separacion.
    xs_mod = [px for pr in L.prims if pr.pm is not None
              and pr.layer in ("MUROS", "COLUMNAS")
              for (px, _py) in pr.pm]
    izq = min(xs_mod) + RETIRO_LATERAL
    der = (FRENTE + RETIRO_LATERAL) - max(xs_mod)
    s_min = max(0.02 * Z * S * HN, 0.03) / 2.0
    for lado, v in (("izquierdo", izq), ("derecho", der)):
        assert v >= s_min - 1e-6, (
            "E.030-2026 Art. 52.3: el lado %s deja %.1f cm de junta y "
            "el minimo s/2 es %.1f cm" % (lado, v * 100, s_min * 100))
    print("  [ok] junta sismica %.1f cm por lado (s/2 minimo %.1f cm)"
          % (izq * 100, s_min * 100))
    # El 4 estaba escrito a mano y valia mientras los ejes longitudinales
    # fueran cuatro. El eje 6,00 -- que la E.070 7.2.1.b obliga a agregar
    # porque el tramo del pozo mide 5,40 m > 5,00 -- NO es un cruce de
    # muros, asi que contar "cruces" lo dejaba afuera. Se cuenta contra el
    # SSOT: un eje longitudinal por cada muro transversal.
    esperados = len(EJES_MX) * len(ejes_x_rotulados()[0])
    assert n_ext + n_int + n_c4 == esperados, (
        "se dibujaron %d columnas y el SSOT declara %d"
        % (n_ext + n_int + n_c4, esperados))

    # y la separacion entre columnas, que es la razon de ser del eje 6,00
    xs_ssot = ejes_x_rotulados()[0]
    for a, b in zip(xs_ssot[:-1], xs_ssot[1:]):
        assert b - a <= TOPE_TRAMO + 1e-9, (
            "E.070 7.2.1.b: el tramo %.2f-%.2f mide %.2f m y el tope es "
            "%.2f m (centro a centro entre columnas)"
            % (a, b, b - a, TOPE_TRAMO))
    for a, b in zip(EJES_MX[:-1], EJES_MX[1:]):
        assert b - a <= TOPE_TRAMO + 1e-9, (
            "E.070 7.2.1.b: el tramo transversal %.2f-%.2f mide %.2f m"
            % (a, b, b - a))
    # ESTE CONTROL CODIFICABA LA REGLA VIEJA: exigia exactamente 2
    # extremas por muro transversal, que es lo mismo que decir "la
    # primera y la ultima de cada fila". Daba verde sobre el defecto que
    # venia a vigilar, porque comprobaba la implementacion contra si
    # misma en vez de contra la norma. Ahora se verifica lo que el
    # 8.5.1.1 pide: que CADA muro aporte dos columnas reforzadas --sean
    # C-2 o C-3-- en sus propios extremos.
    assert n_ext + n_c4 == 2 * len(MUROS) - _extremos_compartidos(), (
        "los muros aportan %d extremos y se dibujaron %d columnas "
        "reforzadas (%d C-2 + %d C-3)"
        % (2 * len(MUROS) - _extremos_compartidos(), n_ext + n_c4,
           n_ext, n_c4))
    assert n_tramos >= len(MUROS), (
        "hay %d tramos para %d muros: algun muro no se dibujo"
        % (n_tramos, len(MUROS)))
    esperados_v = sum(len(m[4]) for m in MUROS)
    assert n_p + n_v == esperados_v, (
        "se dibujaron %d vanos y el SSOT declara %d" % (n_p + n_v, esperados_v))
    esperadas = sum(1 for m in MUROS
                    for a, _w in vanos_ubicados(m[0], m[1], m[2], m[4])
                    if es_ventana(m[0], a))
    assert n_v == esperadas, (
        "se dibujaron %d ventanas y el SSOT declara %d" % (n_v, esperadas))
    # el mensaje mostraba solo dos tipos y el tercero quedaba invisible:
    # un resumen que no suma lo que el control verifica confunde mas que
    # ayuda.
    print("  [ok] %d tramos de muro, %d columnas (%d C-2 + %d C-4 + %d C-1)"
          % (n_tramos, n_ext + n_c4 + n_int, n_ext, n_c4, n_int))
    print("  [ok] %d vanos: %d puertas con barrido y %d ventanas"
          % (n_p + n_v, n_p, n_v))

    # CONTROL: la suma de los tramos cotados de cada muro tiene que dar L, y
    # la suma de sus machones tiene que dar la Ln que usa el calculo. Un
    # plano cuyas cotas no cierran con el calculo es peor que uno sin cotas:
    # parece verificado.
    # CONTROL. Compara LO QUE EL PLANO DIBUJO contra lo que usa el calculo,
    # tramo por tramo. La primera version comparaba SUMAS y no mordia: partir
    # un machon en dos no cambia la suma, asi que un corte inventado pasaba
    # en verde (probado inyectando el error). La segunda re-derivaba los
    # tramos en vez de mirar los dibujados, con lo cual medía su propia
    # copia. Un control tiene que mirar el artefacto.
    for nom, dire, largo, t_, vs in MUROS:
        corto = nom.split()[0]
        if not vs:
            continue
        tramos = cotado.get(corto, [])
        assert tramos, "%s tiene vanos y no se coto ningun tramo" % corto
        cubierto = sum(b - a for a, b, _ in tramos)
        omitido = largo - cubierto
        assert omitido < 0.10 + 1e-9, (
            "%s: la cadena deja %.3f m sin cotar (L = %.2f)"
            % (corto, omitido, largo))

        # los tramos de MACHON del plano, contra los machones del SSOT
        m_plano = sorted((round(a, 3), round(b, 3)) for a, b, ev in tramos
                         if not ev and b - a > SEPARACION_VANO_COLUMNA + 1e-9)
        m_calc = sorted((round(a, 3), round(b, 3))
                        for a, b in machones(corto, dire, largo, vs))
        assert m_plano == m_calc, (
            "%s: el plano cota los machones %s y el calculo usa %s"
            % (corto, m_plano, m_calc))

        # y los VANOS, contra los del SSOT
        v_plano = sorted((round(a, 3), round(b, 3))
                         for a, b, ev in tramos if ev)
        v_calc = sorted((round(a, 3), round(a + w, 3))
                        for a, w in vanos_ubicados(corto, dire, largo, vs))
        assert v_plano == v_calc, (
            "%s: el plano cota los vanos %s y el SSOT declara %s"
            % (corto, v_plano, v_calc))
    print("  [ok] %d muros acotados tramo a tramo (%d cotas), todas cierran"
          % (n_cad, n_cot))

    # CONTROL DE HOJA. El guardian de dibujo audita el DXF, y el DXF solo
    # lleva primitivas de MODELO: cuadros, leyenda y cajetin nunca se
    # miraban. Con la columna colocada a mano, la leyenda quedaba 30 mm
    # encima del cuadro de la reticula y todo daba verde.
    ch = L.control_hoja()
    assert not ch, ("bloques de hoja que se pisan: %s"
                    % ["%s / %s (%.1f x %.1f mm)" % c for c in ch])
    # y que ninguno se salga de la hoja util
    for nom, x0, y0, x1, y1 in L._cajas_hoja:
        assert (6.0 <= x0 and x1 <= A3_MM[0] - 6.0
                and 6.0 <= y0 and y1 <= A3_MM[1] - 6.0), (
            "el bloque %r se sale de la hoja: x[%.1f, %.1f] y[%.1f, %.1f]"
            % (nom, x0, x1, y0, y1))
    print("  [ok] %d bloques de hoja, ninguno se pisa ni se sale"
          % len(L._cajas_hoja))
    return True


def main():
    (L, n_tramos, n_ext, n_int, n_c4, n_p, n_v,
     n_cad, n_cot, cotado) = construir()
    import rutas as R
    salidas = L.render(Path(R.LAMINAS), dpi=200, dxf_dir=Path(R.CAD))
    # TERCER destino: la figura para el informe. Mismo dibujo, sin cajetin
    # ni marco de hoja -- la pagina del informe ya tiene titulo y pie, y el
    # cajetin ahi se come un sexto de la imagen.
    # La figura del informe se compone para la PAGINA (ver
    # lamina.py::render_figura): el DXF y la lamina completa
    # siguen saliendo a tamano de hoja, que es donde van.
    salidas["fig"] = L.render_figura(
        Path(R.INFORME), dpi=200,
        ancho_pagina=6.30, alto_pagina=8.86,
        cota_min_m=1.20)
    print("=" * 74)
    print("LAMINA E-01  -  PLANTA ESTRUCTURAL TIPICA")
    print("=" * 74)
    print()
    for k, v in salidas.items():
        print("  %-5s %s  (%.0f KB)"
              % (k, v.name, os.path.getsize(v) / 1024.0))
    print()
    print("  escala 1:%d, hoja A3 (%.0f x %.0f mm)"
          % (ESCALA, 420, 297))
    control(L, n_tramos, n_ext, n_int, n_c4, n_p, n_v, n_cad, n_cot,
            cotado)
    return salidas


if __name__ == "__main__":
    main()
