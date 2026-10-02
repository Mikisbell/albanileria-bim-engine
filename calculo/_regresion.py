# -*- coding: utf-8 -*-
"""Compara los numeros de hoy contra _baseline_pre_refactor.json.

No compara texto: el texto lo reescribi a proposito. Compara el MULTICONJUNTO
de numeros, y lista que valor aparecio y cual desaparecio, para poder juzgar
uno por uno si es prosa o si es fisica.
"""
import glob, json, os, re, subprocess, sys
from collections import Counter

# Este guardian se corre desde cualquier lado (la raiz del trabajo, la carpeta
# de planos, una tarea programada). Si resuelve sus rutas contra el cwd, falla
# con un FileNotFoundError que PARECE un rojo del guardian y no lo es: es un
# falso rojo que dos veces me hizo creer que algo se habia roto. Las rutas se
# resuelven contra la ubicacion de ESTE archivo, que no cambia.
AQUI = os.path.dirname(os.path.abspath(__file__))
os.chdir(AQUI)

NUM = re.compile(r"-?\d+[.,]?\d*")

# --refrendar REESCRIBE la referencia. Se usa solo despues de mirar el diff
# numero por numero y concluir que el cambio era querido; si se corre a
# ciegas, el guardian deja de guardar nada.
REFRENDAR = "--refrendar" in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith("--")]
REF = args[0] if args else "_baseline.json"
base = json.load(open(REF, encoding="utf-8"))
if REFRENDAR:
    # un script nuevo entra al registro recien al refrendar.
    # El patron es "dos digitos y guion bajo" y NO "0*" mas "1*": esa version
    # dejo al 20_modelo_opensees.py fuera del registro sin decir nada, que es
    # el modo en que un guardian deja de guardar.
    for f in sorted(glob.glob("[0-9][0-9]_*.py")):
        base.setdefault(f, [])
print("referencia: %s" % REF)

# AUDITORIA 2026-09-19. El bucle de abajo recorre el BASELINE, no el disco:
# un script nuevo no figuraba en el registro y por lo tanto NO SE CORRIA, sin
# que nada lo dijera. Podia reventar y la regresion seguia en verde. Es la
# misma familia del glob "0*.py"+"1*.py" que dejo fuera al 20: un guardian
# que solo mira su propia lista no ve lo que la lista no tiene.
_en_disco = set(glob.glob("[0-9][0-9]_*.py"))
_sin_registro = sorted(_en_disco - set(base))
if _sin_registro and not REFRENDAR:
    print()
    for _s in _sin_registro:
        print("!! %s NO esta en el baseline: no se compara. Corre --refrendar." % _s)
_huerfanos = sorted(set(base) - _en_disco)
for _s in _huerfanos:
    print("!! %s esta en el baseline y YA NO existe en disco." % _s)
print()
malo = 0
nuevo_base = {}
_reventados = []

for script in sorted(base):
    out = subprocess.run([sys.executable, script], capture_output=True,
                         text=True, encoding="utf-8", errors="replace")
    if out.returncode != 0:
        # Un script que sale != 0 no entraba en `nuevo_base`, asi que
        # al refrendar SE CAIA DEL BASELINE en silencio y la regresion
        # dejaba de cubrirlo para siempre. Pasa con los que reportan un
        # hallazgo legitimo con exit 2, y pasaria con cualquiera que
        # empezara a reventar. Se conserva su registro y se avisa.
        print("!! %s REVENTO (exit %d)\n%s"
              % (script, out.returncode, out.stderr[-600:]))
        nuevo_base[script] = base[script]
        _reventados.append(script)
        malo += 1
        continue
    hoy = Counter(NUM.findall(out.stdout))
    nuevo_base[script] = NUM.findall(out.stdout)
    antes = Counter(base[script])
    fuera = antes - hoy          # estaba y ya no
    nuevo = hoy - antes          # no estaba y aparecio
    estado = "IDENTICO" if not fuera and not nuevo else "DIFIERE"
    print("%-34s %s  (%d numeros)" % (script, estado, sum(hoy.values())))
    if fuera:
        print("     desaparecieron: %s" % ", ".join(sorted(fuera.elements())))
    if nuevo:
        print("     aparecieron   : %s" % ", ".join(sorted(nuevo.elements())))
    if fuera or nuevo:
        malo += 1

print()
print("scripts con diferencias: %d de %d" % (malo, len(base)))
if _reventados:
    print("scripts que REVIENTAN (se conserva su registro viejo): %s"
          % ", ".join(_reventados))
if _sin_registro:
    # antes solo se contaban SIN --refrendar, de modo que un refrendo
    # incorporaba scripts nuevos sin decir cuales. Ahora se nombran.
    print("scripts SIN comparar (fuera del baseline): %s"
          % ", ".join(sorted(_sin_registro)))
    if not REFRENDAR:
        malo += len(_sin_registro)
if REFRENDAR:
    for _s in sorted(_sin_registro):
        _o = subprocess.run([sys.executable, _s], capture_output=True,
                            text=True, encoding="utf-8",
                            errors="replace")
        nuevo_base[_s] = NUM.findall(_o.stdout)
        print("   + incorporado al baseline: %s (exit %d)"
              % (_s, _o.returncode))
    json.dump(nuevo_base, open(REF, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1, sort_keys=True)
    print()
    print("REFERENCIA REESCRITA: %s  (%d scripts)" % (REF, len(nuevo_base)))
