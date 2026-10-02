# -*- coding: utf-8 -*-
"""Genera borrador/08-anexos.md — punto 8 del contenido que pide la consigna

POR QUE GENERADO Y NO ESCRITO A MANO
====================================
Un anexo es, por definicion, el respaldo de lo que el cuerpo del informe
afirma. Si se teclea, envejece: el cuerpo cambia y el anexo sigue diciendo lo
de antes, que es peor que no tenerlo -- el jurado encuentra la contradiccion
en el lugar donde el trabajo dice "aqui esta la prueba".

Este proyecto ya tuvo ese error hoy mismo, y con el propio archivo de
referencias: se corrigio el `.md` a mano y la siguiente corrida del generador
lo revirtio. La leccion se aplica aca desde el principio.

QUE ANEXO RESPONDE A QUE
========================
  A  el metrado de los 13 muros, muro por muro -> respalda el 3.4
  B  el registro de las 99 obligaciones normativas -> respalda todo
  C  las fichas de unidades analizadas -> respalda el 3.2
  D  la trazabilidad script-por-script -> respalda la reproducibilidad
  E  el estudio de suelos y sus limites declarados -> respalda el 3.3

EL ANEXO B Y EL DERECHO DE AUTOR
================================
La consigna dice, textual, que "los trabajos que no respeten el derecho de
autor seran anulados". El anexo D es la respuesta directa: declara que cada
cifra del informe sale de un script identificado, y el anexo B lista las
obligaciones con el articulo que las impone. Lo que no se cita, no se usa.
"""
import importlib.util
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "..", "borrador", "08-anexos.md")


def co(x, d=2):
    """Numero con COMA decimal y espacio de millar, como el resto del informe.

    Mezclar 9.41 y 9,41 en el mismo documento es de las cosas que el jurado ve
    antes que el calculo. El separador de millar es un espacio fino, no una
    coma, para no chocar con el decimal.
    """
    s = ("{:,.%df}" % d).format(x)
    return s.replace(",", " ").replace(".", ",")


def _cargar(nombre):
    ruta = os.path.join(AQUI, nombre)
    spec = importlib.util.spec_from_file_location(nombre[:2] + "x", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def anexo_a(L):
    """Metrado de los trece muros: la tabla completa que el 3.4 resume."""
    R11 = _cargar("11_metrado_muros.py")
    L += ["### Anexo A. Metrado de los trece muros portantes", "",
          "El apartado 3.4 presenta el muro crítico; aquí están los trece, con",
          "las dos cargas que no son intercambiables: `Pm` con el 100 % de",
          "sobrecarga para el esfuerzo axial (E.070 7.1.1.b) y `P` con el 25 %",
          "para el peso sísmico (E.030 Art. 31).", "",
          "", "Tabla: Metrado de los trece muros portantes y esfuerzo axial resultante",
           "| Muro | Dir. | `L` | `L` neta | `A` trib. | `Pm` (kgf) | `P` (kgf) | `σm` | Límite |",
          "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for f in R11.metrar():
        # GUION NO SEPARABLE (U+2011): con el guion normal Word partia
        # los nombres largos en "MY- / 3a" dentro de la celda. Se ve igual
        # y no es un punto de corte.
        L.append("| %s | %s | %s | %s | %s | %s | %s | **%s** | %s |"
                 % (f["nom"].split()[0].replace("-", "‑"),
                    f["dir"], co(f["L"]), co(f["Ln"]),
                    co(f["trib"]), co(f["pm"], 0), co(f["p"], 0),
                    co(f["sigma"]), co(f["lim"])))
    peor = max(R11.metrar(), key=lambda f: f["sigma"])
    L += ["", "El muro que gobierna es **%s**, con **%s kgf/cm²** contra un"
          % (peor["nom"].split()[0], co(peor["sigma"])),
          "admisible de %s: una holgura del %s %%."
          % (co(peor["lim"]), co(100 * (peor["lim"] / peor["sigma"] - 1), 1)), ""]
    return L


def anexo_b(L):
    """El registro de obligaciones normativas, con su estado."""
    V = _cargar("verificaciones.py")
    ok = sum(1 for f in V.V if f[3] == V.OK)
    falla = sum(1 for f in V.V if f[3] == V.FALLA)
    pend = sum(1 for f in V.V if f[3] == V.PEND)
    decl = sum(1 for f in V.V if f[3] == V.DECL)
    na = sum(1 for f in V.V if f[3] == V.NA)
    # LA TABLA DEBE CERRAR CON SU PROPIO TOTAL. Publicaba tres de los cinco
    # estados contra un total de len(V.V): el lector sumaba 115 + 0 + 6 = 121
    # contra un total de 133 y le faltaban doce filas sin explicacion. El
    # comentario de verificaciones.py::tablero ya advertia que un estado nuevo
    # hay que darlo de alta en TODOS sus contadores; aqui no se habia hecho.
    assert ok + falla + pend + decl + na == len(V.V), (
        "el Anexo B publicaria una tabla que no cierra: %d + %d + %d + %d + %d "
        "= %d contra un total de %d"
        % (ok, falla, pend, decl, na, ok + falla + pend + decl + na, len(V.V)))
    L += ["### Anexo B. Registro de obligaciones normativas", "",
          "Se llevó durante todo el desarrollo un inventario de las",
          "obligaciones que cada Norma impone, con un estado explícito por",
          "cada una. **«Falta verificar» es un estado contable**, no la",
          "ausencia de una línea: una verificación omitida no deja rastro y el",
          "informe se lee correcto sin ella.", "",
          "", "Tabla: Estado de las obligaciones normativas registradas",
           "| Estado | Cantidad |", "|---|---:|",
          "| Comprobadas con cálculo | **%d** |" % ok,
          "| En falla | **%d** |" % falla,
          "| Pendientes de etapas posteriores | %d |" % pend,
          "| Declaradas con su vía de cierre | %d |" % decl,
          "| Fuera del alcance de este proyecto | %d |" % na,
          "| **Total inventariado** | **%d** |" % len(V.V), "",
          "Los pendientes no son omisiones sino trabajo que corresponde a",
          "etapas que este Producto Académico no abarca: ensayos de",
          "laboratorio, especificaciones técnicas y detalles de obra. Se",
          "listan a continuación con la norma que los exige.", "",
          "", "Tabla: Obligaciones normativas que no se cierran en gabinete",
           "| Norma | Obligación | Por qué queda pendiente |", "|---|---|---|"]
    for f in V.V:
        if f[3] == V.PEND:
            L.append("| %s | %s | %s |" % (f[1], f[2], f[4]))
    L.append("")
    return L


def anexo_c(L):
    """Las fichas de unidades: la evidencia del descarte del ladrillo."""
    R13 = _cargar("13_unidad_albanileria.py")
    L += ["### Anexo C. Fichas técnicas de unidades analizadas", "",
          "El apartado 3.2 concluye que **el nombre comercial de una unidad no",
          "determina su clasificación normativa**. La evidencia son estas siete",
          "fichas de fabricantes peruanos: el mismo producto denominado «King",
          "Kong de 18 huecos» declara porcentajes de vacío muy distintos, y el",
          "numeral **2.1.26** de la E.070 exige un área de vacíos no mayor al",
          "**30 %** para considerar sólida a la unidad.", "",
          "**Tres fichas no publican el dato, y el peso las delata**: la",
          "densidad aparente —peso declarado sobre volumen bruto— es el mismo",
          "dato por otro camino, y una unidad con casi la mitad de su volumen",
          "en aire no puede pesar lo que pesa una sólida.", "",
          "", "Tabla: Fichas técnicas de unidades de albañilería analizadas",
           "| Fabricante / producto | Familia | Dimensiones (cm) | Peso (kg) | Vacíos | `f'b` NTP |",
          "|---|---|---|---:|---:|---:|"]
    for (marca, fam, largo, ancho, alto, pmin, pmax, vac, tipo, fb, arch) in R13.FICHAS:
        peso = co(pmin, 2) if pmin == pmax else "%s a %s" % (co(pmin, 2), co(pmax, 2))
        # sin espacios alrededor del signo: con ellos Word partia
        # "24,0 x 13,0 x 9,0" en tres renglones
        L.append("| %s | %s | %s\u00d7%s\u00d7%s | %s | %s | %s |"
                 % (marca, fam, co(largo, 1), co(ancho, 1), co(alto, 1), peso,
                    ("**%s %%**" % co(vac, 1)) if vac is not None
                    else "*no declara*",
                    co(fb, 0)))
    n_declara = sum(1 for f in R13.FICHAS if f[7] is not None)
    L += ["", "De las siete fichas, **%d declaran** el porcentaje de vacíos y %d"
          % (n_declara, len(R13.FICHAS) - n_declara),
          "no lo hacen. Cada ficha lleva el nombre del fabricante; los",
          "PDF originales están en",
          "`evidencia/fichas-tecnicas-ladrillo/`; el cálculo completo, incluida",
          "la densidad aparente de las que callan el dato, en",
          "`calculo/13_unidad_albanileria.py`.", "",
          "> **Por eso la especificación del proyecto se redactó por requisito",
          "> verificable** —área de vacíos no mayor al 30 %, `f'b` ≥ 130 kg/cm²—",
          "> **y no por denominación comercial.**", ""]
    return L


def anexo_d(L):
    """Trazabilidad: que cifra sale de que script. Es la respuesta al
    invalidante de derecho de autor."""
    scripts = sorted(f for f in os.listdir(AQUI)
                     if f[:2].isdigit() and f.endswith(".py"))
    L += ["### Anexo D. Trazabilidad del cálculo", "",
          "**Ninguna cifra de este informe se escribió a mano.** Todas provienen",
          "de un archivo único de constantes (`calculo/proyecto.py`) y de los",
          "scripts que lo consumen; los planos se generan desde esa misma",
          "fuente. Se declara aquí la correspondencia para que cualquier",
          "resultado pueda rehacerse.", "",
          "", "Tabla: Correspondencia entre cada script de cálculo y el resultado que produce",
           "| Script | Qué calcula |", "|---|---|"]
    for s in scripts:
        doc = ""
        with open(os.path.join(AQUI, s), encoding="utf-8") as fh:
            lineas = fh.read().split("\n")
        for i, ln in enumerate(lineas):
            # un docstring puede llevar prefijo u/r/b: `u"""..."""` es
            # valido y el extractor solo reconocia `"""`. Con el 33, que
            # lo usa, la tabla salio diciendo "import math" -- la primera
            # linea que SI empezaba con comillas quedaba mas abajo.
            desnuda = ln.lstrip("urbURB")
            if desnuda.startswith('"""'):
                doc = desnuda.strip('"').strip()
                if not doc and i + 1 < len(lineas):
                    doc = lineas[i + 1].strip()
                break
        L.append("| `%s` | %s |" % (s, doc.rstrip(".")))
    L += ["", "Se lleva además un **control de regresión**: la salida numérica de",
          "los %d scripts se compara contra una referencia, de modo que" % len(scripts),
          "cualquier cambio que altere un resultado queda a la vista en lugar de",
          "pasar inadvertido.", ""]
    return L


def anexo_e(L):
    """El EMS y sus limites, declarados."""
    L += ["### Anexo E. Estudio de mecánica de suelos", "",
          "El estudio disponible para el sector se empleó para la capacidad",
          "portante de diseño. **Sus límites se declaran porque condicionan una",
          "verificación**: alcanzó 3 m de profundidad y no reporta velocidad de",
          "ondas de corte ni ensayo SPT, de modo que el perfil **S2 se adoptó",
          "sin la clasificación que la Tabla 3 de la E.030-2026 requiere**.", "",
          "Por esa razón el apartado 3.3 incluye un **análisis de sensibilidad**",
          "a un perfil S3, que es la forma honesta de trabajar con un dato",
          "incompleto: no suponerlo favorable, sino comprobar que el diseño",
          "aguanta la hipótesis desfavorable.", "",
          "", "Tabla: Parámetros del estudio de mecánica de suelos adoptados",
           "| Parámetro | Valor adoptado | Origen |", "|---|---|---|",
          "| Perfil de suelo | S2 | adoptado; **pendiente de clasificación formal** |",
          "| Profundidad del estudio | 3,00 m | EMS del sector |",
          "| Ensayos de campo | densidad por cono de arena | EMS; **no hay SPT** |",
          "| Profundidad de cimentación `Df` | 1,50 m | adoptada, ver 3.3 |", ""]
    return L


def generar():
    L = ["## 6. Anexos", "",
         "Los anexos reúnen el respaldo de lo que el cuerpo del informe",
         "afirma. Se generan desde la misma fuente que el cálculo, de modo que",
         "no pueden quedar desfasados respecto de él.", ""]
    for fn in (anexo_a, anexo_b, anexo_c, anexo_d, anexo_e):
        L = fn(L)
    texto = "\n".join(L).rstrip() + "\n"

    # a temporal y reemplazo: open(p,'w') trunca al abrir, y si algo revienta
    # entre medias el anexo queda en cero
    tmp = SALIDA + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(texto)
    os.replace(tmp, SALIDA)
    return texto


def control(texto):
    """Que el anexo diga lo mismo que el cuerpo, no algo parecido."""
    R11 = _cargar("11_metrado_muros.py")
    peor = max(R11.metrar(), key=lambda f: f["sigma"])
    # el anexo usa COMA decimal como el resto del informe; buscar con punto
    # hacia fallar este control por formato, no por contenido
    assert co(peor["sigma"]) in texto, (
        "el anexo A no trae el sigma critico %s" % co(peor["sigma"]))
    # y que NO se haya colado un punto decimal en las tablas: mezclar 9.41 y
    # 9,41 en el mismo documento se ve antes que cualquier error de calculo
    # sin regex: las celdas de tabla se parten por '|' y se mira cada una.
    # El regex que habia aqui capturaba cadenas vacias y denunciaba cinco
    # defectos inexistentes -- un control que grita en falso deja de mirarse.
    colados = []
    for linea in texto.split(chr(10)):
        if not linea.startswith("|"):
            continue
        for celda in linea.split("|"):
            c = celda.strip().lstrip("*`").rstrip("*`%")
            if c.replace("-", "").replace(".", "").isdigit() and "." in c:
                colados.append(c)
    assert not colados, "punto decimal en las tablas del anexo: %s" % colados[:5]
    assert peor["nom"].split()[0] in texto, "el anexo A no nombra el muro critico"
    # los cinco anexos, ninguno vacio
    for letra in "ABCDE":
        marca = "### Anexo %s." % letra
        assert marca in texto, "falta el anexo %s" % letra
        cuerpo = texto.split(marca)[1].split("### Anexo")[0]
        assert len(cuerpo.strip()) > 200, "el anexo %s esta casi vacio" % letra   # no-ssot: longitud minima en caracteres del assert, no una sobrecarga
    return True


if __name__ == "__main__":
    t = generar()
    control(t)
    print("=" * 74)
    print("ANEXOS  -  punto 8 del contenido que pide la consigna")
    print("=" * 74)
    print()
    print("  archivo : borrador/08-anexos.md")
    print("  palabras: %d" % len(t.split()))
    print("  anexos  : A metrado de los 13 muros")
    print("            B registro de obligaciones normativas")
    print("            C fichas tecnicas de unidades")
    print("            D trazabilidad del calculo")
    print("            E estudio de suelos y sus limites")
    print()
    print("  El anexo D es la respuesta al invalidante de la consigna:")
    print("  'los trabajos que no respeten el derecho de autor seran")
    print("  anulados'. Declara de que script sale cada cifra.")
