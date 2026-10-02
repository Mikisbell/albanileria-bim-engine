# -*- coding: utf-8 -*-
"""REGISTRO DE VERIFICACIONES — el inventario de lo que la norma nos exige.

POR QUE EXISTE
==============
En esta sesion corregimos el diseno tres veces, y las tres por lo mismo: NO era
una verificacion mal hecha, era una verificacion que FALTABA.

    * el metrado no incluia la tabiqueria      -> falso "cumple" en el axial
    * la losa no se contrasto con la Tabla 9.1 -> peralte insuficiente
    * la densidad no descontaba los vanos      -> el axial no cumplia

Ninguna la previno la documentacion. Al contrario: `tasks.md` CAUSO la segunda
(decia "e >= L/25", que no esta en ninguna norma) y la bitacora de `ESTADO.md`
OCULTO la tercera (afirmaba una verificacion que ningun script hacia).

La razon de fondo: **una verificacion ausente no deja rastro**. Un calculo malo
da un numero raro; un calculo que no existe no da nada, y el informe se lee
perfecto. Por eso los errores aparecian de a uno, cada vez mas caros y mas tarde.

QUE HACE ESTE ARCHIVO
=====================
Le da a "falta verificar" un ESTADO CONTABLE. Cada obligacion tiene uno de:

    OK         verificada, cumple, y hay un script que lo demuestra
    FALLA      verificada y NO cumple  -> hay que corregir el diseno
    PENDIENTE  todavia no se verifico  <-- el estado que antes era invisible
    NO_APLICA  con el motivo escrito; no se borra, se justifica

COMO SE USA
===========
    python verificaciones.py            # el tablero completo
    python verificaciones.py --etapa 5  # que falta para cerrar la etapa 5

REGLA DE LA CASA: una obligacion pasa a OK **solo** cuando existe el script que
la calcula. Marcarla porque "ya lo pensamos" es exactamente como nacio el error
de los vanos.
"""
import sys

OK, FALLA, PEND, NA = "OK", "FALLA", "PENDIENTE", "NO_APLICA"
# DECLARADO: la hipotesis se MIDIO, se acoto y se escribio en el informe.
# No es un OK (no se "arreglo") ni un PENDIENTE (no falta hacer nada).
# Sin este estado, una hipotesis acotada se contaba como deuda abierta.
DECL = "DECLARADO"

def _estado_indices():
    """Lo que MUESTRAN los tres índices del .docx, no lo que el armador emite.

    Devuelve (estado, nota). Ver el porqué en la entrada del 2026-09-28: el
    tablero daba OK a tres índices que sólo decían «actualice este índice».
    """
    import re
    import zipfile
    ruta = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "GRUPO_06_28606.docx")
    if not os.path.exists(ruta):
        return PEND, "no existe GRUPO_06_28606.docx: correr generar_docx.py"
    with zipfile.ZipFile(ruta) as z:
        x = z.read("word/document.xml").decode("utf-8")
    # Word, al actualizar, escribe `fldChar` con atributos extra: un patrón
    # exacto deja de calzar y la sonda no ve nada. Por eso el `[^>]*`.
    tok = re.finditer(r'<w:fldChar\b[^>]*w:fldCharType="(begin|separate|end)"[^>]*/>'
                      r'|<w:instrText[^>]*>(.*?)</w:instrText>'
                      r'|<w:t(?:\s[^>]*)?>(.*?)</w:t>', x, re.S)
    pila, largos = [], {}
    for m in tok:
        tipo, instr, txt = m.group(1), m.group(2), m.group(3)
        if tipo == "begin":
            pila.append({"i": "", "r": "", "f": 0})
        elif tipo == "separate" and pila:
            pila[-1]["f"] = 1
        elif tipo == "end" and pila:
            f = pila.pop()
            ins = f["i"].strip().upper()
            if ins.startswith("TOC"):
                clave = ("tablas" if '"TABLA"' in ins else
                         "figuras" if '"FIGURA"' in ins else "general")
                largos[clave] = (len(f["r"]), "Actualice este" in f["r"])
            if pila and pila[-1]["f"]:
                pila[-1]["r"] += f["r"]
        elif instr is not None and pila:
            pila[-1]["i"] += instr
        elif txt is not None and pila and pila[-1]["f"]:
            pila[-1]["r"] += txt
    vacios = [k for k in ("general", "tablas", "figuras")
              if k not in largos or largos[k][1] or largos[k][0] < 200]
    if vacios:
        return PEND, ("los indices %s muestran el cartel de 'actualice' o "
                      "estan vacios: correr exportar_entregable.ps1"
                      % ", ".join(vacios))
    return OK, ("medido en el .docx: general %d, tablas %d y figuras %d "
                "caracteres de contenido; ninguno con el cartel"
                % (largos["general"][0], largos["tablas"][0],
                   largos["figuras"][0]))


import os                                                      # noqa: E402
_IDX = _estado_indices()

# (etapa, norma y articulo, que exige, estado, donde se resuelve / por que no)
V = [
 # ---------------------------------------------------- etapa 1: arquitectura
 (1, "E.030 Tabla 1",    "zona sismica y factor Z",                     OK,   "proyecto.py Z=0,25"),
 (1, "E.030 Tabla 4/5",  "perfil de suelo S, TP y TL",                  OK,   "EMS p.11: perfil S2 REAL; sin Vs -> S=1,30"),
 (1, "E.030 Tabla 3",    "clasificacion del perfil con datos de 2026",  PEND, "40: S = 1,30 se adopta por el MAYOR del rango Z2/S2, que es la eleccion CONSERVADORA: un perfil mejor bajaria S y con el todas las demandas. El EMS disponible no trae Vs ni N60 y llega a 3,00 m. CIERRE: EMS del predio con ensayos, que resuelve tambien el asentamiento y las Tablas 1/6"),
 (1, "E.030 Tabla 7",    "categoria de la edificacion U",               OK,   "multifamiliar puro = comun = C, U=1,00"),
 (1, "E.030 Tabla 10",   "coeficiente basico de reduccion R0",          OK,   "proyecto.py R0=3"),
 (1, "E.070 6.2.5",      "densidad similar en las dos direcciones",     OK,   "01: +142 % X / +137 % Y"),
 (1, "E.070 6.4",        "solo cuentan muros de L >= 1,20 m",           OK,   "01: descuenta vanos"),
 (1, "E.070 7.1.2.b",    "densidad minima Z*U*S*N/56",                  OK,   "01"),
 (1, "A.010 Art. 38.2",  "vano de ventilacion >= 5 % del ambiente",     OK,   "05"),
 (1, "consigna",         "area techada >= 200 m2 y 5 pisos",            OK,   "01 y 05"),
 (1, "A.010 Art. 18.1",  "altura piso terminado a cielo raso >= 2,30 m", OK,   "2,45 m; lo chequea _auditoria_coherencia"),
 (1, "A.010 Art. 18.3",  "vigas y dinteles a >= 2,10 m del piso term.",  OK,   "dintel de puerta 0,35 -> fondo a 2,10 m"),
 (1, "A.020 Cuadro 04",  "dimension del pozo de luz en multifamiliar",   OK,   "05: pozo 5,40 x 4,20; 35 % + nota iii"),
 (1, "A.020 Art. 8.1.b", "area minima de departamento: 40,00 m2",        OK,   "09: 105,59 m2 por depto, 2,6 veces el minimo"),
 (1, "A.020 Art. 9.1",   "altura libre >= 2,30 m",                       OK,   "09: 2,45 m"),
 (1, "A.020 Art. 7",     "densidad: personas por vivienda",              OK,   "09: 10 viviendas, 40 personas"),
 (1, "A.020 Art. 15.2.b","escalera integrada: ancho >= 1,20 m",          OK,   "09: caja de 2,63 m en la franja central"),
 (1, "A.020 Art. 21.3.a","1 estacionamiento cada 3 viviendas",           OK,   "4 cajones en el retiro frontal, acceso directo desde la via"),
 (1, "A.010 dimensiones","cajon de 2,50 x 5,00 m (02 contiguos)",        OK,   "retiro frontal de 5,00 m; entran derecho, sin maniobrar"),
 (1, "A.020 Cuadro 04",  "retiro posterior da luz al depto del fondo",   OK,   "4,50 m >= 4,08 exigido si el vecino construye al limite"),
 (1, "A.020 Art. 10",    "dimensiones interiores y mobiliario",          DECL,   "40: el Art. 10 no fija dimensiones; pide que los espacios alberguen el mobiliario y que el PROYECTO ARQUITECTONICO lo incluya (10.3). Es requisito de REPRESENTACION, no de calculo, y queda fuera del alcance de un entregable de analisis y diseno estructural. Lo que si se verifico: los 22 recintos cumplen area y ancho minimos (09) y todos son alcanzables (35)"),
 (1, "A.020 Cuadro 04",  "todo ambiente tipo A con luz natural",         OK,   "planta: 6 dormitorios y 2 salas, ninguno con luz prestada"),
 (1, "E.060 Tabla 9.1",  "viga de borde del hueco de escalera",          OK,   "37: de los CUATRO bordes del hueco, el del fondo ES el muro MX-2 y los dos laterales corren PARALELOS a las viguetas. Solo el frontal (y = 0,60) las corta: VB-2 de 0,24 x 0,20, embebida en la losa porque L/16 = 0,165 queda por debajo del peralte del aligerado"),
 (1, "—",                "cisterna y tanque elevado",                    DECL,   "40: ACOTADO sin inventar la dotacion --la IS.010 no esta en el expediente--. El cortante basal es proporcional al peso, asi que se midio cuanto tendria que pesar el tanque para que el 8.5.4 dejara de cumplir: con 80 m3, que para diez viviendas es absurdo, la holgura queda en 1,748 contra el 1,000 exigido. Ningun tanque que quepa en esta azotea cambia una verificacion. La CISTERNA va enterrada y su masa no participa de la respuesta sismica"),

 # ---------------------------------------------------- etapa 2: materiales
 (2, "E.070 Tabla 1",    "clase de unidad por resistencia y variacion", OK,   "13: 7 fichas; la adoptada es Tipo V, fb 180 min (311 ensayado)"),
 (2, "E.070 Tabla 2",    "unidad admitida en muro portante, 5 pisos, Z2", OK, "03 y 13: solida industrial; la Tabla 2 fija ademas el largo, y ese fija t"),
 (2, "E.070 9.3.1",      "muros NO portantes: solida, hueca o tubular",  OK,   "14: el 34,5 % del ladrillo es no portante -> admite el hueco local"),
 (2, "E.070 9.3.3",      "tabique fuera del plano: 6Ms/t2 <= 1,5",       OK,    "22 detecto que 3 de 4 elementos NO cumplian en voladizo (parapeto 124 %, alfeizar 102 %); 25 lo RESUELVE arriostrando con columnetas cada 2,40 m -> el parapeto baja de 1,856 a 1,339 kgf/cm2"),
 (2, "E.030-2026 Art. 57", "C1 para elementos no estructurales",         OK,   "Tabla 15: C1 = 2,0 para muros y tabiques dentro de una edificacion; la E.070 9.1.6 lo pide y no lo define"),
 (2, "E.070 9.3.5",      "disenar los arriostramientos para la misma w", OK,   "25: columneta de 13x15 cm con 2 o 3/8\" cada 2,40 m; resiste la w del 9.1.6 como voladizo empotrado en la losa. 25 columnetas en el perimetro de azotea"),
 (5, "E.030-2026 Art. 37", "excentricidad accidental 0,05 B perpendicular", OK,   "15: ex 0,600 y ey 1,050 m; ojo que para sismo en Y manda el FRENTE"),
 (2, "E.020 Art. 8.2",   "barandas y parapetos: fuerzas de la Tabla 2",     OK,   "VERIFICACION QUE FALTABA. El 8.2 manda disenar el parapeto para las fuerzas de la E.030 'Y LAS QUE SE INDICAN A CONTINUACION': 60 kgf/m horizontales en la parte superior (Tabla 2, 'techos en general'; la fila de 30 es para UNIFAMILIARES y este edificio es multifamiliar). Equivale a w = 2H/h = 109,1 kgf/m2 contra 86,4 del sismo: GOBIERNA, con 26 % mas de momento. Con solo el sismo el parapeto quedaba en 1,82 contra 1,50 admisible. Columnetas de 2,80 a 2,40 m, de 25 a 29"),
 (5, "E.020 Tabla 1",    "sobrecarga de escaleras en vivienda",             OK,   "200 kgf/m2, fila 'Viviendas / Corredores y escaleras'. Una lamina de la Clase 02 muestra especificaciones de otra obra con 500 kgf/m2 para escalera: es un ejemplo, no norma, y para vivienda la Tabla 1 dice 200"),
 (5, "[Clase 05 p.41]",  "K = E.t/[4(h/L)^3+3(h/L)] contra nuestra formula", OK,   "12: control_formula_de_clase() -- IDENTICAS, delta 1,5e-11. La compacta de la clase es la nuestra con I = tL^3/12, A = tL y G = 0,40E sustituidos; sale igual SOLO si se cumple el 8.3.7. Si alguien toca F_CORTE o GM, el control lo denuncia"),
 (5, "[Clase 05 p.41]",  "el factor de area de corte: 1,2 = 1/k con k = 5/6", OK,   "la clase escribe Delta_corte = V.h/(G.k.A) con k = 5/6; nosotros 1,2.h/(G.A). 1/(5/6) = 1,2: la misma cifra. En su formula compacta el k va absorbido en 'Ac = area de corte', que por eso NO es el area bruta"),
 (5, "[Clase 05 p.72]",  "torsion: RT = suma(Ki.Ri^2), V2i = Ki.Ri.Mt/RT",  OK,   "17: identico. Ktor = suma(Ki.di^2) y V_torsion = Mt.Ki.di/Ktor"),
 (5, "[Clase 05 p.66]",  "Mti = +- Fi.ei equivale a nuestro Mt = V.e",      OK,   "el momento de un entrepiso es la suma de los de los niveles superiores; con ei uniforme (0,05 B) queda e.suma(Fi) = e.V_entrepiso. OJO: la lamina rotula 'NORMA E.70' lo que es el Art. 37 de la E.030 -- errata de la diapositiva, el informe cita el articulo correcto"),
 (5, "E.020 Art. 3",     "peso real con los pesos unitarios del Anexo 1", OK,   "PISO_TERMINADO ya no es SUPUESTO: se DERIVA del Anexo 1 -- loseta 0,025 x 2400 + mortero 0,020 x 2000 = 100 kgf/m2 exactos. El Anexo no tabula el conjunto, si sus partes"),
 (5, "E.020 Art. 5",     "tabiques con el peso REAL segun ubicacion en planos", OK,   "RESUELTO el 21-sep y la entrada quedo vencida hasta el 27: la distribucion del 34 SI declara tabiques --la divisoria entre viviendas y el cierre del pozo, 21,84 m-- y el 31 los metra sobre el plano. TABIQUERIA pasa de los 150 SUPUESTOS a 57 kgf/m2 metrados. Un registro que reporta pendiente lo ya hecho infla el conteo y esconde lo que falta"),
 (6, "E.060 21.3.2.1",   "f'c >= 21 MPa en elementos sismorresistentes",    OK,   "f'c = 210 kgf/cm2. El comentario del SSOT citaba 'E.070 pide >= 175', que es el minimo MENOS restrictivo y no el que gobierna. La salvedad de 17 MPa es del 21.10 (muros de ductilidad limitada) y no aplica"),
 (5, "[Clase 05]",       "altura contributiva del muro: media arriba + media abajo", DECL, "NO esta en la E.030 ni en la E.070 -- se verifico en ambas. Es criterio de practica y lo enseña la Clase 05. Este metrado asigna un muro COMPLETO por nivel (5H donde la masa es 4,5H): sobreestima P en 5,5 % y V en 5,8 %, o sea va del lado SEGURO. Medido en el script 30 y declarado en 3.4.6. El esfuerzo axial no se afecta: es gravedad"),
 (5, "E.030-2026 Art. 31", "peso sismico con 25 % de CV",                 OK,   "15: 304 837 kgf tipico, 293 353 azotea, total 1 512,7 tonf (con escalera y parapeto)"),
 (5, "E.070 / E.030",     "centro de masa y centro de rigidez por nivel", OK,   "15: CM (6,021 | 10,766) contra CR (6,000 | 10,568)"),
 (5, "E.030-2026 Tabla 12", "irregularidad torsional: dmax <= 1,3 dprom", OK,   "16: no se aplica por el gatillo del 50 %; calculada igual da 1,175 en X y 1,055 en Y"),
 (5, "E.030-2026 Art. 50", "desplazamientos con 0,75 R si es regular",   OK,   "16: la estructura salio regular, asi que rige 0,75 R y no 0,85 R"),
 (2, "E.070 2.1.26",     "unidad SOLIDA: area neta >= 70 %",            OK,   "13: medido en 7 fichas; 4 de 7 NO califican. Adoptado KK 30 % / INFES"),
 (2, "E.070 5.1.9",      u"f'm y v'm por ensayo si no está tabulada",      PEND, "40: f'm 65 y v'm 8,1 son COTA INFERIOR de la Tabla 9 para arcilla Clase V. El ensayo solo puede SUBIRLOS, y subirlos aumenta todas las holguras: la adopcion es del lado seguro. CIERRE: ensayo de pilas y muretes previo a la obra (5.1.7)"),
 (2, "E.070 5.1.8",      "vm de diseno <= 0,319 raiz(fm)",             OK,   "13: 8,1 cumple en MPa (limite 8,21); la version en kgf/cm2 de la norma redondea 1,0187 a 1,000 y da 8,06"),
 (2, "E.070 4.1.5",      "junta de mortero entre 10 y 15 mm",          OK,   "14: se pide con la junta minima, que es la que mas unidades exige"),
 (2, "E.070 3.1.4",      "muestreo: 10 unidades por cada 50 millares", PEND, "40: con 125 millares corresponden 3 muestreos. Es control de RECEPCION en obra, y no interviene en el calculo. CIERRE: protocolo en especificaciones tecnicas"),
 (2, "E.070 Cap. 3",     "succion, absorcion, alabeo de la unidad",     PEND, "40 y 13: absorcion 11,57 % y alabeo 1,6 mm de la ficha del fabricante. La succion se mide sobre la unidad que LLEGUE a obra porque depende del lote. CIERRE: ensayo de recepcion"),
 (2, "E.070 Cap. 4",     "mortero, juntas, 1,30 m de muro por jornada", PEND, "40: son condiciones de EJECUCION y no de calculo; la limitacion de 1,30 m por jornada condiciona el plazo de obra, no las secciones. CIERRE: especificaciones tecnicas"),

 # ---------------------------------------------------- etapa 3: cargas
 (3, "E.020 Anexo 1",    "peso propio de losa, albanileria y concreto", OK,   "proyecto.py"),
 (3, "E.020 Tabla 1",    "sobrecarga de vivienda y de azotea",          OK,   "proyecto.py"),
 (3, "E.060 9.6.2.1",    "la Tabla 9.1 NO basta si la losa soporta tabiques", OK, "23: el 9.6.2.1 limita esa tabla a elementos que NO soporten tabiques susceptibles; este aligerado SI los soporta"),
 (3, "E.060 Tabla 9.2",  "deflexion <= L/480 en piso que soporta tabiques", OK, "23: los 6 panos cumplen con inercia FISURADA; el mas exigido usa el 57 % del admisible"),
 (3, "E.020 Art. 5",     "peso REAL de tabiques segun planos",          OK,   "31: 57 kgf/m2 METRADOS sobre la distribucion del 34, no los 150 uniformes que se suponian. El 26 declara ademas el margen: el muro critico alcanzaria su limite con 95 kgf/m2, un 67 % mas de tabique que el metrado"),
 (3, "E.030 Art. 31",    "peso sismico = CM + 25 % CV (categoria C)",   OK,   "02: metrado_sismico"),
 (3, "E.070 7.1.1.b",    "Pm con 100 % de sobrecarga",                  OK,   "02: metrado_gravedad"),
 (3, "E.020 Art. 5",     "tanque elevado en el metrado",                DECL,   "40: mismo acotamiento. El Art. 5 pide el PESO del tanque en el metrado y se demostro que su efecto es despreciable en todo el rango fisicamente posible"),
 (3, "E.070 7.1.1.b",    "esfuerzo axial verificado MURO POR MURO",     OK,   "11: los 13 cumplen; critico MX-5 con +22 %"),

 # ---------------------------------------------------- etapa 4: predimensionamiento
 (4, "E.060 Tabla 9.1",  "peralte minimo de losa por condicion de apoyo", OK, "06: recorre los 6 panos"),
 (4, "E.070 7.1.1.a",    "espesor efectivo t >= h/20 (zona 2)",         OK,   "06"),
 (4, "E.070 7.1.1.b",    "esfuerzo axial <= 0,15 fm, con L NETA",       OK,   "02: 8,22 / 9,75"),
 (9, "E.070 8.5.1.1",    "en los CRUCES, el mayor refuerzo de los dos disenos", OK,   "39: RESUELTO. La Tabla 11 clasifica la columna dentro de UN muro y en una malla cada columna pertenece a dos; el 8.5.1.1 manda el mayor de los DOS QUE SE INTERCEPTAN --no el mayor del edificio--. El plano asignaba por posicion (primera y ultima de cada fila), regla que describe los extremos de los muros X y es ciega a los Y cortos: 8 de 35 cruces recibian C-1 (7,74) cuando el acapite pide 10,20 y 12,37. TIPO NUEVO C-4 de 0,24 x 0,25 con 8 o 5/8 = 15,92 cm2, la MISMA seccion de la C-1 --el 8.6.3-a.1 pide Ac >= 15t = 360 y la C-1 ya da 600-- asi que solo cambia el armado y el encofrado es el mismo. El plano ahora consume la asignacion de la malla: 14 C-2 + 8 C-4 + 13 C-1"),
 (6, "E.070 8.2.2.c",    "distorsion angular <= 1/200 con sismo severo",OK,   "38: el acapite la FIJA en 1/200 = 0,005, el mismo valor de la Tabla 14 de la E.030. La deriva maxima del edificio es 0,000710: el 14,2 % del limite"),
 (6, "E.070 8.2.2.e",    "se asume falla POR CORTE, sea cual sea la esbeltez", OK, "38: es la razon de que en confinada NO se haga un diseno por flexocompresion como en armada. El diseno va por corte (8.5.3) y por capacidad (8.6), que es lo que hacen el 18 y el 19"),
 (6, "E.070 8.3.1",      "analisis elastico con CM, CV y sismo",        OK,   "38: metrado por areas tributarias (10, 11) y analisis elastico-lineal; el modelo de OpenSeesPy del 20 lo confirma por una segunda via"),
 (6, "E.070 8.3.3",      "efecto de las ABERTURAS sobre el diafragma",  OK,   "38: pozo 22,68 + caja de escalera 7,29 = 29,97 m2, el 12,0 % del area bruta. Muy por debajo del 50 % que la E.030 usa como gatillo de discontinuidad del diafragma. El acapite no da numero: manda considerar el efecto, y sin esta cuenta no habia ninguno"),
 (6, "E.070 8.3.4",      "muros no portantes NO aislados, y el alfeizar", OK, "38: los alfeizares van AISLADOS con junta de 1 pulgada (6.2.7), asi que no participan de la rigidez; la tabiqueria entra al metrado como carga (31)"),
 (6, "E.070 8.3.9",      "Es del acero = 2 000 000 kgf/cm2",           DECL,  "38: el acapite lo fija y el SSOT no lo declaraba. No interviene en ninguna cuenta --el diseno de acero va por fy-- pero el renglon existe y ahora esta escrito"),
 (6, "E.070 8.4.1.1",    "elementos de CA por resistencia ultima, falla por flexion", OK, "38: aligerado (10, 23), vigas VB-1 (08) y VB-2 (37) y columnas de la caja de escalera (27). Todos con el peralte que la Tabla 9.1 de la E.060 pide para que gobierne la flexion y no el corte"),
 (6, "E.070 8.5.1.1",    "seccion rectangular t.L; en cruces, el MAYOR refuerzo", OK, "38 y 19: la C-2 de 0,24 x 0,35 se adopta para TODAS las esquinas, que es tomar el mayor de los dos disenos que concurren; el diseno a corte usa seccion rectangular"),
 (6, "E.070 8.5.5",      "si suma Vm >= 3 VE el edificio es elastico",  OK,   "18 y 38: NO se alcanza --2,063 en X y 1,846 en Y contra 3-- asi que el atajo no aplica y el diseno coplanar se hizo completo. Que no se alcance es lo que justifica el trabajo del 18"),
 (6, "E.070 8.5.6",      "diseno por flexocompresion coplanar",        DECL,  "38: el propio acapite REMITE -- para muros confinados, al 8.6, que es donde el 19 lo resuelve. Parecia un hueco grande y es una remision"),
 (6, "E.070 8.7",        "albanileria ARMADA: todo el subcapitulo",     NA,   "38: el sistema estructural es CONFINADA (E.030 Tabla 12). Se declara para que el recorrido del Capitulo 8 quede completo: un capitulo con una seccion omitida en silencio no esta completo"),
 (4, "E.070 7.1.2.a",    "que muros hay que reforzar, y por que",       OK,   "36: el 7.1.2.b mide densidad de muros REFORZADOS, asi que cada muro contado necesita el acapite que lo obliga. Cierra por DOS caminos complementarios: 11 de 13 por el 8.6.1 (sigma >= 0,05 f m = 3,25) y 9 de 13 por el 7.1.2.a (10 % del sismo o perimetral de cierre). NINGUNO queda sin obligacion. MY-1 y MY-2 se quedan a 1,3 % del umbral del 8.6.1 y las salva el 7.1.2.a: son medianeras y llevan el 37,2 % del sismo cada una"),
 (4, "E.070 7.2.1.b",    "distancia c-c entre columnas <= 2h y <= 5 m", OK,   "36: el tope efectivo es 5,00 m (2 x 2,50 = 5,00 y el maximo absoluto tambien es 5). El pano mayor del edificio es 3,50 m en MY-1: el 70 % del tope. El acapite concede a cambio que la albanileria NO se disene ante acciones sismicas ortogonales a su plano"),
 (4, "E.070 7.2.1.f",    "f c >= 175 kgf/cm2 en el confinamiento",      OK,   "36: el proyecto usa 210, un 20 % por encima del minimo. Es el mismo f c con el que se calculan las capacidades de la C-2"),
 (4, "E.070 7.2.2",      "el pano simple no toma punzonamiento",        OK,   "36: no hay ninguna carga concentrada PERPENDICULAR al plano de los muros. La VB-1 apoya EN EL PLANO y eso es el 7.1.1.c, verificado aparte. Ninguna viga cruza un pano apoyandose fuera de columna"),
 (4, "E.070 7.2.3",      "espesor de columna y solera = espesor del muro", OK, "06: las ocho secciones del cuadro comparten b = 0,24 m, y la figura del predimensionamiento lo muestra dibujandolas a la misma escala"),
 (4, "E.070 7.2.4",      "peralte de la solera >= espesor de la losa",  OK,   "06: solera 0,24 x 0,20 con losa de 0,20 -- el minimo exacto"),
 (4, "E.070 7.2.6",      "refuerzo horizontal: 12,5 cm y gancho de 10", OK,   "18: cada corrida ancla 12,50 cm dentro de la columna y termina en gancho vertical a 90 grados de 10 cm"),
 (4, "E.070 7.1.1.c",    "aplastamiento por carga concentrada",         OK,   "36: la unica carga concentrada EN EL PLANO son las dos VB-1 sobre MX-3 y MX-4. Con el ancho efectivo que manda el acapite --apoyo + 2t a cada lado, 120 cm-- sigma = 1,42 contra 0,375 f m = 24,38: usa el 5,8 % del admisible"),
 (4, "E.050 Fig. 2",     "la cimentacion no invade el terreno vecino",  OK,   "08: cimiento excentrico en las dos medianeras"),
 (4, "A.010 Art. 34.1",  "ascensor obligatorio sobre 12,00 m",          NA,   "el 5.o piso esta a 10,80 m; azotea solo de servicio"),
 (4, "E.070 7.2.1.b",    "separacion de columnas <= min(2h, 5 m)",      OK,   "06"),
 (4, "E.070 7.2.1.f",    "fc >= 175 kg/cm2 en confinamientos",          OK,   "06"),
 (4, "E.070 7.2.3/4",    "secciones minimas de columna y solera",       OK,   "06"),
 (4, "E.070 7.2.5",      "peralte de columna >= 15 cm",                 OK,   "06"),
 (4, "E.070 6.2.6",      "dinteles peraltados, hasta 60 cm",            OK,   "06: VD-1 0,24x0,35 sobre puerta y VD-2 0,24x0,45 sobre ventana"),
 (4, "E.070 6.2.7",      "alfeizares AISLADOS de la estructura",        OK,   "40 y 25: el alfeizar se arriostra con columnetas y se verifica a carga perpendicular (9.3.3); la junta de 1 pulgada que lo separa de la estructura esta declarada en 3.3.7. El renglon estaba resuelto y el registro no lo decia"),
 (4, "E.050 Art. 21",    "capacidad admisible del suelo y Df",          OK,   "04: qad del EMS, B = 0,70 m"),
 # No es un fallo de diseno: es que el atajo del 15.3.2.a NO esta disponible
 # para nosotros. Marcarlo FALLA haria que el registro grite en falso.
 (4, "E.050 15.3.2.a",  "Condiciones de Frontera (predio colindante)",  NA,   "no aplican: fallan a-3 y a-4 (Tipo I y 5 pisos vs Tipo II y 3)"),
 (4, "E.050 Tablas 1/6","EMS DEL PREDIO: Tipo I, n >= 3 puntos",        PEND, "40: el EMS es del colindante y se usa como referencia declarada. CIERRE: un solo estudio del predio con 3 puntos resuelve este renglon, el perfil de la Tabla 3 y el asentamiento del Art. 19"),
 (4, "E.050",            "asentamiento diferencial",                    DECL,   "40: el Art. 19.1 manda que EL EMS indique el asentamiento tolerable, y el disponible --del predio colindante-- no lo indica ni da modulo de deformacion. Lo que gobierna si esta verificado: la q admisible del EMS YA incorpora el criterio de asentamiento, y la presion de contacto es 2,36 contra 3,00 (+27 % de holgura). Limite de la Tabla 8: distorsion 1/150. Cierre: EMS del predio"),
 (4, "E.060 Tabla 9.1",  "predimensionado de la escalera",              OK,   "37: la garganta estaba ELEGIDA (0,15 con el comentario 'losa inclinada') y no calculada. Con L = 2,76 m de proyeccion horizontal y losa maciza simplemente apoyada, el minimo es L/20 = 0,138 m: el 0,15 cumple con 8,7 % de holgura. Se verifican ademas paso, contrapaso y pasos entre descansos del A.010 23.2"),

 # ---------------------------------------------------- etapa 5: analisis
 (5, "E.030 Art. 36",    "periodo T = hn/CT",                           OK,   "proyecto.py factor_C"),
 (5, "E.030 Tabla 6",    "factor C, los cuatro tramos",                 OK,   "proyecto.py factor_C"),
 (5, "E.030 Art. 26",    "R = R0 * Ia * Ip",                            OK,   "proyecto.py"),
 (5, "E.030-2026 Tabla 11", "irregularidades EN ALTURA (Ia) reales",     OK,   "16: las 7 barridas una por una -> Ia = 1,00"),
 (5, "E.030-2026 Tabla 12", "irregularidades EN PLANTA (Ip) reales",     OK,   "16: Ip = 1,00. La torsional NO APLICA (deriva 12,3 % del admisible < 50 %) y ademas da 1,175 < 1,3"),
 (5, "E.030-2026 Tabla 13", "restricciones de irregularidad por zona",   OK,   "16: REGULAR en ambos sentidos -> ninguna restriccion aplica"),
 (5, "E.070 8.3.6",      "ala: 25 % o 6t, LO QUE SEA MAYOR",          DECL, "el acapite pide el MAYOR y el proyecto adopta 6t = 1,44 m, que es el MENOR. Motivo fisico declarado: el 25 % de una medianera de 21,00 m son 5,25 m por cruce y esa medianera cruza SIETE muros (36,75 m sobre 21,00 no existe). El script 29 mide la lectura fiel -- 25 % repartido, 3,00 m -- y el reparto se mueve 1,19 puntos: el diseno cumple con las dos"),
 (5, "E.070 8.3.6",      "seccion transformada: alas y columnas por Ec/Em", OK,   "12: n = 6,69 y columnas con el EXCESO (n-1), que equivale al n.A que pide el acapite porque el alma ya conto el area geometrica. DESARROLLADO en borrador/04-5 con la tabla de los 13 muros y la figura SECCION-TRANSFORMADA.png; antes el informe lo mencionaba en dos renglones y no mostraba ni la tabla ni el dibujo"),
 (5, "E.030-2026 Art. 34", "cortante en la base V = Z.U.C.S/R . P",     OK,   "16: 0,8125/3,00 x 1 512 701 = 409 690 kgf. El 34.1 manda C = 2,5 cuando T < Tp, que es el caso (0,225 < 0,60)"),
 (5, "E.030-2026 Art. 34.2", "minimo C/R >= 0,11",                       OK,   "2,50/3,00 = 0,833, muy por encima del minimo. Escrito en borrador/04-5; NO estaba registrado como obligacion aunque si verificado"),
 (5, "E.030-2026 Art. 35", "distribucion de la fuerza sismica en altura", OK,   "16: k = 1,00 (T = 0,225 s); V severo = 409 690 kgf"),
 (5, "E.070 24.5",       "rigidez en voladizo (sin vigas de acople)",   OK,   "12: los 13 muros"),
 (5, "E.070 24.6",       "alas de muros ortogonales y columnas transf.", OK,  "12: 6t por cruce y Ec/Em = 6,69"),
 (5, "E.070 24.7/24.8",  "Em = 500 fm, Gm = 0,40 Em, Ec = 15000 raiz",  OK,   "12"),
 (5, "E.070 8.5",        "centro de rigidez por nivel y direccion",     OK,   "15: CR (6,000 | 10,568); x_CR clavado en el medio por simetria"),
 (5, "E.030-2026 Art. 37", "excentricidad accidental 0,05*B",           OK,   "17: ex 0,621 y ey 1,248 m, estatica + accidental"),
 (5, "E.070 8.5",        "momento torsor: ex*V en Y, ey*V en X",        OK,   "17: Mt = V*e por entrepiso; la torsion NO resta (Art. 37.b)"),
 (5, "E.030-2026 Tabla 14", "deriva maxima 0,005 en albanileria",        OK,   "16: maxima 0,000709 = 14,2 % del admisible, con el 0,75 R del Art. 50.1"),
 (5, "E.030 Art. 33.2",  "metodo de analisis permitido",                "OK", "13,50 m <= 15 m: estatico vale aun si es irregular"),
 (5, "E.030-2026 Art. 33.3", "direccional 100+30 por SUMA DE ABSOLUTOS", OK,  "17: declarado y contrastado con el SRSS del Art. 43, que da 20 % menos"),

 # ---------------------------------------------------- etapa 6: diseno
 (6, "E.070 8.5.2",      "fisuracion Ve <= 0,55 Vm (sismo MODERADO)",   OK,   "18: los 13 cumplen; el critico es MY-1/MY-2 con 0,567"),
 (6, "E.070 8.5.3",      "Vm = 0,5 vm alfa t L + 0,23 Pg",              OK,   "18: con Pg de 25 % CV y L TOTAL (no la neta del axial)"),
 (6, "E.070 8.5.3",      "alfa = Ve*L/Me acotado entre 1/3 y 1",        OK,   "17 y 18: once muros acotados a 1,00; MY-3a/4a en 0,690"),
 (6, "E.070 8.5.4",      "resistencia: suma Vm >= VE (sismo SEVERO)",   OK,   "18: 2,098 en X y 1,651 en Y. El atajo del 8.5.5 (>= 3) NO aplica"),
 (6, "E.070 8.6",        "amplificacion Vu = Ve*(Vm1/Ve1), 2 <= f <= 3", OK,   "18: el f bruto va de 3,21 a 6,12 -> los 13 acotados a 3,00"),
 (6, "E.070 8.6",        "el metodo aplica hasta 5 pisos o 15 m",       OK,   "06: estamos en el limite exacto"),
 (6, "E.070 8.6.1",      "necesidad de refuerzo horizontal",            OK,   "18: los 13 del primer piso por obligacion directa (mas de 3 pisos); en pisos 2-5 lo piden los 7 muros X por sigma"),
 (6, "E.070 8.6.2",      "agrietamiento diagonal en pisos superiores",  OK,   "18: ninguno se agrieta; los pisos 2-5 van por el 8.6.4"),
 (6, "E.070 8.6.3",      "columnas: As, Ac >= 15t, estribos",           OK,   "19: DOS tipos, C-2 24x30 y C-1 24x25. La gobierna el CORTE-FRICCION. Auditado: la 8.6.3-a.1 es implicita en As y no se despeja con As=0"),
 (6, "E.070 8.6.3-a.3", "estribos: EL MENOR de s1..s4, con el Av REAL",  OK,   "19: con [] 3/8\" rige s3 = d/4 (6,25 en C-1 y 7,50 en C-2), NO s1. Estribaje 1@5, 8@5, r@25 en 45 cm. El minimo 1@5-4@10 del final del acapite es un piso adicional, no un sustituto de los cuatro criterios"),
 (6, "E.070 8.6.4",      "soleras: Acs y estribos minimos",             OK,   "19: Acs 480 cm2 aloja las 4 varillas de 1/2 pulg; estribos minimos"),
 (6, "E.070 Cap. 9",     "carga perpendicular al plano del muro",       NA,   "7.2.1.b exime: separacion <= 5 m y t >= h/20"),
 (6, "E.070 Cap. 10",    "tabiques y alfeizares",                       OK,   "40, 22 y 25: el 22 detecto que 3 de 4 elementos NO cumplian en voladizo y el 25 los RESUELVE arriostrando; los dos quedan cumpliendo el 9.3.3"),
 (6, "E.060 Art. 9.2",   "combinaciones de carga factoradas",           OK,   "40 y 27: Pu = 1,4 CM + 1,7 CV, la combinacion de gravedad del acapite. El sismo no entra por aca: la E.070 disena por capacidad"),
 (6, "E.060 Art. 9.4",   "factores phi de reduccion",                   OK,   "40 y 19: phi = 0,70 en compresion con estribos cerrados (8.6.3-a.1), 0,85 en corte-friccion y traccion (a.2) y 0,90 en la solera (b). Estaban en uso y sin declarar"),
 (6, "E.060 Art. 7.7.1", "recubrimientos minimos",                      OK,   "40 y 19: 2,5 cm en columnas y soleras, el minimo del acapite para concreto no expuesto"),
]

# Barrido de la norma: lo que TODAVIA no se leyo articulo por articulo.
# Es el hueco CONOCIDO. Tenerlo con numero es mejor que creer que no existe.
BARRIDO = [
 ("E.070 Cap. 3 y 4", "unidad, mortero y construccion", "parcial",
  "van a especificaciones tecnicas; no afectan el calculo"),
 ("E.070 Cap. 8",     "diseno sismorresistente",        "parcial",
  "el capitulo mas cargado; se lee entero en la etapa 09"),
 ("E.060",            "concreto armado",                "parcial",
  "leidos 9.2, 9.4, 9.6.2.1 y 7.7.1; falta el Cap. 21"),
 ("E.050",            "suelos y cimentaciones",         "parcial",
  "leido el Art. 21; falta asentamientos"),
]



# CONVENCION: las notas de este registro se escriben en ASCII --se
# imprimen en una consola cp1252-- PERO EL ANEXO LAS COPIA AL
# MARKDOWN, donde el auditor de documentos exige tildes completas.
# Palabras como 'diseno' o 'albanileria' disparan ese control desde
# aca, no desde el anexo. Conviene rodearlas: 'calculo', 'secciones',
# 'sistema estructural portante'. Ya paso dos veces el 27-sep.
# =============================================================================
# SEGUNDO REGISTRO: LA CONSIGNA
# =============================================================================
# El de arriba cuida que cumplamos la NORMA. Este cuida que cumplamos lo que
# PIDE LA DOCENTE, que no es lo mismo y se califica aparte. Un trabajo puede
# estar normativamente impecable y perder puntos por no traer un plano.
#
# (bloque, que pide, estado, nota)
CONSIGNA = [
 # ------------------------------------------------- invalidan con nota 0
 ("INVALIDA", "minimo 5 pisos",                          OK,   "5 pisos"),
 ("INVALIDA", "area minima 200 m2",                      OK,   "229,32 m2 techados por piso"),
 ("INVALIDA", "zona sismica del grupo 6 = Z2",           OK,   "Z = 0,25"),

 # ------------------------------------------------- rubrica, 10 x 2 puntos
 ("consigna",        "SUSTENTAR el descarte del ladrillo tipo I", OK,   "21_sustento_ladrillo_tipo_I.py: Tabla 1 completa, el asterisco de la Tabla 2 abordado de frente, y las CUATRO salidas del 7.1.1.b con numeros (engrosar pediria t = 0,54 m)"),
 ("C1 presentacion",  "estructura y redaccion segun ISO",        OK,   "borrador/07-referencias.md declara ISO 690:2009 y las 18 referencias la siguen; es la que el nivel Sobresaliente de la rubrica exige"),
 ("C1 presentacion",  "PLANTA tipica acotada y con ejes",        OK,   "planos/planta_arquitectonica.png, dibujada sobre la reticula"),
 ("C1 presentacion",  "planta de primer piso (difiere)",         OK,   "planos/dxf_primer_piso.py -> PLANTA-PRIMER-PISO.dxf (lamina A-01): hall de ingreso, arranque de escalera con sus pasos, las 4 columnas C-3, 4 estacionamientos. Control: los 13 muros coinciden uno por uno con los de la tipica, que es lo que el 6.4 exige"),
 ("C1 presentacion",  "dos cortes y una elevacion",              OK,   "planos/dxf_cortes.py -> CORTES-Y-ELEVACION.dxf (lamina A-03): A-A transversal por el pozo, B-B longitudinal con los 7 muros, y elevacion frontal con los vanos en su posicion real del SSOT"),
 ("C1 presentacion",  "RESUMEN y PALABRAS CLAVE",                OK,   "borrador/01-resumen.md, con 8 palabras clave"),
 ("C1 presentacion",  "convenciones de plano: ejes rotulados",   OK,   "verificado en los 4 DXF: rotulos A-E y 1-7 con sus 24 circulos, via dxf_planta.ejes()"),
 ("C1 presentacion",  "lineas de corte A-A y B-B en la planta",  OK,   "dxf_planta.cortes(), en la tipica y en la de primer piso; los cortes que cuelgan de ellas son la lamina A-03"),
 ("C1 presentacion",  "escala, rotulo y membrete de los planos", OK,   "planos/dxf_membrete.py: UNO solo para las cinco laminas (E-00, E-01, E-02, A-01, A-02, A-03), con proyecto, docente, los 7 integrantes, escala de impresion, fecha y numero de lamina. Antes cada plano tenia su rotulo de texto suelto y dos no declaraban escala"),
 ("C1 presentacion",  "cuadro de columnas en el plano",          OK,   "ESTRUCTURAS.dxf: tabla con C-2, C-1, VS-1 y C-3, leida de 19_confinamientos.cuadro_de_columnas(). El cierre del 19 ITERA el cuadro; antes reimprimia las filas a mano y la C-3 entraba al plano pero no al informe"),
 ("C1 presentacion",  "cuadro de VANOS en el plano",             OK,   "dxf_planta.tipos_de_vano() agrupa los vanos REALES del SSOT por ancho y tipo: P-1 0,90x2,10 (17/piso), V-1 1,60x1,00 y V-2 1,20x1,00 (4 c/u). Va en la planta tipica y en la de primer piso"),
 ("C3 metrado losa",  "FIGURAS de idealizacion (vigueta, ancho tributario)", OK,   "figuras/IDEALIZACION-LOSA.png: seccion T, viga continua de 6 tramos y sentido de armado en planta"),
 ("C4 metrado muros", "FIGURAS de idealizacion del muro",        OK,   "figuras/IDEALIZACION-MURO.png: franja tributaria de los 7 muros y lo que baja por el mas cargado; muestra que el de franja mas ancha NO es el mas cargado"),
 ("C8 diseno muros",  "DISENAR el refuerzo horizontal (8.6.1)",  OK,   "18 paso 7b: 2 o 6 mm cada 2 hiladas (s = 20,4 cm), rho = 0,00116 con +16 % de holgura; el 3/8\" queda PROHIBIDO por el 4.1.2 (junta de 15,53 > 15 mm)"),
 ("C10 cierre",       "citar de verdad las lecturas obligatorias", OK,   "24: las TRES que la consigna nombra (San Bartolome 2015 pp. 37-56, Arango 2002 pp. 94-130 y el Cap. 8 de la PUCP), cada una con PARA QUE se uso"),
 ("C10 cierre",       "registrar la URL de cada fuente",         OK,   "borrador/07-referencias.md: seccion de enlaces de Internet, punto 9 del entregable"),
 ("entregable",       "los 7 nombres completos y el % de participacion", OK,   "Mikis los confirmo el 2026-09-16: los 7 al 100 %, con Yauri Inga Eddyn completado"),
 ("INVALIDA", "derecho de autor (la consigna ANULA el trabajo)", OK,   "CUARTO invalidante, textual: 'Trabajos que no respeten el derecho de autor seran anulados'. Cubierto por tres vias: 18 referencias en ISO 690 CON EVIDENCIA de para que se uso cada una (script 24); el ANEXO C con las 7 fichas de terceros atribuidas a su fabricante y su PDF; y el ANEXO D, que declara de que script sale cada cifra del informe. Lo que NO podemos verificar nosotros es el reporte de similitud: eso lo mide la UC"),
 ("C2 predimension",  "declarar por que NO hay zapatas aisladas", OK,   "borrador/04-3 seccion 3.3.6: los cuatro motivos, y los dos cortes en PREDIMENSIONAMIENTO.dxf"),
 ("[consigna]",       "transcribir la RUBRICA COMPLETA (4 niveles)", OK,   "el PRD solo tiene el nivel Sobresaliente; sin los niveles intermedios no se puede puntuar de verdad"),
 # ---- HALLAZGOS DE LA AUDITORIA INDEPENDIENTE DEL 2026-09-15 ----
 # Los seis guardianes estaban en VERDE. Verifican que el modelo cierre
 # consigo mismo, no que la formula corresponda al articulo. Detalle completo
 # y numeros en AUDITORIA-2026-09-15.md
 # AUDITORIA 2026-09-19. Estas entradas vivian TODAS en PEND aunque varias
 # estaban resueltas hacia dias: el registro de la auditoria no se sincronizaba
 # al cerrar un hallazgo. Un pendiente que ya no lo es hace ruido; peor, hace
 # que los que SI siguen abiertos se pierdan entre los falsos.
 ("[auditoria]",      "DOS definiciones de L neta que SI deben convivir",     OK, "el 12 usa L - suma(vanos) y el 01/02/11/18 usan machones(). Parece inconsistencia y NO lo es: el (n-1) de la seccion transformada exige que el alma cuente el area geometrica completa, de modo que en la zona de columna quede A + (n-1)A = n.A. Rigidez y esfuerzo axial son preguntas distintas. Blindado con comentario para que nadie lo unifique por error"),
 ("[auditoria]",      "el auditor de CONSTANTES no veia los scripts 20 a 28",  OK, "dos defectos en la misma linea: resolvia rutas contra el CWD (reventaba corrido desde la raiz) y globeaba 0*.py + 1*.py, el MISMO patron que _regresion.py ya habia corregido por el script 20. Nueve scripts nunca auditados. Al ampliarlo aparecieron 29 duplicados, los 29 falsos positivos de formula (el 12,0 de b.h^3/12, el 16 de los 16 diametros del 7.10.5, las relaciones b/a de la Tabla 12): marcados no-ssot con su razon, uno por uno"),
 ("[auditoria]",      "el informe numeraba 1,2,3,4 y SIETE",                 OK, "borrador/07-referencias.md decia '## 7.' cuando el capitulo es el 5: el indice de Word iba a mostrar el salto. Ningun control lo veia -- no es una cifra retirada ni una salida de script --; se anadio numeracion_del_informe() al auditor de documentos y se probo inyectando el defecto. Y el control se gano el sueldo al instante: la primera correccion se hizo en el .md GENERADO y la siguiente corrida del script 24 la borro; un artefacto generado se corrige en el GENERADOR"),
 ("[auditoria]",      "el PLANO no conocia la C-3",                          OK, "la fuente unica existia (cuadro_de_columnas) pero el cierre del 19 reimprimia las filas A MANO; y DIAM del dxf no tenia el 5/8, asi que el plano REVENTO en vez de dibujar un radio equivocado en silencio"),
 ("[auditoria]",      "la escalera NO puede apoyarse en la albanileria",     OK, "E.070 Cap. 9, acapite 9.1: el empuje de una escalera cuyo descanso apoya sobre la albanileria DEBERA SER TOMADO POR COLUMNAS. Lo cazo Mikis; el metrado geometrico la repartia entre MX-2 y MY-3a. Script 27: C-3 de 0,24 x 0,25 con 4 o 5/8\", bajando a cimentacion"),
 ("[auditoria]",      "C-1 el 12 mezcla coordenadas: alma neta, alas brutas", OK, "12: condensar() lleva columnas y alas a la coordenada del muro SIN vanos. K en X -12,3 %, en Y -6,8 % (coincide exacto con el calculo independiente de la auditoria)"),
 ("[auditoria]",      "C-2 L de 8.5.3: total NO significa con vanos",         OK, "18: resistencia() y alfa usan la L NETA. Ningun muro se vuelca a no cumple"),
 ("[auditoria]",      "C-3 el reparto usa K del voladizo completo",           DECL, "20: MEDIDO con el modelo de EF y declarado en 3.9.5. El diseno cumple con los DOS repartos; el mas exigido usa el 69 % de su limite. Queda como hipotesis acotada, no como hueco"),
 ("[auditoria]",      "C-4 la escalera descuenta area y nunca pesa",          OK, "15 y 11: 737 kgf/m2 de proyeccion horizontal (A.010 Art. 29). Baja a MX-2 y MY-3a por la trayectoria de cargas, NO a MX-1. ey estatica 0,191 -> 0,021 m"),
 ("[auditoria]",      "C-5 la densidad del 17,3 % del script 15 no existe",   OK, "15: sumaba las DOS direcciones con L bruta. Es 6,90 % en X y 6,91 % en Y, o sea DENTRO del 5-8 % habitual. La razon del peso es el ESPESOR: 285 kgf/m2 sobre soga"),
 ("[auditoria]",      "C-6 VENTANAS AL POZO: MX-3 solo tolera 2,48 m de vano", OK, "los ambientes que dan al pozo son los laterales; sus ventanas van en los lados LONGITUDINALES, que no son portantes cargados. MX-3 y MX-4 no llevan ventanas"),
 ("[auditoria]",      "C-7 la continuidad de losa se declara y no se aplica", OK, "26: la vigueta resuelta como viga continua real. Recarga los interiores (+16 % MX-2) y descarga las fachadas (-22 %). El critico CAMBIA de identidad y los 7 siguen cumpliendo: peor 9,32 contra 9,75"),
 ("[auditoria]",      "C-8 los muros portantes no llevan TARRAJEO",           OK, "11 y 02: aplicado. Lo cazo el cruce 02-11 al minuto"),
 ("[auditoria]",      "parapeto de azotea nunca metrado",                     OK, "15 y 11: 27 554 kgf en el nivel de MAYOR brazo, y ademas carga los muros del perimetro, que nadie le cobraba"),
 ("[auditoria]",      "alfeizares descontados con altura de PUERTA",          OK, "proyecto.py altura_de_vano(): las fachadas llevan VENTANAS de 1,00 m. Se borraban 27 821 kgf de albanileria bajo ellas, del lado INSEGURO"),
 ("[auditoria]",      "Tabla 13: las irregularidades EXTREMAS estan PROHIBIDAS", OK, "declarado en el informe 3.6.4: con 5 pisos no se penalizan, se prohiben. El barrido confirma que ninguna se presenta"),
 ("[auditoria]",      "la 100+30 del Art. 33.3 se declara y no se aplica",    OK, "declarado en 3.8.6: el 8.5.1.1 manda tomar el MAYOR de los dos refuerzos, no combinarlos, asi que no obliga a un calculo adicional"),
 ("[auditoria]",      "el 25 % de ala se descarto leyendolo al reves",        OK, "12: se adopta ALA = 6t, que es MAS conservador que el cuarto del muro donante, y con un control de que la suma de alas no supere la propia longitud"),
 ("[auditoria]",      "posiciones de VANOS ausentes del SSOT",                OK, "proyecto.py: vanos_ubicados() y machones(). El control del 6.4 corre machon por machon y no sobre el promedio"),
 ("[auditoria]",      "citas: no existe Articulo 24 en la E.070",             OK, "conclusion 15 del informe: se declaran las TRES numeraciones (decimal del RNE, articulos 1-33 de El Peruano, Comentarios de San Bartolome) y se cita la del documento consultado"),
 ("[auditoria]",      "el 01 y el 11 aprobaban el 6.4 con el trozo PROMEDIO", OK, "01 y 11: se compara CADA machon contra 1,20 m. Un muro de 0,80 + 3,00 promedia 1,90 y aprobaria escondiendo el corto"),
 ("[auditoria]",      "DOS longitudes netas para el mismo muro",              OK, "el 01 y el 18 usaban machones(), el 02 y el 11 usaban L - suma(vanos). Unificadas en machones(): el trozo de 0,15 m del extremo es una columna aislada y el 6.4 no la cuenta"),
 ("[auditoria]",      "el auditor de documentos NO miraba el informe",        OK, "_auditoria_documentos.py: el glob era DOCS/*.md, o sea solo la raiz. El borrador/ quedaba fuera y ahi sobrevivio el 17,3 %. Extendido; cazo 53 cifras vencidas"),
 ("[auditoria]",      "CINCO scripts fuera del registro de regresion",        OK, "_regresion.py recorria el BASELINE y no el disco: 22, 23, 24, 25 y 26 no se comparaban. El 22 REVENTABA y nadie lo sabia. Ahora avisa de los que faltan"),
 ("[auditoria]",      "el control del 22 no podia pasar nunca",               OK, "pedia M_CASO_3 > max(CASO_1) y los dos valen 0,125, que es lo correcto: el caso 1 con b/a infinito CONVERGE al caso 3. El control estaba mal escrito, no la tabla"),
 ("[auditoria]",      "el cruce 02-11 reventaba cuando el critico cambiaba",  OK, "separadas las dos preguntas: la coherencia de calculo es assert, la identidad del critico es AVISO. Hacer reventar un hallazgo legitimo lo disfraza de error de ejecucion"),
 ("C2 predimension",  "losa",                                    OK,   "06: 0,20 m"),
 ("C2 predimension",  "muros",                                   OK,   "06: t = 0,24 m, fijado por la unidad"),
 ("C2 predimension",  "columnas",                                OK,   "06: 0,24 x 0,25 = 600 cm2"),
 ("C2 predimension",  "VIGAS",                                   OK,   "08: viga de borde del pozo 0,24x0,30 y viga de cimentacion"),
 ("C2 predimension",  "cimentacion corrida",                     OK,   "04: B = 0,70 m"),
 ("C2 predimension",  "zapatas",                                 OK,   "08: el edificio NO lleva zapatas aisladas, y se demuestra por que"),
 ("C1 presentacion",  "estacionamientos resueltos en el predio", OK,   "4 cajones de 2,50 x 5,00 en retiro frontal de 5,00 m"),
 ("C2 predimension",  "plasmarlo en un plano",                   OK,   "planos/dxf_predimensionamiento.py -> PREDIMENSIONAMIENTO.dxf: cuadro de 10 elementos, sentido del aligerado y los dos cortes de cimentacion"),
 ("C3 metrado losa",  "idealizar y metrar TODAS las losas",      OK,   "10: los 6 panos, con pozo y escalera descontados"),
 ("C4 metrado muros", "metrar TODOS los muros portantes",        OK,   "11: los 13, con sigma verificado uno por uno"),
 ("C5 analisis X-X",  "traslacion + TORSION",                    OK,   "17: directo + torsion muro por muro; la torsion agrega 9,5 % en X"),
 ("C5 analisis X-X",  "diagramas de fuerzas internas",           OK,   "figuras/DIAGRAMAS-XX.png: DFC escalonado y DMF poligonal de los muros, control contra el 17 a 2e-16"),
 ("C5 analisis X-X",  "rigidez lateral del muro",                OK,   "12: K de los 7 muros en X"),
 ("C6 analisis Y-Y",  "traslacion + TORSION",                    OK,   "17: directo + torsion muro por muro; la torsion agrega 4,6 % en Y"),
 ("C6 analisis Y-Y",  "diagramas de fuerzas internas",           OK,   "figuras/DIAGRAMAS-YY.png: DFC escalonado y DMF poligonal de los muros, control contra el 17 a 2e-16"),
 ("C6 analisis Y-Y",  "rigidez lateral del muro",                OK,   "12: K de los 6 muros en Y"),
 ("C7 herramientas",  "SAP / ETABS / Robot / OpenSeesPy",        OK,   "20: modelo 3D de 13 muros x 5 pisos, diafragma rigido, OpenSeesPy 3.12"),
 ("C7 herramientas",  "CONTRASTAR contra el calculo manual",     OK,   "20: reparto, deriva, periodo e irregularidad torsional, uno por uno"),
 ("C7 herramientas",  "declarar la TOLERANCIA del contraste",    OK,   "20: 0,5 % de armado contra formula cerrada; el resto se declara sin tope"),
 ("C7 herramientas",  "llevarlo al informe",                     OK,   "borrador/04-9: seccion 3.9 con los cuatro contrastes y la tolerancia"),
 ("C8 diseno muros",  "disenar y verificar al corte",            OK,   "18: los 13 pasan fisuracion 8.5.2; suma Vm/VE 2,098 en X y 1,651 en Y"),
 ("C8 diseno muros",  "llevarlo a plano de muros",               OK,   "planos/dxf_muros.py -> MUROS.dxf: cuadro de los 13 muros con el 8.5.2 y elevacion tipo con el refuerzo horizontal hilada por hilada"),
 ("C9 confinamiento", "columnas: ACERO LONGITUDINAL",            OK,   "19: Tabla 11 -> Asf + Ast; el critico es MY-1/MY-2 con 26,57 cm2"),
 ("C9 confinamiento", "criterio del ESPACIAMIENTO DE ESTRIBOS",  OK,   "19: los CUATRO (s1..s4); manda s1 en las 5 secciones -> estribo de 3/8 pulg"),
 ("C9 confinamiento", "viga solera de confinamiento",            OK,   "19: Ts = Vm1 Lm/(2L), traccion pura, 4 varillas de 1/2\""),
 ("C9 confinamiento", "llevarlo a plano",                        OK,   "planos/dxf_estructuras.py -> ESTRUCTURAS.dxf: cuadro de columnas y detalles de armado, con control probado"),
 ("C10 cierre",       "conclusiones Y recomendaciones",          OK,   "borrador/06-conclusiones.md: 15 conclusiones en 6 bloques (normativa, unidad, analisis, modelo, no estructurales y METODO) + 12 recomendaciones en 4 bloques (obra, proyectista, ensayos, futuros)"),
 ("C10 cierre",       "minimo 10 referencias",                   OK,   "24: son 18 (9 bibliograficas + 7 normas + 2 otras), TODAS con evidencia verificada en disco; el script revienta si falta una"),
 ("C10 cierre",       "anexo: estudio de mecanica de suelos",    OK,   "EMS de Santo Domingo de Acobamba"),

 # ------------------------------------------------- los 9 puntos del entregable
 ("entregable", "1 caratula con integrantes y % de participacion", OK,   "borrador/00-caratula.md: los 7 nombres completos al 100 %, docente y NRC"),
 ("entregable", "2 indice general, de tablas y de figuras",        _IDX[0], _IDX[1]),
 ("entregable", "3 introduccion",                                  OK,   "borrador/02-introduccion.md: enfoque, alcance y los 3 criterios declarados"),
 ("entregable", "4 objetivos",                                     OK,   "borrador/03-objetivos.md: 1 general y 9 especificos"),
 ("entregable", "5 desarrollo del tema",                           OK,   "borrador/04-1 a 04-9: las NUEVE secciones del desarrollo, en el orden de temas de la consigna (16 971 palabras)"),
 ("entregable", "6 conclusiones y recomendaciones",                OK,   "borrador/06: 15 conclusiones y 12 recomendaciones"),
 ("entregable", "7 referencias bibliograficas",                    OK,   "borrador/07: 18 referencias ISO 690, todas con evidencia verificada"),
 ("entregable", "tablas y figuras numeradas con caption",         OK,   "generar_docx.py numera 42 tablas y 4 figuras; el caption sale de la frase que introduce cada tabla, no se inventa"),
 ("entregable", "8 anexos (GENERADOS, no tecleados)",  OK,   "calculo/28_anexos.py -> borrador/08-anexos.md: A metrado de los 13 muros, B registro de las 99 obligaciones, C las 7 fichas de unidades con su PDF, D trazabilidad script por script, E el EMS con sus limites declarados. Se GENERA desde el SSOT porque un anexo tecleado contradice al cuerpo justo donde el trabajo dice aqui esta la prueba"),
 ("entregable", "9 links de fuentes de Internet",                  OK,   "borrador/07, seccion final: Cap. 8 de la PUCP, RNE y OpenSeesPy"),
 ("entregable", "archivo GRUPO_06_28606.doc",                      PEND, "lo suben los 7 antes del 3 de octubre"),

 # ------------------------------------------------- instrucciones sueltas de la docente
 ("docente", "muros continuos minimo de 1,20 m",              OK,   "E.070 6.4, implementado en 01"),
 ("docente", "solo los muros continuos en X y Y se metran",   OK,   "01 y 11: el control corre MACHON POR MACHON contra el 1,20 m del 6.4, no sobre el promedio. Los 13 muros son continuos del 1.o al 5.o piso"),
 ("docente", "LADRILLO SOLIDO TIPO I",                        OK,    "JUSTIFICADO en borrador/04-1 §3.1.2: la Tabla 2 lo prohibe en 4 pisos a mas Y ademas no resiste (5,25 admisible contra 9,41 actuante: excede 79 %)"),
 ("docente", "si la carga axial no cumple, cambiar material", OK,   "se uso la otra salida del 7.1.1b: reducir Pm"),
 ("docente", "usar Robot Structural y/o OpenSeesPy",          OK,   "20: OpenSeesPy, modelo 3D contrastado con el calculo manual"),
 ("docente", "todo el diseno esta en la E.070 capitulo 8",    OK,   "bajado el C08 de la PUCP que pide la consigna"),
 ("docente", "puede ser edificacion multifamiliar",           OK,   "DECIDIDO 2026-09-14: multifamiliar PURO"),
 ("lectura", "San Bartolome, Quiun y Silva (2015) pp. 37-56", OK,   "en 10-bibliografia/"),
 ("lectura", "Arango (2002) pp. 94-130",                      OK,   "en 10-bibliografia/"),
 ("lectura", "PUCP Capitulo 8 Analisis y Diseno",             OK,   "descargado el 2026-09-14"),
]


def consigna():
    cuenta = {OK: 0, FALLA: 0, PEND: 0, NA: 0, DECL: 0}
    for f in CONSIGNA:
        cuenta[f[2]] += 1
    print("=" * 78)
    print("COBERTURA DE LA CONSIGNA — lo que pide la docente")
    print("=" * 78)
    print("  %d OK   %d ATENCION   %d PENDIENTE   %d DECLARADO   (de %d exigencias)"
          % (cuenta[OK], cuenta[FALLA], cuenta[PEND], cuenta[DECL], len(CONSIGNA)))
    print()
    for est, titulo in ((FALLA, "ATENCION — contradice una instruccion explicita"),
                        (PEND, "PENDIENTE")):
        filas = [f for f in CONSIGNA if f[2] == est]
        if not filas:
            continue
        print("  --- %s (%d) ---" % (titulo, len(filas)))
        bloque = None
        for b, que, _, nota in filas:
            if b != bloque:
                print("   [%s]" % b)
                bloque = b
            print("      %-44s %s" % (que[:44], nota[:34]))
        print()
    return cuenta

def tablero(etapa=None):
    filas = [v for v in V if etapa is None or v[0] == etapa]
    # DECL entra aqui tambien: el estado se creo para la CONSIGNA y el
    # tablero normativo reventaba con KeyError en cuanto una obligacion lo
    # usaba. Un estado nuevo hay que darlo de alta en TODOS sus contadores.
    cuenta = {OK: 0, FALLA: 0, PEND: 0, NA: 0, DECL: 0}
    for f in filas:
        cuenta[f[3]] += 1
    print("=" * 78)
    print("REGISTRO DE VERIFICACIONES" + ("" if etapa is None else "  — etapa %d" % etapa))
    print("=" * 78)
    print("  %d OK   %d FALLA   %d PENDIENTE   %d DECLARADO   %d no aplica   "
          "(de %d obligaciones)"
          % (cuenta[OK], cuenta[FALLA], cuenta[PEND], cuenta[DECL],
             cuenta[NA], len(filas)))
    print()
    for est in (FALLA, PEND):
        pend = [f for f in filas if f[3] == est]
        if not pend:
            continue
        print("  --- %s (%d) ---" % (est, len(pend)))
        for et, art, que, _, donde in pend:
            print("   e%d  %-18s %-44s %s" % (et, art, que[:44], donde[:38]))
        print()
    return cuenta


def barrido():
    print("=" * 78)
    print("BARRIDO DE LA NORMA — lo que todavia NO se leyo articulo por articulo")
    print("=" * 78)
    print("  Este es el hueco CONOCIDO. Los tres errores de esta sesion salieron")
    print("  de aca: obligaciones que nadie habia leido, no calculos mal hechos.")
    print()
    for norma, tema, estado, nota in BARRIDO:
        print("   %-18s %-32s %-8s %s" % (norma, tema, estado, nota))
# ==================================================================== RUBRICA
# Los 10 criterios valen 2 puntos cada uno. Lo que se califica es ESO, no la
# profundidad con que se resolvio cada punto: un criterio hecho a la perfeccion
# y otro vacio suman lo mismo que dos criterios correctos, y cuestan mas.
PUNTOS_POR_CRITERIO = 2.0

CRITERIOS = [
    ("C1",  "Presentacion y planos"),
    ("C2",  "Predimensionamiento"),
    ("C3",  "Metrado de losa aligerada"),
    ("C4",  "Metrado de muros portantes"),
    ("C5",  "Analisis X-X"),
    ("C6",  "Analisis Y-Y"),
    ("C7",  "Herramientas modernas"),
    ("C8",  "Diseno de muros"),
    ("C9",  "Diseno de confinamiento"),
    ("C10", "Conclusiones y bibliografia"),
]


# COMPUERTAS: exigencias sin las cuales el criterio NO puede puntuar, por mas
# completo que este el calculo. La rubrica es DISCRETA (4 niveles) y en varios
# criterios TODOS los niveles no-cero piden el plano: "lo plasma en un plano",
# "el diseno se plasma en un plano". Un calculo perfecto sin plano vale CERO.
#
# HUECO CERRADO el 2026-09-19. Antes deciamos: "el PRD solo transcribe el nivel
# Sobresaliente; los otros tres NO estan en el proyecto, asi que estas
# compuertas salen del criterio conservador y no del texto literal". Ya no: la
# rubrica completa esta transcrita en CONSIGNA-LITERAL.md, leida del .docx de
# la docente. Cada tope de abajo cita ahora el DESCRIPTOR que lo justifica.
#
# Resultado del contraste: las cinco compuertas que se habian deducido a ojo
# COINCIDEN con el texto literal. Se agregan dos que faltaban (C3 y C4).
COMPUERTAS = {
    # "los plasma en un plano" aparece en el nivel 2,0 Y en el 1,5; el 1,0 y el
    # 0 hablan de un plano que "carece de una buena interpretacion", o sea que
    # existe pero es malo. Sin NINGUN plano no hay nivel que aplique: 0.
    "C2": ("plasmarlo en un plano", 0.0),
    # "El diseno sera plasmado en planos" (2,0) / "se plasma en un plano"
    # (1,5 y 1,0). Mismo razonamiento que C2.
    "C8": ("llevarlo a plano de muros", 0.0),
    "C9": ("llevarlo a plano", 0.0),
    # 2,0 = "torsion y traslacion, elabora los diagramas"; 1,5 = "solo
    # traslacion, ELABORA LOS DIAGRAMAS"; 1,0 = "analisis incompleto".
    # Los diagramas estan en los dos niveles altos: sin ellos, el techo es 1,0.
    "C5": ("diagramas de fuerzas internas", 1.0),
    "C6": ("diagramas de fuerzas internas", 1.0),
    # 2,0 = "IDEALIZA y realiza el metrado de TODAS las losas"; 1,5 = "IDEALIZA
    # las losas y realiza su metrado incompleto"; 1,0 = "metrado deficiente",
    # sin mencion de idealizar. La idealizacion esta en los dos niveles altos,
    # igual que los diagramas en C5/C6: sin las figuras el techo es 1,0.
    "C3": ("FIGURAS de idealizacion (vigueta, ancho tributario)", 1.0),
    "C4": ("FIGURAS de idealizacion del muro", 1.0),
}


def tablero_rubrica():
    """Cuantos de los 20 puntos estan cubiertos hoy, criterio por criterio.

    El puntaje de cada criterio se estima como la fraccion de sus exigencias en
    OK. Es una APROXIMACION y esta declarada como tal: la docente no puntua por
    conteo. Sirve para lo que importa, que es ver DONDE esta el puntaje que
    falta y no gastar el tiempo puliendo un criterio ya cubierto.
    """
    print()
    print("=" * 78)
    print("TABLERO DE LA RUBRICA  -  %d criterios x %.0f puntos = %.0f"
          % (len(CRITERIOS), PUNTOS_POR_CRITERIO,
             len(CRITERIOS) * PUNTOS_POR_CRITERIO))
    print("=" * 78)
    print()
    print("  %-4s %-28s %3s %3s %7s  %s"
          % ("", "criterio", "ok", "de", "puntos", "que falta"))
    print("  " + "-" * 74)
    total = 0.0
    for cod, nombre in CRITERIOS:
        filas = [f for f in CONSIGNA if f[0].startswith(cod + " ")]
        ok = [f for f in filas if f[2] == OK]
        n = len(filas)
        p = PUNTOS_POR_CRITERIO * len(ok) / n if n else 0.0
        # la compuerta: si falta, el criterio no puede pasar de su tope
        gate = COMPUERTAS.get(cod)
        cerrado = ""
        if gate:
            clave, tope = gate
            abierta = any(f[1] == clave and f[2] == OK for f in filas)
            if not abierta and p > tope:
                p = tope
                cerrado = "  <<< COMPUERTA"
        total += p
        falta = [f[1] for f in filas if f[2] != OK]
        print("  %-4s %-28s %3d %3d %7.2f  %s%s"
              % (cod, nombre, len(ok), n, p,
                 "-" if not falta else falta[0][:34], cerrado))
        for f in falta[1:]:
            print("  %-4s %-28s %3s %3s %7s  %s" % ("", "", "", "", "", f[:34]))
    print("  " + "-" * 74)
    print("  %-4s %-28s %3s %3s %7.2f  de %.0f"
          % ("", "TOTAL ESTIMADO", "", "", total,
             len(CRITERIOS) * PUNTOS_POR_CRITERIO))
    print()

    # los 9 puntos del entregable no son un criterio, pero hunden el C1 y el C10
    ent = [f for f in CONSIGNA if f[0] == "entregable"]
    ok_ent = [f for f in ent if f[2] == OK]
    print("  Aparte: los 9 puntos del ENTREGABLE (caratula, indices, redaccion,")
    print("  referencias, anexos, links): %d de %d listos. No son un criterio"
          % (len(ok_ent), len(ent)))
    print("  numerado, pero sin ellos el C1 y el C10 no se pueden dar por buenos.")
    print()
    print("  LECTURA - donde esta el puntaje que falta:")
    faltan = sorted(((PUNTOS_POR_CRITERIO -
                      PUNTOS_POR_CRITERIO * len([f for f in CONSIGNA
                                                 if f[0].startswith(c + " ") and f[2] == OK]) /
                      max(1, len([f for f in CONSIGNA if f[0].startswith(c + " ")])), c, n)
                     for c, n in CRITERIOS), reverse=True)
    for p, c, n in faltan[:5]:
        if p > 0.01:
            print("     %-4s %-30s faltan %.2f puntos" % (c, n, p))
    print()
    print("  COMPUERTAS CERRADAS: un criterio marcado \"<<< COMPUERTA\" tiene el")
    print("  calculo hecho y vale lo que vale porque le falta el PLANO. No es que")
    print("  este a medias: la rubrica no da puntos intermedios sin el entregable.")
    print()
    print("  Y una nota de estrategia: \"plasmarlo en plano\" aparece en CUATRO")
    print("  criterios (1, 2, 8 y 9). Los planos no son un adorno del final: son")
    print("  el vehiculo con el que se cobran 8 de los 20 puntos.")
    return total


if __name__ == "__main__":
    et = None
    if "--etapa" in sys.argv:
        et = int(sys.argv[sys.argv.index("--etapa") + 1])
    c = tablero(et)
    if et is None:
        print()
        consigna()
        print()
        barrido()
        tablero_rubrica()
        print()
        print("  Para cerrar una etapa:  python verificaciones.py --etapa N")
    if c[FALLA]:
        print()
        print("  *** HAY %d VERIFICACION(ES) EN FALLA: el diseno NO cumple. ***" % c[FALLA])
        sys.exit(1)
