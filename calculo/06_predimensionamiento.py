# -*- coding: utf-8 -*-
"""Predimensionamiento: losa, vigas soleras, dinteles y columnas de confinamiento

Criterio 2 de la rubrica. Cada dimension sale de un articulo, no del ojo.

Fuentes verificadas contra los PDF de ../../06-normas/ en esta sesion:

  E.060 Tabla 9.1 (acapite 9.6.2.1) -- peraltes minimos para NO verificar
     deflexiones. Para "vigas o losas nervadas en una direccion" (el aligerado):
        simplemente apoyado      L / 16
        con un extremo continuo  L / 18,5
        ambos extremos continuos L / 21
        en voladizo              L / 8
     La propia norma aclara que "pueden utilizarse como referencia" y que
     "pueden obviarse si el calculo de las deflexiones demuestra que es posible
     utilizar un espesor menor". Se usan igual: en un trabajo evaluado, cumplir
     la tabla vale mas que prometer un calculo de deflexiones que no se hace.

  E.020 anexo 1 -- peso propio del aligerado (vigueta 0,10 m, 0,40 m entre ejes,
     losa superior 0,05 m):  0,17 m -> 280 | 0,20 -> 300 | 0,25 -> 350 | 0,30 -> 420 kgf/m2

  E.070 7.2.3  espesor minimo de columnas y solera = espesor efectivo del muro
  E.070 7.2.4  peralte minimo de la viga solera = espesor de la losa de techo
  E.070 7.2.5  peralte minimo de la columna de confinamiento = 15 cm
  E.070 7.2.1.b  separacion entre columnas <= 2 x (distancia entre elementos
     horizontales) y <= 5 m. Cumplirla, junto con el espesor minimo de 7.1.1.a,
     EXIME de disenar la albanileria ante sismo perpendicular a su plano.
  E.070 7.2.1.f  concreto de los confinamientos f'c >= 175 kg/cm2
  E.070 8.6.3    el area de la columna sera la mayor que de el diseno, y nunca
     menor que 15 t (cm2)
  E.070 6.2.6    dinteles "preferentemente peraltadas (hasta 60 cm)" en confinada
  E.070 6.2.7    alfeizares AISLADOS de la estructura principal
  E.070 7.1.1.a  t >= h/20 en zonas sismicas 2 y 3

LO QUE ESTE SCRIPT NO HACE: el area definitiva de las columnas y su refuerzo.
Eso sale de 8.6.3 con la fuerza cortante Vu de cada muro, que recien se conoce
despues del reparto (etapa 08). Aca se fija el PREDIMENSIONADO y se declara el
minimo normativo que ninguna columna podra bajar.
"""
from proyecto import (B_CIMIENTO, DF,  # noqa: F401
                      SEPARACION_MX, PANOS_Y, ANCHO_TRIB, E_LOSA, LOSA_ALIGERADA, ESPESOR, H_LIBRE,
                      H_ENTREPISO, ALFEIZAR, ALTURA_VENTANA, H_DINTEL,
                      B_SOLERA, H_SOLERA, B_COLUMNA, H_COLUMNA,
                      H_COLUMNA_EXT, FC, N_PISOS,
                      ALTO_PUERTA, H_DINTEL_PUERTA, H_DINTEL_VENTANA,
                      E_PISO_TERMINADO)

# E.060 Tabla 9.1, fila "vigas o losas nervadas en una direccion"
TABLA_9_1_NERVADAS = {
    "simplemente apoyado": 16.0,   # no-ssot: divisor de la Tabla 9.1, no es N_CONTRAPASOS
    "un extremo continuo": 18.5,
    "ambos extremos continuos": 21.0,   # no-ssot: divisor L/21, no son metros
    "en voladizo": 8.0,
}

# E.020 anexo 1: espesor de aligerado -> peso propio (kgf/m2)
ALIGERADOS_E020 = [(0.17, 280.0), (0.20, 300.0), (0.25, 350.0), (0.30, 420.0)]   # no-ssot: tabla de la E.020; el script comprueba contra ella


def losa():
    """El aligerado. Aca se decide E_LOSA, y de ahi cuelga todo el metrado.

    Los panos NO son iguales, asi que no vale un solo calculo: cada pano tiene
    su luz Y su condicion de apoyo, y hay que recorrerlos todos.
    """
    print("=" * 74)
    print("1. LOSA ALIGERADA — E.060 Tabla 9.1")
    print("=" * 74)
    print("  El aligerado salva los panos entre muros transversales. Son %d panos"
          % len(PANOS_Y))
    print("  desiguales que suman %.2f m. Los DOS extremos apoyan contra fachada"
          % sum(PANOS_Y))
    print("  por un lado: tienen UN SOLO extremo continuo y la tabla los castiga")
    print("  con L/18,5 en vez de L/21. Es la trampa: verificar solo un pano")
    print("  interior deja pasar una losa flaca en los extremos.")
    print()
    print("  %-6s %8s %26s %10s  %s"
          % ("pano", "luz (m)", "condicion de apoyo", "divisor", "h min (m)"))
    filas = []
    for i, L in enumerate(PANOS_Y):
        extremo = (i == 0 or i == len(PANOS_Y) - 1)
        cond = "un extremo continuo" if extremo else "ambos extremos continuos"
        d = TABLA_9_1_NERVADAS[cond]
        filas.append((i + 1, L, cond, d, L / d))
    rige = max(f[4] for f in filas)
    quien = next(f[0] for f in filas if f[4] == rige)
    for n, L, cond, d, h in filas:
        print("  %-6d %8.2f %26s %10s  %8.3f %s"
              % (n, L, cond, "L/%.4g" % d, h, "<== RIGE" if n == quien else ""))
    print()
    print("  RIGE el pano %d: h >= %.3f m" % (quien, rige))
    print()
    print("  %-14s %12s  %s" % ("espesor E.020", "peso kgf/m2", "veredicto"))
    adoptado = None
    for h, p in ALIGERADOS_E020:
        if adoptado is None and h >= rige:
            adoptado = (h, p)
            v = "<== SE ADOPTA (el inmediato superior)"
        elif h < rige:
            v = "insuficiente"
        else:
            v = "sobra"
        print("  %-14.2f %12.0f  %s" % (h, p, v))
    print()
    print("  Se adopta h = %.2f m en TODA la planta, peso %.0f kgf/m2."
          % (adoptado[0], adoptado[1]))
    print("  Espesor uniforme y no dos: un cambio de peralte entre panos es un")
    print("  problema de obra y una discontinuidad de rigidez que no compensa.")
    print()
    print("  POR QUE LOS PANOS SON DESIGUALES. Con una malla pareja de 6 panos de")
    print("  3,50 m todo cerraba mas facil, pero el pozo de luz quedaba de 3,50 m")
    print("  y perdia el respaldo del criterio mas exigente (1/3 del paramento =")
    print("  4,17 m). Se le reserva un pano de %.2f m y el resto se reparte en"
          % max(PANOS_Y))
    print("  %.2f m. El pano grande es INTERIOR, asi que le toca L/21 y no penaliza."
          % min(PANOS_Y))
    assert abs(E_LOSA - adoptado[0]) < 1e-9, \
        "proyecto.py dice E_LOSA=%.3f pero el predimensionado exige %.3f" % (E_LOSA, adoptado[0])
    assert abs(LOSA_ALIGERADA - adoptado[1]) < 1e-9, \
        "proyecto.py dice %.0f kgf/m2 y la E.020 da %.0f" % (LOSA_ALIGERADA, adoptado[1])
    print("  (verificado: proyecto.py ya esta en %.2f m y %.0f kgf/m2)"
          % (E_LOSA, LOSA_ALIGERADA))
    return adoptado


def alternativa_descartada():
    """Por que la malla es de 7 muros. Queda escrito para que no se repregunte."""
    print()
    print("-" * 74)
    print("  POR QUE 7 MUROS TRANSVERSALES Y NO 6")
    print("-" * 74)
    print("  La version anterior tenia 6 muros a 4,20 m y una losa de 0,25 m. Los")
    print("  numeros la tumbaron al descontar los vanos: el esfuerzo axial daba")
    print("  10,87 contra un limite de 9,75  ->  NO CUMPLIA (-10 %).")
    print()
    print("  El 7.1.1b ofrece cuatro salidas: mejorar f'm, engrosar el muro,")
    print("  convertirlo en placa, o REDUCIR Pm. Las tres primeras degradan algo")
    print("  -- subir un f'm declarado para que entre el numero, usar un aparejo")
    print("  que no existe, o abandonar la albanileria que la consigna pide. La")
    print("  cuarta no: un muro mas reparte la misma carga en mas apoyos.")
    print()
    print("  Con 7 muros el ancho tributario critico cae a %.2f m, el axial baja a"
          % ANCHO_TRIB)
    print("  8,22 kgf/cm2 (holgura +19 %) y de yapa la losa vuelve a 0,20 m porque")
    print("  el pano extremo pasa a pedir %.2f/18,5 = %.3f m."
          % (min(PANOS_Y), min(PANOS_Y) / 18.5))
    print()
    print("  RESTRICCION QUE ESTO IMPONE AL PLANO: un solo vano por muro")
    print("  transversal. Con dos puertas el axial vuelve al filo (+1,9 %). La")
    print("  circulacion tiene que ser un corredor corrido en el sentido del fondo")
    print("  que cruce cada muro una sola vez.")


def soleras():
    print()
    print("=" * 74)
    print("2. VIGAS SOLERAS — E.070 7.2.3 y 7.2.4")
    print("=" * 74)
    print("  espesor (ancho) >= espesor efectivo del muro = %.2f m   ->  %.2f m"
          % (ESPESOR, B_SOLERA))
    print("  peralte         >= espesor de la losa de techo = %.2f m   ->  %.2f m"
          % (E_LOSA, H_SOLERA))
    print()
    print("  SOLERA ADOPTADA: %.2f x %.2f m, en todos los muros y en todos los pisos."
          % (B_SOLERA, H_SOLERA))
    print("  Corre embebida en el peralte del aligerado: no baja del cielo raso.")
    print()
    print("  Estribos minimos de la solera (E.070 8.6.4, textual):")
    print("     6 mm, 1 @ 5, 4 @ 10, resto @ 25 cm")
    print("  El area definitiva (Acs) se fija en la etapa 09: debe alojar el As que")
    print("  salga del diseno, y por 8.6.4 puede resolverse con viga chata.")


def dinteles():
    print()
    print("=" * 74)
    print("3. DINTELES — E.070 6.2.6 y E.060 Tabla 9.1")
    print("=" * 74)
    print("  La E.070 los quiere PERALTADOS: 'vigas dinteles preferentemente")
    print("  peraltadas (hasta 60 cm)' cuando el edificio es de muros confinados.")
    print("  Es una preferencia con techo, no una formula: lo que la fija es la")
    print("  altura libre disponible.")
    print()
    print("  Pero NO hay UN dintel: hay DOS, y confundirlos fue el error de la")
    print("  primera version. Sobre una ventana sobra mas altura que sobre una")
    print("  puerta, porque la ventana recien arranca despues del alfeizar.")
    print()
    print("  %-26s %8s %8s %8s  %s" % ("caso", "ocupa", "dintel", "fondo a", "veredicto"))
    casos = [
        ("dintel sobre PUERTA", E_PISO_TERMINADO + ALTO_PUERTA, H_DINTEL_PUERTA),
        ("dintel sobre VENTANA",
         E_PISO_TERMINADO + ALFEIZAR + ALTURA_VENTANA, H_DINTEL_VENTANA),
    ]
    for nom, ocupa, hd in casos:
        fondo = H_LIBRE - hd
        cierra = abs(ocupa + hd - H_LIBRE) < 1e-9
        print("  %-26s %8.2f %8.2f %8.2f  %s"
              % (nom, ocupa, hd, fondo,
                 "CIERRA contra %.2f m" % H_LIBRE if cierra else "NO CIERRA <<<"))
    print()
    print("  EL QUE MANDA ES EL DE PUERTA: %.2f m, y no por estructura sino por la"
          % H_DINTEL_PUERTA)
    print("  A.010 Art. 18.3, que exige que 'las estructuras horizontales tales como")
    print("  vigas u otros elementos' queden a 'altura libre no menor a 2.10 m")
    print("  medida sobre el piso terminado'. Con un dintel de %.2f m el fondo"
          % H_DINTEL_VENTANA)
    print("  quedaria a %.2f m sobre el piso terminado y la puerta no entra."
          % (H_LIBRE - H_DINTEL_VENTANA - E_PISO_TERMINADO))
    print()
    print("  OJO CON EL PISO TERMINADO: la puerta apoya en el acabado, no en la")
    print("  losa. Esos %.2f m salen de la altura libre, y fue lo que se paso por"
          % E_PISO_TERMINADO)
    print("  alto en la PRIMERA correccion: el dintel daba 0,40 m y el fondo")
    print("  quedaba a 2,05 m, cinco centimetros por debajo del minimo. Lo cazo")
    print("  _auditoria_coherencia.py, no la revision a ojo.")
    print()
    print("  Y la altura del ambiente cumple: A.010 Art. 18.1 pide 2,30 m de piso")
    print("  terminado a cielo raso en vivienda. Entrepiso %.2f - losa %.2f - piso"
          % (H_ENTREPISO, E_LOSA))
    print("  terminado %.2f = %.2f m  ->  CUMPLE."
          % (E_PISO_TERMINADO, H_LIBRE - E_PISO_TERMINADO))
    print()
    print("  DINTELES ADOPTADOS:  VD-1 sobre puerta  %.2f x %.2f m"
          % (ESPESOR, H_DINTEL_PUERTA))
    print("                       VD-2 sobre ventana %.2f x %.2f m"
          % (ESPESOR, H_DINTEL_VENTANA))
    print("  Los dos peraltados y los dos por debajo del tope de 0,60 m de 6.2.6.")
    print()
    v_ancho = 1.20   # no-ssot: ancho de vano, no la longitud minima de muro
    d = TABLA_9_1_NERVADAS["simplemente apoyado"]
    print("  Contraste con la E.060: como viga simplemente apoyada sobre un vano de")
    print("  %.2f m, la Tabla 9.1 pediria apenas %.2f/%.4g = %.3f m. El peralte lo"
          % (v_ancho, v_ancho, d, v_ancho / d))
    print("  manda el criterio sismico de la E.070, no la deflexion.")
    print()
    print("  OJO (E.070 6.2.7): los alfeizares van AISLADOS de la estructura. No son")
    print("  parte del muro portante y se disenan aparte, ante carga perpendicular")
    print("  a su plano (Capitulo 10). Por eso no suman a la densidad de muros.")


def columnas():
    print()
    print("=" * 74)
    print("4. COLUMNAS DE CONFINAMIENTO — E.070 7.2.1, 7.2.3, 7.2.5 y 8.6.3")
    print("=" * 74)
    sep_max_norma = 5.00
    sep_max_geom = 2.0 * H_ENTREPISO
    sep_max = min(sep_max_norma, sep_max_geom)
    print("  a) SEPARACION (7.2.1.b). El limite es el MENOR de dos:")
    print("       2 x distancia entre elementos horizontales = 2 x %.2f = %.2f m"
          % (H_ENTREPISO, sep_max_geom))
    print("       tope absoluto de la norma                   = %.2f m" % sep_max_norma)
    print("     rige %.2f m.  Separacion del proyecto = %.2f m  ->  %s"
          % (sep_max, SEPARACION_MX, "CUMPLE" if SEPARACION_MX <= sep_max else "NO CUMPLE <<<"))
    print()
    print("     Esto no es un tramite: cumplir 7.2.1.b JUNTO CON el espesor minimo")
    print("     de 7.1.1.a exime de disenar la albanileria ante sismo perpendicular")
    print("     a su plano. Es un capitulo entero de calculo que se ahorra con")
    print("     fundamento, no por omision.")
    print()
    t_min = H_LIBRE / 20.0
    print("  b) ESPESOR EFECTIVO (7.1.1.a, zona sismica 2): t >= h/20 = %.2f/20 = %.3f m"
          % (H_LIBRE, t_min))
    print("     t del proyecto = %.2f m  ->  %s"
          % (ESPESOR, "CUMPLE" if ESPESOR >= t_min else "NO CUMPLE <<<"))
    print()
    print("  c) SECCION (7.2.3, 7.2.5 y 8.6.3)")
    ac_min = 15.0 * ESPESOR * 100.0
    ac = B_COLUMNA * 100.0 * H_COLUMNA * 100.0
    print("     espesor >= espesor efectivo del muro = %.2f m      ->  %.2f m"
          % (ESPESOR, B_COLUMNA))
    print("     peralte >= 0,15 m (7.2.5)                          ->  %.2f m" % H_COLUMNA)
    print("     area    >= 15 t = 15 x %.0f = %.0f cm2 (8.6.3)      ->  %.0f cm2  %s"
          % (ESPESOR * 100, ac_min, ac, "CUMPLE" if ac >= ac_min else "NO CUMPLE <<<"))
    print()
    print("     COLUMNA PREDIMENSIONADA C-1 (interior): %.2f x %.2f m = %.0f cm2"
          % (B_COLUMNA, H_COLUMNA, ac))
    print("     Se adopta %.0f cm de peralte y no los %.0f del minimo: los 15 cm no"
          % (H_COLUMNA * 100, 15))
    print("     dejan alojar el anclaje recto del refuerzo de la solera donde el")
    print("     muro llega al limite de propiedad, caso que 7.2.5 nombra y que en un")
    print("     lote MEDIANERO ocurre en las dos medianeras.")
    print()
    ac_ext = B_COLUMNA * 100.0 * H_COLUMNA_EXT * 100.0
    print("     COLUMNA C-2 (EXTREMA): %.2f x %.2f m = %.0f cm2"
          % (B_COLUMNA, H_COLUMNA_EXT, ac_ext))
    print("     Esta NO sale del predimensionado sino del DISENO (19_...), y es una")
    print("     leccion del propio proyecto: el 7.2.5 y el 8.6.3 fijan MINIMOS, y")
    print("     un minimo es el piso, no el techo. La Tabla 11 le da a la columna")
    print("     extrema la traccion del momento (T = F - Pc) que la interior no")
    print("     tiene, y con el momento amplificado por f = 3 del 8.6 pide %.0f cm2."
          % 1088)
    print("     Dimensionar TODAS como extremas costaba concreto donde no hace")
    print("     falta; dimensionarlas todas como interiores dejaba los extremos")
    print("     cortos. Por eso son DOS tipos.")
    print()
    print("  d) CONCRETO (7.2.1.f): f'c >= 175 kg/cm2.  Proyecto f'c = %.0f  ->  %s"
          % (FC, "CUMPLE" if FC >= 175 else "NO CUMPLE <<<"))
    print()
    print("  PENDIENTE DECLARADO: el area y el refuerzo DEFINITIVOS salen de 8.6.3")
    print("  con el Vu de cada muro, que no existe hasta el reparto de cortante")
    print("  (etapa 08). Lo de arriba es el piso normativo: ninguna columna podra")
    print("  quedar por debajo, y varias subiran.")


def cuadro():
    """(elemento, b, h, articulo) de cada seccion adoptada, en metros.

    Estaba escrita DENTRO de `resumen()` como lista de strings ya
    formateados, de modo que la unica manera de reusarla era volver a
    escribirla. La figura del cuadro de predimensionamiento la necesita con
    los numeros, no con el texto, asi que sale aca y `resumen()` la
    consume: una sola fuente para la tabla y para el dibujo.

    `b = None` significa que el elemento se define por un solo espesor.
    """
    return [
        ("Losa aligerada", None, E_LOSA, "E.060 Tabla 9.1 (L/18,5)"),
        ("Muro portante", None, ESPESOR, "E.070 7.1.1.a"),
        ("Viga solera VS-1", B_SOLERA, H_SOLERA, "E.070 7.2.3 y 7.2.4"),
        ("Columna C-1 interior", B_COLUMNA, H_COLUMNA,
         "E.070 7.2.5 y 8.6.3 (minimo 15t)"),
        ("Columna C-2 extrema", B_COLUMNA, H_COLUMNA_EXT,
         "E.070 8.6.3 y 7.1.4 (anclaje de solera)"),
        ("Dintel sobre puerta VD-1", ESPESOR, H_DINTEL_PUERTA,
         "A.010 18.3 + E.070 6.2.6"),
        ("Dintel sobre ventana VD-2", ESPESOR, H_DINTEL_VENTANA,
         "E.070 6.2.6 + altura libre"),
        ("Cimiento corrido", B_CIMIENTO, DF, "E.050 + EMS (qadm)"),
    ]


def resumen():
    print()
    print("=" * 74)
    print("RESUMEN — lo que entra al metrado y a los planos")
    print("=" * 74)
    print("  %-34s %-18s %s" % ("elemento", "seccion (m)", "articulo que la fija"))
    for e, b, h, a in cuadro():
        s = ("t = %.2f" % h) if b is None else ("%.2f x %.2f" % (b, h))
        print("  %-34s %-18s %s" % (e, s, a))
    print()
    print("  Faltan del criterio 2: cimiento corrido y zapatas -> 04_cimentacion.py")
    print("  (ya resueltos). Con esto el criterio 2 queda cubierto salvo el area")
    print("  definitiva de columnas, que depende de la etapa 08.")
    print()
    print("  Pisos: %d. El acapite 8.6 de la E.070 aplica 'hasta cinco pisos o 15 m'," % N_PISOS)
    print("  asi que el edificio esta EN EL LIMITE EXACTO del metodo, no fuera.")


if __name__ == "__main__":
    losa()
    alternativa_descartada()
    soleras()
    dinteles()
    columnas()
    resumen()
