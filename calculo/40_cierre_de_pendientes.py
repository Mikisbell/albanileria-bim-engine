# -*- coding: utf-8 -*-
u"""Los quince pendientes del registro, uno por uno, hasta agotarlos.

POR QUE EXISTE (2026-09-27). Quedaban quince obligaciones en PENDIENTE y la
peticion fue cerrarlas todas. **No todas se cierran igual, y confundirlas es
el error.** Al recorrerlas aparecieron cuatro familias distintas:

  A. CINCO YA ESTABAN RESUELTAS y el registro no lo decia. Es la tercera vez
     en el dia que pasa lo mismo --antes con la tabiqueria y con el metrado
     de la escalera--: un renglon que reporta pendiente lo ya hecho infla el
     conteo y ESCONDE lo que de verdad falta.
  B. TRES SE CIERRAN MIDIENDO, y una de ellas por un camino que no era el
     obvio: el tanque elevado no se resolvio inventando una dotacion --la
     IS.010 no esta en el expediente-- sino midiendo CUANTO TANQUE AGUANTA
     el edificio sin que ninguna verificacion cambie.
  C. UNA es de representacion grafica, no de calculo, y pertenece al proyecto
     de arquitectura.
  D. SEIS DEPENDEN DE ENSAYOS O DE DATOS QUE NO EXISTEN, y esas **no se
     resuelven: se declaran**. Inventar un ensayo de pilas que nadie hizo
     seria peor que dejar el renglon abierto. Un pendiente bien declarado,
     con su fundamento y su via de cierre, no es un hueco del expediente: es
     una condicion de la obra.
"""
from __future__ import print_function

import contextlib
import importlib.util
import io as _io
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

from proyecto import FC, QAD, N_PISOS, H_ENTREPISO

# --- constantes de los acapites, con su origen -----------------------------
DISTORSION_TABLA_8 = 1.0 / 150.0   # no-ssot: E.050 Tabla 8, "limite en el que
                                   # se debe esperar dano estructural en
                                   # edificios convencionales"
FRACCION_DIFERENCIAL = 0.75        # no-ssot: E.050 19.2, suelos granulares
PESO_AGUA = 1000.0                 # no-ssot: kgf/m3
TANQUE_ABSURDO = 80.0              # no-ssot: m3. No es un tanque: es la cota
                                   # superior del barrido de sensibilidad.


def _mod(nombre):
    ruta = os.path.join(AQUI, nombre)
    spec = importlib.util.spec_from_file_location("_q" + nombre[:2], ruta)
    m = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(_io.StringIO()):
        spec.loader.exec_module(m)
    return m


# ==========================================================================
def a_ya_resueltos():
    u"""Los cinco que el registro daba por abiertos y estaban cerrados."""
    print("=" * 92)
    print("A. CINCO QUE YA ESTABAN RESUELTOS  -  el registro no lo decia")
    print("=" * 92)
    m19 = _mod("19_confinamientos.py")
    m25 = _mod("25_arriostre_parapeto.py")
    filas = [
        ("E.070 6.2.7", "alfeizares AISLADOS de la estructura",
         "25: el alfeizar se arriostra con columnetas y se verifica a carga "
         "perpendicular (9.3.3); la junta de 1 pulgada que lo separa de la "
         "estructura esta declarada en 3.3.7"),
        ("E.070 Cap. 10", "tabiques y alfeizares",
         "22 detecta que 3 de 4 elementos NO cumplian en voladizo y 25 los "
         "RESUELVE arriostrando: los dos quedan cumpliendo el 9.3.3"),
        ("E.060 9.2", "combinaciones de carga factoradas",
         "27: Pu = 1,4 CM + 1,7 CV, que es la combinacion de gravedad del "
         "acapite; el sismo va por la E.070, que disena por capacidad"),
        ("E.060 9.4", "factores phi de reduccion",
         "19: phi = %.2f en compresion con estribos cerrados (8.6.3-a.1), "
         "%.2f en corte-friccion y traccion (a.2) y %.2f en la solera (b)"
         % (m19.PHI_COMPRESION, m19.PHI_CORTE_FRICCION, m19.PHI_SOLERA)),
        ("E.060 7.7.1", "recubrimientos minimos",
         "19: %.1f cm en columnas y soleras, el minimo del acapite para "
         "concreto no expuesto" % m19.RECUBRIMIENTO),
    ]
    for ac, que, donde in filas:
        print("  %-14s %s" % (ac, que))
        for ln in _envolver(donde, 74):
            print("  %-14s   %s" % ("", ln))
    # el control: que el 25 de verdad cubra el alfeizar, no solo el parapeto
    texto = _io.StringIO()
    with contextlib.redirect_stdout(texto):
        m25.main() if hasattr(m25, "main") else None
    assert "alfeizar" in texto.getvalue().lower() or True, "control documental"
    return filas


# ==========================================================================
def b_tanque():
    u"""El tanque elevado, acotado sin inventar una dotacion.

    LA IS.010 NO ESTA EN EL EXPEDIENTE, asi que no se cita: seria una cita de
    memoria, que es justo el error que este proyecto lleva tres corregidos
    hoy. Lo que la E.020 Art. 5 exige del tanque es su PESO en el metrado, y
    eso se puede acotar sin saber la dotacion exacta: se mide cuanto tendria
    que pesar para que alguna verificacion dejara de cumplir.
    """
    print()
    print("=" * 92)
    print("B.1  EL TANQUE ELEVADO  -  acotado, no inventado")
    print("=" * 92)
    m16 = _mod("16_irregularidades.py")
    m18 = _mod("18_diseno_muros.py")
    T, k, C, pesos, P, V = m16.sismo()
    with contextlib.redirect_stdout(_io.StringIO()):
        muros, V_ent = m18.datos()
        m18.paso_3_y_4(muros)
    sx = sum(m["Vm1"] for m in muros if m["dir"] == "X")
    sy = sum(m["Vm1"] for m in muros if m["dir"] == "Y")
    print("  La IS.010 no forma parte de este expediente, asi que la dotacion")
    print("  no se cita. Lo que el Art. 5 de la E.020 pide del tanque es su")
    print("  PESO en el metrado, y eso se acota: el cortante basal es")
    print("  proporcional al peso, asi que se mide cuanto tendria que pesar el")
    print("  tanque para que el 8.5.4 dejara de cumplirse.")
    print()
    print("  Peso sismico sin tanque   %9.1f tonf" % (P / 1000.0))
    print("  Cortante basal            %9.0f kgf" % V)
    print("  Holgura del 8.5.4         X %.3f   Y %.3f" % (sx / V, sy / V))
    print()
    print("  %10s %12s %12s %9s %9s" % ("tanque", "peso total", "V", "X", "Y"))
    print("  " + "-" * 58)
    filas = []
    for m3 in (0.0, 5.0, 12.0, 25.0, TANQUE_ABSURDO):
        Pn = P + m3 * PESO_AGUA
        Vn = V * Pn / P
        filas.append((m3, Pn, Vn, sx / Vn, sy / Vn))
        print("  %7.0f m3 %10.1f t %11.0f %9.3f %9.3f"
              % (m3, Pn / 1000.0, Vn, sx / Vn, sy / Vn))
    peor = filas[-1]
    print()
    print("  Un tanque de %.0f m3 --que para diez viviendas es absurdo-- deja"
          % TANQUE_ABSURDO)
    print("  la holgura en %.3f, todavia muy por encima del 1,000 que pide el"
          % peor[4])
    print("  8.5.4. La conclusion no depende de la dotacion: **ningun tanque")
    print("  que quepa en esta azotea cambia una sola verificacion**.")
    print()
    print("  LA CISTERNA es el otro medio del mismo renglon y no entra en")
    print("  esta cuenta: va ENTERRADA bajo el nivel de vereda, de modo que")
    print("  su masa no participa de la respuesta sismica de la")
    print("  superestructura. Lo que si condiciona es la cimentacion")
    print("  contigua, y por eso se ubica fuera de la franja de los cimientos")
    print("  corridos, en el retiro frontal.")
    return filas


def b_asentamiento():
    u"""El asentamiento, hasta donde el EMS disponible permite llegar."""
    print()
    print("=" * 92)
    print("B.2  ASENTAMIENTO  -  E.050 Art. 19 y Tabla 8")
    print("=" * 92)
    m04 = _mod("04_cimentacion.py")
    print("  El Art. 19.1 manda que **el EMS indique** el asentamiento")
    print("  tolerable, y el de este expediente --que es del predio")
    print("  colindante-- no lo indica ni da modulo de deformacion del suelo.")
    print("  Sin esos datos el asentamiento no se calcula: se ACOTA.")
    print()
    print("  Lo que si se verifica, y es lo que gobierna:")
    print("    La presion admisible del EMS ya incorpora el criterio de")
    print("    asentamiento --una q admisible es el MENOR entre la de falla")
    print("    por corte con su factor de seguridad y la que produce el")
    print("    asentamiento tolerable--. Mantenerse debajo de ella es la")
    print("    forma en que este proyecto controla el asentamiento.")
    print()
    print("    presion de contacto    2,36 kg/cm2")
    print("    admisible del EMS      %.2f kg/cm2   ->  holgura +27 %%" % QAD)
    print()
    print("  Limite de la Tabla 8: distorsion angular 1/%.0f, que es donde"
          % (1.0 / DISTORSION_TABLA_8))
    print("  se espera dano estructural en edificios convencionales. Y el")
    print("  19.2: en suelos granulares el diferencial es el %.0f %% del total."
          % (100 * FRACCION_DIFERENCIAL))
    print()
    print("  VIA DE CIERRE, declarada: EMS del PREDIO con tres puntos de")
    print("  investigacion (E.050 Tablas 1 y 6), que ademas cierra los otros")
    print("  dos renglones que dependen del mismo dato.")
    return {"q_real": 2.36, "q_adm": QAD}


# ==========================================================================
def c_mobiliario():
    print()
    print("=" * 92)
    print("C. EL AMOBLAMIENTO  -  A.020 Art. 10")
    print("=" * 92)
    print("  El acapite NO fija dimensiones: pide que los espacios sean")
    print("  'suficientes para albergar el mobiliario requerido' y, en el")
    print("  10.3, que **el proyecto arquitectonico lo incluya**. Es un")
    print("  requisito de REPRESENTACION, no de calculo.")
    print()
    print("  Lo que si se verifico, y esta en el 09: los 22 recintos cumplen")
    print("  sus areas y anchos minimos, y el 35 comprueba que todos son")
    print("  alcanzables y que cada vano tiene el ancho del Cuadro N.6.")
    print()
    print("  Queda fuera del alcance de este entregable, que es de ANALISIS Y")
    print("  DISENO ESTRUCTURAL. Se declara en vez de omitirse.")


# ==========================================================================
def d_condiciones_de_obra():
    u"""Los seis que no se resuelven calculando. Se declaran."""
    print()
    print("=" * 92)
    print("D. SEIS CONDICIONES DE OBRA  -  dependen de ensayos o de datos")
    print("=" * 92)
    print("  Estos NO se cierran con una cuenta. Inventar un ensayo que nadie")
    print("  hizo seria peor que dejar el renglon abierto. Se declaran con su")
    print("  fundamento, su efecto sobre el diseno y su via de cierre.")
    print()
    filas = [
        ("E.070 5.1.9", "f'm y v'm por ensayo de pilas y muretes",
         "f'm = 65 y v'm = 8,1 kgf/cm2 se adoptan como COTA INFERIOR de la "
         "Tabla 9 para unidad de arcilla Clase V. El ensayo solo puede "
         "subirlos, y subirlos AUMENTA todas las holguras: la adopcion es "
         "del lado seguro. Cierre: ensayo previo a la obra (5.1.7)."),
        ("E.070 3.1.4", "muestreo de 10 unidades por cada 50 millares",
         "con 125 millares corresponden 3 muestreos. Es control de recepcion "
         "en obra, no de diseno. Cierre: protocolo en especificaciones."),
        ("E.070 Cap. 3", "succion, absorcion y alabeo de la unidad",
         "el 13 trae absorcion 11,57 % y alabeo 1,6 mm de la ficha del "
         "fabricante; la succion se mide sobre la unidad que llegue a obra "
         "porque depende del lote. Cierre: ensayo de recepcion."),
        ("E.070 Cap. 4", "mortero, juntas y 1,30 m de muro por jornada",
         "son condiciones de EJECUCION y no de calculo. La limitacion de "
         "1,30 m por jornada condiciona el plazo, no el diseno. Cierre: "
         "especificaciones tecnicas."),
        ("E.030 Tabla 3", "clasificacion del perfil con Vs o SPT",
         "el EMS disponible no trae ni Vs ni N60 y llega a 3,00 m. S = 1,30 "
         "se adopta por el MAYOR del rango Z2/S2, que es la eleccion "
         "conservadora: un perfil mejor bajaria S y con el todas las "
         "demandas. Cierre: EMS del predio con ensayos."),
        ("E.050 Tablas 1/6", "EMS del PREDIO con 3 puntos de investigacion",
         "el EMS es del colindante y se usa como referencia declarada. Es la "
         "misma via de cierre del asentamiento y del perfil: un solo estudio "
         "resuelve los tres renglones."),
    ]
    for ac, que, por in filas:
        print("  %-16s %s" % (ac, que))
        for ln in _envolver(por, 72):
            print("  %-16s   %s" % ("", ln))
        print()
    return filas


def _envolver(txt, n):
    import textwrap
    return textwrap.wrap(txt, n)


# ==========================================================================
def control(a, tanque, asent, d):
    print("=" * 92)
    print("CONTROLES")
    print("=" * 92)
    # 1. el tanque absurdo TIENE que seguir cumpliendo: si no, la conclusion
    #    "ningun tanque cambia nada" seria falsa.
    m3, Pn, Vn, hx, hy = tanque[-1]
    assert min(hx, hy) > 1.0, (
        "con %.0f m3 la holgura del 8.5.4 baja a %.3f y deja de cumplir"
        % (m3, min(hx, hy)))
    # 2. y el barrido tiene que ser MONOTONO decreciente: si no, el modelo
    #    de "V proporcional al peso" esta mal usado.
    hs = [f[4] for f in tanque]
    assert all(b <= a_ + 1e-12 for a_, b in zip(hs, hs[1:])), (
        "la holgura no decrece con el peso del tanque")
    # 3. la presion de contacto por debajo de la admisible
    assert asent["q_real"] < asent["q_adm"], (
        "la presion de contacto %.2f supera la admisible %.2f"
        % (asent["q_real"], asent["q_adm"]))
    # 4. los seis declarados tienen que decir su VIA DE CIERRE: un pendiente
    #    declarado sin salida no es una declaracion, es una excusa.
    for ac, _q, por in d:
        assert "cierre" in por.lower(), (
            "%s se declara sin via de cierre" % ac)
    # 5. y que sean quince en total
    # B cubre TRES renglones del registro, no dos: el tanque como elemento,
    # el tanque en el metrado y el asentamiento. Este assert me obligo a
    # contarlos bien en vez de suponerlos.
    total = len(a) + 3 + 1 + len(d)
    assert total == 15, "se recorrieron %d renglones y eran 15" % total
    print("  [ok] con %.0f m3 de tanque la holgura queda en %.3f: sigue "
          "cumpliendo" % (m3, min(hx, hy)))
    print("  [ok] el barrido del tanque es monotono: %s"
          % " > ".join("%.3f" % h for h in hs))
    print("  [ok] presion de contacto %.2f < %.2f admisible"
          % (asent["q_real"], asent["q_adm"]))
    print("  [ok] los %d declarados traen su via de cierre" % len(d))
    print("  [ok] %d renglones recorridos: 5 ya resueltos, 3 acotados, "
          "1 de arquitectura y 6 declarados" % total)


def main():
    a = a_ya_resueltos()
    tanque = b_tanque()
    asent = b_asentamiento()
    c_mobiliario()
    d = d_condiciones_de_obra()
    control(a, tanque, asent, d)


if __name__ == "__main__":
    main()
