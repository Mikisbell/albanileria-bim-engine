# -*- coding: utf-8 -*-
"""Metrado de cargas y verificación del esfuerzo axial máximo

Toda constante viene de `proyecto.py`. Este script NO declara geometria ni
cargas propias: si algo cambia, se cambia alla y todos los scripts lo ven.

Produce DOS metrados distintos, y confundirlos es el error mas caro del trabajo:
  Pm = CM + 100 % CV  -> esfuerzo axial. E.070 7.1.1b pide la carga de gravedad
                         maxima de servicio "incluyendo el 100% de sobrecarga".
  P  = CM +  25 % CV  -> peso sismico (E.030 Art. 31.b) y el Pg de la formula de
                         Vm (E.070 8.5.3, "sobrecarga reducida").

Aca se decide la UNIDAD de albanileria. El docente indico "ladrillo solido tipo
I"; el calculo muestra que esa clase no resiste 5 pisos, y la Tabla 2 ademas la
prohibe. La propia E.070 7.1.1b da la salida: "mejorar la calidad de la
albanileria, aumentar el espesor del muro, transformarlo en concreto armado, o
reducir Pm".
"""
import os

from proyecto import (LOSA_ALIGERADA, PISO_TERMINADO, TABIQUERIA, SC_VIVIENDA,
                      SC_AZOTEA, PESO_ALBANILERIA, PESO_CONCRETO, PCT_CV_SISMO,
                      N_PISOS, H_LIBRE, ESPESOR, L_MURO, ANCHO_TRIB, FM,
                      E_LOSA, B_SOLERA, B_COLUMNA, H_COLUMNA, EJES_COLUMNAS_X,
                      vol_columnas, peso_tarrajeo,
                      H_DINTEL_PUERTA, muro, machones)

# Unidades evaluadas. El veredicto de la Tabla 2 NO es el mismo para las tres:
# solo la SOLIDA industrial esta admitida en muro portante de 4 pisos a mas en
# zonas 2 y 3. El King Kong de 18 huecos TIPICO del mercado tiene ~46 % de
# vacios y por 2.1.26 no es unidad solida; el script 13 lo mide sobre cuatro
# fichas reales y solo UNA de las cuatro califica. La Rejilla, igual.
UNIDADES = [
    ("King Kong ARTESANAL (~clase I)", 35.0,
     "solida, pero la Tabla 2 PROHIBE el artesanal en 4 pisos a mas"),
    ("SOLIDO industrial  (ADOPTADA)",  FM,
     "admitida por Tabla 2; f'm adoptado, a confirmar por ensayo (5.1.9)"),
    ("King Kong industrial 18 huecos", 65.0,   # no-ssot: f'm de OTRA unidad
     "~46 % de vacios en 3 de 4 fichas -> hueca -> prohibida (ver script 13)"),
]

AREA_TRIB = L_MURO * ANCHO_TRIB
CM_PISO = LOSA_ALIGERADA + PISO_TERMINADO + TABIQUERIA
# La AZOTEA no lleva tabiqueria: es de servicio, no tiene ambientes. Cargarle
# los 150 kgf/m2 inflaba el axial un 3 %. Lo delato el cruce con el script 11,
# que metra los trece muros: daba 8,22 aca y 7,98 alla para el mismo muro.
CM_AZOTEA = LOSA_ALIGERADA + PISO_TERMINADO

# --- El muro NO es todo albanileria: los confinamientos son concreto ---------
# Una segunda auditoria encontro que el peso propio tomaba los 12,00 m como si
# fueran ladrillo puro. Las columnas de confinamiento son concreto (2400 kgf/m3
# contra 1800) y ocupan su parte del volumen. Es una correccion chica, pero va
# en el sentido de MAS carga, que es donde una omision hace dano.
# --- El muro tiene VANOS, y eso parte el calculo en dos -----------------------
# El muro critico es el transversal interior. Sus puertas lo cortan: por E.070
# 6.4 cada trozo es un muro aparte, y el area que resiste la carga vertical es
# la NETA. La carga, en cambio, no baja: el aligerado sigue apoyando sobre toda
# la linea y lo que cae encima de la puerta lo recoge el dintel y lo pasa a los
# trozos vecinos. Misma carga sobre menos muro.
MURO_CRITICO = "MX-5"   # trib. maxima (sin pozo al lado) y dos vanos
_, _, _, _, VANOS = muro(MURO_CRITICO)
# AUDITORIA 2026-09-19: era L_MURO - sum(VANOS), que deja dentro el trozo de
# 0,15 m del extremo. Ese trozo es una columna aislada de 0,15 m, y el 6.4 no
# la cuenta como muro. Se unifica con machones(), la fuente unica.
L_NETA = sum(b - a_ for a_, b in machones(MURO_CRITICO, "X", L_MURO, VANOS))
H_VANO = H_LIBRE - H_DINTEL_PUERTA   # los vanos de los muros MX son PUERTAS
VOL_VANOS = sum(VANOS) * H_VANO * ESPESOR

VOL_MURO_BRUTO = ESPESOR * H_LIBRE * L_MURO
VOL_COLUMNAS = vol_columnas(len(EJES_COLUMNAS_X), H_LIBRE)
VOL_ALBANILERIA = VOL_MURO_BRUTO - VOL_COLUMNAS - VOL_VANOS
PESO_MURO = N_PISOS * (VOL_ALBANILERIA * PESO_ALBANILERIA
                       + VOL_COLUMNAS * PESO_CONCRETO)
# revoque: el 1800 es la albanileria, no el muro terminado (E.020 anexo 1).
# Se agrega el 2026-09-16; el cruce con el 11 lo cazó al minuto.
PESO_MURO += N_PISOS * peso_tarrajeo(L_MURO * H_LIBRE)

# --- La solera tampoco es aligerado ------------------------------------------
# En la franja que ocupa la solera (0,23 m de ancho por los 12,00 m del muro) no
# hay aligerado sino concreto macizo del peralte de la losa. El metrado cargaba
# ahi 350 kgf/m2 cuando en realidad son 0,25 x 2400 = 600. Se corrige la
# diferencia, no el total, para no contar la franja dos veces.
AREA_SOLERA = B_SOLERA * L_MURO
EXTRA_SOLERA = AREA_SOLERA * (E_LOSA * PESO_CONCRETO - LOSA_ALIGERADA)


def metrado_gravedad():
    """Pm, con el 100 % de la sobrecarga. E.070 7.1.1b."""
    return (4 * AREA_TRIB * (CM_PISO + SC_VIVIENDA)
            + AREA_TRIB * (CM_AZOTEA + SC_AZOTEA)
            + PESO_MURO + N_PISOS * EXTRA_SOLERA)


def metrado_sismico():
    """P (= Pg), con el 25 % de la sobrecarga. E.030 Art. 31.b y 31.d."""
    return (4 * AREA_TRIB * (CM_PISO + PCT_CV_SISMO * SC_VIVIENDA)
            + AREA_TRIB * (CM_AZOTEA + PCT_CV_SISMO * SC_AZOTEA)
            + PESO_MURO + N_PISOS * EXTRA_SOLERA)


def limite_axial(fm):
    """E.070 7.1.1b: el MENOR de 0,2 f'm [1-(h/35t)^2] y 0,15 f'm."""
    h_cm, t_cm = H_LIBRE * 100, ESPESOR * 100
    esbeltez = (h_cm / (35.0 * t_cm)) ** 2
    return min(0.20 * fm * (1 - esbeltez), 0.15 * fm), esbeltez   # no-ssot: coeficientes de 7.1.1b


def sigma(pm, longitud):
    return pm / (longitud * 100 * ESPESOR * 100)


def informe():
    pm, ps = metrado_gravedad(), metrado_sismico()
    print("=" * 74)
    print("METRADO — muro transversal interior (L = %.2f m, ancho trib. %.2f m)"
          % (L_MURO, ANCHO_TRIB))
    print("=" * 74)
    print("  area tributaria = %.2f m2" % AREA_TRIB)
    print("  carga muerta/piso: losa %.0f + piso term. %.0f + tabiqueria %.0f = %.0f kgf/m2"
          % (LOSA_ALIGERADA, PISO_TERMINADO, TABIQUERIA, CM_PISO))
    print("  peso propio del muro (%d pisos) = %.0f kgf" % (N_PISOS, PESO_MURO))
    print()
    print("  Pm (100 %% CV -> axial)   = %9.0f kgf    E.070 7.1.1b" % pm)
    print("  P  ( 25 %% CV -> sismo)   = %9.0f kgf    E.030 Art. 31" % ps)
    print("  Pm supera a P en %.0f kgf (%.0f %%). NO son intercambiables."
          % (pm - ps, (pm / ps - 1) * 100))
    print()
    lim, esb = limite_axial(FM)
    s_bruta = sigma(pm, L_MURO)
    s = sigma(pm, L_NETA)
    print("=" * 74)
    print("ESFUERZO AXIAL — E.070 7.1.1b")
    print("=" * 74)
    print("  El muro lleva %d vanos que suman %.2f m:  L bruta %.2f  ->  L NETA %.2f m"
          % (len(VANOS), sum(VANOS), L_MURO, L_NETA))
    print()
    print("  con L bruta (INCORRECTO): %.0f / (%.0f x %.0f) = %.2f kgf/cm2"
          % (pm, L_MURO * 100, ESPESOR * 100, s_bruta))
    print("  con L NETA  (correcto)  : %.0f / (%.0f x %.0f) = %.2f kgf/cm2"
          % (pm, L_NETA * 100, ESPESOR * 100, s))
    print()
    print("  La diferencia es de %+.0f %% y decide el veredicto. Usar la longitud"
          % ((s / s_bruta - 1) * 100))
    print("  bruta reparte la carga sobre muro que no existe: encima del vano no")
    print("  hay albanileria, y lo que cae ahi lo recoge el dintel y lo descarga")
    print("  en los trozos vecinos. Por E.070 6.4 cada trozo es un muro aparte.")
    print()
    print("  (h/35t)^2 = %.4f   ->  rige %s"
          % (esb, "0,15 f'm" if 0.15 * FM < 0.20 * FM * (1 - esb) else "0,2 f'm[...]"))   # no-ssot: coeficientes de 7.1.1b
    print()
    print("  %-34s %8s  %s" % ("unidad", "limite", "el axial"))
    for nom, fm, nota in UNIDADES:
        l, _ = limite_axial(fm)
        print("  %-34s %8.2f  %s" % (nom, l, "pasa" if s <= l else "NO pasa"))
        print("  %-34s %s" % ("", nota))
    print()
    print("  OJO: la columna dice solo si pasa el AXIAL. El King Kong de 18 huecos")
    print("  lo pasa y aun asi lo PROHIBE la Tabla 2 salvo que su ficha declare")
    print("  vacios <= 30 %, cosa que solo 1 de 4 fabricantes hace (script 13).")
    print("  El filtro normativo va primero; el numerico despues.")
    print()
    print("=" * 74)
    print("MARGEN — la cifra incomoda, dicha de frente")
    print("=" * 74)
    holgura = (lim / s - 1) * 100
    print("  sigma = %.2f   limite = %.2f   holgura = %+.1f %%" % (s, lim, holgura))
    if s > lim:
        print()
        print("  *** NO CUMPLE. ***  El 7.1.1b da cuatro salidas y las cuatro se")
        print("  evaluan aca con numeros, en vez de elegir la comoda:")
        print()
        # no-ssot: 0,15 es el COEFICIENTE del 7.1.1.b (sigma <= 0,15 f'm);
        # coincide de valor con SEPARACION_VANO_COLUMNA y no tiene relacion.
        fm_req = s / 0.15   # no-ssot: el 0,15 del 7.1.1.b, no una separacion
        print("  1) MEJORAR f'm: haria falta f'm >= sigma/0,15 = %.1f kgf/cm2" % fm_req)
        print("     contra los %.0f adoptados. Es +%.0f %%, y subir el f'm declarado"
              % (FM, (fm_req / FM - 1) * 100))
        print("     para que el numero entre es exactamente lo que no se hace.")
        t_req = pm / (L_NETA * 100 * 0.15 * FM) / 100   # no-ssot: idem, el 0,15 del 7.1.1.b
        print("  2) ENGROSAR el muro: t >= %.3f m contra los %.2f actuales. No hay"
              % (t_req, ESPESOR))
        print("     aparejo corriente en ese espesor.")
        print("  3) CONCRETO ARMADO: convertir el muro en placa. Cambia el sistema")
        print("     estructural y la consigna pide albanileria confinada.")
        trib_req = ANCHO_TRIB * lim / s
        print("  4) REDUCIR Pm: es la unica que no degrada nada. Bajando el ancho")
        print("     tributario de %.2f a <= %.2f m el axial entra. Con el fondo de"
              % (ANCHO_TRIB, trib_req))
        print("     21,00 m eso son 7 muros transversales (3,50 m) en vez de 6.")
        print()
        print("  RECOMENDACION: la salida 4. Ademas devuelve la losa a 0,20 m,")
        print("  porque con 3,50 m de luz el pano extremo pide 3,50/18,5 = 0,19 m.")
    elif holgura < 5.0:
        print("  Es una holgura ESTRECHA. El diseno cumple, pero no sobra nada, y")
        print("  por eso corresponde declarar que NO esta dentro del metrado:")
        print("   - el peso real de los tabiques por su ubicacion en planos, que es")
        print("     lo que pide la E.020 Art. 5. Se usa un equivalente uniforme de")
        print("     %.0f kgf/m2 porque el plano de arquitectura aun no esta cerrado." % TABIQUERIA)
        print("   - los alfeizares, que por E.070 6.2.7 van AISLADOS y por lo tanto")
        print("     no descargan sobre el muro portante, pero si sobre la losa.")
        print("   - escaleras y tanque elevado, que aun no tienen ubicacion.")
        print()
        print("  Si al cerrar la arquitectura la carga sube mas de %.1f %%, este muro" % holgura)
        print("  deja de cumplir. Las salidas que da la propia 7.1.1b, en orden de")
        print("  costo: subir f'm con un ensayo de pilas que respalde una clase mas")
        print("  alta, engrosar el muro, o aligerar la losa armandola en dos")
        print("  direcciones. NO vale bajar la tabiqueria para que el numero entre.")
    else:
        print("  Holgura comoda.")
    return pm, ps, s


def control_es_el_critico():
    """Verificar que el muro que este script modela SIGUE siendo el critico.

    AUDITORIA 2026-09-19. Este script modela un muro fijo -- MURO_CRITICO --
    y sobre el declara la holgura del proyecto. Pero cual es el muro mas
    cargado NO es un dato: es un RESULTADO, y cambia cada vez que se corrige
    el metrado. Al devolver los alfeizares a las fachadas y la escalera a los
    muros que la soportan, el critico dejo de ser MX-5 y paso a ser MX-7, y
    este script siguio imprimiendo "holgura comoda" sobre un muro que ya no
    gobernaba. Un valor clavado a mano no avisa cuando deja de ser verdad.
    """
    import importlib.util
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "11_metrado_muros.py")
    spec = importlib.util.spec_from_file_location("r11cruce", ruta)
    r11 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r11)
    filas = r11.metrar()
    peor = max(filas, key=lambda f: f["sigma"])
    mio = [f for f in filas if f["nom"].startswith(MURO_CRITICO)][0]

    print()
    print("=" * 74)
    print("CONTROL  -  el muro modelado, contra los trece del script 11")
    print("=" * 74)
    print("  modelado aqui : %-28s sigma = %.2f" % (MURO_CRITICO, mio["sigma"]))
    print("  el peor del 11: %-28s sigma = %.2f" % (peor["nom"][:28], peor["sigma"]))
    if not peor["nom"].startswith(MURO_CRITICO):
        print()
        print("  >>> ESTE SCRIPT NO MODELA EL MURO CRITICO. El que gobierna el")
        print("      proyecto es %s, con %.2f kgf/cm2 y %+.1f %% de holgura."
              % (peor["nom"].split()[0], peor["sigma"],
                 100 * (limite_axial(FM)[0] / peor["sigma"] - 1)))
        print("      Aqui se conserva %s porque es el caso DIDACTICO -- un" % MURO_CRITICO)
        print("      transversal interior, que es donde se explica el metrado --,")
        print("      pero la cifra que va al informe es la del 11.")
    else:
        print("  coinciden: el caso didactico es tambien el que gobierna.")
    return peor


if __name__ == "__main__":
    informe()
    control_es_el_critico()
