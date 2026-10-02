# -*- coding: utf-8 -*-
"""
scripts/planos/lamina.py — motor de LAMINA para el item 2 (planos).

QUE ES
------
Una ``Lamina`` es una hoja A3 apaisada (420 x 297 mm) con un sistema de
coordenadas en MILIMETROS DE HOJA, dentro de la cual se dibuja la planta a una
ESCALA declarada. Esa separacion (hoja en mm / planta en metros) es lo que
permite que el rotulo "ESC. 1:75" del cajetin sea CIERTO y no decorativo: la
transformacion modelo -> hoja es literalmente ``mm = x_m * 1000 / S``.

POR QUE ESTE MODULO EXISTE Y NO SE REUSO ``_libro_common.py``
-------------------------------------------------------------
``scripts/planos/_libro_common.py`` viene del proyecto anterior y declara en su
cabecera, con la palabra "BLINDADA", la geometria de OTRA casa (grilla
0/5/10/15 x 0/6/12, columnas 0.40, caja de escalera en x[5.30,7.30]). Sus
helpers de arquitectura son coordenadas literales de esa planta: no hay nada
que "cablear al SSOT" ahi, hay que redibujar. Lo que si se conserva de aquel
trabajo es el CRITERIO de dibujo que ya habia sido auditado (cotas con ticks a
45 grados en vez de cabezas de flecha, burbujas blancas opacas por encima de
las lineas de eje, espanol con tildes), y eso esta reimplementado aca.

Toda la geometria del edificio entra por el SSOT del proyecto que lo use
(aqui, ``calculo/proyecto.py``).
Este modulo NO declara ni una cota del edificio.

DOBLE SALIDA
------------
Cada primitiva se guarda una sola vez y se rinde a dos destinos:
  * matplotlib  -> PNG + PDF (la lamina completa, con cajetin y leyenda);
  * ezdxf       -> DXF en METROS (solo la geometria de la planta; el cajetin y
                   los cuadros son mobiliario de hoja y no van al DXF).
Asi el DXF no puede desincronizarse del PNG: salen del mismo arbol de
primitivas.
"""

from __future__ import annotations

import contextlib
import math
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Arc, Circle, Patch, Polygon, Rectangle  # noqa: E402

# Raiz del proyecto: se localiza SUBIENDO el arbol hasta hallar belico.yaml.
# La raiz de ESTE proyecto es la carpeta que contiene calculo/proyecto.py.
# El original subia buscando belico.yaml, que aqui no existe: esta carpeta
# de la universidad no es un repo de la fabrica.
_ROOT = Path(__file__).resolve().parent
while _ROOT != _ROOT.parent and not (_ROOT / "calculo" / "proyecto.py").exists():
    _ROOT = _ROOT.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "calculo") not in sys.path:
    sys.path.insert(0, str(_ROOT / "calculo"))

try:  # ezdxf es opcional: si no esta, se emiten PNG/PDF igual y se avisa.
    import ezdxf

    HAY_EZDXF = True
except ImportError:  # pragma: no cover - depende del entorno
    ezdxf = None
    HAY_EZDXF = False


# ===========================================================================
# HOJA
# ===========================================================================
A3_MM = (420.0, 297.0)
MARGEN_MM = 8.0
CAJETIN_W_MM = 62.0
MM_A_PT = 72.0 / 25.4  # 1 mm de hoja = 2.8346 pt (la figura mide exactamente A3)


# ===========================================================================
# CAPAS  (nombre -> color ACI para DXF, color matplotlib, ancho de linea base)
# ===========================================================================
# La paleta vive en paleta.py: aca solo se referencia. Antes cada color
# estaba escrito a mano en cada archivo y cambiar el aspecto significaba
# buscar veinte literales.
import paleta as PAL                                          # noqa: E402

CAPAS: dict[str, dict[str, Any]] = {
    "EJES":      dict(aci=5,  c=PAL.EJE, lw=0.5),
    "MUROS":     dict(aci=7,  c=PAL.MURO_BORDE, lw=1.6),
    "TABIQUE":   dict(aci=7,  c=PAL.GUIA, lw=1.1),
    "COLUMNAS":  dict(aci=1,  c=PAL.COLUMNA_BORDE, lw=0.8),
    "VIGAS":     dict(aci=3,  c=PAL.SOLERA, lw=1.0),
    "LOSA":      dict(aci=8,  c=PAL.VIGUETA, lw=0.5),
    "VACIO":     dict(aci=8,  c=PAL.VACIO, lw=0.8),
    "COTAS":     dict(aci=4,  c=PAL.COTA, lw=0.5),
    "TEXTO":     dict(aci=2,  c=PAL.TEXTO, lw=0.4),
    "ZAPATAS":   dict(aci=6,  c=PAL.CIMIENTO_BORDE, lw=1.2),
    "VC":        dict(aci=30, c="#c0560f", lw=1.0),
    "PARAPETO":  dict(aci=30, c="#d1780f", lw=1.4),
    "PUERTA":    dict(aci=32, c="#8a5a2b", lw=0.7),
    "VENTANA":   dict(aci=140, c="#2b6cb0", lw=0.9),
    "MUEBLE":    dict(aci=9,  c="#9aa4ad", lw=0.5),
    "ESCALERA":  dict(aci=3,  c="#1e7a46", lw=0.7),
    "CAJETIN":   dict(aci=7,  c="#1a1a1a", lw=0.6),
    "TERRENO":   dict(aci=43, c="#8a7a55", lw=0.8),
}


def _capa(nombre: str) -> dict[str, Any]:
    if nombre not in CAPAS:
        raise KeyError(f"capa desconocida: {nombre!r}. Declararla en CAPAS.")
    return CAPAS[nombre]


# ===========================================================================
# PRIMITIVAS
# ===========================================================================
@dataclass
class Prim:
    """Una primitiva de dibujo.

    ``pm`` son coordenadas de MODELO (metros) cuando la primitiva pertenece a
    la planta; ``ph`` son coordenadas de HOJA (mm). Las primitivas que solo
    tienen ``ph`` (cajetin, cuadros, leyenda) NO se exportan al DXF.
    """

    kind: str
    layer: str
    ph: list[tuple[float, float]] = field(default_factory=list)
    pm: list[tuple[float, float]] | None = None
    opts: dict[str, Any] = field(default_factory=dict)


class Lamina:
    """Hoja A3 con una ventana de planta a escala declarada."""

    def __init__(
        self,
        codigo: str,
        titulo: str,
        subtitulo: str,
        escala: int,
        meta: dict[str, Any],
        nota_pie: str = "",
    ) -> None:
        self.codigo = codigo
        self.titulo = titulo
        self.subtitulo = subtitulo
        self.S = float(escala)            # denominador de escala (1:S)
        self.meta = meta
        self.nota_pie = nota_pie
        self.prims: list[Prim] = []
        self.leyenda: list[tuple[str, str, str]] = []  # (tipo, layer, etiqueta)
        self._caja_leyenda = None
        self._cajas_hoja = []   # (nombre, x0, y0, x1, y1)
        # transformacion modelo -> hoja:  mm = (x_m - ox) * 1000/S + hx
        self._ox = 0.0
        self._oy = 0.0
        self._hx = MARGEN_MM
        self._hy = MARGEN_MM

    # -- area util de dibujo (todo lo que no es cajetin ni margen) ----------
    @property
    def area_dibujo(self) -> tuple[float, float, float, float]:
        return (MARGEN_MM, MARGEN_MM,
                A3_MM[0] - MARGEN_MM - CAJETIN_W_MM, A3_MM[1] - MARGEN_MM)

    # -- escala / encuadre --------------------------------------------------
    def k(self) -> float:
        """Factor modelo(m) -> hoja(mm)."""
        return 1000.0 / self.S

    def m2mm(self, v_m: float) -> float:
        return v_m * self.k()

    def mm2m(self, v_mm: float) -> float:
        return v_mm / self.k()

    def encuadrar(self, x0: float, x1: float, y0: float, y1: float,
                  centro_mm: tuple[float, float] | None = None) -> None:
        """Centra la ventana de modelo [x0,x1]x[y0,y1] en el area de dibujo."""
        ax0, ay0, ax1, ay1 = self.area_dibujo
        if centro_mm is None:
            centro_mm = ((ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0)
        w_mm = self.m2mm(x1 - x0)
        h_mm = self.m2mm(y1 - y0)
        if w_mm > (ax1 - ax0) + 1e-6 or h_mm > (ay1 - ay0) + 1e-6:
            raise ValueError(
                f"[{self.codigo}] la ventana {x1-x0:.2f} x {y1-y0:.2f} m a 1:{self.S:.0f} "
                f"mide {w_mm:.1f} x {h_mm:.1f} mm y NO entra en el area de dibujo "
                f"({ax1-ax0:.1f} x {ay1-ay0:.1f} mm). Bajar la escala o recortar."
            )
        self._ox, self._oy = x0, y0
        self._hx = centro_mm[0] - w_mm / 2.0
        self._hy = centro_mm[1] - h_mm / 2.0

    def T(self, p: Sequence[float]) -> tuple[float, float]:
        """Modelo (m) -> hoja (mm)."""
        return (self._hx + (p[0] - self._ox) * self.k(),
                self._hy + (p[1] - self._oy) * self.k())

    def Tinv(self, q: Sequence[float]) -> tuple[float, float]:
        """Hoja (mm) -> modelo (m). Sirve para colocar un detalle a otra
        escala dentro de una zona libre de la hoja."""
        return (self._ox + (q[0] - self._hx) / self.k(),
                self._oy + (q[1] - self._hy) / self.k())

    # ======================================================================
    # PRIMITIVAS EN COORDENADAS DE MODELO (metros) — van al PNG y al DXF
    # ======================================================================
    def _add(self, kind: str, layer: str, pm=None, ph=None, **opts) -> Prim:
        _capa(layer)
        if pm is not None:
            pm = [(float(a), float(b)) for a, b in pm]
            ph = [self.T(p) for p in pm]
        pr = Prim(kind=kind, layer=layer, ph=list(ph or []), pm=pm, opts=opts)
        self.prims.append(pr)
        return pr

    def linea(self, p1, p2, layer="MUROS", **o):
        return self._add("line", layer, pm=[p1, p2], **o)

    def poli(self, pts, layer="MUROS", cerrar=True, **o):
        return self._add("poly", layer, pm=list(pts), cerrar=cerrar, **o)

    def rect(self, x0, y0, x1, y1, layer="MUROS", **o):
        return self.poli([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layer=layer, **o)

    def circulo(self, c, r_m, layer="EJES", **o):
        return self._add("circle", layer, pm=[c], r=r_m,
                         _r_mm=self.m2mm(r_m), **o)

    def arco(self, c, r_m, a0, a1, layer="PUERTA", **o):
        return self._add("arc", layer, pm=[c], r=r_m, a0=a0, a1=a1,
                         _r_mm=self.m2mm(r_m), **o)

    def texto(self, p, s, h_mm=2.5, layer="TEXTO", ha="center", va="center",
              rot=0.0, weight="normal", color=None, bbox=None, zorder=None):
        return self._add("text", layer, pm=[p], s=s, h_mm=h_mm, ha=ha, va=va,
                         rot=rot, weight=weight, color=color, bbox=bbox,
                         zorder=zorder)

    # ======================================================================
    # PRIMITIVAS EN COORDENADAS DE HOJA (mm) — solo PNG/PDF
    # ======================================================================
    def h_linea(self, p1, p2, layer="CAJETIN", **o):
        return self._add("line", layer, ph=[p1, p2], **o)

    def h_rect(self, x0, y0, x1, y1, layer="CAJETIN", **o):
        return self._add("poly", layer,
                         ph=[(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                         cerrar=True, **o)

    def h_texto(self, p, s, h_mm=2.5, layer="TEXTO", ha="center", va="center",
                rot=0.0, weight="normal", color=None, zorder=None):
        return self._add("text", layer, ph=[p], s=s, h_mm=h_mm, ha=ha, va=va,
                         rot=rot, weight=weight, color=color, bbox=None,
                         zorder=zorder)

    # ======================================================================
    # EJES, BURBUJAS Y COTAS
    # ======================================================================
    def ejes(self, gx: Sequence[float], gy: Sequence[float],
             etx: Sequence[str], ety: Sequence[str],
             ext_mm: float = 14.0, r_burbuja_mm: float = 4.0,
             lados_x: str = "ambos", lados_y: str = "ambos") -> None:
        """Lineas de eje a trazos + burbujas numeradas, con extension en mm."""
        ext = self.mm2m(ext_mm)
        rb = self.mm2m(r_burbuja_mm)
        y0, y1 = gy[0] - ext, gy[-1] + ext
        x0, x1 = gx[0] - ext, gx[-1] + ext
        for i, x in enumerate(gx):
            self.linea((x, y0), (x, y1), layer="EJES", ls=(0, (9, 3, 1.5, 3)))
            sitios = []
            if lados_x in ("ambos", "abajo"):
                sitios.append(y0 - rb)
            if lados_x in ("ambos", "arriba"):
                sitios.append(y1 + rb)
            for yb in sitios:
                self.circulo((x, yb), rb, layer="EJES", fc="white", zorder=30)
                self.texto((x, yb), etx[i], h_mm=3.2, layer="EJES",
                           weight="bold", zorder=31)
        for j, y in enumerate(gy):
            self.linea((x0, y), (x1, y), layer="EJES", ls=(0, (9, 3, 1.5, 3)))
            sitios = []
            if lados_y in ("ambos", "izq"):
                sitios.append(x0 - rb)
            if lados_y in ("ambos", "der"):
                sitios.append(x1 + rb)
            for xb in sitios:
                self.circulo((xb, y), rb, layer="EJES", fc="white", zorder=30)
                self.texto((xb, y), ety[j], h_mm=3.2, layer="EJES",
                           weight="bold", zorder=31)

    def cota(self, p1, p2, txt: str | None = None, off_mm: float = 0.0,
             vert: bool = False, h_mm: float = 2.3, tick_mm: float = 1.6,
             ext_mm: float = 1.2, color: str | None = None,
             pos_txt: float = 0.5) -> None:
        """Cota estilo estructural: linea + ticks a 45 grados + texto encima.

        Se usan TICKS y no cabezas de flecha porque en segmentos cortos las
        cabezas se comen la cota y el numero queda pisado (auditoria del juego
        de planos anterior).
        """
        off = self.mm2m(off_mm)
        t = self.mm2m(tick_mm) / math.sqrt(2.0)
        e = self.mm2m(ext_mm)
        if vert:
            x = p1[0] + off
            a, b = (x, p1[1]), (x, p2[1])
            if txt is None:
                txt = f"{abs(p2[1]-p1[1]):.2f}"
            # lineas de extension
            self.linea((p1[0], p1[1]), (x + e * math.copysign(1, off or 1), p1[1]),
                       layer="COTAS", lw=0.35)
            self.linea((p2[0], p2[1]), (x + e * math.copysign(1, off or 1), p2[1]),
                       layer="COTAS", lw=0.35)
            self.linea(a, b, layer="COTAS", **({"color": color} if color else {}))
            for p in (a, b):
                self.linea((p[0] - t, p[1] - t), (p[0] + t, p[1] + t),
                           layer="COTAS", **({"color": color} if color else {}))
            _yt = p1[1] + (p2[1] - p1[1]) * pos_txt
            self.texto((x - self.mm2m(1.1), _yt), txt,
                       h_mm=h_mm, layer="COTAS", rot=90, ha="center",
                       va="bottom", color=color)
        else:
            y = p1[1] + off
            a, b = (p1[0], y), (p2[0], y)
            if txt is None:
                txt = f"{abs(p2[0]-p1[0]):.2f}"
            self.linea((p1[0], p1[1]), (p1[0], y + e * math.copysign(1, off or 1)),
                       layer="COTAS", lw=0.35)
            self.linea((p2[0], p2[1]), (p2[0], y + e * math.copysign(1, off or 1)),
                       layer="COTAS", lw=0.35)
            self.linea(a, b, layer="COTAS", **({"color": color} if color else {}))
            for p in (a, b):
                self.linea((p[0] - t, p[1] - t), (p[0] + t, p[1] + t),
                           layer="COTAS", **({"color": color} if color else {}))
            _xt = p1[0] + (p2[0] - p1[0]) * pos_txt
            self.texto((_xt, y + self.mm2m(1.1)), txt,
                       h_mm=h_mm, layer="COTAS", ha="center", va="bottom",
                       color=color)

    def cadena_cotas(self, valores: Sequence[float], fijo: float,
                     off_mm: float, vert: bool = False,
                     total: bool = True, sep_mm: float = 7.0,
                     rotulo_total: str | None = None) -> None:
        """Cadena de cotas parciales + una cota total por debajo/al costado.

        `rotulo_total` le pone NOMBRE al total. Sin él, la cota del frente
        decía «11.90» y no decía de qué: el lote mide 12,00 y la diferencia
        son las dos juntas sísmicas de 5 cm, cosa que el lector no tiene
        cómo deducir de un número suelto. Una cota sin sujeto obliga a
        adivinar cuál de las dos medidas está mirando.
        """
        for a, b in zip(valores[:-1], valores[1:]):
            if vert:
                self.cota((fijo, a), (fijo, b), off_mm=off_mm, vert=True)
            else:
                self.cota((a, fijo), (b, fijo), off_mm=off_mm)
        if total and len(valores) > 2:
            o2 = off_mm + math.copysign(sep_mm, off_mm if off_mm else -1)
            largo = abs(valores[-1] - valores[0])
            txt = ("%.2f" % largo if not rotulo_total
                   else "%.2f  (%s)" % (largo, rotulo_total))
            if vert:
                self.cota((fijo, valores[0]), (fijo, valores[-1]),
                          txt=txt, off_mm=o2, vert=True)
            else:
                self.cota((valores[0], fijo), (valores[-1], fijo),
                          txt=txt, off_mm=o2)

    # ======================================================================
    # MOBILIARIO DE HOJA: cajetin, leyenda, norte, escala grafica
    # ======================================================================
    def cajetin(self) -> None:
        W, H = A3_MM
        x0 = W - MARGEN_MM - CAJETIN_W_MM
        x1 = W - MARGEN_MM
        y0, y1 = MARGEN_MM, H - MARGEN_MM
        # marco de la hoja y del cajetin
        self.h_rect(MARGEN_MM, MARGEN_MM, x1, y1, layer="CAJETIN", lw=1.4)
        self.h_rect(x0, y0, x1, y1, layer="CAJETIN", lw=1.0, fc="#fbfaf7")
        m = self.meta
        filas: list[tuple[float, list[tuple[str, float, str, str]]]] = []

        def banda(alto, contenido, fc=None):
            filas.append((alto, contenido, fc))

        banda(13, [("UNIVERSIDAD CONTINENTAL", 3.2, "bold", "#1a1a1a"),
                   ("Facultad de Ingenieria - E.P. Ingenieria Civil", 2.1, "normal", "#444")],
              "#eef1f4")
        banda(10, [("CURSO", 1.8, "normal", "#777"),
                   (str(m.get("curso", "")), 2.6, "bold", "#1a1a1a")])
        # el nombre del proyecto venia CLAVADO ("VIVIENDA UNIFAMILIAR DE 3
        # NIVELES"): un cajetin que miente sobre que edificio dibuja es peor
        # que no tener cajetin. Entra por meta, como todo lo demas.
        banda(16, [("PROYECTO", 1.8, "normal", "#777")]
                  + [(t_, 2.5, "bold", "#1a1a1a")
                     for t_ in _wrap(str(m.get("proyecto", "-")), 26)]
                  + [(str(m.get("ubicacion", "")), 2.1, "normal", "#444")])
        banda(20, [("LAMINA", 1.8, "normal", "#777")]
                  + [(t, 3.0, "bold", "#1a1a1a") for t in _wrap(self.titulo, 26)],
              "#f2f6f2")
        banda(13, [("CONTENIDO", 1.8, "normal", "#777")]
                  + [(t, 2.05, "normal", "#333") for t in _wrap(self.subtitulo, 34)])
        banda(11, [("ESCALA", 1.8, "normal", "#777"),
                   (f"1 : {self.S:.0f}", 4.0, "bold", "#1a1a1a")], "#f2f6f2")
        banda(11, [("ALUMNO", 1.8, "normal", "#777"),
                   (str(m.get("alumno", "-")), 2.6, "bold", "#1a1a1a")])
        banda(11, [("PERIODO / FECHA", 1.8, "normal", "#777"),
                   (f"{m.get('periodo','')}   {m.get('fecha','')}", 2.3, "normal", "#333")])
        banda(15, [("MATERIALES", 1.8, "normal", "#777"),
                   (f"f'c = {m['fc']:.0f} kgf/cm2", 2.2, "normal", "#333"),
                   (f"fy = {m['fy']:.0f} kgf/cm2", 2.2, "normal", "#333")])
        banda(21, [("NORMAS APLICADAS", 1.8, "normal", "#777")]
                  + [(n, 1.85, "normal", "#333") for n in m.get("norms", [])])

        y = y1
        for alto, contenido, *rest in filas:
            fc = rest[0] if rest else None
            y2 = y - alto
            if fc:
                self.h_rect(x0, y2, x1, y, layer="CAJETIN", lw=0.5, fc=fc)
            else:
                self.h_linea((x0, y2), (x1, y2), layer="CAJETIN", lw=0.5)
            n = len(contenido)
            paso = alto / (n + 0.6)
            yy = y - paso * 0.85
            for s, h, w, c in contenido:
                self.h_texto((x0 + 2.5, yy), s, h_mm=h, ha="left", va="center",
                             weight=w, color=c)
                yy -= paso
            y = y2
        # codigo de lamina, abajo del cajetin
        self.h_rect(x0, y0, x1, y0 + 16, layer="CAJETIN", lw=0.8, fc="#1a1a1a")
        self.h_texto((x0 + 3, y0 + 8), "LAMINA", h_mm=2.2, ha="left",
                     va="center", color="white")
        self.h_texto((x1 - 3, y0 + 8), self.codigo, h_mm=6.5, ha="right",
                     va="center", weight="bold", color="white")
        # pie de hoja: procedencia del dibujo (a la derecha, antes del cajetin, para no pisar ejes)
        proc_str = str(m.get("procedencia", "Geometria leida del SSOT del proyecto"))
        if self.nota_pie:
            self.h_texto((x0 - 4, MARGEN_MM + 4.2), self.nota_pie, h_mm=2.0,
                         ha="right", va="bottom", color="#a33", weight="bold")
            self.h_texto((x0 - 4, MARGEN_MM + 1.2), proc_str,
                         h_mm=1.7, ha="right", va="bottom", color="#777")
        else:
            self.h_texto((x0 - 4, MARGEN_MM + 2.0), proc_str,
                         h_mm=1.8, ha="right", va="bottom", color="#777")
        # EL PIE ES UN BLOQUE MAS. No estaba registrado, asi que el control
        # de bloques no lo veia: el 2026-09-30 el detalle de junta de la E-01
        # quedo montado sobre el con «6 bloques, ninguno se pisa» en verde.
        # Ancho estimado a 0,56 h por caracter (medido en la hoja: 0,52).
        if self.nota_pie:
            ancho = max(len(self.nota_pie) * 2.0, len(proc_str) * 1.7) * 0.56
            alto = 4.2 + 2.0 * 1.2
        else:
            ancho = len(proc_str) * 1.8 * 0.56
            alto = 2.0 + 1.8 * 1.2
        self._cajas_hoja.append(("PIE DE HOJA", x0 - 4 - ancho, MARGEN_MM,
                                 x0 - 4, MARGEN_MM + alto))

    def leyenda_add(self, tipo: str, layer: str, etiqueta: str) -> None:
        self.leyenda.append((tipo, layer, etiqueta))

    def leyenda_dibujar(self, x_mm: float, y_mm: float, ancho_mm: float = 56.0,
                        titulo: str = "LEYENDA") -> None:
        if not self.leyenda:
            return
        # 5,0 mm de paso para un texto de 2,3 era holgura de sobra; al
        # sumar la entrada del muro con ventana la caja invadio el bloque
        # de abajo por 1,7 mm. 4,6 sigue siendo el doble del alto del tipo.
        paso = 4.6
        alto = 7.4 + paso * len(self.leyenda)
        # el ancho lo manda la entrada mas larga, no un numero fijo
        mas_larga = max(len(str(e[2])) for e in self.leyenda)
        # Factor empirico ajustado a 0.7 para que los textos largos no desborden la caja
        ancho_mm = max(ancho_mm, 13.5 + 2.15 * 0.70 * mas_larga + 5.0)
        # se recuerda la caja: `render_figura` la usa para saber que
        # primitivas de hoja son la leyenda y cuales son cajetin
        self._caja_leyenda = (x_mm, y_mm - alto, x_mm + ancho_mm, y_mm)
        self._cajas_hoja.append(("LEYENDA",) + self._caja_leyenda)
        self.h_rect(x_mm, y_mm - alto, x_mm + ancho_mm, y_mm,
                    layer="CAJETIN", lw=0.7, fc="white")
        self.h_texto((x_mm + 3, y_mm - 4.2), titulo, h_mm=2.6, ha="left",
                     va="center", weight="bold")
        yy = y_mm - 9.5
        for tipo, layer, et in self.leyenda:
            cfg = _capa(layer)
            if tipo == "linea":
                self.h_linea((x_mm + 3, yy), (x_mm + 11, yy), layer=layer,
                             lw=cfg["lw"] * 1.4)
            elif tipo == "trazos":
                self.h_linea((x_mm + 3, yy), (x_mm + 11, yy), layer=layer,
                             lw=cfg["lw"] * 1.4, ls=(0, (4, 2)))
            else:  # parche
                self.h_rect(x_mm + 3, yy - 1.7, x_mm + 11, yy + 1.7,
                            layer=layer, lw=0.7, fc=tipo)
            self.h_texto((x_mm + 13.5, yy), et, h_mm=2.15, ha="left", va="center")
            yy -= paso

    def norte(self, x_mm: float, y_mm: float, r_mm: float = 7.0) -> None:
        """Rosa de los vientos. +Y del modelo apunta al NORTE (ver doc)."""
        self.h_rect(x_mm - r_mm - 2, y_mm - r_mm - 6, x_mm + r_mm + 2,
                    y_mm + r_mm + 6, layer="CAJETIN", lw=0.6, fc="white")
        self._add("poly", "CAJETIN",
                  ph=[(x_mm, y_mm + r_mm), (x_mm - r_mm * 0.45, y_mm - r_mm * 0.55),
                      (x_mm, y_mm - r_mm * 0.2)], cerrar=True, fc="#1a1a1a", lw=0.4)
        self._add("poly", "CAJETIN",
                  ph=[(x_mm, y_mm + r_mm), (x_mm + r_mm * 0.45, y_mm - r_mm * 0.55),
                      (x_mm, y_mm - r_mm * 0.2)], cerrar=True, fc="white", lw=0.4)
        self.h_texto((x_mm, y_mm + r_mm + 3.2), "N", h_mm=3.0, weight="bold")

    def escala_grafica(self, x_mm: float, y_mm: float, metros: int = 5,
                       paso_m: float = 1.0) -> None:
        """Escala grafica: sobrevive a un PDF reescalado, el rotulo 1:S no."""
        largo = self.m2mm(metros)
        h = 1.8
        for i in range(metros):
            x0 = x_mm + self.m2mm(i * paso_m)
            x1 = x_mm + self.m2mm((i + 1) * paso_m)
            self.h_rect(x0, y_mm, x1, y_mm + h, layer="CAJETIN", lw=0.4,
                        fc=("#1a1a1a" if i % 2 == 0 else "white"))
        for i in range(metros + 1):
            self.h_texto((x_mm + self.m2mm(i * paso_m), y_mm - 1.2),
                         f"{i * paso_m:.0f}", h_mm=1.9, va="top")
        self.h_texto((x_mm + largo + 3, y_mm + h / 2), "m", h_mm=2.0,
                     ha="left", va="center")

    # ======================================================================
    # CUADROS (tablas) EN HOJA
    # ======================================================================
    def cuadro(self, x_mm: float, y_mm: float, titulo: str,
               encabezado: Sequence[str], filas: Sequence[Sequence[str]],
               anchos_mm: Sequence[float], h_fila: float = 5.0,
               h_txt: float = 2.05, color_tit: str = "#1a1a1a",
               nota: str = "") -> float:
        """Dibuja una tabla con esquina superior izquierda en (x_mm, y_mm).

        Devuelve la coordenada Y (mm) del borde inferior, para encadenar.
        """
        W = sum(anchos_mm)
        self.h_texto((x_mm, y_mm + 2.0), titulo, h_mm=2.7, ha="left",
                     va="bottom", weight="bold", color=color_tit)
        y = y_mm
        todas = [list(encabezado)] + [list(f) for f in filas]
        for r, fila in enumerate(todas):
            xx = x_mm
            for c, celda in enumerate(fila):
                self.h_rect(xx, y - h_fila, xx + anchos_mm[c], y,
                            layer="CAJETIN", lw=0.4,
                            fc=("#e8eef3" if r == 0 else "white"))
                self.h_texto((xx + anchos_mm[c] / 2.0, y - h_fila / 2.0),
                             str(celda), h_mm=h_txt,
                             weight=("bold" if r == 0 else "normal"))
                xx += anchos_mm[c]
            y -= h_fila
        if nota:
            for k, ln in enumerate(_wrap(nota, int(W / 1.35))):
                self.h_texto((x_mm, y - 2.0 - k * 2.6), ln, h_mm=1.85,
                             ha="left", va="top", color="#666")
            y -= 2.0 + 2.6 * len(_wrap(nota, int(W / 1.35)))
        self._cajas_hoja.append((titulo[:28], x_mm, y, x_mm + W, y_mm + 4.0))
        return y

    # ======================================================================
    # SALIDA
    # ======================================================================
    def render(self, out_dir: Path, dpi: int = 200,
               dxf_dir: Path | None = None) -> dict[str, Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        fig = plt.figure(figsize=(A3_MM[0] / 25.4, A3_MM[1] / 25.4), dpi=dpi)
        ax = fig.add_axes((0, 0, 1, 1))
        ax.set_xlim(0, A3_MM[0])
        ax.set_ylim(0, A3_MM[1])
        ax.set_aspect("equal")
        ax.axis("off")
        fig.patch.set_facecolor("white")
        for pr in self.prims:
            _render_mpl(ax, pr)
        base = f"{self.codigo}_{_slug(self.titulo)}"
        salidas: dict[str, Path] = {}
        for ext in ("png", "pdf"):
            p = out_dir / f"{base}.{ext}"
            fig.savefig(p, dpi=dpi, facecolor="white")
            salidas[ext] = p
        plt.close(fig)
        if dxf_dir is not None and HAY_EZDXF:
            salidas["dxf"] = self._render_dxf(dxf_dir / f"{base}.dxf")
        return salidas

    def render_figura(self, out_dir: Path, dpi: int = 200,
                      con_leyenda: bool = True, margen_mm: float = 11.0,
                      sufijo: str = "_fig",
                      ancho_pagina: float | None = None,
                      alto_pagina: float | None = None,
                      cota_min_m: float = 0.0,
                      solo_bloque: str | None = None,
                      incluir_bloques: Sequence[str] | None = None,
                      dx_bloques: float = 0.0) -> Path:
        """El dibujo SOLO, recortado, para pegar en un informe o un libro.

        Sin cajetin y sin marco de hoja: en una pagina que ya tiene titulo,
        numero de figura y pie, el cajetin repite lo que la portada dijo y
        se come el espacio del dibujo. La leyenda si se conserva -- el
        lector del informe la necesita igual -- salvo que se pida lo
        contrario.

        El lienzo toma la PROPORCION del dibujo, de modo que la figura
        llene la pagina en vez de quedar flotando en una hoja apaisada.
        """
        out_dir.mkdir(parents=True, exist_ok=True)

        # que primitivas entran: las de modelo siempre; las de hoja solo si
        # pertenecen a la leyenda o a bloques pedidos expresamente
        caja_ley = self._caja_leyenda if con_leyenda else None
        cajas_inc = []
        if incluir_bloques:
            for b in incluir_bloques:
                cajas_inc.extend([c for c in self._cajas_hoja if b.upper() in c[0].upper()])

        elegidas = []
        for pr in self.prims:
            if pr.pm is not None:
                elegidas.append(pr)
            elif caja_ley and pr.ph and self._en_caja(pr.ph, caja_ley):
                elegidas.append(pr)
            elif cajas_inc and pr.ph:
                for c in cajas_inc:
                    bx0, by0, bx1, by1 = c[1], c[2], c[3], c[4]
                    if all(bx0 - 2 <= q[0] <= bx1 + 2 and by0 - 2 <= q[1] <= by1 + 2 for q in pr.ph):
                        elegidas.append(pr)
                        break
        if not elegidas:
            # Una lamina puede ser SOLO detalles en coordenadas de hoja --
            # E-05 no lleva planta--, y entonces no hay ni una primitiva de
            # modelo. En ese caso la figura son los BLOQUES registrados,
            # menos el cajetin, que es lo que un informe no quiere.
            cajas = [c for c in self._cajas_hoja
                     if "CAJETIN" not in c[0].upper()]
            if cajas:
                bx0 = min(c[1] for c in cajas)
                by0 = min(c[2] for c in cajas)
                bx1 = max(c[3] for c in cajas)
                by1 = max(c[4] for c in cajas)
                elegidas = [pr for pr in self.prims
                            if pr.pm is None and pr.ph
                            and all(bx0 - 2 <= q[0] <= bx1 + 2
                                    and by0 - 2 <= q[1] <= by1 + 2
                                    for q in pr.ph)]
        # UN SOLO BLOQUE, si se pide: cada detalle es su propia figura.
        if solo_bloque:
            caja = next((c for c in self._cajas_hoja
                         if c[0].upper() == solo_bloque.upper()), None)
            if caja is None:
                raise ValueError(
                    "[%s] no hay bloque %r; los que hay son %s"
                    % (self.codigo, solo_bloque,
                       [c[0] for c in self._cajas_hoja]))
            _n, bx0, by0, bx1, by1 = caja
            elegidas = [pr for pr in elegidas
                        if all(bx0 - 2 <= q[0] <= bx1 + 2
                               and by0 - 2 <= q[1] <= by1 + 2
                               for q in self._puntos_hoja(pr))]

        if not elegidas:
            raise ValueError("[%s] no hay nada que dibujar" % self.codigo)

        # LAS COTAS DE OBRA NO VAN EN LA PAGINA. Ver el docstring.
        self.cotas_omitidas = 0
        if cota_min_m > 0:
            def _es_cota_chica(pr):
                if pr.layer != "COTAS":
                    return False
                if pr.kind == "text":
                    s = str(pr.opts.get("s", "")).replace(",", ".")
                    try:
                        return float(s) < cota_min_m
                    except ValueError:
                        return False
                if pr.pm and len(pr.pm) >= 2:
                    (ax_, ay), (bx, by) = pr.pm[0], pr.pm[-1]
                    return ((bx - ax_) ** 2 + (by - ay) ** 2) ** 0.5 < cota_min_m
                return False

            antes = len(elegidas)
            elegidas = [pr for pr in elegidas if not _es_cota_chica(pr)]
            self.cotas_omitidas = antes - len(elegidas)

        # La leyenda se dibujo donde la hoja A3 tenia sitio, que es lejos
        # del dibujo. Recortar sin mas deja ese hueco adentro de la figura:
        # en la planta 12 x 21 un tercio de la imagen quedaba en blanco. Se
        # la TRASLADA y se la pega al costado del dibujo.
        pm_pts = [q for pr in elegidas if pr.pm is not None
                  for q in self._puntos_hoja(pr)]
        ley = [pr for pr in elegidas if pr.pm is None]
        desp = {}
        if pm_pts and ley and not incluir_bloques:
            mx0 = min(q[0] for q in pm_pts)
            my0 = min(q[1] for q in pm_pts)
            lp = [q for pr in ley for q in pr.ph]
            # Mover debajo del dibujo: alinear a la izquierda (mx0) y poner el tope de la leyenda
            # debajo de la base del dibujo (my0 - margen_mm * 1.5)
            dx = mx0 - min(q[0] for q in lp)
            dy = (my0 - margen_mm * 1.5) - max(q[1] for q in lp)
            for pr in ley:
                desp[id(pr)] = (dx, dy)
        elif incluir_bloques and dx_bloques != 0.0:
            for pr in ley:
                desp[id(pr)] = (dx_bloques, 0.0)

        def _pts(pr):
            q = self._puntos_hoja(pr)
            d = desp.get(id(pr))
            return [(a + d[0], b + d[1]) for a, b in q] if d else q

        xs = [q[0] for pr in elegidas for q in _pts(pr)]
        ys = [q[1] for pr in elegidas for q in _pts(pr)]
        x0, x1 = min(xs) - margen_mm, max(xs) + margen_mm
        y0, y1 = min(ys) - margen_mm, max(ys) + margen_mm
        w, h = x1 - x0, y1 - y0

        # EL LIENZO: el de la hoja, o el de la PAGINA si se pide. Ver el
        # porque en el docstring. Al componer para la pagina el texto
        # conserva su cuerpo en puntos y lo que se comprime es el dibujo.
        anc_in, alt_in = w / 25.4, h / 25.4
        if ancho_pagina:
            k = ancho_pagina / anc_in
            if alto_pagina and alt_in * k > alto_pagina:
                k = alto_pagina / alt_in
            anc_in, alt_in = anc_in * k, alt_in * k
            self.compresion = k
        fig = plt.figure(figsize=(anc_in, alt_in), dpi=dpi)
        ax = fig.add_axes((0, 0, 1, 1))
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        ax.set_aspect("equal")
        ax.axis("off")
        fig.patch.set_facecolor("white")
        for pr in elegidas:
            d = desp.get(id(pr))
            if d:
                pr = replace(pr, ph=[(a + d[0], b + d[1]) for a, b in pr.ph])
            _render_mpl(ax, pr)
        p = out_dir / f"{self.codigo}_{_slug(self.titulo)}{sufijo}.png"
        fig.savefig(p, dpi=dpi, facecolor="white", bbox_inches="tight",
                    pad_inches=0.04)
        plt.close(fig)
        return p

    # -- soporte de render_figura ------------------------------------------
    def _puntos_hoja(self, pr) -> list:
        """Los puntos de una primitiva, siempre en coordenadas de hoja."""
        pts = [self.T(p) for p in pr.pm] if pr.pm is not None else list(pr.ph)
        if pr.kind == "text" and pts:
            # Expandir caja del texto para que no se recorte en los bordes
            x, y = pts[0]
            s = str(pr.opts.get("s", ""))
            h_mm = float(pr.opts.get("h_mm", 1.8))
            w = len(s) * h_mm * 0.75
            h = h_mm * 1.5
            return [(x - w, y - h), (x + w, y + h)]
        return pts

    @staticmethod
    def _en_caja(puntos, caja) -> bool:
        cx0, cy0, cx1, cy1 = caja
        return all(cx0 - 1 <= q[0] <= cx1 + 1 and cy0 - 1 <= q[1] <= cy1 + 1
                   for q in puntos)

    @contextlib.contextmanager
    def bloque_hoja(self, nombre: str, margen_mm: float = 1.0):
        """Registra la caja REAL de lo que se dibuje adentro.

        Antes cada bloque declaraba su caja a mano, y la caja declarada no es
        la caja real: el corte de cimentacion se salia 30 mm por arriba de la
        suya -- Df = 1,50 m a 1:25 son 60 mm de hoja y el numero escrito
        decia 46 -- y el control de solapes lo aprobo, porque comparaba la
        caja que YO dije, no la que el dibujo ocupa. Es el mismo patron que
        ya habia mordido dos veces: el control tiene que mirar el artefacto.
        """
        i0 = len(self.prims)
        yield
        pts = [q for pr in self.prims[i0:] if pr.pm is None for q in pr.ph]
        pts += [self.T(q) for pr in self.prims[i0:] if pr.pm is not None
                for q in pr.pm]
        if pts:
            m = margen_mm
            self._cajas_hoja.append((
                nombre, min(q[0] for q in pts) - m,
                min(q[1] for q in pts) - m,
                max(q[0] for q in pts) + m,
                max(q[1] for q in pts) + m))

    def control_hoja(self, holgura_mm: float = 0.5) -> list:
        """Bloques de hoja que se pisan entre si.

        El guardian de dibujo audita el DXF, y el DXF solo lleva las
        primitivas de MODELO: los cuadros, la leyenda y el cajetin viven en
        coordenadas de hoja y nunca se auditaban. Con la columna de cuadros
        colocada por numeros escritos a mano, la leyenda quedo encima del
        cuadro de la reticula y todo dio verde.
        """
        ch = []
        # Primero: contra el DIBUJO. La version anterior solo comparaba
        # bloques de hoja entre si, y el detalle de junta aterrizo encima de
        # la planta sin que nada chistara -- la planta es de MODELO, no de
        # hoja. Un bloque de hoja tampoco puede pisar el dibujo.
        pm_pts = [self.T(q) for pr in self.prims if pr.pm is not None
                  and pr.layer in ("MUROS", "COLUMNAS", "PUERTA", "VENTANA",
                                   "POZO", "ESCALERA", "COTAS", "EJES",
                                   "TEXTO")
                  for q in pr.pm]
        if pm_pts:
            dx0 = min(q[0] for q in pm_pts)
            dx1 = max(q[0] for q in pm_pts)
            dy0 = min(q[1] for q in pm_pts)
            dy1 = max(q[1] for q in pm_pts)
            for nom, ax0, ay0, ax1, ay1 in self._cajas_hoja:
                sx = min(ax1, dx1) - max(ax0, dx0) - holgura_mm
                sy = min(ay1, dy1) - max(ay0, dy0) - holgura_mm
                if sx > 0 and sy > 0:
                    ch.append((nom, "EL DIBUJO", round(sx, 1), round(sy, 1)))
        for i in range(len(self._cajas_hoja)):
            for j in range(i + 1, len(self._cajas_hoja)):
                na, ax0, ay0, ax1, ay1 = self._cajas_hoja[i]
                nb, bx0, by0, bx1, by1 = self._cajas_hoja[j]
                # contencion: uno adentro del otro, con su margen
                dentro = ((ax0 >= bx0 - 1.5 and ax1 <= bx1 + 1.5
                           and ay0 >= by0 - 1.5 and ay1 <= by1 + 1.5)
                          or (bx0 >= ax0 - 1.5 and bx1 <= ax1 + 1.5
                              and by0 >= ay0 - 1.5 and by1 <= ay1 + 1.5))
                if dentro:
                    continue
                sx = min(ax1, bx1) - max(ax0, bx0) - holgura_mm
                sy = min(ay1, by1) - max(ay0, by0) - holgura_mm
                if sx > 0 and sy > 0:
                    ch.append((na, nb, round(sx, 1), round(sy, 1)))
        return ch

    def _render_dxf(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = ezdxf.new(setup=True)
        doc.units = ezdxf.units.M
        for nombre, cfg in CAPAS.items():
            if nombre not in doc.layers:
                doc.layers.add(nombre, color=cfg["aci"])
        msp = doc.modelspace()
        h_txt_m = self.mm2m(1.0)  # 1 mm de hoja en metros de modelo
        for pr in self.prims:
            if pr.pm is None:          # mobiliario de hoja: no va al DXF
                continue
            at = {"layer": pr.layer}
            if pr.kind == "line":
                msp.add_line(pr.pm[0], pr.pm[1], dxfattribs=at)
            elif pr.kind == "poly":
                msp.add_lwpolyline(pr.pm, close=pr.opts.get("cerrar", True),
                                   dxfattribs=at)
            elif pr.kind == "circle":
                msp.add_circle(pr.pm[0], pr.opts["r"], dxfattribs=at)
            elif pr.kind == "arc":
                msp.add_arc(pr.pm[0], pr.opts["r"], pr.opts["a0"], pr.opts["a1"],
                            dxfattribs=at)
            elif pr.kind == "text":
                t = msp.add_text(_sin_tildes(str(pr.opts["s"])).replace("\n", " "),
                                 height=pr.opts["h_mm"] * h_txt_m,
                                 rotation=pr.opts.get("rot", 0.0),
                                 dxfattribs=at)
                t.set_placement(pr.pm[0],
                                align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        doc.saveas(path)
        return path


# ===========================================================================
# RENDER matplotlib de una primitiva
# ===========================================================================
def _render_mpl(ax, pr: Prim) -> None:
    cfg = _capa(pr.layer)
    color = pr.opts.get("color") or cfg["c"]
    lw = pr.opts.get("lw", cfg["lw"])
    z = pr.opts.get("zorder")
    if pr.kind == "line":
        (x0, y0), (x1, y1) = pr.ph
        ax.plot([x0, x1], [y0, y1], color=color, lw=lw,
                ls=pr.opts.get("ls", "-"), solid_capstyle="round",
                zorder=z if z is not None else 4)
    elif pr.kind == "poly":
        fc = pr.opts.get("fc", "none")
        ax.add_patch(Polygon(pr.ph, closed=pr.opts.get("cerrar", True),
                             facecolor=fc, edgecolor=color, lw=lw,
                             ls=pr.opts.get("ls", "-"),
                             hatch=pr.opts.get("hatch"),
                             zorder=z if z is not None else (2 if fc != "none" else 4)))
    elif pr.kind == "circle":
        ax.add_patch(Circle(pr.ph[0], pr.opts["_r_mm"],
                            facecolor=pr.opts.get("fc", "none"),
                            edgecolor=color, lw=lw,
                            zorder=z if z is not None else 8))
    elif pr.kind == "arc":
        d = 2 * pr.opts["_r_mm"]
        ax.add_patch(Arc(pr.ph[0], d, d, angle=0.0, theta1=pr.opts["a0"],
                         theta2=pr.opts["a1"], color=color, lw=lw,
                         zorder=z if z is not None else 6))
    elif pr.kind == "text":
        bbox = pr.opts.get("bbox")
        ax.text(pr.ph[0][0], pr.ph[0][1], pr.opts["s"],
                fontsize=pr.opts["h_mm"] * MM_A_PT,
                ha=pr.opts.get("ha", "center"), va=pr.opts.get("va", "center"),
                rotation=pr.opts.get("rot", 0.0), color=color,
                fontweight=pr.opts.get("weight", "normal"),
                bbox=bbox, zorder=z if z is not None else 20,
                rotation_mode="anchor")


# ===========================================================================
# UTILIDADES
# ===========================================================================
def _wrap(s: str, n: int) -> list[str]:
    palabras = str(s).split()
    lineas: list[str] = []
    act = ""
    for p in palabras:
        if len(act) + len(p) + 1 <= n:
            act = (act + " " + p).strip()
        else:
            if act:
                lineas.append(act)
            act = p
    if act:
        lineas.append(act)
    return lineas or [""]


def _slug(s: str) -> str:
    s = _sin_tildes(s).lower()
    out = []
    for ch in s:
        out.append(ch if ch.isalnum() else "_")
    r = "".join(out)
    while "__" in r:
        r = r.replace("__", "_")
    return r.strip("_")[:48]


_TILDES = str.maketrans("áéíóúÁÉÍÓÚñÑüÜ°²³", "aeiouAEIOUnNuU023")


def _sin_tildes(s: str) -> str:
    return s.translate(_TILDES)
