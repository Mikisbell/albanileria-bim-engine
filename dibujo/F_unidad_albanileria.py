# -*- coding: utf-8 -*-
"""La unidad de albañilería: por qué el nombre comercial no clasifica.

QUE PIDE LA CONSIGNA
====================
El apartado 3.2 se apoya en las pp. 37-56 del libro de San Bartolomé, Quiun
y Silva, que son el capítulo «Componentes de la albañilería».

DISEÑO SENIOR Y LEGIBILIDAD
===========================
El gráfico demuestra dos hechos cruciales de la práctica peruana:
1. De 5 marcas comerciales vendidas con el nombre «King Kong 18 huecos»,
   4 superan el 45 % de vacíos y están PROHIBIDAS para muros portantes
   según la E.070 (Art. 2.1.26 y Tabla 2). Solo 1 cumple (Tayson, vacíos = 30 %).
2. El peso en balanza delata a las que callan el dato: las sólidas pesan ≥ 3,75 kg,
   mientras que las huecas pesan ≤ 2,95 kg (~1 kg menos de arcilla).
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
import matplotlib.pyplot as plt                                # noqa: E402
import matplotlib.patches as patches                           # noqa: E402

COLOR_OK = "#1b5e20"       # Verde oscuro texto
COLOR_BAD = "#b71c1c"      # Rojo oscuro texto
COLOR_BAR_OK = "#2e7d32"   # Verde esmeralda barra
COLOR_BAR_BAD = "#c62828"  # Rojo carmesí barra
COLOR_LINE = "#d97706"     # Ámbar profesional


def _renglon_unidad_adoptada():
    """La unidad adoptada, leida de las fichas SOLIDAS del script 13."""
    import importlib
    import proyecto as P
    with contextlib.redirect_stdout(_io.StringIO()):
        m13 = importlib.import_module("13_unidad_albanileria")
    sol = [f for f in m13.FICHAS if f[1] == "SOLIDO"]
    tipos = {f[8] for f in sol}
    assert len(tipos) == 1, tipos
    return (" • UNIDAD ADOPTADA: King Kong sólido Tipo %s — f'b ≥ %.0f y f'm = %.0f kgf/cm², "
            "vacíos ≤ %.0f %%, %s a %s kg."
            % (tipos.pop(), min(f[9] for f in sol), P.FM, m13.VACIOS_MAXIMOS,
               C.coma(min(f[5] for f in sol), 2), C.coma(max(f[6] for f in sol), 2)))


def datos():
    """Las fichas de fabricante ya clasificadas, del script 13."""
    ruta = os.path.join(AQUI, "..", "calculo", "13_unidad_albanileria.py")
    spec = importlib.util.spec_from_file_location("_m13", ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
        rho = m.calibracion()
        filas = m.tabla(rho)
    return m, filas


def main():
    m, filas = datos()
    lim = m.VACIOS_MAXIMOS

    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 9.50), dpi=220, facecolor="white")

    # Título Principal Superior
    fig.suptitle(
        "CLASIFICACIÓN DE LA UNIDAD DE ALBAÑILERÍA SEGÚN LA NORMA TÉCNICA E.070 (ART. 2.1.26)\n"
        "El Nombre Comercial no Clasifica: Análisis del Área Neta y Control de Calidad por Peso",
        fontsize=10.5, fontweight="bold", color="#0f172a", y=0.975,
        wrap=True
    )

    # -------------------------------------------------------------
    # (a) % de vacíos contra el umbral del Art. 2.1.26
    # -------------------------------------------------------------
    ax1 = fig.add_axes([0.115, 0.585, 0.85, 0.285])

    # EL ROTULO SE DERIVA DEL DATO, no se escribe al lado. Esta lista
    # estaba a mano, en paralelo a `filas`, y sus siete nombres largos se
    # pisaban unos con otros: el auditor de textos midio cinco pares, uno
    # con 46 % de solape. Ahora se abrevia de forma mecanica -- la primera
    # palabra de la marca y la familia en la segunda linea -- y queda
    # horizontal, que es lo que se lee sin girar la hoja.
    def _corto(f):
        marca = f["nom"].split()[0].rstrip(",")
        fam = "18H" if f["fam"] == "18 huecos" else "SÓLIDO"
        return marca + chr(10) + fam

    nombres_display = [_corto(f) for f in filas]
    assert len(set(nombres_display)) == len(nombres_display), (
        "dos unidades quedarian con el mismo rotulo: %s"
        % nombres_display)

    vacios = [f["v"] for f in filas]
    colores = [COLOR_BAR_OK if f["solida"] else COLOR_BAR_BAD for f in filas]

    bars = ax1.bar(range(len(filas)), vacios, width=0.58, color=colores,
                   edgecolor="#1e293b", linewidth=0.9, zorder=3)

    # Línea de umbral normativo del 30%
    ax1.axhline(lim, color=COLOR_LINE, linestyle="--", linewidth=2.0, zorder=4)

    # Badge distintivo de la línea normativa (esquina superior izquierda libre)
    ax1.text(0.03, 0.94, f"— — Límite Normativo E.070: Vacíos ≤ {lim:.0f} % (Unidad SÓLIDA)",
             transform=ax1.transAxes, fontsize=9.2, fontweight="bold", color="#9a3412",
             bbox=dict(boxstyle="round,pad=0.35", facecolor="#fef3c7", edgecolor="#f59e0b",
                       lw=1.1, alpha=0.95), zorder=5)

    # Anotaciones numéricas y de estado en cada barra
    for b, f in zip(bars, filas):
        v = f["v"]
        # Porcentaje exacto en la cima de la barra
        ax1.text(b.get_x() + b.get_width() / 2.0, v + 1.2, f"{v:.1f} %",
                 ha="center", va="bottom", fontsize=10.0, fontweight="bold",
                 color="#0f172a", zorder=5)

        # Estado normativo dentro de la barra (sin colisionar con la línea del 30%)
        if f["solida"]:
            ax1.text(b.get_x() + b.get_width() / 2.0, 15.0, "SÓLIDA",
                     ha="center", va="center", fontsize=9.0, fontweight="bold",
                     color="white", zorder=5)
        else:
            ax1.text(b.get_x() + b.get_width() / 2.0, 37.0, "HUECA",
                     ha="center", va="center", fontsize=9.0, fontweight="bold",
                     color="white", zorder=5)

    ax1.set_xticks(range(len(filas)))
    ax1.set_xticklabels(nombres_display, rotation=0, ha="center", fontsize=8.4,
                       fontweight="bold", color="#1e293b")
    ax1.set_ylabel("Porcentaje de Vacíos (%)", fontsize=10.5, fontweight="bold",
                   color="#1e293b")
    ax1.set_ylim(0, 60)
    ax1.set_xlim(-0.6, len(filas) - 0.4)
    ax1.grid(axis="y", linestyle=":", alpha=0.7, color="#94a3b8", zorder=1)
    ax1.set_axisbelow(True)

    h18 = [f for f in filas if f["fam"] == "18 huecos"]
    ok18 = [f for f in h18 if f["solida"]]
    ax1.set_title(f"(a) % de Vacíos vs. Límite E.070: {len(h18)} marcas «18 Huecos» (Solo {len(ok18)} cumple)",
                  fontsize=10.5, fontweight="bold", color="#0f172a", loc="left", pad=10)

    for spine in ["top", "right"]:
        ax1.spines[spine].set_visible(False)
    ax1.spines["left"].set_color("#64748b")
    ax1.spines["bottom"].set_color("#64748b")

    # -------------------------------------------------------------
    # (b) Dispersión: el peso en balanza delata a la unidad
    # -------------------------------------------------------------
    ax2 = fig.add_axes([0.115, 0.220, 0.85, 0.235])

    # Zonas de fondo sombreadas
    ax2.axhspan(30.0, 54.0, xmin=0.0, xmax=0.48, color="#fee2e2", alpha=0.55, zorder=1)
    ax2.axhspan(18.0, 30.0, xmin=0.68, xmax=1.0, color="#dcfce7", alpha=0.55, zorder=1)

    # Línea horizontal del límite
    ax2.axhline(lim, color=COLOR_LINE, linestyle="--", linewidth=1.8, zorder=2)

    for f in filas:
        c = COLOR_BAR_OK if f["solida"] else COLOR_BAR_BAD
        ax2.scatter(f["peso"], f["v"], color=c, s=135, edgecolor="#0f172a",
                    linewidth=1.1, zorder=4)

    # Cajas explicativas (callouts) con flechas hacia los grupos de puntos
    ax2.annotate("LADRILLOS HUECOS (4 marcas)\n• Peso: 2.70 a 2.95 kg\n• Vacíos: 45.8 % a 46.5 %\n• PROHIBIDOS (Art. 2.1.26)",
                 xy=(2.78, 46.2), xytext=(2.55, 34.5),
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="#fff1f2", edgecolor="#e11d48", lw=1.2),
                 arrowprops=dict(arrowstyle="->", color="#e11d48", lw=1.4, shrinkA=3, shrinkB=6),
                 fontsize=8.2, fontweight="bold", color="#9f1239", ha="left", zorder=6)

    ax2.annotate("LADRILLOS SÓLIDOS (3 marcas)\n• Peso: 3.75 a 3.85 kg\n• Vacíos: 30.0 % (Clase IV y V)\n• ADMITIDOS EN ZONA 2",
                 xy=(3.80, 30.0), xytext=(3.12, 22.0),
                 bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0fdf4", edgecolor="#16a34a", lw=1.2),
                 arrowprops=dict(arrowstyle="->", color="#16a34a", lw=1.4, shrinkA=3, shrinkB=6),
                 fontsize=8.2, fontweight="bold", color="#14532d", ha="left", zorder=6)

    ax2.set_xlabel("Peso de la Unidad (kg)", fontsize=10.5, fontweight="bold", color="#1e293b")
    ax2.set_ylabel("Porcentaje de Vacíos (%)", fontsize=10.5, fontweight="bold", color="#1e293b")
    ax2.set_xlim(2.50, 4.05)
    ax2.set_ylim(18, 54)
    ax2.grid(True, linestyle=":", alpha=0.6, color="#94a3b8", zorder=1)
    ax2.set_axisbelow(True)
    ax2.set_title("(b) Correlación: Peso (kg) vs. % Vacíos",
                  fontsize=10.5, fontweight="bold", color="#0f172a", loc="left", pad=10)

    for spine in ["top", "right"]:
        ax2.spines[spine].set_visible(False)
    ax2.spines["left"].set_color("#64748b")
    ax2.spines["bottom"].set_color("#64748b")

    # -------------------------------------------------------------
    # Banner Inferior: Tarjeta Ejecutiva de Criterio Normativo
    # -------------------------------------------------------------
    banner_ax = fig.add_axes([0.075, 0.025, 0.89, 0.145])
    banner_ax.axis("off")

    rect = patches.FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.015,rounding_size=0.025",
                                  facecolor="#f8fafc", edgecolor="#cbd5e1", linewidth=1.1,
                                  transform=banner_ax.transAxes, zorder=1)
    banner_ax.add_patch(rect)

    # EL RENGLON DE LA UNIDAD SE DERIVA. Decia «Clase V (f'b = 130)»: 130 es
    # el minimo de la Clase IV; la V exige 180 (E.070 Tabla 1), que es lo que
    # declaran las dos fichas solidas del script 13. Y el peso era 3,80 cuando
    # las fichas dan 3,70 a 4,00. Tecleado, nadie lo vio en dos semanas.
    banner_text = (
        "DICTAMEN TÉCNICO Y CRITERIO NORMATIVO (NTE E.070 ALBAÑILERÍA):\n"
        " • Definición Normativa (Art. 2.1.26): La unidad SÓLIDA se define por tener área de alvéolos ≤ 30 % del área bruta. Si supera 30 %, es clasificada como HUECA.\n"
        " • Exigencia Sísmica (Tabla 2): En Zona Sísmica 2, 3 y 4 está estrictamente PROHIBIDO el uso de unidad hueca en muros portantes para edificios de 4 a más pisos.\n"
        " • Trampa del Mercado: De 5 marcas comerciales vendidas como «King Kong 18 Huecos», 4 son huecas (vacíos ~46 %) y solo 1 cumple (Tayson, vacíos = 30 %).\n"
        " • Control de Recepción en Obra: Una balanza de precisión delata la unidad. Las sólidas pesan ≥ 3.75 kg; las huecas pesan ≤ 2.95 kg (~1 kg menos de arcilla).\n"
        + _renglon_unidad_adoptada()
    )

    # ENVUELTO VINETA POR VINETA: en una linea cada una medía hasta
    # 190 caracteres y ensanchaba la figura varias pulgadas.
    _y = 0.94
    for _par in banner_text.split(chr(10)):
        _sang = "   " if _par.strip().startswith("•") else ""
        for _q, _l in enumerate(C.envolver(banner_ax, _par.strip(),
                                            7.4, 0.905)):
            banner_ax.text(0.015, _y, ("" if _q == 0 else _sang) + _l,
                           fontsize=7.4, color="#1e293b", va="top",
                           ha="left", transform=banner_ax.transAxes,
                           zorder=2)
            _y -= 0.082
        _y -= 0.016

    out = os.path.join(R.INFORME, "UNIDAD-ALBANILERIA.png")
    fig.savefig(out, dpi=220, facecolor="white", bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)
    print("  %s" % os.path.basename(out))
    print()
    control(filas, lim)


def control(filas, lim):
    assert filas, "no se leyo ninguna ficha de fabricante"
    ok = [f["nom"] for f in filas if f["solida"]]
    no = [f["nom"] for f in filas if not f["solida"]]
    assert ok and no, (
        "la figura afirma que unas cumplen y otras no, y todas son %s"
        % ("solidas" if ok else "huecas"))
    for f in filas:
        esperado = f["v"] <= lim + 1e-9
        assert f["solida"] == esperado, (
            "%s: clasificada %s con %.1f %% de vacios contra el umbral %.0f"
            % (f["nom"], "solida" if f["solida"] else "hueca",
               f["v"], lim))
    print("  [ok] %d fichas: %d admitidas y %d prohibidas por el 2.1.26"
          % (len(filas), len(ok), len(no)))
    print("  [ok] la clasificacion coincide con el umbral de %.0f %% en todas"
          % lim)
    h18 = [f for f in filas if f["fam"] == "18 huecos"]
    ok18 = [f for f in h18 if f["solida"]]
    assert len(h18) >= 3 and len(ok18) < len(h18), (
        "el titulo afirma que de %d unidades con el mismo nombre solo %d "
        "sirve: no se sostiene" % (len(h18), len(ok18)))
    print("  [ok] familia '18 huecos': %d fichas, %d admitida(s) -- el "
          "titulo lo dice derivado" % (len(h18), len(ok18)))


if __name__ == "__main__":
    main()
