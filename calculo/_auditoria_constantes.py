# -*- coding: utf-8 -*-
"""Busca constantes del proyecto REPETIDAS fuera de proyecto.py.

No busca por nombre (renombrar la burla) sino por VALOR literal en el AST, que
es lo que de verdad se desincroniza. Ignora comentarios y cadenas: ahi un numero
es documentacion, no una fuente de verdad paralela.
"""
import ast
import os, glob, os

# AUDITORIA 2026-09-19. Las rutas se resolvian contra el CWD: corrido desde la
# raiz del proyecto, este auditor reventaba con FileNotFoundError. Es el mismo
# defecto que ya se habia corregido en _regresion.py y que aqui seguia vivo --
# arreglar un bug en un archivo no lo arregla en sus hermanos.
AQUI = os.path.dirname(os.path.abspath(__file__))


def _ruta(nombre):
    return os.path.join(AQUI, nombre)


fuente = ast.parse(open(_ruta("proyecto.py"), encoding="utf-8").read())
CANON = {}                      # valor -> [nombres que lo declaran]
for n in fuente.body:
    if isinstance(n, ast.Assign) and isinstance(n.value, (ast.Constant,)):
        v = n.value.value
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            CANON.setdefault(float(v), []).append(n.targets[0].id)

# Valores tan comunes que exigirlos importados seria ruido, no rigor.
TRIVIALES = {0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 10.0, 100.0, 0.5}
SOSPECHOSOS = {v: ns for v, ns in CANON.items() if v not in TRIVIALES}

hallazgos = 0
# El patron es "dos digitos y guion bajo" y NO "0*" mas "1*": esa version
# dejaba fuera a los scripts 20 a 28 SIN DECIRLO -- nueve scripts que nunca
# se auditaron por constantes duplicadas. Es exactamente el mismo glob que
# _regresion.py ya habia tenido que corregir por el script 20.
for f in sorted(os.path.basename(x)
                for x in glob.glob(os.path.join(AQUI, "[0-9][0-9]_*.py"))):
    src = open(_ruta(f), encoding="utf-8").read()
    # Una linea marcada # no-ssot fue triada a mano: el valor coincide por
    # casualidad pero es OTRA magnitud (200 m2 de la consigna vs 200 kgf/m2
    # de sobrecarga). Marcarlas es lo que hace que un duplicado NUEVO se vea.
    exentas = {i + 1 for i, l in enumerate(src.splitlines()) if "# no-ssot" in l}
    arbol = ast.parse(src)
    importados = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.ImportFrom) and n.module == "proyecto":
            importados |= {a.name for a in n.names}
    malos = []
    for n in ast.walk(arbol):
        if not isinstance(n, ast.Constant):
            continue
        if isinstance(n.value, bool) or not isinstance(n.value, (int, float)):
            continue
        if float(n.value) not in SOSPECHOSOS or n.lineno in exentas:
            continue
        malos.append((n.lineno, n.value, "/".join(SOSPECHOSOS[float(n.value)])))
    print("%-34s importa %2d de proyecto.py" % (f, len(importados)))
    for ln, v, nombres in sorted(set(malos)):
        print("    linea %3d: literal %-8s duplica %s" % (ln, v, nombres))
        hallazgos += 1

print()
print("constantes del proyecto duplicadas en literales: %d" % hallazgos)


def audita_el_ssot():
    """El guardian del SSOT tambien tiene que mirar el SSOT.

    El 2026-09-15, al llevar el espesor de 0,23 a 0,24 m, la caja de escalera
    quedo 1 cm corta: ESC_X1 llevaba el 0.23 escrito A MANO dentro del propio
    proyecto.py. Nadie lo vio porque este script solo auditaba 0*.py y 1*.py.
    Un literal de proyecto.py que repite una constante de proyecto.py es la
    misma falla que se persigue afuera, y sale mas cara: se propaga a los 13.
    """
    src = open(_ruta("proyecto.py"), encoding="utf-8").read()
    exentas = {i + 1 for i, l in enumerate(src.splitlines()) if "# no-ssot" in l}
    arbol = ast.parse(src)
    # Las asignaciones simples de nivel superior SON la declaracion canonica:
    # ahi el literal es la fuente de verdad, no una copia.
    canonicas = {id(n.value) for n in arbol.body
                 if isinstance(n, ast.Assign) and isinstance(n.value, ast.Constant)}
    malos = set()
    for n in ast.walk(arbol):
        if not isinstance(n, ast.Constant) or id(n) in canonicas:
            continue
        if isinstance(n.value, bool) or not isinstance(n.value, (int, float)):
            continue
        if float(n.value) not in SOSPECHOSOS or n.lineno in exentas:
            continue
        malos.add((n.lineno, n.value, "/".join(SOSPECHOSOS[float(n.value)])))
    print()
    print("%-34s %d literales que repiten una constante SUYA"
          % ("proyecto.py (el SSOT mismo)", len(malos)))
    for ln, v, nombres in sorted(malos):
        print("    linea %3d: literal %-8s duplica %s" % (ln, v, nombres))
    return len(malos)


if __name__ == "__main__":
    n = audita_el_ssot()
    print()
    print("total de duplicados: %d" % (hallazgos + n))
