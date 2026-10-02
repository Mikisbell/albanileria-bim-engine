# -*- coding: utf-8 -*-
"""Quinto guardian: que el modelo no se contradiga a si mismo.

POR QUE EXISTE
==============
Los otros cuatro cuidan cosas distintas y ninguno cazaba esta:

    _auditoria_constantes   que no se repita un valor
    _regresion              que no cambie un numero sin que nos enteremos
    _auditoria_documentos   que los .md no digan cifras retiradas
    verificaciones          que no falte una obligacion de la norma

Pero un modelo puede tener las cuatro en verde y seguir siendo IMPOSIBLE de
construir. El caso que lo motivo: el dintel media 0,50 m, su fondo quedaba a
1,95 m del piso terminado y **por ahi no pasa una puerta**. Ningun control lo
veia, porque cada pieza por separado estaba bien.

Este script comprueba que las piezas CIERREN ENTRE SI: que las alturas sumen,
que la geometria calce, que cada seccion respete su minimo y que los muros no
tengan mas vano que longitud.

Sale con codigo 1 si algo no cierra.
"""
import sys

import proyecto as P

fallos, avisos, total = [], [], [0]


def chequeo(ok, titulo, detalle, critico=True):
    total[0] += 1
    (fallos if critico else avisos).append((titulo, detalle)) if not ok else None
    print("  %-52s %s" % (titulo[:52], "ok" if ok else ("FALLA" if critico else "aviso")))


def cerca(a, b, tol=1e-9):
    return abs(a - b) < tol


print("=" * 78)
print("AUDITORIA DE COHERENCIA — que el modelo no se contradiga a si mismo")
print("=" * 78)
print()
print(" GEOMETRIA")
chequeo(cerca(sum(P.PANOS_Y), P.FONDO),
        "los panos suman el fondo del lote",
        "%.2f vs %.2f" % (sum(P.PANOS_Y), P.FONDO))
chequeo(cerca(P.EJES_MX[0], 0.0) and cerca(P.EJES_MX[-1], P.FONDO),
        "los ejes de muros arrancan en 0 y terminan en el fondo", "")
chequeo(cerca(P.POZO_LARGO, P.PANOS_Y[P.PANO_POZO]),
        "el pozo ocupa exactamente un pano",
        "%.2f vs %.2f" % (P.POZO_LARGO, P.PANOS_Y[P.PANO_POZO]))
chequeo(P.POZO_X0 in P.EJES_COLUMNAS_X and P.POZO_X1 in P.EJES_COLUMNAS_X,
        "los bordes E-O del pozo caen sobre ejes de muros longitudinales", "")
chequeo(cerca(P.AREA_PLANTA, P.AREA_EDIFICADA - P.AREA_POZO),
        "el area techada es la huella menos el pozo", "")
chequeo(P.FONDO_LOTE >= P.FONDO, "el lote es al menos tan profundo como el edificio",
        "%.2f vs %.2f" % (P.FONDO_LOTE, P.FONDO))
chequeo(cerca(P.AREA_LIBRE,
              P.FRENTE * (P.RETIRO_FRONTAL + P.RETIRO_POSTERIOR) + P.AREA_POZO),
        "area libre = los dos retiros + el pozo  [A.010 9.3]", "")
chequeo(P.PCT_AREA_LIBRE >= P.AREA_LIBRE_MINIMA,
        "area libre >= 30 % del lote  [parametro municipal]",
        "%.1f %%" % (P.PCT_AREA_LIBRE * 100))
chequeo(P.RETIRO_FRONTAL >= P.EST_LARGO,
        "retiro frontal >= largo del cajon  [A.010]",
        "%.2f vs %.2f m" % (P.RETIRO_FRONTAL, P.EST_LARGO))
chequeo(P.N_ESTACIONAMIENTOS * P.EST_ANCHO + 1.20 <= P.FRENTE,
        "los cajones y el ingreso peatonal caben en el frente",
        "%.2f vs %.2f m" % (P.N_ESTACIONAMIENTOS * P.EST_ANCHO + 1.20, P.FRENTE))
chequeo(P.RETIRO_POSTERIOR >= 0.30 * (P.HN + P.PARAPETO - P.ALFEIZAR),
        "retiro posterior >= 30 % del paramento  [A.020 Cuadro 04]",
        "%.2f vs %.2f m" % (P.RETIRO_POSTERIOR,
                            0.30 * (P.HN + P.PARAPETO - P.ALFEIZAR)))
my = sum(m[2] for m in P.MUROS if m[0].startswith("MY-3"))
chequeo(cerca(my, P.FONDO - P.POZO_LARGO),
        "los tramos del muro MY-3 suman el fondo menos el pozo",
        "%.2f vs %.2f" % (my, P.FONDO - P.POZO_LARGO))

print()
print(" MUROS Y VANOS")
for nom, dire, L, t, vanos in P.MUROS:
    chequeo(sum(vanos) < L, "vanos < longitud en %s" % nom[:28],
            "%.2f vs %.2f" % (sum(vanos), L))
    trozo = (L - sum(vanos)) / (len(vanos) + 1)
    chequeo(trozo >= P.LONG_MINIMA,
            "trozo medio >= 1,20 m en %s" % nom[:28], "%.2f m" % trozo)

print()
print(" CONFINAMIENTO (E.070)")
seps = [P.EJES_COLUMNAS_X[i + 1] - P.EJES_COLUMNAS_X[i]
        for i in range(len(P.EJES_COLUMNAS_X) - 1)]
tope = min(2 * P.H_ENTREPISO, 5.00)
chequeo(max(seps) <= tope, "separacion de columnas <= min(2h, 5 m)  [7.2.1.b]",
        "%.2f vs %.2f" % (max(seps), tope))
chequeo(cerca(P.EJES_COLUMNAS_X[0], 0.0) and cerca(P.EJES_COLUMNAS_X[-1], P.FRENTE),
        "las columnas cubren todo el frente del muro transversal", "")
chequeo(P.ESPESOR >= P.H_LIBRE / 20.0, "espesor efectivo t >= h/20  [7.1.1.a]",
        "%.3f vs %.3f" % (P.ESPESOR, P.H_LIBRE / 20.0))
chequeo(cerca(P.B_COLUMNA, P.ESPESOR) and cerca(P.B_SOLERA, P.ESPESOR),
        "columna y solera tienen el espesor del muro  [7.2.3]", "")
chequeo(cerca(P.H_SOLERA, P.E_LOSA),
        "peralte de solera = espesor de losa  [7.2.4]", "")
chequeo(P.H_COLUMNA >= 0.15, "peralte de columna >= 0,15 m  [7.2.5]",
        "%.2f" % P.H_COLUMNA)
chequeo(P.B_COLUMNA * 100 * P.H_COLUMNA * 100 >= 15 * P.ESPESOR * 100,
        "area de columna >= 15 t  [8.6.3]", "")
chequeo(P.FC >= 175, "f'c de confinamientos >= 175  [7.2.1.f]", "%.0f" % P.FC)

print()
print(" ALTURAS — aca estaba el hueco que motivo este script")
chequeo(cerca(P.E_PISO_TERMINADO + P.ALTO_PUERTA + P.H_DINTEL_PUERTA, P.H_LIBRE),
        "piso term. + puerta + dintel de puerta = altura libre",
        "%.2f vs %.2f" % (P.E_PISO_TERMINADO + P.ALTO_PUERTA + P.H_DINTEL_PUERTA, P.H_LIBRE))
chequeo(cerca(P.E_PISO_TERMINADO + P.ALFEIZAR + P.ALTURA_VENTANA + P.H_DINTEL_VENTANA, P.H_LIBRE),
        "piso term. + alfeizar + ventana + dintel = altura libre", "")
fondo_dintel = P.H_LIBRE - P.H_DINTEL_PUERTA - P.E_PISO_TERMINADO
chequeo(fondo_dintel >= 2.10,
        "fondo del dintel >= 2,10 m sobre piso term.  [A.010 18.3]",
        "%.2f m" % fondo_dintel)
chequeo(P.H_LIBRE - P.E_PISO_TERMINADO >= 2.30,
        "piso terminado a cielo raso >= 2,30 m  [A.010 18.1]",
        "%.2f m" % (P.H_LIBRE - P.E_PISO_TERMINADO))
chequeo(max(P.H_DINTEL_PUERTA, P.H_DINTEL_VENTANA) <= 0.60,
        "dinteles <= 0,60 m  [E.070 6.2.6]", "")
nivel_ultimo = (P.N_PISOS - 1) * P.H_ENTREPISO
chequeo(nivel_ultimo <= 12.00,
        "sin ascensor: ultimo nivel comun <= 12,00 m  [A.010 34.1.a]",
        "%.2f m" % nivel_ultimo, critico=False)

print()
print(" POZO DE LUZ (A.020 Cuadro N.o 04)")
h_par = P.HN + P.PARAPETO - P.ALFEIZAR
req_pozo = 0.35 * h_par   # no-ssot: porcentaje del A.020 Cuadro 04, no metros
chequeo(h_par <= 18.00, "altura de paramento en el primer tramo (<= 18 m)",
        "%.2f m" % h_par)
deficit = (req_pozo - min(P.POZO_ANCHO, P.POZO_LARGO)) / req_pozo * 100
chequeo(deficit <= 20.0, "deficit del lado menor <= 20 %  [nota iii]",
        "%.1f %%" % deficit)
chequeo(P.AREA_POZO >= req_pozo ** 2 - 1e-9,
        "area del pozo >= la normativa  [nota iii]",
        "%.2f vs %.2f m2" % (P.AREA_POZO, req_pozo ** 2))
chequeo(min(P.POZO_ANCHO, P.POZO_LARGO) >= 2.10,
        "lado minimo del pozo >= 2,10 m  [nota vi]",
        "%.2f m" % min(P.POZO_ANCHO, P.POZO_LARGO))

print()
print(" LOSA (E.060 Tabla 9.1)")
for i, L in enumerate(P.PANOS_Y):
    div = 18.5 if (i == 0 or i == len(P.PANOS_Y) - 1) else 21.0
    chequeo(P.E_LOSA >= L / div - 1e-9,
            "pano %d: e_losa >= L/%.4g" % (i + 1, div),
            "%.3f vs %.3f" % (P.E_LOSA, L / div))

print()
print(" INVALIDANTES DE LA CONSIGNA")
chequeo(P.N_PISOS >= 5, "minimo 5 pisos", "%d" % P.N_PISOS)
chequeo(P.AREA_PLANTA >= 200, "area techada >= 200 m2", "%.2f" % P.AREA_PLANTA)
chequeo(cerca(P.Z, 0.25), "zona sismica 2 (grupo 6)", "Z = %.2f" % P.Z)
chequeo(cerca(P.HN, P.N_PISOS * P.H_ENTREPISO), "hn coherente con pisos y entrepiso", "")

print()
print("=" * 78)
if fallos:
    print("INCOHERENCIAS: %d" % len(fallos))
    for tit, det in fallos:
        print("   %-54s %s" % (tit, det))
    sys.exit(1)
print("El modelo cierra consigo mismo: %d comprobaciones, 0 incoherencias."
      % total[0])
if avisos:
    print("avisos (no bloquean): %d" % len(avisos))
