# -*- coding: utf-8 -*-
"""Columnas de confinamiento y vigas soleras. E.070 8.6.3 y 8.6.4. Criterio 9

QUE RESUELVE
============
El acero longitudinal de las columnas, los ESTRIBOS con sus cuatro criterios de
espaciamiento, y el refuerzo de las soleras. El docente pregunto expresamente
por el criterio de los estribos: son los S1 a S4 del 8.6.3-a.3, y van los CUATRO
porque se toma el MENOR.

DE DONDE SALE CADA COSA (nada se re-deriva)
===========================================
  Vm1, Vu, Mu   -> 18_diseno_muros.py
  Pg, Pm        -> 11_metrado_muros.py
  f'c, fy, t    -> proyecto.py

LA SECUENCIA DEL 8.6.3
======================
  a)   fuerzas internas por la TABLA 11 (columna interior y extrema)
  a.1  seccion de concreto: la MAYOR entre compresion y corte-friccion,
       y nunca menor que 15 t
  a.2  refuerzo vertical: As = Asf + Ast, minimo 4 varillas
  a.3  estribos: el MENOR de s1, s2, s3, s4, en la zona de confinamiento
  b)   soleras a traccion pura

Y el 8.6.4 hace lo mismo, mas liviano, para los pisos que NO se agrietaron
(en este edificio, los pisos 2 a 5: lo verifico el script 18).
"""
import importlib.util
import math
import os

from proyecto import (FC, ESPESOR, H_COLUMNA, H_COLUMNA_EXT, B_SOLERA,
                      H_DINTEL_PUERTA, H_DINTEL_VENTANA,
                      H_SOLERA, H_ENTREPISO, N_PISOS, MUROS,
                      EJES_COLUMNAS_X, EJES_MX, POZO_Y0, POZO_Y1,
                      FRENTE)

FY = 4200.0          # no-ssot: kgf/cm2, acero grado 60
PHI_COMPRESION = 0.7    # no-ssot: 8.6.3-a.1, con estribos cerrados
PASO_MULTIPLO = 2.5     # no-ssot: cm. San Bartolome, Quiun y Silva (2015),
                        # 7.1.3 B.4: la separacion "debe ser multiplo de
                        # 2.5cm para facilitar el proceso constructivo, no
                        # mayor que 10cm ni menor que 5cm". La E.070 da los
                        # cuatro criterios pero no el dato constructivo.
DELTA_TRANSV = 1.0      # no-ssot: 8.6.3-a.1, columna confinada por muros transversales
DELTA_SIN_TRANSV = 0.8  # no-ssot: 8.6.3-a.1, columna SIN muro transversal
PHI_CORTE_FRICCION = 0.85   # no-ssot: 8.6.3-a.1' y a.2
MU_FRICCION = 0.8       # no-ssot: 8.6.3-a.2, junta sin tratamiento (conservador)
PHI_SOLERA = 0.9        # no-ssot: 8.6.3-b
AC_MIN_FACTOR = 15.0    # no-ssot: 8.6.3-a.1, Ac >= 15 t
AS_MIN_FACTOR = 0.1     # no-ssot: 8.6.3-a.2, As >= 0,1 f'c Ac / fy
RECUBRIMIENTO = 2.5     # no-ssot: cm, medido al estribo. E.070 4.2.10 pide 2 cm
                        # en muros tarrajeados (3 cm caravista); se adopta 2,5.
                        # Citaba la E.060 7.7.1, que para columnas da 40 mm:
                        # no es la que rige en albanileria confinada.
ZONA_CONF_MIN = 45.0    # no-ssot: cm, 8.6.3-a.3
ZONA_CONF_FACTOR = 1.5  # no-ssot: 8.6.3-a.3, o 1,5 d
S3_MIN = 5.0            # no-ssot: cm, 8.6.3-a.3
S4 = 10.0               # no-ssot: cm, 8.6.3-a.3
AV_ESTRIBO = 2 * 0.32   # no-ssot: cm2, dos ramas de 6 mm (0,32 cm2 c/u)
AREA_3_8 = 0.71         # no-ssot: cm2, varilla de 3/8"
AREA_1_2 = 1.29         # no-ssot: cm2, varilla de 1/2"
AREA_3_4 = 2.84         # no-ssot: cm2, varilla de 3/4"
# LAS CUATRO AREAS SON DE LA MISMA TABLA: ASTM A615M, Tabla 1 (N.o 10 = 71,
# N.o 13 = 129, N.o 16 = 199, N.o 19 = 284 mm2). El 5/8" se usaba con 1,98 en
# el 39 y con 2,00 en el 27: dos valores distintos para la misma varilla, y
# ninguno de la tabla de donde salen los otros tres.
AREA_5_8 = 1.99         # no-ssot: cm2, varilla de 5/8"
# diametros nominales, cm (misma tabla)
DB = {'3/8"': 0.952, '1/2"': 1.27, '5/8"': 1.588, '3/4"': 1.905}   # no-ssot: diametros nominales ASTM A615M
DB_ESTRIBO = DB['3/8"']
LIBRE_MIN = 4.0         # no-ssot: cm, E.060 7.6.3: libre >= 1,5 db y >= 40 mm
APOYO_MAX = 15.0        # no-ssot: cm, E.060 7.10.5.3: 150 mm libres a una barra apoyada


def _cargar(nombre):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "c", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R18 = _cargar("18_diseno_muros.py")


def preparar():
    muros, V_ent = R18.datos()
    for mu in muros:
        mu["Vm1"] = R18.resistencia(mu, 0)
        f_bruto = mu["Vm1"] / mu["Ve"][0]
        mu["f"] = min(R18.F_MAX, max(R18.F_MIN, f_bruto))
        mu["Vu"] = [v * mu["f"] for v in mu["Ve"]]
        mu["Mu"] = [m * mu["f"] for m in mu["Me"]]
    return muros


def n_columnas(nom, dire):
    if dire == "X":
        return len(EJES_COLUMNAS_X)
    if nom.startswith("MY-3a") or nom.startswith("MY-4a"):
        return sum(1 for y in EJES_MX if y <= POZO_Y0 + 1e-9)
    if nom.startswith("MY-3b") or nom.startswith("MY-4b"):
        return sum(1 for y in EJES_MX if y >= POZO_Y1 - 1e-9)
    return len(EJES_MX)


def tabla_11(mu):
    """Fuerzas internas en la columna EXTREMA, que es la que gobierna.

    La extrema toma 1,5 veces el cortante de la interior y, sobre todo, es la
    unica que recibe la traccion del momento: T = F - Pc con F = M/L. La interior
    casi siempre queda con refuerzo minimo.
    """
    Vm1 = mu["Vm1"]
    L = mu["L"]
    h = H_ENTREPISO
    Nc = n_columnas(mu["nom"], mu["dir"])
    # Lm: "longitud del pano mayor o 0,5 L, lo que sea MAYOR".
    # OJO: el PANO es el tramo entre DOS COLUMNAS consecutivas, no entre vanos.
    # Con Nc columnas hay Nc-1 panos. Tomarlo por los vanos daba Lm = L en los
    # muros sin vanos (21,00 m en las medianeras) y duplicaba el Vc.
    Lm = max(L / max(1, Nc - 1), 0.5 * L)
    M = mu["Mu"][0] - 0.5 * Vm1 * h
    F = M / L
    # Pc (8.6.3): carga directa + MITAD del pano A CADA LADO + transversales.
    # La INTERIOR tiene pano a los dos lados; la EXTREMA a uno solo, o sea la
    # mitad. Usar el mismo Pc para las dos SUBESTIMA la traccion de la extrema
    # (T = F - Pc), que es justo el acero que impide que el muro se despegue.
    Pc_int = mu["Pg"] / Nc
    Pc = 0.5 * Pc_int
    Vc_base = Vm1 * Lm / (L * (Nc + 1))
    return {"Nc": Nc, "Lm": Lm, "M": M, "F": F, "Pc": Pc, "Pc_int": Pc_int,
            # EXTREMA: 1,5 veces el cortante Y la traccion del momento
            "Vc": 1.5 * Vc_base,  # no-ssot: 1,5 es el factor de la Tabla 11, no Df
            "T": F - Pc, "C": Pc + F,
            # INTERIOR: la Tabla 11 le da otras tres expresiones, y no se parecen
            "Vc_i": Vc_base,
            "T_i": Vm1 * h / L - Pc_int,
            "C_i": Pc_int - Vm1 * h / (2.0 * L)}


def acero_por_resistencia(t11):
    """As que pide la RESISTENCIA. No depende de la seccion (8.6.3 a.2)."""
    Asf = t11["Vc"] / (FY * MU_FRICCION * PHI_CORTE_FRICCION)
    Ast = max(0.0, t11["T"]) / (FY * PHI_CORTE_FRICCION)
    return Asf, Ast, Asf + Ast


def nucleo_necesario(C, As, delta=None):
    """An de la formula 8.6.3-a.1, que es IMPLICITA en As.

        An = As + (C/phi - As fy) / (0,85 delta f'c)

    Resolverla con As = 0 NO es conservador, es responder otra pregunta: la de
    una columna sin acero. Con el As real el nucleo necesario cae a un tercio.
    """
    if delta is None:
        delta = DELTA_TRANSV
    return max(0.0, As + (C / PHI_COMPRESION - As * FY) / (0.85 * delta * FC))  # no-ssot: 0,85 es el bloque de compresion del concreto, no phi


def disenar_columna(t11, d_minimo):
    """Peralte necesario, VERIFICANDO la seccion en vez de despejarla.

    El acero sale de la resistencia y no depende de la seccion; con ese acero se
    calcula el nucleo necesario, y de ahi el peralte. Despues se comprueba el
    minimo por cuantia con el Ac REAL (no con el requerido) y, si obliga a mas
    acero, se vuelve a pasar: el lazo converge en dos vueltas.
    """
    import math as _m
    t_cm = ESPESOR * 100.0
    Asf, Ast, As = acero_por_resistencia(t11)
    Acf = t11["Vc"] / (0.2 * FC * PHI_CORTE_FRICCION)      # corte-friccion  # no-ssot: 0,2 es el coeficiente de corte-friccion del 8.6.3-a.1'
    Ac_min = AC_MIN_FACTOR * t_cm                          # 15 t
    for _ in range(5):
        An_nec = nucleo_necesario(t11["C"], As)
        d_nucleo = An_nec / (t_cm - 2 * RECUBRIMIENTO) + 2 * RECUBRIMIENTO
        d = max(d_minimo, d_nucleo, Acf / t_cm, Ac_min / t_cm)
        d = 5.0 * _m.ceil(d / 5.0)                         # multiplo de 5 cm
        Ac = t_cm * d
        As_min = AS_MIN_FACTOR * FC * Ac / FY              # con el Ac REAL
        nuevo_As = max(Asf + Ast, As_min)
        if abs(nuevo_As - As) < 1e-6:
            break
        As = nuevo_As
    An_disp = (t_cm - 2 * RECUBRIMIENTO) * (d - 2 * RECUBRIMIENTO)
    return {"Asf": Asf, "Ast": Ast, "As": As, "As_min": As_min,
            "Acf": Acf, "Ac_min": Ac_min, "d": d, "Ac": Ac,
            "An_nec": nucleo_necesario(t11["C"], As), "An_disp": An_disp}


def varillas(As):
    """Cuantas varillas de 1/2 pulgada, con el minimo de 4 del 8.6.3-a.2."""
    n = max(4, math.ceil(As / AREA_1_2))
    return n, n * AREA_1_2


def estribos(d_cm, av=None):
    """a.3: los CUATRO espaciamientos, para una columna de t x d. Rige el MENOR.

    OJO CON LA COHERENCIA: `Ac` y `An` tienen que ser de la MISMA columna. Una
    version previa de este script tomaba el Ac que PEDIA el diseno junto con el
    An de la columna predimensionada, y el termino (Ac/An - 1) se inflaba hasta
    dar s1 = 1,16 cm -- un estribo cada centimetro, que no existe. El disparate
    era la pista de que las dos areas no hablaban de la misma seccion.

    EL AREA DEL ESTRIBO ES UN PARAMETRO, y no lo era. Con 6 mm regia s1; al
    subir a 3/8" para hacerlo constructible, s1 y s2 crecen con Av pero
    **s3 = d/4 no depende de Av**, de modo que el criterio que rige CAMBIA.
    La version previa solo recalculaba s1 y conservaba el veredicto viejo:
    el estribaje adoptado quedaba a 10 cm donde el 8.6.3-a.3 pide 6,25.
    """
    if av is None:
        av = AV_ESTRIBO
    t_cm = ESPESOR * 100.0
    tn = t_cm - 2 * RECUBRIMIENTO                      # espesor del nucleo
    An = tn * (d_cm - 2 * RECUBRIMIENTO)               # nucleo confinado
    Ac = t_cm * d_cm                                   # la MISMA columna
    s1 = (av * FY / (0.3 * tn * FC * (Ac / An - 1))  # no-ssot: 0,3 es el coeficiente del s1 del 8.6.3-a.3, no el area libre
          if Ac > An else float("inf"))
    s2 = av * FY / (0.12 * tn * FC)
    s3 = max(d_cm / 4.0, S3_MIN)
    zona = max(ZONA_CONF_MIN, ZONA_CONF_FACTOR * d_cm)
    return s1, s2, s3, S4, min(s1, s2, s3, S4), zona, An, tn


def _par(n):
    """El numero de varillas se lleva a PAR: armado simetrico.

    El momento sismico se invierte, asi que la columna trabaja igual hacia
    los dos lados; un numero impar obliga a una barra sin pareja. Es el mismo
    criterio con que el 39 fijo ocho barras para la C-4 y no siete.
    """
    return n + n % 2


def disposicion(b_cm, h_cm, n, diam):
    """DONDE VA CADA VARILLA, verificado contra la E.060. Una regla para todos.

    Las barras van en el PERIMETRO del nucleo, con las cuatro esquinas, y se
    prueban todos los repartos simetricos (k barras por cara larga, las que
    sobran por cara corta). Sobrevive el que cumple:

      7.6.3     libre entre barras >= 1,5 db y >= 40 mm
      7.10.5.3  esquinas y barras ALTERNAS apoyadas en la esquina de un
                estribo; ninguna a mas de 150 mm libres de una apoyada

    Las barras intermedias que la 7.10.5.3 obliga a apoyar llevan un GANCHO
    que une las dos caras opuestas. Entre los repartos validos se elige el de
    menos ganchos y, a igualdad, el de mayor distancia libre.

    Devuelve las coordenadas de los centros (cm, desde la esquina inferior
    izquierda de la seccion b x h), los ganchos como pares de puntos, las
    barras por cara y la distancia libre minima. Si ningun reparto cumple,
    REVIENTA: una columna que no se puede armar no es un diseno.
    """
    if n % 2:
        raise ValueError("%d varillas: impar, no hay reparto simetrico" % n)
    db = DB[diam]
    c = RECUBRIMIENTO + DB_ESTRIBO + db / 2.0      # del borde al centro
    exigido = max(1.5 * db, LIBRE_MIN)

    def apoyadas(k):
        # esquinas y una de cada dos: la 7.10.5.3 no deja dos seguidas sin apoyo
        return sorted({0, k - 1} | {i for i in range(k) if i % 2 == 0})

    def libre(L, k):
        return (L - 2 * c - (k - 1) * db) / (k - 1)

    largo, corto = max(b_cm, h_cm), min(b_cm, h_cm)
    candidatos = []
    for kl in range(2, n // 2 + 1):
        kc = n // 2 + 2 - kl
        if kc < 2:
            continue
        ll, lc = libre(largo, kl), libre(corto, kc)
        if min(ll, lc) < exigido - 1e-9:
            continue
        ganchos = 0
        ok = True
        for L, k, lib in ((largo, kl, ll), (corto, kc, lc)):
            ap = apoyadas(k)
            ganchos += len([i for i in ap if 0 < i < k - 1])
            if len(ap) < k and lib > APOYO_MAX + 1e-9:
                ok = False
        if ok:
            candidatos.append((ganchos, -min(ll, lc), kl, kc))
    if not candidatos:
        raise ValueError(
            "%d o %s en %.0f x %.0f cm: ningun reparto cumple la E.060 7.6.3 "
            "y 7.10.5.3" % (n, diam, b_cm, h_cm))
    g, menos_libre, kl, kc = min(candidatos)
    # caras horizontales (largo b) y verticales (largo h)
    kb, kh = (kl, kc) if b_cm >= h_cm else (kc, kl)
    xs = [c + i * (b_cm - 2 * c) / (kb - 1) for i in range(kb)]
    ys = [c + i * (h_cm - 2 * c) / (kh - 1) for i in range(kh)]
    puntos = ([(x, c) for x in xs] + [(x, h_cm - c) for x in xs] +
              [(c, y) for y in ys[1:-1]] + [(b_cm - c, y) for y in ys[1:-1]])
    ganchos = ([((xs[i], c), (xs[i], h_cm - c)) for i in apoyadas(kb)
                if 0 < i < kb - 1] +
               [((c, ys[i]), (b_cm - c, ys[i])) for i in apoyadas(kh)
                if 0 < i < kh - 1])
    # los ganchos atraviesan la seccion: uno sirve a las DOS caras opuestas
    assert len(puntos) == n, "se ubicaron %d varillas de %d" % (len(puntos), n)
    return {"puntos": puntos, "ganchos": ganchos, "por_cara": (kb, kh),
            "libre": -menos_libre, "exigido": exigido, "db": db, "c": c}


def completar_disposicion(fila):
    """Agrega la disposicion a una fila del cuadro que no la trae (C-3, C-4)."""
    if "disp" not in fila:
        fila["disp"] = disposicion(fila["b"] * 100.0, fila["h"] * 100.0,
                                   fila["n"], fila["diam"])
    return fila


def verificar_delta_y_pt(muros):
    """Cada columna, en cada muro al que pertenece: delta propio y C con Pt.

    CLASE 07 (2026-10-01) y E.070 8.6.3-a.1. El diseno usaba delta = 1,0 en
    todas las columnas, y la norma da 0,8 a las que no tienen muro transversal:
    en esta planta son las del eje 5,95, que tiene columnas y no muro. Y la
    compresion se calculaba con la mitad de Pg/Nc y sin Pt, la carga que baja
    del muro transversal (8.3.6), lo que es conservador para la TRACCION pero
    subestima la COMPRESION. Aca se verifica el nucleo con lo desfavorable
    para la compresion: Pc = Pg/Nc + Pt, Pt = Lt Pg/L del transversal, con Lt
    el ala de 6t que usa el script 12. El armado no cambia; si el nucleo no
    alcanzara, esto revienta.
    """
    import contextlib
    import io as _io
    R12 = _cargar("12_rigidez_lateral.py")
    m39 = _cargar("39_columnas_en_planta.py")
    with contextlib.redirect_stdout(_io.StringIO()):
        cuadro = {f["tipo"]: f for f in m39.cuadro_completo()}
    c4 = cuadro["C-4"]["cruces"] if "C-4" in cuadro else []

    def tipo(q):
        if any(m39._mismo(q, r) for r in c4):
            return "C-4"
        return m39.asignacion_del_plano(q)

    geo = m39.geometria_de_muros()
    por_clave = {mu["nom"].split()[0]: mu for mu in muros}
    h = H_ENTREPISO
    filas = []
    for w in geo:
        mu = por_clave[w["clave"]]
        Nc = mu["t11"]["Nc"]
        for q in w["puntos"]:
            otros = [g for g in geo if g is not w
                     and any(m39._mismo(q, r) for r in g["puntos"])]
            delta = DELTA_TRANSV if otros else DELTA_SIN_TRANSV
            Pt = sum(R12.ALA / g["L"] * por_clave[g["clave"]]["Pg"]
                     for g in otros)
            extrema = any(m39._mismo(q, e) for e in w["extremos"])
            Pc = mu["Pg"] / Nc + Pt
            if extrema:
                C = Pc + mu["t11"]["F"]
            else:
                C = Pc - mu["Vm1"] * h / (2.0 * mu["L"])
            f = cuadro[tipo(q)]
            An_disp = ((f["b"] * 100 - 2 * RECUBRIMIENTO)
                       * (f["h"] * 100 - 2 * RECUBRIMIENTO))
            An_nec = nucleo_necesario(C, f["As_prov"], delta)
            filas.append((w["clave"], q, tipo(q), extrema, delta, Pt, C,
                          An_nec, An_disp))
    malas = [x for x in filas if x[7] > x[8] + 1e-9]
    assert not malas, "nucleo insuficiente: %r" % (malas,)
    return filas


def solera(mu, t11):
    """b: la solera se disena a TRACCION PURA.  Ts = Vm1 Lm / (2 L)"""
    Ts = mu["Vm1"] * t11["Lm"] / (2.0 * mu["L"])
    Acs = B_SOLERA * 100.0 * H_SOLERA * 100.0
    As = max(Ts / (PHI_SOLERA * FY), AS_MIN_FACTOR * FC * Acs / FY)
    n, area = varillas(As)
    return Ts, Acs, As, n, area


def informe(muros):
    print("=" * 104)
    print("1. FUERZAS INTERNAS EN LAS COLUMNAS  -  TABLA 11 (columna EXTREMA)")
    print("=" * 104)
    print()
    print("  M = Mu1 - 1/2 Vm1 h   ·   F = M/L   ·   T = F - Pc   ·   C = Pc + F")
    print("  (h = %.2f m, la altura del PRIMER piso, no la total)" % H_ENTREPISO)
    print()
    print("  %-30s %3s %6s %9s %11s %10s %11s %11s"
          % ("muro", "Nc", "Lm (m)", "Vc (kgf)", "M (kgf.m)", "F (kgf)",
             "T (kgf)", "C (kgf)"))
    print("  " + "-" * 100)
    for mu in muros:
        t = tabla_11(mu)
        mu["t11"] = t
        print("  %-30s %3d %6.2f %9.0f %11.0f %10.0f %11.0f %11.0f"
              % (mu["nom"], t["Nc"], t["Lm"], t["Vc"], t["M"], t["F"],
                 t["T"], t["C"]))
    print()
    print("  T negativa = la columna NO entra en traccion: la carga gravitacional")
    print("  que baja por ella supera lo que el momento intenta levantarla. Ahi")
    print("  manda el refuerzo minimo, no el calculo de traccion.")


def informe_columnas(muros):
    print()
    print("=" * 104)
    print("2. SECCION Y ACERO  -  8.6.3 a.1 y a.2, EXTREMA contra INTERIOR")
    print("=" * 104)
    print()
    print("  Procedimiento: el ACERO sale de la resistencia (Asf + Ast) y no")
    print("  depende de la seccion. Con ese acero se calcula el nucleo necesario")
    print("  por la 8.6.3-a.1, y de ahi el peralte. Al final se comprueba el minimo")
    print("  por cuantia con el Ac REAL. NO se despeja la seccion con As = 0.")
    print()
    print("  %-30s %19s %24s"
          % ("", "EXTREMA (C-2)", "INTERIOR (C-1)"))
    print("  %-30s %6s %6s %6s %6s %6s %6s"
          % ("muro", "d req", "Ac", "As", "d req", "Ac", "As"))
    print("  " + "-" * 76)
    d_min = H_COLUMNA * 100.0
    peor_e = peor_i = 0.0
    As_e = As_i = 0.0
    for mu in muros:
        e = disenar_columna(mu["t11"], d_min)
        t_int = {"Vc": mu["t11"]["Vc_i"], "T": mu["t11"]["T_i"],
                 "C": mu["t11"]["C_i"]}
        i = disenar_columna(t_int, d_min)
        mu["dis_e"], mu["dis_i"] = e, i
        peor_e, peor_i = max(peor_e, e["d"]), max(peor_i, i["d"])
        As_e, As_i = max(As_e, e["As"]), max(As_i, i["As"])
        print("  %-30s %6.0f %6.0f %6.2f %6.0f %6.0f %6.2f"
              % (mu["nom"], e["d"], e["Ac"], e["As"], i["d"], i["Ac"], i["As"]))
    print("  " + "-" * 76)
    print("  %-30s %6.0f %6.0f %6.2f %6.0f %6.0f %6.2f"
          % ("EL QUE MANDA", peor_e, ESPESOR * 100 * peor_e, As_e,
             peor_i, ESPESOR * 100 * peor_i, As_i))
    print()
    mu0 = max(muros, key=lambda m: m["dis_e"]["d"])
    e = mu0["dis_e"]
    print("  QUIEN GOBIERNA el peralte de la C-2 (%s):" % mu0["nom"].split()[0])
    print("     nucleo por compresion  ->  d = %5.1f cm"
          % (e["An_nec"] / (ESPESOR * 100 - 2 * RECUBRIMIENTO) + 2 * RECUBRIMIENTO))
    print("     corte-friccion         ->  d = %5.1f cm  (Acf = %.0f cm2)"
          % (e["Acf"] / (ESPESOR * 100), e["Acf"]))
    print("     minimo 15t             ->  d = %5.1f cm  (Ac = %.0f cm2)"
          % (e["Ac_min"] / (ESPESOR * 100), e["Ac_min"]))
    print("     peralte de la C-1      ->  d = %5.1f cm" % d_min)
    print("     ADOPTADO (multiplo de 5)  ->  d = %.0f cm" % e["d"])
    print()
    print("  CONTROL de la 8.6.3-a.1:  An disponible >= An necesario")
    print("     %.0f cm2  >=  %.0f cm2   ->  %s"
          % (e["An_disp"], e["An_nec"],
             "cumple" if e["An_disp"] >= e["An_nec"] else "NO CUMPLE <<<"))
    return peor_e, peor_i, As_e, As_i


def paso_constructivo(s):
    """El espaciamiento llevado a multiplo de 2,5 cm HACIA ABAJO.

    San Bartolome, Quiun y Silva (2015), 7.1.3 B.4: la separacion "debe ser
    multiplo de 2.5cm para facilitar el proceso constructivo, no mayor que
    10cm ni menor que 5cm". Hacia abajo, porque redondear hacia arriba
    empeoraria un espaciamiento que la norma ya fijo como maximo.
    """
    import math as _m
    return max(S3_MIN, min(S4, _m.floor(s / PASO_MULTIPLO) * PASO_MULTIPLO))


def estribaje_adoptado(peraltes, av):
    """El detalle de estribos, DERIVADO del menor de los cuatro criterios."""
    menores = [estribos(d, av)[4] for d in peraltes]
    s = paso_constructivo(min(menores))
    zona = max(estribos(d, av)[5] for d in peraltes)
    import math as _m
    n = int(_m.ceil(round(zona / s, 6)))          # estribos que cubren la zona
    assert n * s >= round(zona, 6) and (n - 1) * s < round(zona, 6)
    return s, zona, n


def informe_estribos(muros):
    print()
    print("=" * 104)
    print("3. ESTRIBOS  -  8.6.3 a.3, LOS CUATRO CRITERIOS")
    print("=" * 104)
    print()
    print("  s1 = Av fy / [0,3 tn f'c (Ac/An - 1)]      s2 = Av fy / (0,12 tn f'c)")
    print("  s3 = d/4, pero no menor de %.0f cm            s4 = %.0f cm"
          % (S3_MIN, S4))
    print()
    print("  El acapite manda colocar EL MENOR de los cuatro, y \"d\" es el")
    print("  PERALTE de la columna. t = %.0f cm · recubrimiento %.1f cm."
          % (ESPESOR * 100, RECUBRIMIENTO))
    print("  Ac y An son de la MISMA columna: mezclarlas infla (Ac/An - 1).")
    print()
    # LA TABLA TIENE QUE INCLUIR LA SECCION QUE SE CONSTRUYE. Solo listaba
    # los peraltes que el CALCULO exige -- 25 y 30 cm --, y la C-2 se
    # construye de 35 porque el anclaje de la solera lo obliga (E.070 7.1.4).
    # El detalle adoptado si usa los 35, asi que la tabla de los cuatro
    # criterios y el estribaje adoptado hablaban de secciones distintas.
    peraltes = sorted({mu["dis_e"]["d"] for mu in muros}
                      | {mu["dis_i"]["d"] for mu in muros}
                      | {H_COLUMNA * 100.0, H_COLUMNA_EXT * 100.0})
    AV_38 = 2 * AREA_3_8

    for etiqueta, av in (("[] 6 mm   (Av = %.2f cm2)" % AV_ESTRIBO, AV_ESTRIBO),
                         ('[] 3/8"   (Av = %.2f cm2)' % AV_38, AV_38)):
        print("  %s" % etiqueta)
        print("  %-14s %9s %9s %9s %9s %10s %9s %s"
              % ("columna", "An (cm2)", "s1 (cm)", "s2 (cm)", "s3 (cm)",
                 "s4 (cm)", "RIGE", "zona conf."))
        print("  " + "-" * 92)
        for d in peraltes:
            s1, s2, s3, s4, menor, zona, An, tn = estribos(d, av)
            cual = {s1: "s1", s2: "s2", s3: "s3", s4: "s4"}[menor]
            print("  %-14s %9.0f %9.2f %9.2f %9.2f %10.2f %6.2f %s %7.0f cm"
                  % ("%.0f x %.0f" % (ESPESOR * 100, d), An, s1, s2, s3, s4,
                     menor, cual, zona))
        print()

    print("  La zona de confinamiento es el MAYOR de %.0f cm y 1,5 d, medidos por"
          % ZONA_CONF_MIN)
    print("  debajo y por encima de la solera, dintel o sobrecimiento.")
    print()
    print("  POR QUE NO ALCANZA EL ESTRIBO DE 6 mm. Con ese diametro rige s1 y")
    print("  pide %.2f cm en la seccion chica: un estribo cada cuatro"
          % estribos(peraltes[0])[4])
    print("  centimetros, por debajo del minimo constructivo de %.0f cm. La salida"
          % S3_MIN)
    print("  no es apretar el paso hasta lo inejecutable sino subir el DIAMETRO:")
    print("  s1 y s2 son proporcionales a Av y se abren con el.")
    print()
    print("  Y AQUI ESTA EL PUNTO QUE SE HABIA PASADO POR ALTO. Al subir a 3/8\"")
    print("  **cambia el criterio que rige**: s1 y s2 crecen con Av, pero")
    print("  s3 = d/4 NO DEPENDE DE Av. El menor pasa de s1 a s3. Mirar solo")
    print("  como se relajo s1 y conservar el veredicto viejo deja el estribaje")
    print("  en el minimo del acapite -- 1 @ 5, 4 @ 10 -- cuando el calculo")
    print("  pide %.2f cm. Lo destapo el libro de San Bartolome, Quiun y Silva"
          % min(estribos(d, AV_38)[4] for d in peraltes))
    print("  (2015), 7.1.3 B.4, al describir el mismo acapite con el dato")
    print("  constructivo que la norma no escribe: multiplo de 2,5 cm, no mayor")
    print("  que 10 ni menor que 5.")
    print()
    s, zona, n = estribaje_adoptado(peraltes, AV_38)
    print("  ESTRIBAJE ADOPTADO:  %s" % _estribaje_texto(H_COLUMNA_EXT * 100.0))
    print("     zona de confinamiento cubierta: %.1f cm >= %.0f cm"
          % (S3_MIN + (n - 1) * s, zona))
    print("     + 2 estribos en la union solera-columna")
    print("     + estribos @ 10 cm en el sobrecimiento")
    print()
    print("  El paso de %.1f cm cumple el menor de los cuatro criterios en LAS DOS"
          % s)
    print("  secciones (%.2f cm en la C-1 y %.2f en la C-2) y es multiplo de 2,5."
          % (estribos(peraltes[0], AV_38)[4], estribos(peraltes[-1], AV_38)[4]))


def informe_soleras(muros):
    print()
    print("=" * 104)
    print("4. VIGAS SOLERAS  -  8.6.3 b, traccion PURA")
    print("=" * 104)
    print()
    print("  Ts = Vm1 Lm / (2 L)    ·    As = Ts/(%.1f fy), minimo 0,1 f'c Acs/fy"
          % PHI_SOLERA)
    print("  Solera de %.2f x %.2f m = %.0f cm2 (viga chata, peralte = espesor de losa)"
          % (B_SOLERA, H_SOLERA, B_SOLERA * 100 * H_SOLERA * 100))
    print()
    print("  %-30s %11s %10s %10s %s"
          % ("muro", "Ts (kgf)", "As req", "As min", "varillas"))
    print("  " + "-" * 82)
    for mu in muros:
        Ts, Acs, As, n, area = solera(mu, mu["t11"])
        print("  %-30s %11.0f %10.2f %10.2f  %d ø 1/2\" = %.2f cm2"
              % (mu["nom"], Ts, As, AS_MIN_FACTOR * FC * Acs / FY, n, area))
    print()
    print("  Estribos minimos de la solera (8.6.4): [] 6 mm, 1 @ 5, 4 @ 10, r @ 25 cm.")


def disenar():
    """Los muros con TODO su diseno adjunto, y sin imprimir nada.

    Existe porque el diseno se va adjuntando a los muros DENTRO de las
    funciones `informe*`, asi que hay un orden de llamadas obligatorio que
    antes cada consumidor tenia que adivinar: `informe()` pone el t11 e
    `informe_columnas()` pone el dis_e / dis_i. Quien se saltaba uno recibia
    un KeyError pelado. El orden vive aca, en un solo lugar.
    """
    import contextlib
    import io as _io
    muros = preparar()
    with contextlib.redirect_stdout(_io.StringIO()):
        informe(muros)
        informe_columnas(muros)
    return muros


def _estribaje_texto(d_cm, ganchos=0):
    peraltes = [H_COLUMNA * 100.0, H_COLUMNA_EXT * 100.0]
    s, zona_max, _ = estribaje_adoptado(peraltes, 2 * AREA_3_8)
    zona_base = max(ZONA_CONF_MIN, ZONA_CONF_FACTOR * d_cm)
    import math as _m
    n_base = int(_m.ceil(round(zona_base / s, 6)))
    assert n_base * s >= round(zona_base, 6) and (n_base - 1) * s < round(zona_base, 6)
    n_puerta = int(_m.ceil(round((H_DINTEL_PUERTA * 100.0 + zona_base) / s, 6)))
    assert n_puerta * s >= round(H_DINTEL_PUERTA * 100.0 + zona_base, 6) and (n_puerta - 1) * s < round(H_DINTEL_PUERTA * 100.0 + zona_base, 6)
    n_ventana = int(_m.ceil(round((H_DINTEL_VENTANA * 100.0 + zona_base) / s, 6)))
    assert n_ventana * s >= round(H_DINTEL_VENTANA * 100.0 + zona_base, 6) and (n_ventana - 1) * s < round(H_DINTEL_VENTANA * 100.0 + zona_base, 6)
    
    if abs(s - S3_MIN) < 1e-9:
        base = '[] 3/8": %d@%g, r@25' % (n_base, s)
        base += ' (%d@%g junto a puerta, %d@%g junto a ventana)' % (n_puerta, s, n_ventana, s)
    else:
        base = '[] 3/8": 1@%g, %d@%g, r@25' % (S3_MIN, n_base - 1, s)
        base += ' (1@%g, %d@%g junto a puerta; 1@%g, %d@%g junto a ventana)' % (S3_MIN, n_puerta - 1, s, S3_MIN, n_ventana - 1, s)
    return base + (" + %d gancho" % ganchos if ganchos else "")


def cuadro_de_columnas(muros):
    """Los datos del cuadro, SIN imprimir. Una sola fuente para dos destinos.

    El informe de abajo y el plano de estructuras (planos/dxf_estructuras.py)
    tienen que decir el mismo armado. Si cada uno lo calculara por su lado,
    tarde o temprano el plano y la memoria se separarian sin que nadie se
    entere, que es justo lo que este proyecto viene evitando.
    """
    import math as _m
    # guarda: el diseno de cada columna lo adjunta informe_columnas(). Sin esa
    # llamada previa esto reventaba con un KeyError pelado, que no dice que
    # hacer. Mejor decirlo.
    if not muros or "dis_e" not in muros[0]:
        raise RuntimeError(
            "cuadro_de_columnas() necesita que antes se haya corrido "
            "informe_columnas(muros), que es la que adjunta el diseno de "
            "cada columna a cada muro.")
    As_e = max(mu["dis_e"]["As"] for mu in muros)
    As_i = max(mu["dis_i"]["As"] for mu in muros)
    # PAR, no el techo pelado: ver _par(). El techo daba 11 y la C-2 se
    # dibujaba con una barra suelta en el centro del nucleo.
    n_e = _par(max(4, _m.ceil(As_e / AREA_3_4)))
    n_i = _par(max(4, _m.ceil(As_i / AREA_1_2)))
    disp_e = disposicion(ESPESOR * 100.0, H_COLUMNA_EXT * 100.0, n_e, '3/4"')
    cuadro = [
        {"tipo": "C-2", "b": ESPESOR, "h": H_COLUMNA_EXT,
         "n": n_e, "diam": '3/4"', "area_barra": AREA_3_4,
         "As_req": As_e, "As_prov": n_e * AREA_3_4,
         "estribo": _estribaje_texto(H_COLUMNA_EXT * 100.0, len(disp_e["ganchos"])),
         "disp": disp_e},
        {"tipo": "C-1", "b": ESPESOR, "h": H_COLUMNA,
         "n": n_i, "diam": '1/2"', "area_barra": AREA_1_2,
         "As_req": As_i, "As_prov": n_i * AREA_1_2,
         "estribo": _estribaje_texto(H_COLUMNA * 100.0)},
        {"tipo": "VS-1", "b": B_SOLERA, "h": H_SOLERA,
         "n": 4, "diam": '1/2"', "area_barra": AREA_1_2,
         "As_req": None, "As_prov": 4 * AREA_1_2,
         "estribo": "[] 6mm: 1@5, 4@10, r@25"},
        # La C-3 no es de confinamiento: la exige el 9.1 de la E.070 para que
        # el descanso de la escalera no descargue en la albanileria. Nacio en
        # otro script y por eso el PLANO no la conocia -- dibujaba C-1 y C-2 y
        # el elemento que la norma manda poner no figuraba en ninguna parte.
        _cargar("27_columnas_de_escalera.py").fila_cuadro(),
    ]
    for fila in cuadro:
        completar_disposicion(fila)
    # si la disposicion pide gancho, el estribaje del cuadro tiene que decirlo
    for fila in cuadro:
        assert not fila["disp"]["ganchos"] or "gancho" in fila["estribo"], (
            "%s necesita gancho y su estribaje no lo dice" % fila["tipo"])
    return cuadro


def cierre(muros):
    print()
    print("=" * 104)
    print("CIERRE DEL CRITERIO 9  -  cuadro de columnas para el plano")
    print("=" * 104)
    print()
    cuadro = cuadro_de_columnas(muros)
    As_e = cuadro[0]["As_req"]
    As_i = cuadro[1]["As_req"]
    n_e = cuadro[0]["n"]
    n_i = cuadro[1]["n"]
    print("  %-8s %-14s %-11s %-22s %s"
          % ("TIPO", "SECCION", "Ac", "REFUERZO LONGITUDINAL", "ESTRIBOS"))
    print("  " + "-" * 94)
    # AUDITORIA 2026-09-19. Estas filas se imprimian A MANO, una por una,
    # mientras cuadro_de_columnas() existia al lado como "fuente unica".
    # Tener la fuente y no usarla es peor que no tenerla: cuando aparecio la
    # C-3 entro al cuadro -- y por tanto al PLANO -- pero no a este informe,
    # asi que memoria y plano decian cosas distintas, que es justo lo que la
    # fuente unica se creo para impedir. Ahora se ITERA.
    for fila in cuadro:
        print("  %-8s %-14s %-11s %-22s %s"
              % (fila["tipo"],
                 "%.0f x %.0f cm" % (fila["b"] * 100, fila["h"] * 100),
                 "%.0f cm2" % (fila["b"] * 100 * fila["h"] * 100),
                 "%d ø %s (%.1f cm2)" % (fila["n"], fila["diam"], fila["As_prov"]),
                 fila["estribo"]))
    print()
    print()
    print("  DISPOSICION DE LAS VARILLAS  -  E.060 7.6.3 y 7.10.5.3")
    print("  %-6s %-12s %-16s %-22s %s"
          % ("TIPO", "ARMADO", "POR CARA (b,h)", "LIBRE MIN / EXIGIDO", "GANCHOS"))
    for fila in cuadro:
        d = fila["disp"]
        print("  %-6s %-12s %-16s %-22s %d"
              % (fila["tipo"], "%d o %s" % (fila["n"], fila["diam"]),
                 "%d y %d" % d["por_cara"],
                 "%.2f >= %.2f cm" % (d["libre"], d["exigido"]),
                 len(d["ganchos"])))
    # el 5/8" del 27 tiene que ser el mismo de aca
    assert abs(_cargar("27_columnas_de_escalera.py").fila_cuadro()["area_barra"]
               - AREA_5_8) < 1e-9, "el 27 usa otra area para el 5/8"
    print("  [ok] todas en el perimetro, distancia libre y apoyo lateral cumplen")
    print()
    print("  As requerido: C-2 %.2f cm2 (cuantia %.2f %%) · C-1 %.2f cm2 (%.2f %%)"
          % (As_e, 100 * As_e / (ESPESOR * 100 * H_COLUMNA_EXT * 100),
             As_i, 100 * As_i / (ESPESOR * 100 * H_COLUMNA * 100)))
    print("  Las dos cuantias quedan holgadas bajo el 6 % maximo del concreto.")
    print()
    print("  UBICACION EN PLANTA")
    print("     C-2  ->  los dos extremos de cada muro. En este edificio eso es")
    print("              TODO EL PERIMETRO (x = 0 y x = %.2f) mas los extremos de"
          % FRENTE)
    print("              los muros del pozo. Son las que cruzan dos muros, y el")
    print("              8.5.1.1 manda tomar ahi EL MAYOR de los dos disenos.")
    print("     C-1  ->  las interiores de los muros transversales (x = 3,30 ·")
    print("              6,00 · 8,70), que solo pertenecen a un muro.")
    print()
    print("  POR QUE DOS TIPOS Y NO UNO SOLO. Unificar en C-2 seria mas simple en")
    print("  obra, pero mete concreto (2400 kgf/m3) donde habria albanileria (1800)")
    print("  y sube el peso sismico sin ganar nada: a la interior la gobierna el")
    print("  minimo de 15t, no el calculo. Unificar en C-1 deja los extremos")
    print("  cortos, que es justo donde el momento levanta la columna.")
    print()
    print("  PISOS 2 A %d: el script 18 verifico que NINGUNO se agrieta, asi que" % N_PISOS)
    print("  van por el 8.6.4 -- extremas por la traccion del momento (que da")
    print("  menos que el primer piso) e internas con refuerzo minimo. Se mantiene")
    print("  el mismo detalle en todos los niveles para no cambiar el armado a")
    print("  media altura, que es donde la obra se equivoca.")


if __name__ == "__main__":
    muros = preparar()
    informe(muros)
    informe_columnas(muros)
    informe_estribos(muros)
    informe_soleras(muros)
    cierre(muros)
    filas = verificar_delta_y_pt(muros)
    print()
    print("=" * 104)
    print("VERIFICACION DE COMPRESION CON Pt Y delta POR COLUMNA  -  8.6.3-a.1 y 8.3.6")
    print("=" * 104)
    sin_t = [x for x in filas if x[4] < DELTA_TRANSV]
    print("  %d verificaciones (cada columna en cada muro al que pertenece)" % len(filas))
    print("  %d con delta = %.1f (sin muro transversal): %s"
          % (len(sin_t), DELTA_SIN_TRANSV,
             ", ".join(sorted({"(%.2f;%.2f)" % x[1] for x in sin_t}))))
    peor = max(filas, key=lambda x: x[7] / x[8])
    print("  la mas exigida: %s en (%.2f;%.2f), %s, C = %.0f kgf, Pt = %.0f kgf,"
          % (peor[0], peor[1][0], peor[1][1], peor[2], peor[6], peor[5]))
    print("     An necesario %.0f cm2 <= disponible %.0f cm2 (%.0f %%)"
          % (peor[7], peor[8], 100.0 * peor[7] / peor[8]))
    print("  [ok] el nucleo alcanza en todas: el armado NO cambia")
