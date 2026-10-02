# -*- coding: utf-8 -*-
"""La altura contributiva del muro: el criterio que la docente enseña.

DE DONDE SALE
=============
No de la norma. La E.030 y la E.070 NO fijan como repartir el peso de un muro
entre los niveles -- se verifico buscando en ambas y no hay articulo. Sale de
la Clase 05 (semana 5, Unidad III, ANALISIS SISMICO), que lo dice asi:

    "Para calcular el peso de los muros se considera que su ALTURA
     CONTRIBUTIVA ES LA MITAD DE LAS ALTURAS DE LOS MUROS QUE CONCURREN
     VERTICALMENTE en cada piso o techo. Tambien deben considerarse el peso de
     los alfeizares, con la carga que transmite a cada piso."

Es el criterio estandar de la practica peruana, y es FISICAMENTE correcto: la
mitad inferior del muro del primer piso descarga directamente en la
cimentacion y no forma parte de la masa que oscila.

QUE HACE NUESTRO MODELO
=======================
Asigna un muro COMPLETO a cada uno de los cinco niveles. Eso cuenta 5H de muro
cuando la masa sismica real es 4,5H: sobra media altura, la que baja a la
cimentacion. Es CONSERVADOR -- mas peso es mas fuerza sismica -- pero no es lo
que la Clase 05 ensena.

POR QUE SE CONTRASTA EN VEZ DE CAMBIARLO
========================================
Porque la norma no obliga a ninguno de los dos y el nuestro va del lado
seguro. Adoptar el criterio de la docente BAJARIA el cortante y aflojaria
todas las verificaciones; conservarlo sin declararlo seria peor, porque el
metrado no coincidiria con el que ella ensena y nadie sabria por que.

Se mide, se declara y se verifica que el diseno cumple con los dos. Es el
mismo trato que recibieron la continuidad de la losa (script 26) y la lectura
del ala del 8.3.6 (script 29).
"""
import contextlib
import importlib.util
import io as _io
import os

from proyecto import MUROS, N_PISOS, H_LIBRE, Z, U, S, PARAPETO

AQUI = os.path.dirname(os.path.abspath(__file__))


def _cargar(nombre):
    ruta = os.path.join(AQUI, nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "h", ruta)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


R15 = _cargar("15_centro_masa_y_rigidez.py")
C_MESETA = 2.50       # no-ssot: el 34.1 lo impone cuando T < Tp, que es el caso
R_COEF = 3.00         # no-ssot: R0 = 3 de la Tabla 10, con Ia = Ip = 1


def peso_muros_un_piso():
    """kgf de TODOS los muros del proyecto, en la altura de UN entrepiso."""
    return sum(R15.peso_muro_por_piso(n, d, L, t, v) for n, d, L, t, v in MUROS)


def reparto_por_nivel():
    """Altura de muro que cada nivel recibe, con los dos criterios.

    Nuestro modelo da H a los cinco. El de la Clase 05 da media altura del muro
    de abajo mas media del de arriba: los niveles intermedios reciben H igual,
    pero la AZOTEA solo recibe H/2 -- no hay muro encima -- y la otra mitad del
    piso 1 baja a la cimentacion.
    """
    filas = []
    for k in range(1, N_PISOS + 1):
        nuestro = 1.0
        abajo = 0.5                       # media altura del muro de ESTE piso
        arriba = 0.5 if k < N_PISOS else 0.0   # media del de encima, si existe
        filas.append((k, nuestro, abajo + arriba))
    return filas


def informe():
    w = peso_muros_un_piso()
    filas = reparto_por_nivel()

    print("=" * 88)
    print("ALTURA CONTRIBUTIVA DEL MURO  -  el criterio de la Clase 05")
    print("=" * 88)
    print("  La E.030 y la E.070 NO fijan como repartir el peso de un muro")
    print("  entre niveles: se busco en ambas y no hay articulo. El criterio")
    print("  es de la Clase 05, y es el estandar de la practica.")
    print()
    print("  peso de todos los muros en UN entrepiso = %s kgf"
          % "{:,.0f}".format(w).replace(",", " "))
    print()
    print("  %-8s %16s %18s %14s" % ("nivel", "nuestro (x H)", "Clase 05 (x H)", "delta kgf"))
    print("  " + "-" * 62)
    tot_n = tot_d = 0.0
    for k, nuestro, docente in filas:
        tot_n += nuestro
        tot_d += docente
        print("  %-8d %16.1f %18.1f %14s"
              % (k, nuestro, docente,
                 "{:,.0f}".format((nuestro - docente) * w).replace(",", " ")))
    print("  " + "-" * 62)
    print("  %-8s %16.1f %18.1f %14s"
          % ("TOTAL", tot_n, tot_d,
             "{:,.0f}".format((tot_n - tot_d) * w).replace(",", " ")))
    print()
    print("  La media altura que sobra es la del piso 1: baja DIRECTO a la")
    print("  cimentacion y no participa de la masa que oscila.")
    print()

    # el peso sismico completo con cada criterio
    with contextlib.redirect_stdout(_io.StringIO()):
        p_nuestro = R15.peso_sismico()
    exceso = (tot_n - tot_d) * w
    p_docente = p_nuestro - exceso
    zucs = Z * U * C_MESETA * S / R_COEF

    print("  %-34s %14s %14s" % ("", "nuestro", "Clase 05"))
    print("  " + "-" * 64)
    print("  %-34s %14s %14s"
          % ("peso sismico P (kgf)",
             "{:,.0f}".format(p_nuestro).replace(",", " "),
             "{:,.0f}".format(p_docente).replace(",", " ")))
    print("  %-34s %14s %14s"
          % ("cortante basal V = ZUCS/R . P",
             "{:,.0f}".format(zucs * p_nuestro).replace(",", " "),
             "{:,.0f}".format(zucs * p_docente).replace(",", " ")))
    print("  %-34s %13.1f %% %13.1f %%"
          % ("diferencia", 0.0, 100 * (p_docente / p_nuestro - 1)))
    print()
    print("  NUESTRO MODELO ES EL CONSERVADOR: pide %.1f %% mas de cortante."
          % (100 * (p_nuestro / p_docente - 1)))
    print("  Por eso se CONSERVA, y por eso se DECLARA: un metrado que no")
    print("  coincide con el que la clase ensena y no dice por que, parece un")
    print("  error aunque vaya del lado seguro.")
    print()
    print("  LO QUE NO CAMBIA: el esfuerzo axial. Es carga de GRAVEDAD, y ahi")
    print("  el muro del primer piso carga los cinco pisos completos")
    # EL SIGMA CRITICO SE LEE DEL 11, NO SE ESCRIBE. Estaba clavado a mano
    # como "9,41 kgf/cm2 en MX-7" y sobrevivio a dos cambios de geometria: el
    # 2026-09-21 el valor real era 8,99 y este print seguia anunciando 9,41.
    # Un literal dentro de un print es una cifra vencida que ningun auditor
    # de documentos mira, porque no esta en el informe: esta en el script que
    # lo alimenta.
    import importlib.util as _ilu
    _ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "11_metrado_muros.py")
    _spec = _ilu.spec_from_file_location("_m11c", _ruta)
    _m11 = _ilu.module_from_spec(_spec)
    import contextlib as _ctx
    import io as _io2
    with _ctx.redirect_stdout(_io2.StringIO()):
        _spec.loader.exec_module(_m11)
    _peor = max(_m11.metrar(), key=lambda f: f["sigma"])
    print("  cualquiera sea el criterio de masa sismica. El sigma critico de")
    print("  %.2f kgf/cm2 en %s se mantiene intacto."
          % (_peor["sigma"], _peor["nom"].split()[0]))
    return p_nuestro, p_docente, exceso


def control(p_nuestro, p_docente, exceso):
    w = peso_muros_un_piso()
    # la diferencia tiene que ser EXACTAMENTE media altura de muro
    assert abs(exceso - 0.5 * w) < 1.0, (
        "el exceso deberia ser media altura de muro (%.0f), y da %.0f"
        % (0.5 * w, exceso))
    assert p_docente < p_nuestro, "el criterio de la clase deberia dar MENOS peso"
    # y el alfeizar, que la misma cita menciona, ya tiene que estar contado
    from proyecto import (MUROS_CON_VENTANA, altura_de_vano,   # noqa: F401
                          ALTURA_VENTANA, MUROS, vanos_ubicados,
                          tipo_de_vano)
    # el descuento de vano en fachada tiene que usar la altura de VENTANA en
    # las ventanas -- para que el alfeizar que la cita menciona quede
    # contado -- y la de PUERTA en la puerta de ingreso, que no lleva
    # alfeizar. Se comprueba vano por vano, no por muro.
    fila = [m for m in MUROS if m[0].startswith("MX-1")][0]
    nom, dire, L, _t, vanos = fila
    tipos = [tipo_de_vano(nom, x0)
             for x0, _a in vanos_ubicados(nom, dire, L, vanos)]
    assert tipos.count("ventana") == 3 and tipos.count("puerta") == 1, (
        "la fachada frontal debe llevar 3 ventanas y la puerta de ingreso, "
        "y lleva %s" % tipos)
    for x0, _a in vanos_ubicados(nom, dire, L, vanos):
        if tipo_de_vano(nom, x0) == "ventana":
            assert abs(altura_de_vano(nom, x0) - ALTURA_VENTANA) < 1e-12, (
                "la cita de la Clase 05 tambien pide contar los alfeizares, "
                "y el descuento no usa la altura de VENTANA")
    print("  [ok] el exceso es exactamente media altura de muro")
    print("  [ok] los alfeizares que la misma cita exige ya estan contados")
    return True


if __name__ == "__main__":
    pn, pd, ex = informe()
    print()
    print("=" * 88)
    print("CONTROL")
    print("=" * 88)
    control(pn, pd, ex)
