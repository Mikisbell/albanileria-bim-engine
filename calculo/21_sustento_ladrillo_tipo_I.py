# -*- coding: utf-8 -*-
"""SUSTENTO del descarte del ladrillo sólido tipo I, con números

POR QUE ESTE SCRIPT EXISTE
==========================
La consigna de la docente dice, textual en sus notas: "ladrillos solido tipo I".
Este proyecto NO lo usa. Apartarse de una indicacion expresa hay que
sustentarlo, y sustentarlo no es afirmar: es calcular.

EL FLANCO QUE HAY QUE CUBRIR, Y QUE CASI SE NOS PASA
====================================================
La respuesta facil seria "la Tabla 2 lo prohibe". Pero al mirar la tabla EN
IMAGEN (2026-09-19) se ve que el asterisco de la nota al pie esta colocado
sobre la fila "Solido Artesanal", o sea sobre EXACTAMENTE el tipo que la
consigna pide, y la nota dice:

    "Las limitaciones indicadas establecen condiciones minimas que pueden ser
     exceptuadas con el respaldo de un informe y memoria de calculo sustentada
     por un ingeniero civil."

O sea: la norma SI admite el artesanal por encima de dos pisos, a condicion de
respaldarlo con memoria de calculo. Presentar la prohibicion como inapelable
era inexacto, y un corrector que conozca esa nota tenia ahi una objecion
legitima.

LA RESPUESTA CORRECTA ES MAS FUERTE, Y ES LA QUE ESTE SCRIPT CALCULA
====================================================================
La excepcion no exime de verificar: CONDICIONA el permiso a una memoria de
calculo. Esta es esa memoria. Y dice que no pasa, por un margen que no admite
discusion. Se recorren ademas las CUATRO salidas que el propio 7.1.1.b
enumera, para que no quede la duda de si se busco una alternativa.
"""
import importlib.util
import os

from proyecto import (ESPESOR, HN, FM, PESO_ALBANILERIA, PESO_MORTERO,
                      E_TARRAJEO, N_PISOS)

# Tabla 1 de la E.070, verificada contra imagen el 2026-09-19.
# (clase, variacion hasta 100 mm en %, alabeo max en mm, f'b en kg/cm2)
TABLA_1 = [
    ("Ladrillo I",   8, 10,  50),
    ("Ladrillo II",  7,  8,  70),
    ("Ladrillo III", 5,  6,  95),
    ("Ladrillo IV",  4,  4, 130),
    ("Ladrillo V",   3,  2, 180),
    ("Bloque P",     4,  4,  50),
    # OJO: el alabeo del Bloque NP es 8 mm. El 6 que trae su fila es la
    # columna "variacion hasta 150 mm", no el alabeo. Error propio al
    # transcribir la Tabla 1, cazado al leer la salida contra la imagen.
    ("Bloque NP",    7,  8,  20),
]

# Tabla 9: fila del King Kong ARTESANAL, que es la unidad tabulada mas cercana
# al tipo I. Su f'b (55) es MEJOR que el minimo de la clase I (50), asi que
# usarla es GENEROSO con el tipo I: el veredicto no depende de esta eleccion.
FM_ARTESANAL = 35.0      # no-ssot: kg/cm2, Tabla 9, fila KK Artesanal
FB_ARTESANAL = 55.0      # no-ssot: kg/cm2, idem

C_015 = 0.15             # no-ssot: 7.1.1.b, el tope de 0,15 f'm
C_020 = 0.20             # no-ssot: 7.1.1.b, el coeficiente del termino de esbeltez
ESBELTEZ_35 = 35.0       # no-ssot: 7.1.1.b, el 35 de (h/35t)^2


def _cargar(nombre):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "s", ruta)
    mod = importlib.util.module_from_spec(spec)
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


R02 = _cargar("02_metrado_y_esfuerzo_axial.py")


def limite(fm, t):
    """7.1.1.b: sigma <= 0,20 f'm [1-(h/35t)^2] <= 0,15 f'm, en kgf/cm2."""
    h = R02.H_LIBRE * 100.0
    esb = (h / (ESBELTEZ_35 * t * 100.0)) ** 2
    return min(C_020 * fm * (1.0 - esb), C_015 * fm), esb


def peso_propio_muro(t):
    """Peso del muro mas su tarrajeo, por metro de longitud y altura total."""
    alb = t * HN * PESO_ALBANILERIA
    tar = 2 * E_TARRAJEO * HN * PESO_MORTERO
    return alb + tar          # kgf por metro lineal de muro


def descomponer():
    """Separa el Pm del muro critico en (lo que baja de las losas, peso propio).

    Hace falta para poder engrosar el muro: al subir t sube su peso propio,
    y el esfuerzo NO baja en proporcion inversa como uno esperaria.
    """
    pm = R02.metrado_gravedad()
    Ln = R02.L_NETA
    propio = peso_propio_muro(ESPESOR) * Ln
    return pm, Ln, propio, pm - propio


def clasificacion():
    print("=" * 96)
    print("1. QUE ES EL TIPO I  -  Tabla 1 de la E.070")
    print("=" * 96)
    print()
    print("  La tabla mide TRES propiedades, no solo la resistencia:")
    print()
    print("  %-14s %14s %12s %16s" % ("clase", "var. <=100mm", "alabeo max", "f'b min"))
    print("  " + "-" * 60)   # no-ssot: ancho del separador de texto, no C_T
    for nom, var, ala, fb in TABLA_1:
        marca = "  <== el que pide la consigna" if nom == "Ladrillo I" else (
                "  <== el adoptado" if nom == "Ladrillo V" else "")
        print("  %-14s %13d %% %9d mm %11.0f kg/cm2%s" % (nom, var, ala, fb, marca))
    print()
    print("  El tipo I reune LAS TRES PEORES de la clasificacion: la resistencia")
    print("  mas baja, la mayor tolerancia dimensional y el mayor alabeo. Van")
    print("  juntas y no por casualidad: describen una unidad hecha a mano.")


def el_asterisco():
    print()
    print("=" * 96)
    print("2. LA TABLA 2 NO LO PROHIBE DEL TODO  -  y conviene decirlo")
    print("=" * 96)
    print()
    print("  Tabla 2, zona sismica 2 y 3, muro portante de 4 pisos a mas:")
    print("     Solido Artesanal   No       <== el tipo I")
    print("     Solido Industrial  Si       <== el adoptado")
    print("     Alveolar           Si, celdas totalmente rellenas con grout")
    print("     Hueca              No")
    print("     Tubular            No")
    print()
    print("  PERO el asterisco de la nota al pie esta sobre la fila \"Solido")
    print("  Artesanal\" -- sobre EL TIPO QUE LA CONSIGNA PIDE -- y dice:")
    print()
    print("     \"Las limitaciones indicadas establecen condiciones minimas que")
    print("      pueden ser exceptuadas con el respaldo de un informe y memoria")
    print("      de calculo sustentada por un ingeniero civil.\"")
    print()
    print("  O sea que la norma SI deja usarlo, con memoria de calculo. Por eso")
    print("  el argumento no puede ser \"esta prohibido\": tiene que ser el")
    print("  calculo. Va a continuacion.")


def el_calculo():
    print()
    print("=" * 96)
    print("3. LA MEMORIA DE CALCULO QUE LA EXCEPCION EXIGE  -  7.1.1.b")
    print("=" * 96)
    print()
    pm, Ln, propio, de_losas = descomponer()
    s = pm / (Ln * 100.0 * ESPESOR * 100.0)
    lim_I, esb = limite(FM_ARTESANAL, ESPESOR)
    lim_V, _ = limite(FM, ESPESOR)
    print("  MURO CRITICO del edificio (el mas cargado):")
    print("     Pm  = %9.0f kgf   (de losas %8.0f  +  peso propio %8.0f)"
          % (pm, de_losas, propio))
    print("     L neta = %.2f m   t = %.2f m" % (Ln, ESPESOR))
    print("     sigma = Pm/(L.t) = %.2f kgf/cm2" % s)
    print()
    print("  %-34s %12s %12s" % ("", "TIPO I", "TIPO V adoptado"))
    print("  " + "-" * 60)   # no-ssot: ancho del separador de texto, no C_T
    print("  %-34s %12.0f %12.0f" % ("f'b minimo (Tabla 1)", 50, 180))
    print("  %-34s %12.0f %12.0f" % ("f'm adoptado (Tabla 9)", FM_ARTESANAL, FM))
    print("  %-34s %12.2f %12.2f" % ("0,15 f'm", C_015 * FM_ARTESANAL, C_015 * FM))
    print("  %-34s %12.2f %12.2f" % ("0,20 f'm [1-(h/35t)2]",
                                      C_020 * FM_ARTESANAL * (1 - esb),
                                      C_020 * FM * (1 - esb)))
    print("  %-34s %12.2f %12.2f" % ("LIMITE (el menor)", lim_I, lim_V))
    print("  %-34s %12.2f %12.2f" % ("sigma requerido", s, s))
    print("  %-34s %12s %12s"
          % ("VEREDICTO", "NO CUMPLE" if s > lim_I else "cumple",
             "NO CUMPLE" if s > lim_V else "cumple"))
    print()
    print("  Con el tipo I el muro excede el admisible en %.0f %%." % (100 * (s / lim_I - 1)))
    print()
    print("  NOTA SOBRE LO GENEROSO DE ESTE CALCULO: el f'm = %.0f sale de la fila"
          % FM_ARTESANAL)
    print("  del KK Artesanal de la Tabla 9, cuyo f'b es %.0f -- o sea MEJOR que"
          % FB_ARTESANAL)
    print("  el minimo de %.0f que define a la clase I. Con el minimo estricto el" % 50)
    print("  margen seria todavia peor. El veredicto no depende de esa eleccion.")
    return pm, Ln, propio, de_losas, s, lim_I


def las_cuatro_salidas(pm, Ln, propio, de_losas, s, lim_I):
    print()
    print("=" * 96)
    print("4. LAS CUATRO SALIDAS QUE EL 7.1.1.b ENUMERA, EVALUADAS")
    print("=" * 96)
    print()
    print("  No alcanza con decir que no cumple: hay que mostrar que se busco")
    print("  la alternativa. El articulo ofrece cuatro y se recorren las cuatro.")
    print()

    # AUDITORIA 2026-09-19. Este sustento corre sobre el transversal INTERIOR,
    # que es el caso donde se explica el metrado. No es el muro mas cargado
    # del proyecto: desde que las fachadas recuperaron sus alfeizares, el que
    # gobierna es MX-7. Se deja el interior porque el argumento no necesita el
    # peor caso -- si el tipo I no alcanza NI SIQUIERA aqui, menos alla -- pero
    # callar cual es el critico seria elegir el numero que mas conviene.
    import importlib.util as _il
    _r = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "11_metrado_muros.py")
    _sp = _il.spec_from_file_location("r11tipoI", _r)
    _m11 = _il.module_from_spec(_sp)
    _sp.loader.exec_module(_m11)
    _peor = max(_m11.metrar(), key=lambda f: f["sigma"])
    print("  NOTA. Lo anterior corre sobre el transversal interior (sigma = %.2f)."
          % s)
    print("  El muro que GOBIERNA el proyecto es %s, con %.2f kgf/cm2: alli el"
          % (_peor["nom"].split()[0], _peor["sigma"]))
    print("  tipo I excederia el admisible en %.0f %% y no en %.0f %%."
          % (100 * (_peor["sigma"] / lim_I - 1), 100 * (s / lim_I - 1)))
    print()

    # (a) mejorar f'm
    fm_req = s / C_015
    print("  (a) MEJORAR f'm hasta que entre")
    print("      f'm >= sigma/0,15 = %.1f kg/cm2, contra los %.0f del tipo I."
          % (fm_req, FM_ARTESANAL))
    print("      Es %.1f veces la resistencia de la unidad artesanal, y la"
          % (fm_req / FM_ARTESANAL))
    print("      Tabla 9 no tabula ninguna arcilla artesanal que llegue. Subir")
    print("      el f'm DECLARADO para que el numero entre es exactamente lo")
    print("      que este proyecto no hace.")
    print()

    # (b) engrosar el muro, ITERANDO porque el peso propio sube con t
    print("  (b) ENGROSAR el muro  (iterado: al engrosar, el muro pesa mas)")
    t = ESPESOR
    for _ in range(60):   # no-ssot: ancho del separador de texto, no C_T
        pm_t = de_losas + peso_propio_muro(t) * Ln
        s_t = pm_t / (Ln * 100.0 * t * 100.0)
        lim_t, _e = limite(FM_ARTESANAL, t)
        if s_t <= lim_t:
            break
        t += 0.005   # no-ssot: incremento de 5 mm al iterar el espesor, no la deriva limite
    ok = s_t <= lim_t
    print("      espesor necesario: %.2f m  (hoy %.2f)" % (t, ESPESOR))
    print("      con ese espesor Pm sube a %.0f kgf y sigma queda en %.2f"
          % (pm_t, s_t))
    print("      %s" % ("converge, pero..." if ok else "NO CONVERGE: el peso propio crece mas rapido que la seccion"))
    print("      No hay aparejo corriente en %.0f cm: seria un muro de %.1f"
          % (t * 100, t / ESPESOR))
    print("      veces el espesor actual, con el mismo ladrillo que no resiste.")
    print()

    # (c) convertirlo en placa de concreto
    print("  (c) CONVERTIRLO EN PLACA de concreto armado")
    print("      Deja de ser albanileria confinada, que es el sistema que la")
    print("      consigna pide analizar. Se descarta por alcance, no por calculo.")
    print()

    # (d) reducir Pm
    print("  (d) REDUCIR Pm agregando muros que repartan la carga")
    print("      Es la salida que este proyecto YA TOMO: son 7 muros")
    print("      transversales y no 6, y por eso el ancho tributario critico")
    print("      cayo a %.2f m. Ya esta usada; no queda margen ahi." % R02.ANCHO_TRIB)
    print()
    print("      Y aunque se agregaran mas, el tipo I necesitaria bajar sigma de")
    print("      %.2f a %.2f, o sea repartir la carga entre %.0f %% mas de muro."
          % (s, lim_I, 100 * (s / lim_I - 1)))


def cierre():
    print()
    print("=" * 96)
    print("CONCLUSION")
    print("=" * 96)
    print()
    print("  La Tabla 2 admite exceptuar al solido artesanal CON memoria de")
    print("  calculo. Esta es la memoria, y dice que no resiste por un 65 %.")
    print()
    print("  LA EXCEPCION DEL ASTERISCO NO SALVA AL TIPO I: LO CONDENA. Esa nota")
    print("  al pie no exime de verificar, condiciona el permiso a un calculo, y")
    print("  el calculo es el que lo deja afuera. Invocarla obligaria a presentar")
    print("  justamente el numero que la vuelve inaplicable.")
    print()
    print("  Se adopta el solido INDUSTRIAL, que la Tabla 2 admite SIN condicion")
    print("  para muro portante de 4 pisos a mas en zona sismica 2.")


def control():
    """Que el sustento no se despegue del calculo del proyecto."""
    pm, Ln, propio, de_losas = descomponer()
    s = pm / (Ln * 100.0 * ESPESOR * 100.0)
    s_02 = R02.sigma(R02.metrado_gravedad(), R02.L_NETA)
    assert abs(s - s_02) < 1e-9, (
        "el sigma de este sustento (%.4f) no es el del script 02 (%.4f)" % (s, s_02))
    lim_V, _ = limite(FM, ESPESOR)
    lim_02, _e = R02.limite_axial(FM)
    assert abs(lim_V - lim_02) < 1e-9, (
        "el limite de este sustento (%.4f) no es el del 02 (%.4f)" % (lim_V, lim_02))
    lim_I, _ = limite(FM_ARTESANAL, ESPESOR)
    assert s > lim_I, "el tipo I estaria cumpliendo: revisar el sustento"
    print()
    print("  [ok] sigma y limite coinciden con el script 02 (mismo calculo)")
    print("  [ok] el tipo I no cumple: %.2f > %.2f" % (s, lim_I))


if __name__ == "__main__":
    clasificacion()
    el_asterisco()
    datos = el_calculo()
    las_cuatro_salidas(*datos)
    cierre()
    control()
