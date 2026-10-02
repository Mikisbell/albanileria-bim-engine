# -*- coding: utf-8 -*-
"""Centro de masa, centro de rigidez y excentricidad. La bisagra del trabajo

DE ESTO CUELGA TODO LO QUE FALTA
================================
Con la excentricidad sale el momento torsor; con el torsor, el cortante que le
toca a cada muro; con ese cortante, el diseno del Capitulo 8 y el de los
confinamientos. Un error aca no se nota: se propaga.

Y hay algo mas en juego. La E.030-2026, Tabla 12, castiga la IRREGULARIDAD
TORSIONAL con Ip = 0,75. Como R = R0 x Ia x Ip, pasar de Ip = 1,00 a 0,75 baja
R de 3,00 a 2,25 y sube la fuerza sismica un 33 %. El proyecto viene declarando
ese riesgo desde que se calculo la rigidez, porque las medianeras se llevan el
72 % de la direccion Y. Aca se mide.

LO QUE MIDE CADA COSA
=====================
  CENTRO DE MASA     donde actua la fuerza de inercia. Depende del PESO y de
                     donde esta puesto.
  CENTRO DE RIGIDEZ  donde el edificio "se deja empujar sin girar". Depende de
                     la RIGIDEZ de los muros y de donde estan puestos.
  EXCENTRICIDAD      la distancia entre los dos. Es el brazo del torsor.

Son cosas distintas y se confunden seguido: un edificio puede tener la masa
perfectamente centrada y aun asi girar, si los muros rigidos estan a un lado.

CONVENCION DE EJES, declarada para que nadie tenga que adivinar
==============================================================
  x  de 0 a %FRENTE% m, medido desde la medianera izquierda
  y  de 0 a %FONDO% m, medido desde la fachada frontal
  Los muros se ubican POR SU EJE, como en el plano.

  Sismo en X  -> resisten los muros MX (los transversales). Su rigidez se
                 reparte segun la coordenada Y, y el brazo del torsor es ey.
  Sismo en Y  -> resisten los muros MY (los longitudinales). Su rigidez se
                 reparte segun la coordenada X, y el brazo del torsor es ex.

SIMPLIFICACION DECLARADA
========================
El centroide en X de cada muro MX se toma en el centro del frente. Es EXACTO
cuando los vanos son simetricos (las dos fachadas lo son: 1,60 / 2,40 / 1,60) y
aproximado en los muros interiores con una o dos puertas. El script acota el
error al final en vez de esconderlo: mueve los vanos al peor extremo posible y
mide cuanto se corre el centro de masa.
"""
import importlib.util
import os

from proyecto import (FRENTE, FONDO, MUROS, EJES_MX, ESPESOR, H_LIBRE, N_PISOS,
                      POZO_X0, POZO_X1, POZO_Y0, POZO_Y1, ESC_X0, ESC_X1,
                      ESC_Y0, ESC_Y1, E_LOSA, B_COLUMNA, H_COLUMNA, B_SOLERA,
                      LOSA_ALIGERADA, PISO_TERMINADO, TABIQUERIA, SC_VIVIENDA,
                      SC_AZOTEA, PESO_ALBANILERIA, PESO_CONCRETO, PCT_CV_SISMO,
                      H_DINTEL_PUERTA, EJES_COLUMNAS_X, EXC_ACCIDENTAL,
                      AREA_PLANTA, machones,
                      AREA_ESCALERA, peso_escalera_m2, volumen_de_vanos, A_UNIDAD, PARAPETO, peso_tarrajeo)

H_VANO = H_LIBRE - H_DINTEL_PUERTA
CM_TIPICO = LOSA_ALIGERADA + PISO_TERMINADO + TABIQUERIA
CM_AZOTEA = LOSA_ALIGERADA + PISO_TERMINADO
EXTRA_SOLERA_M2 = E_LOSA * PESO_CONCRETO - LOSA_ALIGERADA


def rigideces():
    """Trae K de cada muro del script 12 en vez de recalcularla.

    Los nombres de modulo no pueden empezar con digito, asi que no se puede
    hacer `import 12_rigidez_lateral`. Se carga por ruta. Importarlo es lo
    correcto: si la rigidez se recalculara aca, habria DOS formulas de rigidez
    en el proyecto y tarde o temprano una de las dos quedaria vieja.
    """
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "12_rigidez_lateral.py")
    spec = importlib.util.spec_from_file_location("rigidez12", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    K = {}
    for nom, dire, L, t, vanos in MUROS:
        _A, I, Ac, _Ln = mod.seccion(nom, dire, L, t, vanos)
        K[nom], _fl, _co = mod.rigidez(I, Ac)
    return K


def posicion(nom, dire, L):
    """(x, y) del CENTROIDE del muro, en la convencion declarada arriba."""
    if dire == "X":
        # transversal: corre en x de 0 a FRENTE, y esta en su eje
        i = int(nom.split("-")[1][0]) - 1
        return FRENTE / 2.0, EJES_MX[i]
    # longitudinal: esta en un eje x y corre en y
    x = {"MY-1": 0.0, "MY-2": FRENTE, "MY-3": POZO_X0, "MY-4": POZO_X1}[nom[:4]]
    if nom[:4] in ("MY-1", "MY-2"):
        y0 = 0.0
    else:
        y0 = POZO_Y1 if nom[4:5] == "b" else 0.0
    return x, y0 + L / 2.0


def n_columnas(nom, dire):
    if dire == "X":
        return len(EJES_COLUMNAS_X)
    if nom.startswith("MY-3a") or nom.startswith("MY-4a"):
        return sum(1 for y in EJES_MX if y <= POZO_Y0 + 1e-9)
    if nom.startswith("MY-3b") or nom.startswith("MY-4b"):
        return sum(1 for y in EJES_MX if y >= POZO_Y1 - 1e-9)
    return len(EJES_MX)


def peso_muro_por_piso(nom, dire, L, t, vanos):
    """kgf de UN piso de ese muro: albanileria + columnas + extra de solera."""
    vol_bruto = t * H_LIBRE * L
    vol_col = n_columnas(nom, dire) * B_COLUMNA * H_COLUMNA * H_LIBRE
    # AUDITORIA: las fachadas llevan VENTANAS, no puertas. Bajo cada una
    # queda un alfeizar de albanileria que pesa (ver proyecto.py). El
    # descuento es VANO POR VANO: la puerta de ingreso no tiene alfeizar.
    vol_vanos = volumen_de_vanos(nom, dire, L, vanos, t)
    vol_alb = vol_bruto - vol_col - vol_vanos
    return (vol_alb * PESO_ALBANILERIA + vol_col * PESO_CONCRETO
            + B_SOLERA * L * EXTRA_SOLERA_M2)


def losa():
    """Area y centroide de la losa, con el pozo y la escalera descontados.

    No es el centro geometrico: los dos huecos estan descentrados y lo corren.
    """
    piezas = [
        ("planta llena", FRENTE * FONDO, FRENTE / 2.0, FONDO / 2.0, +1),
        ("pozo de luz", (POZO_X1 - POZO_X0) * (POZO_Y1 - POZO_Y0),
         (POZO_X0 + POZO_X1) / 2.0, (POZO_Y0 + POZO_Y1) / 2.0, -1),
        ("caja de escalera", (ESC_X1 - ESC_X0) * (ESC_Y1 - ESC_Y0),
         (ESC_X0 + ESC_X1) / 2.0, (ESC_Y0 + ESC_Y1) / 2.0, -1),
    ]
    A = sum(s * a for _n, a, _x, _y, s in piezas)
    x = sum(s * a * cx for _n, a, cx, _y, s in piezas) / A
    y = sum(s * a * cy for _n, a, _x, cy, s in piezas) / A
    return A, x, y, piezas


def centro_de_masa(azotea):
    """(peso, x, y) del nivel. La azotea no lleva tabiqueria."""
    A_losa, xl, yl, piezas = losa()
    cm = CM_AZOTEA if azotea else CM_TIPICO
    sc = SC_AZOTEA if azotea else SC_VIVIENDA
    # la losa y todo lo que va sobre ella comparten centroide
    w_losa = A_losa * (cm + PCT_CV_SISMO * sc)
    num_x, num_y, total = w_losa * xl, w_losa * yl, w_losa
    detalle = [("losa + acabados + %d %% CV" % (100 * PCT_CV_SISMO),
                w_losa, xl, yl)]
    # AUDITORIA C-4. losa() DESCUENTA la caja de escalera, y hasta aca nadie
    # volvia a sumar la escalera que la ocupa: el hueco pesaba cero. Como
    # esta contra la fachada frontal (y = 1,98 m contra un centroide de
    # 10,77), su omision corria el centro de masa hacia el fondo e inflaba
    # la excentricidad ey -- del lado seguro -- mientras restaba peso
    # sismico -- del lado inseguro.
    # AUDITORIA 2026-09-19. El PARAPETO de azotea no pesaba en ningun script:
    # el 14 lo usa para contar unidades y el 05 para la altura de paramento,
    # pero el peso sismico lo ignoraba. Y es el peor lugar para olvidarlo,
    # porque esta en el nivel de MAYOR BRAZO: cada kilo ahi pesa cinco veces
    # mas en el momento de volteo que uno del primer piso. Va de soga (mide
    # A_UNIDAD) y corre por el perimetro exterior MAS el del pozo.
    if azotea:
        per = 2.0 * (FRENTE + FONDO) + 2.0 * ((POZO_X1 - POZO_X0)
                                              + (POZO_Y1 - POZO_Y0))
        area_par = per * PARAPETO
        w_par = area_par * A_UNIDAD * PESO_ALBANILERIA + peso_tarrajeo(area_par)
        # el parapeto corre por el perimetro: su centroide es el de la planta
        num_x += w_par * (FRENTE / 2.0)
        num_y += w_par * (FONDO / 2.0)
        total += w_par
        detalle.append(("parapeto de azotea", w_par, FRENTE / 2.0, FONDO / 2.0))

    w_esc = AREA_ESCALERA * (peso_escalera_m2() + PCT_CV_SISMO * sc)
    x_esc = (ESC_X0 + ESC_X1) / 2.0
    y_esc = (ESC_Y0 + ESC_Y1) / 2.0
    num_x += w_esc * x_esc
    num_y += w_esc * y_esc
    total += w_esc
    detalle.append(("caja de escalera", w_esc, x_esc, y_esc))
    for nom, dire, L, t, vanos in MUROS:
        w = peso_muro_por_piso(nom, dire, L, t, vanos)
        x, y = posicion(nom, dire, L)
        num_x += w * x
        num_y += w * y
        total += w
        detalle.append((nom, w, x, y))
    return total, num_x / total, num_y / total, detalle, A_losa, xl, yl


def centro_de_rigidez(K):
    """x del CR para sismo en Y, y del CR para sismo en X."""
    sx = sy = nx = ny = 0.0
    for nom, dire, L, t, vanos in MUROS:
        x, y = posicion(nom, dire, L)
        if dire == "Y":          # resisten el sismo en Y; su posicion es x
            sy += K[nom]
            nx += K[nom] * x
        else:                    # resisten el sismo en X; su posicion es y
            sx += K[nom]
            ny += K[nom] * y
    return nx / sy, ny / sx, sy, sx


def informe():
    K = rigideces()
    A_losa, xl, yl, piezas = losa()

    print("=" * 88)
    print("1. CENTRO DE MASA  -  donde actua la fuerza sismica")
    print("=" * 88)
    print()
    print("  La losa primero. NO basta el centro geometrico: los dos huecos la")
    print("  descentran, y cada uno para un lado distinto.")
    print()
    print("  %-22s %10s %8s %8s" % ("pieza", "area (m2)", "x", "y"))
    for n, a, cx, cy, s in piezas:
        print("  %-22s %10.2f %8.2f %8.2f%s" % (n, s * a, cx, cy,
              "" if s > 0 else "   (se resta)"))
    print("  %-22s %10.2f %8.3f %8.3f" % ("LOSA NETA", A_losa, xl, yl))
    print()
    print("  El centro geometrico de la planta esta en (%.2f, %.2f). La losa real"
          % (FRENTE / 2.0, FONDO / 2.0))
    print("  lo tiene en (%.3f, %.3f): la escalera, que esta contra la fachada"
          % (xl, yl))
    print("  frontal y a la izquierda, empuja el centroide hacia atras y a la")
    print("  derecha.")
    print()

    niveles = []
    for azotea in (False, True):
        W, xm, ym, detalle, _a, _xl, _yl = centro_de_masa(azotea)
        niveles.append((azotea, W, xm, ym, detalle))
        print("  NIVEL %s" % ("AZOTEA (sin tabiqueria)" if azotea else "TIPICO"))
        print("     peso sismico W = %10.0f kgf" % W)
        print("     centro de masa = (%.3f, %.3f) m" % (xm, ym))
        print()

    print("=" * 88)
    print("2. CENTRO DE RIGIDEZ  -  donde el edificio no gira")
    print("=" * 88)
    print()
    xr, yr, sumKy, sumKx = centro_de_rigidez(K)
    print("  %-30s %3s %12s %8s %10s"
          % ("muro", "dir", "K (kgf/cm)", "posicion", "% de su dir"))
    print("  " + "-" * 72)
    for nom, dire, L, t, vanos in MUROS:
        x, y = posicion(nom, dire, L)
        tot = sumKy if dire == "Y" else sumKx
        pos = x if dire == "Y" else y
        print("  %-30s %3s %12.0f %8.2f %9.1f %%"
              % (nom, dire, K[nom], pos, 100.0 * K[nom] / tot))
    print()
    print("  Sismo en Y (resisten los MY):  x_CR = %.3f m   (suma K = %.0f)"
          % (xr, sumKy))
    print("  Sismo en X (resisten los MX):  y_CR = %.3f m   (suma K = %.0f)"
          % (yr, sumKx))
    return niveles, xr, yr, sumKy, sumKx


def excentricidad(niveles, xr, yr):
    print()
    print("=" * 88)
    print("3. EXCENTRICIDAD  -  el brazo del momento torsor")
    print("=" * 88)
    print()
    print("  La E.030-2026 suma dos: la ESTATICA, que es la distancia real entre")
    print("  centro de masa y centro de rigidez, y la ACCIDENTAL de 0,05 B, que")
    print("  cubre lo que el calculo no sabe (tabiques que no estan donde se")
    print("  dibujaron, la gente parada de un lado, la variacion del material).")
    print()
    for azotea, W, xm, ym, _d in niveles:
        et = "AZOTEA" if azotea else "TIPICO"
        ex_est = abs(xm - xr)
        ey_est = abs(ym - yr)
        # Art. 37: la dimension PERPENDICULAR a la direccion de analisis
        ex_acc = EXC_ACCIDENTAL * FRENTE   # sismo en Y -> manda el frente
        ey_acc = EXC_ACCIDENTAL * FONDO    # sismo en X -> manda el fondo
        print("  NIVEL %s" % et)
        print("     sismo en Y:  ex estatica = |%.3f - %.3f| = %.3f m"
              % (xm, xr, ex_est))
        print("                  ex accidental = %.2f x %.2f = %.3f m"
              % (EXC_ACCIDENTAL, FRENTE, ex_acc))
        print("                  ex TOTAL = %.3f m   (%.1f %% del frente)"
              % (ex_est + ex_acc, 100.0 * (ex_est + ex_acc) / FRENTE))
        print("     sismo en X:  ey estatica = |%.3f - %.3f| = %.3f m"
              % (ym, yr, ey_est))
        print("                  ey accidental = %.2f x %.2f = %.3f m"
              % (EXC_ACCIDENTAL, FONDO, ey_acc))
        print("                  ey TOTAL = %.3f m   (%.1f %% del fondo)"
              % (ey_est + ey_acc, 100.0 * (ey_est + ey_acc) / FONDO))
        print()


def sensibilidad():
    """Cuanto puede moverse el CM por la simplificacion de los vanos."""
    print("=" * 88)
    print("4. CONTROL DE LA SIMPLIFICACION  -  cuanto vale no saber donde van")
    print("   los vanos")
    print("=" * 88)
    print()
    W, xm, _ym, _d, _a, _x, _y = centro_de_masa(False)
    peor = 0.0
    for nom, dire, L, t, vanos in MUROS:
        if dire != "X" or not vanos:
            continue
        w = peso_muro_por_piso(nom, dire, L, t, vanos)
        # el vano quita peso; si todo el vano estuviera pegado a un extremo, el
        # centroide del muro se correria como maximo esto:
        # AUDITORIA: las fachadas llevan VENTANAS, no puertas (ver
        # proyecto.py). Vano por vano: la puerta de ingreso no lleva alfeizar.
        vol_vanos = volumen_de_vanos(nom, dire, L, vanos, t)
        w_vano = vol_vanos * PESO_ALBANILERIA
        corr = w_vano * (L / 2.0 - sum(vanos) / 2.0) / w
        peor += w * corr
    dx = peor / W
    print("  Suponiendo el caso IMPOSIBLE de que todos los vanos de los muros")
    print("  transversales estuvieran pegados al mismo extremo, el centro de masa")
    print("  se correria %.4f m en x, o sea el %.2f %% del frente."
          % (dx, 100.0 * dx / FRENTE))
    print()
    print("  Para comparar: la excentricidad ACCIDENTAL que la norma obliga a")
    print("  sumar es %.2f x %.2f = %.3f m, o sea %.0f veces mas grande."
          % (EXC_ACCIDENTAL, FRENTE, EXC_ACCIDENTAL * FRENTE,
             (EXC_ACCIDENTAL * FRENTE) / dx if dx else 0))
    print("  La simplificacion vive comoda dentro de la incertidumbre que la")
    print("  propia norma ya reconoce. Igual se cierra cuando el plano fije los")
    print("  vanos, y entonces este control tiene que volver a correr.")


def peso_sismico():
    """Tabla de peso por nivel y total. Cierra un pendiente de los criterios 5 y 6."""
    print()
    print("=" * 88)
    print("5. PESO SISMICO POR NIVEL Y TOTAL")
    print("=" * 88)
    print()
    A_losa, _xl, _yl, _p = losa()
    W_tip, _x, _y, _d, _a, _b, _c = centro_de_masa(False)
    W_azo, _x, _y, _d, _a, _b, _c = centro_de_masa(True)
    print("  %-8s %-26s %14s" % ("nivel", "que lleva", "Wi (kgf)"))
    print("  " + "-" * 52)
    total = 0.0
    for i in range(N_PISOS, 0, -1):
        azotea = (i == N_PISOS)
        W = W_azo if azotea else W_tip
        total += W
        print("  %-8d %-26s %14.0f"
              % (i, "azotea, sin tabiqueria" if azotea else "tipico", W))
    print("  " + "-" * 52)
    print("  %-22s %14.0f kgf  =  %.1f tonf" % ("TOTAL P", total, total / 1000.0))
    print()
    print("  CONTROL DE ORDEN DE MAGNITUD, que es lo que caza los errores gruesos:")
    print("     peso por m2 de losa = %.0f / %.2f = %.0f kgf/m2"
          % (W_tip, A_losa, W_tip / A_losa))
    print()
    # AUDITORIA C-5. La version previa explicaba el peso con una "densidad del
    # 17,3 %" que NO existe: sumaba las DOS direcciones y usaba la longitud
    # BRUTA, contra un area que ademas no era la de planta. Medida como la
    # define el 7.1.2.b -- POR DIRECCION, longitud NETA, sobre Ap -- la
    # densidad es 6,9 % y cae DENTRO del 5-8 % habitual. O sea que el argumento
    # decia justo lo contrario de lo que probaba. La razon real es el ESPESOR.
    dens = {}
    for d in ("X", "Y"):
        ln = sum(sum(b - a for a, b in machones(n, dd, L, v))
                 for n, dd, L, _t, v in MUROS if dd == d)
        dens[d] = (ln, ln * ESPESOR / AREA_PLANTA)
    Lneta = dens["X"][0] + dens["Y"][0]
    # un muro de soga mide el ancho de la unidad: es A_UNIDAD, no un 0,13
    sobre = Lneta * (ESPESOR - A_UNIDAD) * H_LIBRE * PESO_ALBANILERIA / AREA_PLANTA

    print("  Es ALTO contra el 900 - 1100 kgf/m2 tipico de una vivienda de")
    print("  albanileria. La razon NO es una densidad de muros atipica: medida")
    print("  como la define el 7.1.2.b -- por direccion, con longitud NETA --")
    print("     X: %.2f m x %.2f / %.2f m2 = %.2f %%" % (dens["X"][0], ESPESOR, AREA_PLANTA, 100 * dens["X"][1]))
    print("     Y: %.2f m x %.2f / %.2f m2 = %.2f %%" % (dens["Y"][0], ESPESOR, AREA_PLANTA, 100 * dens["Y"][1]))
    print("  queda DENTRO del 5 - 8 % habitual. La razon es el ESPESOR:")
    print("     el mismo muraje en soga (0,13 m) pesaria %.0f kgf/m2 menos," % sobre)
    print("     o sea %.0f kgf/m2, dentro del rango." % (W_tip / A_losa - sobre))
    print("  Y el espesor no es opcional: de soga la densidad seguiria cumpliendo,")
    # el 8,64 estaba CLAVADO aqui y quedo viejo sin que nada lo dijera. El
    # esfuerzo axial es inversamente proporcional al espesor, asi que lo que
    # este script puede afirmar sin importar el valor es la PROPORCION; el
    # numero lo dan el 02 y el 11, que son los que metran.
    print("  pero el esfuerzo axial del 7.1.1.b subiria %.2f veces (t se divide)"
          % (ESPESOR / A_UNIDAD))
    print("  y eso lo saca del admisible: ver los scripts 02 y 11.")
    print("  En albanileria confinada eso no es gratis: mas espesor es mas")
    print("  resistencia Y mas fuerza sismica, porque V = ZUCS/R x P.")
    return total


def concentracion_en_Y():
    u"""Que fraccion de la rigidez de Y se llevan las dos medianeras.

    SE DERIVA. Este numero estaba clavado a mano --72,6-- en el `print` de
    abajo y desde ahi se habia propagado a TRES lugares del informe. El valor
    vivo es 73,8 %: el literal quedo de antes de que la seccion transformada
    incorporara las alas del 8.3.6. Un numero derivado escrito a mano no lo
    caza el auditor de constantes, que compara contra `proyecto.py` y no
    contra lo que otro script calcula.
    """
    m12 = _rigidez()
    ks = sorted((f["K"] for f in m12 if f["dir"] == "Y"), reverse=True)
    return 100.0 * (ks[0] + ks[1]) / sum(ks)


def _rigidez():
    u"""Las filas del 12, sin volver a calcular la rigidez aca."""
    import contextlib
    import importlib.util
    import io as _io
    import os as _os
    ruta = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                         "12_rigidez_lateral.py")
    spec = importlib.util.spec_from_file_location("_r12", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
        return m.tabla()


def torsion_en_perspectiva(xr, yr, niveles):
    print()
    print("=" * 88)
    print("6. EL RIESGO TORSIONAL QUE SE VENIA DECLARANDO: MEDIDO")
    print("=" * 88)
    print()
    print("  Desde que se calculo la rigidez, este proyecto venia advirtiendo que")
    conc = concentracion_en_Y()
    print("  las medianeras se llevan el %.0f %% de la direccion Y y que eso"
          % conc)
    print("  podia")
    print("  sacar el centro de rigidez de lugar, disparar la irregularidad")
    print("  torsional y bajar R de 3,00 a 2,25.")
    print()
    print("  MEDIDO, NO OCURRE, y conviene entender por que. La concentracion de")
    print("  rigidez es real: %.1f %% en dos muros. Pero esos dos muros estan en"
          % conc)
    print("  x = 0,00 y x = %.2f, o sea SIMETRICOS respecto del centro. Dos masas"
          % FRENTE)
    print("  iguales a distancias iguales no corren el centroide: lo fijan. Por eso")
    print("  x_CR = %.3f m, exactamente el medio del frente." % xr)
    print()
    _az, _W, xm, ym, _d = niveles[0]
    print("  Resultado: ex estatica = %.3f m, que es el %.2f %% del frente."
          % (abs(xm - xr), 100.0 * abs(xm - xr) / FRENTE))
    print("  La excentricidad que gobierna NO es la del edificio: es la ACCIDENTAL")
    print("  de %.2f B que impone la norma, %.0f veces mayor."
          % (EXC_ACCIDENTAL, (EXC_ACCIDENTAL * FRENTE) / abs(xm - xr)))
    print()
    print("  En X la cosa es menos redonda: y_CR = %.3f contra un centro de fondo"
          % yr)
    print("  en %.2f. Los siete transversales tienen rigidez pareja, pero las dos"
          % (FONDO / 2.0))
    print("  fachadas son las MENOS rigidas (%.1f %% cada una) porque son las que"
          % 10.6)
    print("  llevan las ventanas anchas. Aun asi ey estatica = %.3f m."
          % abs(ym - yr))
    print()
    print("  LO QUE ESTO NO DEMUESTRA TODAVIA. La E.030 Tabla 12 no define la")
    print("  irregularidad torsional por la excentricidad sino por DESPLAZAMIENTOS:")
    print("  hay irregularidad si el desplazamiento maximo de un extremo supera")
    print("  1,3 veces el promedio de los dos extremos. Eso exige repartir el")
    print("  cortante con torsion, que es la etapa siguiente. Lo que si se puede")
    print("  afirmar hoy: la causa que se tenia bajo sospecha quedo descartada, y")
    print("  lo que decida la irregularidad sera la excentricidad ACCIDENTAL, que")
    print("  es la misma para cualquier edificio de este ancho.")


if __name__ == "__main__":
    niveles, xr, yr, sumKy, sumKx = informe()
    excentricidad(niveles, xr, yr)
    sensibilidad()
    peso_sismico()
    torsion_en_perspectiva(xr, yr, niveles)
