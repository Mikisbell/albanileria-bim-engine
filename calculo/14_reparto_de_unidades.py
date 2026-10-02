# -*- coding: utf-8 -*-
"""Dónde SÍ entra el ladrillo de Sapallanga: el edificio no es todo portante

LA PREGUNTA
===========
El ladrillo que la Tabla 2 exige (solido, vacios <= 30 %) no se fabrica en la
sierra central: LAROKA, en Sapallanga, produce King Kong de 18 huecos y
pandereta. Quedan descartados del proyecto?

NO. Quedan descartados de UNA parte del proyecto.

LO QUE DICE LA NORMA, TEXTUAL
=============================
  Tabla 2   limita la unidad "PARA FINES ESTRUCTURALES", y sus tres columnas
            hablan todas de "MURO PORTANTE". Hueca: No. Tubular: No.

  9.3.1     "Los muros no portantes (cercos, tabiques y parapetos) podran ser
            construidos empleando unidades de albanileria SOLIDA, HUECA O
            TUBULAR; pudiendose emplear la albanileria armada parcialmente
            rellena."

  2.1.21    "Tabique. Muro no portante de carga vertical, utilizado para
            subdividir ambientes o como cierre perimetral."

O sea que la prohibicion de la Tabla 2 es sobre el MURO PORTANTE, no sobre el
ladrillo. El mismo ladrillo que esta prohibido en un muro portante esta
EXPRESAMENTE permitido en tabiques, cercos y parapetos, por un articulo que los
nombra uno por uno.

LAS CONDICIONES QUE SI HAY QUE CUMPLIR
======================================
  9.3.3   en albanileria simple, fm = 6 Ms / t^2  <=  ft' = 1,5 kgf/cm2
          (traccion por flexion fuera del plano: el tabique trabaja como losa)
  9.3.5   arriostres disenados por metodos racionales
  6.2.7   los alfeizares van AISLADOS de la estructura
  6.3.3   "de no aislarse adecuadamente los alfeizares y tabiques de la
          estructura principal, se deberan contemplar sus efectos en el analisis"
          -> si no se aislan, aparece el tabique como puntal diagonal y cambia
          la rigidez. Es el Capitulo 10 entero.

POR QUE ESTE SCRIPT EXISTE
==========================
Porque "se puede usar en tabiques" sin un numero al lado no sirve para decidir.
Lo que decide es CUANTO: si el ladrillo local cubre el 5 % del edificio, da
igual; si cubre un tercio, cambia el presupuesto y la logistica de la obra.
"""
from proyecto import (FRENTE, FONDO, POZO_X0, POZO_X1, POZO_Y0, POZO_Y1,
                      PARAPETO, N_PISOS, H_LIBRE, MUROS, TABIQUERIA,
                      PESO_ALBANILERIA, PESO_ALBANILERIA_HUECA, AREA_PLANTA,
                      AREA_ESCALERA, ALFEIZAR, ESPESOR, A_UNIDAD,
                      H_UNIDAD, JUNTA_MIN, JUNTA_MAX)

# Tabique de SOGA con la unidad que fabrica LAROKA (KK 18 huecos, 23 x 12,5).
# De soga el muro mide el ANCHO de la unidad, igual que de cabeza mide el largo.
T_TABIQUE = 0.125        # no-ssot: ancho de la unidad hueca, no una constante del proyecto
E_TARRAJEO = 0.015       # no-ssot: SUPUESTO, 1,5 cm por cara
PESO_MORTERO = 2000.0    # no-ssot: kgf/m3, E.020 anexo 1, mortero de cemento
N_CARAS = 2              # no-ssot: se tarrajea por dentro y por fuera

# La unidad SOLIDA que se decidio traer de Lima: KK 30 % de vacio / INFES.
# Las tres medidas salen de las fichas de Lark y Sagitario (ver script 13).
# Las medidas de la unidad y la junta se mudaron al SSOT cuando el script 18
# empezo a necesitarlas para el refuerzo horizontal: dos consumidores, una
# sola fuente.
L_UNIDAD = ESPESOR       # de cabeza, el largo ES el espesor del muro
J_MIN = JUNTA_MIN
J_MAX = JUNTA_MAX
DESPERDICIO = 0.05       # no-ssot: SUPUESTO de obra, 5 %


def peso_tabique_por_m2():
    """kgf por m2 de tabique, incluido su tarrajeo en las dos caras."""
    albanileria = T_TABIQUE * PESO_ALBANILERIA_HUECA
    tarrajeo = N_CARAS * E_TARRAJEO * PESO_MORTERO
    return albanileria + tarrajeo, albanileria, tarrajeo


def portantes():
    """m2 de muro PORTANTE en todo el edificio, con los vanos descontados."""
    L_neta = sum(L - sum(vanos) for _n, _d, L, _t, vanos in MUROS)
    return L_neta * H_LIBRE * N_PISOS, L_neta


def tabiqueria():
    """m2 de TABIQUE, deducidos de la carga que el metrado ya viene cargando.

    El metrado no tiene la distribucion interior dibujada todavia: lleva la
    tabiqueria como una carga repartida de TABIQUERIA kgf/m2 de losa. Ese
    numero se puede invertir: si se sabe cuanto pesa un metro cuadrado de
    tabique, se sabe cuantos metros cuadrados hay.
    """
    area_losa = AREA_PLANTA - AREA_ESCALERA
    peso_por_piso = TABIQUERIA * area_losa
    p_m2, _a, _t = peso_tabique_por_m2()
    area_por_piso = peso_por_piso / p_m2
    return area_por_piso * N_PISOS, area_por_piso, area_losa, peso_por_piso


def parapetos():
    """m2 de parapeto en la azotea: perimetro exterior MAS el del pozo."""
    per_ext = 2.0 * (FRENTE + FONDO)
    per_pozo = 2.0 * ((POZO_X1 - POZO_X0) + (POZO_Y1 - POZO_Y0))
    return (per_ext + per_pozo) * PARAPETO, per_ext, per_pozo


def alfeizares():
    """m2 de alfeizar bajo las ventanas de fachada.

    Solo se cuentan las ventanas de las dos fachadas, que son los vanos anchos
    de MX-1 y MX-7. Los vanos de 0,90 m son puertas y no llevan alfeizar. Los
    de los muros que dan al pozo todavia no estan en el modelo: el area real
    sera MAYOR que esta.
    """
    ancho = 0.0
    for nom, _d, _L, _t, vanos in MUROS:
        if not nom.startswith(("MX-1", "MX-7")):
            continue
        ancho += sum(vanos)
    return ancho * ALFEIZAR * N_PISOS, ancho


def tabla():
    print("=" * 80)
    print("REPARTO DE UNIDADES  -  que ladrillo va en cada elemento")
    print("=" * 80)
    print()
    p_m2, alb, tar = peso_tabique_por_m2()
    print("  Peso de un tabique de soga con unidad HUECA, por m2:")
    print("     albanileria  %.3f m x %.0f kgf/m3      = %6.1f kgf/m2"
          % (T_TABIQUE, PESO_ALBANILERIA_HUECA, alb))
    print("     tarrajeo     %d caras x %.3f m x %.0f    = %6.1f kgf/m2"
          % (N_CARAS, E_TARRAJEO, PESO_MORTERO, tar))
    print("     %-44s   %6.1f kgf/m2" % ("TOTAL", p_m2))
    print()

    a_port, L_neta = portantes()
    a_tab, a_tab_piso, area_losa, peso_piso = tabiqueria()
    a_par, per_ext, per_pozo = parapetos()
    a_alf, ancho_vent = alfeizares()

    print("  ELEMENTO                        m2 de muro   unidad que le corresponde")
    print("  " + "-" * 76)
    print("  %-30s %10.1f   %s"
          % ("Muros PORTANTES (%.1f m/piso)" % L_neta, a_port,
             "SOLIDA <= 30 % vacios  (Tabla 2)"))
    print("  %-30s %10.1f   %s"
          % ("Tabiques interiores", a_tab, "solida, HUECA o tubular  (9.3.1)"))
    print("  %-30s %10.1f   %s"
          % ("Parapetos de azotea", a_par, "solida, HUECA o tubular  (9.3.1)"))
    print("  %-30s %10.1f   %s"
          % ("Alfeizares de fachada", a_alf, "solida, HUECA o tubular  (9.3.1)"))
    print("  " + "-" * 76)
    no_port = a_tab + a_par + a_alf
    total = a_port + no_port
    print("  %-30s %10.1f   %.1f %% del edificio"
          % ("SUBTOTAL no portante", no_port, 100.0 * no_port / total))
    print("  %-30s %10.1f" % ("TOTAL", total))
    print()
    print("  De donde sale la tabiqueria: el metrado carga %.0f kgf/m2 sobre los"
          % TABIQUERIA)
    print("  %.2f m2 de losa de cada piso = %.0f kgf. A %.1f kgf/m2 el tabique,"
          % (area_losa, peso_piso, p_m2))
    print("  son %.1f m2 por piso. NO es un metrado: es la carga invertida, y vale"
          % a_tab_piso)
    print("  mientras la distribucion interior no este dibujada.")
    print()
    print("  Parapetos: %.2f m de perimetro exterior + %.2f m del pozo, por %.2f m"
          % (per_ext, per_pozo, PARAPETO))
    print("  Alfeizares: %.2f m de ventana por piso, por %.2f m de alto. Faltan los"
          % (ancho_vent, ALFEIZAR))
    print("  que dan al pozo -> el area real es MAYOR.")
    return no_port, total


def lectura(no_port, total):
    print()
    print("=" * 80)
    print("LECTURA")
    print("=" * 80)
    print()
    print("  Casi un %.0f %% del ladrillo del edificio NO es portante, y para esa"
          % (100.0 * no_port / total))
    print("  parte el Art. 9.3.1 admite EXPRESAMENTE la unidad hueca y la tubular.")
    print("  El ladrillo de Sapallanga no queda descartado del proyecto: queda")
    print("  descartado de los muros portantes, que es otra cosa.")
    print()
    print("  QUE SIGNIFICA EN OBRA")
    print("   - Solo el %.0f %% restante se trae de Lima. El resto se compra en la"
          % (100.0 * (total - no_port) / total))
    print("     region, y encima mas barato y mas liviano (%.0f contra %.0f kgf/m3)."
          % (PESO_ALBANILERIA_HUECA, PESO_ALBANILERIA))
    print("   - Y el tabique DEBE ser el liviano: es peso muerto en altura que no")
    print("     aporta resistencia; ponerle unidad solida seria pagar mas para")
    print("     empeorar el peso sismico.")
    print()
    print("  LO QUE NO SE PUEDE HACER, Y CONVIENE DECIRLO EN EL INFORME")
    print("   La nota al pie de la Tabla 2 dice que las limitaciones \"pueden ser")
    print("   exceptuadas con el respaldo de un informe y memoria de calculo")
    print("   sustentada por un ingeniero civil\". Tienta: seria la via para usar")
    print("   el hueco local en los muros portantes y no traer nada. Tres razones")
    print("   para NO tomarla:")
    print("     1. El asterisco esta puesto sobre la fila \"Solido Artesanal\", no")
    print("        sobre la tabla. Que el texto diga \"las limitaciones indicadas\"")
    print("        en plural lo vuelve ambiguo, y una excepcion ambigua no es una")
    print("        autorizacion.")
    print("     2. Aunque aplicara, habria que SUSTENTAR con ensayos por que una")
    print("        unidad hueca resiste lo que la norma dice que no resiste. No se")
    print("        tiene ese ensayo, y el proyecto ya declara que f'm y v'm estan")
    print("        adoptados a confirmar.")
    print("     3. El motivo fisico sigue ahi. Los Comentarios (Fig. 1.12) lo")
    print("        dicen sin rodeos: \"las unidades huecas y tubulares terminan")
    print("        triturandose despues de ocurrir la falla por fuerza cortante\".")
    print("        La excepcion es administrativa; el ladrillo no se entera.")
    print()
    print("  CONDICIONES QUE EL TABIQUE SI TIENE QUE CUMPLIR (no es tierra de")
    print("  nadie): 9.3.3 traccion por flexion fm = 6Ms/t2 <= 1,5 kgf/cm2 ;")
    print("  9.3.5 arriostres calculados ; 6.2.7 alfeizares AISLADOS ; y 6.3.3,")
    print("  que obliga a meter el tabique en el analisis si NO se aisla. Esto")
    print("  ultimo importa: un tabique pegado a la estructura trabaja como")
    print("  puntal diagonal, y este proyecto declara que los alfeizares van")
    print("  aislados justamente para no tener que modelarlos.")


def cuanto_se_trae():
    """Cuantas unidades solidas hay que traer, ahora que se decidio traerlas.

    Se calcula el rendimiento en vez de copiar el del catalogo, porque el
    catalogo no dice con que junta lo calculo y la junta cambia el resultado un
    9 %. La E.070 4.1.5 la acota: "el espesor de las juntas de mortero sera como
    minimo 10 mm y el espesor maximo sera 15 mm o dos veces la tolerancia
    dimensional en la altura de la unidad mas 4 mm, lo que sea mayor". Con
    tolerancia de +-3 mm en el alto, 2 x 3 + 4 = 10 mm < 15, asi que rige 15 mm.
    """
    a_port, _L = portantes()
    print()
    print("=" * 80)
    print("CUANTO SE TRAE DE LIMA")
    print("=" * 80)
    print()
    print("  Muro de CABEZA: la cara vista de la unidad es ANCHO x ALTO = %.0f x %.0f cm."
          % (A_UNIDAD * 100, H_UNIDAD * 100))
    print("  (el LARGO, %.0f cm, atraviesa el muro: por eso t = %.2f m)"
          % (L_UNIDAD * 100, L_UNIDAD))
    print()
    print("  %-22s %12s %14s %14s" % ("junta (E.070 4.1.5)", "und/m2", "para %.1f m2" % a_port, "con %.0f %% desperd." % (100 * DESPERDICIO)))
    print("  " + "-" * 66)
    peor = 0
    for j, etiq in ((J_MIN, "minima, 10 mm"), (J_MAX, "maxima, 15 mm")):
        rend = 1.0 / ((A_UNIDAD + j) * (H_UNIDAD + j))
        total = rend * a_port
        con_desp = total * (1.0 + DESPERDICIO)
        peor = max(peor, con_desp)
        print("  %-22s %12.1f %14.0f %14.0f" % (etiq, rend, total, con_desp))
    print()
    print("  Se pide con la junta MINIMA, que es la que mas unidades exige:")
    print("       %s unidades  ~  %.0f millares" % ("{:,}".format(int(peor)).replace(",", " "), peor / 1000.0))
    print()
    print("  ES UNA COTA SUPERIOR, a proposito. No descuenta las columnas de")
    print("  confinamiento ni las soleras, que son concreto y ocupan parte de esa")
    print("  area. En obra sobrar ladrillo cuesta plata; que falte a media jornada")
    print("  cuesta la jornada, y ademas la E.070 4.1.6 prohibe levantar mas de")
    print("  1,30 m de muro por jornada: una parada obliga a junta de construccion.")
    print()
    print("  CONTROL DE RECEPCION, que es lo que hace que esto no sea papel: por")
    print("  el Art. 3.1.4 se toman 10 unidades por cada 50 millares. Con %.0f"
          % (peor / 1000.0))
    print("  millares son %d muestreos. Y antes del ensayo, la balanza: la unidad"
          % (int(peor / 50000.0) + 1))
    print("  solida pesa 3,7 - 4,0 kg y la hueca 2,6 - 3,1. Un lote que llega")
    print("  pesando menos de 3,5 kg por unidad NO es el que se compro.")


if __name__ == "__main__":
    n, t = tabla()
    cuanto_se_trae()
    lectura(n, t)
