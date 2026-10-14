"""Metadatos de las entidades (formularios, validaciones y permisos) y validador generico."""
import datetime
import costing
from db import hash_pw


def f(n, l, t="text", req=False, **k):
    d = dict(n=n, l=l, t=t, req=req)
    d.update(k)
    return d

SI_NO = [[1, "Sí"], [0, "No"]]
EMP = "empresa_id=?"
PROD = "producto_id IN (SELECT id FROM productos WHERE empresa_id=?)"
ORD = "orden_id IN (SELECT id FROM ordenes WHERE empresa_id=?)"

ENT = {
 "empresas": dict(label="Empresas", table="empresas", lab="razon_social", order="razon_social", search=["nit", "razon_social"],
   cols=["nit", "razon_social", "regimen", "ciudad", "telefono"], unique=[["nit"]], scope=None, fields=[
   f("nit", "NIT", req=True), f("razon_social", "Razón social", req=True), f("nombre_comercial", "Nombre comercial"),
   f("regimen", "Régimen tributario", "sel", opts=[[x, x] for x in ["Responsable de IVA", "No responsable de IVA", "Régimen simple de tributación"]]),
   f("tarifa_iva", "Tarifa de IVA %", "pct"), f("retencion_fuente", "Retención en la fuente %", "pct"),
   f("actividad_ciiu", "Actividad económica (CIIU)"), f("direccion", "Dirección"), f("ciudad", "Ciudad"),
   f("telefono", "Teléfono"), f("email", "Correo electrónico", email=True)]),
 "periodos": dict(label="Períodos contables", table="periodos", lab="codigo", order="fecha_inicio DESC", scope=EMP, search=["codigo", "nombre"],
   cols=["codigo", "nombre", "fecha_inicio", "fecha_fin", "estado", "cif_base", "base_presupuestada"], unique=[["codigo"]], fields=[
   f("codigo", "Código (ej. 2026-10)", req=True), f("nombre", "Nombre"), f("fecha_inicio", "Fecha inicio", "date", True), f("fecha_fin", "Fecha fin", "date", True),
   f("estado", "Estado", "sel", True, opts=[["abierto", "Abierto"], ["cerrado", "Cerrado"]], default="abierto"),
   f("cif_base", "Base de aplicación del CIF", "sel", True, opts=[["HMOD", "Horas de mano de obra directa"], ["UNIDADES", "Unidades producidas"]], default="HMOD"),
   f("base_presupuestada", "Base presupuestada (horas o unidades)", "num", True, gt0=True)]),
 "unidades": dict(label="Unidades de medida", table="unidades", lab="nombre", order="nombre", scope=None, search=["codigo", "nombre"],
   cols=["codigo", "nombre"], unique=[["codigo"]], fields=[f("codigo", "Código", req=True), f("nombre", "Nombre", req=True)]),
 "centros_costo": dict(label="Centros de costo", table="centros_costo", lab="codigo||' - '||nombre", order="codigo", scope=EMP, search=["codigo", "nombre"],
   cols=["codigo", "nombre", "tipo"], unique=[["codigo"]], fields=[f("codigo", "Código", req=True), f("nombre", "Nombre", req=True),
   f("tipo", "Tipo", "sel", True, opts=[["productivo", "Productivo"], ["servicio", "Servicio"], ["administrativo", "Administrativo"]], default="productivo")]),
 "productos": dict(label="Productos", table="productos", lab="codigo||' - '||nombre", order="codigo", scope=EMP, search=["codigo", "nombre"],
   cols=["codigo", "nombre", "unidad_id", "precio_venta", "centro_costo_id"], unique=[["codigo"]], fields=[
   f("codigo", "Código", req=True), f("nombre", "Nombre", req=True), f("unidad_id", "Unidad de medida", "ref", True, ref="unidades"),
   f("precio_venta", "Precio de venta", "num", True), f("centro_costo_id", "Centro de costo", "ref", ref="centros_costo")]),
 "materias_primas": dict(label="Materias primas", table="materias_primas", lab="codigo||' - '||descripcion", order="codigo", scope=EMP,
   search=["codigo", "descripcion", "proveedor"], cols=["codigo", "descripcion", "proveedor", "presentacion", "unidad_id", "costo_compra", "contenido", "merma_pct", "costo_estandar"],
   unique=[["codigo"]], fields=[
   f("codigo", "Código", req=True), f("descripcion", "Descripción", req=True), f("proveedor", "Proveedor"), f("presentacion", "Presentación de compra"),
   f("unidad_id", "Unidad estándar", "ref", True, ref="unidades"), f("costo_compra", "Costo de compra de la presentación", "num", True),
   f("contenido", "Contenido (unidades estándar por presentación)", "num", True, gt0=True),
   f("merma_pct", "% de merma", "pct"), f("logistica_pct", "% costo logístico", "pct"),
   f("costo_estandar", "Costo estándar por unidad", "ro")]),
 "receta": dict(label="Receta estándar (cantidades y eficiencia)", table="producto_mp", lab="id", order="producto_id", scope=PROD,
   cols=["producto_id", "mp_id", "cantidad_std", "eficiencia_pct"], unique=[["producto_id", "mp_id"]], fields=[
   f("producto_id", "Producto", "ref", True, ref="productos"), f("mp_id", "Materia prima", "ref", True, ref="materias_primas"),
   f("cantidad_std", "Cantidad estándar por unidad", "num", True, gt0=True),
   f("eficiencia_pct", "Eficiencia % (rendimiento)", "pct", True, gt0=True, default=100)]),
 "trabajadores": dict(label="Trabajadores y cargos", table="trabajadores", lab="codigo||' - '||nombre", order="codigo", scope=EMP,
   search=["codigo", "nombre", "cargo"], cols=["codigo", "nombre", "cargo", "salario", "prestaciones_pct", "cargas_pct", "horas_mes", "costo_hora"],
   unique=[["codigo"]], fields=[
   f("codigo", "Código", req=True), f("nombre", "Nombre", req=True), f("cargo", "Cargo", req=True),
   f("centro_costo_id", "Centro de costo", "ref", ref="centros_costo"), f("salario", "Salario mensual", "num", True, gt0=True),
   f("prestaciones_pct", "Prestaciones sociales %", "pct", True), f("cargas_pct", "Cargas laborales %", "pct", True),
   f("horas_mes", "Horas estándar por mes", "num", True, gt0=True, default=240), f("costo_hora", "Tarifa estándar por hora", "ro")]),
 "producto_mod": dict(label="Hora estándar de MOD por producto", table="producto_mod", lab="id", order="producto_id", scope=PROD,
   cols=["producto_id", "trabajador_id", "horas_std"], unique=[["producto_id", "trabajador_id"]], fields=[
   f("producto_id", "Producto", "ref", True, ref="productos"), f("trabajador_id", "Trabajador / cargo", "ref", True, ref="trabajadores"),
   f("horas_std", "Horas estándar por unidad", "num", True, gt0=True)]),
 "cif": dict(label="Registro de CIF", table="cif", lab="codigo", order="periodo_id DESC, codigo", scope=EMP, search=["codigo", "descripcion"],
   cols=["periodo_id", "codigo", "descripcion", "tipo", "centro_costo_id", "presupuestado", "valor_real"], unique=[["periodo_id", "codigo"]],
   check="periodo_abierto", fields=[
   f("periodo_id", "Período", "ref", True, ref="periodos"), f("codigo", "Código", req=True), f("descripcion", "Descripción", req=True),
   f("tipo", "Tipo", "sel", True, opts=[["fijo", "Fijo"], ["variable", "Variable"]]),
   f("centro_costo_id", "Centro de costo", "ref", ref="centros_costo"),
   f("presupuestado", "CIF presupuestado", "num", True), f("valor_real", "CIF real", "num", True)]),
 "ordenes": dict(label="Órdenes de producción", table="ordenes", lab="numero", order="fecha DESC, numero DESC", scope=EMP, search=["numero"],
   cols=["numero", "fecha", "producto_id", "periodo_id", "cantidad_planeada", "cantidad_terminada", "cantidad_proceso", "avance_pct", "estado"],
   unique=[["numero"]], check="orden", fields=[
   f("numero", "Número de orden", req=True), f("periodo_id", "Período", "ref", True, ref="periodos"),
   f("producto_id", "Producto", "ref", True, ref="productos"), f("fecha", "Fecha", "date", True),
   f("cantidad_planeada", "Cantidad planeada", "num", True, gt0=True), f("cantidad_terminada", "Cantidad terminada", "num", True),
   f("cantidad_proceso", "Cantidad en proceso", "num", True), f("avance_pct", "% de avance de lo que está en proceso", "pct", True),
   f("estado", "Estado", "sel", True, opts=[["abierta", "Abierta"], ["cerrada", "Cerrada"]], default="abierta")]),
 "orden_mp": dict(label="Materia prima utilizada", table="orden_mp", lab="id", order="orden_id DESC", scope=ORD,
   cols=["orden_id", "mp_id", "cantidad_real", "precio_real"], unique=[["orden_id", "mp_id"]], fields=[
   f("orden_id", "Orden de producción", "ref", True, ref="ordenes"), f("mp_id", "Materia prima", "ref", True, ref="materias_primas"),
   f("cantidad_real", "Cantidad real utilizada", "num", True, gt0=True), f("precio_real", "Precio real por unidad", "num", True)]),
 "orden_mod": dict(label="Horas de trabajo (MOD real)", table="orden_mod", lab="id", order="orden_id DESC", scope=ORD,
   cols=["orden_id", "trabajador_id", "horas_real", "tarifa_real"], unique=[["orden_id", "trabajador_id"]], fields=[
   f("orden_id", "Orden de producción", "ref", True, ref="ordenes"), f("trabajador_id", "Trabajador / cargo", "ref", True, ref="trabajadores"),
   f("horas_real", "Horas reales trabajadas", "num", True, gt0=True), f("tarifa_real", "Tarifa real por hora", "num", True)]),
 "usuarios": dict(label="Usuarios", table="usuarios", lab="username", order="username", scope=None, admin=True, search=["username", "nombre"],
   cols=["username", "nombre", "rol", "activo"], unique=[["username"]], fields=[
   f("username", "Usuario", req=True), f("nombre", "Nombre completo", req=True),
   f("rol", "Rol", "sel", True, opts=[["admin", "Administrador"], ["usuario", "Usuario"], ["estudiante", "Estudiante (solo consulta)"]]),
   f("activo", "Activo", "sel", True, opts=SI_NO, default=1, int=True), f("password", "Contraseña (mín. 6 caracteres)", "pwd")]),
 "actividad": dict(label="Registro de actividades", table="actividad", lab="id", order="id DESC", scope=None, admin=True, ro=True, search=["usuario", "accion", "detalle"],
   cols=["fecha", "usuario", "accion", "entidad", "detalle"], unique=[], fields=[
   f("fecha", "Fecha", "ro"), f("usuario", "Usuario", "ro"), f("accion", "Acción", "ro"), f("entidad", "Entidad", "ro"), f("detalle", "Detalle", "ro")]),
}
for k, e in ENT.items():
    e["key"] = k
    e["has_emp"] = any(x["n"] == "empresa_id" for x in e.get("fields", [])) or k in ("periodos", "centros_costo", "productos", "materias_primas", "trabajadores", "cif", "ordenes")
RECALC = {"productos", "materias_primas", "receta", "trabajadores", "producto_mod", "cif", "ordenes", "orden_mp", "orden_mod", "periodos"}


def can(rol, accion, key):
    e = ENT[key]
    if rol == "admin":
        return True
    if e.get("admin"):
        return False
    if accion == "read":
        return True
    if e.get("ro"):
        return False
    return rol == "usuario" and accion in ("create", "update")


def meta_for(rol):
    out = {}
    for k, e in ENT.items():
        if not can(rol, "read", k):
            continue
        out[k] = dict(label=e["label"], cols=e["cols"], fields=e["fields"], search=bool(e.get("search")), has_emp=e["has_emp"],
                      perms={a: can(rol, a, k) for a in ("create", "update", "delete")})
    return out


def _num(v, fd, errs):
    l = fd["l"]
    try:
        x = float(str(v).replace(",", "."))
    except ValueError:
        errs.append(f"«{l}» debe ser un número válido."); return None
    if x != x or x in (float("inf"), float("-inf")):
        errs.append(f"«{l}» debe ser un número válido."); return None
    if fd["t"] == "pct":
        if x < 0 or x > 100 or (fd.get("gt0") and x == 0):
            errs.append(f"«{l}» debe ser un porcentaje {'mayor que 0 y ' if fd.get('gt0') else 'entre 0 y '}{'hasta ' if fd.get('gt0') else ''}100."); return None
    elif fd.get("gt0") and x <= 0:
        errs.append(f"«{l}» debe ser mayor que cero."); return None
    elif x < 0:
        errs.append(f"«{l}» no puede ser negativo."); return None
    return x


def validate(c, key, data, rid, emp):
    e, out, errs = ENT[key], {}, []
    for fd in e["fields"]:
        n, l, t = fd["n"], fd["l"], fd["t"]
        if t == "ro":
            continue
        v = data.get(n)
        if isinstance(v, str):
            v = v.strip()
        if v is None or v == "":
            if (fd["req"] or t == "pwd") and not (t == "pwd" and rid):
                errs.append(f"El campo «{l}» es obligatorio.")
            if t != "pwd":
                out[n] = fd.get("default", 0 if t in ("num", "pct") else None)
            continue
        if t in ("num", "pct"):
            x = _num(v, fd, errs)
            if x is not None:
                out[n] = x
        elif t == "ref":
            try:
                v = int(v)
            except (TypeError, ValueError):
                errs.append(f"Seleccione un valor válido en «{l}»."); continue
            if not c.execute(f"SELECT 1 FROM {ENT[fd['ref']]['table']} WHERE id=?", (v,)).fetchone():
                errs.append(f"El valor elegido en «{l}» no existe."); continue
            out[n] = v
        elif t == "sel":
            ok = {str(o[0]) for o in fd["opts"]}
            if str(v) not in ok:
                errs.append(f"El valor de «{l}» no es válido."); continue
            out[n] = int(v) if fd.get("int") else v
        elif t == "date":
            try:
                datetime.datetime.strptime(str(v), "%Y-%m-%d")
            except ValueError:
                errs.append(f"«{l}» no es una fecha válida (use AAAA-MM-DD)."); continue
            out[n] = v
        elif t == "pwd":
            if len(str(v)) < 6:
                errs.append("La contraseña debe tener al menos 6 caracteres.")
            else:
                out[n] = v
        else:
            if len(str(v)) > 200:
                errs.append(f"«{l}» es demasiado largo (máximo 200 caracteres)."); continue
            if fd.get("email") and ("@" not in v or "." not in v.split("@")[-1]):
                errs.append(f"«{l}» no es un correo válido."); continue
            out[n] = v
    if errs:
        return out, errs
    # Duplicidad de codigos
    for u in e["unique"]:
        w, p = [f"{n}=?" for n in u], [out.get(n) for n in u]
        if e["has_emp"]:
            w.append("empresa_id=?"); p.append(emp)
        if rid:
            w.append("id<>?"); p.append(rid)
        if c.execute(f"SELECT 1 FROM {e['table']} WHERE {' AND '.join(w)}", p).fetchone():
            lab = ", ".join(next(x["l"] for x in e["fields"] if x["n"] == n) for n in u)
            errs.append(f"Ya existe un registro con el mismo valor de «{lab}» ({', '.join(str(out.get(n)) for n in u)}). Los códigos no se pueden repetir.")
    if key == "periodos" and out["fecha_fin"] < out["fecha_inicio"]:
        errs.append("La fecha final del período no puede ser anterior a la fecha inicial.")
    if e.get("check") in ("periodo_abierto", "orden"):
        per = c.execute("SELECT * FROM periodos WHERE id=?", (out["periodo_id"],)).fetchone()
        if per["estado"] == "cerrado":
            errs.append(f"El período {per['codigo']} está cerrado. Ábralo en «Períodos contables» para registrar o modificar datos.")
        if e["check"] == "orden" and not (per["fecha_inicio"] <= out["fecha"] <= per["fecha_fin"]):
            errs.append(f"La fecha de la orden debe estar dentro del período ({per['fecha_inicio']} a {per['fecha_fin']}).")
        if e["check"] == "orden" and out["cantidad_terminada"] + out["cantidad_proceso"] == 0:
            errs.append("Registre cantidad terminada o en proceso (no pueden ser ambas cero).")
    return out, errs


def before_save(key, out):
    if key == "materias_primas":
        out["costo_estandar"] = out["costo_compra"] / out["contenido"] * (1 + out["merma_pct"] / 100) * (1 + out["logistica_pct"] / 100)
    elif key == "trabajadores":
        out["costo_hora"] = out["salario"] * (1 + out["prestaciones_pct"] / 100 + out["cargas_pct"] / 100) / out["horas_mes"]
    elif key == "usuarios" and out.get("password"):
        out["password_hash"], out["salt"] = hash_pw(out.pop("password"))
    out.pop("password", None)
