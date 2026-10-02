# -*- coding: utf-8 -*-
"""Los datos del cajetín, una sola vez para las seis láminas.

Antes cada generador DXF repetía el nombre del docente, el NRC y los siete
integrantes. Siete copias del mismo dato es siete formas de que una quede
vieja: cuando el título del proyecto cambió, tres láminas se enteraron y
tres no.

Todo lo numérico sale de `calculo/proyecto.py`. Lo administrativo —quiénes
somos, qué curso, qué NRC— vive aquí y en ningún otro lado.
"""
import datetime
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))

from proyecto import FC, FY, N_PISOS, HN, ESPESOR, FM   # noqa: E402

CURSO = "Albañilería"
NRC = "28606"
GRUPO = "Grupo 6"
DOCENTE = "Ing. Lourdes Graciela Poma Bernaola"
INTEGRANTES = [
    "Guillen Gala, Johan Ronaldo",
    "Paredes Terrel, Joel Marcos",
    "Ramirez Herrera, Milton Frank",
    "Rivera Ospina, Miguel Angel",
    "Taype Montanez, Jean",
    "Trigos Estrada, Maycol Jeyson",
    "Yauri Inga, Eddyn",
]

UBICACION = "Santo Domingo de Acobamba, Huancayo, Junín"
# LA ORIENTACION ES UNA DECISION DE PROYECTO, no un calculo: la
# fachada principal da a la via publica y el retiro posterior al
# fondo del lote. Vivia escrita en tres figuras distintas.
ORIENTACION_FACHADA = "Sur"
ORIENTACION_POSTERIOR = "Norte"

NORMAS = [
    "E.070 Albanileria (2006)",
    "E.030 Diseno Sismorresistente (2026)",
    "E.060 Concreto Armado (2009)",
    "E.020 Cargas (2006)",
    "E.050 Suelos y Cimentaciones",
    "A.010 / A.020 (2021)",
]


def meta():
    """El diccionario que el cajetín de `lamina.Lamina` espera."""
    return {
        "curso": "%s  -  NRC %s  -  %s" % (CURSO, NRC, GRUPO),
        "proyecto": ("EDIFICIO MULTIFAMILIAR DE %d PISOS - "
                     "ALBANILERIA CONFINADA" % N_PISOS),
        "ubicacion": "%s - Zona 2" % UBICACION,
        "alumno": "%s (%d integrantes)" % (GRUPO, len(INTEGRANTES)),
        "periodo": "2026-2",
        "fecha": datetime.date.today().strftime("%d/%m/%Y"),
        "fc": FC,
        "fy": FY,
        "norms": NORMAS,
        "procedencia": ("Geometria y cifras leidas de calculo/proyecto.py "
                        "(SSOT) - ninguna cota se teclea"),
    }
