# -*- coding: utf-8 -*-
"""Diagramas de fuerzas internas por muro: DFC y DMF. Criterios 5 y 6.

QUE CIERRA ESTE SCRIPT
======================
Los criterios 5 y 6 (analisis X-X y Y-Y) piden los "diagramas de fuerzas
internas". El calculo esta hecho en calculo/17_reparto_cortante.py, que tiene
el cortante y el momento de los 13 muros en los 5 entrepisos; lo que faltaba
era graficarlo. Sin los diagramas cada criterio tiene un techo de 1,00 de sus
2,00 puntos.

COMO SE CONSTRUYE CADA DIAGRAMA, Y POR QUE ASI
==============================================
El muro se comporta como un voladizo empotrado en la base, cargado con una
fuerza horizontal en cada nivel de piso (las Fi del Art. 35 de la E.030,
repartidas entre los muros segun su rigidez mas la torsion).

  DFC  -- el cortante es CONSTANTE dentro de cada entrepiso y SALTA en cada
          nivel, donde entra una fuerza nueva. Por eso el diagrama es
          ESCALONADO y no una linea inclinada: dibujarlo continuo seria
          dibujar una carga distribuida que no existe.

  DMF  -- el momento crece LINEALMENTE dentro de cada entrepiso (M = V.y,
          con V constante) y cambia de pendiente en cada nivel, donde cambia
          el cortante. Por eso es una poligonal, con el maximo en la base.

SIGNO Y SENTIDO: se grafican valores absolutos. El sismo actua en los dos
sentidos y el diseno usa la envolvente; dibujar el signo de un solo sentido
sugeriria que el otro no ocurre.

QUE SISMO SE GRAFICA: el SEVERO, que es el que sale del analisis de los
criterios 5 y 6. El control de fisuracion del 8.5.2 usa la mitad (sismo
moderado, definicion 8.1), y eso se anota en la figura para que nadie compare
peras con manzanas.
"""
import importlib.util
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import rutas as R      # noqa: E402
import cuadro as C                                             # noqa: E402
CALCULO = os.path.join(AQUI, "..", "calculo")
sys.path.insert(0, CALCULO)

from proyecto import N_PISOS, H_ENTREPISO, HN, FACTOR_MODERADO

COLOR_CRITICO = "#c0392b"
COLOR_RESTO = "#95a5a6"


def _cargar(nombre):
    ruta = os.path.join(CALCULO, nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "f", ruta)
    mod = importlib.util.module_from_spec(spec)
    import contextlib
    import io as _io
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def datos():
    """Ve y Me de cada muro por entrepiso, del criterio 5/6. Nada se recalcula."""
    import contextlib
    import io as _io
    R17 = _cargar("17_reparto_cortante.py")
    with contextlib.redirect_stdout(_io.StringIO()):
        filas, h, Fi, V, xm, ym, xr, yr = R17.contexto()
        Ktor, Kx, Ky = R17.geometria_torsional(filas, xr, yr)
        V_ent = R17.cortantes_de_entrepiso(Fi)
        rep, e = R17.repartir(filas, V_ent, xm, ym, xr, yr, Ktor, Kx, Ky)
        rep = R17.momentos(rep)
    return rep, Fi, V_ent


def escalones_dfc(Ve):
    """Puntos del diagrama escalonado: (cortante, altura).

    Ve[i] es el cortante del entrepiso i (0 = el de la base). El diagrama se
    recorre de la base al tope, y en cada nivel el valor SALTA.
    """
    xs, ys = [], []
    for i in range(N_PISOS):
        y0 = i * H_ENTREPISO
        y1 = (i + 1) * H_ENTREPISO
        xs += [Ve[i], Ve[i]]
        ys += [y0, y1]
        if i + 1 < N_PISOS:          # el salto vertical en el nivel
            xs.append(Ve[i + 1])
            ys.append(y1)
    return xs, ys


def poligonal_dmf(Ve):
    """Momento acumulado: poligonal con quiebre en cada nivel.

    M en la cota y, dentro del entrepiso i, es el momento del nivel superior
    mas Ve[i] por lo que falta. Se construye de arriba hacia abajo.
    """
    ys = [N_PISOS * H_ENTREPISO]
    ms = [0.0]
    m = 0.0
    for i in range(N_PISOS - 1, -1, -1):
        m += Ve[i] * H_ENTREPISO
        ys.append(i * H_ENTREPISO)
        ms.append(m)
    return ms, ys


def figura(rep, Fi, V_ent, dire, salida):
    muros = [(n, r) for n, r in rep.items() if r["dir"] == dire]
    muros.sort(key=lambda kv: -kv[1]["V"][0][2])
    critico, r_crit = muros[0]

    # TRES PANELES APILADOS, no en fila: tres sobre 13,5 pulgadas dan 4,5
    # cada uno; sobre la hoja darian 2,1, que no alcanza para un diagrama
    # con sus cotas. Apilados, cada uno se queda con el ancho entero.
    fig, ax = plt.subplots(3, 1, figsize=(C.ANCHO_PAGINA, 8.20))
    fig.suptitle(u"Diagramas de fuerzas internas  ·  dirección "
                 u"%s-%s  ·  sismo SEVERO" % (dire, dire),
                 fontsize=11.5, fontweight="bold", wrap=True)

    # --- panel 1: fuerzas de piso y cortante de entrepiso
    niveles = [(i + 1) * H_ENTREPISO for i in range(N_PISOS)]
    ax[0].barh(niveles, [f / 1000.0 for f in Fi], height=0.35,
               color="#2980b9", label="Fi de piso")
    xs, ys = escalones_dfc([v / 1000.0 for v in V_ent])
    ax[0].plot(xs, ys, color="#c0392b", lw=2.0, label="V de entrepiso")
    ax[0].set_title("Fuerzas de piso y cortante del EDIFICIO")
    ax[0].set_xlabel("tonf")
    ax[0].set_ylabel("altura (m)")
    ax[0].legend(fontsize=8, loc="upper right")

    # --- panel 2: DFC por muro
    for n, r in muros:
        Ve = [v[2] / 1000.0 for v in r["V"]]
        xs, ys = escalones_dfc(Ve)
        es = (n == critico)
        ax[1].plot(xs, ys, lw=2.2 if es else 1.0,
                   color=COLOR_CRITICO if es else COLOR_RESTO,
                   label=n.split()[0] if es else None, zorder=3 if es else 2)
    ax[1].set_title("DFC  ·  cortante por muro")
    ax[1].set_xlabel("Ve (tonf)")
    ax[1].legend(fontsize=9)

    # --- panel 3: DMF por muro
    for n, r in muros:
        Ve = [v[2] / 1000.0 for v in r["V"]]
        ms, ys = poligonal_dmf(Ve)
        es = (n == critico)
        ax[2].plot(ms, ys, lw=2.2 if es else 1.0,
                   color=COLOR_CRITICO if es else COLOR_RESTO,
                   label=n.split()[0] if es else None, zorder=3 if es else 2)
    ax[2].set_title("DMF  ·  momento por muro")
    ax[2].set_xlabel(u"Me (tonf\u00b7m)")
    ax[2].legend(fontsize=9)

    for a in ax:
        # el rotulo del ULTIMO tick de un panel desbordaba hacia el panel
        # vecino y se pisaba con su "0" (medido por el auditor de textos, no
        # estimado). Se poda el tick de arriba y se limita la cantidad.
        a.xaxis.set_major_locator(MaxNLocator(nbins=4, prune="upper"))
        a.set_ylim(0, HN + 0.4)
        a.set_yticks([i * H_ENTREPISO for i in range(N_PISOS + 1)])
        a.grid(alpha=0.3, linestyle=":")
        a.axhline(0, color="k", lw=1.2)
        a.set_xlim(left=0)

    pie = ("El DFC es ESCALONADO porque el cortante es constante en cada entrepiso y salta en cada nivel; "
           "el DMF quiebra donde cambia el cortante.\n"
           u"En rojo el muro m\u00e1s cargado (%s): Ve = %.1f tonf y Me = %.1f tonf\u00b7m en la base. "
           u"Para el control de fisuraci\u00f3n del 8.5.2 estos valores se dividen por %.0f (sismo moderado, E.070 8.1)."
           % (critico.split()[0], r_crit["V"][0][2] / 1000.0,
              r_crit["M"][0] / 1000.0, FACTOR_MODERADO))
    fig.tight_layout(rect=[0, 0.105, 1, 0.965])
    _axp = fig.add_axes((0, 0, 1, 1), frame_on=False)
    _axp.set_axis_off()
    _yp = 0.092
    for _par in pie.split(chr(10)):
        for _ln in C.envolver(_axp, _par, 8.0, 0.92):
            fig.text(0.5, _yp, _ln, ha="center", fontsize=8.0,
                     style="italic", va="top")
            _yp -= 0.0148
    C.guardar(fig, salida)
    return critico, r_crit


def control(rep, V_ent):
    """Que los diagramas representen lo que el analisis calculo.

    Dos comprobaciones que revientan:
      1. la suma de los cortantes de los muros de una direccion, en el primer
         entrepiso, no puede ser MENOR que el cortante del edificio: eso
         significaria que el reparto perdio fuerza por el camino.
      2. el momento de la base de cada muro tiene que coincidir con el que el
         script 17 calculo integrando, no con una integracion propia de esta
         figura (si no, la figura estaria dibujando otro calculo).
    """
    for dire in ("X", "Y"):
        s = sum(r["V"][0][2] for r in rep.values() if r["dir"] == dire)
        assert s >= V_ent[0] * 0.999, (
            "en %s los muros suman %.0f y el entrepiso pide %.0f" % (dire, s, V_ent[0]))
    peor = 0.0
    for n, r in rep.items():
        Ve = [v[2] for v in r["V"]]
        m_fig = poligonal_dmf(Ve)[0][-1]      # el ultimo punto es la base
        m_17 = r["M"][0]
        peor = max(peor, abs(m_fig - m_17) / m_17)
    assert peor < 1e-9, (
        "el momento de la figura difiere del del script 17 en %.2e" % peor)
    return peor


def main():
    rep, Fi, V_ent = datos()
    peor = control(rep, V_ent)
    print("=" * 78)
    print("DIAGRAMAS DE FUERZAS INTERNAS  -  criterios 5 y 6")
    print("=" * 78)
    print("  control: el momento de base de la figura coincide con el del")
    print("           script 17 (diferencia maxima %.1e)" % peor)
    print()
    for dire in ("X", "Y"):
        salida = os.path.join(R.INFORME,
                              "DIAGRAMAS-%s%s.png" % (dire, dire))
        crit, r = figura(rep, Fi, V_ent, dire, salida)
        print("  %s-%s  ->  %-22s  muro mas cargado %s"
              % (dire, dire, os.path.basename(salida), crit.split()[0]))
        print("         Ve base %9.1f tonf   ·   Me base %9.1f tonf.m"
              % (r["V"][0][2] / 1000.0, r["M"][0] / 1000.0))
        print("         %.1f KB" % (os.path.getsize(salida) / 1024.0))


if __name__ == "__main__":
    main()
