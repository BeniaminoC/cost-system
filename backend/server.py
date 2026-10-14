"""Sistema de costos: API REST + archivos estaticos.

Se ejecuta de dos formas con el MISMO codigo:
  * Local  : python backend/server.py  (servidor estandar de Python, SQLite)
  * Web    : wsgi.py (Flask) en Vercel, con MySQL de Aiven. Sin estado en memoria (sesiones firmadas).
"""
import json, os, sys, time, hmac, hashlib, base64, secrets, threading, traceback, webbrowser, mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import db, costing, reports, exports
from entities import ENT, RECALC, can, meta_for, validate, before_save

FRONT = db.path("public")
MIN = int(db.cfg("seguridad", "minutos_sesion", "60"))
MAX_BODY = 4_000_000


class ApiError(Exception):
    def __init__(self, msg, code=400, errs=None):
        self.msg, self.code, self.errs = msg, code, errs


# ---------- sesiones sin estado (token firmado con HMAC) ----------
def _secret():
    k = os.environ.get("SECRET_KEY")
    if k:
        return k.encode()
    if db.WEB:   # derivada de variables que solo conoce el dueño del proyecto
        return hashlib.sha256(("costos|" + db.DATABASE_URL + "|" + (os.environ.get("ADMIN_PASSWORD") or "")).encode()).digest()
    return secrets.token_bytes(32)


SECRET = _secret()
def _b64(b): return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
def _unb64(s): return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def make_token(uid):
    p = _b64(json.dumps({"u": uid, "e": int(time.time()) + MIN * 60}, separators=(",", ":")).encode())
    return p + "." + _b64(hmac.new(SECRET, p.encode(), hashlib.sha256).digest())


def read_token(t):
    try:
        p, sig = t.split(".")
        if not hmac.compare_digest(sig, _b64(hmac.new(SECRET, p.encode(), hashlib.sha256).digest())):
            return None
        d = json.loads(_unb64(p))
        return d["u"] if d["e"] >= time.time() else None
    except Exception:
        return None


def log(c, user, accion, entidad="", detalle=""):
    c.execute("INSERT INTO actividad(fecha,usuario,accion,entidad,detalle) VALUES(?,?,?,?,?)",
              (db.now(), user, accion, entidad, detalle))
    c.commit()


# ---------- copias de seguridad (JSON portable entre SQLite y MySQL) ----------
TABLAS = ["usuarios", "unidades", "empresas", "centros_costo", "periodos", "productos", "materias_primas", "producto_mp",
          "trabajadores", "producto_mod", "cif", "ordenes", "orden_mp", "orden_mod", "costos_estandar", "costos_reales",
          "variaciones", "actividad"]


def backup_bytes(c):
    out = {"sistema": "delicious-food-costos", "version": 1, "fecha": db.now(), "tablas": {}}
    for t in TABLAS:
        rows = [dict(r) for r in c.execute(f"SELECT * FROM {t} ORDER BY id")]
        out["tablas"][t] = rows
    return json.dumps(out, ensure_ascii=False, default=str).encode("utf-8")


def restore_backup(c, data):
    import re
    if not isinstance(data, dict) or data.get("sistema") != "delicious-food-costos" or not isinstance(data.get("tablas"), dict):
        raise ApiError("El archivo no es una copia de seguridad válida de este sistema.")
    T = data["tablas"]
    users = T.get("usuarios") or []
    if not any(u.get("rol") == "admin" and u.get("activo") for u in users):
        raise ApiError("La copia no contiene ningún administrador activo; no se restauró nada.")
    total = 0
    try:
        for t in reversed(TABLAS):
            c.execute(f"DELETE FROM {t}")
        for t in TABLAS:
            rows = T.get(t) or []
            if not rows:
                continue
            cols = list(rows[0].keys())
            if not all(re.fullmatch(r"[a-z_]+", k) for k in cols):
                raise ApiError("La copia de seguridad tiene columnas no válidas.")
            c.executemany(f"INSERT INTO {t}({','.join(cols)}) VALUES({','.join('?' * len(cols))})",
                          [[r.get(k) for k in cols] for r in rows])
            total += len(rows)
        c.commit()
    except ApiError:
        c.rollback(); raise
    except Exception as ex:
        c.rollback()
        raise ApiError(f"No se pudo restaurar la copia (no se cambió nada): {ex}")
    return total


class Api:
    """Procesa una peticion. No depende del servidor HTTP: recibe datos simples y devuelve (codigo, tipo, cuerpo, cabeceras)."""

    def __init__(self, c, auth):
        self.c, self.auth, self.new_token = c, auth, None

    def out(self, body, code=200, ctype="application/json", extra=None):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
        h = {"Cache-Control": "no-store"}
        if self.new_token:
            h["X-Token"] = self.new_token
        h.update(extra or {})
        return code, ctype + ("; charset=utf-8" if ctype.startswith("text") or ctype == "application/json" else ""), body, h

    def fallos(self, name):
        """Intentos fallidos recientes (se cuentan en la base de datos, asi funciona con varias instancias)."""
        seg = int(db.cfg("seguridad", "bloqueo_segundos", "60"))
        import datetime
        desde = (datetime.datetime.strptime(db.now(), "%Y-%m-%d %H:%M:%S") - datetime.timedelta(seconds=seg)).strftime("%Y-%m-%d %H:%M:%S")
        return self.c.execute("SELECT COUNT(*) AS n FROM actividad WHERE usuario=? AND accion='login_fallido' AND fecha>=?",
                              (name[:100], desde)).fetchone()["n"]

    # ---------- seguridad ----------
    def user(self):
        uid = read_token(self.auth.replace("Bearer ", "").strip())
        u = self.c.execute("SELECT id,username,nombre,rol,activo FROM usuarios WHERE id=?", (uid,)).fetchone() if uid else None
        if not u or not u["activo"]:
            raise ApiError("Su sesión expiró. Inicie sesión nuevamente.", 401)
        self.new_token = make_token(u["id"])          # sesion deslizante: se renueva en cada peticion
        return {"id": u["id"], "username": u["username"], "nombre": u["nombre"], "rol": u["rol"]}

    def need(self, rol, accion, ent):
        if not can(rol, accion, ent):
            raise ApiError("No tiene permiso para realizar esta acción.", 403)

    def emp(self, q):
        try:
            e = int(q.get("empresa_id") or 0)
        except ValueError:
            e = 0
        return e

    # ---------- API ----------
    def api(self, m, r, q, body):
        c = self.c
        if r == ["login"] and m == "POST":
            name = str(body.get("username", "")).strip()
            if self.fallos(name) >= int(db.cfg("seguridad", "intentos_maximos_login", "5")):
                raise ApiError("Demasiados intentos fallidos. Espere un momento e intente de nuevo.", 429)
            u = c.execute("SELECT * FROM usuarios WHERE username=?", (name,)).fetchone()
            if not u or not u["activo"] or db.hash_pw(str(body.get("password", "")), u["salt"])[0] != u["password_hash"]:
                log(c, name[:100], "login_fallido", "usuarios", "Credenciales incorrectas")
                raise ApiError("Usuario o contraseña incorrectos.", 401)
            tok = make_token(u["id"])
            usr = {"id": u["id"], "username": u["username"], "nombre": u["nombre"], "rol": u["rol"]}
            log(c, name, "inicio_sesion", "usuarios", f"Rol {u['rol']}")
            return self.out({"token": tok, "user": usr})
        user = self.user()
        rol = user["rol"]
        if r == ["logout"]:
            log(c, user["username"], "cierre_sesion", "usuarios")
            return self.out({"ok": True})
        if r == ["respaldo"] and m == "GET":
            self.need(rol, "read", "usuarios")          # solo administrador
            log(c, user["username"], "respaldo", "sistema", "Descarga de copia de seguridad")
            return self.out(backup_bytes(c), 200, "application/json",
                            {"Content-Disposition": f'attachment; filename="respaldo-costos-{db.now()[:10]}.json"'})
        if r == ["restaurar"] and m == "POST":
            self.need(rol, "read", "usuarios")
            if str(body.get("confirmar", "")).strip().upper() != "RESTAURAR":
                raise ApiError("Escriba RESTAURAR para confirmar.")
            n = restore_backup(c, body.get("datos"))
            log(c, user["username"], "restauracion", "sistema", f"Restauración de copia ({n} filas)")
            return self.out({"ok": True, "filas": n})
        if r == ["meta"]:
            return self.out({"entities": meta_for(rol), "user": user,
                             "app": {"nombre": db.cfg("aplicacion", "nombre"), "moneda": db.cfg("aplicacion", "moneda", "COP"), "web": db.WEB}})
        if r == ["cambiar-clave"] and m == "POST":
            row = c.execute("SELECT * FROM usuarios WHERE id=?", (user["id"],)).fetchone()
            if db.hash_pw(str(body.get("actual", "")), row["salt"])[0] != row["password_hash"]:
                raise ApiError("La contraseña actual no es correcta.")
            if len(str(body.get("nueva", ""))) < 6:
                raise ApiError("La contraseña nueva debe tener al menos 6 caracteres.")
            h, s = db.hash_pw(body["nueva"])
            c.execute("UPDATE usuarios SET password_hash=?,salt=? WHERE id=?", (h, s, user["id"])); c.commit()
            log(c, user["username"], "cambio_clave", "usuarios")
            return self.out({"ok": True})
        emp = self.emp(q)
        if r[0] == "opciones":
            k = r[1]; E = ENT.get(k)
            if not E: raise ApiError("Entidad desconocida", 404)
            sql, p = f"SELECT id, {E['lab']} AS label FROM {E['table']}", []
            if E["scope"]:
                sql += f" WHERE {E['scope']}"; p.append(emp)
            return self.out([dict(x) for x in c.execute(sql + " ORDER BY label", p)])
        if r[0] == "e" and len(r) >= 2:
            return self.crud(m, r, q, body, user, emp)
        if r == ["dashboard"]:
            return self.out(costing.dashboard(c, emp, int(q.get("periodo_id") or 0) or None, int(q.get("producto_id") or 0) or None))
        if r == ["cif-resumen"]:
            d = costing.compute(c, emp, int(q.get("periodo_id") or 0) or None)
            return self.out([{k: v for k, v in p.items() if k != "cifs"} for p in d["periodos"]])
        if r == ["recalcular"] and m == "POST":
            self.need(rol, "update", "ordenes")
            costing.persist(c, emp)
            log(c, user["username"], "recalculo_costos", "costos", f"Empresa {emp}")
            return self.out({"ok": True})
        if r[0] == "reporte" and len(r) == 2 and r[1] in reports.REPORTES:
            rep = reports.build(c, r[1], emp, int(q.get("periodo_id") or 0), int(q.get("producto_id") or 0))
            fmt = q.get("formato", "json")
            if fmt == "json":
                return self.out(rep)
            log(c, user["username"], "exportar", "reportes", f"{rep['titulo']} ({fmt})")
            if fmt == "xlsx":
                return self.out(exports.xlsx_bytes(rep["titulo"], rep["subtitulo"], rep["columnas"], rep["filas"]), 200,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            if fmt == "pdf":
                return self.out(exports.pdf_bytes(rep["titulo"], rep["subtitulo"], rep["columnas"], rep["filas"]), 200, "application/pdf")
        raise ApiError("Ruta no encontrada", 404)

    def crud(self, m, r, q, body, user, emp):
        c, rol, k = self.c, user["rol"], r[1]
        E = ENT.get(k)
        if not E: raise ApiError("Entidad desconocida", 404)
        t = E["table"]
        if m == "GET" and len(r) == 2:
            self.need(rol, "read", k)
            sel = ["t.*"]
            for fd in E["fields"]:
                if fd["t"] == "ref":
                    R = ENT[fd["ref"]]
                    sel.append(f"(SELECT {R['lab']} FROM {R['table']} WHERE id=t.{fd['n']}) AS {fd['n']}__l")
            w, p = [], []
            if E["scope"]: w.append(E["scope"]); p.append(emp)
            if q.get("periodo_id") and any(x["n"] == "periodo_id" for x in E["fields"]):
                w.append("periodo_id=?"); p.append(int(q["periodo_id"]))
            if q.get("q") and E.get("search"):
                w.append("(" + " OR ".join(f"{s} LIKE ?" for s in E["search"]) + ")"); p += [f"%{q['q']}%"] * len(E["search"])
            sql = f"SELECT {','.join(sel)} FROM {t} t" + (f" WHERE {' AND '.join(w)}" if w else "") + f" ORDER BY {E['order']} LIMIT 2000"
            rows = [dict(x) for x in c.execute(sql, p)]
            for x in rows:
                x.pop("password_hash", None); x.pop("salt", None)
            return self.out(rows)
        if m == "GET":
            self.need(rol, "read", k)
            x = c.execute(f"SELECT * FROM {t} WHERE id=?", (r[2],)).fetchone()
            if not x: raise ApiError("Registro no encontrado", 404)
            x = dict(x); x.pop("password_hash", None); x.pop("salt", None)
            return self.out(x)
        if m in ("POST", "PUT"):
            rid = int(r[2]) if m == "PUT" else None
            self.need(rol, "update" if rid else "create", k)
            out, errs = validate(c, k, body, rid, emp)
            if errs: raise ApiError("Corrija los datos indicados.", 422, errs)
            before_save(k, out)
            if E["has_emp"]: out["empresa_id"] = emp
            try:
                if rid:
                    c.execute(f"UPDATE {t} SET {','.join(f'{a}=?' for a in out)} WHERE id=?", list(out.values()) + [rid])
                else:
                    rid = c.execute(f"INSERT INTO {t}({','.join(out)}) VALUES({','.join('?' * len(out))})", list(out.values())).lastrowid
                c.commit()
            except Exception as ex:
                c.rollback()
                raise ApiError(f"No se pudo guardar el registro: {ex}")
            if k in RECALC: costing.persist(c, emp)
            log(c, user["username"], "editar" if m == "PUT" else "crear", k, f"id={rid} " + str({a: v for a, v in out.items() if a not in ('password_hash', 'salt')})[:180])
            return self.out({"id": rid})
        if m == "DELETE":
            self.need(rol, "delete", k)
            if k == "usuarios" and int(r[2]) == user["id"]:
                raise ApiError("No puede eliminar su propio usuario mientras está conectado.", 409)
            try:
                c.execute(f"DELETE FROM {t} WHERE id=?", (r[2],)); c.commit()
            except Exception:
                c.rollback()
                raise ApiError("No se puede eliminar: el registro está siendo usado por otros datos (por ejemplo, órdenes, recetas o períodos). Elimine primero los registros relacionados.", 409)
            if k in RECALC: costing.persist(c, emp)
            log(c, user["username"], "eliminar", k, f"id={r[2]}")
            return self.out({"ok": True})
        raise ApiError("Método no permitido", 405)




def static(p):
    p = "/index.html" if p in ("/", "") else p
    fp = os.path.normpath(os.path.join(FRONT, p.lstrip("/")))
    if not fp.startswith(FRONT) or not os.path.isfile(fp):
        return 404, "application/json; charset=utf-8", json.dumps({"error": "No encontrado"}).encode(), {"Cache-Control": "no-store"}
    with open(fp, "rb") as f:
        ct = mimetypes.guess_type(fp)[0] or "application/octet-stream"
        return 200, ct + ("; charset=utf-8" if ct.startswith("text") else ""), f.read(), {"Cache-Control": "no-store"}


def _err(msg, code, errs=None):
    return code, "application/json; charset=utf-8", json.dumps({"error": msg, "errores": errs or [msg]}, ensure_ascii=False).encode(), {"Cache-Control": "no-store"}


def dispatch(method, path, query, auth, raw):
    """Punto de entrada unico (lo usan el servidor local y Flask/Vercel)."""
    if not path.startswith("/api/"):
        return static(path)
    c = None
    try:
        if len(raw or b"") > MAX_BODY:
            raise ApiError("El archivo supera el máximo de 4 MB.", 413)
        body = json.loads(raw) if raw else {}
        db.init_db()
        c = db.connect()
        return Api(c, auth).api(method, path[5:].strip("/").split("/"), query, body)
    except ApiError as e:
        return _err(e.msg, e.code, e.errs)
    except db.DbError as e:
        return _err(e.msg, e.code)
    except json.JSONDecodeError:
        return _err("La petición no es válida.", 400)
    except Exception:
        traceback.print_exc()
        return _err("Ocurrió un error interno. Revise los registros (logs) del sistema.", 500)
    finally:
        if c is not None:
            c.close()


class Handler(BaseHTTPRequestHandler):
    """Servidor local (modo sin internet)."""
    def log_message(self, *a): pass
    def do_GET(self): self.go("GET")
    def do_POST(self): self.go("POST")
    def do_PUT(self): self.go("PUT")
    def do_DELETE(self): self.go("DELETE")

    def go(self, m):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        code, ctype, body, hdr = dispatch(m, u.path, {k: v[0] for k, v in parse_qs(u.query).items()},
                                          self.headers.get("Authorization") or "", self.rfile.read(n) if n else b"")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in hdr.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)


def main():
    db.init_db()
    host, port = db.cfg("servidor", "host", "127.0.0.1"), int(db.cfg("servidor", "puerto", "8080"))
    srv = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print(f"\n  {db.cfg('aplicacion', 'nombre')}\n  Sistema en ejecución: {url}\n  (Cierre esta ventana para detener el sistema)\n")
    if db.cfg("servidor", "abrir_navegador", "true").lower() == "true":
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
