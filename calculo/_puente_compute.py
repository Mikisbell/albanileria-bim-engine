# -*- coding: utf-8 -*-
"""Puente al interprete de calculo (OpenSeesPy).

POR QUE EXISTE ESTE ARCHIVO
===========================
OpenSeesPy NO se puede importar desde el mismo interprete que corre el resto
del calculo. La carga de sus DLL falla en Python 3.13; vive en un entorno
3.12 dedicado. Esta es exactamente la arquitectura que la fabrica de papers
ya tenia resuelta y documentada:

    "NEVER call OpenSeesPy directly from the pipeline .venv (3.13 - DLL load
     fails). FEM/compute goes through the bridge run_compute_op(), which
     delegates to the dedicated .venv-compute (3.12) via subprocess JSON.
     Resolve the interpreter with get_compute_python (env
     BELICO_COMPUTE_PYTHON), NEVER hardcode paths."

Se replica el patron, no la dependencia: este trabajo academico no importa
codigo de la fabrica, solo su leccion. El contrato es JSON por stdin/stdout,
de modo que el runner solo necesita openseespy y la biblioteca estandar.

COMO SE RESUELVE EL INTERPRETE, en orden y sin rutas a mano:
  1. la variable de entorno BELICO_COMPUTE_PYTHON, si esta puesta
  2. config/paths.py::get_compute_python de la fabrica, si es alcanzable
  3. un .venv-compute en las raices declaradas en BELICO_HOME
Si ninguna responde, se levanta un error que DICE que hacer, en vez de
reportar "no esta instalado", que fue el diagnostico equivocado que este
archivo viene a impedir que se repita.
"""
import json
import os
import subprocess
import sys

RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "_opensees_runner.py")


class ComputeNoDisponible(RuntimeError):
    pass


def _candidatos():
    env = os.environ.get("BELICO_COMPUTE_PYTHON")
    if env:
        yield ("env BELICO_COMPUTE_PYTHON", env)
    home = os.environ.get("BELICO_HOME", "D:/Jarvis-Belico")
    paths_py = os.path.join(home, "config", "paths.py")
    if os.path.isfile(paths_py):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("_belico_paths", paths_py)
            mod = importlib.util.module_from_spec(spec)
            sys.path.insert(0, home)
            spec.loader.exec_module(mod)
            sys.path.pop(0)
            yield ("config/paths.py::get_compute_python", str(mod.get_compute_python()))
        except Exception:
            pass
    for raiz in (home,):
        for sub in ("Scripts/python.exe", "bin/python"):
            p = os.path.join(raiz, ".venv-compute", *sub.split("/"))
            if os.path.isfile(p):
                yield ("%s/.venv-compute" % raiz, p)


def interprete():
    """Devuelve (origen, ruta) del primer interprete que TENGA openseespy."""
    visto = []
    for origen, ruta in _candidatos():
        if not ruta or not os.path.isfile(ruta):
            visto.append((origen, ruta, "no existe el archivo"))
            continue
        r = subprocess.run([ruta, "-c", "import openseespy.opensees"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return origen, ruta
        visto.append((origen, ruta, "no importa openseespy"))
    detalle = "\n".join("    %-42s %s  -> %s" % (o, r, m) for o, r, m in visto)
    raise ComputeNoDisponible(
        "No se encontro un interprete con OpenSeesPy.\n"
        "  Se probaron:\n%s\n"
        "  Solucion: exportar BELICO_COMPUTE_PYTHON con la ruta del python\n"
        "  que tenga openseespy instalado." % (detalle or "    (ninguno)"))


def correr(datos, verbose=True):
    """Manda el modelo al interprete de compute y devuelve sus resultados."""
    origen, py = interprete()
    if verbose:
        print("  puente de compute: %s" % origen)
        v = subprocess.run([py, "-c", "import sys;print(sys.version.split()[0])"],
                           capture_output=True, text=True).stdout.strip()
        print("  interprete       : Python %s" % v)
    r = subprocess.run([py, RUNNER], input=json.dumps(datos),
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("el runner de OpenSees fallo (%d):\n%s"
                           % (r.returncode, r.stderr[-3000:]))
    # OpenSees escupe avisos por stdout sin avisar; el runner marca donde
    # empieza SU respuesta para que un warning no rompa el parseo.
    marca = "<<<JSON>>>"
    if marca not in r.stdout:
        raise RuntimeError("el runner no devolvio JSON:" + chr(10) + "%s"
                           % r.stdout[-3000:])
    return json.loads(r.stdout.split(marca, 1)[1])
