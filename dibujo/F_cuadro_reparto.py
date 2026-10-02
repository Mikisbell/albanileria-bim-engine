# -*- coding: utf-8 -*-
"""Lámina-cuadro: reparto del cortante por muro, traslación y torsión.

POR QUE ESTA LAMINA
===================
Es **lo que el docente pide literalmente** al cerrar la Clase 05, en la
diapositiva «APLICACIÓN»:

    «Para un edificio: a) Presentar en un cuadro las fuerzas cortantes
     totales en los muros portantes…»

y lo desarrolla en tres láminas: fuerza cortante total, la parte por
traslación (directa) y la parte por torsión (indirecta), con las columnas
`Ki`, `Ri`, `Ki·Ri`, `Ki·Ri²`, el factor y el cortante de cada muro.

Este cuadro es el mismo, con los trece muros de este proyecto y el primer
entrepiso, que es el que gobierna el diseño.

UNA DIFERENCIA DE METODO, DECLARADA
===================================
El ejemplo de clase calcula DOS momentos torsores —`Mt1` con la
excentricidad propia más la accidental y `Mt2` con la propia menos la
accidental— y lleva las dos columnas hasta el final. Este proyecto toma
directamente el **sentido de giro que perjudica a cada muro**, con valor
absoluto, que es lo que el Art. 37.b obliga a considerar: cada muro se
diseña para el peor de los dos sentidos, no para el promedio ni para uno
elegido de antemano. Por eso la columna del cortante por torsión aparece
una sola vez y siempre suma, nunca resta.
"""
import contextlib
import importlib.util
import io as _io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))
sys.path.insert(0, AQUI)

import rutas as R                                              # noqa: E402
import cuadro as C                                             # noqa: E402
import paleta as PAL                                           # noqa: E402
from matplotlib.patches import Rectangle                       # noqa: E402


def datos():
    ruta = os.path.join(AQUI, "..", "calculo", "17_reparto_cortante.py")
    spec = importlib.util.spec_from_file_location("_m17", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def croquis_de_planta(rep, xr, yr, e):
    u"""El mecanismo que la tabla no puede mostrar: que es Ri y que hace el giro.

    POR QUE. Una tabla ensena el CALCULO y no el fenomeno. El lector que ve
    la columna "Ri (m)" con valores de -10,76 a +10,24 tiene que imaginarse
    la planta para entenderla, y sin esa imagen la columna es una lista de
    numeros con signo. San Bartolome resuelve eso dibujando los parametros
    al lado de la tabla --su Fig. 8.24 ilustra justamente los de la Tabla
    11-- y es el recurso que a estas laminas les faltaba.

    LO QUE EL CROQUIS AGREGA y el texto no puede: que el SIGNO de Ri es de
    que lado del centro de rigidez esta el muro, y que por eso el giro suma
    cortante a unos y se lo quita a otros -- aunque la norma obligue a tomar
    el sentido desfavorable para cada uno, que es la razon de que la columna
    de torsion no sume cero.
    """
    import proyecto as P

    def dibujar(ax, x0, y0, ancho, alto):
        B, L = P.FRENTE, P.FONDO
        esc = min(ancho * 0.30 / B, alto * 0.94 / L)
        ox, oy = x0 + ancho * 0.06, y0 + alto * 0.06
        X = lambda u: ox + u * esc
        Y = lambda v: oy + v * esc
        # la planta
        ax.add_patch(Rectangle((X(0), Y(0)), B * esc, L * esc, fc="#f7f9fc",
                               ec="#c5d5e6", lw=0.9, zorder=2))
        # los muros Y (verticales en planta) y los X (horizontales)
        ejes_x, _r = P.ejes_x_rotulados()
        for yy in P.EJES_MX:
            ax.plot([X(0), X(B)], [Y(yy)] * 2, color=PAL.MURO, lw=2.0,
                    solid_capstyle="butt", zorder=3)
        # LOS MUROS Y VAN TODOS. Dibujar solo las medianeras dejaba la
        # planta como un rectangulo con rayas y el lector no reconocia su
        # edificio; los cuatro interiores son los que dan la escala.
        for xx in ejes_x:
            ancho_l = 2.8 if xx in (ejes_x[0], ejes_x[-1]) else 1.5
            ax.plot([X(xx)] * 2, [Y(0), Y(L)], color=PAL.MURO, lw=ancho_l,
                    solid_capstyle="butt", zorder=3)
        # el CENTRO DE RIGIDEZ, que es el origen de todos los Ri
        ax.plot([X(xr)], [Y(yr)], "o", color=PAL.ALERTA, ms=7,
                mec="#ffffff", mew=1.2, zorder=6)
        ax.text(X(xr) + ancho * 0.012, Y(yr), "CR", fontsize=8.0,
                color=PAL.ALERTA, fontweight="bold", va="center", zorder=6)
        # el giro
        # EL GIRO, con su rotulo LEJOS del CR: puesto al lado se montaba
        # sobre la etiqueta "CR" y sobre la propia flecha.
        rg = min(B, L) * esc * 0.17
        ax.annotate("", xy=(X(xr) + rg, Y(yr) + rg * 0.7),
                    xytext=(X(xr) + rg, Y(yr) - rg * 0.7),
                    arrowprops=dict(arrowstyle="-|>", color=PAL.GOBIERNA,
                                    lw=1.5, connectionstyle="arc3,rad=0.55"),
                    zorder=6)
        ax.text(X(B) + ancho * 0.008, Y(yr), "giro por\ne = %s m"
                % _coma(e["X"], 3), fontsize=7.6, color=PAL.GOBIERNA,
                fontweight="bold", va="center", ha="left", zorder=6)
        # Ri acotado en DOS muros X: el mas lejano de cada lado, que son los
        # que el giro castiga y alivia
        xs = sorted(((r["d"], n) for n, r in rep.items() if r["dir"] == "X"),
                    key=lambda z: z[0])
        for d, nom in (xs[0], xs[-1]):
            yy = yr + d
            col = PAL.BIEN if d > 0 else PAL.ALERTA
            ax.annotate("", xy=(X(B * 0.50), Y(yy)), xytext=(X(B * 0.50), Y(yr)),
                        arrowprops=dict(arrowstyle="<->", color=col, lw=1.1),
                        zorder=5)
            ax.text(X(B * 0.54), Y((yy + yr) / 2.0),
                    "%s\nRi = %s m" % (nom, _coma(d)), fontsize=7.2,
                    color=col, fontweight="bold", va="center", zorder=6)
        tx = x0 + ancho * 0.40
        C.bloque_de_texto(
            ax, tx, y0 + alto * 0.94, (x0 + ancho) - tx - 0.01,
            u"Ri es la distancia de cada muro al CENTRO DE RIGIDEZ, con "
            u"signo:",
            [u"Los muros de un lado del CR giran en un sentido y los del "
             u"otro en el contrario; por eso Ri cambia de signo, y el "
             u"producto Ki·Ri de la tabla también.",
             u"La norma manda tomar para CADA muro el sentido que lo "
             u"perjudica (valor absoluto), y esa es la razón de que la "
             u"columna de torsión NO sume cero."])
    return dibujar


def _coma(x, d=2):
    return (("%%.%df" % d) % x).replace(".", ",")


def main():
    m = datos()
    with contextlib.redirect_stdout(_io.StringIO()):
        filas, h, Fi, V, xm, ym, xr, yr = m.contexto()
        V_ent = m.cortantes_de_entrepiso(Fi)
        Ktor, Kx, Ky = m.geometria_torsional(filas, xr, yr)
        rep, e = m.repartir(filas, V_ent, xm, ym, xr, yr, Ktor, Kx, Ky)

    K_dir = {"X": Kx, "Y": Ky}
    bloques, sumas = [], {}
    for dire in ("X", "Y"):
        fs, tot_d, tot_t = [], 0.0, 0.0
        colores = []
        muros = [(n, r) for n, r in rep.items() if r["dir"] == dire]
        # SI EMPATAN, GOBIERNAN LAS DOS. Tomar el primero de la lista
        # ordenada marcaba solo uno de los dos muros medianeros, que dan
        # exactamente el mismo cortante, y obligaba al lector a preguntarse
        # por que ese y no el otro. Es el mismo defecto que ya aparecio en
        # la lamina E-02 con el control de fisuracion.
        vmax = max(r["V"][0][2] for _n, r in muros)
        peores = set(n for n, r in muros
                     if abs(r["V"][0][2] - vmax) < 1e-6)
        for n, r in sorted(muros, key=lambda kv: kv[0]):
            directo, tor, total = r["V"][0]
            tot_d += directo
            tot_t += tor
            fs.append([
                n.split()[0],
                C.miles(r["K"]),
                C.coma(r["d"]),
                C.coma(r["K"] / K_dir[dire], 4),
                C.miles(directo),
                C.miles(tor),
                C.miles(total),
            ])
            colores.append("#fff4e5" if n in peores else None)
        sumas[dire] = (tot_d, tot_t, peores, vmax)
        bloques.append({
            "titulo": "Dirección %s-%s  ·  primer entrepiso  ·  "
                      "e = %s m" % (dire, dire, C.coma(e[dire], 3)),
            # sin el producto Ki x Ri: sus dos factores estan al lado
            "cols": ["Muro", "Ki\n(kgf/cm)", "Ri\n(m)",
                     "Ki/ΣKi", "V directo\n(kgf)", "V torsión\n(kgf)",
                     "Ve total\n(kgf)"],
            "filas": fs,
            "suma": ["Σ", C.miles(K_dir[dire]), "", "1,0000",
                     C.miles(tot_d), C.miles(tot_t),
                     C.miles(tot_d + tot_t)],
            "colores_fila": colores,
        })

    comprobacion = [
        "Traslación:  V directo = Ve · Ki/ΣKi   →   la suma de la columna "
        "reproduce el cortante del entrepiso, %s kgf" % C.miles(V_ent[0]),
        "Torsión:  V torsión = |Ve · e · Ki · Ri / Ktor|   con   Ktor = "
        "Σ(Ki·Ri²) = %s kgf·cm/rad" % C.miles(Ktor),
    ]

    nota = (
        "Ri es la distancia del muro al CENTRO DE RIGIDEZ, con signo: los "
        "muros de un lado giran en un sentido y los del otro en el "
        "contrario. La excentricidad e suma la propia (|CM − CR|) y la "
        "accidental del Art. 37 (0,05 de la dimensión perpendicular).\n"
        "La torsión NO reparte: sólo AÑADE. Se toma el sentido de giro que "
        "perjudica a cada muro —por eso el valor absoluto—, de modo que la "
        "suma de la columna de torsión no da cero como daría en un reparto "
        "algebraico. La fila en crema es el muro más cargado de cada "
        "dirección, que es el que gobierna el diseño del Capítulo 8.")

    # UNA LAMINA POR DIRECCION. Ver el porque arriba.
    for k_dir, dire in enumerate(("X", "Y")):
      bloque = [b for b in bloques if ("%s-%s" % (dire, dire)) in b["titulo"]]
      assert len(bloque) == 1, (
          "no se encontro el bloque de la direccion %s en %s"
          % (dire, [b["titulo"] for b in bloques]))
      out = os.path.join(R.INFORME, "CUADRO-REPARTO-CORTANTE-%s.png" % dire)
      C.lamina(
          paso="Paso 4 — Reparto del cortante en %s: traslación y torsión" % dire,
          titulo="Cortante que toma cada muro de la dirección %s-%s en el "
                 "primer entrepiso, separado en la parte directa y la parte "
                 "por giro" % (dire, dire),
          formula=r"$V_{directo} = V_e\,\dfrac{K_i}{\sum K_i}$"
                  r"$\qquad\qquad$"
                  r"$V_{torsion} = \left|\,V_e\,e\,"
                  r"\dfrac{K_i\,R_i}{K_{tor}}\right|$",
          acapite="E.030  Art. 37",
          bloques=bloque,
          comprobacion=comprobacion,
          nota=nota,
          salida=out,
          croquis=croquis_de_planta(rep, xr, yr, e),
          alto_croquis=2.6,
      )
    print()
    control(m, rep, V_ent, sumas, K_dir)


def control(m, rep, V_ent, sumas, K_dir):
    """Lo que la lámina afirma sale del script 17, no del dibujo."""
    for dire in ("X", "Y"):
        tot_d, tot_t, peores, vmax = sumas[dire]
        # EL CONJUNTO marcado tiene que ser el conjunto de maximos, no uno
        # cualquiera de ellos: se compara conjunto contra conjunto
        reales = set(n for n, r in rep.items()
                     if r["dir"] == dire
                     and abs(r["V"][0][2] - vmax) < 1e-6)
        assert peores == reales, (
            "en %s se marcan %s y los maximos son %s"
            % (dire, sorted(peores), sorted(reales)))
        # 1. LA AFIRMACION del pie: la parte DIRECTA reproduce el cortante
        #    del entrepiso. Si no cerrara, el reparto perdió fuerza.
        assert abs(tot_d - V_ent[0]) < 1.0, (
            "en %s la traslacion suma %.0f y el entrepiso pide %.0f"
            % (dire, tot_d, V_ent[0]))
        # 2. y la parte por TORSION solo anade: nunca es negativa
        assert tot_t > 0, "la torsion en %s no anade nada" % dire
        # 3. la suma de rigideces de la direccion tiene que ser la del
        #    denominador que la formula usa
        s = sum(r["K"] for r in rep.values() if r["dir"] == dire)
        assert abs(s - K_dir[dire]) < 1e-6, (
            "la suma de Ki en %s no coincide con el denominador" % dire)
        print("  [ok] %s: la traslacion suma el cortante del entrepiso "
              "(%.0f kgf) y la torsion anade %.0f" % (dire, tot_d, tot_t))
        print("  [ok] %s: gobierna(n) %s con %.0f kgf"
              % (dire, ", ".join(sorted(x.split()[0] for x in peores)),
                 vmax))
    return True


if __name__ == "__main__":
    main()
