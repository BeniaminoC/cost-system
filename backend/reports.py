"""Definicion de los reportes. Cada reporte devuelve columnas [(titulo, tipo)] y filas.
Tipos: text | money | num | pct | var (monto con color favorable/desfavorable)."""
import costing as K


def hoja_costos(d):
    cols = [("Producto", "text"), ("Elemento", "text"), ("Unid. equiv.", "num"), ("Std. unitario", "money"), ("Std. total", "money"),
            ("Real unitario", "money"), ("Real total", "money"), ("Diferencia", "var"), ("Dif. %", "pct"), ("Resultado", "text")]
    rows = []
    def line(prod, el, a, std, real):
        eq = a["eq"]
        dif = real - std
        rows.append([prod, el, eq, std / eq if eq else 0, std, real / eq if eq else 0, real, dif,
                     dif / std * 100 if std else 0, K.clasif(dif)])
    for name, a in K.by_product(d["ordenes"]):
        line(name, "Materiales directos", a, a["std_mp"], a["real_mp"])
        line(name, "Mano de obra directa", a, a["std_mod"], a["real_mod"])
        line(name, "Costos indirectos (CIF)", a, a["std_cif"], a["real_cif"])
        line(name, "COSTO TOTAL", a, a["std"], a["real"])
    return "Hoja de costos", cols, rows


def materiales(d):
    cols = [("Orden", "text"), ("Producto", "text"), ("Materia prima", "text"), ("Cant. std. permitida", "num"), ("Cant. real", "num"),
            ("Precio std.", "money"), ("Precio real", "money"), ("Var. precio", "var"), ("Var. cantidad", "var"), ("Var. total", "var")]
    return "Reporte de materiales", cols, [[o["numero"], o["producto"], f'{m["codigo"]} {m["nombre"]}', m["q_perm"], m["q_real"], m["p_std"],
            m["p_real"], m["v_precio"], m["v_cant"], m["v_precio"] + m["v_cant"]] for o in d["ordenes"] for m in o["mp_rows"]]


def mod(d):
    cols = [("Orden", "text"), ("Producto", "text"), ("Trabajador", "text"), ("Horas std. permitidas", "num"), ("Horas reales", "num"),
            ("Tarifa std./h", "money"), ("Tarifa real/h", "money"), ("Costo estándar", "money"), ("Costo real", "money"),
            ("Var. tarifa", "var"), ("Var. eficiencia", "var")]
    return "Reporte de mano de obra directa (MOD)", cols, [[o["numero"], o["producto"], m["nombre"], m["h_perm"], m["h_real"], m["t_std"],
            m["t_real"], m["std"], m["real"], m["v_tarifa"], m["v_efic"]] for o in d["ordenes"] for m in o["mod_rows"]]


def cif(d):
    cols = [("Período", "text"), ("Concepto", "text"), ("Tipo", "text"), ("Presupuestado", "money"), ("Real", "money"),
            ("Diferencia", "var"), ("Resultado", "text")]
    rows = []
    for p in d["periodos"]:
        for x in p["cifs"]:
            dif = x["valor_real"] - x["presupuestado"]
            rows.append([p["codigo"], f'{x["codigo"]} {x["descripcion"]}', x["tipo"], x["presupuestado"], x["valor_real"], dif, K.clasif(dif)])
        u = "horas MOD" if p["base"] == "HMOD" else "unidades"
        rows.append([p["codigo"], f"Base de aplicación ({u})", "base", p["base_p"], p["base_real"], p["base_real"] - p["base_p"], ""])
        rows.append([p["codigo"], "Tasa predeterminada por unidad de base", "tasa", p["tasa"], p["tasa_real"], p["tasa_real"] - p["tasa"], ""])
        rows.append([p["codigo"], "CIF aplicado (tasa × base estándar permitida)", "aplicado", p["cif_p"], p["aplicado"], p["aplicado"] - p["cif_p"], ""])
        for n, k in [("Variación de presupuesto CIF", "v_pres"), ("Variación de volumen CIF", "v_vol"), ("Variación total CIF", "v_total")]:
            rows.append([p["codigo"], n, "variación", 0, 0, p[k], K.clasif(p[k])])
    return "Reporte de costos indirectos de fabricación (CIF)", cols, rows


def produccion(d):
    cols = [("Orden", "text"), ("Fecha", "text"), ("Producto", "text"), ("Terminada", "num"), ("En proceso", "num"), ("% avance", "pct"),
            ("Unid. equiv.", "num"), ("Costo prod. terminada", "money"), ("Costo prod. en proceso", "money"), ("Costo total real", "money")]
    rows = [[o["numero"], o["fecha"], o["producto"], o["terminada"], o["proceso"], o["avance"], o["eq"], o["costo_term"], o["costo_proc"], o["real"]]
            for o in d["ordenes"]]
    if rows:
        rows.append(["TOTAL", "", "", sum(r[3] for r in rows), sum(r[4] for r in rows), "", sum(r[6] for r in rows),
                     sum(r[7] for r in rows), sum(r[8] for r in rows), sum(r[9] for r in rows)])
    return "Reporte de producción", cols, rows


def variaciones(d):
    cols = [("Producto", "text"), ("Precio MP", "var"), ("Cantidad MP", "var"), ("Tarifa MOD", "var"), ("Eficiencia MOD", "var"),
            ("Presupuesto CIF", "var"), ("Volumen CIF", "var"), ("Variación total", "var"), ("Resultado", "text")]
    rows, ks = [], ["v_precio_mp", "v_cant_mp", "v_tarifa", "v_efic", "v_pres", "v_vol"]
    for name, a in K.by_product(d["ordenes"]):
        rows.append([name] + [a[k] for k in ks] + [a["v_total"], K.clasif(a["v_total"])])
    if rows:
        tot = K.agg(d["ordenes"])
        rows.append(["TOTAL"] + [tot[k] for k in ks] + [tot["v_total"], K.clasif(tot["v_total"])])
        allv = [tot[k] for k in ks]
        fav, des = sum(v for v in allv if v < 0), sum(v for v in allv if v > 0)
        rows.append(["Suma de variaciones favorables", "", "", "", "", "", "", fav, "Favorable"])
        rows.append(["Suma de variaciones desfavorables", "", "", "", "", "", "", des, "Desfavorable"])
    return "Reporte de variaciones", cols, rows


def estado_costos(d):
    t = K.agg(d["ordenes"])
    cols = [("Concepto", "text"), ("Valor", "money")]
    rows = [["Materiales directos utilizados (real)", t["real_mp"]], ["Mano de obra directa (real)", t["real_mod"]],
            ["Costos indirectos de fabricación (real asignado)", t["real_cif"]],
            ["= COSTOS DE MANUFACTURA DEL PERÍODO", t["real"]],
            ["(+) Inventario inicial de producción en proceso (no se arrastran saldos)", 0],
            ["(−) Inventario final de producción en proceso", -t["costo_proc"]],
            ["= COSTO DE LA PRODUCCIÓN TERMINADA", t["costo_term"]],
            ["Unidades terminadas", t["terminada"]], ["Costo unitario promedio de lo terminado", t["costo_term"] / t["terminada"] if t["terminada"] else 0],
            ["Costo estándar de la producción equivalente", t["std"]], ["Variación neta (real − estándar)", t["v_total"]],
            ["Resultado de la variación", K.clasif(t["v_total"])]]
    return "Estado de costos de producción", cols, rows


REPORTES = {"hoja_costos": hoja_costos, "materiales": materiales, "mod": mod, "cif": cif,
            "produccion": produccion, "variaciones": variaciones, "estado_costos": estado_costos}


def build(c, tipo, emp, periodo_id, producto_id):
    d = K.compute(c, emp, periodo_id or None, producto_id or None)
    titulo, cols, rows = REPORTES[tipo](d)
    e = c.execute("SELECT razon_social,nit FROM empresas WHERE id=?", (emp,)).fetchone()
    per = c.execute("SELECT codigo FROM periodos WHERE id=?", (periodo_id,)).fetchone() if periodo_id else None
    prod = c.execute("SELECT nombre FROM productos WHERE id=?", (producto_id,)).fetchone() if producto_id else None
    sub = f'{e["razon_social"]}  NIT {e["nit"]}  |  Período: {per[0] if per else "todos"}  |  Producto: {prod[0] if prod else "todos"}'
    return {"titulo": titulo, "subtitulo": sub, "columnas": cols, "filas": rows}
