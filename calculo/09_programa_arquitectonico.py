# -*- coding: utf-8 -*-
"""Programa arquitectónico: lo que la A.020 Vivienda exige del multifamiliar

Cierra los pendientes del criterio 1 que quedaron abiertos al descargar la norma
(RM 188-2021-VIVIENDA, de gob.pe, el 2026-09-14).

Lo que se verifica, con su articulo:

  Art. 7        densidad: personas por vivienda segun numero de dormitorios
  Art. 8.1.b    area techada MINIMA del departamento en multifamiliar: 40,00 m2
  Art. 9.1      altura libre minima piso terminado a cielo raso: 2,30 m
  Art. 15.2.b   escalera integrada: ancho minimo 1,20 m ENTRE MUROS
  Art. 21.3.a   estacionamientos: 1 cada 3 viviendas (regla SUPLETORIA, aplica
                porque no se dispone de la ordenanza del distrito)
  A.010 34.1.a  ascensor obligatorio sobre 12,00 m de circulacion comun

EL HALLAZGO INCOMODO esta en los estacionamientos, y no es un tramite: un auto
necesita mas profundidad que la que deja una reticula de muros portantes cada
3,36 m. Se declara en vez de dibujarlo mal.
"""
from proyecto import (AREA_PLANTA, N_PISOS, H_LIBRE, E_PISO_TERMINADO, PANOS_Y,
                      POZO_X0, POZO_X1, FRENTE, ESPESOR, H_ENTREPISO)

DEPTOS_POR_PISO = 2          # DECISION DE PROYECTO: uno al frente, uno al fondo
AREA_MIN_DEPTO = 40.00       # A.020 Art. 8.1.b
ANCHO_MIN_ESCALERA = 1.20    # A.020 Art. 15.2.b  # no-ssot: ancho de escalera
VIV_POR_ESTACIONAMIENTO = 3  # A.020 Art. 21.3.a
DORMITORIOS = 3              # por departamento -- SUPUESTO de proyecto
# A.020 Art. 7: densidad segun numero de dormitorios
DENSIDAD = {1: 2, 2: 3, 3: 4}
# Dimensiones de un estacionamiento de auto, practica corriente
AUTO_ANCHO, AUTO_LARGO = 2.50, 5.00


def nucleo():
    """La escalera y el hall comun, alojados en la franja central del frente."""
    ancho_franja = POZO_X1 - POZO_X0
    largo = PANOS_Y[0]
    area = ancho_franja * largo
    print("=" * 78)
    print("1. NUCLEO DE CIRCULACION — escalera y hall")
    print("=" * 78)
    print("  Va en la franja central del primer pano, que es la que el pozo deja")
    print("  libre hacia el frente: %.2f m de ancho x %.2f m = %.2f m2 por piso."
          % (ancho_franja, largo, area))
    print()
    print("  A.020 Art. 15.2.b: 'deben tener un ancho minimo de 1,20 m ENTRE MUROS")
    print("  que la conforman'. Dos tramos de %.2f m = %.2f m, mas el muro"
          % (ANCHO_MIN_ESCALERA, 2 * ANCHO_MIN_ESCALERA))
    print("  intermedio de %.2f m  ->  caja de %.2f m de ancho."
          % (ESPESOR, 2 * ANCHO_MIN_ESCALERA + ESPESOR))
    caja = 2 * ANCHO_MIN_ESCALERA + ESPESOR
    print("  Entra en la franja de %.2f m  ->  %s"
          % (ancho_franja, "CUMPLE" if caja <= ancho_franja else "NO CUMPLE <<<"))
    print()
    print("  Pasos y contrapasos: %d contrapasos de %.3f m salvan el entrepiso de"
          % (round(H_ENTREPISO / 0.175), H_ENTREPISO / round(H_ENTREPISO / 0.175)))
    print("  %.2f m. Se reparten en dos tramos con descanso intermedio." % H_ENTREPISO)
    return area


def departamentos(area_nucleo):
    print()
    print("=" * 78)
    print("2. DEPARTAMENTOS — A.020 Art. 8.1.b")
    print("=" * 78)
    disponible = AREA_PLANTA - area_nucleo
    por_depto = disponible / DEPTOS_POR_PISO
    print("  area techada por piso        %8.2f m2" % AREA_PLANTA)
    print("  - nucleo de circulacion      %8.2f m2" % area_nucleo)
    print("  = disponible para vivienda   %8.2f m2" % disponible)
    print()
    print("  %d departamentos por piso  ->  %.2f m2 cada uno" % (DEPTOS_POR_PISO, por_depto))
    print("  A.020 Art. 8.1.b exige %.2f m2 minimo  ->  %s (%.1f veces el minimo)"
          % (AREA_MIN_DEPTO, "CUMPLE" if por_depto >= AREA_MIN_DEPTO else "NO CUMPLE <<<",
             por_depto / AREA_MIN_DEPTO))
    print()
    print("  Cuantos departamentos caben, por area, sin bajar del minimo:")
    print("     %d  (%.2f m2 cada uno)" % (int(disponible // AREA_MIN_DEPTO),
                                           disponible / int(disponible // AREA_MIN_DEPTO)))
    print("  Se adoptan %d y no el maximo: el pozo parte la planta en frente y" % DEPTOS_POR_PISO)
    print("  fondo, y esa division es la que manda la circulacion.")
    print()
    viviendas = DEPTOS_POR_PISO * N_PISOS
    personas = viviendas * DENSIDAD[DORMITORIOS]
    print("  %-34s %d" % ("departamentos por piso", DEPTOS_POR_PISO))
    print("  %-34s %d" % ("pisos", N_PISOS))
    print("  %-34s %d" % ("VIVIENDAS TOTALES", viviendas))
    print("  %-34s %d por vivienda (Art. 7, %d dormitorios)"
          % ("densidad", DENSIDAD[DORMITORIOS], DORMITORIOS))
    print("  %-34s %d personas" % ("POBLACION DE DISENO", personas))
    return viviendas


def alturas():
    print()
    print("=" * 78)
    print("3. ALTURAS — A.020 Art. 9.1 y A.010 Art. 34.1.a")
    print("=" * 78)
    libre = H_LIBRE - E_PISO_TERMINADO
    print("  altura libre piso terminado a cielo raso = %.2f - %.2f = %.2f m"
          % (H_LIBRE, E_PISO_TERMINADO, libre))
    print("  A.020 Art. 9.1 exige 2,30 m  ->  %s"
          % ("CUMPLE" if libre >= 2.30 else "NO CUMPLE <<<"))
    print()
    nivel = (N_PISOS - 1) * H_ENTREPISO
    print("  ultimo nivel de circulacion comun = %d x %.2f = %.2f m"
          % (N_PISOS - 1, H_ENTREPISO, nivel))
    print("  A.010 Art. 34.1.a exige ascensor 'a partir de un nivel de circulacion")
    print("  comun superior a 12.00 m'  ->  %s"
          % ("NO se requiere ascensor" if nivel <= 12.00 else "SE REQUIERE ASCENSOR"))   # no-ssot: 12,00 m de la A.010, no el frente del lote
    print("  Condicion: la azotea queda de SERVICIO (tanque y mantenimiento), no")
    print("  de uso comun. Si se habilitara como area comun, su nivel (%.2f m)" % (N_PISOS * H_ENTREPISO))
    print("  pasaria los 12,00 m y el ascensor volveria a ser obligatorio.")


def estacionamientos(viviendas):
    print()
    print("=" * 78)
    print("4. ESTACIONAMIENTOS — A.020 Art. 21.3.a, y un conflicto real")
    print("=" * 78)
    print("  Art. 21.2: el numero 'debe estar establecido en las normas")
    print("  correspondientes' — la ordenanza del distrito, que NO tenemos.")
    print("  Art. 21.3.a, regla supletoria: '1 estacionamiento cada (3) tres")
    print("  viviendas'.")
    print()
    req = -(-viviendas // VIV_POR_ESTACIONAMIENTO)     # techo de la division
    print("  %d viviendas / %d = %.2f  ->  %d estacionamientos requeridos"
          % (viviendas, VIV_POR_ESTACIONAMIENTO, viviendas / VIV_POR_ESTACIONAMIENTO, req))
    print()
    print("  EL PROBLEMA: un auto no entra en la reticula.")
    print("  Un estacionamiento corriente mide %.2f x %.2f m. Los panos entre muros"
          % (AUTO_ANCHO, AUTO_LARGO))
    print("  transversales miden %.2f m, y los muros son PORTANTES: no se pueden"
          % min(PANOS_Y))
    print("  suprimir para abrir la playa.")
    print()
    print("  %-40s %6.2f m" % ("profundidad que pide un auto", AUTO_LARGO))
    print("  %-40s %6.2f m" % ("pano menor de la reticula", min(PANOS_Y)))
    print("  %-40s %6.2f m" % ("pano mayor (el del pozo, ocupado)", max(PANOS_Y)))
    print("  %-40s %s" % ("veredicto",
                          "NO cabe dentro de la planta estructurada"))
    print()
    print("  Esto no es un descuido del proyecto: es una consecuencia del sistema.")
    print("  La albanileria confinada necesita muros portantes poco espaciados, y")
    print("  eso es incompatible con las luces que pide un estacionamiento. Por eso")
    print("  los edificios con playa en planta baja usan porticos o placas en ese")
    print("  nivel -- y eso seria un piso blando, justo lo que la E.030 penaliza.")
    print()
    print("  SALIDA ADOPTADA, con respaldo en la propia norma. El Art. 21.1 dice que")
    print("  el estacionamiento 'debe ser considerado de manera conjunta en la")
    print("  edificacion de las viviendas O SEPARADA DE ELLAS' y que 'pueden ser o")
    print("  no techados'. Se resuelven los %d espacios FUERA de la huella" % req)
    print("  estructurada, y queda DECLARADO como condicion del proyecto.")
    print()
    print("  RECOMENDACION: verificar la ordenanza de Santo Domingo de Acobamba. En")
    print("  distritos rurales es frecuente que exija menos que la regla supletoria,")
    print("  o que no exija. Con la ordenanza a la vista el numero puede bajar.")
    return req


def resumen(viviendas, est):
    print()
    print("=" * 78)
    print("RESUMEN DEL PROGRAMA")
    print("=" * 78)
    print("  %-38s %s" % ("tipologia", "multifamiliar puro (sin comercio)"))
    print("  %-38s %d" % ("departamentos por piso", DEPTOS_POR_PISO))
    print("  %-38s %d" % ("viviendas totales", viviendas))
    print("  %-38s %d" % ("poblacion de diseno (personas)",
                          viviendas * DENSIDAD[DORMITORIOS]))
    print("  %-38s %d" % ("estacionamientos requeridos", est))
    print("  %-38s %s" % ("ascensor", "no requerido (ultimo nivel a 10,80 m)"))
    print("  %-38s %.2f m" % ("ancho de escalera entre muros", ANCHO_MIN_ESCALERA))
    print()
    print("  LO QUE SIGUE PENDIENTE Y NO SE INVENTA AQUI: la distribucion interior")
    print("  de cada departamento (Art. 10, mobiliario y circulacion) y el cuadro")
    print("  de acabados. Eso es el PLANO, no el calculo.")


if __name__ == "__main__":
    a = nucleo()
    v = departamentos(a)
    alturas()
    e = estacionamientos(v)
    resumen(v, e)
