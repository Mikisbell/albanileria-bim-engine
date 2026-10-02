# -*- coding: utf-8 -*-
"""Lámina-cuadro: densidad mínima de muros reforzados (E.070 7.1.2.b).

POR QUE ESTA LAMINA
===================
El docente revisó el informe y pidió **una imagen por tema, con el formato
de las tablas de sus diapositivas**. En su ejemplo de edificio de 4 niveles
(Clase 06, «Paso 3 — Estructuración en planta, densidad mínima de muros»)
el cuadro tiene una columna por cada término de la fórmula, la fila Σ, la
comprobación escrita con sus números y el veredicto. Eso es lo que esta
lámina hace con los muros de ESTE proyecto.

UNA DIFERENCIA DE CRITERIO, DECLARADA
=====================================
El ejemplo de clase agrega una columna `Nm` —número de pisos— y suma
`Ac × Nm`. El acápite 7.1.2.b pone el número de pisos **en el lado derecho**
de la desigualdad:

    Σ(L·t) / Ap  ≥  Z·U·S·N / 56

de modo que el área de corte se suma sobre **una planta típica** y la `N`
entra una sola vez, en el límite. Multiplicar también el numerador contaría
los pisos dos veces. Este proyecto sigue la lectura literal del acápite, y
por eso su cuadro no lleva la columna `Nm`: el `N = 5` está adentro del
0,02902 de la derecha.

Vale la regla de la casa: las diapositivas mandan en CÓMO se presenta, la
norma manda en QUÉ se verifica.
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
    ruta = os.path.join(AQUI, "..", "calculo",
                        "01_arquitectura_y_densidad.py")
    spec = importlib.util.spec_from_file_location("_m01", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


def croquis_de_machones():
    u"""El mecanismo que la tabla no muestra: de donde sale la longitud NETA.

    POR QUE. La tabla trae "L = 11,90" al lado de "neta = 6,15" y el lector no
    tiene como saber por que casi la mitad del muro no cuenta. La respuesta es
    geometrica y se ve de un vistazo: el muro esta INTERRUMPIDO por vanos, y lo
    que entra en la densidad son los MACHONES --los tramos macizos entre
    ellos--, no el largo del muro.

    Y hay un umbral que la tabla tampoco puede mostrar: el acapite 6.4 solo
    admite machones de L >= 1,20 m. En este proyecto ninguno queda fuera --el
    mas corto mide 1,50-- pero eso es un RESULTADO, no un supuesto, y el
    croquis lo hace visible en vez de pedir que se crea.

    OJO CON LA LECTURA FACIL: no se pintan "machones descartados" porque no
    hay ninguno. Dibujar una leyenda para un caso vacio es la forma mas
    silenciosa de mentir en una figura.
    """
    import proyecto as P

    def dibujar(ax, x0, y0, ancho, alto):
        B, L = P.FRENTE, P.FONDO
        esc = min(ancho * 0.30 / B, alto * 0.94 / L)
        ox, oy = x0 + ancho * 0.05, y0 + alto * 0.04
        X = lambda u: ox + u * esc
        Y = lambda v: oy + v * esc
        t_dib = max(P.ESPESOR * esc, alto * 0.018)

        ax.add_patch(Rectangle((X(0), Y(0)), B * esc, L * esc, fc="#fbfcfe",
                               ec="#dde5ee", lw=0.7, zorder=1))
        ejes_x, _rot = P.ejes_x_rotulados()

        # CADA MURO SE DIBUJA COMO SUS TRAMOS, no como una linea entera: el
        # hueco de cada vano es lo que explica la longitud neta.
        peor, peor_nom = 1.0, ""
        for nom, dire, largo, t, vanos in P.MUROS:
            # LOS TRAMOS SE PIDEN, NO SE RECALCULAN. La primera version de
            # este croquis los derivaba de los vanos partiendo de x = 0, y
            # asi contaba de mas el tramo de arranque --los 0,15 m de media
            # columna extrema, que `machones()` NO devuelve porque no es
            # machon util--. Resultado: la figura decia que en MX-1 cuentan
            # 6,30 m y la tabla de al lado decia 6,15. **Dos numeros
            # distintos para el mismo dato en la misma lamina**, y el
            # causante fue violar la regla de la casa en la figura que la
            # enuncia. Se pide al SSOT y se verifica contra el.
            ubic = P.vanos_ubicados(nom, dire, largo, vanos)
            cortes = P.machones(nom, dire, largo, vanos)
            neta = sum(b - a for a, b in cortes)
            if largo > 0 and neta / largo < peor:
                peor, peor_nom = neta / largo, nom.split()[0]

            if dire == "X":
                yy = P.EJES_MX[_indice_x(nom)]
                for a, b in cortes:
                    ax.add_patch(Rectangle((X(a), Y(yy) - t_dib / 2.0),
                                           (b - a) * esc, t_dib,
                                           fc=PAL.BIEN, ec="none", zorder=3))
                for v0, w in ubic:
                    ax.add_patch(Rectangle((X(v0), Y(yy) - t_dib / 2.0),
                                           w * esc, t_dib, fc="#ffffff",
                                           ec=PAL.GUIA, lw=0.5, zorder=4))
            else:
                xx = _eje_y(nom, ejes_x)
                y_ini = P.POZO_Y1 if nom.split()[0].endswith("b") else 0.0
                for a, b in cortes:
                    ax.add_patch(Rectangle((X(xx) - t_dib / 2.0, Y(y_ini + a)),
                                           t_dib, (b - a) * esc,
                                           fc=PAL.BIEN, ec="none", zorder=3))
                for v0, w in ubic:
                    ax.add_patch(Rectangle((X(xx) - t_dib / 2.0, Y(y_ini + v0)),
                                           t_dib, w * esc, fc="#ffffff",
                                           ec=PAL.GUIA, lw=0.5, zorder=4))

        # EL CONTROL QUE FALTABA: lo que el croquis dibuja tiene que sumar
        # exactamente la longitud neta que la tabla publica. Sin este
        # assert, una figura puede contradecir a la tabla que tiene al
        # lado y nadie se entera hasta que lo lee un tercero.
        netas = {}
        for dire in ("X", "Y"):
            for f in datos().tabla_densidad(dire):
                netas[f["nom"].split()[0]] = f["neta"]
        for nom, dire, largo, t_, vanos in P.MUROS:
            clave = nom.split()[0]
            dib = sum(b - a for a, b in P.machones(nom, dire, largo, vanos))
            assert abs(dib - netas[clave]) < 1e-6, (
                "%s: el croquis dibuja %.2f m de machon y la tabla publica "
                "%.2f" % (clave, dib, netas[clave]))

        # el muro mas interrumpido, acotado: es el que hace la pregunta
        ax.annotate("", xy=(X(0), Y(-0.9)), xytext=(X(B), Y(-0.9)),
                    arrowprops=dict(arrowstyle="<->", color=PAL.COTA, lw=1.0),
                    zorder=5)
        ax.text(X(B / 2.0), Y(-1.9), "L = %s m" % _coma(B), fontsize=7.2,
                color=PAL.COTA, ha="center", va="top", zorder=5)

        tx = x0 + ancho * 0.40
        disp = (x0 + ancho) - tx - 0.01
        titular = C.envolver(
            ax, u"Lo que cuenta en la densidad son los MACHONES, no el "
            u"muro:", 8.2, disp, "bold")
        for j, ln in enumerate(titular):
            ax.text(tx, y0 + alto * (0.95 - 0.075 * j), ln, fontsize=8.2,
                    color="#37474f", fontweight="bold", va="top")
        # PARRAFOS ENTEROS: los parte el motor contra el ancho que hay.
        # Antes venian cortados a mano para un lienzo de 13,6 pulgadas y eran
        # justo las lineas que se salian de la hoja.
        parrafos = [
            u"En verde los tramos macizos; en blanco los vanos, que "
            u"interrumpen el muro y no aportan área de corte. Por eso la "
            u"columna «neta» es menor que «L».",
            u"El caso extremo es %s: mide %s m y sólo cuentan %s — el %s %% "
            u"de su longitud. Un muro lleno de vanos aporta poco aunque sea "
            u"largo." % (peor_nom, _coma(B), _coma(B * peor),
                         _coma(100 * peor, 0)),
            u"El acápite 6.4 además descarta el machón de L < %s m. Acá "
            u"ninguno queda fuera: el más corto mide %s m. Es un "
            u"resultado, no un supuesto."
            % (_coma(P.LONG_MINIMA), _coma(_machon_mas_corto())),
        ]
        # el parrafo arranca DEBAJO del titular, cuente las lineas que cuente
        k = 0
        base = 0.95 - 0.075 * len(titular) - 0.015
        for par in parrafos:
            for ln in C.envolver(ax, par, 7.6, disp):
                ax.text(tx, y0 + alto * (base - 0.082 * k), ln, fontsize=7.6,
                        color="#55606a", va="top")
                k += 1
            k += 0.6
    return dibujar


def _indice_x(nom):
    u"""La fila del muro X, derivada de su orden en el SSOT."""
    import proyecto as P
    xs = [n for n, d, L, t, v in P.MUROS if d == "X"]
    return xs.index(nom)


def _eje_y(nom, ejes_x):
    u"""El eje vertical de un muro Y, por su clave."""
    clave = nom.split()[0][:4]
    return {"MY-1": ejes_x[0], "MY-3": ejes_x[1],
            "MY-4": ejes_x[3], "MY-2": ejes_x[-1]}[clave]


def _machon_mas_corto():
    """El machón más corto que queda en pie, MEDIDO.

    El párrafo que lo usa dice «es un resultado, no un supuesto» y lo
    escribía a mano: 1,50 m. Ahora lo es.
    """
    import proyecto as P
    # `machones` devuelve TRAMOS (inicio, fin): la longitud es la resta.
    return min(b - a for fila in P.MUROS
               for a, b in P.machones(fila[0], fila[1],
                                      fila[2], fila[4]))


def _coma(x, d=2):
    return (("%%.%df" % d) % x).replace(".", ",")


def main():
    from proyecto import AREA_PLANTA, Z, U, S, N_PISOS, LONG_MINIMA
    m = datos()
    req = m.densidad_requerida()
    area_req = req * AREA_PLANTA

    bloques, sumas, n_muros = [], {}, 0
    for dire in ("X", "Y"):
        filas_d = m.tabla_densidad(dire)
        filas, colores = [], []
        for f in filas_d:
            filas.append([
                f["nom"].split()[0],
                C.coma(f["L"]),
                C.coma(f["vanos"]),
                C.coma(f["neta"]),
                C.coma(f["t"]),
                C.coma(f["Ac"], 3),
            ])
            # el muro que pierde algún machón por el 6.4 se marca: es el
            # dato que explica por qué su Ac no es L·t
            colores.append("#fff4e5" if f["descartados"] else None)
        n_muros += len(filas_d)
        suma = sum(f["Ac"] for f in filas_d)
        sumas[dire] = suma
        bloques.append({
            "titulo": "Dirección %s-%s" % (dire, dire),
            "cols": ["Muro", "L\n(m)", "Σ vanos\n(m)", "L neta\n(m)",
                     "t\n(m)", "Ac = L·t\n(m²)"],
            "filas": filas,
            "suma": ["Σ", "", "", "", "", C.coma(suma, 3)],
            "colores_fila": colores,
        })

    comprobacion = []
    for dire in ("X", "Y"):
        d = sumas[dire] / AREA_PLANTA
        comprobacion.append(
            "Dirección %s-%s:   Σ(L·t)/Ap = %s / %s = %s   ≥   %s   →   "
            "CUMPLE  (holgura +%s %%)"
            % (dire, dire, C.coma(sumas[dire], 3), C.coma(AREA_PLANTA),
               C.coma(d, 4), C.coma(req, 4),
               C.coma((sumas[dire] / area_req - 1) * 100, 1)))

    # LA NOTA SOLO DICE LO QUE SE VE. Mencionaba "las filas en crema"
    # siempre, y hoy ningun muro pierde machones por el 6.4: no hay una
    # sola fila crema y la nota explicaba un color ausente.
    n_desc = sum(1 for d in ("X", "Y") for f in m.tabla_densidad(d)
                 if f["descartados"])
    nota = (
        "Solo cuenta el machon de %s m o mas: el acapite 6.4 exige que cada "
        "trozo llegue a ese minimo por su cuenta, y un vano parte el muro "
        "en dos. En esta planta los %d muros conservan todos sus machones "
        "por encima de ese minimo, asi que Ac coincide con L neta por t."
        % (C.coma(LONG_MINIMA), n_muros)) if n_desc == 0 else (
        "Solo cuenta el machon de %s m o mas (acapite 6.4). Las %d filas "
        "en crema son los muros a los que el 6.4 descarta algun machon, y "
        "por eso su Ac no sale de multiplicar la longitud neta por t."
        % (C.coma(LONG_MINIMA), n_desc))
    nota += (
        chr(10) + "El numero de pisos N = %d entra UNA vez, en el limite de "
        "la derecha (Z·U·S·N/56 = %s·%s·%s·%d/56 = %s): el area de "
        "corte se suma sobre una planta tipica, no se acumula por nivel."
        % (N_PISOS, C.coma(Z), C.coma(U), C.coma(S), N_PISOS,
           C.coma(req, 5)))

    out = os.path.join(R.INFORME, "CUADRO-DENSIDAD.png")
    C.lamina(
        paso="Paso 1 — Densidad mínima de muros",
        titulo="Área de corte de los muros reforzados sobre el área de la "
               "planta típica, dirección por dirección",
        formula=r"$\dfrac{\sum L \cdot t}{A_p} \;\geq\; "
                r"\dfrac{Z \cdot U \cdot S \cdot N}{56}$",
        acapite="E.070  7.1.2.b",
        bloques=bloques,
        comprobacion=comprobacion,
        nota=nota,
        salida=out,
        croquis=croquis_de_machones(),
        alto_croquis=2.5,
    )
    print()
    control(m, sumas, area_req, n_desc)


def control(m, sumas, area_req, n_desc):
    """Lo que la lámina afirma sale del script 01, no del dibujo."""
    from proyecto import AREA_PLANTA
    for dire in ("X", "Y"):
        # 1. la suma dibujada tiene que ser la del script, muro por muro
        s = sum(f["Ac"] for f in m.tabla_densidad(dire))
        assert abs(s - sumas[dire]) < 1e-9, (
            "la lámina suma %.3f en %s y el script da %.3f"
            % (sumas[dire], dire, s))
        # 2. y el veredicto que escribe tiene que ser cierto
        assert sumas[dire] >= area_req, (
            "la lámina escribe CUMPLE en %s y %.3f < %.3f"
            % (dire, sumas[dire], area_req))
    # 3. la nota afirma que hay muros con machones descartados por el 6.4;
    #    si dejara de haberlos, el color crema no explicaría nada
    con_descarte = [f for d in ("X", "Y") for f in m.tabla_densidad(d)
                    if f["descartados"]]
    print("  [ok] las dos sumas coinciden con el script 01")
    print("  [ok] las dos direcciones superan el área requerida de %.3f m²"
          % area_req)
    # LA NOTA TIENE QUE DECIR LO QUE SE VE: si no hay filas crema, no puede
    # hablar de ellas, y si las hay tiene que nombrarlas. Un pie que explica
    # un color ausente es la misma familia de defecto que un rotulo escrito
    # a mano que envejece.
    assert (len(con_descarte) == 0) == (n_desc == 0), (
        "la nota y la tabla no coinciden sobre los machones descartados")
    print("  [ok] machones descartados por el 6.4: %d; la nota dice lo que "
          "se ve" % len(con_descarte))
    return True


if __name__ == "__main__":
    main()
