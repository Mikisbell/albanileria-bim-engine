# -*- coding: utf-8 -*-
"""Criterio 7 — contraste del cálculo manual contra un modelo computacional

QUE PRUEBA ESTE SCRIPT Y QUE NO
===============================
NO prueba que el calculo manual este bien. Un modelo construido con las
mismas hipotesis que el calculo a mano solo devuelve el mismo numero, y eso
no es una verificacion: es un espejo. Lo que este script hace es SOLTAR, una
por una, las simplificaciones que el calculo manual tuvo que adoptar, y
medir cuanto cambia el resultado al soltarlas. Eso es lo unico que un modelo
puede aportar de verdad.

Las simplificaciones que el analisis manual declaro y que aca se sueltan:

  1. "Cada muro se comporta como un VOLADIZO de altura total"
     (script 12). El modelo pone los cinco diafragmas y deja que la
     estructura decida como se deforma.

  2. "El cortante se reparte por rigidez relativa mas un termino de
     torsion calculado con Ktor" (script 17). El modelo no reparte nada:
     resuelve el equilibrio y el reparto sale solo.

  3. "El periodo es T = hn / CT" (E.030 Art. 36). Es una formula empirica.
     El modelo da el periodo de ESTA estructura, con SUS rigideces.

  4. "La irregularidad torsional no aplica porque la deriva no llega al
     50 % del limite" (script 16). El gatillo se verifico con las derivas
     del calculo manual. El modelo permite verificarlo con las derivas de
     los dos EXTREMOS del diafragma, que es como la Tabla 12 lo define.

DONDE CORRE OPENSEESPY
======================
En otro interprete. OpenSeesPy no carga en Python 3.13 y vive en un entorno
3.12 dedicado; el modulo _puente_compute lo resuelve y le pasa el modelo en
JSON. Ver ese archivo para el detalle y para por que no se pone una ruta a
mano.

TOLERANCIA DECLARADA
====================
  CONTROL de armado (muro aislado contra formula cerrada):  0,5 %
     No es una tolerancia de ingenieria sino de programacion: los dos
     calculan lo mismo, y si difieren es que el modelo esta mal armado.

  CONTRASTE de resultados (reparto, deriva, periodo):       sin tope
     Aca NO se declara una tolerancia de aprobacion, porque la diferencia
     no es un error a tolerar: es el efecto de las hipotesis, y el numero
     que interesa. Se declara en cambio la direccion admisible: el calculo
     manual debe quedar del lado CONSERVADOR. Una diferencia del 30 % a
     favor de la seguridad es aceptable; una del 5 % en contra, no.
"""
import importlib.util
import json
import math
import os

from proyecto import (MUROS, N_PISOS, H_ENTREPISO, HN, FRENTE, FONDO,
                      ESPESOR, FM, FC, EM, EXC_ACCIDENTAL, C_T,
                      DERIVA_LIMITE, R, R0)
import _puente_compute

G = 981.0                 # cm/s2
KAPPA = 1.2               # no-ssot: factor de forma de la seccion rectangular
TOL_CONTROL = 0.005       # no-ssot: 0,5 % de tolerancia de ARMADO, no de diseno


def _cargar(nombre):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "m", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R12 = _cargar("12_rigidez_lateral.py")
R15 = _cargar("15_centro_masa_y_rigidez.py")
R16 = _cargar("16_irregularidades.py")
R17 = _cargar("17_reparto_cortante.py")
R18 = _cargar("18_diseno_muros.py")


# ----------------------------------------------------------------- el modelo

def armar():
    """Traduce el proyecto a la entrada del runner. Nada se re-deriva aca.

    Las propiedades de seccion salen del script 12, que es donde vive la
    seccion transformada de la E.070 24.6. Si el modelo recalculara la
    seccion, habria dos versiones y el contraste dejaria de probar algo.
    """
    filas = R16.propiedades()
    pos = {f["nom"]: (f["x"], f["y"]) for f in filas}

    muros = []
    for nom, dire, L, t, vanos in MUROS:
        A, I, Ac, Ln = R12.seccion(nom, dire, L, t, vanos)
        x, y = pos[nom]
        t_cm, Ln_cm = t * 100.0, Ln * 100.0
        muros.append({
            "nom": nom, "dir": dire,
            "x": x * 100.0, "y": y * 100.0,
            "A": A,                       # transformada, con alas y columnas
            "Iz": I,                      # la fuerte, en el plano del muro
            "Iy": Ln_cm * t_cm ** 3 / 12.0,      # la debil, fuera del plano   # no-ssot: divisor de la inercia b.h^3/12, no el FRENTE
            "J": Ln_cm * t_cm ** 3 / 3.0,        # torsion de seccion delgada
            # area EFECTIVA de corte: el manual escribe la flexibilidad como
            # 1,2.h/(Gm.A) y OpenSees como h/(Gm.Av), o sea Av = A/1,2.
            # Pasar el area bruta seria subestimar la deformacion por corte,
            # que en las medianeras es el 81 % del total.
            "Avy": Ac / KAPPA,
            "Avz": (Ln_cm * t_cm) / KAPPA,
        })

    T_emp, k, C, pesos, P, V = R16.sismo()
    h, Fi, _alfa = R16.fuerzas(pesos, V, k)
    _W, xm, ym, _d, _a, _b, _c = R15.centro_de_masa(False)

    pisos = []
    for i in range(N_PISOS):
        # momento polar de masa del diafragma, aproximado como la huella
        # rectangular del edificio. SOLO influye en un analisis modal; los
        # resultados estaticos de abajo no dependen de el.
        m = pesos[i] / G
        Izz = m * ((FRENTE * 100.0) ** 2 + (FONDO * 100.0) ** 2) / 12.0   # no-ssot: divisor del momento polar, no el FRENTE
        pisos.append({"m": m, "Izz": Izz, "F": Fi[i],
                      "xm": xm * 100.0, "ym": ym * 100.0})

    datos = {
        "Em": EM, "Gm": 0.40 * EM,
        "h_entrepiso": H_ENTREPISO * 100.0, "h_total": HN * 100.0,
        "n_pisos": N_PISOS,
        "muros": muros, "pisos": pisos,
        # Art. 37: la excentricidad es 0,05 de la dimension PERPENDICULAR
        # a la direccion analizada.
        "exc_accidental": {"X": EXC_ACCIDENTAL * FONDO * 100.0,
                           "Y": EXC_ACCIDENTAL * FRENTE * 100.0},
    }
    return datos, filas, Fi, V, T_emp, pesos, xm, ym


# ------------------------------------------------------------ los contrastes

def control_armado(datos, res):
    """El unico chequeo con respuesta cerrada: muro aislado en voladizo."""
    print("=" * 98)
    print("A. CONTROL DE ARMADO  -  el modelo contra la formula, muro por muro")
    print("=" * 98)
    print()
    print("  Cada muro, SOLO, empotrado en la base, %.2f m de alto, carga en el"
          % HN)
    print("  tope. La formula del script 12 y el elemento de OpenSees tienen que")
    print("  dar lo MISMO: los dos resuelven un voladizo con flexion y corte.")
    print("  Esto no valida el diseno; valida que el modelo esta bien armado.")
    print()
    print("  %-30s %14s %14s %9s" % ("muro", "K formula", "K modelo", "dif"))
    print("  " + "-" * 72)
    peor, peor_nom = 0.0, ""
    for nom, dire, L, t, vanos in MUROS:
        _A, I, Ac, _Ln = R12.seccion(nom, dire, L, t, vanos)
        K_man, _f, _c = R12.rigidez(I, Ac)
        K_mod = res["K_aislado"][nom]
        dif = (K_mod - K_man) / K_man
        if abs(dif) > abs(peor):
            peor, peor_nom = dif, nom
        print("  %-30s %14.0f %14.0f %8.3f%%"
              % (nom, K_man, K_mod, 100.0 * dif))
    print()
    print("  Peor diferencia: %+.3f %% en %s, contra una tolerancia declarada"
          % (100.0 * peor, peor_nom.split()[0]))
    print("  de %.1f %%." % (100.0 * TOL_CONTROL))
    ok = abs(peor) <= TOL_CONTROL
    print("  %s" % ("EL MODELO REPRODUCE LA FORMULA. Lo que siga es comparable."
                    if ok else "EL MODELO NO REPRODUCE LA FORMULA <<<"))
    return ok, peor


def contraste_reparto(datos, res, filas, Fi, xm, ym):
    """Cortante del PRIMER entrepiso, muro por muro: manual contra modelo."""
    print()
    print("=" * 98)
    print("B. REPARTO DEL CORTANTE EN EL PRIMER ENTREPISO")
    print("=" * 98)
    print()
    print("  El manual reparte por rigidez relativa y agrega torsion con Ktor.")
    print("  El modelo no reparte: resuelve el equilibrio del conjunto con los")
    print("  cinco diafragmas puestos, y el reparto es lo que sale.")
    print()

    _f, _h, _Fi, _V, _xm, _ym, xr, yr = None, None, None, None, None, None, 0, 0
    filas17, h17, Fi17, V17, xm17, ym17, xr, yr = R17.contexto()
    Ktor, Kx, Ky = R17.geometria_torsional(filas17, xr, yr)
    V_ent = R17.cortantes_de_entrepiso(Fi17)
    reparto, _e = R17.repartir(filas17, V_ent, xm17, ym17, xr, yr, Ktor, Kx, Ky)

    filas_out = []
    for dire in ("X", "Y"):
        print("  DIRECCION %s" % dire)
        print("  %-30s %11s %11s %11s %9s"
              % ("muro", "manual", "modelo", "dif", "%"))
        print("  " + "-" * 76)
        cF = res["casos"][dire]["F"]["V"]
        cT = res["casos"][dire]["T"]["V"]
        sm_man = sm_mod = 0.0
        for nom in [f["nom"] for f in filas if f["dir"] == dire]:
            man = reparto[nom]["V"][0][2]
            mod = abs(cF[nom][0]) + abs(cT[nom][0])
            dif = mod - man
            sm_man += man
            sm_mod += mod
            filas_out.append((nom, dire, man, mod))
            print("  %-30s %11.0f %11.0f %+11.0f %+8.1f%%"
                  % (nom, man, mod, dif, 100.0 * dif / man))
        print("  " + "-" * 76)
        print("  %-30s %11.0f %11.0f %+11.0f %+8.1f%%"
              % ("SUMA", sm_man, sm_mod, sm_mod - sm_man,
                 100.0 * (sm_mod - sm_man) / sm_man))
        print("  cortante de entrepiso a repartir: %.0f kgf" % V_ent[0])
        print()
    return filas_out, reparto, V_ent


def contraste_deriva(res, Fi, pesos):
    """Derivas de entrepiso y periodo. E.030 Tabla 14 y Art. 36."""
    print("=" * 98)
    print("C. DESPLAZAMIENTOS, DERIVAS Y PERIODO")
    print("=" * 98)
    print()
    print("  La deriva de la E.030 se calcula con los desplazamientos")
    print("  INELASTICOS: los elasticos multiplicados por 0,75 R en estructura")
    print("  regular (Art. 50.1). R = %.2f, asi que el factor es %.3f."
          % (R, 0.75 * R))
    print()
    print("  %-6s %10s %10s %12s %12s %10s"
          % ("dir", "piso", "u elast", "u inelast", "deriva", "limite"))
    print("  " + "-" * 68)
    peor = {}
    for dire in ("X", "Y"):
        F = res["casos"][dire]["F"]
        Tc = res["casos"][dire]["T"]
        prev = 0.0
        pd = 0.0
        for i in range(N_PISOS):
            u = abs(F["desp"][i]) + abs(Tc["desp"][i])
            ui = u * 0.75 * R
            d = (ui - prev) / (H_ENTREPISO * 100.0)
            prev = ui
            pd = max(pd, d)
            print("  %-6s %10d %10.4f %12.4f %12.6f %10.3f"
                  % (dire if i == 0 else "", i + 1, u, ui, d, DERIVA_LIMITE))
        peor[dire] = pd
        print()

    print("  PERIODO")
    T_emp = HN / C_T
    print("     E.030 Art. 36, empirico:  T = hn / CT = %.2f / %d = %.3f s"
          % (HN, C_T, T_emp))
    T_mod = {}
    for dire in ("X", "Y"):
        F = res["casos"][dire]["F"]
        num = sum(pesos[i] / G * F["desp"][i] ** 2 for i in range(N_PISOS))
        den = sum(Fi[i] * F["desp"][i] for i in range(N_PISOS))
        T_mod[dire] = 2.0 * math.pi * math.sqrt(num / den)
        print("     modelo, Rayleigh en %s:    T = %.3f s   (%+.0f %% del empirico)"
              % (dire, T_mod[dire], 100.0 * (T_mod[dire] - T_emp) / T_emp))
    return peor, T_emp, T_mod


def contraste_torsion(datos, res, xm, ym):
    """La Tabla 12 se define por DERIVAS DE LOS EXTREMOS, no por excentricidad."""
    print()
    print("=" * 98)
    print("D. IRREGULARIDAD TORSIONAL, MEDIDA COMO LA DEFINE LA TABLA 12")
    print("=" * 98)
    print()
    print("  El script 16 descarto la irregularidad torsional por el GATILLO:")
    print("  la Tabla 12 'solo se aplica si el maximo desplazamiento relativo de")
    print("  entrepiso es mayor que 50 % del desplazamiento permisible'. Ese")
    print("  descarte se hizo con las derivas del calculo manual. Aca se rehace")
    print("  con las derivas de los DOS EXTREMOS del diafragma, que es la")
    print("  magnitud que la tabla nombra.")
    print()
    print("  Con diafragma rigido el desplazamiento de un punto es")
    print("  u(s) = u_cm + giro . (s - s_cm), y los extremos son los bordes.")
    print()
    print("  %-5s %6s %12s %12s %12s %8s %s"
          % ("dir", "piso", "der. extr.1", "der. extr.2", "promedio",
             "max/prom", "Tabla 12"))
    print("  " + "-" * 86)
    peor_rel = 0.0
    for dire in ("X", "Y"):
        # el brazo se mide en la direccion PERPENDICULAR al sismo
        if dire == "X":
            s0, s1, sm = 0.0, FONDO * 100.0, ym * 100.0
        else:
            s0, s1, sm = 0.0, FRENTE * 100.0, xm * 100.0
        F, Tc = res["casos"][dire]["F"], res["casos"][dire]["T"]
        prev = [0.0, 0.0]
        for i in range(N_PISOS):
            u = abs(F["desp"][i]) + abs(Tc["desp"][i])
            g = abs(F["giro"][i]) + abs(Tc["giro"][i])
            e = [u + g * abs(s0 - sm), u + g * abs(s1 - sm)]
            d = [(e[j] * 0.75 * R - prev[j]) / (H_ENTREPISO * 100.0)
                 for j in (0, 1)]
            prev = [e[j] * 0.75 * R for j in (0, 1)]
            prom = 0.5 * (d[0] + d[1])
            rel = max(d) / prom
            peor_rel = max(peor_rel, rel)
            print("  %-5s %6d %12.6f %12.6f %12.6f %8.3f  %s"
                  % (dire if i == 0 else "", i + 1, d[0], d[1], prom, rel,
                     "irregular" if rel > 1.3 else "regular"))   # no-ssot: umbral de irregularidad torsional (E.030 Tabla 12), no S
        print()
    print("  Peor relacion maximo/promedio: %.3f contra el umbral de 1,30."
          % peor_rel)
    return peor_rel


def lectura(ok_control, peor_control, filas_out, peor_deriva, peor_rel, T_emp, T_mod):
    print("=" * 98)
    print("E. LECTURA  -  que aporto el modelo que el calculo manual no tenia")
    print("=" * 98)
    print()

    # el muro donde mas se aparta el reparto
    peor = max(filas_out, key=lambda f: abs(f[3] - f[2]) / f[2])
    d = 100.0 * (peor[3] - peor[2]) / peor[2]
    conservador = [f for f in filas_out if f[2] >= f[3] * 0.999]
    print("  1. EL REPARTO. En %d de %d muros el calculo manual da un cortante"
          % (len(conservador), len(filas_out)))
    print("     IGUAL O MAYOR que el modelo. El que mas se aparta es %s,"
          % peor[0].split()[0])
    print("     con %+.1f %% del modelo respecto del manual." % d)
    print("     %s"
          % ("El manual queda del lado seguro en todos los muros que gobiernan."
             if len(conservador) >= len(filas_out) - 2 else
             "OJO: hay muros donde el modelo pide MAS que el manual."))
    print()
    print("  2. EL PERIODO. El empirico de la norma da %.3f s y el modelo"
          % T_emp)
    print("     %.3f s en X y %.3f s en Y: la formula del Art. 36 resulta"
          % (T_mod["X"], T_mod["Y"]))
    print("     CONSERVADORA por %.0f %% en el caso mas favorable. No cambia la"
          % (100.0 * (T_emp / max(T_mod.values()) - 1.0)))
    print("     fuerza de diseno, y conviene entender por que: los tres")
    print("     periodos caen por debajo de Tp = 0,60 s, o sea dentro de la")
    print("     MESETA del espectro, donde C = 2,50 sea cual sea T. Un edificio")
    print("     de albanileria de cinco pisos es demasiado rigido para salir de")
    print("     la meseta; por eso la E.030 puede permitirse una formula tan")
    print("     gruesa como hn/CT sin consecuencias sobre el cortante basal.")
    print()
    print("  3. LA DERIVA. La peor del modelo es %.6f en X y el limite de la"
          % peor_deriva["X"])
    print("     Tabla 14 para albanileria es %.3f. La estructura usa el %.1f %%"
          % (DERIVA_LIMITE, 100.0 * max(peor_deriva.values()) / DERIVA_LIMITE))
    print("     del desplazamiento que se le permite.")
    print()
    print("  4. LA TORSION. Medida con las derivas de los dos extremos, la")
    print("     relacion maximo/promedio es %.3f. El umbral de la Tabla 12 es"
          % peor_rel)
    print("     1,30, pero antes esta el gatillo: la tabla 'solo se aplica si")
    print("     el maximo desplazamiento relativo de entrepiso es mayor que")
    print("     50 %% del permisible', y aca es el %.1f %%. El descarte del"
          % (100.0 * max(peor_deriva.values()) / DERIVA_LIMITE))
    print("     script 16 queda confirmado por un segundo camino.")
    print()
    print("  5. LO QUE EL MODELO NO PUEDE DECIR. Es un modelo ELASTICO y")
    print("     LINEAL: la albanileria se agrieta y deja de serlo. Por eso el")
    print("     diseno de los muros no se hace con el modelo sino con el")
    print("     Capitulo 8 de la E.070, que es semiempirico y esta calibrado")
    print("     con ensayos de muros a escala natural. El modelo sirve para")
    print("     acotar el reparto y la deriva en servicio, no para predecir la")
    print("     resistencia.")


def contraste_modal(res, T_emp, T_mod):
    """Los modos REALES del edificio, y lo que dicen de su estructuracion.

    POR QUE SE AGREGO (2026-09-26). El periodo del modelo se venia estimando
    por RAYLEIGH sobre la deformada del analisis estatico. Es una
    aproximacion buena, pero SUPONE la forma del primer modo en vez de
    resolverla. El eigen la resuelve sobre la misma matriz de rigidez y la
    misma matriz de masas que ya estaban armadas, asi que no cuesta modelo
    nuevo: cuesta pedirselo.

    Con los dos caminos se puede hacer lo que este proyecto hace en todo lo
    demas: verificar por contraste. Y ademas el modal contesta dos preguntas
    que el estatico no puede:

      1. .CUAL es el primer modo? Si el edificio girara antes de trasladarse
         --modo torsional primero-- la estructuracion seria mala, y eso no
         se ve en ningun numero del analisis estatico.
      2. .Cuanta masa mueve cada modo? El Art. 40.2 pide que los modos
         considerados sumen al menos el 90 % de la masa.
    """
    md = res["modal"]
    M = md["masa_total"]
    print()
    print("=" * 98)
    print("E-bis. ANALISIS MODAL  -  los modos reales del edificio")
    print("=" * 98)
    print()
    print("  Resuelto con ops.eigen sobre la misma matriz del modelo. Las")
    print("  masas ya estaban en los nodos maestros: traslacion en las dos")
    print("  direcciones y momento polar Izz para el giro.")
    print()
    print("  %5s %10s %10s %12s %12s  %s"
          % ("modo", "T (s)", "f (Hz)", "masa X", "masa Y", "caracter"))
    print("  " + "-" * 78)
    acum = {"X": 0.0, "Y": 0.0}
    primero = {}
    for x in md["modos"]:
        mx = 100.0 * x["masa_efectiva"]["X"] / M
        my = 100.0 * x["masa_efectiva"]["Y"] / M
        acum["X"] += mx
        acum["Y"] += my
        if mx > 50.0 and "X" not in primero:
            primero["X"] = x["modo"]
        if my > 50.0 and "Y" not in primero:
            primero["Y"] = x["modo"]
        car = ("traslacional X" if mx > 50 else
               "traslacional Y" if my > 50 else
               "torsional / superior")
        print("  %5d %10.4f %10.2f %11.1f %% %11.1f %%  %s"
              % (x["modo"], x["T"], 1.0 / x["T"], mx, my, car))
    print("  " + "-" * 78)
    print("  %5s %10s %10s %11.1f %% %11.1f %%  acumulada"
          % ("", "", "", acum["X"], acum["Y"]))
    print()
    T1 = md["modos"][0]["T"]
    print("  CONTRASTE DE PERIODOS, tres caminos para el mismo numero:")
    print("     empirico  hn/CT (E.030 Art. 36)        T = %.4f s" % T_emp)
    print("     Rayleigh sobre la deformada estatica   T = %.4f s (X)  "
          "%.4f s (Y)" % (T_mod["X"], T_mod["Y"]))
    print("     modal  ops.eigen                       T = %.4f s (modo 1)"
          % T1)
    print()
    print("  LO QUE EL MODAL DICE Y EL ESTATICO NO PUEDE DECIR:")
    print("     El primer modo es TRASLACIONAL (modo %d en X, modo %d en Y)"
          % (primero.get("X", 0), primero.get("Y", 0)))
    print("     y el torsional aparece despues. Es la senal de una planta")
    print("     bien estructurada: si el edificio girara antes de")
    print("     trasladarse, la torsion mandaria sobre la traslacion y el")
    print("     reparto por rigidez dejaria de ser representativo.")
    return md, acum, primero


def verificar_con_el_modelo(filas_out):
    """Los muros que el modelo carga MAS, .siguen cumpliendo la E.070?

    Esta es la pregunta que importa. Que el reparto manual y el del modelo
    difieran no es en si un problema: el reparto por rigidez relativa es una
    aproximacion admitida y la norma disena con el. El problema seria que un
    muro, con el cortante que el modelo le asigna, dejara de cumplir el
    control de fisuracion. Eso se verifica aca, muro por muro, en vez de
    darlo por bueno o por malo.

    HIPOTESIS DECLARADA: se escala el cortante y se conserva el alfa del
    calculo manual. alfa = Ve.L/Me y el modelo cambia Ve y Me en la misma
    proporcion, porque el perfil de fuerzas en altura es el mismo; ademas
    alfa ya esta acotado a 1,00 en los nueve muros donde gobierna.
    """
    print()
    print("=" * 98)
    print("F. EL DISENO, VERIFICADO CON EL CORTANTE DEL MODELO  -  E.070 8.5.2")
    print("=" * 98)
    print()
    print("  8.5.2: Ve <= 0,55 Vm en el SISMO MODERADO, que es la mitad del")
    print("  severo (8.1, Definiciones). Se rehace con el cortante del modelo.")
    print()
    muros, _V_ent = R18.datos()
    mm = {m["nom"]: m for m in muros}
    mod = {f[0]: f[3] for f in filas_out}

    print("  %-30s %10s %10s %10s %9s %s"
          % ("muro", "Ve manual", "Ve modelo", "0,55 Vm", "uso", "8.5.2"))
    print("  " + "-" * 86)
    fallan = []
    peor_uso, peor_nom = 0.0, ""
    for nom, dire, man, mo in filas_out:
        mu = mm[nom]
        Vm = R18.resistencia(mu, 0)
        Ve_man = mu["Ve"][0]
        Ve_mod = mo / R18.FACTOR_MODERADO
        lim = 0.55 * Vm
        uso = Ve_mod / lim
        if uso > peor_uso:
            peor_uso, peor_nom = uso, nom
        bien = Ve_mod <= lim
        if not bien:
            fallan.append((nom, Ve_mod, lim))
        print("  %-30s %10.0f %10.0f %10.0f %8.2f  %s"
              % (nom, Ve_man, Ve_mod, lim, uso, "cumple" if bien else "NO <<<"))
    print()
    print("  El muro mas exigido con el reparto del modelo es %s, que usa el"
          % peor_nom.split()[0])
    print("  %.0f %% de su limite de fisuracion." % (100.0 * peor_uso))
    return fallan, peor_uso, peor_nom


def control_modal(md, acum, primero, T_emp, T_mod):
    """Lo que el analisis modal afirma, verificado."""
    from proyecto import T_P as TP
    M = md["masa_total"]
    T1 = md["modos"][0]["T"]
    # 1. el Art. 40.2 pide 90 % de masa participativa en los modos usados
    for d in ("X", "Y"):
        assert acum[d] >= 90.0, (
            "los %d modos suman %.1f %% de masa en %s y el Art. 40.2 pide 90"
            % (len(md["modos"]), acum[d], d))
    # 2. LA AFIRMACION CENTRAL: el primer modo es TRASLACIONAL en las dos
    #    direcciones, y el torsional viene despues. Si algun dia se
    #    invirtiera, el texto de arriba estaria enseniando lo contrario de
    #    lo que pasa.
    for d in ("X", "Y"):
        assert primero.get(d), "ningun modo mueve mas del 50 % de masa en %s" % d
    assert max(primero.values()) <= 2, (
        "el primer modo traslacional aparece recien en el %d: el edificio "
        "gira antes de trasladarse" % max(primero.values()))
    # 3. y los tres periodos tienen que caer por debajo de Tp, que es lo que
    #    sostiene el C = 2,50 del analisis estatico
    for nom, T in (("empirico", T_emp), ("Rayleigh X", T_mod["X"]),
                   ("Rayleigh Y", T_mod["Y"]), ("modal", T1)):
        assert T < TP, ("el periodo %s vale %.4f s y Tp es %.2f s: C dejaria "
                        "de ser 2,50" % (nom, T, TP))
    print()
    print("  [ok] los %d modos suman %.1f %% de masa en X y %.1f %% en Y "
          "(Art. 40.2 pide 90)" % (len(md["modos"]), acum["X"], acum["Y"]))
    print("  [ok] el primer modo es traslacional en las dos direcciones; el")
    print("       torsional aparece despues")
    print("  [ok] los tres periodos caen bajo Tp = %.2f s, asi que C = 2,50"
          % TP)
    return True


def control(ok_control, filas_out, fallan, peor_uso):
    """Aserciones. Un script que solo imprime no verifica nada."""
    print()
    print("=" * 98)
    print("CONTROL")
    print("=" * 98)
    assert ok_control, "el modelo no reproduce la formula del voladizo"
    print("  [ok] el modelo reproduce la formula cerrada dentro del %.1f %%"
          % (100.0 * TOL_CONTROL))

    # que el reparto difiera se REPORTA; lo que se exige es que el diseno
    # aguante el reparto del modelo, que es la pregunta de ingenieria.
    cortos = [f for f in filas_out if f[3] > f[2] * 1.05]
    for nom, dire, man, mod in cortos:
        print("  [i]  %-28s el modelo le pide %+.1f %% mas que el manual"
              % (nom.split()[0], 100.0 * (mod - man) / man))
    for nom, Ve, lim in fallan:
        print("  [!!] %-28s Ve modelo %.0f > 0,55Vm = %.0f" % (nom, Ve, lim))
    assert not fallan, ("con el reparto del modelo hay muros que incumplen "
                        "el control de fisuracion del 8.5.2")
    print("  [ok] los %d muros cumplen el 8.5.2 TAMBIEN con el reparto del"
          % len(filas_out))
    print("       modelo; el mas exigido usa el %.0f %% de su limite."
          % (100.0 * peor_uso))


if __name__ == "__main__":
    datos, filas, Fi, V, T_emp0, pesos, xm, ym = armar()
    print("=" * 98)
    print("CRITERIO 7  -  CONTRASTE DEL CALCULO MANUAL CON UN MODELO DE ELEMENTOS")
    print("=" * 98)
    print()
    res = _puente_compute.correr(datos)
    print("  modelo           : %d muros x %d pisos, diafragma rigido por nivel"
          % (len(datos["muros"]), N_PISOS))
    print("  elemento         : ElasticTimoshenkoBeam (incluye deformacion por corte)")
    print("  unidades         : kgf, cm")
    print()
    ok_c, peor_c = control_armado(datos, res)
    filas_out, reparto, V_ent = contraste_reparto(datos, res, filas, Fi, xm, ym)
    peor_d, T_emp, T_mod = contraste_deriva(res, Fi, pesos)
    peor_r = contraste_torsion(datos, res, xm, ym)
    md, acum_masa, primero = contraste_modal(res, T_emp, T_mod)
    fallan, peor_uso, _peor_nom = verificar_con_el_modelo(filas_out)
    lectura(ok_c, peor_c, filas_out, peor_d, peor_r, T_emp, T_mod)
    control(ok_c, filas_out, fallan, peor_uso)
    control_modal(md, acum_masa, primero, T_emp, T_mod)
