# -*- coding: utf-8 -*-
"""La unidad: el nombre comercial NO decide si es apta; el peso sí. Y fija t

PREGUNTA QUE RESUELVE
=====================
"El King Kong de 18 huecos, que es el que esta mas cerca, tiene menos del 30 %
de vacios?" El proyecto venia respondiendo que NO con un solo dato: la Fig. 1.12
de los Comentarios a la E.070 (SENCICO 2008), que rotula un "King Kong
industrial con 40 % de huecos" entre las "unidades NO APTAS para muros portantes
confinados".

Ese dato es real, pero se usaba mal: como si el 40 % fuera una propiedad del
NOMBRE. Se bajaron SEIS fichas tecnicas de fabricantes peruanos y el rango real
va de 30 % a 50 %. El nombre no clasifica nada; el area de vacios si.

EL CRITERIO, TEXTUAL
====================
  2.1.26  "Unidad de Albanileria Solida (o Maciza): unidad cuya seccion
          transversal en cualquier plano paralelo a la superficie de asiento
          tiene un area igual o mayor que el 70% del area bruta"
  2.1.25  Hueca: la misma seccion, MENOR que el 70%.
  Tabla 2  Muro portante, zonas 2 y 3, edificio de 4 pisos a mas:
          solido artesanal NO . solido industrial SI . HUECA **NO**.

"Solida" NO quiere decir sin agujeros: el propio Art. 4.1.6 habla aparte de
"unidades totalmente solidas (sin perforaciones)". Una unidad perforada ES
solida mientras el area neta llegue al 70 %. El limite es el 30 % y nada mas.

EL INSTRUMENTO INDEPENDIENTE: EL PESO
=====================================
Tres de las seis fichas NO declaran el area de vacios. Callarlo no la esconde:
la densidad aparente (peso / volumen bruto) es el mismo dato por otro camino,

        densidad aparente = densidad del material ceramico x (1 - vacios)

La densidad del material no se inventa: se DEDUCE de las fichas que declaran
ambas cosas. Cuatro fabricantes distintos dan el mismo numero dentro del 2,6 %,
y Piramide lo confirma desde afuera: declara "densidad aparente 1,9 - 2,1 g/cm3"
en su propia ficha, que es exactamente el valor deducido.

LO QUE ESTE SCRIPT LE IMPONE AL RESTO DEL PROYECTO
==================================================
En aparejo de CABEZA el espesor del muro es el LARGO de la unidad. Todas las
unidades solidas del mercado peruano miden 24 cm de largo (las de 23 son las
huecas), asi que elegir la unidad que la Tabla 2 permite FIJA t = 0,24 m. No es
una preferencia de diseno: es una consecuencia de cumplir la norma.
"""
from proyecto import FM, VM, ESPESOR

# Fichas tecnicas de fabricante; PDF en evidencia/fichas-tecnicas-ladrillo/.
# Datos de TERCEROS, no constantes del proyecto: por eso van marcadas y no
# salen de proyecto.py.
# (marca, familia, largo, ancho, alto [cm], peso min, peso max [kg],
#  vacios declarados [%] o None, tipo NTP, f'b NTP, archivo)
FICHAS = [                                                            # no-ssot
    # --- los "18 huecos": el ladrillo que todo el mundo pide por costumbre
    ("Tayson (Morrope) 2025",    "18 huecos", 24.0, 13.0, 9.0,        # no-ssot
     3.75, 3.75, 30.0, "IV", 130.0, "tayson-kk18h.pdf"),              # no-ssot
    ("D'Surco 2020",             "18 huecos", 23.0, 12.5, 9.0,        # no-ssot
     2.610, 2.800, 46.5, "IV", 130.0, "dsurco-kk18h.pdf"),            # no-ssot
    ("Lark (Puente Piedra) 2019", "18 huecos", 23.0, 12.5, 9.0,       # no-ssot
     2.70, 2.70, None, "IV", 130.0, "lark-kk.pdf"),                   # no-ssot
    ("Sagitario (Huachipa)",     "18 huecos", 24.0, 13.0, 9.0,        # no-ssot
     2.80, 3.10, None, "IV", 130.0, "sagitario-kk18.pdf"),            # no-ssot
    ("Piramide",                 "18 huecos", 23.0, 12.5, 9.0,        # no-ssot
     2.60, 2.80, None, "IV", 130.0, "piramide-kk18.pdf"),             # no-ssot
    # --- los SOLIDOS: "30 % de vacio" / "INFES". Otro producto, otro peso.
    ("Lark KK 30% VACIO 2019",   "SOLIDO",    24.0, 13.0, 9.0,        # no-ssot
     3.80, 3.80, 30.0, "V", 180.0, "lark-kk30.pdf"),                  # no-ssot
    ("Sagitario KK INFES",       "SOLIDO",    24.0, 13.0, 9.0,        # no-ssot
     3.70, 4.00, 30.0, "V", 180.0, "sagitario-infes.pdf"),            # no-ssot
]

N_HUECOS = 18                    # no-ssot: es el nombre del producto
AREA_NETA_MINIMA = 70.0          # no-ssot: E.070 2.1.26, en porcentaje
VACIOS_MAXIMOS = 100.0 - AREA_NETA_MINIMA


def densidad_aparente(L, a, h, p_min, p_max):
    """Peso promedio declarado sobre volumen BRUTO, en g/cm3."""
    return (p_min + p_max) / 2.0 * 1000.0 / (L * a * h)


def calibracion():
    """Densidad del material ceramico, deducida de las fichas completas."""
    print("=" * 84)
    print("PASO 1 - CALIBRAR: que densidad tiene la arcilla cocida, segun las")
    print("         propias fichas que declaran peso Y vacios")
    print("=" * 84)
    print()
    print("  Si  dens.aparente = dens.material x (1 - vacios),  entonces")
    print("      dens.material = dens.aparente / (1 - vacios)")
    print()
    rho = []
    for nom, _fam, L, a, h, pmin, pmax, vac, _t, _fb, _ar in FICHAS:
        if vac is None:
            continue
        da = densidad_aparente(L, a, h, pmin, pmax)
        dm = da / (1.0 - vac / 100.0)
        rho.append(dm)
        print("  %-28s aparente %.3f  vacios %.1f %%  ->  material %.3f g/cm3"
              % (nom, da, vac, dm))
    m = sum(rho) / len(rho)
    print()
    print("  %d fabricantes distintos, en anhos distintos, y coinciden dentro"
          % len(rho))
    print("  del %.1f %%. Se adopta %.3f g/cm3."
          % (100.0 * (max(rho) - min(rho)) / m, m))
    print()
    print("  CONTROL EXTERNO: Piramide declara en su ficha \"densidad aparente")
    print("  1,9 g/cm3 (min) - 2,1 g/cm3 (max)\". Es el mismo valor, publicado por")
    print("  un fabricante que NO se uso para deducirlo. El metodo no es un truco")
    print("  aritmetico: mide lo que la industria ya sabe de su propia arcilla.")
    return m


def tabla(rho_material):
    print()
    print("=" * 84)
    print("PASO 2 - APLICAR: %d fichas, dos familias de producto" % len(FICHAS))
    print("=" * 84)
    print()
    print("  %-28s %-9s %5s %6s %7s %7s %s"
          % ("fabricante", "familia", "tipo", "peso", "aparent", "vacios",
             "E.070 2.1.26"))
    print("  %-28s %-9s %5s %6s %7s %7s %s"
          % ("", "", "NTP", "(kg)", "(g/cm3)", "(%)", ""))
    print("  " + "-" * 80)
    filas = []
    for nom, fam, L, a, h, pmin, pmax, vac, tipo, _fb, _ar in FICHAS:
        da = densidad_aparente(L, a, h, pmin, pmax)
        if vac is None:
            v = 100.0 * (1.0 - da / rho_material)
            marca = "*"          # estimado del peso
        else:
            v = vac
            marca = " "
        solida = v <= VACIOS_MAXIMOS + 1e-9
        filas.append({"nom": nom, "fam": fam, "v": v, "solida": solida,
                      "L": L, "peso": (pmin + pmax) / 2.0})
        print("  %-28s %-9s %5s %6.2f %7.3f %6.1f%s %s"
              % (nom, fam, tipo, (pmin + pmax) / 2.0, da, v, marca,
                 "SOLIDA -> admitida" if solida else "hueca -> PROHIBIDA"))
    print()
    print("  (*) area de vacios NO declarada en la ficha: estimada del peso.")
    print()
    print("  EL PESO SEPARA LAS DOS FAMILIAS SIN AMBIGUEDAD. Los solidos pesan")
    print("  3,70 - 4,00 kg; los de 18 huecos, 2,60 - 3,10. Sagitario fabrica")
    print("  AMBOS en 24 x 13 x 9: su 18 huecos pesa 2,95 kg y su INFES 3,85.")
    print("  Un kilo de diferencia en el mismo molde es exactamente el material")
    print("  que le falta al hueco. Por eso una balanza alcanza para el control")
    print("  de recepcion en obra.")
    return filas


def contradiccion():
    """El caso Piramide: el fabricante recomienda lo que la norma prohibe."""
    print()
    print("=" * 84)
    print("PASO 3 - LA TRAMPA: lo que dice el fabricante NO es lo que dice la norma")
    print("=" * 84)
    print()
    print("  La ficha de Piramide declara, en la misma hoja:")
    print("     \"Area de vacios  < 50%\"")
    print("     \"APLICACIONES: Muros portantes (albanileria confinada)\"")
    print()
    print("  Las dos cosas no pueden ser ciertas a la vez para este edificio. Con")
    print("  50 %% de vacios el area neta es 50 %%, menor que el %.0f %% que pide el"
          % AREA_NETA_MINIMA)
    print("  2.1.26, o sea HUECA por 2.1.25, y la Tabla 2 prohibe la hueca en muro")
    print("  portante de 4 pisos a mas en zonas 2 y 3. El fabricante no miente")
    print("  sobre su producto: omite el LIMITE de uso, que depende de la altura")
    print("  del edificio y de la zona sismica.")
    print()
    print("  Leccion para las especificaciones tecnicas: la hoja del fabricante")
    print("  acredita el PRODUCTO, nunca autoriza el USO. Quien autoriza es la")
    print("  Tabla 2, y hay que leerla con el numero de pisos en la mano.")


def espesor_del_muro(filas):
    """En aparejo de cabeza, el largo de la unidad ES el espesor del muro."""
    print()
    print("=" * 84)
    print("PASO 4 - CONSECUENCIA DE PROYECTO: la unidad elegida FIJA el espesor")
    print("=" * 84)
    print()
    print("  En aparejo de CABEZA la unidad atraviesa el muro, asi que")
    print("       espesor efectivo del muro  =  LARGO de la unidad")
    print()
    largos_ok = sorted({f["L"] for f in filas if f["solida"]})
    largos_no = sorted({f["L"] for f in filas if not f["solida"]})
    print("  largos de las unidades SOLIDAS (admitidas):  %s cm"
          % ", ".join("%.0f" % x for x in largos_ok))
    print("  largos de las unidades huecas (prohibidas):  %s cm"
          % ", ".join("%.0f" % x for x in largos_no))
    print()
    t_exigido = max(largos_ok) / 100.0
    print("  Las solidas del mercado peruano son TODAS de %.0f cm de largo; el"
          % max(largos_ok))
    print("  formato de 23 cm pertenece a la familia hueca. Entonces la eleccion")
    print("  normativa arrastra el espesor:")
    print()
    print("       t = %.2f m     (el 0,23 que traia el proyecto salia del" % t_exigido)
    print("                      ladrillo HUECO, que es el que no se puede usar)")
    print()
    if abs(ESPESOR - t_exigido) < 1e-9:
        print("  proyecto.py declara ESPESOR = %.2f m  ->  COHERENTE." % ESPESOR)
    else:
        print("  proyecto.py declara ESPESOR = %.2f m  ->  DESALINEADO <<<"
              % ESPESOR)
        print("  Hay que llevarlo a %.2f m y recorrer el pipeline completo."
              % t_exigido)
    print()
    print("  El cambio JUEGA A FAVOR en casi todo: mas espesor es mas area por")
    print("  metro de muro, asi que baja el esfuerzo axial, sube la densidad y")
    print("  sube la rigidez. Lo que sube en contra es el peso propio, en menor")
    print("  proporcion que el area.")
    return t_exigido


def veredicto(filas):
    print()
    print("=" * 84)
    print("VEREDICTO")
    print("=" * 84)
    h18 = [f for f in filas if f["fam"] == "18 huecos"]
    ok18 = [f for f in h18 if f["solida"]]
    sol = [f for f in filas if f["fam"] == "SOLIDO"]
    print()
    print("  De las %d fichas de \"King Kong 18 huecos\", %d califica como unidad"
          % (len(h18), len(ok18)))
    print("  SOLIDA y %d NO. De las %d fichas de la familia SOLIDA, califican %d."
          % (len(h18) - len(ok18), len(sol), len(sol)))
    print()
    print("  Asi que \"el de 18 huecos cumple?\" no tiene respuesta por el nombre.")
    print("  Lo que existe es una familia de producto DISENADA para cumplirlo, y")
    print("  se llama distinto: KK 30 % de vacio, o KK INFES. Es Tipo V (no IV),")
    print("  f'b >= 180 kgf/cm2 (no 130) y pesa un kilo mas. Cuesta mas y es el")
    print("  que corresponde.")
    print()
    print("  LO QUE SE ESPECIFICA:")
    print("   - NO por nombre comercial. \"King Kong\" solo no dice nada.")
    print("   - SI por requisito verificable: unidad SOLIDA de arcilla, Tipo IV o")
    print("     superior (NTP 399.613), AREA DE VACIOS <= %.0f %% DECLARADA EN"
          % VACIOS_MAXIMOS)
    print("     FICHA DE FABRICANTE, f'b >= 130 kgf/cm2, formato 24 x 13 x 9 cm.")
    print("   - Y se controla en obra PESANDO: por debajo de 3,5 kg, se rechaza.")
    print()
    print("  RESERVA DECLARADA. Las fichas que califican lo hacen con vacios")
    print("  = %.0f %% EXACTO, sin margen, y varias lo escriben como limite"
          % VACIOS_MAXIMOS)
    print("  (\"<= 30 %\"). Y el Art. 5.1.9 no acepta fichas: manda ENSAYO de pilas")
    print("  y muretes. La ficha prueba que el producto existe en el mercado; el")
    print("  ensayo prueba que el lote comprado sirve.")
    print()
    print("  DISPONIBILIDAD REGIONAL - hueco honesto del proyecto. La obra esta en")
    print("  Santo Domingo de Acobamba (Junin) y las seis fichas son de fabricas")
    print("  de Lima y Lambayeque. El unico fabricante de la sierra central que se")
    print("  ubico, LAROKA (Sapallanga, Huancayo), produce King Kong 18 huecos y")
    print("  pandereta, y NO publica ficha tecnica. O sea que el ladrillo que la")
    print("  norma exige NO se fabrica en la region: hay que traerlo, o exigirle")
    print("  al proveedor local el ensayo. Eso va a las especificaciones tecnicas")
    print("  y al presupuesto; no se puede tapar.")
    print()
    print("  f'm = %.0f kgf/cm2 y v'm = %.1f kgf/cm2 siguen siendo valores"
          % (FM, VM))
    print("  ADOPTADOS a confirmar por ensayo, NO leidos de estas fichas: la")
    print("  Tabla 9 tabula la ALBANILERIA (unidad + mortero), no el ladrillo")
    print("  suelto, y ninguna de las seis ensaya pilas.")


def fm_y_vm():
    """Por que 65 y 8,1 dejaron de ser 'adoptados a dedo' y pasaron a ser COTA.

    Hasta hoy el proyecto declaraba f'm = 65 y v'm = 8,1 como valores adoptados
    a confirmar, sin poder decir de donde salian mas que 'de la Tabla 9'. Con el
    producto ya identificado se puede decir algo mas fuerte: son los valores de
    una unidad PEOR que la que se va a comprar, en los DOS indicadores.
    """
    import math
    print()
    print("=" * 84)
    print("PASO 5 - f'm y v'm: no son un numero comodo, son una COTA INFERIOR")
    print("=" * 84)
    print()
    print("  La Tabla 9 tabula, para arcilla:")
    print("     %-22s f'b %5.0f   f'm %5.0f   v'm %4.1f" % ("King Kong Artesanal", 55, 35, 5.1))   # no-ssot: fila de la Tabla 9
    print("     %-22s f'b %5.0f   f'm %5.0f   v'm %4.1f  <== adoptada"
          % ("King Kong Industrial", 145, FM, VM))                     # no-ssot: fila de la Tabla 9
    print("     %-22s f'b %5.0f   f'm %5.0f   v'm %4.1f" % ("Rejilla Industrial", 215, 85, 9.2))   # no-ssot: fila de la Tabla 9
    print()
    print("  Y los Comentarios identifican a ese 'King Kong Industrial' en su Fig.")
    print("  1.12 como el de 40 % de huecos: o sea que la fila tabulada corresponde")
    print("  a una unidad HUECA, la misma que la Tabla 2 prohibe.")
    print()
    fb_tabla, vac_tabla = 145.0, 40.0          # no-ssot: los de la fila tabulada
    fb_nuestro = min(f for _n, _f, _L, _a, _h, _p1, _p2, _v, _t, f, _ar in FICHAS
                     if _f == "SOLIDO")
    vac_nuestro = VACIOS_MAXIMOS
    print("  Contra lo que se va a comprar:")
    print("     %-28s f'b        vacios" % "")
    print("     %-28s %5.0f      %4.1f %%" % ("fila tabulada (KK Industrial)", fb_tabla, vac_tabla))
    print("     %-28s %5.0f      %4.1f %%   (Tipo V)" % ("KK 30 % / INFES adoptado", fb_nuestro, vac_nuestro))
    print()
    print("  Mejor en los DOS indicadores: +%.0f %% de resistencia de unidad y"
          % (100.0 * (fb_nuestro / fb_tabla - 1.0)))
    print("  %.0f puntos menos de vacios. La albanileria que resulte no puede ser"
          % (vac_tabla - vac_nuestro))
    print("  MENOS resistente que la tabulada, asi que f'm = %.0f y v'm = %.1f son"
          % (FM, VM))
    print("  una COTA INFERIOR, no una estimacion optimista. El Art. 5.1.9 sigue")
    print("  exigiendo el ensayo de pilas y muretes; lo que cambia es que ahora el")
    print("  valor adoptado esta del lado seguro Y se puede argumentar por que.")
    print()
    print("  CONTROL DEL ART. 5.1.8, que casi nadie hace. Dice que v'm de diseno")
    print("  'no sera mayor de 0,319 raiz(f'm) MPa ( raiz(f'm) kgf/cm2 )'. Las dos")
    print("  formas NO son equivalentes, y la diferencia decide el veredicto:")
    MPA = 10.1972                              # no-ssot: kgf/cm2 por MPa
    lim_kgf = math.sqrt(FM)
    lim_mpa = 0.319 * math.sqrt(FM / MPA) * MPA
    print("     leyendo en kgf/cm2 : raiz(%.0f)          = %.3f  ->  v'm = %.1f %s"
          % (FM, lim_kgf, VM, "EXCEDE" if VM > lim_kgf else "cumple"))
    print("     leyendo en MPa     : 0,319 raiz(f'm)  = %.3f  ->  v'm = %.1f %s"
          % (lim_mpa, VM, "EXCEDE" if VM > lim_mpa else "cumple"))
    print()
    print("  El factor de conversion real entre ambas es %.4f, y la norma lo"
          % (0.319 * math.sqrt(MPA)))
    print("  redondeo a 1,000 al escribir la version en kgf/cm2. Por eso su propia")
    print("  Tabla 9 parece violar su propio Art. 5.1.8 por un 0,5 %. NO lo viola:")
    print("  el MPa es la unidad primaria de la norma y ahi cumple con holgura.")
    print("  Se conserva v'm = %.1f, que es el valor textual de la Tabla 9, y queda"
          % VM)
    print("  declarado el chequeo. Cuando llegue el ensayo, el 5.1.8 se re-aplica")
    print("  sobre el f'm medido, no sobre este.")


if __name__ == "__main__":
    r = calibracion()
    f = tabla(r)
    contradiccion()
    espesor_del_muro(f)
    fm_y_vm()
    veredicto(f)
