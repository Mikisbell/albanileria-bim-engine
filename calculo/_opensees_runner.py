# -*- coding: utf-8 -*-
"""Runner de OpenSeesPy. Corre en el interprete 3.12, NO en el del calculo.

Contrato: lee un JSON por stdin, escribe un JSON por stdout despues del
marcador <<<JSON>>>. Solo depende de openseespy y de la biblioteca estandar,
para que el entorno de compute no tenga que conocer nada de este proyecto.

UNIDADES: kgf y cm en todo el archivo, las mismas del calculo manual, para
que los numeros se puedan comparar sin conversiones que escondan errores.

CONVENCION DE EJES, que es donde se cometen los errores en modelos 3D:
  el elemento es vertical, o sea su eje local x apunta como el Z global.
  Se elige el vector vecxz de cada muro de modo que en AMBAS direcciones
  la inercia FUERTE quede en Iz y el area de corte del alma en Avy:
      muro en Y (fuerte en el eje Y global)  -> vecxz = (1, 0, 0)
      muro en X (fuerte en el eje X global)  -> vecxz = (0, 1, 0)
  Asi un solo par (Iz, Avy) describe el comportamiento en el plano del muro
  y no hay que recordar cual indice corresponde a que direccion.

POR QUE DOS CASOS DE CARGA POR DIRECCION Y NO UNO
=================================================
El calculo manual reparte el cortante en dos sumandos: el DIRECTO, por
rigidez relativa, y el de TORSION, del que toma el signo que perjudica a
cada muro. Para poder comparar sumando contra sumando, el modelo corre por
separado:
    caso "F"  fuerzas de piso aplicadas en el centro de masa
    caso "T"  solo el momento torsor de la excentricidad ACCIDENTAL
El caso F ya contiene la torsion que la estructura genera sola por tener el
centro de rigidez fuera del de masa; el caso T agrega UNICAMENTE el
incremento accidental, que es lo que manda sumar el Art. 37.b de la E.030.
Como el sistema es lineal, la envolvente por muro es |V_F| + |V_T|.
"""
import json
import math
import sys

import openseespy.opensees as ops


def _vecxz(dire):
    return (1.0, 0.0, 0.0) if dire == "Y" else (0.0, 1.0, 0.0)


def _seccion(m):
    """(A, J, Iy, Iz, Avy, Avz) del muro, con la fuerte SIEMPRE en Iz."""
    return m["A"], m["J"], m["Iy"], m["Iz"], m["Avy"], m["Avz"]


def _resolver():
    ops.system("BandGeneral")
    ops.numberer("RCM")
    ops.constraints("Transformation")
    ops.integrator("LoadControl", 1.0)
    ops.algorithm("Linear")
    ops.analysis("Static")
    ok = ops.analyze(1)
    # Un analisis que falla devuelve un codigo y deja los desplazamientos en
    # CERO. Si no se corta aca, el cero viaja hasta las tablas y se lee como
    # "no se mueve" en vez de "no se resolvio": el peor verde falso posible.
    if ok != 0:
        raise RuntimeError("OpenSees no resolvio el sistema (analyze -> %d). "
                           "Revisar restricciones y singularidad." % ok)
    return ok


def rigidez_aislada(d):
    """CONTROL: cada muro solo, en voladizo, empotrado, carga en el tope.

    Es el unico resultado del modelo que tiene respuesta cerrada conocida
    (la formula del script 12). Si aca no coinciden, el modelo esta mal
    armado y nada de lo que siga vale.
    """
    E, Gm, H = d["Em"], d["Gm"], d["h_total"]
    out = {}
    for m in d["muros"]:
        ops.wipe()
        ops.model("basic", "-ndm", 3, "-ndf", 6)
        ops.node(1, 0.0, 0.0, 0.0)
        ops.node(2, 0.0, 0.0, H)
        ops.fix(1, 1, 1, 1, 1, 1, 1)
        vx, vy, vz = _vecxz(m["dir"])
        ops.geomTransf("Linear", 1, vx, vy, vz)
        A, J, Iy, Iz, Avy, Avz = _seccion(m)
        ops.element("ElasticTimoshenkoBeam", 1, 1, 2, E, Gm, A, J, Iy, Iz,
                    Avy, Avz, 1)
        dof = 2 if m["dir"] == "Y" else 1
        f = [0.0] * 6
        f[dof - 1] = 1000.0
        ops.timeSeries("Linear", 1)
        ops.pattern("Plain", 1, 1)
        ops.load(2, *f)
        _resolver()
        out[m["nom"]] = 1000.0 / ops.nodeDisp(2, dof)
    return out


def construir(d):
    """Modelo completo: 5 pisos, diafragma rigido por nivel, base empotrada."""
    ops.wipe()
    ops.model("basic", "-ndm", 3, "-ndf", 6)
    E, Gm = d["Em"], d["Gm"]
    h, n = d["h_entrepiso"], d["n_pisos"]
    ops.geomTransf("Linear", 1, 1.0, 0.0, 0.0)   # muros en Y
    ops.geomTransf("Linear", 2, 0.0, 1.0, 0.0)   # muros en X

    nodo, tag = {}, 1
    for m in d["muros"]:
        for i in range(n + 1):
            ops.node(tag, m["x"], m["y"], i * h)
            nodo[(m["nom"], i)] = tag
            tag += 1
        ops.fix(nodo[(m["nom"], 0)], 1, 1, 1, 1, 1, 1)

    maestro = {}
    for i in range(1, n + 1):
        p = d["pisos"][i - 1]
        ops.node(tag, p["xm"], p["ym"], i * h)
        maestro[i] = tag
        ops.mass(tag, p["m"], p["m"], 0.0, 0.0, 0.0, p["Izz"])
        # El nodo maestro es un punto de referencia del diafragma, no un punto
        # de la estructura: el diafragma le da rigidez SOLO en los tres grados
        # de su plano (ux, uy, giro vertical). Los otros tres quedarian sin
        # ninguna rigidez y la matriz sale singular -- que es exactamente como
        # fallo la primera version. Se restringen porque no tienen significado
        # fisico, no para "arreglar" el solver.
        ops.fix(tag, 0, 0, 1, 1, 1, 0)
        tag += 1

    elem, et = {}, 1
    for m in d["muros"]:
        A, J, Iy, Iz, Avy, Avz = _seccion(m)
        tr = 1 if m["dir"] == "Y" else 2
        for i in range(n):
            ops.element("ElasticTimoshenkoBeam", et, nodo[(m["nom"], i)],
                        nodo[(m["nom"], i + 1)], E, Gm, A, J, Iy, Iz,
                        Avy, Avz, tr)
            elem[(m["nom"], i)] = et
            et += 1

    for i in range(1, n + 1):
        esclavos = [nodo[(m["nom"], i)] for m in d["muros"]]
        ops.rigidDiaphragm(3, maestro[i], *esclavos)
    return nodo, maestro, elem


def modal(d, n_modos=6):
    """Analisis MODAL del edificio: periodos y formas de modo reales.

    POR QUE HACIA FALTA. El periodo del modelo se venia estimando por
    RAYLEIGH -- 2*pi*raiz(sum(m*u^2)/sum(F*u)) sobre la deformada del
    analisis estatico --, que es una aproximacion buena pero que SUPONE la
    forma del primer modo en vez de resolverla. El eigen la resuelve: es un
    problema de valores propios sobre la misma matriz de rigidez y la misma
    matriz de masas que ya estaban armadas.

    Tener los dos permite lo que este proyecto hace en todo lo demas:
    verificar por DOS CAMINOS. Si Rayleigh y el eigen dan lo mismo, el
    periodo esta bien; si no, uno de los dos modelos esta mal armado.

    Las masas ya estaban asignadas en los nodos maestros (traslacion en las
    dos direcciones y momento polar para el giro), asi que no hay que
    agregar nada al modelo: solo pedirle los modos.
    """
    n = d["n_pisos"]
    nodo, maestro, elem = construir(d)
    # con diafragma rigido hay 3 grados por piso (ux, uy, giro), asi que
    # pedir mas modos que 3*n no tiene sentido
    n_modos = min(n_modos, 3 * n)
    vals = ops.eigen("-fullGenLapack", n_modos)
    out = []
    for j, lam in enumerate(vals, 1):
        if lam <= 0:
            raise RuntimeError("el modo %d dio autovalor %.3e: la matriz no "
                               "es definida positiva" % (j, lam))
        w = math.sqrt(lam)
        forma = []
        for i in range(1, n + 1):
            ux = ops.nodeEigenvector(maestro[i], j, 1)
            uy = ops.nodeEigenvector(maestro[i], j, 2)
            rz = ops.nodeEigenvector(maestro[i], j, 6)
            forma.append({"ux": ux, "uy": uy, "rz": rz})
        # masa participativa por direccion, con la forma normalizada a masa:
        #   L = sum(m_i * phi_i)   ;   M* = sum(m_i * phi_i^2)
        part = {}
        for clave, comp in (("X", "ux"), ("Y", "uy")):
            L = sum(d["pisos"][i]["m"] * forma[i][comp] for i in range(n))
            Mg = sum(d["pisos"][i]["m"] * forma[i][comp] ** 2
                     for i in range(n))
            Mg += sum(d["pisos"][i]["Izz"] * forma[i]["rz"] ** 2
                      for i in range(n))
            part[clave] = (L * L / Mg) if Mg > 0 else 0.0
        out.append({"modo": j, "w": w, "T": 2.0 * math.pi / w,
                    "forma": forma, "masa_efectiva": part})
    m_total = sum(d["pisos"][i]["m"] for i in range(n))
    ops.wipeAnalysis()
    return {"modos": out, "masa_total": m_total}


def caso(d, dire, tipo):
    """Un caso de carga: 'F' (fuerzas en el CM) o 'T' (solo torsor accidental).

    EL MODELO SE RECONSTRUYE EN CADA CASO, a proposito. OpenSees ACUMULA el
    factor de carga entre analisis sucesivos: con LoadControl(1.0), el
    segundo analisis del mismo dominio se resuelve con factor 2, el tercero
    con 3. La primera version de este archivo reutilizaba el dominio y por
    eso el caso Y devolvia exactamente el doble del cortante aplicado. Se
    reconstruye en vez de resetear el tiempo porque un modelo de 83 nodos se
    arma en milisegundos y asi no queda ningun estado que arrastrar.
    """
    n = d["n_pisos"]
    nodo, maestro, elem = construir(d)
    ops.timeSeries("Linear", 1)
    ops.pattern("Plain", 1, 1)
    for i in range(1, n + 1):
        F = d["pisos"][i - 1]["F"]
        if tipo == "F":
            fx, fy, mz = (F, 0.0, 0.0) if dire == "X" else (0.0, F, 0.0)
        else:
            fx, fy, mz = 0.0, 0.0, F * d["exc_accidental"][dire]
        ops.load(maestro[i], fx, fy, 0.0, 0.0, 0.0, mz)
    ok = _resolver()

    dof = 1 if dire == "X" else 2
    # CONTROL DE EQUILIBRIO. La suma de las reacciones horizontales de la base
    # tiene que ser igual y opuesta a la suma de las fuerzas aplicadas. Es un
    # chequeo de tres lineas que no depende de ninguna hipotesis y que caza
    # solo la clase de error que un modelo comete en silencio: cargas
    # duplicadas, factores acumulados, apoyos de mas.
    ops.reactions()
    Rh = sum(ops.nodeReaction(nodo[(m["nom"], 0)], dof) for m in d["muros"])
    Fap = sum(d["pisos"][i]["F"] for i in range(n)) if tipo == "F" else 0.0
    if abs(Rh + Fap) > max(1.0, 1e-6 * abs(Fap if Fap else 1.0)):
        raise RuntimeError(
            "el modelo NO esta en equilibrio en %s/%s: aplicado %.1f kgf, "
            "reaccionado %.1f kgf" % (dire, tipo, Fap, -Rh))
    desp = [ops.nodeDisp(maestro[i], dof) for i in range(1, n + 1)]
    giro = [ops.nodeDisp(maestro[i], 6) for i in range(1, n + 1)]
    V = {}
    for m in d["muros"]:
        if m["dir"] != dire:
            continue
        V[m["nom"]] = [ops.eleResponse(elem[(m["nom"], i)], "localForce")[1]
                       for i in range(n)]
    ops.remove("loadPattern", 1)
    ops.remove("timeSeries", 1)
    ops.wipeAnalysis()
    return {"ok": ok, "desp": desp, "giro": giro, "V": V}


def main():
    d = json.loads(sys.stdin.read())
    res = {"K_aislado": rigidez_aislada(d), "casos": {},
           "modal": modal(d)}
    for dire in ("X", "Y"):
        res["casos"][dire] = {t: caso(d, dire, t) for t in ("F", "T")}
    sys.stdout.write("<<<JSON>>>" + json.dumps(res))


if __name__ == "__main__":
    main()
