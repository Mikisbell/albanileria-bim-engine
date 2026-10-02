# -*- coding: utf-8 -*-
u"""GUARDIÁN 19 - el número TECLEADO dentro de una figura.

POR QUÉ EXISTE. El 2026-09-28 Mikis me corrigió: «tienes que ser acorde a
los cálculos que hicimos, no puedes inventar sin esa información». Tenía
razón, y al revisar salió esto, todo dentro de figuras que se entregan:

  · la ficha del corte A-A publicaba **q_adm = 1,10 kg/cm²**; el EMS da
    **3,00** (`QAD`, del gráfico «B vs qad» de su Fig. N.º 3);
  · la ficha de la elevación publicaba **«Densidad Muros X: 0.043 >=
    0.038»**; los valores vivos son **0,0659 >= 0,0290**;
  · el cuadro de parámetros declaraba la unidad como **«Macizo Tipo IV»**
    cuando el proyecto adoptó la **sólida Tipo V** de 30 % de vacíos —la
    Tipo IV con 40 % es justamente la que la Tabla 2 prohíbe en zona 2—;
  · la ficha del corte B-B decía **«7 muros confinados»** bajo el rótulo
    «Transversales (Eje Y)»: en Y hay **6**.

Y ninguno de los dieciocho guardianes podía verlos. El de MAGNITUDES —que
existe justamente para cazar el número viejo que se parece al vivo— lee el
BORRADOR; el de CONSTANTES mira que los scripts no reconstruyan el SSOT.
Entre los dos queda un hueco del tamaño de una figura: el texto que un
generador de dibujo escribe como rótulo no lo audita nadie, y una figura es
lo primero que mira un jurado.

CÓMO AUDITA. Recorre cada generador con `ast`, saca los literales de texto
y busca en ellos números que COINCIDAN con una magnitud viva del SSOT. La
coincidencia no es sospechosa: es el síntoma. Si el rótulo dice «0.24 m» y
`ESPESOR` vale 0,24, ese rótulo está escrito a mano al lado del valor que
lo produce, y el día que el espesor cambie el dibujo va a seguir diciendo
0,24 sin que nada avise. Es el mismo defecto por el que la ficha decía 1,10
cuando el EMS ya decía 3,00.

LO QUE NO HACE. No caza las etiquetas de PALABRA —«Macizo Tipo IV» no tiene
números—, y para eso no hay atajo: esas se cruzan a mano contra la decisión
que las fija. Tampoco toca lo que el propio dibujo necesita para dibujarse
(posiciones, tamaños de tipografía, colores): sólo mira TEXTO que se
imprime.

LA EXENCIÓN, con marca y contada. Un rótulo puede citar legítimamente un
número que coincide con uno vivo —el mínimo de una norma, por ejemplo—. Se
exime con `# tecleado-ok` en la misma línea, y las exenciones se cuentan:
una exención que no se ve es la puerta por donde vuelve todo.
"""
import ast
import contextlib
import io
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
CALCULO = os.path.join(os.path.dirname(AQUI), "calculo")
sys.path.insert(0, CALCULO)
sys.path.insert(0, AQUI)

MARCA = "tecleado-ok"
MIN_CIFRAS = 2          # un "5" suelto coincide con cualquier cosa
# LA UNIDAD DESAMBIGUA, igual que en el guardian 18. Sin esto, el guardian
# denunciaba el «0,85» del factor phi de una formula porque PHI_CORTANTE
# vale 0,85, y el «0,70» de otra porque coincide con el ancho de un vano de
# bano. Un numero sin unidad al lado no es una medida publicada: es un
# coeficiente, y los coeficientes de norma se escriben donde van.
UNIDAD = re.compile(r"^\s*(m(?![a-zA-Z])|m[²2]|cm|mm|kgf?(/cm[²2])?|%|s|"
                    r"tonf|kg/cm[²2])")
VENTANA_UNIDAD = 12     # cuanto texto se mira detras del numero
# un numero de rotulo: 0.24, 13,50, 227.22, 1 421,9
NUMERO = re.compile(r"(?<![\w.,])(\d{1,3}(?:[   ]\d{3})+(?:[.,]\d+)?"
                    r"|\d+[.,]\d+)(?![\w])")
# lo que NO es un rotulo: especificaciones de estilo de matplotlib
ESTILO = re.compile(r"boxstyle|pad=|rounding|round,|square,|^#[0-9a-fA-F]{3,8}$"
                    r"|arrowstyle|->|-\|>|^[a-z_]+$")


def vivas():
    """Las magnitudes del SSOT, con su nombre."""
    import proyecto as P
    out = {}
    for k in dir(P):
        if not k.isupper() or k.startswith("_"):
            continue
        v = getattr(P, k)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        if abs(v) < 0.01:
            continue                 # 0 y los factores chicos coinciden solos
        out[k] = float(v)
    return out


def cifras(s):
    return len(re.sub(r"[^\d]", "", s).lstrip("0"))


def valor(s):
    for sep in (" ", " ", " "):
        s = s.replace(sep, "")
    try:
        return float(s.replace(",", "."))
    except ValueError:
        return None


def coincide(x, viv, dec):
    """El publicado ES el vivo escrito con `dec` decimales."""
    return abs(round(viv, dec) - x) < 10.0 ** (-dec) / 2.0


def literales(ruta):
    """(línea, texto) de cada literal de cadena del archivo."""
    # utf-8-sig y no utf-8: un generador del repo trae BOM, y el BOM
    # sobrevive a la lectura y hace fallar a  con un caracter no
    # imprimible. Python lo maneja al importar; leerlo a mano, no.
    with io.open(ruta, encoding="utf-8-sig") as f:
        fuente = f.read()
    arbol = ast.parse(fuente, filename=ruta)
    lineas = fuente.split(chr(10))
    # LOS DOCSTRINGS NO SON ROTULOS, y este guardian se denunciaba a si
    # mismo: su propia explicacion cita el «1,10 kg/cm²» que vino a cazar.
    # Se marcan por posicion -- primer enunciado de modulo, funcion o clase--
    # que es lo que los distingue de una cadena cualquiera.
    docs = set()
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        cuerpo = getattr(nodo, "body", None)
        if (cuerpo and isinstance(cuerpo[0], ast.Expr)
                and isinstance(cuerpo[0].value, ast.Constant)
                and isinstance(cuerpo[0].value.value, str)):
            docs.add(id(cuerpo[0].value))
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)
                and id(nodo) not in docs):
            yield nodo.lineno, nodo.value, lineas


def auditar(ruta, VIVAS):
    fallas = []
    exentas = 0
    for lineno, texto, lineas in literales(ruta):
        if len(texto) > 400:
            continue                       # un docstring no es un rotulo
        if ESTILO.search(texto):
            continue
        if not re.search(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]", texto):
            continue                       # sin letras no es un rotulo
        linea = lineas[lineno - 1] if lineno - 1 < len(lineas) else ""
        for m in NUMERO.finditer(texto):
            s = m.group(1)
            if cifras(s) < MIN_CIFRAS:
                continue
            x = valor(s)
            if x is None:
                continue
            dec = len(re.split(r"[.,]", s)[1]) if re.search(r"[.,]", s) else 0
            cola = texto[m.end():m.end() + VENTANA_UNIDAD]
            mu = UNIDAD.match(cola)
            if not mu:
                continue
            # LA UNIDAD NO SOLO DESAMBIGUA: CONVIERTE. Sin esto el guardian
            # denunciaba «junta sismica e = 2.5 cm» contra EST_ANCHO, que
            # vale 2,5 METROS. Dos numeros iguales en unidades distintas no
            # son el mismo dato, y tratarlos como tal es el falso rojo mas
            # facil de fabricar.
            u = mu.group(1).strip()
            factor = 0.01 if u == "cm" else (0.001 if u == "mm" else 1.0)
            x = x * factor
            dec = dec + (2 if u == "cm" else (3 if u == "mm" else 0))
            for nom, viv in VIVAS.items():
                if not coincide(x, viv, dec):
                    continue
                if MARCA in linea:
                    exentas += 1
                    break
                fallas.append((os.path.basename(ruta), lineno, s, nom, viv,
                               texto[:46]))
                break
    return fallas, exentas


def main():
    print("=" * 78)
    print("NUMEROS TECLEADOS EN FIGURAS  -  el rotulo que repite una magnitud viva")
    print("=" * 78)
    print("")
    with contextlib.redirect_stdout(io.StringIO()):
        VIVAS = vivas()
    generadores = sorted(f for f in os.listdir(AQUI)
                         if f.endswith(".py")
                         and (f.startswith("F_") or f.startswith("L_")))
    fallas = []
    exentas = 0
    for f in generadores:
        fa, ex = auditar(os.path.join(AQUI, f), VIVAS)
        fallas += fa
        exentas += ex
    print("  %d generadores recorridos contra %d magnitudes del SSOT"
          % (len(generadores), len(VIVAS)))
    if exentas:
        print("  exentos por marca `%s`: %d  -- se cuentan: una exencion"
              % (MARCA, exentas))
        print("   que no se ve es la puerta por donde vuelve todo.")
    print("")
    if not fallas:
        print("  [ok] ningun rotulo repite a mano una magnitud del SSOT")
        print("")
        return 0
    print("  %d ROTULO(S) CON UN NUMERO ESCRITO A MANO:" % len(fallas))
    print("")
    for arch, lin, s, nom, viv, muestra in fallas:
        print("   %s:%d  escribe %s  y %s vale %s"
              % (arch, lin, s, nom,
                 ("%.4f" % viv).rstrip("0").rstrip(".").replace(".", ",")))
        print("      en: %r" % muestra)
    print("")
    print("  Cada uno se resuelve igual: interpolar la constante en vez de")
    print("  escribir su valor. Si el rotulo cita a proposito un numero de")
    print("  norma que coincide, se exime con `# %s` en esa linea." % MARCA)
    print("")
    return 1


if __name__ == "__main__":
    sys.exit(main())
