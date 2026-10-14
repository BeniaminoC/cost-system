"""Motor de costos estandar: hoja de costos, produccion equivalente y analisis de variaciones.

Convenciones:  variacion > 0  => DESFAVORABLE (costo real mayor al estandar)
               variacion < 0  => FAVORABLE
"""
EPS = 0.005


def clasif(v):
    return "Desfavorable" if v > EPS else "Favorable" if v < -EPS else "Sin variación"


def _rows(c, sql, p=()):
    return [dict(r) for r in c.execute(sql, p)]


def load_ctx(c, emp):
    ctx = {"mps": {r["id"]: r for r in _rows(c, "SELECT * FROM materias_primas WHERE empresa_id=?", (emp,))},
           "trab": {r["id"]: r for r in _rows(c, "SELECT * FROM trabajadores WHERE empresa_id=?", (emp,))},
           "prods": {r["id"]: r for r in _rows(c, "SELECT * FROM productos WHERE empresa_id=?", (emp,))},
           "rec": {}, "mods": {}}
    for r in _rows(c, "SELECT * FROM producto_mp WHERE producto_id IN (SELECT id FROM productos WHERE empresa_id=?)", (emp,)):
        ctx["rec"].setdefault(r["producto_id"], []).append(r)
    for r in _rows(c, "SELECT * FROM producto_mod WHERE producto_id IN (SELECT id FROM productos WHERE empresa_id=?)", (emp,)):
        ctx["mods"].setdefault(r["producto_id"], []).append(r)
    return ctx


def unit_std(ctx, pid):
    """Costo estandar unitario de MP y MOD y horas estandar por unidad."""
    mp = sum(r["cantidad_std"] / (r["eficiencia_pct"] / 100) * ctx["mps"][r["mp_id"]]["costo_estandar"]
             for r in ctx["rec"].get(pid, []))
    mod = sum(r["horas_std"] * ctx["trab"][r["trabajador_id"]]["costo_hora"] for r in ctx["mods"].get(pid, []))
    horas = sum(r["horas_std"] for r in ctx["mods"].get(pid, []))
    return mp, mod, horas


def _orden(ctx, o, per, mpr_all, mor_all):
    pid = o["producto_id"]
    prod = ctx["prods"][pid]
    eq = o["cantidad_terminada"] + o["cantidad_proceso"] * o["avance_pct"] / 100
    rec = {r["mp_id"]: r for r in ctx["rec"].get(pid, [])}
    mods = {r["trabajador_id"]: r for r in ctx["mods"].get(pid, [])}
    mpr = {r["mp_id"]: r for r in mpr_all.get(o["id"], [])}
    mor = {r["trabajador_id"]: r for r in mor_all.get(o["id"], [])}
    mp_rows, mod_rows = [], []
    for mid in dict.fromkeys(list(rec) + list(mpr)):
        m = ctx["mps"][mid]; ps = m["costo_estandar"]
        qp = rec[mid]["cantidad_std"] / (rec[mid]["eficiencia_pct"] / 100) * eq if mid in rec else 0
        qr = mpr[mid]["cantidad_real"] if mid in mpr else 0
        pr = mpr[mid]["precio_real"] if mid in mpr else ps
        mp_rows.append(dict(codigo=m["codigo"], nombre=m["descripcion"], q_perm=qp, q_real=qr, p_std=ps, p_real=pr,
                            v_precio=(pr - ps) * qr, v_cant=(qr - qp) * ps, std=qp * ps, real=qr * pr))
    for tid in dict.fromkeys(list(mods) + list(mor)):
        t = ctx["trab"][tid]; ts = t["costo_hora"]
        hp = mods[tid]["horas_std"] * eq if tid in mods else 0
        hr = mor[tid]["horas_real"] if tid in mor else 0
        tr = mor[tid]["tarifa_real"] if tid in mor else ts
        mod_rows.append(dict(codigo=t["codigo"], nombre=f'{t["nombre"]} ({t["cargo"]})', h_perm=hp, h_real=hr, t_std=ts,
                             t_real=tr, v_tarifa=(tr - ts) * hr, v_efic=(hr - hp) * ts, std=hp * ts, real=hr * tr))
    s = lambda rows, k: sum(r[k] for r in rows)
    h_unit = sum(r["horas_std"] for r in mods.values())
    hmod = per["cif_base"] == "HMOD"
    return dict(orden_id=o["id"], numero=o["numero"], fecha=o["fecha"], periodo_id=per["id"], periodo=per["codigo"],
                producto_id=pid, producto=prod["nombre"], estado=o["estado"], terminada=o["cantidad_terminada"],
                proceso=o["cantidad_proceso"], avance=o["avance_pct"], eq=eq, ventas=prod["precio_venta"] * o["cantidad_terminada"],
                std_mp=s(mp_rows, "std"), std_mod=s(mod_rows, "std"), real_mp=s(mp_rows, "real"), real_mod=s(mod_rows, "real"),
                v_precio_mp=s(mp_rows, "v_precio"), v_cant_mp=s(mp_rows, "v_cant"),
                v_tarifa=s(mod_rows, "v_tarifa"), v_efic=s(mod_rows, "v_efic"),
                horas_real=s(mod_rows, "h_real"), horas_std=s(mod_rows, "h_perm"),
                mp_rows=mp_rows, mod_rows=mod_rows,
                _base_std=(h_unit * eq) if hmod else eq, _base_real=s(mod_rows, "h_real") if hmod else eq)


def compute(c, emp, periodo_id=None, producto_id=None):
    ctx = load_ctx(c, emp)
    sql, p = "SELECT * FROM periodos WHERE empresa_id=?", [emp]
    if periodo_id:
        sql += " AND id=?"; p.append(periodo_id)
    periodos, ordenes = [], []
    # Se cargan los datos de toda la empresa en pocas consultas (importa mucho cuando la base de datos esta en internet)
    cif_all, ord_all, mpr_all, mor_all = {}, {}, {}, {}
    for r in _rows(c, "SELECT * FROM cif WHERE empresa_id=? ORDER BY codigo", (emp,)):
        cif_all.setdefault(r["periodo_id"], []).append(r)
    for r in _rows(c, "SELECT * FROM ordenes WHERE empresa_id=? ORDER BY fecha,numero", (emp,)):
        ord_all.setdefault(r["periodo_id"], []).append(r)
    for r in _rows(c, "SELECT * FROM orden_mp WHERE orden_id IN (SELECT id FROM ordenes WHERE empresa_id=?)", (emp,)):
        mpr_all.setdefault(r["orden_id"], []).append(r)
    for r in _rows(c, "SELECT * FROM orden_mod WHERE orden_id IN (SELECT id FROM ordenes WHERE empresa_id=?)", (emp,)):
        mor_all.setdefault(r["orden_id"], []).append(r)
    for per in _rows(c, sql + " ORDER BY fecha_inicio", p):
        cifs = cif_all.get(per["id"], [])
        fijo = sum(x["presupuestado"] for x in cifs if x["tipo"] == "fijo")
        var = sum(x["presupuestado"] for x in cifs if x["tipo"] == "variable")
        bp = per["base_presupuestada"] or 1
        tf, tv = fijo / bp, var / bp
        tasa = tf + tv
        cif_real = sum(x["valor_real"] for x in cifs)
        res = [_orden(ctx, o, per, mpr_all, mor_all) for o in ord_all.get(per["id"], [])]
        bstd = sum(r["_base_std"] for r in res); breal = sum(r["_base_real"] for r in res)
        flex = fijo + tv * bstd
        vol = fijo - tf * bstd
        for r in res:
            r["std_cif"] = tasa * r["_base_std"]
            r["real_cif"] = cif_real * r["_base_real"] / breal if breal else 0
            share = r["_base_std"] / bstd if bstd else 0
            r["v_vol"] = vol * share
            r["v_pres"] = (r["real_cif"] - r["std_cif"]) - r["v_vol"]
            r["std"] = r["std_mp"] + r["std_mod"] + r["std_cif"]
            r["real"] = r["real_mp"] + r["real_mod"] + r["real_cif"]
            r["v_total"] = r["real"] - r["std"]
            r["std_unit"] = r["std"] / r["eq"] if r["eq"] else 0
            r["real_unit"] = r["real"] / r["eq"] if r["eq"] else 0
            r["costo_term"] = r["real_unit"] * r["terminada"]
            r["costo_proc"] = r["real"] - r["costo_term"]
        periodos.append(dict(id=per["id"], codigo=per["codigo"], base=per["cif_base"], base_p=bp, base_std=bstd, base_real=breal,
                             fijo_p=fijo, var_p=var, cif_p=fijo + var, cif_real=cif_real, tasa=tasa, tasa_fija=tf, tasa_var=tv,
                             tasa_real=cif_real / breal if breal else 0, aplicado=tasa * bstd, flex=flex,
                             v_pres=cif_real - flex, v_vol=vol, v_total=cif_real - tasa * bstd, cifs=cifs))
        ordenes += res
    if producto_id:
        ordenes = [o for o in ordenes if o["producto_id"] == producto_id]
    return {"periodos": periodos, "ordenes": ordenes, "ctx": ctx}


KEYS = ["eq", "terminada", "proceso", "ventas", "costo_term", "costo_proc", "std_mp", "std_mod", "std_cif", "std",
        "real_mp", "real_mod", "real_cif", "real", "v_precio_mp", "v_cant_mp", "v_tarifa", "v_efic", "v_pres", "v_vol", "v_total"]


def agg(rows):
    t = {k: sum(r[k] for r in rows) for k in KEYS}
    t["v_mat"] = t["v_precio_mp"] + t["v_cant_mp"]
    t["v_mod"] = t["v_tarifa"] + t["v_efic"]
    t["v_cif"] = t["v_pres"] + t["v_vol"]
    t["std_unit"] = t["std"] / t["eq"] if t["eq"] else 0
    t["real_unit"] = t["real"] / t["eq"] if t["eq"] else 0
    return t


def by_product(ordenes):
    g = {}
    for o in ordenes:
        g.setdefault((o["producto_id"], o["producto"]), []).append(o)
    return [(name, agg(rows)) for (_, name), rows in g.items()]


def dashboard(c, emp, periodo_id=None, producto_id=None):
    d = compute(c, emp, periodo_id, producto_id)
    t = agg(d["ordenes"])
    margen = t["ventas"] - t["costo_term"]
    dif = (t["real_unit"] - t["std_unit"]) / t["std_unit"] * 100 if t["std_unit"] else 0
    per = {}
    for o in d["ordenes"]:
        per.setdefault(o["periodo"], []).append(o)
    return {
        "kpis": dict(std_unit=t["std_unit"], real_unit=t["real_unit"], dif_pct=dif, v_mat=t["v_mat"], v_mod=t["v_mod"],
                     v_cif=t["v_cif"], costo_total=t["real"], ventas=t["ventas"], margen=margen,
                     margen_pct=margen / t["ventas"] * 100 if t["ventas"] else 0, v_total=t["v_total"]),
        "productos": [dict(nombre=n, std_unit=a["std_unit"], real_unit=a["real_unit"], margen=a["ventas"] - a["costo_term"])
                      for n, a in by_product(d["ordenes"])],
        "variaciones": [dict(n="Precio MP", v=t["v_precio_mp"]), dict(n="Cant. MP", v=t["v_cant_mp"]),
                        dict(n="Tarifa MOD", v=t["v_tarifa"]), dict(n="Efic. MOD", v=t["v_efic"]),
                        dict(n="Ppto. CIF", v=t["v_pres"]), dict(n="Vol. CIF", v=t["v_vol"])],
        "composicion": dict(mp=t["real_mp"], mod=t["real_mod"], cif=t["real_cif"]),
        "periodos": [dict(n=k, real=sum(x["real"] for x in v), std=sum(x["std"] for x in v),
                          margen=sum(x["ventas"] - x["costo_term"] for x in v)) for k, v in per.items()],
    }


def persist(c, emp):
    """Guarda en BD los costos estandar, reales y variaciones calculados."""
    d = compute(c, emp)
    ctx = d["ctx"]
    c.execute("DELETE FROM costos_estandar WHERE empresa_id=?", (emp,))
    c.execute("DELETE FROM costos_reales WHERE orden_id IN (SELECT id FROM ordenes WHERE empresa_id=?)", (emp,))
    c.execute("DELETE FROM variaciones WHERE orden_id IN (SELECT id FROM ordenes WHERE empresa_id=?)", (emp,))
    est, rea, var = [], [], []
    for per in d["periodos"]:
        for pid in ctx["prods"]:
            mp, mod, h = unit_std(ctx, pid)
            cif = per["tasa"] * (h if per["base"] == "HMOD" else 1)
            est.append((emp, per["id"], pid, mp, mod, cif, mp + mod + cif))
    for o in d["ordenes"]:
        rea.append((o["orden_id"], o["real_mp"], o["real_mod"], o["real_cif"], o["real"], o["eq"], o["real_unit"]))
        for tipo, k in [("Precio de materiales", "v_precio_mp"), ("Cantidad de materiales", "v_cant_mp"),
                        ("Tarifa de mano de obra", "v_tarifa"), ("Eficiencia de mano de obra", "v_efic"),
                        ("Presupuesto de CIF", "v_pres"), ("Volumen de CIF", "v_vol")]:
            var.append((o["orden_id"], tipo, o[k], clasif(o[k])))
    c.executemany("INSERT INTO costos_estandar(empresa_id,periodo_id,producto_id,mp_unit,mod_unit,cif_unit,total_unit) VALUES(?,?,?,?,?,?,?)", est)
    c.executemany("INSERT INTO costos_reales(orden_id,mp,mano_obra,cif,total,unidades_equiv,costo_unit) VALUES(?,?,?,?,?,?,?)", rea)
    c.executemany("INSERT INTO variaciones(orden_id,tipo,valor,clasificacion) VALUES(?,?,?,?)", var)
    c.commit()
