# -*- coding: utf-8 -*-
"""Figura isométrica 3D del modelo estructural OpenSeesPy.

Genera un renderizado 3D de alta resolución (PNG) que muestra la volumetría
estructural completa del edificio de 5 niveles:
  - 13 muros portantes confinados con sus longitudes y espesores reales
  - 5 diafragmas rígidos (losas aligeradas con el pozo de luz central)
  - Centros de masa y enlaces rígidos del diafragma (ops.rigidDiaphragm)
  - Ejes y dimensiones globales (11,90 m x 21,00 m x 13,50 m)
"""
import contextlib
import importlib
import io
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
CALCULO = os.path.join(RAIZ, "calculo")
sys.path.insert(0, CALCULO)
sys.path.insert(0, AQUI)

import rutas as R
import proyecto as P
import cuadro as C
import estilo as E


def datos():
    M20 = importlib.import_module("20_modelo_opensees")
    with contextlib.redirect_stdout(io.StringIO()):
        d, filas, Fi, V, T_emp, pesos, xm, ym = M20.armar()
    return d, xm, ym


def dibujar_caja(ax, x0, y0, z0, dx, dy, dz, color, alpha=0.85, edge_color=None):
    """Dibuja un prisma rectangular 3D (muro o losa)."""
    # 8 vertices
    x = [x0, x0 + dx]
    y = [y0, y0 + dy]
    z = [z0, z0 + dz]
    
    vertices = [
        [[x[0], y[0], z[0]], [x[1], y[0], z[0]], [x[1], y[1], z[0]], [x[0], y[1], z[0]]], # abajo
        [[x[0], y[0], z[1]], [x[1], y[0], z[1]], [x[1], y[1], z[1]], [x[0], y[1], z[1]]], # arriba
        [[x[0], y[0], z[0]], [x[1], y[0], z[0]], [x[1], y[0], z[1]], [x[0], y[0], z[1]]], # frente
        [[x[0], y[1], z[0]], [x[1], y[1], z[0]], [x[1], y[1], z[1]], [x[0], y[1], z[1]]], # atras
        [[x[0], y[0], z[0]], [x[0], y[1], z[0]], [x[0], y[1], z[1]], [x[0], y[0], z[1]]], # izq
        [[x[1], y[0], z[0]], [x[1], y[1], z[0]], [x[1], y[1], z[1]], [x[1], y[0], z[1]]]  # der
    ]
    
    ec = edge_color if edge_color else color
    poly = Poly3DCollection(vertices, facecolors=color, linewidths=0.6,
                            edgecolors=ec, alpha=alpha)
    ax.add_collection3d(poly)


def main():
    d, xm, ym = datos()
    
    fig = plt.figure(figsize=(C.ANCHO_PAGINA, 7.80), dpi=220)
    ax = fig.add_subplot(111, projection="3d")
    
    # Colores sobrios y realistas de Albañilería Confinada (Norma E.070)
    COLOR_LADRILLO = "#c2410c"      # Ladrillo King Kong arcilla cocida (terracota)
    COLOR_LADRILLO_MED = "#b45309"  # Ladrillo medianera con visibilidad volumétrica
    COLOR_CONCRETO = "#64748b"      # Columnas C-1 / C-2 concreto f'c 175 kg/cm2
    COLOR_SOLERA = "#475569"        # Vigas soleras de confinamiento
    COLOR_LOSA = "#94a3b8"          # Losa aligerada (e = 0,20 m)
    COLOR_CM = "#f59e0b"            # Centro de masa (nodo maestro)
    COLOR_ALF = "#c2410c"           # Alféizar de albañilería bajo ventana
    COLOR_VID = "#38bdf8"           # Vidrio arquitectónico translúcido
    COLOR_DIN = "#475569"           # Dintel de concreto armado

    nPisos = P.N_PISOS
    hPiso = P.H_ENTREPISO
    frente = P.FRENTE
    fondo = P.FONDO

    muros_p_map = {m[0]: m for m in P.MUROS}

    # 1. Dibujar Muros de Albañilería Confinada con Columnas, Vigas Soleras y Vanos
    for m in d["muros"]:
        nom = m["nom"]
        p_info = muros_p_map.get(nom)
        L = p_info[2] if p_info else 11.90
        t = p_info[3] if p_info else 0.24
        vanos = p_info[4] if p_info else []

        xc = m["x"] / 100.0
        yc = m["y"] / 100.0
        isX = m["dir"] == "X"
        is_med_right = "medianera derecha" in nom.lower() or "my-2" in nom.lower()
        is_med_left = "medianera izquierda" in nom.lower() or "my-1" in nom.lower()

        # Medianera derecha en primer plano: alpha 0.45 para ver la distribución interior sin perder el muro
        if is_med_right:
            col_ladrillo = COLOR_LADRILLO_MED
            alpha_brick = 0.48
            edge_brick = "#9a3412"
        elif is_med_left:
            col_ladrillo = COLOR_LADRILLO
            alpha_brick = 0.90
            edge_brick = "#7c2d12"
        else:
            col_ladrillo = COLOR_LADRILLO
            alpha_brick = 0.88
            edge_brick = "#7c2d12"

        origX = xc - L / 2.0 if isX else xc
        origY = yc if isX else yc - L / 2.0

        uv = P.vanos_ubicados(nom, m["dir"], L, vanos)
        uv.sort(key=lambda x: x[0])

        # Machones de albañilería
        piers = []
        curr = 0.0
        for x0, w in uv:
            if x0 > curr + 1e-4:
                piers.append((curr, x0))
            curr = x0 + w
        if curr < L - 1e-4:
            piers.append((curr, L))

        # Ejes de columna de confinamiento
        ejes_col = P.ejes_de_columna(nom, m["dir"], L)

        for p in range(nPisos):
            z0 = p * hPiso
            h_brick = hPiso - 0.20  # Altura libre de ladrillo bajo viga solera

            # A. Machones sólidos de albañilería (ladrillo)
            for s, e in piers:
                p_len = e - s
                dx = p_len if isX else t
                dy = t if isX else p_len
                px = origX + s if isX else origX - t / 2.0
                py = origY - t / 2.0 if isX else origY + s
                dibujar_caja(ax, px, py, z0, dx, dy, h_brick, col_ladrillo, alpha=alpha_brick, edge_color=edge_brick)

            # B. Vigas Soleras de concreto armado coronando el muro
            sdx = L if isX else t
            sdy = t if isX else L
            spx = origX if isX else origX - t / 2.0
            spy = origY - t / 2.0 if isX else origY
            dibujar_caja(ax, spx, spy, z0 + h_brick, sdx, sdy, 0.20, COLOR_SOLERA, alpha=0.85, edge_color="#1e293b")

            # C. Columnas de confinamiento (C-1 / C-2)
            for cPos in ejes_col:
                colX = (origX + cPos) if isX else origX
                colY = origY if isX else (origY + cPos)
                is_ext = (abs(colX) < 0.05 or abs(colX - frente) < 0.05)
                dim_l = 0.35 if is_ext else 0.25
                cdx = dim_l if isX else t
                cdy = t if isX else dim_l
                cpx = (colX - dim_l / 2.0) if isX else (colX - t / 2.0)
                cpy = (colY - t / 2.0) if isX else (colY - dim_l / 2.0)
                dibujar_caja(ax, cpx, cpy, z0, cdx, cdy, hPiso, COLOR_CONCRETO, alpha=0.90, edge_color="#1e293b")

            # D. Vanos arquitectónicos (puertas, ventanas, alféizares, vidrios y dinteles)
            for x0, w in uv:
                tipo = P.tipo_de_vano(nom, x0)
                # En la fachada frontal MX-1, el vano de ingreso es PUERTA ÚNICAMENTE en el Piso 1 (p == 0).
                # En los pisos 2 a 5 (p > 0), el hall común no sale a la calle: es una VENTANA
                # protegida con su alféizar de ladrillo de 1,00 m y vidrio translúcido (evita salto al vacío).
                if nom.startswith("MX-1") and tipo == "puerta" and p > 0:
                    tipo = "ventana"

                vx = origX + x0 if isX else origX - t / 2.0
                vy = origY - t / 2.0 if isX else origY + x0
                dx = w if isX else t
                dy = t if isX else w

                # Dintel de concreto (de 2.10m a 2.50m)
                dibujar_caja(ax, vx, vy, z0 + 2.10, dx, dy, 0.40, COLOR_DIN, alpha=0.85, edge_color="#1e293b")

                if tipo == "ventana":
                    # Alféizar de ladrillo (de 0 a 1.00m)
                    dibujar_caja(ax, vx, vy, z0, dx, dy, 1.00, COLOR_ALF, alpha=0.85, edge_color="#7c2d12")
                    # Vidrio arquitectónico translúcido (de 1.00m a 2.10m)
                    dibujar_caja(ax, vx, vy, z0 + 1.00, dx, dy, 1.10, COLOR_VID, alpha=0.40, edge_color="#0284c7")

    # 2. Dibujar Losas Aligeradas (5 niveles) con Pozo de Luz
    # Para dejar el pozo hueco en 3D, dividimos la losa en 4 franjas alrededor del pozo
    px0, px1 = P.POZO_X0, P.POZO_X1
    py0, py1 = P.POZO_Y0, P.POZO_Y1
    
    for p in range(1, nPisos + 1):
        z0 = p * hPiso - 0.18
        dz = 0.18
        
        # Franja frontal (antes del pozo en Y)
        dibujar_caja(ax, 0, 0, z0, frente, py0, dz, COLOR_LOSA, alpha=0.28, edge_color="#64748b")
        # Franja posterior (despues del pozo en Y)
        dibujar_caja(ax, 0, py1, z0, frente, fondo - py1, dz, COLOR_LOSA, alpha=0.28, edge_color="#64748b")
        # Franja lateral izquierda (al costado del pozo)
        dibujar_caja(ax, 0, py0, z0, px0, py1 - py0, dz, COLOR_LOSA, alpha=0.28, edge_color="#64748b")
        # Franja lateral derecha (al costado del pozo)
        dibujar_caja(ax, px1, py0, z0, frente - px1, py1 - py0, dz, COLOR_LOSA, alpha=0.28, edge_color="#64748b")

    # 3. Dibujar Nodos Maestros (Centro de Masa) y Diafragmas Rigidos
    for p in range(1, nPisos + 1):
        zp = p * hPiso
        # Esfera CM
        ax.scatter([xm], [ym], [zp], color=COLOR_CM, s=45, depthshade=False, zorder=10)
        
        # Enlaces radiales a los muros del nivel
        for m in d["muros"]:
            xc = m["x"] / 100.0
            yc = m["y"] / 100.0
            ax.plot([xm, xc], [ym, yc], [zp, zp], color=COLOR_CM,
                    linestyle=":", linewidth=0.7, alpha=0.45)

    # 4. Dibujar Terreno del Lote con Retiros y Estacionamientos
    ret_front = P.RETIRO_FRONTAL    # 5.00 m
    ret_post = P.RETIRO_POSTERIOR   # 4.50 m
    
    # Asfalto del retiro frontal con 4 estacionamientos (12 x 5 m)
    dibujar_caja(ax, 0, -ret_front, -0.05, frente, ret_front, 0.04, "#1e293b", alpha=0.90, edge_color="#334155")
    # Lineas amarillas de los 4 cajones (2.50 x 5.00 m)
    for k in range(1, 4):
        ax.plot([k * 2.97, k * 2.97], [-ret_front + 0.3, -0.3], [-0.01, -0.01],
                color="#facc15", linewidth=1.5, zorder=5)
    
    # Patio posterior (12 x 4.50 m)
    dibujar_caja(ax, 0, fondo, -0.05, frente, ret_post, 0.04, "#14532d", alpha=0.85, edge_color="#166534")

    # 5. Ajustar limites, ejes y vista técnica
    ax.set_xlim(-1, frente + 1)
    ax.set_ylim(-ret_front - 1, fondo + ret_post + 1)
    ax.set_zlim(0, P.HN + 1)
    
    ax.set_xlabel("Frente X (m)", fontsize=8.5, labelpad=8)
    ax.set_ylabel("Fondo Y (m)", fontsize=8.5, labelpad=8)
    ax.set_zlabel("Altura Z (m)", fontsize=8.5, labelpad=6)
    
    ax.view_init(elev=24, azim=-52)
    
    # Titulos y notas tecnicas
    plt.title(
        u"Modelo Tridimensional OpenSeesPy  ·  13 Muros × 5 Niveles con Diafragmas Rígidos\n"
        u"Albañilería Confinada (E.070)  ·  T1 = 0,188 s (X, 81,3 %)  ·  T2 = 0,168 s (Y, 83,6 %)",
        fontsize=10.5, fontweight="bold", color=E.TINTA, pad=12
    )
    
    # Leyenda personalizada
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLOR_LADRILLO, edgecolor="#7c2d12", label=u"Muros de Albañilería (Ladrillo King Kong arcilla)"),
        Patch(facecolor=COLOR_CONCRETO, edgecolor="#1e293b", label=u"Columnas de Confinamiento C-1 / C-2"),
        Patch(facecolor=COLOR_SOLERA, edgecolor="#1e293b", label=u"Vigas Soleras de Confinamiento (e = 0,20 m)"), # tecleado-ok
        Patch(facecolor=COLOR_LOSA, alpha=0.4, edgecolor="#64748b", label=u"Losas Aligeradas (con Pozo de Luz central)"),
        Patch(facecolor="#1e293b", edgecolor="#facc15", label=u"4 Estacionamientos frontales (2,50 × 5,00 m)"), # tecleado-ok
        Line2D([0], [0], marker="o", color="w", markerfacecolor=COLOR_CM, markersize=7, label=u"Centro de Masa (ops.rigidDiaphragm)"),
    ]
    ax.legend(handles=legend_elements, loc="upper left", bbox_to_anchor=(0.01, 0.96),
              fontsize=7.5, framealpha=0.92)

    # Guardar en salidas/
    out_png = os.path.join(R.RAIZ, "salidas", "modelo_3d_opensees.png")
    plt.tight_layout()
    plt.savefig(out_png, dpi=220, bbox_inches="tight")
    plt.close()
    print("  [ok] Generado render isometrico 3D:", out_png)


if __name__ == "__main__":
    main()
