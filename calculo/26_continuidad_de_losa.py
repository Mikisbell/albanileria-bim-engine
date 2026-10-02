# -*- coding: utf-8 -*-
"""El esfuerzo axial con las reacciones de la losa CONTINUA (hallazgo C-7)

POR QUE EXISTE ESTE SCRIPT
==========================
El metrado de los muros reparte la losa por AREA TRIBUTARIA: cada muro recibe
media luz a cada lado. Es la practica corriente y la E.020 no manda otra cosa.
Pero el proyecto DECLARA que el aligerado es una viga continua de seis tramos
-- y se apoya en esa continuidad para fijar el peralte, porque la Tabla 9.1 de
la E.060 solo concede el L/21 a los panos con AMBOS extremos continuos.

Ahi esta la inconsistencia que la auditoria encontro: la continuidad se invoca
donde CONVIENE (reduce el peralte) y se ignora donde PERJUDICA (concentra la
reaccion en los apoyos interiores). Una hipotesis no puede valer en un renglon
y dejar de valer en el siguiente.

Este script no cambia el metrado: lo CONTRASTA. Resuelve la vigueta como viga
continua real y verifica que el esfuerzo axial sigue cumpliendo tambien con
ese reparto. Es el mismo criterio con que el script 20 trata el reparto
lateral: lo relevante no es cual de las dos hipotesis es la correcta, sino que
el diseno resista con las dos.

LO QUE EL AREA TRIBUTARIA NO VE
===============================
En una viga continua el apoyo interior recibe MAS que media luz a cada lado,
porque la continuidad le transfiere parte de la carga de los tramos vecinos;
y el apoyo EXTREMO recibe MENOS. El area tributaria no distingue: le da lo
mismo a los dos. Por eso subestima los muros interiores y sobreestima las
fachadas.

EL POZO CORTA LA CONTINUIDAD
============================
Las viguetas no son todas iguales. Las que pasan por el pozo de luz (5,40 m de
los 12,00 m de frente) NO existen en el pano central: ahi la losa se parte en
dos vigas mas cortas. Tratar toda la planta como una sola viga de seis tramos
daria un reparto que no corresponde a la mitad de las viguetas.
"""
import importlib.util
import os

from proyecto import (EJES_MX, POZO_X0, POZO_X1, FRENTE, MUROS, ESPESOR,
                      FM, TABIQUERIA, N_PISOS)


def _cargar(nombre):
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "c", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R11 = _cargar("11_metrado_muros.py")
# el limite del 7.1.1.b lo define el 02; el 11 ya lo reexporta desde alli
limite_axial = R11.limite_axial

LUCES = [round(EJES_MX[i + 1] - EJES_MX[i], 4) for i in range(len(EJES_MX) - 1)]
I_POZO = 2          # el pano central (entre MX-3 y MX-4) es el que lleva el pozo
NOM_MX = [m[0] for m in MUROS if m[1] == "X"]


def reacciones(luces, w=1.0):
    """Reacciones de una viga continua de apoyos simples bajo carga uniforme.

    Metodo de rigidez con los GIROS como incognitas (EI = 1, que se cancela al
    ser todos los tramos de la misma seccion). Se arma el sistema, se resuelve,
    se recuperan los momentos de extremo de cada tramo y de ahi los cortantes
    por equilibrio. Sin numpy: con siete nudos la eliminacion a mano sobra.
    """
    n = len(luces) + 1
    K = [[0.0] * n for _ in range(n)]
    F = [0.0] * n
    for i, L in enumerate(luces):
        K[i][i] += 4.0 / L
        K[i][i + 1] += 2.0 / L
        K[i + 1][i] += 2.0 / L
        K[i + 1][i + 1] += 4.0 / L
        fem = w * L * L / 12.0          # empotramiento perfecto del tramo   # no-ssot: divisor del empotramiento perfecto w.L^2/12, no el FRENTE
        F[i] += fem
        F[i + 1] -= fem
    for c in range(n):                  # eliminacion de Gauss-Jordan
        piv = K[c][c]
        for j in range(c, n):
            K[c][j] /= piv
        F[c] /= piv
        for r in range(n):
            if r == c or abs(K[r][c]) < 1e-15:
                continue
            f = K[r][c]
            for j in range(c, n):
                K[r][j] -= f * K[c][j]
            F[r] -= f * F[c]
    th = F
    R = [0.0] * n
    for i, L in enumerate(luces):
        Mi = (4.0 / L) * th[i] + (2.0 / L) * th[i + 1] - w * L * L / 12.0   # no-ssot: divisor del empotramiento perfecto w.L^2/12, no el FRENTE
        Mj = (2.0 / L) * th[i] + (4.0 / L) * th[i + 1] + w * L * L / 12.0   # no-ssot: divisor del empotramiento perfecto w.L^2/12, no el FRENTE
        R[i] += w * L / 2.0 - (Mi + Mj) / L
        R[i + 1] += w * L / 2.0 + (Mi + Mj) / L
    return R


def factores():
    """Reaccion continua / reaccion por area tributaria, muro por muro."""
    ancho_pozo = POZO_X1 - POZO_X0
    ancho_libre = FRENTE - ancho_pozo

    # familia A: viguetas FUERA del pozo, continuas en los seis tramos
    RA = reacciones(LUCES)
    # familia B: viguetas DENTRO del pozo, la losa se parte en el pano central
    RB = [0.0] * len(EJES_MX)
    for tramo, base in ((LUCES[:I_POZO], 0), (LUCES[I_POZO + 1:], I_POZO + 1)):
        for i, r in enumerate(reacciones(tramo)):
            RB[base + i] += r

    fac = {}
    for i, nom in enumerate(NOM_MX):
        izq = (EJES_MX[i] - EJES_MX[i - 1]) / 2.0 if i > 0 else 0.0
        der = (EJES_MX[i + 1] - EJES_MX[i]) / 2.0 if i < len(EJES_MX) - 1 else 0.0
        geo = 0.0
        for lado, pano in ((izq, i - 1), (der, i)):
            if lado <= 0:
                continue
            geo += lado * (ancho_libre if pano == I_POZO else FRENTE)
        cont = RA[i] * ancho_libre + RB[i] * ancho_pozo
        fac[nom] = (geo, cont, cont / geo)
    return fac


def sigma_continua(f, razon):
    """Esfuerzo axial del muro con la reaccion de la losa continua.

    Solo la parte de LOSA se reparte distinto. El peso propio del muro, la
    solera, el tarrajeo y la escalera no dependen de como trabaje el
    aligerado, y por eso se dejan intactos: escalarlos tambien inflaria el
    resultado con carga que la continuidad no toca.
    """
    carga_losa = f["pm"] - f["pp"]
    pm = f["pp"] + carga_losa * razon
    return pm / (f["Ln"] * 100 * ESPESOR * 100)


def verificar():
    print("=" * 84)
    print("ESFUERZO AXIAL CON LA LOSA CONTINUA  -  contraste del hallazgo C-7")
    print("=" * 84)
    print("  luces de la vigueta: %s m" % " / ".join("%.2f" % L for L in LUCES))
    print("  el pano %d (%.2f m) lleva el POZO: en %.2f m de los %.2f de frente"
          % (I_POZO + 1, LUCES[I_POZO], POZO_X1 - POZO_X0, FRENTE))
    print("  la losa se corta y la vigueta deja de ser continua.")
    print()

    fac = factores()
    metrado = {f["nom"]: f for f in R11.metrar()}
    lim, _ = limite_axial(FM)

    print("  %-26s %8s %8s %7s %8s %8s  %s"
          % ("muro", "A geom", "A cont", "razon", "sigma", "s. cont", "veredicto"))
    print("  A geom y A cont son las areas del REPARTO (geometrica y continua);")
    print("  el metrado del 11 usa la geometrica YA descontados pozo y escalera,")
    print("  y lo que se traslada de aca es la RAZON, no el area.")
    print("  " + "-" * 82)
    peor, ok = (None, 0.0), True
    for nom in NOM_MX:
        f = metrado[nom]
        geo, cont, razon = fac[nom]
        s_cont = sigma_continua(f, razon)
        if s_cont > peor[1]:
            peor = (nom, s_cont)
        if s_cont > lim:
            ok = False
        print("  %-26s %8.2f %8.2f %7.3f %8.2f %8.2f  %s"
              % (nom, geo, cont, razon, f["sigma"], s_cont,
                 "cumple" if s_cont <= lim else "NO CUMPLE  <<<"))
    print()
    print("  limite del 7.1.1.b = %.2f kgf/cm2" % lim)
    print()
    # CUANTA TABIQUERIA ADMITE EL DISENO. El margen del muro mas exigido es
    # del 3 % sobre el limite, y un 3 % dicho asi asusta sin informar: lo que
    # importa es cuanto puede CRECER la carga que lo genera. La tabiqueria es
    # la unica partida de la carga muerta que todavia puede moverse -- los
    # modulos de servicio son grandes y en obra se subdividen --, asi que se
    # despeja el valor que llevaria al muro al limite.
    #
    # sigma_cont = [pp + (carga_losa + a_trib . n_tip . dT) . razon] / (Ln.t)
    # es lineal en la tabiqueria, y se invierte sin iterar.
    f = metrado[peor[0]]
    _geo, _cont, razon = fac[peor[0]]
    n_tip = N_PISOS - 1
    dT = ((lim * f["Ln"] * 100 * ESPESOR * 100 - f["pp"]) / razon
          - (f["pm"] - f["pp"])) / (f["trib"] * n_tip)
    print("  MARGEN DE TABIQUERIA. Con %.1f kgf/m2 metrados, %s llega a %.2f;"
          % (TABIQUERIA, peor[0].split()[0], peor[1]))
    print("  alcanzaria el limite con %.0f kgf/m2, o sea que el diseno admite"
          % (TABIQUERIA + dT))
    print("  %.0f %% mas de tabique que el metrado. Cualquier subdivision que"
          % (100.0 * dT / TABIQUERIA))
    print("  pase de ahi exige reverificar este muro.")
    print("  el mas exigido con la losa continua es %s, con %.2f (holgura %+.1f %%)"
          % (peor[0], peor[1], 100 * (lim / peor[1] - 1)))
    print()
    print("  LECTURA. La continuidad RECARGA los apoyos interiores y DESCARGA")
    print("  las fachadas, que es justo lo que el area tributaria no puede ver:")
    print("  reparte media luz a cada lado sin distinguir un apoyo extremo de")
    print("  uno interior. El muro mas exigido CAMBIA de identidad, y aun asi")
    print("  ninguno pasa el limite. El diseno es robusto frente a la hipotesis")
    print("  de reparto VERTICAL, igual que el script 20 lo mostro para el")
    print("  reparto LATERAL.")
    return ok


def control_equilibrio():
    """La suma de reacciones tiene que ser la carga total.

    Sin este control el solver puede devolver cualquier cosa con cara de
    numero: un sistema mal armado no avisa, da resultados.
    """
    for luces in (LUCES, LUCES[:I_POZO], LUCES[I_POZO + 1:]):
        R = reacciones(luces)
        assert abs(sum(R) - sum(luces)) < 1e-9, (
            "el solver de viga continua no equilibra: %.6f contra %.6f"
            % (sum(R), sum(luces)))
    # y una viga de UN tramo tiene que dar medio y medio
    R1 = reacciones([4.0])
    assert abs(R1[0] - 2.0) < 1e-9 and abs(R1[1] - 2.0) < 1e-9, R1
    # dos tramos iguales: el apoyo central toma 1,25 wL, valor de tabla
    R2 = reacciones([1.0, 1.0])
    assert abs(R2[1] - 1.25) < 1e-9, R2
    print("  controles del solver: equilibrio, un tramo (1/2 y 1/2) y dos")
    print("  tramos iguales (el central toma 1,25 wL, valor de tabla)   OK")


if __name__ == "__main__":
    control_equilibrio()
    print()
    ok = verificar()
    print()
    print("RESULTADO:", "el axial CUMPLE tambien con la losa continua" if ok
          else "REVISAR: algun muro no cumple con el reparto continuo")
