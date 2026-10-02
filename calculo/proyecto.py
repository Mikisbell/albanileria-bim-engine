# -*- coding: utf-8 -*-
"""FUENTE UNICA DE VERDAD del proyecto. Todo script importa de aca.

Por que existe este archivo: la auditoria del 2026-09-13 encontro que las
constantes geometricas estaban repetidas en cuatro scripts. Cambiar la planta en
uno dejaba a los otros con valores viejos -- que es EXACTAMENTE el error del
trabajo de referencia, donde los libros 2-3 describian una planta de 40 x 18 m y
los libros 4-5 otra de 26 x 12,25 m, y las excentricidades de uno no alimentaban
al otro.

REGLA: ningun script vuelve a declarar una constante que este aca. Se importa:
    from proyecto import FRENTE, FONDO, Z, U, S, ...

Cada valor lleva su fuente. Los que no vienen de norma estan marcados SUPUESTO.
"""

# ============================================================ SISMO (E.030-2026)
# Los cuatro primeros NO son supuestos: salen del EMS real de Santo Domingo de
# Acobamba (Gob. Regional de Junin, contrato 267-2017-GRJ-GGR, Ing. Edgar Quiroz
# Villon CIP 62441), pagina 11, que declara textual:
#     Zona 2 | Z = 0,25g | Perfil del suelo tipo T = S2 | Tp = 0,6 s | S = 1,20
# El EMS trae ademas "Factor U = 1,50": ES DE SU PROYECTO, un centro de salud
# (categoria esencial). A nosotros no nos aplica.
Z = 0.25          # Tabla N.o 1, zona 2. El EMS lo confirma: "Z = 0,25g"
U = 1.00          # Tabla N.o 7, categoria C: "edificaciones comunes tales como
                  # viviendas". Decision del grupo: multifamiliar PURO, sin
                  # comercio en planta baja, asi que no hay mezcla de categorias.
# S: el EMS dice 1,20 porque usa la E.030-2018, donde S2 en Z2 era un valor unico.
# La E.030-2026 vigente lo da como INTERVALO 1,00 - 1,30, y su nota (*) manda:
#   "En caso no se disponga informacion relativa a la velocidad de ondas de corte
#    (Vs), se debe considerar el MAYOR VALOR del intervalo para el factor S,
#    TP = 0,6 s y TL = 2,0 s para suelos S2"
# El EMS no tiene ensayo geofisico (solo calicatas y laboratorio), asi que no hay
# Vs para interpolar -> rige el extremo superior.
S = 1.30          # Tabla N.o 4, Z2/S2 = [1,00 - 1,30], sin Vs -> el mayor
T_P = 0.60        # Tabla N.o 5 y nota (*), s, para suelo S2
T_L = 2.00        # Tabla N.o 5 y nota (*), s, para suelo S2
C_T = 60          # Art. 36, albanileria
R0 = 3.0          # Tabla N.o 10, albanileria armada o confinada
IA = 1.00         # Tabla N.o 11  -- SUPUESTO a verificar con el analisis
IP = 1.00         # Tabla N.o 12  -- SUPUESTO a verificar con el analisis
R = R0 * IA * IP  # Art. 26
DERIVA_LIMITE = 0.005     # albanileria
FACTOR_MODERADO = 2.0     # severo/2 (Comentarios Art. 22)

# ============================================================ GEOMETRIA
# FRENTE_LOTE = frente del TERRENO.  FRENTE = frente EDIFICADO.
# La distincion es la misma que este archivo ya hacia entre FONDO y
# FONDO_LOTE, y hasta el 2026-09-21 no existia en X porque no habia retiro
# lateral: el edificio ocupaba los 12,00 m de lado a lado, apoyado sobre los
# dos limites de propiedad.
#
# Lo prohibe la E.030-2026 Art. 52.3: "El edificio se debe distanciar de los
# limites de propiedad adyacentes a otros lotes edificables, o con
# edificaciones, en una distancia no menor que 2/3 del desplazamiento maximo
# calculado segun el articulo 50; ni menor que s/2 si la edificacion
# existente cuenta con una junta sismica reglamentaria."
#
# Los otros dos lados NO lo gatillan: al frente hay 5,00 m de retiro hacia la
# via publica -- que no es "otro lote edificable" -- y atras 4,50 m.
#
# El valor lo fija s/2, no el desplazamiento: con Z = 0,25, S = 1,30 y
# h = 13,50 la formula del 52.2 da s = 0,02 Z S h = 8,78 cm y s/2 = 4,39 cm,
# mientras que 2/3 del desplazamiento inelastico maximo (0,75 R delta) son
# apenas 0,57 cm. En albanileria la deriva es tan chica que el criterio de
# desplazamiento nunca gobierna. Se redondea al alza a 5 cm: mas separacion
# es mas seguro y es una medida replanteable en obra.
#
# Si la edificacion vecina NO tiene junta reglamentaria, el Art. 52.4 pide
# s/2 propio mas s/2 del vecino; eso depende de la altura del vecino y se
# verifica en obra. Queda declarado en el plano (inciso g).
FRENTE_LOTE = 12.00        # m, direccion X -- el TERRENO
RETIRO_LATERAL = 0.05      # m, E.030-2026 Art. 52.3 (s/2 = 4,39 cm -> 5 cm)
FRENTE = FRENTE_LOTE - 2 * RETIRO_LATERAL   # m, la EDIFICACION
# OJO CON ESTOS DOS: no son lo mismo, y confundirlos fue lo que dejo el proyecto
# con 9 % de area libre.
#   FONDO       = fondo de la EDIFICACION. Es el que arma la reticula de muros.
#   FONDO_LOTE  = fondo del TERRENO. La diferencia es el retiro posterior.
# El area libre no la exige el RNE: la A.010 Art. 9.4 la delega en "la normativa
# local" (parametros urbanisticos municipales). Se adopta el 30 % que es el valor
# corriente en zonificacion residencial, porque sin el no hay licencia.
FONDO = 21.00        # m, fondo edificado
# DOS RETIROS, y cada uno esta por una razon distinta.
#
#  * FRONTAL: aloja los estacionamientos. La A.010 fija el cajon en 2,50 x 5,00 m
#    ("02 estacionamientos contiguos"), asi que el retiro tiene que medir 5,00 m
#    para que el auto entre DERECHO desde la calle, sin maniobrar. Dentro del
#    edificio no caben: los panos entre muros portantes miden 3,36 m.
#  * POSTERIOR: le da luz a la sala y a los dormitorios del departamento del
#    fondo. No se puede achicar a gusto -- si el vecino construye hasta el
#    limite, ese retiro funciona como un pozo de 1 y 2 lados, y la A.020
#    Cuadro N.o 04 pide 30 % de la altura del paramento = 4,08 m.
RETIRO_FRONTAL = 5.00
RETIRO_POSTERIOR = 4.50
FONDO_LOTE = RETIRO_FRONTAL + FONDO + RETIRO_POSTERIOR
AREA_LIBRE_MINIMA = 0.30   # -- parametro MUNICIPAL, no del RNE
# A.010, cuadro de dimensiones: "02 estacionamientos contiguos"
EST_ANCHO, EST_LARGO = 2.50, 5.00
N_ESTACIONAMIENTOS = 4     # A.020 21.3.a: 1 cada 3 viviendas, con 10 viviendas
N_PISOS = 5
H_ENTREPISO = 2.70
# --- La malla de muros transversales -----------------------------------------
# SIETE muros, no seis, y con panos DESIGUALES. Las dos cosas tienen motivo:
#
#  * Siete, porque con seis el esfuerzo axial NO cumplia al descontar los vanos
#    (10,87 contra 9,75). La E.070 7.1.1b ofrece cuatro salidas y la unica que no
#    degrada nada es "reducir Pm", o sea achicar el ancho tributario.
#  * Desiguales, porque el pozo de luz necesita 4,20 m de fondo para respaldar el
#    criterio mas exigente (1/3 del paramento = 4,17 m). Se le reserva un pano de
#    4,20 y el resto se reparte parejo.
PANOS_Y = [3.36, 3.36, 4.20, 3.36, 3.36, 3.36]     # suma 21,00 m
EJES_MX = [sum(PANOS_Y[:i]) for i in range(len(PANOS_Y) + 1)]
PANO_POZO = 2                                       # indice del pano de 4,20

# E_LOSA sale del predimensionamiento: E.060 Tabla 9.1 pide L/18,5 en los panos
# extremos del aligerado (un solo extremo continuo). Ver 06_predimensionamiento.py.
E_LOSA = 0.20
H_LIBRE = H_ENTREPISO - E_LOSA
HN = N_PISOS * H_ENTREPISO

# EL POZO LO DIMENSIONA LA A.020, NO EL CRITERIO DEROGADO DE LA A.010.
# La Norma Tecnica A.020 Vivienda (RM 188-2021-VIVIENDA), Cuadro N.o 04, fija la
# dimension del pozo en multifamiliar como un PORCENTAJE de la altura del
# paramento: 35 % para ambientes tipo A (dormitorios, salas, comedores) con el
# pozo definido por 3 o 4 lados propios. Con h = HN + parapeto - alfeizar =
# 13,60 m eso son 4,76 m, y el pozo cuadrado de 4,20 que traiamos NO CUMPLIA.
#
# Se aplica la nota iii del mismo cuadro: se admite hasta 20 % de deficit en un
# sentido si el otro compensa Y se cumple el area normativa. El deficit en Y es
# 11,8 % (admisible) y se compensa alargando en X. Asi el pano de losa en Y
# sigue siendo de 4,20 m y el aligerado no tiene que engordar.
PARAPETO = 1.10   # m -- SUPUESTO de proyecto; entra en la altura del paramento
# El pozo se CENTRA en el frente edificado, no se deja en una coordenada
# escrita a mano. Con el retiro lateral el frente pasa de 12,00 a 11,90, y
# un pozo fijo en 3,30-8,70 quedaria con 3,30 de un lado y 3,20 del otro:
# una excentricidad de 5 cm metida a mano en una planta que hoy es simetrica
# en X, justo la que despues hay que pagar en torsion.
POZO_ANCHO_NOM = 5.40      # m -- dimension de proyecto del pozo
POZO_X0 = (FRENTE - POZO_ANCHO_NOM) / 2.0
POZO_X1 = POZO_X0 + POZO_ANCHO_NOM
POZO_Y0, POZO_Y1 = EJES_MX[PANO_POZO], EJES_MX[PANO_POZO + 1]
POZO_ANCHO = POZO_X1 - POZO_X0
POZO_LARGO = POZO_Y1 - POZO_Y0
ALFEIZAR = 1.00     # m  -- SUPUESTO; altura del alfeizar mas bajo que da al pozo

# El espesor NO es una eleccion de diseno: lo fija la unidad. En aparejo de
# cabeza el muro mide lo que mide el LARGO del ladrillo, y la unidad SOLIDA
# que exige la Tabla 2 (KK 30 % de vacio / INFES) solo se fabrica en 24 cm;
# el formato de 23 es el de la familia HUECA, prohibida. Medido sobre 7
# fichas de fabricante en 13_unidad_albanileria.py.
ESPESOR = 0.24        # m, aparejo de cabeza = largo de la unidad solida

# Las otras dos medidas de la unidad y el espesor de la junta. Vivian sueltas
# en 14_reparto_de_unidades.py, pero desde que el 18 disena el REFUERZO
# HORIZONTAL las necesitan DOS scripts: la hilada (alto + junta) es la que fija
# el espaciamiento posible de las varillas. Una constante que usan dos scripts
# pertenece al SSOT.
A_UNIDAD = 0.13       # m, ancho de la unidad (ficha de fabricante, script 13)
H_UNIDAD = 0.09       # m, alto de la unidad
JUNTA_MIN = 0.010     # m, E.070 4.1.2: espesor minimo de junta
JUNTA_MAX = 0.015     # m, E.070 4.1.2: espesor maximo de junta
# E.070 4.1.2, textual: "En las juntas que contengan refuerzo horizontal, el
# espesor minimo de la junta sera 6 mm mas el diametro de la barra". Con el
# maximo de 15 mm, eso ACOTA el diametro utilizable a 9 mm: una varilla de
# 3/8" (9,53 mm) pediria 15,53 mm de junta y queda descartada.
SOBREESPESOR_JUNTA_REF = 0.006   # m, los 6 mm del 4.1.2

# La caja de escalera tambien perfora la losa, igual que el pozo, y por lo tanto
# tambien descuenta area y tambien pide viga de borde. Va en la franja central
# del primer pano, apoyada contra el muro longitudinal izquierdo.
# Ancho = dos tramos de 1,20 m (A.020 15.2.b) mas el muro intermedio.
ANCHO_TRAMO_ESCALERA = 1.20
ESC_X0 = POZO_X0
ESC_X1 = POZO_X0 + 2 * ANCHO_TRAMO_ESCALERA + ESPESOR
ESC_Y0 = 0.60       # deja un descanso contra la fachada
ESC_Y1 = PANOS_Y[0]
AREA_ESCALERA = (ESC_X1 - ESC_X0) * (ESC_Y1 - ESC_Y0)

AREA_LOTE = FRENTE_LOTE * FONDO_LOTE     # el TERRENO
AREA_EDIFICADA = FRENTE * FONDO          # la huella de la edificacion
AREA_POZO = POZO_ANCHO * POZO_LARGO
AREA_PLANTA = AREA_EDIFICADA - AREA_POZO # la techada: el pozo no es planta
# A.010 9.3: area libre es aquella "sobre la cual no existen proyecciones de
# areas techadas". Suma el retiro posterior y el pozo de luz.
AREA_LIBRE = FRENTE * (RETIRO_FRONTAL + RETIRO_POSTERIOR) + AREA_POZO
PCT_AREA_LIBRE = AREA_LIBRE / AREA_LOTE

# ============================================================ MUROS
# ESPESOR se define arriba, en GEOMETRIA: la caja de escalera lo necesita
# para dimensionarse y Python lee el modulo de arriba hacia abajo.
LONG_MINIMA = 1.20    # E.070: solo cuentan los muros de L >= 1,20 m

# ---- elementos de confinamiento (todos salen de 06_predimensionamiento.py)
B_SOLERA = ESPESOR    # E.070 7.2.3: espesor minimo = espesor efectivo del muro
H_SOLERA = E_LOSA     # E.070 7.2.4: peralte minimo = espesor de la losa de techo
B_COLUMNA = ESPESOR   # E.070 7.2.3
# DOS TIPOS DE COLUMNA, porque la Tabla 11 del 8.6.3 distingue INTERIOR de
# EXTREMA y las fuerzas no se parecen: en la medianera mas exigida, la
# extrema recibe C = 108 409 kgf y la interior 5 425. Dimensionar todas como
# extremas pedia 1113 cm2 en cada una; dimensionarlas como interiores dejaba
# los extremos cortos. Se separan (ver 19_confinamientos.py).
H_COLUMNA = 0.25      # C-1 INTERIOR. E.070 7.2.5 pide >= 0,15; 8.6.3 pide Ac >= 15t
# C-2 EXTREMA. Tres criterios la tocan y gana el tercero:
#   1. CORTE-FRICCION del 8.6.3-a.2:  Acf = 624 cm2  ->  d = 26 cm
#   2. compresion: no gobierna
#   3. ANCLAJE DE LA SOLERA EN EL LIMITE DE PROPIEDAD, E.070 7.1.4:
#      "En el caso que se discontinuen las vigas soleras, [...] porque el
#      muro llega a un limite de propiedad, el peralte minimo de la columna
#      de confinamiento respectiva debera ser suficiente como para permitir
#      el anclaje de la parte recta del refuerzo longitudinal existente en
#      la viga solera mas el recubrimiento respectivo."
#
#      Las CATORCE C-2 estan en los dos limites laterales -- son los extremos
#      de los siete muros X --, y ahi las soleras se discontinuan. La VS-1
#      lleva o 1/2" y su ldh con gancho estandar (E.060 12.5.2,
#      0,075 fy db / raiz f'c) es 27,6 cm. Con d = 30 quedaban 30 - 2,5 =
#      27,5 cm: faltaban 0,15 cm. Con d = 35 quedan 32,5, un 18 % de holgura.
#
#      Se descarto bajar el refuerzo de la solera a 8 o 3/8" (ldh = 20,7 cm,
#      tambien resuelve): congestiona un nudo que ya recibe columna y losa, y
#      el acapite habla de PERALTE, no de cambiar el armado.
#
#      OJO: el peralte entra en s3 = d/4 del 8.6.3-a.3, asi que cambiar este
#      numero recalcula CUAL de los cuatro espaciamientos rige. Lo deriva el
#      script 19; no se toca el estribaje a mano.
H_COLUMNA_EXT = 0.35


def vol_columnas(n_col, altura):
    """Volumen de concreto de las columnas de UN muro: 2 extremas + el resto.

    Un muro siempre tiene sus dos extremos confinados; las de adentro son
    interiores. Con n_col = 2 las dos son extremas.
    """
    n_ext = min(2, n_col)
    n_int = max(0, n_col - 2)
    return (n_ext * B_COLUMNA * H_COLUMNA_EXT * altura
            + n_int * B_COLUMNA * H_COLUMNA * altura)
ALTURA_VENTANA = 1.00 # m -- SUPUESTO de proyecto
ALTO_PUERTA = 2.10    # m -- altura de puerta. NO es un capricho: la A.010 Art.
                      # 18.3 pide que vigas y elementos horizontales queden a
                      # "altura libre no menor a 2.10 m medida sobre el piso
                      # terminado". Un dintel mas bajo no deja pasar la puerta.
E_PISO_TERMINADO = 0.05   # m -- espesor del contrapiso mas el acabado.
# NO es un detalle: la puerta apoya en el PISO TERMINADO, no en la losa, asi que
# come 5 cm de la altura libre. Omitirlo dejaba el fondo del dintel a 2,05 m y
# la A.010 Art. 18.3 pide 2,10 m. Lo cazo _auditoria_coherencia.py.
#
# HAY DOS DINTELES, y confundirlos fue el error de la primera version: sobre la
# ventana sobra mas altura que sobre la puerta, porque la ventana recien arranca
# despues del alfeizar.
H_DINTEL_VENTANA = H_LIBRE - E_PISO_TERMINADO - ALFEIZAR - ALTURA_VENTANA  # 0,45
H_DINTEL_PUERTA = H_LIBRE - E_PISO_TERMINADO - ALTO_PUERTA                 # 0,35
H_DINTEL = H_DINTEL_PUERTA        # el que manda: es el menor y el mas comun
SEPARACION_MX = max(PANOS_Y)   # el pano mayor, que es el que manda para la losa
# Donde cae una columna de confinamiento a lo largo de un muro transversal: en
# cada cruce con un muro longitudinal. Las separaciones que resultan (3,90 /
# 4,20 / 3,90) cumplen el tope de 5 m de la E.070 7.2.1.b sin columnas extra.
# Con el pozo de 5,40 m, el tramo entre los ejes longitudinales supera el tope
# de 5,00 m de la E.070 7.2.1.b, asi que se agrega una columna intermedia en el
# eje 6,00. No tiene muro longitudinal debajo y no hace falta: el 7.2.1.b limita
# la SEPARACION entre columnas, no exige que coincidan con un cruce de muros.
# El eje extremo ES el frente del lote y los intermedios SON los bordes del
# pozo: se escriben con sus constantes para que muevan juntos.
# el eje agregado por el 7.2.1.b va al MEDIO del tramo del pozo, derivado
EJES_COLUMNAS_X = [0.00, POZO_X0, (POZO_X0 + POZO_X1) / 2.0,
                   POZO_X1, FRENTE]
# Los ROTULOS de esos ejes. Viven acá y no en cada generador porque el 2026-09-21
# se descubrio que CUATRO archivos de dibujo tenian su propia lista
# -- [0, POZO_X0, POZO_X1, FRENTE] --, todos sin el eje 6,00: el proyecto
# dibujaba 4 ejes y calculaba con 5. Los vanos ya se ubicaban con los 5
# (vanos_ubicados llama a ejes_de_columna), asi que el plano contradecia a su
# propia fuente. Cuarto caso del mismo patron en este proyecto.
ETIQUETAS_EJES_X = ["A", "B", "C", "D", "E"]
assert len(ETIQUETAS_EJES_X) == len(EJES_COLUMNAS_X)


def ejes_x_rotulados():
    """(coordenadas, etiquetas) de los ejes longitudinales. Fuente unica."""
    return list(EJES_COLUMNAS_X), list(ETIQUETAS_EJES_X)
L_MURO = FRENTE                # muro transversal interior, cruza todo el frente


def tributaria_mx():
    """Area tributaria de CADA muro transversal, con el pozo descontado.

    Sobre el pozo no hay losa, asi que los muros que lo bordean reciben menos
    carga que los del medio. Suponer un ancho tributario unico para todos seria
    conservador en unos y, sobre todo, dejaria sin identificar cual es el muro
    critico -- que es el dato que de verdad hace falta.

    Devuelve (nombre, y, ancho de franja, area).
    """
    filas = []
    for i, y in enumerate(EJES_MX):
        y0 = y - (PANOS_Y[i - 1] / 2.0 if i > 0 else 0.0)
        y1 = y + (PANOS_Y[i] / 2.0 if i < len(PANOS_Y) else 0.0)
        area = (y1 - y0) * FRENTE
        solape = max(0.0, min(y1, POZO_Y1) - max(y0, POZO_Y0))
        area -= solape * POZO_ANCHO
        filas.append(("MX-%d" % (i + 1), y, y1 - y0, area))
    return filas


# El ancho tributario del muro CRITICO, no el de uno cualquiera.
ANCHO_TRIB = max(f[3] for f in tributaria_mx()) / FRENTE

# (nombre, direccion, longitud_bruta_m, espesor_m, [anchos de vano en m])
#
# Los VANOS son parte del dato, no un detalle de arquitectura: un muro partido
# por una puerta son DOS muros, y la E.070 6.4 solo deja contar los que tienen
# "una longitud mayor o igual a 1,20 m para ser considerados como contribuyentes
# en la resistencia a las fuerzas horizontales". Contar la longitud bruta es
# inflar la densidad con muro que no existe.
#
# Las medianeras no llevan vanos: dan contra el predio vecino. Es la ventaja
# estructural del lote medianero, y conviene no desperdiciarla.
# EL CUADRO DE VANOS SALE DE LA PLANTA, no al reves. Cada puerta de la
# distribucion arquitectonica es un vano en un muro PORTANTE, y le quita area de
# corte al edificio. Por eso la planta se diseno para cruzar muros lo menos
# posible: circulacion concentrada, banos y cocinas agrupados contra las
# medianeras, y ningun ambiente al que haya que entrar atravesando otro.
# Ver figuras/planta_arquitectonica.py.
_POZO_Y0, _POZO_Y1 = POZO_Y0, POZO_Y1

# AUDITORIA 2026-09-19. Los scripts 11 y 15 descontaban el volumen de TODOS
# los vanos con la altura de una PUERTA. En las dos fachadas los vanos son
# VENTANAS: miden 1,00 m de alto y debajo de cada una queda un ALFEIZAR de
# albanileria que existe y que pesa. Descontarlo como si fuera puerta borraba
# 1,15 m de muro bajo cada ventana -- 27 830 kgf sobre los cinco niveles, el
# 1,9 % del peso sismico -- y lo hacia del lado INSEGURO, porque menos peso
# es menos fuerza sismica. Un descuento de mas no se nota: el muro sale mas
# liviano y ningun control grita.
# EL ANCHO DE CADA VANO DE PUERTA LO FIJA LA NORMA, POR AMBIENTE SERVIDO.
# A.020 Art. 12.2.b, Cuadro N.6 "Ancho minimo de los vanos", textual:
#
#   Acceso principal a una unidad vivienda ......................... 0,90 m
#   Acceso a ambientes de descanso (dormir), reunion (estar),
#     alimentacion (cocinar y comer) ............................... 0,80 m
#   Acceso a ambientes de aseo y servicios (banos) ................. 0,70 m
#   Acceso principal a una vivienda multifamiliar, de uso colectivo
#     o conjunto residencial ....................................... 1,20 m
#
# El proyecto usaba 0,90 m en los diecinueve vanos interiores SIN fundamento
# -- y el A.010 Art. 19.1, que es donde se lo habria buscado, no fija ancho:
# dice que "deben calcularse segun el uso de los ambientes a los que sirven"
# y solo fija la altura minima de 2,10 m. El cuadro que si los fija esta en la
# A.020, la norma de VIVIENDA.
#
# No es un detalle de arquitectura: el ancho del vano sale de la longitud del
# muro, y de la longitud neta salen la densidad, el esfuerzo axial y la
# resistencia al corte. Diecinueve vanos con 0,10 m de sobrancho son 1,90 m de
# muro que no existe.
ANCHO_VANO_EDIFICIO = 1.20    # acceso principal al multifamiliar
ANCHO_VANO_VIVIENDA = 0.90    # acceso principal a una unidad de vivienda
ANCHO_VANO_AMBIENTE = 0.80    # dormir, estar, cocinar y comer
ANCHO_VANO_BANO = 0.70        # aseo y servicios

MUROS_CON_VENTANA = ("MX-1", "MX-7")          # las dos fachadas


def tipo_de_vano(nom, x0):
    """'puerta' o 'ventana'. Es POR VANO, no por muro.

    `MUROS_CON_VENTANA` declara el tipo por MURO, y con eso los cuatro
    vanos de la fachada frontal salian ventana: el edificio no tenia puerta
    de ingreso. La excepcion es UNA y esta declarada en `PUERTA_INGRESO`.

    `x0` es la coordenada de arranque del vano sobre el muro, la misma que
    devuelve `vanos_ubicados()`.
    """
    nom_i, tramo_i = PUERTA_INGRESO
    if nom.startswith(nom_i):
        ejes = ejes_de_columna(nom, "X", FRENTE)
        if abs(x0 - (ejes[tramo_i] + SEPARACION_VANO_COLUMNA)) < 0.01:
            return "puerta"
    return "ventana" if nom.startswith(MUROS_CON_VENTANA) else "puerta"


def altura_de_vano(nom, x0):
    """Altura del hueco que se descuenta del volumen del muro, en m.

    Es POR VANO porque un muro puede llevar las dos cosas: la fachada
    frontal tiene tres ventanas de 1,00 m -- con su alfeizar de albanileria
    debajo, que existe y pesa -- y la puerta de ingreso, que llega hasta el
    dintel. Descontar todo con una sola altura falsea el peso.

    EL VANO DE INGRESO CUENTA COMO VENTANA, y es a proposito. Es puerta
    SOLO en el primer piso: en los cuatro de arriba el hall no da a la
    calle y ese vano es su ventana, con su alfeizar de albanileria debajo.
    `MUROS` describe el piso TIPICO y el metrado lo multiplica por los
    cinco niveles, asi que tomar la puerta en los cinco borraria cuatro
    alfeizares que existen -- unos 1 500 kgf -- y eso va del lado INSEGURO:
    menos peso es menos fuerza sismica. Tomar la ventana es lo que ocurre
    en 4 de los 5 pisos y ademas es el lado seguro.

    El DIBUJO si la trata como puerta: la planta del primer piso y la
    elevacion frontal la muestran con su hoja y su barrido, y dejan nota de
    que en los pisos 2 a 5 ese vano es una ventana del hall.
    """
    nom_i, _tramo_i = PUERTA_INGRESO
    if nom.startswith(nom_i):
        return ALTURA_VENTANA
    if tipo_de_vano(nom, x0) == "ventana":
        return ALTURA_VENTANA
    return H_LIBRE - H_DINTEL_PUERTA


def volumen_de_vanos(nom, dire, largo, vanos, t):
    """m3 de hueco que se le descuenta a un muro, vano por vano."""
    return sum(ancho * altura_de_vano(nom, x0) * t
               for x0, ancho in vanos_ubicados(nom, dire, largo, vanos))


MUROS = [
    # medianeras: dan contra el predio vecino, no llevan vano
    ("MY-1  medianera izquierda",      "Y", FONDO, ESPESOR, []),
    ("MY-2  medianera derecha",        "Y", FONDO, ESPESOR, []),
    # longitudinales interiores: una puerta por pano servido
    ("MY-3a eje 3,30 frontal",         "Y", _POZO_Y0,         ESPESOR,
     [ANCHO_VANO_VIVIENDA]),                     # acceso a la vivienda A
    ("MY-3b eje 3,30 posterior",       "Y", FONDO - _POZO_Y1, ESPESOR,
     [ANCHO_VANO_AMBIENTE, ANCHO_VANO_BANO,      # cocina / lavanderia
      ANCHO_VANO_AMBIENTE]),                     # dormitorio  # no-ssot: 0,90 es el ancho de un VANO, no el factor phi
    ("MY-4a eje 8,70 frontal",         "Y", _POZO_Y0,         ESPESOR,
     [ANCHO_VANO_VIVIENDA]),                     # acceso a la vivienda B
    ("MY-4b eje 8,70 posterior",       "Y", FONDO - _POZO_Y1, ESPESOR,
     [ANCHO_VANO_AMBIENTE, ANCHO_VANO_BANO,      # cocina / lavanderia
      ANCHO_VANO_AMBIENTE]),                     # dormitorio  # no-ssot: 0,90 es el ancho de un VANO, no el factor phi
    # fachadas: UNA ventana por ambiente. Son tres ambientes por fachada
    # (dormitorio - sala - dormitorio), asi que son TRES vanos. Con dos, uno de
    # los dormitorios se quedaba sin ventana: lo delato el plano, no el calculo.
    # La ventana de la sala era UNA de 2,40 y se parte en DOS de 1,20. Motivo:
    # con los ejes de columna de este proyecto, el tramo mas largo mide 3,30 m,
    # y un vano de 2,40 deja un machon de 0,75 m -- por debajo del 1,20 que el
    # 6.4 exige para que un trozo de muro CUENTE. Partirla mantiene los 2,40 m
    # de vano (o sea la ventilacion del A.010 no cambia), mantiene L_neta en
    # 6,40 (densidad y esfuerzo axial intactos) y acorta los dinteles.
    ("MX-1  fachada frontal",          "X", FRENTE, ESPESOR, [1.60, 1.20, 1.20, 1.60]),   # no-ssot: 1,20 es el ANCHO de estas dos ventanas y coincide de valor con LONG_MINIMA
    # transversales interiores: una puerta por franja que haya que cruzar
    ("MX-2  eje y=3,36",               "X", FRENTE, ESPESOR,
     [ANCHO_VANO_AMBIENTE, ANCHO_VANO_VIVIENDA,  # dormitorio / paso comun
      ANCHO_VANO_AMBIENTE]),                     # dormitorio
    ("MX-3  eje y=6,72 (borde pozo)",  "X", FRENTE, ESPESOR,
     [ANCHO_VANO_AMBIENTE, ANCHO_VANO_AMBIENTE]),   # las dos salas  # no-ssot: 0,90 es el ancho de un VANO, no el factor phi
    ("MX-4  eje y=10,92 (borde pozo)", "X", FRENTE, ESPESOR,
     [ANCHO_VANO_AMBIENTE, ANCHO_VANO_AMBIENTE]),   # las dos salas
    ("MX-5  eje y=14,28",              "X", FRENTE, ESPESOR,
     [ANCHO_VANO_BANO, ANCHO_VANO_BANO]),          # los dos SS.HH.  # no-ssot: 0,90 es el ancho de un VANO, no el factor phi
    ("MX-6  eje y=17,64",              "X", FRENTE, ESPESOR,
     [ANCHO_VANO_AMBIENTE, ANCHO_VANO_AMBIENTE]),   # los dos dormitorios
    ("MX-7  fachada posterior",        "X", FRENTE, ESPESOR, [1.60, 1.20, 1.20, 1.60]),   # no-ssot: idem MX-1
]

# ================================================== GEOMETRIA DE LOS VANOS
# EN QUE TRAMO VA CADA VANO. Lo dicta la ARQUITECTURA, no la estructura.
#
# EL DEFECTO QUE ESTO CORRIGE (2026-09-21). `vanos_ubicados()` repartia los
# vanos con un criterio puramente estructural -- «el mas ancho al tramo mas
# largo» -- y NADA lo obligaba a coincidir con lo que la distribucion
# necesita. Este mismo archivo declara veinte lineas mas arriba que «EL
# CUADRO DE VANOS SALE DE LA PLANTA, no al reves», y hacia lo contrario. El
# resultado, que el control 35 destapo: el edificio no tenia puerta de
# ingreso, habia una puerta que unia dos viviendas distintas, y otra que
# abria un dormitorio a la escalera comun.
#
# AHORA la lista sale de `35_circulacion_y_vanos.py::vanos_necesarios()`,
# que construye el arbol de recorrido de cada vivienda -- prefiriendo los
# tabiques, que no le quitan area de corte a nada -- y dice exactamente que
# conexion cruza que muro portante. El indice es el TRAMO entre ejes de
# columna, y el orden de la lista corresponde al orden de los anchos
# declarados en MUROS. El 35 verifica que lo declarado aca coincida con lo
# que la planta pide, muro por muro.
TRAMO_DE_VANO = {
    # fachada frontal: ventana al dormitorio principal de cada vivienda
    # (tramos 0 y 3), ventana de la escalera (1) y la PUERTA DE INGRESO al
    # hall (2)
    "MX-1": [0, 1, 2, 3],
    # y = 3,36: vivienda A (0), el hall cruzando de adelante hacia atras
    # (2) y vivienda B (3)
    "MX-2": [0, 2, 3],
    "MX-3": [0, 3],
    "MX-4": [0, 3],
    "MX-5": [0, 3],
    "MX-6": [0, 3],
    # fachada posterior: una ventana por dormitorio, cuatro en total
    "MX-7": [0, 1, 2, 3],
    # el acceso a la vivienda A desde el hall de atras
    "MY-3a": [1],
    "MY-3b": [0, 1, 2],
    # el acceso a la vivienda B desde el hall de atras
    "MY-4a": [1],
    "MY-4b": [0, 1, 2],
}

# LA PUERTA DE INGRESO AL EDIFICIO. Es un vano de la fachada frontal, y es
# el UNICO de ese muro que no es ventana: da al hall, que es la pieza comun
# que toca la via publica. Antes no existia -- `MUROS_CON_VENTANA` declaraba
# el tipo POR MURO, asi que los cuatro vanos de MX-1 salian ventana y el
# edificio no tenia por donde entrarse.
PUERTA_INGRESO = ("MX-1", 2)        # (muro, indice de tramo)
ANCHO_INGRESO = ANCHO_VANO_EDIFICIO  # A.020 Cuadro N.6: acceso principal
                                     # a una vivienda multifamiliar

# EL CERRAMIENTO DEL POZO DE LUZ. MY-3 y MY-4 se interrumpen en la franja
# del pozo -- de y = 6,72 a y = 10,92 --, asi que sus dos caras laterales
# quedaban ABIERTAS AL VACIO: 4,20 m por cara sin muro ni tabique, y los dos
# ambientes que se iluminan por el pozo sin una sola ventana. Lo destapo el
# control 35.
#
# El cierre es TABIQUERIA, no muro portante, y eso no es un atajo: en la
# franja del pozo no hay losa de un lado, asi que ese paño no recibe
# diafragma en las dos caras. La E.070 9.3.1 admite expresamente la unidad
# hueca en tabiques -- la Tabla 2 solo la prohibe en muro PORTANTE de cuatro
# pisos a mas -- y un vano en un tabique no le quita area de corte al
# edificio. El tabique queda arriostrado por las columnas de las cuatro
# esquinas del pozo, que ya existen, y por la solera de cada nivel.
#
# (eje, coordenada, desde, hasta, ancho de la ventana)
CERRAMIENTO_POZO = [
    ("x", POZO_X0, POZO_Y0, POZO_Y1, 1.20),
    ("x", POZO_X1, POZO_Y0, POZO_Y1, 1.20),
]


def ventanas_del_pozo():
    """[(eje, coordenada, inicio, ancho)] de cada ventana al pozo."""
    out = []
    for eje, c, a, b, ancho in CERRAMIENTO_POZO:
        out.append((eje, c, (a + b) / 2.0 - ancho / 2.0, ancho))
    return out

# Hasta el 2026-09-17 el SSOT declaraba de cada vano solo su ANCHO, nunca su
# POSICION. Eso alcanzaba para descontar area, pero no para nada que dependa
# de DONDE esta el hueco, y hay tres cosas que dependen:
#
#   * la RIGIDEZ. 12_rigidez_lateral.py colocaba el alma de 0 a L_neta y las
#     columnas y alas en su coordenada real sobre la longitud BRUTA: en MX-1
#     eso ponia piezas 5,60 m mas alla del extremo del alma e inflaba la
#     inercia 14,8 veces (hallazgo C-1 de la auditoria del 15-set).
#   * el CONTROL DEL 6.4. control_6_4() promediaba (L - vanos)/n_panos, o sea
#     verificaba un trozo MEDIO. Un promedio de 1,60 puede esconder un machon
#     de 0,75 que no cuenta.
#   * el PLANO. La capa VANOS no dibujaba ni una puerta ni una ventana.
#
# CRITERIO DE UBICACION, declarado porque es una decision de proyecto:
# cada vano se ubica en UN tramo entre ejes de columna consecutivos, pegado a
# la columna de la izquierda. Asi cada machon queda enmarcado por columnas en
# sus cuatro lados, que es lo que pide el 7.2.1.a, y el vano no parte un pano
# por el medio. Los vanos mas anchos van a los tramos mas largos, que es lo
# que maximiza el machon mas corto.
SEPARACION_VANO_COLUMNA = 0.15   # m, media columna extrema: el vano arranca
                                 # en la cara interior de la columna, no en su eje


def ejes_de_columna(nom, dire, L):
    """Ejes de columna que caen sobre el muro, en COORDENADA DEL MURO (0..L)."""
    if dire == "X":
        return list(EJES_COLUMNAS_X)
    y0 = 0.0 if nom[:4] in ("MY-1", "MY-2") else (
        POZO_Y1 if nom[4:5] == "b" else 0.0)
    return [y - y0 for y in EJES_MX if y0 - 1e-9 <= y <= y0 + L + 1e-9]


def vanos_ubicados(nom, dire, L, vanos):
    """[(inicio, ancho)] de cada vano, ordenados por coordenada del muro.

    LA POSICION LA DICTA LA ARQUITECTURA. El tramo entre columnas lo
    declara `TRAMO_DE_VANO`; dentro del tramo, el vano arranca en la cara
    interior de la columna de la izquierda, de modo que cada machon queda
    enmarcado por columnas en sus cuatro lados -- que es lo que pide el
    7.2.1.a -- y ningun vano parte un paño por el medio.

    Antes el reparto era «el vano mas ancho al tramo mas largo», un
    criterio estructural que ignoraba la distribucion: producia puertas
    entre dos viviendas distintas y dejaba ambientes sin acceso. Ahora, si
    un muro tiene vanos y nadie declaro donde van, esto FALLA en vez de
    inventar una posicion.
    """
    if not vanos:
        return []
    ejes = ejes_de_columna(nom, dire, L)
    tramos = [(ejes[i], ejes[i + 1] - ejes[i]) for i in range(len(ejes) - 1)]
    idx = None
    for clave in sorted(TRAMO_DE_VANO, key=len, reverse=True):
        if nom.startswith(clave):
            idx = TRAMO_DE_VANO[clave]
            break
    if idx is None:
        raise ValueError("%s tiene %d vano(s) y TRAMO_DE_VANO no declara en "
                         "que tramo va cada uno" % (nom, len(vanos)))
    if len(idx) != len(vanos):
        raise ValueError("%s declara %d anchos de vano y %d tramos"
                         % (nom, len(vanos), len(idx)))
    if len(set(idx)) != len(idx):
        raise ValueError("%s pone dos vanos en el mismo tramo: %s"
                         % (nom, idx))
    puestos = []
    for ancho, k in zip(vanos, idx):
        if not 0 <= k < len(tramos):
            raise ValueError("%s: el tramo %d no existe (hay %d)"
                             % (nom, k, len(tramos)))
        t0, largo_tramo = tramos[k]
        if ancho + SEPARACION_VANO_COLUMNA > largo_tramo + 1e-9:
            raise ValueError("%s: el vano de %.2f m no entra en el tramo %d, "
                             "que mide %.2f m" % (nom, ancho, k, largo_tramo))
        puestos.append((t0 + SEPARACION_VANO_COLUMNA, ancho))
    return sorted(puestos)


def machones(nom, dire, L, vanos):
    """[(inicio, fin)] de los trozos de albanileria que quedan entre vanos.

    Es lo que de verdad resiste: el 6.4 solo cuenta los de L >= 1,20 m.
    """
    puestos = vanos_ubicados(nom, dire, L, vanos)
    trozos = []
    x = 0.0
    for x0, ancho in puestos:
        if x0 - x > 1e-9:
            trozos.append((x, x0))
        x = x0 + ancho
    if L - x > 1e-9:
        trozos.append((x, L))
    # Un trozo de SEPARACION_VANO_COLUMNA no es albanileria: es la media
    # columna que queda entre el EJE y la CARA donde arranca el vano. Contarlo
    # como machon fabricaba trozos de 0,15 m que despues el control del 6.4
    # denunciaba como "no cuenta", cuando en realidad ahi hay concreto.
    return [(a, b) for a, b in trozos
            if b - a > SEPARACION_VANO_COLUMNA + 1e-9]


def machones_efectivos(nom, dire, L, vanos):
    """Solo los machones que el 6.4 deja contar (L >= LONG_MINIMA)."""
    return [(a, b) for a, b in machones(nom, dire, L, vanos)
            if b - a >= LONG_MINIMA - 1e-9]


# ============================================================ CARGAS (E.020)
LOSA_ALIGERADA = 300.0   # kgf/m2, anexo 1, h = 0,20 m (0,25 -> 350; 0,17 -> 280)
# El piso terminado NO es un supuesto: se DERIVA. El Art. 3 de la E.020 manda
# calcular el peso real "en base a los pesos unitarios que aparecen en el
# Anexo 1", y el Anexo 1 tabula los dos materiales que lo componen: loseta
# (2 400 kgf/m3, fila "Losetas") y mortero de asiento (2 000, fila "Enlucido o
# Revoque de: mortero de cemento"). Decia "SUPUESTO, no tabulado en la E.020",
# y lo que no esta tabulado es el CONJUNTO, no sus partes.
E_LOSETA = 0.025         # m -- espesor de loseta, dato de proyecto
E_ASIENTO = 0.020        # m -- mortero de asiento bajo la loseta
PESO_LOSETA = 2400.0     # kgf/m3, E.020 anexo 1, fila 'Losetas'
PESO_MORTERO = 2000.0    # kgf/m3, anexo 1, 'Enlucido o Revoque de: mortero de cemento'
PISO_TERMINADO = E_LOSETA * PESO_LOSETA + E_ASIENTO * PESO_MORTERO
# EL PESO DE LA TABIQUERIA ES UN METRADO, NO UN SUPUESTO (2026-09-21).
#
# La E.020 Art. 5 es literal: "Se considerara el peso de todos los tabiques,
# usando los PESOS REALES en las UBICACIONES QUE INDICAN LOS PLANOS". No
# admite un valor uniforme por metro cuadrado de losa, y el proyecto venia
# cargando 150 kgf/m2 repartidos -- que su propio script 31 declaraba sin
# adornos: "NO es un metrado: es la carga invertida".
#
# Ahora la distribucion existe y esta derivada (script 34), asi que el metrado
# se puede hacer y el 31 lo hace: 21,84 m de tabique -- la divisoria entre las
# dos viviendas mas el cierre de las dos caras del pozo -- que sobre la losa
# del piso dan 56,3 kgf/m2. Se adopta 57 kgf/m2, redondeado al alza.
#
# POR QUE IMPORTA Y POR QUE NO ES UNA RELAJACION PARA APROBAR. La circulacion
# de dos viviendas obliga a TRES vanos en MX-2, que es el muro mas cargado del
# edificio, y con los 150 kgf/m2 inventados el muro excedia el 7.1.1.b en un
# 5,7 % bajo la lectura de losa continua. Reemplazar un numero inventado por
# el metrado que la norma exige no es ajustar el modelo al resultado: es lo
# que el Articulo 5 manda hacer en cuanto hay plano. Lo que SI seria ajustar
# es callar el margen, asi que el 26 calcula y declara cuanta tabiqueria
# admite el diseno antes de que MX-2 alcance el limite.
TABIQUERIA = 57.0        # kgf/m2  -- METRADO por el 31 (E.020 Art. 5)
SC_VIVIENDA = 200.0      # kgf/m2, tabla 1
SC_AZOTEA = 100.0        # kgf/m2, art. 7.1.a
PESO_ALBANILERIA = 1800.0  # kgf/m3, anexo 1, arcilla cocida solida
# La HUECA pesa 25 % menos, y ese es justamente el material que la Tabla 2
# le prohibe al muro portante y el Art. 9.3.1 le PERMITE al tabique.
PESO_ALBANILERIA_HUECA = 1350.0  # kgf/m3, anexo 1, arcilla cocida hueca
# El 1800 es la ALBANILERIA, no el muro terminado: la E.020 tabula el revoque
# en linea aparte. Faltaba en los muros portantes -- y el script 14 si se lo
# cobraba al tabique. Dos criterios para el mismo material (auditoria 09-15).
E_TARRAJEO = 0.015       # m -- espesor de revoque por cara. La E.020 tabula el
                         # PESO del mortero (2 000 kgf/m3) pero no el espesor,
                         # que es decision de proyecto: 1,5 cm es el corriente.
                         # Verificado que ninguna de las cinco normas lo fija.


def peso_tarrajeo(area_muro, medianera=False):
    """kgf de revoque sobre un muro. La medianera solo se tarrajea por dentro."""
    caras = 1 if medianera else 2
    return caras * E_TARRAJEO * PESO_MORTERO * area_muro
PESO_CONCRETO = 2400.0     # kgf/m3, anexo 1 (simple 2300 + 100)
PCT_CV_SISMO = 0.25      # E.030 Art. 31.b (categoria C) y 31.d (azotea)
# E.030-2026 Art. 37: "la excentricidad accidental en cada nivel (ei) se
# considera como 0,05 veces la dimension del edificio en la direccion
# PERPENDICULAR a la direccion de analisis". Ojo con eso: para sismo en Y la
# dimension que manda es el FRENTE, no el fondo.
EXC_ACCIDENTAL = 0.05    # E.030-2026 Art. 37

# ==================================================== ESCALERA (peso, no hueco)
# AUDITORIA 2026-09-19 (hallazgo C-4). La caja de escalera DESCONTABA area de
# la losa en el script 15 y en el 10, y NO aportaba peso en ningun script: el
# hueco estaba metrado y la estructura que lo llena, no. Son dos errores de
# signo OPUESTO y por eso ninguno delata al otro -- falta fuerza sismica (del
# lado inseguro) y sobra excentricidad ey (del lado seguro).
# A.010 Art. 23.2: el paso no sera menor de 0,25 m en vivienda (23.2.b) ni
# el contrapaso mayor de 0,18 (23.2.c). ATRIBUCION CORREGIDA el 2026-09-27:
# antes decia 'Art. 29', y en la A.010 de 2021 el Articulo 29 es 'Escaleras
# Abiertas (B3)'. El numero era correcto y el articulo no, que es la misma
# familia del Art. 24.5 de la E.070: una cita valida apuntando al documento
# o al lugar equivocado. Lo verifica el 37.
PASO_ESCALERA = 0.25
N_CONTRAPASOS = 16                                    # dos tramos de ocho
CONTRAPASO_ESCALERA = H_ENTREPISO / N_CONTRAPASOS     # 0,169 m <= 0,18  cumple
E_LOSA_ESCALERA = 0.15                                # losa inclinada


def peso_escalera_m2():
    """kgf/m2 de PROYECCION HORIZONTAL de la escalera (E.020 anexo 1).

    Dos terminos, y omitir el segundo es el error tipico: la losa inclinada,
    cuyo espesor VISTO EN PLANTA es e/cos(t) y no e, mas los pasos macizos,
    que en promedio anaden medio contrapaso de concreto sobre esa losa.
    """
    import math
    cos_t = PASO_ESCALERA / math.hypot(PASO_ESCALERA, CONTRAPASO_ESCALERA)
    e_equivalente = E_LOSA_ESCALERA / cos_t + CONTRAPASO_ESCALERA / 2.0
    return e_equivalente * PESO_CONCRETO + PISO_TERMINADO

# ============================================================ MATERIALES (E.070)
# Ladrillo SOLIDO industrial, clase IV o superior, vacios <= 30 %.
# f'm y v'm: la Tabla 9 no tabula esta denominacion; el Art. 5.1.9 obliga a
# ensayar. Se adoptan como REFERENCIA DECLARADA y se exige el ensayo (5.1.7).
FM = 65.0    # kgf/cm2  -- SUPUESTO declarado, a confirmar por ensayo de pilas
VM = 8.1     # kgf/cm2  -- SUPUESTO declarado, a confirmar por ensayo de muretes
EM = 500 * FM            # E.070 8.5.2 para unidades de arcilla

# ============================================================ SUELO (del EMS)
DF = 1.50          # m, profundidad de cimentacion
# Fig. N.o 3 del EMS, "B vs qad": la capacidad admisible DEPENDE del ancho.
# (ancho_m, qad_kg_cm2)
QAD_SEGUN_B = [(1.00, 3.00), (1.50, 3.85)]   # no-ssot: 1,50 es el ANCHO B tabulado por el EMS, no la profundidad Df
QAD = min(q for _, q in QAD_SEGUN_B)   # el mas desfavorable del grafico
# Ancho adoptado de cimiento corrido. Lo verifica 04_cimentacion.py, que importa
# el Pm del metrado. Con la malla de 7 muros el B requerido es 0,58 m.
B_CIMIENTO = 0.70   # m. Paso de 0,60 a 0,70 el 2026-09-16: al sumar el
                    # tarrajeo la holgura del suelo cayo al +2 %, que no es margen

# ============================================================ CONCRETO (E.060)
FC = 210.0         # kgf/cm2 -- NO es un supuesto libre: es el MINIMO NORMATIVO.
                   # Decia "(E.070 pide >= 175 en columnas)", que es el minimo
                   # MENOS restrictivo y no el que gobierna. El que manda es la
                   # E.060 21.3.2.1: "Concreto en elementos resistentes a
                   # fuerzas inducidas por sismo. La resistencia especificada a
                   # la compresion del concreto, f'c, NO DEBE SER MENOR QUE
                   # 21 MPa" -- y 210 kgf/cm2 es el equivalente comercial
                   # peruano. Una columna de confinamiento de muro portante es
                   # elemento resistente a sismo, asi que 175 no alcanza.
                   # La salvedad de 17 MPa del 21.10 es para MUROS DE
                   # DUCTILIDAD LIMITADA y no aplica aqui (verificado 2026-09-20).
FY = 4200.0        # kgf/cm2
PHI_FLEXION = 0.90
PHI_TRACCION = 0.90
PHI_COMPRESION_ESTRIBOS = 0.70
PHI_CORTANTE = 0.85
REC_CONTRA_SUELO = 0.070   # m, Art. 7.7.1.a
REC_VIGAS_COLUMNAS = 0.040 # m, Art. 7.7.1.c
REC_LOSAS = 0.020          # m, Art. 7.7.1.c


def muro(prefijo):
    """Devuelve la fila de MUROS cuyo nombre empieza con `prefijo`."""
    for m in MUROS:
        if m[0].startswith(prefijo):
            return m
    raise KeyError("no hay muro que empiece con %r" % prefijo)


def factor_C(t_p=None, t_l=None):
    """Tabla N.o 6 de la E.030-2026, los cuatro tramos.

    Los periodos son parametros para poder correr la sensibilidad de perfil de
    suelo (script 07) sin reimplementar la formula. Sin argumentos usa los del
    proyecto.
    """
    t_p = T_P if t_p is None else t_p
    t_l = T_L if t_l is None else t_l
    T = HN / C_T
    if T < 0.2 * t_p:   # no-ssot: 0,2 es el coeficiente de la E.030, no el espesor de losa
        return 1 + 7.5 * (T / t_p), T
    if T <= t_p:
        return 2.5, T
    if T < t_l:
        return 2.5 * t_p / T, T
    return 2.5 * t_p * t_l / T ** 2, T


def cortante_unitario(severo=True):
    """V/P para el nivel de sismo pedido."""
    C, _ = factor_C()
    v = Z * U * C * S / R
    return v if severo else v / FACTOR_MODERADO


if __name__ == "__main__":
    C, T = factor_C()
    print("FUENTE UNICA DE VERDAD — resumen")
    print("  LOTE %.2f x %.2f = %.2f m2 | libre %.2f m2 (%.1f %%)"
          % (FRENTE, FONDO_LOTE, AREA_LOTE, AREA_LIBRE, PCT_AREA_LIBRE * 100))
    print("  retiros: frontal %.2f m (%d estacionamientos) | posterior %.2f m"
          % (RETIRO_FRONTAL, N_ESTACIONAMIENTOS, RETIRO_POSTERIOR))
    print("  EDIFICIO %.2f x %.2f = %.2f m2 | pozo %.2f | TECHADA %.2f m2"
          % (FRENTE, FONDO, AREA_EDIFICADA, AREA_POZO, AREA_PLANTA))
    print("  %d pisos x %.2f = %.2f m | T = %.3f s | C = %.2f" % (N_PISOS, H_ENTREPISO, HN, T, C))
    print("  R = %.1f x %.2f x %.2f = %.2f" % (R0, IA, IP, R))
    print("  V/P severo = %.4f | moderado = %.4f"
          % (cortante_unitario(True), cortante_unitario(False)))
    print("  muros: %d (%d en X, %d en Y)"
          % (len(MUROS), sum(1 for m in MUROS if m[1] == "X"), sum(1 for m in MUROS if m[1] == "Y")))
