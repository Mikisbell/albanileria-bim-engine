# -*- coding: utf-8 -*-
"""Mide los textos que se pisan en TODAS las figuras, con el renderer real.

POR QUE EXISTE
==============
Mikis, 2026-09-21: *"todos los gráficos tienen los mismos errores, incluso
los textos se sobreponen encima de otro, no respetan su espacio, eso es
antiprofesional"*. Tenía razón, y lo peor es que había un guardián de solapes
**dando verde**: buscaba los `.dxf` en `dibujo/` cuando se habían mudado a
`salidas/cad/`, así que auditaba CERO archivos y reportaba CERO hallazgos.

Aquel guardián, además, sólo ve las láminas — lo que va al DXF. Las figuras
de análisis son matplotlib puro y no pasaban por ningún control.

COMO MIDE
=========
No estima: pide al renderer la caja real de cada texto ya compuesto, con su
fuente, su tamaño y su rotación, y cruza todas contra todas. Es lo mismo que
ve el ojo, medido en píxeles.

Se engancha interceptando `Figure.savefig`: cada generador guarda sus figuras
como siempre y aquí se miden justo antes de escribir el archivo, con el
tamaño y el dpi definitivos.
"""
import glob
import importlib.util
import io as _io
import contextlib
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, "..", "calculo"))

import matplotlib                                              # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402
from matplotlib.figure import Figure                           # noqa: E402

# Cuánto solape se tolera. No es cero: dos textos pueden compartir un píxel
# de borde sin que nadie lo note. Se mide como fracción del área del texto
# más chico, que es el que queda ilegible.
TOLERANCIA = 0.12

HALLAZGOS = []


def _ticks_en_rango(ax):
    u"""Los ticklabels que de verdad se dibujan: los que caen dentro.

    El eje se recorre con una BANDERA explicita y no preguntando
    `e in ax.get_xticklabels()`: esa llamada REGENERA la lista, asi que la
    pertenencia por identidad puede dar False para un tick horizontal y
    hacer que se lea su coordenada Y. El filtro descartaria entonces ticks
    perfectamente visibles y el auditor quedaria ciego justo donde mas
    mira. Un control que se equivoca callado es peor que no tenerlo.
    """
    dentro = []
    for etiquetas, lim, eje in ((ax.get_xticklabels(), ax.get_xlim(), 0),
                                (ax.get_yticklabels(), ax.get_ylim(), 1)):
        lo, hi = min(lim), max(lim)
        for e in etiquetas:
            v = e.get_position()[eje]
            if lo - 1e-9 <= v <= hi + 1e-9:
                dentro.append(e)
    return dentro


def _ascii(s):
    u"""Deja el texto imprimible en una consola cp1252."""
    return s.encode("cp1252", "replace").decode("cp1252")


def _cajas_de_texto(fig, renderer):
    """(texto, x0, y0, x1, y1) de cada rótulo visible, en píxeles."""
    out = []
    for ax in fig.get_axes():
        # Un eje apagado con axis("off") NO dibuja sus ticklabels, pero
        # matplotlib los conserva y `get_window_extent` les sigue dando
        # caja. Contarlos produce solapes que el ojo no ve: el auditor
        # reportaba que una cota "pisaba" el tick 7.5 de un eje invisible.
        vis = ax.axison
        textos = list(ax.texts)
        if vis:
            # Y TAMPOCO SE DIBUJAN LOS TICKS FUERA DE LOS LIMITES. El locator
            # de matplotlib genera la serie completa --0, 10, ... 70-- y la
            # devuelve entera aunque el `xlim` corte en 63: esos sobrantes no
            # llegan al papel, pero `get_window_extent` les da caja igual. El
            # auditor los contaba y reportaba que un "70" invisible pisaba un
            # titulo, que es el mismo modo de falso positivo que el eje
            # apagado de arriba. Se descarta el tick cuyo VALOR cae fuera.
            textos += _ticks_en_rango(ax)
        if ax.get_title():
            textos.append(ax.title)
        for t in textos:
            s = (t.get_text() or "").strip()
            if not s or not t.get_visible():
                continue
            try:
                bb = t.get_window_extent(renderer=renderer)
            except Exception:
                continue
            if bb.width <= 0 or bb.height <= 0:
                continue
            out.append((s, bb.x0, bb.y0, bb.x1, bb.y1))
    for t in fig.texts:
        s = (t.get_text() or "").strip()
        if not s:
            continue
        try:
            bb = t.get_window_extent(renderer=renderer)
        except Exception:
            continue
        out.append((s, bb.x0, bb.y0, bb.x1, bb.y1))
    return out


def solapes_de(fig):
    """Los pares de texto que se pisan más de la tolerancia."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    cajas = _cajas_de_texto(fig, r)
    malos = []
    for i in range(len(cajas)):
        for j in range(i + 1, len(cajas)):
            sa, ax0, ay0, ax1, ay1 = cajas[i]
            sb, bx0, by0, bx1, by1 = cajas[j]
            sx = min(ax1, bx1) - max(ax0, bx0)
            sy = min(ay1, by1) - max(ay0, by0)
            if sx <= 0 or sy <= 0:
                continue
            area = sx * sy
            menor = min((ax1 - ax0) * (ay1 - ay0), (bx1 - bx0) * (by1 - by0))
            if menor > 0 and area / menor > TOLERANCIA:
                malos.append((sa, sb, area / menor))
    return malos


def tapados_por_el_dibujo(fig, renderer, umbral=6):
    """Textos con demasiado dibujo debajo: ilegibles aunque no pisen texto.

    El auditor medía texto contra texto y daba verde mientras "2 tramos de
    1,20 m" quedaba escrito encima de los nueve escalones de la escalera y
    "PASAJE" cruzaba un muro. Un texto no compite sólo con otro texto:
    compite con el dibujo, y ahí también deja de leerse.

    Se cuenta cuántas líneas y parches cruzan la caja del texto. Un rótulo
    sobre una superficie lisa cruza uno o dos; sobre una trama, muchos.
    """
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    malos = []
    for ax in fig.get_axes():
        textos = [x for x in ax.texts if (x.get_text() or "").strip()]
        piezas = [a for a in ax.get_children()
                  if isinstance(a, (Line2D, Patch))]
        for tx in textos:
            try:
                bb = tx.get_window_extent(renderer=renderer)
            except Exception:
                continue
            if bb.width <= 0:
                continue
            n = 0
            for pz in piezas:
                try:
                    pbb = pz.get_window_extent(renderer=renderer)
                except Exception:
                    continue
                if pbb.width <= 0 and pbb.height <= 0:
                    continue
                if (min(bb.x1, pbb.x1) > max(bb.x0, pbb.x0)
                        and min(bb.y1, pbb.y1) > max(bb.y0, pbb.y0)):
                    n += 1
            if n >= umbral:
                malos.append((tx.get_text().strip()[:36], n))
    return malos


def instalar():
    """Intercepta savefig para medir cada figura justo antes de guardarla."""
    original = Figure.savefig

    def savefig(self, fname, *a, **k):
        try:
            malos = solapes_de(self)
            self.canvas.draw()
            _r = self.canvas.get_renderer()
            for s, n in tapados_por_el_dibujo(self, _r):
                malos.append((s, "TAPADO por %d piezas de dibujo" % n, 1.0))
        except Exception as e:                      # nunca romper el dibujo
            malos = []
            HALLAZGOS.append((str(fname), [("<no se pudo medir>", str(e), 0)]))
        if malos:
            nombre = os.path.basename(str(fname))
            HALLAZGOS.append((nombre, malos))
        return original(self, fname, *a, **k)

    Figure.savefig = savefig


def generadores():
    """Las figuras de analisis Y LOS PLANOS. Ver el porque arriba."""
    for patron in ("F_*.py", "L_*.py"):
        for p in sorted(glob.glob(os.path.join(AQUI, patron))):
            yield p


def main():
    instalar()
    print("=" * 78)
    print("TEXTOS QUE SE PISAN  -  medidos con el renderer, no estimados")
    print("=" * 78)
    n = 0
    fallidos = []
    for ruta in generadores():
        nom = os.path.basename(ruta)
        spec = importlib.util.spec_from_file_location("_t_" + nom[:6], ruta)
        mod = importlib.util.module_from_spec(spec)
        try:
            with contextlib.redirect_stdout(_io.StringIO()):
                spec.loader.exec_module(mod)
                # No todos exponen main(): la planta arquitectonica se
                # ejecuta con dibujar(), asi que NUNCA pasaba por aca y sus
                # solapes no se median. Un auditor que solo mira lo que sabe
                # nombrar deja fuera justo lo que no conoce.
                arranque = None
                for nombre_f in ("main", "dibujar", "generar", "figura"):
                    if callable(getattr(mod, nombre_f, None)):
                        arranque = getattr(mod, nombre_f)
                        break
                if arranque is None:
                    raise RuntimeError(
                        "no expone main/dibujar/generar: no se puede auditar")
                arranque()
        except Exception as e:
            print("  !! %s no se pudo correr: %s" % (nom, str(e)[:70]))
            fallidos.append((nom, str(e)))
            continue
        n += 1
    print("  %d generadores de figura ejecutados" % n)
    print()
    if fallidos:
        print("  !! %d generador(es) NO se pudieron ejecutar:" % len(fallidos))
        for fnom, ferr in fallidos:
            print("      - %s: %s" % (fnom, ferr[:80]))
        print()
    if not HALLAZGOS and not fallidos:
        print("  [ok] ningun texto se pisa en ninguna figura")
        return 0
    total = 0
    for nombre, malos in HALLAZGOS:
        # SE CUENTA LA LISTA ENTERA, no los renglones que se imprimen. Ver
        # el porque arriba: el contador estaba dentro del bucle del [:8].
        total += len(malos)
        print("  %s   (%d solapes)" % (nombre, len(malos)))
        for sa, sb, frac in sorted(malos, key=lambda x: -x[2])[:8]:
            # EL GUARDIAN NO PUEDE REVENTAR AL REPORTAR. La consola de esta
            # maquina es cp1252 y los textos que audita son de las figuras,
            # donde hay simbolos que cp1252 no tiene --la raiz, las flechas,
            # las letras griegas--. Imprimirlos crudos levantaba un
            # UnicodeEncodeError y el guardian moria SIN DECIR CUAL ERA EL
            # SOLAPE: encontraba el defecto y se llevaba el hallazgo a la
            # tumba. Se sanea lo que se imprime, no lo que se mide.
            print("      %3.0f%%  %-34r pisa %r"
                  % (100 * frac, _ascii(sa[:32]), _ascii(sb[:32])))
        if len(malos) > 8:
            print("      ... y %d solapes mas en esta figura"
                  % (len(malos) - 8))
    print()
    if HALLAZGOS:
        print("  %d pares de texto que se pisan, en %d figuras"
              % (total, len(HALLAZGOS)))
    return total + len(fallidos)


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
