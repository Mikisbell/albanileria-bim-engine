# -*- coding: utf-8 -*-
"""Cuatro verificaciones normativas, dibujadas.

POR QUE
=======
Mikis, 2026-09-21: *"el ojo humano aprende más viendo que leyendo"*. Estas
cuatro eran tablas de números, y las cuatro responden a la misma pregunta
—¿cumple o no, y por cuánto?—, que es exactamente lo que un gráfico con una
línea de límite contesta de un vistazo.

  DENSIDAD      ΣL·t/Ap contra el mínimo del 7.1.2.b, por dirección.
  RESISTENCIA   ΣVm contra VE: el control global del 8.5.4.
  LOSA          El peralte del aligerado contra la Tabla 9.1 de la E.060,
                paño por paño, y contra la regla de dedo «L/25» que NO es
                norma y da un 35 % menos.
  INVALIDANTES  Las condiciones que, de fallar una, invalidan el trabajo.
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
import estilo as E                                             # noqa: E402
import matplotlib                                              # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches                                # noqa: E402
from proyecto import (MUROS, ESPESOR, AREA_PLANTA, PANOS_Y,    # noqa: E402
                      E_LOSA, N_PISOS, Z, U, S, machones,
                      AREA_EDIFICADA, FRENTE_LOTE, LONG_MINIMA)

VERDE = "#2e7d52"
ROJO = "#b02a1f"
AMBAR = "#c98a16"
GRIS = "#9fb0bd"
AZUL = "#1f5fbf"


def cargar(nombre):
    ruta = os.path.join(AQUI, "..", "calculo", nombre)
    spec = importlib.util.spec_from_file_location("_v" + nombre[:2], ruta)
    mod = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def guardar(fig, nombre):
    """Delega en cuadro.guardar(), que MIDE. Ver el porque arriba."""
    return C.guardar(fig, os.path.join(R.INFORME, nombre))


def limpiar(ax):
    ax.grid(axis="y", color="#dde3e8", lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


# ======================================================================
def densidad():
    """ΣL·t/Ap contra el mínimo del 7.1.2.b, por dirección."""
    m01 = cargar("01_arquitectura_y_densidad.py")
    with contextlib.redirect_stdout(_io.StringIO()):
        req = m01.densidad_requerida()
    areas = {}
    for dire in ("X", "Y"):
        tot = 0.0
        for nom, d, L, t, vs in MUROS:
            if d != dire:
                continue
            corto = nom.split()[0]
            for a, b in machones(corto, d, L, vs):
                if b - a >= 1.20 - 1e-9:      # el 6.4: solo los que cuentan
                    tot += (b - a) * t
        areas[dire] = tot
    A_req = req * AREA_PLANTA

    _PIE = (u"Sólo cuentan los machones de %.2f m o más (E.070 " % LONG_MINIMA +
            u"6.4): un vano parte el muro y los trozos cortos no "
            u"contribuyen. Con esa cuenta, las dos direcciones superan el "
            u"mínimo con más del 130 % de holgura.")
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 5.20), dpi=200)
    y_ar, y_ab = C.marco(fig, u"Densidad de muros  ·  E.070 7.1.2.b",
                         pie=_PIE)
    ax = fig.add_axes((0.145, y_ab, 0.82, y_ar - y_ab - 0.03))
    xs = [0, 1]
    vals = [areas["X"], areas["Y"]]
    ax.bar(xs, vals, 0.5, color=[AZUL, "#c0560f"])
    ax.axhline(A_req, color=ROJO, lw=2.0, ls="--")
    ax.annotate("mínimo exigido  %.3f m²   (Z·U·S·N/56 · Ap)" % A_req,
                (0.5, A_req), xytext=(-0.30, A_req * 1.10), fontsize=9.5,
                color=ROJO, fontweight="bold")
    for x, v in zip(xs, vals):
        ax.annotate("%.2f m²\n+%.0f %% de holgura"
                    % (v, 100.0 * (v / A_req - 1)),
                    (x, v), xytext=(x, v * 1.02), ha="center", fontsize=9.5,
                    color=E.TINTA, fontweight="bold")
    ax.set_xticks(xs)
    ax.set_xticklabels(["dirección X-X", "dirección Y-Y"], fontsize=10)
    ax.set_ylabel("área de corte  Σ L·t  (m²)", fontsize=9)
    ax.set_ylim(0, max(vals) * 1.28)
    limpiar(ax)
    guardar(fig, "DENSIDAD-DE-MUROS.png")
    return areas, A_req


# ======================================================================
def resistencia_global():
    """ΣVm contra VE: el control del 8.5.4, por dirección."""
    m18 = cargar("18_diseno_muros.py")
    with contextlib.redirect_stdout(_io.StringIO()):
        muros, _ad = m18.disenar()
        _m, V_ent = m18.datos()
    VE = V_ent[0]
    sVm = {}
    for dire in ("X", "Y"):
        sVm[dire] = sum(mu["Vm1"] for mu in muros if mu["dir"] == dire)

    _PIE = (u"El 8.5.4 pide que la suma de las resistencias al corte de "
            u"los muros de una dirección supere el cortante del sismo "
            u"SEVERO. Se excluyen los muros de menos de %.2f m, que la "
            % LONG_MINIMA +
            u"norma no deja contar.")
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 5.20), dpi=200)
    y_ar, y_ab = C.marco(
        fig, u"Resistencia al corte del edificio  ·  E.070 8.5.4 "
        u"(ΣVm ≥ VE)", pie=_PIE)
    ax = fig.add_axes((0.145, y_ab, 0.82, y_ar - y_ab - 0.03))
    w = 0.34
    for k, dire in enumerate(("X", "Y")):
        ax.bar(k - w / 2, sVm[dire] / 1000.0, w, color=VERDE,
               label="ΣVm disponible" if k == 0 else None)
        ax.bar(k + w / 2, VE / 1000.0, w, color=ROJO,
               label="VE demandado (sismo severo)" if k == 0 else None)
        ax.annotate("%.2f×" % (sVm[dire] / VE), (k, sVm[dire] / 1000.0),
                    xytext=(k, sVm[dire] / 1000.0 * 1.03), ha="center",
                    fontsize=11, color=E.TINTA, fontweight="bold")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["dirección X-X", "dirección Y-Y"], fontsize=10)
    ax.set_ylabel("cortante  (tonf)", fontsize=9)
    ax.set_ylim(0, max(sVm.values()) / 1000.0 * 1.22)
    ax.legend(fontsize=8.5, frameon=False, loc="upper right")
    limpiar(ax)
    guardar(fig, "RESISTENCIA-GLOBAL.png")
    return sVm, VE


# ======================================================================
def peralte_de_losa():
    """El aligerado contra la Tabla 9.1, paño por paño. Y la regla de dedo."""
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 8.50), dpi=220, facecolor="white")
    fig.suptitle(
        "PREDIMENSIONAMIENTO DE LOSA ALIGERADA: ANÁLISIS PAÑO POR PAÑO SEGÚN NTE E.060\n"
        "Verificación del Peralte Mínimo (Tabla 9.1) frente al Riesgo de la Regla Empírica «L/25»",
        fontsize=12.5, fontweight="bold", color="#0f172a", y=0.965
    , wrap=True)

    ax = fig.add_axes([0.08, 0.28, 0.88, 0.55])
    n = len(PANOS_Y)
    xs = list(range(n))
    div = [18.5 if k in (0, n - 1) else 21.0 for k in range(n)]
    exig = [L / d for L, d in zip(PANOS_Y, div)]
    dedo = [L / 25.0 for L in PANOS_Y]

    w = 0.32
    ax.bar([x - 0.18 for x in xs], exig, width=w, color="#c2410c", edgecolor="#9a3412",
           linewidth=1.0, label="Norma E.060 Tabla 9.1 (L/18.5 extremo fachada | L/21 interior)", zorder=3)
    ax.bar([x + 0.18 for x in xs], dedo, width=w, color="#94a3b8", edgecolor="#475569",
           linewidth=1.0, label="Regla de dedo empírica «L/25» (NO autorizada por norma)", zorder=3)

    # Línea adoptada detrás de las etiquetas numéricas
    ax.axhline(E_LOSA, color="#15803d", linestyle="--", linewidth=2.2, zorder=2)

    # Badge adoptado en esquina superior derecha
    ax.text(0.98, 0.72, f"PERALTE ADOPTADO: h = {E_LOSA:.2f} m ({E_LOSA*100:.0f} cm)\n— CUMPLE EN TODOS LOS PAÑOS —",
            transform=ax.transAxes, ha="right", va="top", fontsize=9.2, fontweight="bold", color="#14532d",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#dcfce7", edgecolor="#16a34a", lw=1.2), zorder=5)

    # Números en barras con fondo blanco de protección
    for i in range(n):
        v1 = exig[i]
        v2 = dedo[i]
        if i == 2:
            txt1 = f"{v1*100:.1f} cm (RIGE)\n[exigido: {v1:.3f} m]"
            y_pos1 = v1 + 0.008
            col_t1 = "#9a3412"
            bbox_dict = dict(boxstyle="round,pad=0.2", facecolor="#fff7ed", edgecolor="#ea580c", lw=1.0)
        else:
            txt1 = f"{v1*100:.1f} cm\n({v1:.3f} m)"
            y_pos1 = v1 + 0.005
            col_t1 = "#9a3412"
            bbox_dict = dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.95)

        ax.text(xs[i] - 0.18, y_pos1, txt1, ha="center", va="bottom", fontsize=8.5,
                fontweight="bold", color=col_t1, bbox=bbox_dict, zorder=6)

        ax.text(xs[i] + 0.18, v2 + 0.004, f"{v2*100:.1f} cm\n({v2:.3f} m)",
                ha="center", va="bottom", fontsize=8.2, fontweight="bold", color="#334155",
                bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.90), zorder=6)

    # TRES RENGLONES CORTOS y no dos largos: seis etiquetas de 44
    # caracteres se montan de a pares en el ancho de la hoja.
    _N = chr(10)
    # LAS LUCES SE RESTAN DE LOS EJES, que es de donde sale el grafico.
    # Escritas a mano eran una segunda fuente del mismo numero, y la
    # segunda fuente es siempre la que envejece.
    _luces = list(PANOS_Y)
    _n = len(_luces)
    etiquetas = []
    _rige = max(range(_n), key=lambda k: _luces[k])
    for k, _L in enumerate(_luces):
        _borde = k in (0, _n - 1)
        _tit = "Paño %d%s" % (k + 1, "  [RIGE]" if k == _rige else "")
        etiquetas.append(_tit + _N + ("Extremo" if _borde else "Interior")
                         + _N + "%.2f m · L/%s" % (_L, "18,5" if _borde
                                                   else "21"))
    ax.set_xticks(xs)
    ax.set_xticklabels(etiquetas, fontsize=7.4, fontweight="bold",
                       color="#1e293b", linespacing=1.3)
    ax.set_ylabel("Peralte Mínimo de Losa h (m)", fontsize=10.5, fontweight="bold", color="#1e293b")
    ax.set_ylim(0, 0.360)
    ax.grid(axis="y", linestyle=":", alpha=0.7, color="#94a3b8", zorder=1)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9.0, framealpha=0.95, edgecolor="#cbd5e1")

    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#64748b")
    ax.spines["bottom"].set_color("#64748b")

    # Banner técnico inferior
    banner_ax = fig.add_axes([0.08, 0.03, 0.88, 0.19])
    banner_ax.axis("off")
    rect = patches.FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.015,rounding_size=0.025",
                                  facecolor="#f8fafc", edgecolor="#cbd5e1", linewidth=1.1,
                                  transform=banner_ax.transAxes, zorder=1)
    banner_ax.add_patch(rect)

    peor = max(exig)
    _k = exig.index(peor)
    pct_error = 100.0 * (1 - dedo[_k] / peor)

    banner_text = (
        "FUNDAMENTACIÓN NORMATIVA Y CONTROL DE FLECHAS (NTE E.060 CONCRETO ARMADO):\n"
        " • Condición de Apoyo (Tabla 9.1): Los paños extremos (1 y 6) apoyan sobre muro de fachada con un solo extremo continuo, por lo que la norma castiga con L/18,5 (18,2 cm).\n"
        f" • Paño Gobernante: Rige el paño de mayor luz (L = {max(PANOS_Y):.2f} m, junto al pozo de luz), demandando h = {peor:.3f} m ({peor * 100:.1f} cm). Los paños interiores con doble continuidad usan L/21 (16,0 cm).\n"
        f" • Deficiencia de la Regla «L/25»: La práctica informal de usar L/25 arrojaría h = {dedo[_k]:.3f} m (16,8 cm), subdimensionando la losa en un {pct_error:.0f} % y arriesgando fisuras en tabiquería.\n"
        f" • DECISIÓN ESTRUCTURAL: Se adopta losa aligerada unidireccional estándar de h = {E_LOSA:.2f} m ({E_LOSA*100:.0f} cm) con viguetas de 10 cm cada 40 cm y bovedilla de 15 cm."
    )
    # ENVUELTO VINETA POR VINETA: en una linea cada una medía 180
    # caracteres y ensanchaba la figura 4,76 pulgadas.
    _y = 0.94
    for _par in banner_text.split(chr(10)):
        _sangria = "   " if _par.strip().startswith("•") else ""
        for _q, _l in enumerate(C.envolver(banner_ax, _par.strip(), 7.6,
                                           0.955)):
            banner_ax.text(0.012, _y, ("" if _q == 0 else _sangria) + _l,
                           fontsize=7.6, color="#1e293b", va="top",
                           ha="left", transform=banner_ax.transAxes,
                           zorder=2)
            _y -= 0.105
        _y -= 0.02

    guardar(fig, "PERALTE-DE-LOSA.png")
    return exig, dedo


# ======================================================================
def invalidantes():
    """Las condiciones que, si falla una, invalidan el trabajo entero."""
    filas = [
        ("Mínimo 5 pisos", N_PISOS, 5, "pisos", N_PISOS >= 5),
        ("Área techada ≥ 200 m²", AREA_PLANTA, 200.0, "m²",
         AREA_PLANTA >= 200.0),
        ("Zona sísmica 2  (Z = 0,25)", Z, 0.25, "", abs(Z - 0.25) < 1e-9),
        ("Terreno medianero", FRENTE_LOTE, FRENTE_LOTE, "m de frente", True),
    ]
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 3.90), dpi=200)
    fig.suptitle("Las cuatro condiciones invalidantes de la consigna",
                 fontsize=13.5, fontweight="bold", color=E.TINTA, wrap=True)
    ax = fig.add_axes((0.04, 0.08, 0.92, 0.72))
    ax.axis("off")
    for k, (nom, val, req, uni, ok) in enumerate(filas):
        y = 0.80 - k * 0.22
        col = VERDE if ok else ROJO
        ax.add_patch(plt.Rectangle((0.02, y - 0.075), 0.96, 0.16,
                                   fc=("#eaf5ee" if ok else "#fdecea"),
                                   ec=col, lw=1.4))
        ax.text(0.05, y, nom, fontsize=9.8, va="center", color=E.TINTA,
                fontweight="bold")
        ax.text(0.575, y, ("%.2f %s" % (val, uni) if isinstance(val, float)
                           else "%s %s" % (val, uni)),
                fontsize=9.5, va="center", color=E.TINTA)
        ax.text(0.905, y, "CUMPLE" if ok else "NO CUMPLE", fontsize=9.5,
                va="center", ha="center", color=col, fontweight="bold")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    guardar(fig, "INVALIDANTES.png")
    return filas


def main():
    ar, A_req = densidad()
    sVm, VE = resistencia_global()
    exig, dedo = peralte_de_losa()
    inval = invalidantes()
    print()
    control(ar, A_req, sVm, VE, exig, dedo, inval)


def control(ar, A_req, sVm, VE, exig, dedo, inval):
    # cada figura AFIRMA que algo cumple: hay que comprobarlo
    for d, v in ar.items():
        assert v > A_req, ("la direccion %s tiene %.3f m2 y el minimo es "
                           "%.3f" % (d, v, A_req))
    for d, v in sVm.items():
        assert v > VE, ("la direccion %s suma Vm = %.0f y VE = %.0f"
                        % (d, v, VE))
    assert E_LOSA >= max(exig) - 1e-9, (
        "el peralte adoptado %.2f no llega al exigido %.3f" % (E_LOSA,
                                                               max(exig)))
    # y que la regla de dedo de MENOS que la norma, que es lo que la nota dice
    assert max(dedo) < max(exig), (
        "la figura dice que la regla de dedo queda corta y no lo hace")
    for nom, val, req, uni, ok in inval:
        assert ok, ("el invalidante %r no se cumple" % nom)
    print("  [ok] densidad: X %.2f y Y %.2f m2 contra el minimo %.3f"
          % (ar["X"], ar["Y"], A_req))
    print("  [ok] 8.5.4: X %.2fx y Y %.2fx el cortante severo"
          % (sVm["X"] / VE, sVm["Y"] / VE))
    print("  [ok] losa: adoptado %.2f m >= exigido %.3f m"
          % (E_LOSA, max(exig)))
    print("  [ok] los %d invalidantes cumplen" % len(inval))


if __name__ == "__main__":
    main()
