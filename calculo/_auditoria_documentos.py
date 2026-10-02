# -*- coding: utf-8 -*-
"""Tercer guardian: que los .md no queden diciendo cifras que ya no son.

Los otros dos cuidan el codigo. Este cuida la documentacion, que es donde los
numeros viejos sobreviven mas tiempo: nadie vuelve a leer un parrafo que "ya
estaba escrito".

COMO FUNCIONA. Lleva una lista de valores RETIRADOS -- cifras que el proyecto
tuvo y ya no tiene -- y avisa donde siguen apareciendo. No intenta adivinar si
un numero es correcto: solo sabe cuales dejaron de serlo.

QUE NO REVISA, a proposito:
  * la seccion "Bitacora": es registro historico y DEBE decir lo que paso.
  * cualquier linea marcada con <!-- h --> (comentario HTML, no se renderiza),
    para el parrafo que narra una correccion y necesita nombrar el valor viejo.
"""
import glob
import io
import os
import re
import sys

# La consola de Windows es cp1252 y este guardian imprime TROZOS DE LA
# DOCUMENTACION, que tiene simbolos matematicos. Sin esto, el guardian revienta
# justo cuando encuentra un hallazgo: fallaria solo cuando sirve.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# (texto retirado, que rige hoy)
#
# ESTA LISTA NECESITA CURADURIA: un valor retirado puede VOLVER a estar vigente
# con otro significado, y entonces el auditor empieza a marcar cifras correctas.
# Paso con "0,45" (dejo de ser el dintel unico y volvio como dintel de ventana)
# y con "2,45 m" (dejo de ser la altura libre y volvio como altura de piso
# terminado a cielo raso). Cuando eso ocurra, se SACA de la lista: un control
# que marca lo correcto se vuelve ruido, y el ruido tapa lo que si importa.
RETIRADOS = [
    ("0,25 m",     "la losa es de 0,20 m",
                   ("0,24 × 0,25", "0,24 x 0,25",     # la seccion de la C-1
                    "paso de 0,25", "0,25 m dan",     # el paso de la escalera
                    "Paso mínimo")),             # y su fila en el cuadro del 3.3.9
    ("350 kgf/m²", "el aligerado de 0,20 m pesa 300 kgf/m2"),
    ("0,75 m",     "el cimiento corrido es de 0,70 m"),
    # 2026-09-16: el cimiento PASO de 0,60 a 0,70 al sumar el tarrajeo. La
    # entrada vieja marcaba "0,70 m" como retirado, o sea denunciaba el valor
    # VIGENTE y callaba el obsoleto: un guardian invertido es peor que ninguno.
    ("0,60 m",     "el cimiento corrido paso a 0,70 m el 2026-09-16",
                   ("tope de 0,60", "hasta 0,60",     # el tope de peralte del 6.2.6
                    "franja de losa de 0,60")),       # la franja entre fachada y caja
    # 2026-09-17: correccion del hallazgo C-1 (coordenadas condensadas en la
    # rigidez). Cambio la rigidez y con ella el reparto, la deriva y el acero
    # de la columna extrema. NO cambio la densidad ni el esfuerzo axial.
    # RETIRADA 2026-09-19: "0,000614" fue el valor obsoleto de la deriva
    # manual antes de C-1, pero HOY es la deriva en Y que arroja el modelo
    # de elementos finitos. La entrada habia quedado denunciando una cifra
    # VIGENTE -- el mismo guardian invertido que ya paso con el 0,70 del
    # cimiento. Una entrada de este auditor caduca cuando su cifra vuelve a
    # ser verdad por otro camino, y eso no avisa solo.
    # 2026-09-19: dos cifras del RESUMEN que quedaron viejas tras corregir la
    # rigidez. El resumen es lo primero que lee quien califica.
    ("el 12 % del limite", "la deriva usa el 13,2 % del limite"),
    ("mas del 130 %", "la densidad supera el minimo en mas del 137 %"),
    # 2026-09-19 (auditoria C-5): el script 01 comparaba el trozo MEDIO contra
    # el 1,20 m del 6.4 en vez de cada machon, y contaba los 0,15 m de media
    # columna. Al unificarlo con machones() el area de corte bajo de 15,95 a
    # 15,816 m2 en X y de 15,97 a 15,840 en Y.
    ("15,95 m²",   "el area de corte en X es 15,816 m2"),
    ("15,97 m²",   "el area de corte en Y es 15,840 m2"),
    # 2026-09-21. Las dos holguras de densidad SALEN de esta lista. Motivo:
    # al aplicar el retiro lateral de la E.030 Art. 52.3 el frente edificado
    # bajo a 11,90 m y los valores se movieron otra vez -- hoy son +135,7 %
    # en X y +140,2 % en Y --. O sea que "+140,2 %", que estaba prohibido por
    # ser el valor de antes de la auditoria C-5, VOLVIO A SER EL VIGENTE por
    # pura coincidencia numerica, y el guardian lo denunciaba en un texto
    # correcto.
    #
    # Un control por texto no puede distinguir una cifra vieja de una que
    # volvio a ser valida: son el mismo numero. Cuando eso pasa, la entrada
    # deja de servir y hay que retirarla, no marcar la linea como excepcion
    # -- marcarla taparia tambien un uso de verdad viejo.
    ("mas del 139 %", "la densidad supera el minimo en mas del 137 %"),
    # 2026-09-19 (auditoria C-5): la "densidad del 17,3 %" nunca existio --
    # sumaba las dos direcciones con longitud bruta. Es 6,90 % y 6,91 %.
    ("densidad de muros del 17,3 %", "la densidad es 6,90 % en X y 6,91 % en Y"),
    ("0,000606",   "la deriva maxima es 0,000709"),
    # 2026-09-20: el parapeto se rehizo con la carga del E.020 Art. 8.2, que
    # GOBIERNA sobre el sismo (26 % mas de momento). Columnetas mas juntas.
    ("cada 2,80 m", "las columnetas del parapeto van cada 2,40 m"),
    ("2,80 m**", "las columnetas del parapeto van cada 2,40 m"),
    ("25 en el perímetro", "son 29 columnetas en el perimetro de azotea"),
    ("1,443", "el fm del parapeto es 1,339 con la carga del 8.2"),
    # 2026-09-19: el periodo del modelo se movio con el peso corregido.
    ("0,180 s",    "el periodo del modelo en X es 0,188 s"),
    ("0,169 s",    "el periodo del modelo en Y es 0,168 s"),
    # 2026-09-27 (auditoria de huecos): la seccion 3.5 publicaba la rigidez de
    # ANTES de la reparacion C-1 del script 12, en DOS tablas a la vez -- la
    # principal y la de sensibilidad del ala-, y el apartado 3.9 citaba una
    # corrida vieja del modelo. Ninguno de los 16 guardianes miraba una suma
    # escrita a mano; de ahi salio el 17.
    ("728 351",    "la suma K en X es 691 019 (lectura adoptada, 6t)"),
    ("849 696",    "la suma K en Y es 896 035 (lectura adoptada, 6t)"),
    ("819 592",    "la suma K en X con el ala alternativa es 775 951"),
    ("916 002",    "la suma K en Y con el ala alternativa es 962 863"),
    ("422 013",    "la suma del reparto en X, 1.er entrepiso, es 418 901"),
    ("407 032",    "la suma del reparto en Y, 1.er entrepiso, es 405 660"),
    ("416 251",    "el modelo reparte 413 135 kgf en X"),
    ("400 490",    "el modelo reparte 399 573 kgf en Y"),
    ("0,000718",   "la deriva del modelo en X es 0,000720"),
    ("0,000641",   "la deriva del modelo en Y es 0,000575"),
    ("0,187 s",    "el periodo del modelo en X es 0,188 s"),
    # 2026-09-27 (2.a vuelta): el informe publicaba la formula del 8.5.3 con
    # un coeficiente de arcilla de 0,54. El PDF de la norma dice 0,5 (0,35
    # para silico-calcarea) y el codigo usa 0,5: era un numero inventado en
    # la formula que gobierna TODO el diseno por corte.
    ("0{,}54 \cdot v", "el coeficiente de arcilla del 8.5.3 es 0,5"),
    ("en un 25 %", "la formula empirica es 20 % conservadora"),
    # 2026-09-19 (auditoria, ultima vuelta): alfeizares de fachada y parapeto
    # de azotea, los dos ausentes del metrado. Peso +3,8 % y con el todo.
    ("1 457,3",    "el peso sismico es 1 512,7 tonf"),
    ("1 457 326",  "el peso sismico es 1 512 701 kgf"),
    ("299 273",    "el piso tipico pesa 304 837 kgf"),
    ("260 235",    "la azotea pesa 293 353 kgf"),
    ("394 693",    "VE severo es 409 690 kgf"),
    ("0,000675",   "la deriva maxima es 0,000709"),
    ("13,5 %",     "la deriva usa el 14,2 % del limite",
                   ("Moderado", "moderado", "del peso")),   # V/P moderado, no la deriva
    ("2,152",      "suma Vm/VE es 2,098 en X"),
    ("1,712",      "suma Vm/VE es 1,651 en Y"),
    ("849 519",    "suma Vm en X es 859 327 kgf"),
    ("675 796",    "suma Vm en Y es 676 256 kgf"),
    ("31,56",      "el As requerido de la C-2 es 31,94 cm2"),
    ("4,38 %",     "la cuantia de la C-2 es 4,44 %"),
    ("9,15",       "sigma critico vale 9,41 kgf/cm2 (MX-7)"),
    ("8,77",       "sigma critico vale 9,41; el 8,77 es el transversal interior",
                   ("transversal interior", "MX-5", "modelo simple",
                    "Con `L` neta", "σm = 8,77")),
    ("1 348 kgf",  "el peso por m2 de losa es 1 373 kgf/m2"),
    ("1 063 kgf",  "en soga quedaria en 1 088 kgf/m2"),
    # 2026-09-19 (auditoria C-4): la caja de escalera descontaba area y NO
    # pesaba. Al metrarla (737 kgf/m2 de proyeccion horizontal) el peso
    # sismico sube 2 % y con el todo lo que cuelga del cortante basal.
    ("1 428,8",    "el peso sismico es 1 512,7 tonf"),
    ("1 428 844",  "el peso sismico es 1 512 701 kgf"),
    ("293 540",    "el piso tipico pesa 304 837 kgf"),
    ("254 684",    "la azotea pesa 293 353 kgf"),
    ("1 322 kgf",  "el peso por m2 de losa es 1 373 kgf/m2"),
    ("1 037 kgf",  "en soga quedaria en 1 088 kgf/m2"),
    ("386 978",    "VE severo es 409 690 kgf"),
    ("0,000662",   "la deriva maxima es 0,000709"),
    ("13,2 %",     "la deriva usa el 14,2 % del limite"),
    ("2,195",      "suma Vm/VE es 2,098 en X"),
    ("1,746",      "suma Vm/VE es 1,651 en Y"),
    ("849 540",    "suma Vm en X es 859 327 kgf"),
    ("675 835",    "suma Vm en Y es 676 256 kgf"),
    # INVERTIDO 2026-10-01: el 16 da hoy 1,1791 (corrido y leido). Esta
    # entrada denunciaba el valor VIGENTE y anunciaba uno que ningun script
    # imprime ya. Se cazan las dos cifras que si estan retiradas.
    ("1,154",      "la relacion torsional en X es 1,179 (script 16)"),
    ("1,172",      "la relacion torsional en X es 1,179 (script 16)"),
    ("1,059",      "la relacion torsional en Y es 1,058"),
    ("31,35",      "el As requerido de la C-2 es 31,94 cm2"),
    ("4,35 %",     "la cuantia de la C-2 es 4,44 %"),
    ("79 235",     "el Ve moderado de MY-1 es 80 711 kgf"),
    ("0,602",      "MY-1 emplea 0,613 de su limite de fisuracion"),
    ("3,020",      "el f bruto de MY-1 es 2,965 y NO llega al tope de 3"),
    ("38 826",     "el Ve moderado de MX-2 es 39 016 kgf"),
    ("0,476",      "MX-2 emplea 0,478 de su limite"),
    ("3,822",      "el f bruto de MX-2 es 3,803"),
    ("116 478",    "el Vu de MX-2 es 117 047 kgf"),
    ("1 133 774",  "el Mu de MX-2 es 1 139 612 kgf.m"),
    ("237 705",    "el Vu de MY-1 es 239 280 kgf"),
    ("2 313 780",  "el Mu de MY-1 es 2 329 718 kgf.m"),
    ("53 979",     "la fuerza del piso 2 es 55 018 kgf"),
    ("veintinueve veces", "la accidental es cien veces la estatica en x"),
    # 2026-09-19 (auditoria C-7/L neta): el 02 y el 11 usaban L - suma(vanos)
    # y el 01 y el 18 usaban machones(). Al unificar en machones() la L neta
    # de MX-5 paso de 10,20 a 10,05 m y sigma de 8,64 a 8,77.
    ("8,64",       "sigma vale 9,41 kgf/cm2 con la L neta unificada"),
    ("+12,8 %",    "la holgura del esfuerzo axial es +3,6 %"),
    ("12,8 %",     "la holgura del esfuerzo axial es +3,6 %"),
    ("10,20 m",    "la L neta de MX-5 es 10,05 m"),
    ("2,213",      "suma Vm/VE es 2,098 en X"),
    ("1,766",      "suma Vm/VE es 1,651 en Y"),
    ("856 245",    "suma Vm en X es 849 540 kgf"),
    ("683 270",    "suma Vm en Y es 675 835 kgf"),
    ("0,53 m",     "engrosar el muro pediria 0,54 m"),
    ("del 65 %",   "el tipo I excede el admisible en 79 %"),
    # 2026-09-17 (segunda vuelta): correccion del hallazgo C-2, la L del 8.5.3
    # pasa de bruta a NETA. Baja Vm y con el la relacion suma Vm/VE.
    ("2,762 en X", "suma Vm/VE es 2,213 en X"),
    ("2,099 en Y", "suma Vm/VE es 1,766 en Y"),
    ("2,72 en X",  "suma Vm/VE es 2,213 en X"),
    ("2,73 en X",  "suma Vm/VE es 2,213 en X"),
    ("2,07 en Y",  "suma Vm/VE es 1,766 en Y"),
    ("2,08 en Y",  "suma Vm/VE es 1,766 en Y"),
    # GUARDIAN INVERTIDO, la tercera vez en este archivo (ya paso con el
    # 0,70 del cimiento y con el 0,000614 de la deriva). Esta entrada
    # denunciaba "11 o 3/4" como retirado y anunciaba 12 como vigente. Se
    # escribio cuando el peralte de la C-2 era 30 cm; al subirlo a 35 por el
    # anclaje de la solera (E.070 7.1.4) la cuantia bajo y volvieron a ser
    # ONCE. O sea que el guardian pasaba a denunciar el valor CORRECTO y a
    # exigir el obsoleto, que es peor que no tener guardian.
    #
    # El patron ya tiene nombre en este archivo y vuelve a aparecer: una
    # entrada caduca cuando su cifra vuelve a ser verdad por otro camino, y
    # eso no avisa solo. Por eso se invierte en vez de borrarse: el 12 SI
    # esta retirado y conviene que quede cazado.
    #
    # SE INVIERTE OTRA VEZ, 2026-09-30, y ahora por DETALLADO, no por area.
    # Once barras cubren el area (30,45 cm2) pero no tienen disposicion
    # admisible: impar, y la E.060 7.10.5.3 pide apoyo en cada barra alterna.
    # Doce en el perimetro (5 y 3 por cara) con un gancho si. Lo decide
    # 19::disposicion(), que ahora revienta si el armado no se puede armar.
    ("11 ø 3/4",  "la C-2 lleva 12 varillas de 3/4 pulg: 11 no tienen disposicion admisible (E.060 7.10.5.3)"),
    ("31,2 cm²",  "la C-2 de 12 o 3/4 pulg da 34,1 cm2"),
    ("15,84",     "la C-4 de 8 o 5/8 pulg da 15,92 cm2 (5/8 = 1,99 cm2, ASTM A615M)"),
    # 2026-10-01: el cotejo del Word manual encontro el texto de 3.5, 3.6 y
    # 3.9 con cifras de una corrida vieja que ningun guardian veia (el diseno
    # SI estaba al dia). Quedan cazadas.
    ("0,000759",  "la deriva maxima es 0,000710 (script 16)"),
    ("5,944 m",   "el centro de masa tipico es (5,940; 10,565) (script 15)"),
    ("10,747 m",  "el centro de rigidez en y es 10,761 (script 15)"),
    ("5,119",     "Ktor es 5,174e7 kgf.cm/rad (script 16)"),
    ("+76,2 %",   "MY-3a: el modelo pide +54,2 % (script 20)"),
    ("1,153 <",   "tipico/azotea = 0,968 (script 16)"),
    ("12 694",    "MY-3a: modelo 29 713 kgf (script 20)"),
    ("0,50 m",     "el dintel de ventana es 0,45 m y el de puerta 0,35 m"),
    ("9,51",       "sigma vale 8,64 kgf/cm2 con el tarrajeo"),
    ("8,92",       "sigma vale 8,64 kgf/cm2 con el tarrajeo"),
    ("8,27",       "sigma vale 8,64 kgf/cm2 con el tarrajeo"),
    # Afinadas: "seis muros" pelado cazaba "En SEIS MUROS el modelo asigna
    # mas cortante", que es un CONTEO de resultados y no una afirmacion sobre
    # la configuracion. Lo que hay que impedir es que se AFIRME la planta vieja.
    ("SEIS muros transversales", "son SIETE muros transversales"),
    ("seis muros transversales", "son siete muros transversales"),
    ("con seis muros", "son siete muros transversales"),
    ("los seis muros", "son siete muros transversales"),
    ("262 559",    "Pm vale 209 751 kgf"),
    ("246 060",    "Pm vale 209 751 kgf"),
    ("e ≥ L/25",   "la E.060 Tabla 9.1: L/16, L/18,5, L/21, L/8"),
    ("h ≥ L/10",   "la E.070 6.2.6, dinteles peraltados hasta 60 cm"),
    ("A.010 Art. 19", "ese articulo esta DEROGADO; hoy son los Arts. 36 y 38"),
    ("234,36",      "el area techada es 229,32 m2 (pozo de 22,68)"),
    ("4,20 x 4,20", "el pozo es de 5,40 x 4,20 m  [A.020 Cuadro 04]"),
    ("4,20 × 4,20", "el pozo es de 5,40 x 4,20 m  [A.020 Cuadro 04]"),
    # OJO: 17,64 es TAMBIEN el sexto eje de muro transversal (EJES_MX), que
    # es un dato vigente y correcto. Sin la excepcion, cualquier documento
    # que liste los ejes de la planta queda marcado.
    ("17,64",       "el area del pozo es 22,68 m2",
                    ("EJES_MX", "eje y=17,64", "y = 17,64")),
    # --- espesor 0,23 -> 0,24 (la unidad solida solo viene en 24 cm)
    # OJO: NO se puede listar "0,23" pelado. El 0,23 tambien es el
    # COEFICIENTE de la formula Vm = 0,5 vm a t L + 0,23 Pg (E.070 8.5.3),
    # que sigue vigente; listarlo pelado marcaria la formula en falso.
    ("0,23 ×",       "las secciones son 0,24 x ...; el espesor es 0,24 m"),
    ("0,23 m",       "el espesor efectivo del muro es 0,24 m",
                     ("vuela",)),   # el vuelo del cimiento corrido, otra magnitud
    ("575 cm",       "la columna es 0,24 x 0,25 = 600 cm2"),
    ("345 cm",       "el minimo de 8.6.3 es 15t = 15 x 24 = 360 cm2"),
    # el dintel unico de 0,50 se retiro el 2026-09-14 y sobrevivio en el PRD
    # hasta el 15 porque la entrada vieja pedia "0,50 m" CON unidad, y ahi
    # estaba escrito "0,23 x 0,50", sin m. Falso negativo: se agrega la forma.
    ("× 0,50",       "no hay dintel unico: VD-1 0,24x0,35 y VD-2 0,24x0,45"),
    # --- el lote crecio para llegar al 30 % de area libre (2026-09-14) y estas
    # cifras del lote VIEJO sobrevivieron en el PRD y en PARAMETROS hasta que
    # las encontro una auditoria. Tres documentos, tres geometrias distintas.
    ("27,50",       "el lote es 12,00 x 30,50 = 366,00 m2"),
    ("330 m",       "el lote es de 366,00 m2"),
    ("330,00",      "el lote es de 366,00 m2"),
    ("100,68",      "el area libre es 136,68 m2"),
    ("30,5 %",      "el area libre es el 37,3 %"),
    ("6,50 m",      "el retiro posterior es 4,50 m (y el frontal 5,00)"),
    # --- la escalera. El apartado 3.1.4 afirmaba "15 contrapasos de 0,18 m"
    # mientras el SSOT declara 16 de 0,1688 y el 3.4 los metraba asi: el mismo
    # informe se contradecia a si mismo en dos apartados. Lo encontro la
    # REVISION VISUAL del PDF, no un script, porque ninguna cifra estaba mal
    # calculada -- estaba escrita a mano. Y 0,18 m es justo el MAXIMO que
    # admite el Articulo 29 del A.010: disenar al filo de un limite es lo que
    # un milimetro de obra tumba.
    ("15 contrapasos",      "la escalera tiene 16 contrapasos [proyecto.py]"),
    ("contrapasos de 0,18", "el contrapaso es 0,169 m; 0,18 es el MAXIMO del A.010 Art. 29"),
    # --- el estribaje de confinamiento. Con [] 3/8" el criterio que rige
    # pasa de s1 a s3 = d/4, y el minimo "1 @ 5, 4 @ 10" del final del
    # acapite deja estribos a 10 cm donde el calculo pide 6,25. El minimo
    # del acapite es un piso adicional, no un sustituto de los cuatro
    # criterios. OJO: la VS-1 SI lleva ese detalle, y por eso la entrada
    # incluye el diametro: el de la solera es de 6 mm.
    ("3/8\": 1@5, 4@10", "C-1 y C-2 llevan 1@5, 8@5, r@25 [8.6.3-a.3]"),
    ("contrapaso de 0,18",  "el contrapaso es 0,169 m; 0,18 es el MAXIMO del A.010 Art. 29",
                            ("máximo", "maximo")),
]


def revisar(ruta):
    hallazgos = []
    historico = False
    with open(ruta, encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            if re.match(r"^#{1,3}\s+Bit[áa]cora", linea):
                historico = True
            elif re.match(r"^#{1,3}\s", linea):
                historico = False
            if historico or "<!-- h -->" in linea:
                continue
            for entrada in RETIRADOS:
                viejo, vigente = entrada[0], entrada[1]
                # Tercer campo OPCIONAL: subcadenas ante las cuales la cifra
                # significa OTRA magnitud y no hay nada que denunciar. Nacio
                # el 2026-09-19 al extender el auditor a borrador/: de 13
                # avisos, 11 eran ruido -- "0,25 m" cazaba la seccion de la
                # columna C-1 (0,24 x 0,25) y "0,23 m" el vuelo del cimiento.
                # Un control con 85 % de falsos positivos deja de mirarse,
                # que es exactamente como no tenerlo.
                exentos = entrada[2] if len(entrada) > 2 else ()
                # Frontera de digito a ambos lados. Sin esto "0,50 m" matchea
                # dentro de "30,50 m" y el auditor marca en falso el frente del
                # lote; un control que grita en falso deja de mirarse.
                patron = r"(?<![\d,.])" + re.escape(viejo) + r"(?!\d)"
                if re.search(patron, linea):
                    # el GUION NO SEPARABLE (U+2011) se ve igual que el guion
                    # normal y rompe cualquier exencion escrita con "-". Paso
                    # el 2026-09-20: el anexo A empezo a escribir "MX‑5"
                    # para que Word no partiera el nombre en la celda, y la
                    # exencion de "MX-5" dejo de matchear -- un falso positivo
                    # sobre una cifra que estaba perfecta.
                    plana = linea.replace("‑", "-")
                    if any(e in plana for e in exentos):
                        continue
                    hallazgos.append((n, viejo, vigente, linea.strip()[:60]))
    return hallazgos


def laminas_citadas():
    """Toda lamina que el texto nombre tiene que existir en salidas/cad/.

    EL DEFECTO QUE ESTE CONTROL CIERRA (2026-09-22). El informe convivia con
    DOS nomenclaturas de lamina: la vigente -- E-01 a E-05, que es lo que la
    cadena genera -- y la de un juego anterior que ya no se regenera --
    E-00, A-01, A-02, A-03 --. Consecuencias que Mikis vio de frente:

      * el informe mostraba DOS laminas distintas llamadas "E-02";
      * citaba una "lamina E-00" y una "A-01" que no existen;
      * y la frase "la lamina E-01 lleva el mismo cuadro" era falsa: la E-01
        dibuja las columnas en planta, no su cuadro.

    Ninguno de los trece guardianes lo veia, porque ninguno preguntaba si lo
    que el texto NOMBRA existe. Este lo pregunta.
    """
    import glob as _glob
    vivas = set()
    for f in _glob.glob(os.path.join(DOCS, "salidas", "cad", "*.dxf")):
        vivas.add(os.path.basename(f).split("_")[0])
    citadas = {}
    for f in sorted(_glob.glob(os.path.join(DOCS, "borrador", "*.md"))):
        txt = io.open(f, encoding="utf-8").read()
        for m in re.finditer("[Ll]áminas?\s+\*{0,2}([EA]-\d{2})", txt):
            citadas.setdefault(m.group(1), set()).add(os.path.basename(f))
    malas = sorted(k for k in citadas if k not in vivas)
    print()
    print("laminas citadas en el informe")
    for k in sorted(citadas):
        estado = "ok" if k in vivas else "NO EXISTE en salidas/cad/"
        print("    %-6s %-28s %s" % (k, ", ".join(sorted(citadas[k])), estado))
    if not citadas:
        print("    (ninguna)")
    print("  el juego vigente es: %s" % ", ".join(sorted(vivas)))
    return malas


def numeracion_del_informe():
    """Que los capitulos del informe numeren 1, 2, 3... sin saltos.

    Nacio de un defecto REAL que ningun otro control veia: el borrador
    numeraba "## 4. Conclusiones" y despues "## 7. Referencias", de modo que
    el indice de Word iba a mostrar 1, 2, 3, 4, 7. El auditor de cifras no
    podia cazarlo -- no es una cifra retirada -- y la regresion tampoco, que
    mira la salida de los scripts, no el texto. Un salto de numeracion es de
    las pocas cosas que solo se ven leyendo el indice, y leerlo a mano es
    justo lo que deja de hacerse cuando hay prisa.
    """
    import glob as _g
    import re as _re
    vistos = []
    for ruta in sorted(_g.glob(os.path.join(DOCS, "borrador", "*.md"))):
        for linea in open(ruta, encoding="utf-8"):
            m = _re.match("^##\\s+(\\d+)\\.\\s+(.+)$", linea)
            if m:
                vistos.append((int(m.group(1)), m.group(2).strip(),
                               os.path.basename(ruta)))
    print()
    esperado = list(range(1, len(vistos) + 1))
    reales = [n for n, _t, _f in vistos]
    ok = reales == esperado
    print("%-30s %s" % ("numeracion de capitulos",
                        "1 a %d, correlativa" % len(vistos) if ok
                        else "SALTO: %s" % reales))
    for (n, tit, arch), esp in zip(vistos, esperado):
        if n != esp:
            print("    %s dice '%d. %s' y deberia ser %d"
                  % (arch, n, tit[:40], esp))
    return ok


def numeracion_de_apartados():
    """Que los subapartados #### N.N.N numeren correlativo dentro de cada N.N.

    El control de capitulos (## N.) no veia esto: al insertar un apartado nuevo
    quedo un 3.5.9 ENTRE el 3.5.5 y el 3.5.6, y el indice de Word lo habria
    mostrado asi. Es el mismo defecto que el salto de 4 a 7, un nivel mas
    abajo, y por eso el control se extiende en vez de duplicarse.
    """
    import glob as _g
    # sin regex: el patron construido con chr() metio comillas literales
    # DENTRO del patron y el control no cazaba nada. Un control que no puede
    # fallar es decorativo, asi que se parte la linea a mano y se comprueba.
    malos = []
    for ruta in sorted(_g.glob(os.path.join(DOCS, "borrador", "*.md"))):
        vistos = {}
        for linea in open(ruta, encoding="utf-8"):
            if not linea.startswith("#### "):
                continue
            cab = linea[5:].split()[0].rstrip(".")     # p. ej. "3.5.6"
            partes = cab.split(".")
            if len(partes) != 3 or not all(q.isdigit() for q in partes):
                continue
            bloque = partes[0] + "." + partes[1]
            vistos.setdefault(bloque, []).append(int(partes[2]))
        for bloque, nums in vistos.items():
            if nums != list(range(1, len(nums) + 1)):
                malos.append((os.path.basename(ruta), bloque, nums))
    print("%-30s %s" % ("numeracion de apartados",
                        "correlativa en todos" if not malos
                        else "SALTO en %d bloque(s)" % len(malos)))
    for arch, bloque, nums in malos:
        print("    %s, apartados del %s: %s" % (arch, bloque, nums))
    return not malos


def scripts_sin_documentar():
    """Que ningun script exista sin figurar en la documentacion.

    Este control nacio de un hueco real: ARQUITECTURA.md listaba 6 scripts
    cuando ya habia 12. Los otros controles no lo veian porque ninguno vigila
    lo que FALTA documentar -- solo lo que quedo escrito de mas.
    """
    aqui = os.path.dirname(os.path.abspath(__file__))
    scripts = sorted(os.path.basename(f) for f in
                     glob.glob(os.path.join(aqui, "[0-9]*.py"))
                     + glob.glob(os.path.join(aqui, "..", "planos", "*.py")))
    texto = ""
    for ruta in (glob.glob(os.path.join(DOCS, "*.md"))
                 + glob.glob(os.path.join(DOCS, "borrador", "*.md"))):
        texto += open(ruta, encoding="utf-8").read()
    faltan = [s for s in scripts if s not in texto]
    print()
    print("%-30s %d scripts, %d sin documentar"
          % ("cobertura de scripts", len(scripts), len(faltan)))
    for s in faltan:
        print("    %s no aparece en ningun .md" % s)
    return faltan


def estado_refleja_el_ssot():
    """ESTADO.md dice "donde estamos". Si el SSOT cambio y ESTADO no, miente.

    Regla que costo una correccion de Mikis el 2026-09-15: al cerrar una tarea
    hay que actualizar DOS cosas distintas. La Bitacora CRECE, porque es la
    historia; el cuadro "Donde estamos" se PISA, porque es la foto de hoy.
    Escribir solo la bitacora deja el estado viejo CON el registro completo, que
    es lo mas enganoso que puede pasar: el documento parece mantenido.

    Paso exactamente eso con la densidad de muros. La bitacora contaba el cambio
    de espesor con todo detalle y el cuadro seguia diciendo "+142 % en X", que
    era el valor de antes. Nadie lo habria visto releyendo la bitacora.

    Este control toma las constantes VIVAS del SSOT y exige que aparezcan en
    ESTADO.md. No hay lista que mantener a mano: si manana cambia el espesor,
    el control lo pide solo.
    """
    import proyecto as P

    def coma(x, dec):
        return ("%.*f" % (dec, x)).replace(".", ",")

    CLAVES = [
        ("espesor de muro",        coma(P.ESPESOR, 2)),
        ("numero de pisos",        "%d" % P.N_PISOS),
        ("area techada por piso",  coma(P.AREA_PLANTA, 2)),
        ("f'm adoptado",           "%d" % P.FM),
        ("altura total hn",        coma(P.HN, 2)),
        ("espesor de losa",        coma(P.E_LOSA, 2)),
        ("ancho de cimiento",      coma(P.B_CIMIENTO, 2)),
    ]
    ruta = os.path.join(DOCS, "ESTADO.md")
    texto = open(ruta, encoding="utf-8").read()
    faltan = [(q, v) for q, v in CLAVES if v not in texto]
    print()
    print("%-30s %s" % ("ESTADO.md refleja el SSOT",
                        "si" if not faltan else "NO <<<"))
    for q, v in faltan:
        print("    falta %-26s (%s) -- el cuadro quedo viejo" % (q, v))
    return len(faltan)


ANCHO_BLOQUE = 74


def bloques_que_no_entran():
    """Una linea de codigo mas ancha que la caja se PARTE por la mitad.

    Word no recorta ni encoge un bloque preformateado: lo parte donde cae, y
    en el PDF se leyo "(Anexo 1, ... Revo / que))", "5 nivel / es" y una
    formula de estribos cortada en "(0,12 . tn . / f'c)". Ninguna cifra estaba
    mal: el defecto nace en el RENDER y por eso solo aparece al mirar el PDF.

    Medido contra el documento: a 72-73 caracteres entra y a 75 ya se parte.
    El limite se fija en 74. Vale para el bloque preformateado, no para la
    prosa, que Word si reacomoda sola.
    """
    largas = []
    for ruta in sorted(glob.glob(os.path.join(DOCS, "borrador", "*.md"))):
        dentro = False
        for n, linea in enumerate(io.open(ruta, encoding="utf-8"), 1):
            s = linea.rstrip("\n")
            if s.strip().startswith("```"):
                dentro = not dentro
                continue
            if dentro and len(s) > ANCHO_BLOQUE:
                largas.append((os.path.basename(ruta), n, len(s), s.strip()[:50]))
    print()
    print("%-30s %s" % ("bloques dentro de %d caracteres" % ANCHO_BLOQUE,
                        "si" if not largas else "NO <<<"))
    for arch, n, ancho, txt in largas:
        print("    %s:%d  %d caracteres  %s..." % (arch, n, ancho, txt))
    return len(largas)


def asteriscos_dentro_de_codigo():
    """Un ** dentro de un span `...` NO es negrita: sale literal.

    En el PDF se leyo "A + (n-1)A = **n.A**", con los cuatro asteriscos a la
    vista. Markdown no interpreta enfasis dentro de codigo, y el markdown
    fuente no delata nada -- ahi los asteriscos parecen negrita como en
    cualquier otro lado. Solo se ve en el documento compuesto.
    """
    malos = []
    for ruta in sorted(glob.glob(os.path.join(DOCS, "borrador", "*.md"))):
        for n, linea in enumerate(io.open(ruta, encoding="utf-8"), 1):
            for span in re.findall(r"`([^`]*)`", linea):
                if "**" in span:
                    malos.append((os.path.basename(ruta), n, span[:50]))
    print()
    print("%-30s %s" % ("codigo sin asteriscos literales",
                        "si" if not malos else "NO <<<"))
    for arch, n, s in malos:
        print("    %s:%d  `%s`" % (arch, n, s))
    return len(malos)


SIN_TILDE = [
    "albanileria", "Albanileria", "ALBANILERIA",
    "diseno", "Diseno", "construccion", "Construccion",
    "Catolica", "Tecnica", "Tecnicas", "Analisis",
    "sismico", "sismica", "sismicos", "sismicas",
    "Peru", "PERU", "Capitulo", "Articulo", "Articulos",
    "seccion", "Seccion", "direccion", "Direccion",
    "Idealizacion", "area", "vacios", "maximo", "minimo", "critico",
]


def palabras_sin_tilde():
    """Palabras del dominio tecleadas en ASCII dentro del informe.

    Las citas ISO 690 del apartado 5 vivieron asi hasta el 2026-09-20: "SAN
    BARTOLOME, Angel ... Diseno y construccion ... Universidad Catolica del
    Peru", mientras la lista de enlaces de la misma pagina las escribia con
    todas sus tildes. En una cita el titulo es un NOMBRE PROPIO, de modo que
    escribirlo en ASCII no es un descuido tipografico sino otro titulo.

    Se saltan los bloques de codigo -- donde el ASCII es deliberado, porque
    reproducen salidas y nombres de variable -- y las lineas con rutas.
    """
    malas = []
    for ruta in sorted(glob.glob(os.path.join(DOCS, "borrador", "*.md"))):
        dentro = False
        for n, linea in enumerate(io.open(ruta, encoding="utf-8"), 1):
            if linea.strip().startswith("```"):
                dentro = not dentro
                continue
            if dentro or ".pdf" in linea or ".png" in linea or "http" in linea:
                continue
            for p in SIN_TILDE:
                if re.search(r"\b" + p + r"\b", linea):
                    malas.append((os.path.basename(ruta), n, p, linea.strip()[:45]))
    print()
    print("%-30s %s" % ("informe con tildes completas",
                        "si" if not malas else "NO <<<"))
    for arch, n, p, txt in malas:
        print("    %s:%d  '%s'  en  %s..." % (arch, n, p, txt))
    return len(malas)


def referencias_a_lamina():
    """Que lo que el informe cita exista, y que lo que existe se cite.

    La rubrica pide en TRES criterios de 2 puntos que el diseno "se plasme
    en un plano". Una lamina que existe y que ningun capitulo menciona deja
    el plano y el calculo sueltos uno del otro justo donde se califican
    juntos; y una lamina citada que no existe manda a buscar un fantasma.
    """
    import sys
    planos = os.path.join(DOCS, "planos")
    if not os.path.isdir(planos):
        print()
        print("%-30s %s" % ("referencias a lamina", "sin planos/ - se omite"))
        return 0
    sys.path.insert(0, planos)
    import rasterizar as R

    reales = set()
    for dxf in R.ORDEN:
        reales.add(R.datos_de_lamina(dxf)[0])

    citadas = {}
    for ruta in sorted(glob.glob(os.path.join(DOCS, "borrador", "*.md"))):
        for n, linea in enumerate(io.open(ruta, encoding="utf-8"), 1):
            for m in re.finditer(r"\b([AE]-\d{2})\b", linea):
                citadas.setdefault(m.group(1), []).append(
                    (os.path.basename(ruta), n))

    fantasma = sorted(set(citadas) - reales)
    huerfana = sorted(reales - set(citadas))
    print()
    print("%-30s %s" % ("laminas citadas que existen",
                        "si" if not fantasma else "NO <<<"))
    for f in fantasma:
        for arch, n in citadas[f]:
            print("    %s:%d cita la lamina %s, que NO existe" % (arch, n, f))
    if huerfana:
        print("    [i] existen y no las cita ningun capitulo: %s"
              % " ".join(huerfana))
        print("        la rubrica pide que el diseno se plasme EN UN PLANO;")
        print("        si el capitulo no dice cual, quedan sueltos")
    return len(fantasma)


if __name__ == "__main__":
    total = 0
    # verificaciones.py NO es .md pero es DOCUMENTACION: es el registro que
    # se lee para saber que falta. El 2026-09-15 se encontro ahi un "234,36"
    # retirado hacia dias, vivo porque el auditor solo miraba .md.
    objetivos = sorted(glob.glob(os.path.join(DOCS, "*.md")))
    # 2026-09-19 (auditoria): el glob era DOCS/*.md, o sea SOLO la raiz. El
    # INFORME vive en borrador/ y por lo tanto NO se auditaba -- que es el
    # unico documento que el jurado lee. Ahi sobrevivieron una "densidad de
    # muros del 17,3 %" inexistente y un "+139,8 %" vencido. El guardian
    # estaba sano; apuntaba al lugar equivocado.
    objetivos += sorted(glob.glob(os.path.join(DOCS, "borrador", "*.md")))
    objetivos.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "verificaciones.py"))
    for ruta in objetivos:
        h = revisar(ruta)
        print("%-30s %s" % (os.path.basename(ruta),
                            "limpio" if not h else "%d por revisar" % len(h)))
        for n, viejo, vigente, txt in h:
            print("    linea %4d: %-16s -> hoy %s" % (n, repr(viejo), vigente))
            print("                %s..." % txt)
        total += len(h)
    print()
    print("cifras retiradas que siguen en la documentacion: %d" % total)
    numeracion_del_informe()
    numeracion_de_apartados()
    faltan = scripts_sin_documentar()
    viejo = estado_refleja_el_ssot()
    anchos = bloques_que_no_entran()
    aster = asteriscos_dentro_de_codigo()
    tildes = palabras_sin_tilde()
    lam = referencias_a_lamina()
    # y que toda lamina NOMBRADA en el texto exista de verdad
    fantasmas = laminas_citadas()
    if fantasmas:
        print()
        print("  [FALLA] el informe cita laminas que no existen: %s"
              % ", ".join(fantasmas))
    if total or faltan or viejo or anchos or aster or tildes or lam or fantasmas:
        sys.exit(1)
