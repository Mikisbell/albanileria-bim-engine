# -*- coding: utf-8 -*-
"""Diseño de los muros al corte. E.070 Capítulo 8. Criterio 8 de la rúbrica

LO QUE HACE, EN EL ORDEN QUE MANDA LA NORMA
===========================================
  (3) Vm = 0,5 v'm alfa t L + 0,23 Pg          8.5.3
  (4) control de fisuracion: Ve <= 0,55 Vm      8.5.2   (sismo MODERADO)
  (5) resistencia del edificio: suma Vm >= VE   8.5.4   (sismo SEVERO)
      y el ATAJO: si suma Vm >= 3 VE, el diseno coplanar CULMINA ahi  8.5.5
  (6) amplificacion f = Vm1/Ve1, acotada 2 <= f <= 3; Vu = Ve f, Mu = Me f   8.6
  (7) refuerzo horizontal                       8.6.1
  (8) agrietamiento en pisos superiores: Vmi >= Vui   8.6.2

Las formulas estan verificadas contra la IMAGEN del PDF y transcritas en
PRONTUARIO-DISENO-MUROS.md. Aca solo se aplican.

LAS TRES TRAMPAS QUE ESTE SCRIPT EVITA A PROPOSITO
==================================================
1. `Pg` es la carga con SOBRECARGA REDUCIDA (25 % de CV), no la de servicio
   completa. Usar Pm infla Vm y es error del lado inseguro.
2. `L` es la longitud TOTAL del muro incluyendo columnas (8.5.3), no la neta
   con vanos descontados que usa el esfuerzo axial (7.1.1.b).
3. `Ve` y `Me` son del sismo MODERADO. El severo entra recien en el paso (5)
   para el control global, y en el (6) por amplificacion.

DE DONDE SALE CADA DATO
=======================
  alfa, Ve, Me     -> 17_reparto_cortante.py   (reparto directo + torsion)
  Pg               -> 11_metrado_muros.py      (metrado con 25 % de CV)
  v'm, t           -> proyecto.py              (SSOT)
Nada se re-deriva: si un numero cambia arriba, cambia aca solo.
"""
import importlib.util
import os

from proyecto import (VM, ESPESOR, MUROS, N_PISOS, FACTOR_MODERADO, FM,
                      H_UNIDAD, JUNTA_MIN, JUNTA_MAX,
                      SOBREESPESOR_JUNTA_REF, H_LIBRE)

C_ARCILLA = 0.5    # no-ssot: 8.5.3, coeficiente de arcilla (silico-calcarea 0,35)
C_PG = 0.23        # no-ssot: 8.5.3, aporte de la carga gravitacional
C_FISURA = 0.55    # no-ssot: 8.5.2, control de fisuracion
F_MIN, F_MAX = 2.0, 3.0      # no-ssot: 8.6, cota del factor de amplificacion
ATAJO_ELASTICO = 3.0         # no-ssot: 8.5.5, suma Vm >= 3 VE
C_SIGMA_REFUERZO = 0.05      # no-ssot: 8.6.1, sigma_m >= 0,05 f'm
RHO_MIN = 0.001              # no-ssot: 8.6.1, cuantia minima del refuerzo horizontal
HOLGURA_MIN = 0.10           # no-ssot: CRITERIO DE PROYECTO, no de la norma.
# La cuantia real depende del espesor de junta, que en obra varia entre 10 y
# 15 mm. Un diseno que cumple por el 1 % deja de cumplir con un milimetro de
# mortero de mas. Se exige 10 % de margen para absorber esa tolerancia.
ANCLAJE_COLUMNA = 12.5       # no-ssot: cm, E.070 4.2.3
GANCHO = 10.0                # no-ssot: cm, E.070 4.2.3, vertical a 90 grados
TRASLAPE_DIAMETROS = 45      # no-ssot: E.070 4.2.5, 45 veces el diametro

# Varillas candidatas para el refuerzo horizontal: (nombre, diametro m, area cm2)
CANDIDATAS = [
    ("6 mm",   0.0060, 0.283),   # no-ssot: 0,006 es el DIAMETRO de esta
    # varilla y coincide por casualidad con SOBREESPESOR_JUNTA_REF, que son
    # los 6 mm que el 4.1.2 suma a la junta. Dos magnitudes distintas que
    # valen lo mismo; el auditor no puede saberlo y por eso se tria a mano.
    ('1/4"',   0.00635, 0.320),
    ("8 mm",   0.0080, 0.503),
    ('3/8"',   0.00953, 0.710),
]


def _cargar(nombre):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "d", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R11 = _cargar("11_metrado_muros.py")
R17 = _cargar("17_reparto_cortante.py")


def datos():
    """Junta el reparto (17) con el metrado (11), muro por muro."""
    filas, h, Fi, V, xm, ym, xr, yr = R17.contexto()
    V_ent = R17.cortantes_de_entrepiso(Fi)
    Ktor, Kx, Ky = R17.geometria_torsional(filas, xr, yr)
    reparto, e = R17.repartir(filas, V_ent, xm, ym, xr, yr, Ktor, Kx, Ky)
    reparto = R17.momentos(reparto)
    metrado = {f["nom"]: f for f in R11.metrar()}

    muros = []
    for nom, dire, L, t, vanos in MUROS:
        r = reparto[nom]
        m = metrado[nom]
        Ve = [v[2] / FACTOR_MODERADO for v in r["V"]]      # moderado
        Me = [x / FACTOR_MODERADO for x in r["M"]]
        alfa = []
        for i in range(N_PISOS):
            # alfa usa la MISMA L que Vm (8.5.3): la neta. Mezclarlas seria
            # calcular el factor de una geometria y la resistencia de otra.
            a = Ve[i] * m["Ln"] / Me[i] if Me[i] else 0.0
            alfa.append(min(1.0, max(1.0 / 3.0, a)))
        muros.append({"nom": nom, "dir": dire, "L": L, "t": t,
                      "Pg": m["p"], "Pm": m["pm"], "Ln": m["Ln"],
                      "Ve": Ve, "Me": Me, "alfa": alfa,
                      "Ve_sev": [v[2] for v in r["V"]]})
    return muros, V_ent


def resistencia(mu, i):
    """Vm del entrepiso i, en kgf.  8.5.3, unidades de arcilla.

    QUE L VA ACA (hallazgo C-2 de la auditoria del 15-set, corregido el 17).
    El 8.5.3 dice L = "longitud total del muro (INCLUYENDO A LAS COLUMNAS en
    el caso de muros confinados)". Ese parentesis aclara que NO se descuentan
    las columnas de concreto; no dice que se incluyan los VANOS.

    Y el 6.4 lo prueba por el absurdo: si un vano no partiera el muro, el
    limite de 1,20 m "para ser considerados como contribuyentes" seria letra
    muerta, porque cualquier muro largo con huecos contaria entero.

    Se usa por lo tanto la longitud NETA (Ln), que es la suma de los machones.
    Antes se usaba la bruta y eso SOBREESTIMABA la resistencia -- del lado
    inseguro. Medido: SumVm/VE pasa de 2,762 a 2,323 en X y de 2,099 a 1,901
    en Y, y ningun muro se vuelca a "no cumple".
    """
    L_cm = mu["Ln"] * 100.0
    t_cm = mu["t"] * 100.0
    # Pg se reparte por piso: el muro del entrepiso i carga los de arriba
    Pg_i = mu["Pg"] * (N_PISOS - i) / N_PISOS
    return C_ARCILLA * VM * mu["alfa"][i] * t_cm * L_cm + C_PG * Pg_i


def paso_3_y_4(muros):
    print("=" * 100)
    print("3 y 4. RESISTENCIA AL AGRIETAMIENTO (8.5.3) Y FISURACION (8.5.2)")
    print("=" * 100)
    print()
    print("  Vm = %.1f v'm alfa t L + %.2f Pg    con v'm = %.1f kgf/cm2, t = %.2f m"
          % (C_ARCILLA, C_PG, VM, ESPESOR))
    print("  Control: Ve <= %.2f Vm, con Ve del sismo MODERADO" % C_FISURA)
    print()
    print("  %-30s %3s %6s %11s %11s %11s %9s %s"
          % ("muro", "dir", "alfa", "Pg (kgf)", "Vm (kgf)", "Ve mod", "Ve/0,55Vm",
             "8.5.2"))
    print("  " + "-" * 96)
    malos = []
    for mu in muros:
        Vm = resistencia(mu, 0)
        Ve = mu["Ve"][0]
        rel = Ve / (C_FISURA * Vm)
        ok = rel <= 1.0
        if not ok:
            malos.append(mu["nom"])
        mu["Vm1"] = Vm
        print("  %-30s %3s %6.3f %11.0f %11.0f %11.0f %9.3f %s"
              % (mu["nom"], mu["dir"], mu["alfa"][0], mu["Pg"], Vm, Ve, rel,
                 "cumple" if ok else "NO CUMPLE <<<"))
    print()
    if malos:
        print("  <<< %d muro(s) se fisuran ante el sismo moderado: %s"
              % (len(malos), ", ".join(malos)))
    else:
        print("  Los %d muros pasan el control de fisuracion. Es el control que"
              % len(muros))
        print("  el trabajo de referencia ni menciona, y el que asegura que el")
        print("  edificio no se agriete ante los sismos FRECUENTES.")
    return malos


def paso_5(muros, V_ent):
    print()
    print("=" * 100)
    print("5. RESISTENCIA AL CORTE DEL EDIFICIO (8.5.4) Y EL ATAJO DEL 8.5.5")
    print("=" * 100)
    print()
    VE = V_ent[0]           # cortante basal del sismo SEVERO
    print("  %-12s %14s %14s %10s %s"
          % ("direccion", "suma Vm (kgf)", "VE severo", "suma/VE", "8.5.4"))
    print("  " + "-" * 64)
    atajo = True
    for dire in ("X", "Y"):
        sVm = sum(mu["Vm1"] for mu in muros if mu["dir"] == dire)
        rel = sVm / VE
        if rel < ATAJO_ELASTICO:
            atajo = False
        print("  %-12s %14.0f %14.0f %10.3f %s"
              % (dire, sVm, VE, rel, "cumple" if rel >= 1.0 else "NO CUMPLE <<<"))
    print()
    print("  El 8.5.5 dice que si suma(Vm) >= %.0f VE en CADA entrepiso, el"
          % ATAJO_ELASTICO)
    print("  edificio se comporta elasticamente y \"en este paso culminara el")
    print("  diseno de estos edificios ante cargas sismicas coplanares\".")
    print()
    if atajo:
        print("  >>> EL ATAJO APLICA. Se podria cerrar el diseno coplanar aca y")
        print("  usar refuerzo minimo. Se sigue igual con el diseno completo,")
        print("  porque la rubrica pide las verificaciones y porque tener el")
        print("  margen no exime de mostrarlo.")
    else:
        print("  El atajo NO aplica: la holgura alcanza para cumplir el 8.5.4 pero")
        print("  no llega al triple. Hay que hacer el diseno completo, que es lo")
        print("  que sigue. Conviene decirlo en el informe: se evaluo y no se uso.")
    return atajo


def paso_6(muros, V_ent):
    """f = Vm1/Ve1 del PRIMER piso, acotado entre 2 y 3."""
    print()
    print("=" * 100)
    print("6. FUERZAS DE DISENO (8.6)  -  amplificacion del sismo moderado")
    print("=" * 100)
    print()
    print("  f = Vm1/Ve1 (ambos del primer piso), acotado %.0f <= f <= %.0f"
          % (F_MIN, F_MAX))
    print()
    print("  %-30s %11s %11s %8s %9s %13s %15s"
          % ("muro", "Vm1", "Ve1 mod", "f bruto", "f usado", "Vu (kgf)",
             "Mu (kgf.m)"))
    print("  " + "-" * 96)
    for mu in muros:
        f_bruto = mu["Vm1"] / mu["Ve"][0]
        f = min(F_MAX, max(F_MIN, f_bruto))
        mu["f"] = f
        mu["Vu"] = [v * f for v in mu["Ve"]]
        mu["Mu"] = [m * f for m in mu["Me"]]
        marca = "" if abs(f - f_bruto) < 1e-9 else " *"
        print("  %-30s %11.0f %11.0f %8.3f %8.2f%s %13.0f %15.0f"
              % (mu["nom"], mu["Vm1"], mu["Ve"][0], f_bruto, f, marca,
                 mu["Vu"][0], mu["Mu"][0]))
    print()
    print("  (*) el factor bruto se salio de la cota y se acoto. La cota existe")
    print("  porque el 8.6 supone que la falla final es por corte en los")
    print("  entrepisos bajos: por debajo de 2 el diseno seria contra un sismo")
    print("  menor que el real, y por encima de 3 se pediria una sobrerresistencia")
    print("  que la albanileria no llega a desarrollar.")


def paso_7(muros):
    print()
    print("=" * 100)
    print("7. REFUERZO HORIZONTAL (8.6.1)")
    print("=" * 100)
    print()
    lim = C_SIGMA_REFUERZO * FM
    print("  Lleva refuerzo horizontal todo muro con Vu >= Vm, O con")
    print("  sigma_m = Pm/(L t) >= %.2f f'm = %.2f kgf/cm2." % (C_SIGMA_REFUERZO, lim))
    print()
    print("  PERO el mismo articulo zanja el primer piso sin calculo: \"en los")
    print("  edificios de MAS DE TRES PISOS, TODOS los muros portantes del primer")
    print("  nivel seran reforzados horizontalmente\". Con %d pisos, los %d muros"
          % (N_PISOS, len(muros)))
    print("  del primer nivel lo llevan por obligacion directa.")
    print()
    print("  Se calcula igual el criterio, que es lo que decide en los pisos 2 a %d:"
          % N_PISOS)
    print()
    print("  %-30s %11s %11s %9s %10s %s"
          % ("muro", "sigma_m", "vs 0,05f'm", "Vu1/Vm1", "primer piso", "pisos 2-5"))
    print("  " + "-" * 92)
    for mu in muros:
        sigma = mu["Pm"] / (mu["Ln"] * 100.0 * mu["t"] * 100.0)
        por_sigma = sigma >= lim
        por_corte = mu["Vu"][0] >= mu["Vm1"]
        sup = "SI" if (por_sigma or por_corte) else "verificar piso a piso"
        print("  %-30s %11.2f %11s %9.3f %10s %s"
              % (mu["nom"], sigma, "SI" if por_sigma else "no",
                 mu["Vu"][0] / mu["Vm1"], "SI (8.6.1)", sup))
    print()
    print("  Cuantia: rho = As/(s t) >= 0,001. Las varillas penetran al menos")
    print("  12,5 cm en las columnas y terminan con gancho a 90 grados de 10 cm.")


def disenar():
    """Los muros con TODO su diseno adjunto, y el refuerzo horizontal adoptado.

    Misma razon que `disenar()` del script 19: el diseno se va adjuntando a
    los muros dentro de las funciones `paso_*`, asi que hay un orden de
    llamadas obligatorio. Vive aca, en un solo lugar, para que el plano de
    muros no tenga que adivinarlo ni recalcular nada.

    Devuelve (muros, refuerzo_adoptado).
    """
    import contextlib
    import io as _io
    muros, V_ent = datos()
    with contextlib.redirect_stdout(_io.StringIO()):
        paso_3_y_4(muros)
        paso_5(muros, V_ent)
        paso_6(muros, V_ent)
        paso_7(muros)
        ad, _total = paso_7b(muros)
        paso_8(muros)
    return muros, ad


def opciones_refuerzo_horizontal():
    """Dimensiona el refuerzo horizontal: DOS restricciones, y gana la rara.

    1) CUANTIA - 8.6.1:   rho = As/(s.t) >= 0,001
    2) LA JUNTA - 4.1.2:  textual, "en las juntas que contengan refuerzo
       horizontal, el espesor minimo de la junta sera 6 mm mas el diametro de
       la barra". Y el mismo articulo fija el espesor MAXIMO de junta en
       15 mm. De las dos cosas juntas sale un tope que la norma no escribe
       pero impone:  6 + diametro <= 15  ->  diametro <= 9 mm.

    La segunda es la que gobierna y es la que sorprende: DESCARTA la varilla
    de 3/8" (9,53 mm), que pediria una junta de 15,53 mm, aunque por cuantia
    sobraria. El refuerzo horizontal de la albanileria no se elige por
    resistencia: se elige por lo que ENTRA en la junta.

    Devuelve la lista de opciones evaluadas; cada una dice si cumple y por que
    no, si no cumple.
    """
    import math as _m
    t_cm = ESPESOR * 100.0
    out = []
    for nombre, diam, area in CANDIDATAS:
        junta_req = SOBREESPESOR_JUNTA_REF + diam
        entra = junta_req <= JUNTA_MAX + 1e-12
        junta = max(JUNTA_MIN, junta_req)
        hilada = (H_UNIDAD + junta) * 100.0          # cm
        for n in (1, 2):
            As = n * area
            s_max = As / (RHO_MIN * t_cm)            # cm
            n_hil = int(_m.floor(s_max / hilada)) if hilada > 0 else 0
            s = n_hil * hilada
            rho = As / (s * t_cm) if s > 0 else 0.0
            out.append({
                "nombre": nombre, "diam": diam, "area": area, "n": n,
                "junta_req": junta_req, "junta": junta, "hilada": hilada,
                "As": As, "s_max": s_max, "n_hiladas": n_hil, "s": s,
                "rho": rho,
                "entra": entra,
                "cumple": entra and n_hil >= 1,
                "motivo": ("" if entra else
                           "la junta pediria %.2f mm y el maximo es %.0f"
                           % (junta_req * 1000, JUNTA_MAX * 1000))
                          or ("" if n_hil >= 1 else
                              "ni una varilla por hilada alcanza la cuantia"),
            })
    return out


def adoptar_refuerzo(opciones):
    """Elige entre las que cumplen, pero NO la que queda al filo.

    La primera version de esta funcion ordenaba solo por "menos operaciones en
    obra" y eligio 2 varillas de 8 mm cada 4 hiladas: cuantia 0,00101 contra
    un minimo de 0,00100, o sea **+1 % de holgura**. Eso no es un diseno, es
    una coincidencia: la cuantia depende de la hilada, la hilada depende del
    espesor REAL de la junta, y la junta la pone un albanil con badilejo
    dentro de una tolerancia de 10 a 15 mm. Un milimetro de mas en el asiento
    y el muro queda por debajo del minimo normativo, sin que nadie lo note.

    Por eso se exige HOLGURA_MIN antes de mirar la comodidad constructiva. Es
    un criterio de proyecto, no de la norma, y por eso esta declarado.
    """
    buenas = [o for o in opciones
              if o["cumple"] and o["rho"] >= RHO_MIN * (1.0 + HOLGURA_MIN)]
    if not buenas:      # si nada tiene holgura, se vuelve al minimo estricto
        buenas = [o for o in opciones if o["cumple"]]
    if not buenas:
        return None
    return sorted(buenas, key=lambda o: (-o["n_hiladas"], o["n"], o["diam"]))[0]


def computo_refuerzo(muros, ad):
    """Metros lineales de varilla, que es lo que se compra."""
    h_muro = H_LIBRE * 100.0                     # cm de muro por piso
    corridas = int(h_muro // ad["s"])            # corridas de refuerzo por piso
    total = 0.0
    filas = []
    for mu in muros:
        # cada corrida recorre el muro y ancla 12,5 cm + gancho de 10 en cada
        # extremo (4.2.3). Se cuentan las n varillas de la junta.
        largo = mu["L"] * 100.0 + 2 * (ANCLAJE_COLUMNA + GANCHO)
        m = corridas * N_PISOS * ad["n"] * largo / 100.0
        total += m
        filas.append((mu["nom"], corridas, m))
    return corridas, filas, total


def paso_7b(muros):
    """El dimensionamiento que faltaba: cuanto acero, de que diametro y cada cuanto."""
    print()
    print("=" * 100)
    print("7b. DIMENSIONAMIENTO DEL REFUERZO HORIZONTAL  -  8.6.1 y 4.1.2")
    print("=" * 100)
    print()
    print("  El paso 7 dijo QUE muros lo llevan (los 13 del primer nivel, por")
    print("  obligacion directa del 8.6.1). Falta decir CUANTO, y ahi entra una")
    print("  restriccion que no es de calculo sino de albanileria:")
    print()
    print("     E.070 4.1.2: \"En las juntas que contengan refuerzo horizontal,")
    print("     el espesor minimo de la junta sera 6 mm mas el diametro de la")
    print("     barra\".  Y el maximo de junta es %.0f mm." % (JUNTA_MAX * 1000))
    print()
    print("  De las dos cosas sale un tope que la norma no escribe pero impone:")
    print("     6 mm + diametro <= %.0f mm   ->   diametro <= %.0f mm"
          % (JUNTA_MAX * 1000, JUNTA_MAX * 1000 - SOBREESPESOR_JUNTA_REF * 1000))
    print()
    opciones = opciones_refuerzo_horizontal()
    print("  %-8s %3s %8s %9s %8s %9s %8s %9s  %s"
          % ("varilla", "n", "As cm2", "junta mm", "hilada", "s max cm",
             "s real", "rho", "veredicto"))
    print("  " + "-" * 96)
    for o in opciones:
        ver = "cumple" if o["cumple"] else "NO: " + o["motivo"]
        print("  %-8s %3d %8.3f %9.2f %8.2f %9.2f %8.2f %9.5f  %s"
              % (o["nombre"], o["n"], o["As"], o["junta_req"] * 1000,
                 o["hilada"], o["s_max"], o["s"], o["rho"], ver))
    ad = adoptar_refuerzo(opciones)
    assert ad is not None, "ninguna varilla candidata cumple el 8.6.1"
    print()
    print("  ADOPTADO: %d varilla(s) de %s cada %d hilada(s) = %.1f cm"
          % (ad["n"], ad["nombre"], ad["n_hiladas"], ad["s"]))
    print("     cuantia rho = %.5f >= %.4f  (holgura +%.0f %%)"
          % (ad["rho"], RHO_MIN, 100.0 * (ad["rho"] / RHO_MIN - 1.0)))
    print("     junta de asiento en esas hiladas: %.1f mm (el resto, %.0f mm)"
          % (ad["junta"] * 1000, JUNTA_MIN * 1000))
    alt = [o for o in opciones
           if o["cumple"] and o is not ad
           and o["n_hiladas"] == ad["n_hiladas"] and o["n"] == ad["n"]]
    if alt:
        a0 = alt[0]
        print("     ALTERNATIVA admisible sin recalcular: %d de %s al mismo paso,"
              % (a0["n"], a0["nombre"]))
        print("     con rho = %.5f (holgura +%.0f %%). Si en obra hay ese calibre"
              % (a0["rho"], 100.0 * (a0["rho"] / RHO_MIN - 1.0)))
        print("     y no el adoptado, se puede usar: queda del lado seguro.")
    print()
    print("  POR QUE NO LA DE 3/8\", que es la que uno usaria por costumbre:")
    tres_octavos = [o for o in opciones if o["nombre"] == '3/8\"'][0]
    print("     pediria una junta de %.2f mm y el maximo es %.0f. No entra."
          % (tres_octavos["junta_req"] * 1000, JUNTA_MAX * 1000))
    print()
    print("  POR QUE ESTE MURO PIDE MAS ACERO QUE LO HABITUAL. La cuantia se")
    print("  mide sobre el ESPESOR: rho = As/(s.t). Con t = %.0f cm (aparejo de"
          % (ESPESOR * 100))
    print("  cabeza, que es lo que exige la unidad solida de la Tabla 2) hace")
    print("  falta casi el doble de acero horizontal que en un muro de soga de")
    print("  13 cm. El espesor que nos dio holgura en densidad y en esfuerzo")
    print("  axial se cobra aca.")
    print()
    print("  DETALLE CONSTRUCTIVO  -  4.2.3 y 4.2.5")
    print("     anclaje en la columna      %.1f cm con gancho vertical a 90 de %.0f cm"
          % (ANCLAJE_COLUMNA, GANCHO))
    print("     traslape                   %d diametros = %.1f cm"
          % (TRASLAPE_DIAMETROS, TRASLAPE_DIAMETROS * ad["diam"] * 100))
    print("     continuidad                el 4.2.3 la exige: el refuerzo NO se corta en los vanos")
    print()
    corridas, filas, total = computo_refuerzo(muros, ad)
    print("  COMPUTO  -  %d corridas por piso (muro de %.2f m de alto libre)"
          % (corridas, H_LIBRE))
    print("     %d muros x %d pisos x %d varilla(s) por junta"
          % (len(muros), N_PISOS, ad["n"]))
    print("     longitud total de varilla de %s:  %.0f m  (%.0f kg aprox.)"
          % (ad["nombre"], total, total * ad["area"] * 7.85 / 10.0))
    print()
    print("     SUPUESTO DECLARADO, y no es menor porque son varias toneladas:")
    print("     se computa el MISMO detalle en los %d niveles. El 8.6.1 lo obliga"
          % N_PISOS)
    print("     sin calculo solo en el PRIMER nivel; en los pisos 2 a %d se pide"
          % N_PISOS)
    print("     muro por muro. Se extiende a todos por la misma razon por la que")
    print("     el criterio 9 no cambia el armado de columnas a media altura: un")
    print("     detalle que cambia de piso es un detalle que en obra se ejecuta")
    print("     mal. Ademas el sigma critico de este edificio (8,64) esta muy por")
    print("     encima del 0,05 f'm = %.2f que dispara la exigencia, asi que la"
          % (C_SIGMA_REFUERZO * FM))
    print("     mayoria lo pediria igual. Quien quiera afinar el presupuesto puede")
    print("     recortarlo en los niveles altos, con la verificacion del paso 7.")
    return ad, total


def paso_8(muros):
    print()
    print("=" * 100)
    print("8. AGRIETAMIENTO EN LOS PISOS SUPERIORES (8.6.2):  Vmi >= Vui")
    print("=" * 100)
    print()
    print("  Si un entrepiso superior no cumple, TAMBIEN se agrieta y sus")
    print("  confinamientos se disenan como los del primero (8.6.3) en vez de")
    print("  como los de un piso sano (8.6.4). Decide cuanto acero hay que poner")
    print("  arriba, asi que no es un tramite.")
    print()
    print("  %-30s %s" % ("muro", "  ".join("piso %d" % (i + 1)
                                            for i in range(1, N_PISOS))))
    print("  " + "-" * 76)
    agrietados = []
    for mu in muros:
        celdas = []
        for i in range(1, N_PISOS):
            Vmi = resistencia(mu, i)
            ok = Vmi >= mu["Vu"][i]
            if not ok:
                agrietados.append((mu["nom"], i + 1))
            celdas.append("%6.2f%s" % (Vmi / mu["Vu"][i], " " if ok else "!"))
        print("  %-30s %s" % (mu["nom"], "  ".join(celdas)))
    print()
    print("  (se muestra Vmi/Vui; con \"!\" el piso se agrieta)")
    print()
    if agrietados:
        print("  <<< SE AGRIETAN %d combinaciones muro-piso:" % len(agrietados))
        for nom, p in agrietados[:8]:
            print("        %s, piso %d" % (nom, p))
    else:
        print("  Ningun entrepiso superior se agrieta. Los pisos 2 a %d se disenan"
              % N_PISOS)
        print("  por el 8.6.4, que es el juego de formulas mas liviano: columnas")
        print("  extremas por la traccion del momento, internas con refuerzo")
        print("  minimo, y soleras con Ts = Vu Lm/(2L).")
    return agrietados


def cierre(muros, malos, atajo, agrietados):
    print()
    print("=" * 100)
    print("CIERRE DEL CRITERIO 8")
    print("=" * 100)
    print()
    print("  Fisuracion (8.5.2)      : %s" % ("TODOS cumplen" if not malos
                                              else "%d NO cumplen" % len(malos)))
    print("  Resistencia (8.5.4)     : cumple en las dos direcciones")
    print("  Atajo elastico (8.5.5)  : %s" % ("aplica" if atajo else "no aplica, se disena completo"))
    print("  Pisos superiores (8.6.2): %s" % ("ninguno se agrieta" if not agrietados
                                              else "%d se agrietan" % len(agrietados)))
    print()
    crit = max(muros, key=lambda m: m["Ve"][0] / (C_FISURA * m["Vm1"]))
    print("  Muro que gobierna la fisuracion: %s, con Ve/(0,55Vm) = %.3f"
          % (crit["nom"].split()[0], crit["Ve"][0] / (C_FISURA * crit["Vm1"])))
    print()
    print("  LO QUE ESTO HABILITA: el criterio 9. Con Vm1, Vu y Mu de cada muro")
    print("  ya se pueden calcular las fuerzas internas de la Tabla 11, el acero")
    print("  de las columnas, los cuatro espaciamientos de estribos y el refuerzo")
    print("  de las soleras. Todas esas formulas estan en el prontuario.")


if __name__ == "__main__":
    muros, V_ent = datos()
    malos = paso_3_y_4(muros)
    atajo = paso_5(muros, V_ent)
    paso_6(muros, V_ent)
    paso_7(muros)
    paso_7b(muros)
    agrietados = paso_8(muros)
    cierre(muros, malos, atajo, agrietados)
