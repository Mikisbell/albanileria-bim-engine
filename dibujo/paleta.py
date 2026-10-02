# -*- coding: utf-8 -*-
"""La paleta del juego de planos, en un solo lugar.

POR QUE EXISTE
==============
Mikis, 2026-09-21: *"los planos los pusiste en negro y blanco y ese es un
error garrafal, además mejóralo profesionalmente, debe ser un plano pero
dinámico moderno, lo haces como si estuviéramos en el 2002"*.

Tenía razón: el muro se dibujaba con `#3d3d3d` —un gris casi negro, plano—,
la columna con un rojo ladrillo apagado y el resto sobre blanco puro. Es la
paleta por defecto de un CAD de hace veinte años, y además cada color estaba
escrito a mano en cada archivo, así que «cambiar el aspecto» significaba
buscar veinte literales.

CRITERIO DE LA PALETA
=====================
Un plano moderno no es un plano de colores: es un plano con JERARQUÍA. Lo que
resiste se lee primero, lo que informa después, y lo que es referencia casi
no se ve.

  NIVEL 1  la estructura que resiste -- muro y columna. Tono profundo y
           saturado, contraste alto contra el papel.
  NIVEL 2  lo que se construye pero no resiste -- losa, vanos, escalera.
           Tonos claros, con color pero sin peso.
  NIVEL 3  la información -- cotas, ejes, rótulos. Un solo color frío que
           no compite con el dibujo.
  ACENTO   lo que hay que mirar -- el límite de propiedad, el muro que
           gobierna, una advertencia.

Los tonos son de la familia azul-grafito, que es lo que usa hoy la
documentación técnica: el negro puro sobre blanco puro cansa la vista y en
impresión se ve sucio.
"""

# ---------------------------------------------------------------- NIVEL 1
MURO = "#37474f"            # azul grafito, el muro portante
MURO_BORDE = "#263238"
# El muro que lleva ventana: el mismo grafito, dos tonos mas claro. NO
# es otro color -- sigue siendo muro portante y tiene que leerse como
# tal--; es el MISMO material con menos seccion. Ver el porque en
# L_planta_estructural.py::muros().
MURO_VENTANA = "#78909c"
COLUMNA = "#d84315"         # naranja profundo: se distingue del muro a 1:100
COLUMNA_BORDE = "#8d2c08"
CIMIENTO = "#795548"
CIMIENTO_BORDE = "#4e342e"

# ---------------------------------------------------------------- NIVEL 2
LOSA = "#eceff1"
VIGUETA = "#b0bec5"
SOLERA = "#00796b"
VIGA = "#e65100"
PUERTA = "#bcaaa4"
VENTANA = "#b3e5fc"
ESCALERA = "#c8e6c9"
VACIO = "#90a4ae"           # el pozo: un hueco, no una superficie
TERRENO = "#efebe9"

# ---------------------------------------------------------------- NIVEL 3
COTA = "#00838f"            # cian profundo
EJE = "#5c6bc0"             # índigo suave
TEXTO = "#37474f"
GUIA = "#90a4ae"

# ----------------------------------------------------------------- ACENTO
LIMITE = "#6a1b9a"          # el límite de propiedad y la junta sísmica
GOBIERNA = "#6a1b9a"        # el elemento que decide la verificación
ALERTA = "#c62828"
BIEN = "#2e7d32"
REGULAR = "#ef6c00"

# ------------------------------------------------------------------ HOJA
PAPEL = "#ffffff"
MARCO = "#546e7a"
CAJETIN_BANDA = "#37474f"   # la banda de título del cajetín
CAJETIN_FONDO = "#fafafa"


def semaforo(frac, corte_bien=0.50, corte_mal=1.00):
    """El color de una verificación según cuánto usa de su límite."""
    if frac >= corte_mal:
        return ALERTA
    if frac >= corte_bien:
        return REGULAR
    return BIEN
