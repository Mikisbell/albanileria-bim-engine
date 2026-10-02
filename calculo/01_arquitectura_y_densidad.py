# -*- coding: utf-8 -*-
"""Planteamiento arquitectónico y verificación de densidad de muros

El orden importa: la densidad minima que exige la E.070 (7.1.2b) DECIDE la
planta, no al reves. Si la verificacion falla, se cambian los MUROS en
`proyecto.py` y se vuelve a correr. Nada de dibujar primero y calcular despues.

Toda constante viene de `proyecto.py`: este script no declara geometria propia.
"""
from proyecto import (Z, U, S, R, N_PISOS, H_ENTREPISO, HN, FRENTE, FONDO,
                      AREA_LOTE, AREA_POZO, AREA_PLANTA, POZO_ANCHO, POZO_LARGO,
                      MUROS, LONG_MINIMA, factor_C, cortante_unitario, machones, SEPARACION_VANO_COLUMNA)


def densidad_requerida():
    """E.070 (7.1.2b): Area de corte / Area de planta >= Z*U*S*N/56."""
    return Z * U * S * N_PISOS / 56.0


def tabla_densidad(dire):
    """Filas (nom, L, vanos, L_neta, Ac, machones, cuenta) de esa direccion.

    Estaba dentro de `verificar()`, tejida con los `print`, asi que la unica
    forma de reusarla era volver a escribir el bucle. La lamina-cuadro de la
    densidad la necesita con los numeros, no con el texto ya formateado, y
    dos copias del mismo bucle se separan sin avisar.
    """
    out = []
    for nom, d, L, t_, vanos in MUROS:
        if d != dire:
            continue
        ms = [b - a for a, b in machones(nom, d, L, vanos)]
        buenos = [m for m in ms if m >= LONG_MINIMA - 1e-9]
        out.append({"nom": nom, "L": L, "vanos": sum(vanos),
                    "neta": sum(ms), "t": t_,
                    "Ac": sum(buenos) * t_, "machones": ms,
                    "descartados": [m for m in ms
                                    if m < LONG_MINIMA - 1e-9]})
    return out


def verificar():
    req = densidad_requerida()
    area_req = req * AREA_PLANTA
    print("=" * 72)
    print("PLANTEAMIENTO ARQUITECTONICO Y DENSIDAD DE MUROS")
    print("=" * 72)
    print("  Lote medianero %.2f x %.2f m = %.2f m2" % (FRENTE, FONDO, AREA_LOTE))
    print("  Pozo de luz %.2f x %.2f = %.2f m2" % (POZO_ANCHO, POZO_LARGO, AREA_POZO))
    print("  Area de planta tipica (techada) = %.2f m2   %s"
          % (AREA_PLANTA, "CUMPLE >= 200" if AREA_PLANTA >= 200 else "NO CUMPLE <<<"))   # no-ssot: 200 m2 de la consigna, no es la s/c
    print("  Pisos: %d   Altura de entrepiso: %.2f m   hn = %.2f m"
          % (N_PISOS, H_ENTREPISO, HN))
    print()
    print("  E.070 (7.1.2b): Z*U*S*N/56 = %.2f*%.2f*%.2f*%d/56 = %.5f"
          % (Z, U, S, N_PISOS, req))
    print("  Area de corte requerida por direccion = %.3f m2" % area_req)
    print()

    print("  Los VANOS se descuentan. E.070 6.4: un muro solo es contribuyente a")
    print("  la resistencia horizontal si tiene 'una longitud mayor o igual a")
    print("  1,20 m'. Una puerta parte el muro en dos, y cada trozo debe llegar a")
    print("  ese minimo por su cuenta. Contar la longitud bruta infla la densidad")
    print("  con muro que no esta construido.")
    print()

    ok = True
    for d in ("X", "Y"):
        print("  --- DIRECCION %s ---" % d)
        print("     %-30s %6s %6s %6s %8s  %s"
              % ("muro", "bruta", "vanos", "neta", "corte m2", "trozos"))
        suma = 0.0
        for nom, dire, L, t, vanos in MUROS:
            if dire != d:
                continue
            # AUDITORIA. Hasta aca este bucle comparaba el trozo MEDIO
            # (neta/n_trozos) contra 1,20 m, y el propio script declaraba
            # abajo que habia que "volver aca con las posiciones reales".
            # Las posiciones reales existen desde que proyecto.py tiene
            # vanos_ubicados()/machones(): la deuda estaba escrita y sin
            # saldar. Un promedio APRUEBA un muro con machones de 0,80 y
            # 3,00 m, y el 6.4 exige que CADA UNO llegue a 1,20.
            pass
        for f in tabla_densidad(d):
            ms, corto, ap = f["machones"], f["descartados"], f["Ac"]
            suma += ap
            print("     %-30s %6.2f %6.2f %6.2f %8.3f  %d de %s %s"
                  % (f["nom"], f["L"], f["vanos"], f["neta"], ap, len(ms),
                     "/".join("%.2f" % m for m in ms),
                     "" if not corto else "<<< %d trozo(s) < 1,20 NO cuentan" % len(corto)))
        print("     %-30s %27.3f m2" % ("suma", suma))
        if suma < area_req:
            ok = False
        print("     requerido %.3f m2  ->  %s  (holgura %+.1f %%)"
              % (area_req, "CUMPLE" if suma >= area_req else "NO CUMPLE",
                 (suma / area_req - 1) * 100))
        print()
    print("  SOBRE LA COLUMNA 'trozos': son los machones REALES, tomados de las")
    print("  posiciones de vano de proyecto.py, y cada uno se mide por separado")
    print("  contra el 1,20 m del 6.4. No es un promedio.")
    print()
    print("  Se descuenta ademas el trozo de %.2f m que queda entre el EXTREMO del" % SEPARACION_VANO_COLUMNA)
    print("  muro y la cara del primer vano: eso es media columna de concreto, no")
    # los dos numeros SE MIDEN, no se escriben: un literal a mano aqui se
    # queda viejo en silencio en cuanto cambie un vano.
    _neta = sum(L - sum(v) for _n, _d, L, _t, v in MUROS)
    _mach = sum(sum(b - a_ for a_, b in machones(n, d, L, v))
                for n, d, L, _t, v in MUROS)
    print("  albanileria. Son %.2f m en total sobre %.2f m de muraje (%.1f %%), y el"
          % (_neta - _mach, _neta, 100 * (_neta - _mach) / _neta))
    print("  descuento va del lado SEGURO: el 8.5.3 permitiria contarlo.")
    return ok


def demanda():
    C, T = factor_C()
    print("=" * 72)
    print("DEMANDA SISMICA (E.030-2026, analisis estatico)")
    print("=" * 72)
    print("  T = hn/CT = %.3f s   ->  C = %.2f" % (T, C))
    print("  V/P severo   = %.4f  (%.1f %% del peso)"
          % (cortante_unitario(True), cortante_unitario(True) * 100))
    print("  V/P moderado = %.4f  (%.1f %% del peso)"
          % (cortante_unitario(False), cortante_unitario(False) * 100))


if __name__ == "__main__":
    ok = verificar()
    demanda()
    print()
    print("RESULTADO:", "planta VIABLE" if ok else "planta INVIABLE, corregir MUROS en proyecto.py")
