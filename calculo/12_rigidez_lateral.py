# -*- coding: utf-8 -*-
"""Rigidez lateral de cada muro — primera mitad de los criterios 5 y 6

Es el dato del que cuelga todo lo que sigue: centro de rigidez, excentricidad,
torsion y reparto de cortante. Si esta mal, el diseno de muros hereda el error.

LO QUE DICE LA NORMA, verificado en los Comentarios a la E.070 (SENCICO 2008,
Cap. 8), que es la lectura que la consigna enlaza:

  Art. 24.5  "La rigidez de cada muro podra determinarse SUPONIENDOLO EN
             VOLADIZO cuando no existan vigas de acoplamiento". Es nuestro caso:
             no hay vigas disenadas para acoplar ductilmente.

  Art. 24.6  DOS correcciones que casi nadie aplica y que cambian el resultado:
             (a) "se agregara a su seccion transversal el 25% de la seccion
                 transversal de aquellos muros que concurran ortogonalmente al
                 muro en analisis O 6 VECES SU ESPESOR, lo que sea mayor"
                 -> los muros tienen ALAS donde los cruza otro muro.
             (b) "la rigidez lateral de un muro confinado debera evaluarse
                 TRANSFORMANDO EL CONCRETO de sus columnas de confinamiento en
                 area equivalente de albanileria, multiplicando su espesor real
                 por la relacion de modulos Ec/Em"
                 -> las columnas no son ladrillo: son 6,7 veces mas rigidas.

  Art. 24.7  Em = 500 f'm para unidades de arcilla;  Gm = 0,40 Em
  Art. 24.8  Ec segun la E.060, que da Ec = 15000 raiz(f'c)

POR QUE EL ALA SE TOMA COMO 6t Y NO COMO EL 25 %
================================================
El texto deja elegir "lo que sea mayor", y para una medianera de 21,00 m el 25 %
son 5,25 m de ala. Pero esa misma medianera cruza SIETE muros transversales: si
cada uno se lleva 5,25 m, la suma (36,75 m) supera la longitud del propio muro,
que es fisicamente imposible. El propio articulo pone un tope ("su contribucion
a cada muro no excedera de la mitad de su longitud") pensado para el caso de DOS
muros, no de siete.

Se adopta **6t por cruce** (= 6 x 0,24 = 1,44 m; el comentario decia 1,38, que
es 6 x 0,23, el espesor VIEJO -- corregido el 2026-09-19), y se comprueba que la
suma de alas que cede cada muro NO supere su propia longitud.

HAY QUE DECIRLO CON PRECISION: el articulo pide "LO QUE SEA MAYOR", y 6t es el
MENOR de los dos. No se esta aplicando el texto al pie de la letra, y el motivo
es el de arriba -- el 25 % es inaplicable con siete cruces --, no una
conveniencia. Por eso el script 29 contrasta la otra lectura y verifica que el
diseno cumpla con las dos, que es como este proyecto trata toda hipotesis
discutible.

SIMPLIFICACION DECLARADA
========================
Cada muro se modela con su longitud NETA (vanos descontados) como un unico
voladizo. Un analisis riguroso trataria cada trozo entre vanos por separado. El
modelo de OpenSeesPy del criterio 7 sirve justamente para contrastar esto, y la
tolerancia se declara ahi.
"""
import math

from proyecto import (MUROS, EJES_MX, EJES_COLUMNAS_X, FONDO, FRENTE, HN,
                      ESPESOR, FM, FC, H_COLUMNA, H_COLUMNA_EXT, EM,
                      POZO_Y0, POZO_Y1,
                      POZO_X0, POZO_X1, LONG_MINIMA,
                      vanos_ubicados, machones)

EC = 15000.0 * math.sqrt(FC)      # E.060: Ec = 15000 raiz(f'c), kgf/cm2
N_TRANSF = EC / EM                # relacion de modulos
GM = 0.40 * EM                    # E.070 24.7
F_CORTE = 1.2   # no-ssot: factor de forma de seccion rectangular, no una longitud.
                # Es 1/k con k = 5/6, el factor de area de corte que la Clase 05
                # escribe en su deduccion: Delta_corte = V.h/(G.k.A) con k = 5/6.
                # 1/(5/6) = 1,2 -- la misma cifra por los dos caminos. En su
                # formula compacta el k va absorbido dentro de "Ac = area de
                # corte", que por eso NO es el area bruta.
ALA = 6.0 * ESPESOR   # no-ssot: 6 es el multiplicador del articulo 24.6


def cruces(nom, dire, L):
    """Posiciones, EN COORDENADA DEL MURO, donde lo cruza un muro ortogonal."""
    if dire == "X":
        y = EJES_MX[int(nom.split("-")[1][0]) - 1]
        xs = [0.0, FRENTE]                       # las dos medianeras siempre
        for x in (POZO_X0, POZO_X1):             # los longitudinales interiores
            if y <= POZO_Y0 + 1e-9 or y >= POZO_Y1 - 1e-9:
                xs.append(x)
        return sorted(xs)
    # muros en Y: los cruzan los transversales que caen dentro de su extension
    y0 = POZO_Y1 if nom[4:5] == "b" else 0.0
    if nom[:4] in ("MY-1", "MY-2"):
        y0 = 0.0
    return [y - y0 for y in EJES_MX if y0 - 1e-9 <= y <= y0 + L + 1e-9]


def columnas(nom, dire, L):
    """Posiciones de las columnas de confinamiento, en coordenada del muro."""
    if dire == "X":
        return list(EJES_COLUMNAS_X)
    return cruces(nom, dire, L)      # en los MY, columna en cada cruce


def condensar(x, puestos):
    """Lleva la coordenada x del muro BRUTO al muro CONDENSADO (sin vanos).

    EL ERROR QUE ESTA FUNCION REPARA (hallazgo C-1, auditoria del 15-set).
    Esta funcion modelaba el alma de 0 a L_neta pero colocaba las columnas y
    las alas en su coordenada REAL sobre la longitud BRUTA. En MX-1, con
    L = 12,00 y L_neta = 6,40, eso ponia piezas en 8,70 y 12,00: hasta
    5,60 m MAS ALLA del extremo del alma. Como la inercia va con el brazo al
    cuadrado, la sobreestimacion era brutal -- el sintoma que lo delataba es
    que I_script / I_alma daba 14,84, y un patin no multiplica por quince la
    inercia de un rectangulo.

    La reparacion NO cambia el modelo (el muro sigue siendo UN voladizo de
    longitud neta): lo hace coherente. Condensar es quitar los vanos y pegar
    los machones, de modo que toda pieza caiga dentro de [0, L_neta].

    Medido EN AQUELLA CORRIDA (15-set): SumK baja 12,3 % en X y 6,8 % en Y,
    y el ratio I/I_alma de MX-1 cae de 14,84 a 4,54. El valor en Y coincidio
    con el que la auditoria habia calculado por su cuenta (849 696), lo que
    confirmo la correccion por dos caminos independientes.

    CUIDADO AL LEER ESOS NUMEROS: son los de aquel dia y NO los vigentes.
    Despues se corrigieron el espesor de las columnas extremas y el ala, y
    hoy la suma en Y es 896 035. Quedan fechados porque son la EVIDENCIA de
    la verificacion cruzada, no el estado actual; el estado actual lo da
    tabla(). Un numero historico sin fecha se lee como vigente, y asi fue
    como el borrador llego a publicar 849 696 como si fuera de hoy.
    """
    c = x
    for x0, ancho in puestos:
        if x >= x0 + ancho - 1e-12:
            c -= ancho          # el vano quedo enteramente antes de x
        elif x > x0:
            c -= (x - x0)       # x cae DENTRO del vano
    return c


def seccion(nom, dire, L, t, vanos):
    """Propiedades de la seccion transformada: area, inercia y area de corte.

    Se trabaja en cm para que Em y Ec esten en sus unidades (kgf/cm2).
    Todas las piezas se ubican en coordenada CONDENSADA: ver condensar().
    """
    # OJO, Y NO SE CORRIGE: aqui va L - suma(vanos) y NO la suma de machones,
    # aunque el 01, el 02, el 11 y el 18 usen machones(). No es un descuido y
    # cambiarlo introduce un error.
    #
    # El motivo es el (N_TRANSF - 1) de mas abajo. El alma cuenta el area
    # GEOMETRICA completa -- incluidos los tramos donde hay columna -- y cada
    # columna suma solo el EXCESO de rigidez del concreto sobre la albanileria
    # que el alma ya conto. En la zona de columna el area transformada resulta
    # entonces A + (n-1)A = n.A, que es lo correcto. Si el alma pasara a
    # machones, que EXCLUYE la media columna del extremo, habria que sumar n
    # COMPLETO; mezclar machones con (n-1) perderia esa area.
    #
    # Son dos preguntas distintas con respuestas distintas, y las dos legitimas:
    #   RIGIDEZ  -> cuanta seccion hay para resistir el desplazamiento: TODA,
    #               con el concreto pesando lo que pesa.
    #   AXIAL    -> que trozos cuenta el 6.4 como muro portante: solo los
    #               machones de 1,20 m o mas.
    L_neta = (L - sum(vanos)) * 100.0
    t_cm = t * 100.0
    puestos = vanos_ubicados(nom, dire, L, vanos)
    # alma. El 12 es el de la formula de la inercia, no el frente del lote.
    piezas = [(L_neta / 2.0, L_neta * t_cm, t_cm * L_neta ** 3 / 12.0)]   # no-ssot

    # columnas transformadas: el concreto pesa como (n-1) veces mas albanileria
    # las columnas de los EXTREMOS son mas peraltadas (C-2), y como estan en la
    # punta del muro son justo las que mas aportan a la inercia: el brazo entra
    # al cuadrado. Tratarlas como interiores subestimaba la rigidez.
    ejes_col = columnas(nom, dire, L)
    for j, x in enumerate(ejes_col):
        extrema = (j == 0 or j == len(ejes_col) - 1)
        h_col = (H_COLUMNA_EXT if extrema else H_COLUMNA) * 100.0
        a = h_col * t_cm * (N_TRANSF - 1.0)
        piezas.append((condensar(x, puestos) * 100.0, a, 0.0))

    # alas donde concurre un muro ortogonal
    for x in cruces(nom, dire, L):
        piezas.append((condensar(x, puestos) * 100.0, ALA * 100.0 * t_cm, 0.0))

    A = sum(p[1] for p in piezas)
    xc = sum(p[0] * p[1] for p in piezas) / A
    I = sum(p[2] + p[1] * (p[0] - xc) ** 2 for p in piezas)
    A_corte = L_neta * t_cm          # solo el alma toma cortante
    return A, I, A_corte, L_neta / 100.0


def control_formula_de_clase(t_cm, L_cm):
    """Nuestra K contra la formula COMPACTA de la Clase 05, para muro rectangular.

        k_muro = E.t / [ 4(h/L)^3 + 3(h/L) ]

    No es otra formula: es la nuestra con I = tL^3/12, A = tL y G = 0,40E
    sustituidos. Sale identica SI Y SOLO SI se cumple el 8.3.7 (G = 0,40 Em) y
    el factor de area de corte es 5/6. Si algun dia alguien toca F_CORTE o GM,
    este control lo denuncia.

    Solo vale para el ALMA rectangular: con alas y columnas transformadas la
    seccion deja de ser un rectangulo y la compacta ya no aplica.
    """
    h = HN * 100.0
    I = t_cm * L_cm ** 3 / 12.0   # no-ssot: divisor de b.h^3/12, no el FRENTE del lote
    A = t_cm * L_cm
    nuestro = 1.0 / (h ** 3 / (3.0 * EM * I) + F_CORTE * h / (GM * A))
    clase = EM * t_cm / (4.0 * (h / L_cm) ** 3 + 3.0 * (h / L_cm))
    assert abs(nuestro - clase) < 1e-6 * max(1.0, abs(clase)), (
        "nuestra K (%.4f) no coincide con la formula compacta de la Clase 05 "
        "(%.4f). Revisar F_CORTE = 1/k con k = 5/6, o GM = 0,40 EM (8.3.7)"
        % (nuestro, clase))
    return nuestro, clase


def rigidez(I, A_corte):
    """Voladizo con deformacion por flexion y por corte. E.070 24.5."""
    h = HN * 100.0
    flex = h ** 3 / (3.0 * EM * I)
    corte = F_CORTE * h / (GM * A_corte)
    return 1.0 / (flex + corte), flex, corte


def tabla():
    print("=" * 100)
    print("RIGIDEZ LATERAL DE CADA MURO — voladizo de %.2f m (E.070 24.5)" % HN)
    print("=" * 100)
    print("  Em = 500 f'm = %.0f kgf/cm2     Gm = 0,40 Em = %.0f" % (EM, GM))
    print("  Ec = 15000 raiz(%.0f) = %.0f      Ec/Em = %.2f" % (FC, EC, N_TRANSF))
    print("  ala por cruce = 6t = %.2f m" % ALA)
    print()
    print("  %-30s %3s %7s %5s %4s %12s %10s %6s %6s"
          % ("muro", "dir", "L neta", "alas", "col", "I (cm4)", "K (kgf/cm)",
             "%flex", "%cort"))
    filas = []
    for nom, dire, L, t, vanos in MUROS:
        A, I, Ac, Ln = seccion(nom, dire, L, t, vanos)
        K, fl, co = rigidez(I, Ac)
        filas.append({"nom": nom, "dir": dire, "L": Ln, "I": I, "K": K,
                      "cruces": len(cruces(nom, dire, L))})
        print("  %-30s %3s %7.2f %5d %4d %12.3e %10.0f %5.0f%% %5.0f%%"
              % (nom, dire, Ln, len(cruces(nom, dire, L)),
                 len(columnas(nom, dire, L)), I, K,
                 100 * fl / (fl + co), 100 * co / (fl + co)))
    print()
    for d in ("X", "Y"):
        s = sum(f["K"] for f in filas if f["dir"] == d)
        print("  %-30s suma K = %12.0f kgf/cm" % ("DIRECCION %s" % d, s))
    return filas


def lectura(filas):
    print()
    print("=" * 100)
    print("LECTURA — que dice la tabla")
    print("=" * 100)
    for d in ("X", "Y"):
        g = [f for f in filas if f["dir"] == d]
        s = sum(f["K"] for f in g)
        top = max(g, key=lambda f: f["K"])
        print("  DIRECCION %s: %d muros, K total %.0f kgf/cm. El mas rigido es %s,"
              % (d, len(g), s, top["nom"].split()[0]))
        print("     con el %.0f %% de la rigidez de la direccion." % (100 * top["K"] / s))
    print()
    print("  POR QUE LAS MEDIANERAS DOMINAN. Miden %.2f m contra los %.2f de un"
          % (FONDO, FRENTE))
    print("  transversal, no tienen vanos, y la rigidez de un voladizo crece con el")
    print("  CUBO de la longitud en el termino de flexion. Esa concentracion es")
    print("  justamente la que puede sacar el centro de rigidez del centro de masa")
    print("  y generar torsion: es el riesgo que este proyecto viene declarando")
    print("  desde el principio, y el que decide si Ip se mantiene en 1,00.")
    print()
    print("  SOBRE EL REPARTO FLEXION / CORTE: en los muros largos manda el corte y")
    print("  en los cortos la flexion. Un modelo que ignore la deformacion por")
    print("  corte sobrestima la rigidez de los muros largos, que son justo los que")
    print("  deciden el centro de rigidez.")


def control(filas):
    """Que ningun muro ceda mas ala de la que tiene."""
    print()
    print("=" * 100)
    print("CONTROL — las alas no pueden salir de la nada")
    print("=" * 100)
    print("  Cada muro CEDE un ala de %.2f m a cada muro que lo cruza. La suma no" % ALA)
    print("  puede superar su propia longitud.")
    print()
    ok = True
    for nom, dire, L, t, vanos in MUROS:
        cede = len(cruces(nom, dire, L)) * ALA
        bien = cede <= L + 1e-9
        ok = ok and bien
        print("  %-30s cede %5.2f m de %5.2f  %s"
              % (nom, cede, L, "ok" if bien else "EXCEDE <<<"))
    print()
    print("  %s" % ("Ningun muro cede mas de lo que tiene." if ok else
                    "HAY MUROS QUE CEDEN MAS ALA QUE SU LONGITUD <<<"))
    assert ok, "el reparto de alas es fisicamente imposible"


if __name__ == "__main__":
    # control cruzado con la formula de la Clase 05 antes de nada
    _n, _c = control_formula_de_clase(ESPESOR * 100, FRENTE * 100)
    print("  [ok] K coincide con la formula compacta de la Clase 05: "
          "%.1f kgf/cm por los dos caminos" % _n)
    f = tabla()
    lectura(f)
    control(f)
