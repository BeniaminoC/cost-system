"""Acceso a configuracion, base de datos y seguridad de claves.

Dos modos (se elige solo):
  * LOCAL: SQLite en data/delicious_food.db (sin internet, como siempre).
  * WEB  : MySQL (Aiven) cuando existe la variable de entorno DATABASE_URL (o se ejecuta en Vercel).
"""
import os, sys, sqlite3, configparser, hashlib, secrets, datetime, re
from urllib.parse import urlparse, unquote


def base_dir():
    if getattr(sys, "frozen", False):          # ejecutable generado con PyInstaller
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


BASE = base_dir()
def path(*p): return os.path.join(BASE, *p)

CFG = configparser.ConfigParser()
CFG.read(path("config", "config.ini"), encoding="utf-8")
def cfg(sec, key, default=""): return CFG.get(sec, key, fallback=default)

DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()
WEB = bool(DATABASE_URL) or bool(os.environ.get("VERCEL"))
DB_PATH = path(cfg("base_datos", "ruta", "data/delicious_food.db"))


class DbError(Exception):
    """Error de configuracion o conexion con mensaje listo para mostrar al usuario."""
    def __init__(self, msg, code=503):
        super().__init__(msg)
        self.msg, self.code = msg, code


def now():
    """Fecha/hora para el registro de actividad (en la web: hora de Colombia, UTC-5, salvo ZONA_HORARIA_HORAS)."""
    if WEB:
        h = float(os.environ.get("ZONA_HORARIA_HORAS", "-5"))
        return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=h))).strftime("%Y-%m-%d %H:%M:%S")
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------- MySQL
class Row(dict):
    """Fila que se comporta como sqlite3.Row: acceso por nombre o por posicion."""
    def __getitem__(self, k):
        if isinstance(k, int):
            return list(self.values())[k]
        return dict.__getitem__(self, k)


class Cur:
    def __init__(self, cur):
        self.cur = cur
        self.lastrowid = cur.lastrowid
        self.rowcount = cur.rowcount

    def fetchone(self):
        r = self.cur.fetchone()
        return Row(r) if r is not None else None

    def fetchall(self):
        return [Row(r) for r in self.cur.fetchall()]

    def __iter__(self):
        return iter(self.fetchall())


class MyConn:
    """Envoltura de PyMySQL con la misma interfaz que usa el resto del sistema (execute/commit/...)."""
    def __init__(self, conn):
        self.conn = conn

    @staticmethod
    def _sql(sql):
        return sql.replace("?", "%s")

    def execute(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(self._sql(sql), tuple(params))
        return Cur(cur)

    def executemany(self, sql, seq):
        seq = [tuple(x) for x in seq]
        cur = self.conn.cursor()
        if seq:
            cur.executemany(self._sql(sql), seq)
        return Cur(cur)

    def commit(self): self.conn.commit()
    def rollback(self): self.conn.rollback()
    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


def _parse_url():
    if not DATABASE_URL:
        raise DbError("Falta la variable DATABASE_URL en Vercel. Agréguela en Settings → Environment Variables y haga Redeploy.")
    u = urlparse(DATABASE_URL.replace("mysql+pymysql://", "mysql://", 1))
    if u.scheme != "mysql" or not u.hostname:
        raise DbError("La variable DATABASE_URL no tiene el formato correcto. Debe ser la «Service URI» de Aiven (empieza con mysql://).")
    return dict(host=u.hostname, port=u.port or 3306, user=unquote(u.username or ""), password=unquote(u.password or ""),
                database=(u.path or "/defaultdb").lstrip("/") or "defaultdb")


def _connect_mysql():
    try:
        import pymysql, ssl
    except ImportError:
        raise DbError("Falta la biblioteca PyMySQL. Ejecute: pip install -r requirements.txt")
    p = _parse_url()
    sin_ssl = "ssl-mode=disabled" in DATABASE_URL.lower()      # solo para pruebas locales sin cifrado
    ctx = None if sin_ssl else ssl.create_default_context()
    ca = os.environ.get("MYSQL_CA_CERT")
    if sin_ssl:
        pass
    elif ca:                                 # verificacion completa si se entrega el certificado CA de Aiven
        ctx.load_verify_locations(cadata=ca)
    else:                                    # equivale a ssl-mode=REQUIRED (cifrado sin verificar el certificado)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    try:
        c = pymysql.connect(**p, charset="utf8mb4", ssl=ctx, connect_timeout=10, read_timeout=30, write_timeout=30,
                            cursorclass=pymysql.cursors.DictCursor, autocommit=False,
                            init_command="SET SESSION sql_mode=CONCAT(@@SESSION.sql_mode,',PIPES_AS_CONCAT')")
    except pymysql.err.OperationalError as e:
        code = e.args[0] if e.args else 0
        if code == 1045:
            raise DbError("La base de datos rechazó el usuario o la contraseña. Copie otra vez la Service URI completa desde Aiven, reemplácela en Vercel y haga Redeploy.")
        if code == 1049:
            raise DbError("La base de datos indicada en DATABASE_URL no existe. Use la Service URI tal como la entrega Aiven (termina en /defaultdb?ssl-mode=REQUIRED).")
        raise DbError("No se pudo conectar con la base de datos. Verifique que el servicio MySQL esté encendido (Running) en Aiven y que la Service URI sea correcta.")
    except Exception:
        raise DbError("No se pudo conectar con la base de datos. Verifique que el servicio MySQL esté encendido (Running) en Aiven y que la Service URI sea correcta.")
    return MyConn(c)


# ---------------------------------------------------------------- SQLite (local)
def _connect_sqlite():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=15)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


def connect():
    return _connect_mysql() if WEB else _connect_sqlite()


def hash_pw(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt),
                            int(cfg("seguridad", "iteraciones_hash", "120000"))).hex()
    return h, salt


# ---------------------------------------------------------------- inicializacion
def _statements(sql):
    sql = re.sub(r"--[^\n]*", "", sql)
    return [s.strip() for s in sql.split(";") if s.strip()]


def check_admin_password():
    """En la web NO se permite arrancar con una contraseña de admin por defecto."""
    pw = os.environ.get("ADMIN_PASSWORD") or ""
    if not pw or pw == "admin123":
        raise DbError("Por seguridad, en la versión web no se permite la contraseña inicial. Agregue la variable ADMIN_PASSWORD "
                      "(mínimo 8 caracteres con letras y números) en Vercel y haga Redeploy.")
    if len(pw) < 8 or not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw):
        raise DbError("La variable ADMIN_PASSWORD debe tener mínimo 8 caracteres con letras y números.")
    return pw


_READY = False


def init_db():
    """Crea tablas y datos iniciales la primera vez. En la web se ejecuta una vez por instancia y usa un candado
    de MySQL para que dos instancias no inicialicen a la vez."""
    global _READY
    if _READY:
        return
    c = connect()
    try:
        if WEB:
            c.execute("SELECT GET_LOCK('delicious_food_init', 50)").fetchone()
            try:
                vacio = True
                if c.execute("SHOW TABLES LIKE 'usuarios'").fetchone():
                    vacio = c.execute("SELECT COUNT(*) AS n FROM usuarios").fetchone()["n"] == 0
                if vacio:
                    check_admin_password()
                    with open(path("database", "schema_mysql.sql"), encoding="utf-8") as f:
                        for st in _statements(f.read()):
                            c.execute(st)
                    _seed(c)
            finally:
                try:
                    c.execute("SELECT RELEASE_LOCK('delicious_food_init')")
                except Exception:
                    pass
        else:
            if not c.execute("SELECT 1 FROM sqlite_master WHERE name='usuarios'").fetchone():
                with open(path("database", "schema.sql"), encoding="utf-8") as f:
                    c.executescript(f.read())
                _seed(c)
    finally:
        c.close()
    _READY = True


def _seed(c):
    import seed
    seed.seed_base(c)
    ej = os.environ.get("CARGAR_DATOS_EJEMPLO") if WEB else None
    ej = (ej if ej is not None else cfg("base_datos", "cargar_datos_ejemplo", "true")).lower()
    if ej in ("true", "1", "si", "sí", "yes"):
        seed.seed_ejemplo(c)
    c.commit()
