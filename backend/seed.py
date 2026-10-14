"""Datos iniciales: usuarios, unidades y un caso de ejemplo tomado del Excel DELICIOUS FOOD."""
import os, random
import db
from db import hash_pw
import costing


def seed_base(c):
    if db.WEB:   # version web: solo admin (contraseña = variable ADMIN_PASSWORD); los demas usuarios se crean desde el sistema
        users = [("admin", "Administrador", "admin", db.check_admin_password())]
        for u, n, r, var in [("usuario", "Usuario operativo", "usuario", "USUARIO_PASSWORD"),
                             ("estudiante", "Estudiante", "estudiante", "ESTUDIANTE_PASSWORD")]:
            if len(os.environ.get(var) or "") >= 6:
                users.append((u, n, r, os.environ[var]))
    else:
        users = [("admin", "Administrador", "admin", "admin123"), ("usuario", "Usuario operativo", "usuario", "usuario123"),
                 ("estudiante", "Estudiante", "estudiante", "estudiante123")]
    for u, n, r, p in users:
        h, s = hash_pw(p)
        c.execute("INSERT INTO usuarios(username,nombre,password_hash,salt,rol) VALUES(?,?,?,?,?)", (u, n, h, s, r))
    for cod, nom in [("PZA", "Pieza"), ("POR", "Porción"), ("KG", "Kilo"), ("LB", "Libra"), ("GR", "Gramo"),
                     ("LT", "Litro"), ("ML", "Mililitro"), ("OZ", "Onza"), ("GAL", "Galón"),
                     ("M3", "Metro cúbico"), ("ROL", "Rollo"), ("HR", "Hora")]:
        c.execute("INSERT INTO unidades(codigo,nombre) VALUES(?,?)", (cod, nom))


def seed_ejemplo(c):
    U = {r["codigo"]: r["id"] for r in c.execute("SELECT id,codigo FROM unidades")}
    c.execute("""INSERT INTO empresas(nit,razon_social,nombre_comercial,regimen,tarifa_iva,retencion_fuente,
                 actividad_ciiu,ciudad,email) VALUES('900000001-1','Delicious Food S.A.S. (ejemplo)','Delicious Food',
                 'Régimen simple de tributación',0,0,'5611','Bucaramanga','info@deliciousfood.example')""")
    E = c.execute("SELECT id FROM empresas").fetchone()["id"]
    cc = {}
    for cod, nom, tipo in [("CC-PROD", "Cocina - Producción", "productivo"), ("CC-SRV", "Servicios generales", "servicio"),
                           ("CC-ADM", "Administración", "administrativo")]:
        cc[cod] = c.execute("INSERT INTO centros_costo(empresa_id,codigo,nombre,tipo) VALUES(?,?,?,?)", (E, cod, nom, tipo)).lastrowid
    P = {}
    for cod, nom, pv in [("DF-001", "Arepa de chorizo", 7000), ("DF-002", "Perro caliente", 7000), ("DF-003", "Suizo", 10000)]:
        P[cod] = c.execute("INSERT INTO productos(empresa_id,codigo,nombre,unidad_id,precio_venta,centro_costo_id) VALUES(?,?,?,?,?,?)",
                           (E, cod, nom, U["PZA"], pv, cc["CC-PROD"])).lastrowid
    # Materias primas: (cod, descripcion, presentacion, unidad estandar, costo compra, contenido)
    M, CE = {}, {}
    for cod, des, pres, un, cc_, cont in [
        ("MP-001", "Arepa", "Paquete x10", "PZA", 4800, 10), ("MP-002", "Chorizo", "Paquete x8", "PZA", 9700, 8),
        ("MP-003", "Jamón", "Paquete x24", "PZA", 8800, 24), ("MP-004", "Queso", "Paquete x22", "PZA", 10700, 22),
        ("MP-005", "Queso costeño", "Libra (500 g)", "GR", 14000, 500), ("MP-006", "Recorte de papa", "Kilo (1000 g)", "GR", 10500, 1000),
        ("MP-007", "Salsas", "Presentación 14,35 kg", "GR", 23000, 14350), ("MP-008", "Pan de perro", "Paquete x10", "PZA", 5200, 10),
        ("MP-009", "Salchicha long", "Paquete x22", "PZA", 28800, 22), ("MP-010", "Suiza", "Paquete x8 (4 porciones c/u)", "POR", 40800, 32),
        ("MP-011", "Papa", "Bulto 2,5 kg", "GR", 15800, 2500), ("MP-012", "Lechuga", "Unidad (9,6 porciones)", "POR", 3500, 9.6)]:
        CE[cod] = cc_ / cont
        M[cod] = c.execute("""INSERT INTO materias_primas(empresa_id,codigo,descripcion,proveedor,presentacion,unidad_id,costo_compra,
                    contenido,costo_estandar) VALUES(?,?,?,?,?,?,?,?,?)""",
                           (E, cod, des, "Proveedor local", pres, U[un], cc_, cont, cc_ / cont)).lastrowid
    R = {"DF-001": [("MP-001", 1, 98), ("MP-002", 1, 100), ("MP-003", 1, 100), ("MP-004", 1, 100), ("MP-005", 10, 100),
                    ("MP-006", 10, 95), ("MP-007", 4.79, 95)],
         "DF-002": [("MP-008", 1, 100), ("MP-009", 1, 100), ("MP-006", 10, 95), ("MP-007", 4.79, 95), ("MP-005", 10, 100)],
         "DF-003": [("MP-010", 1, 100), ("MP-002", 0.5, 100), ("MP-011", 10, 100), ("MP-012", 1, 90), ("MP-006", 1, 95),
                    ("MP-005", 10, 100), ("MP-007", 4.79, 95)]}
    for p, lines in R.items():
        for m, q, e in lines:
            c.execute("INSERT INTO producto_mp(producto_id,mp_id,cantidad_std,eficiencia_pct) VALUES(?,?,?,?)", (P[p], M[m], q, e))
    # Operarios: suman los $3.520.000 de "Salarios Operativos" del Excel (reparto ilustrativo)
    T, CH = {}, {}
    for cod, nom, cargo, sal in [("OP-001", "Cocinero 1", "Cocinero", 1300000), ("OP-002", "Cocinero 2", "Cocinero", 1300000),
                                 ("OP-003", "Auxiliar de cocina", "Auxiliar", 920000)]:
        ch = round(sal * (1 + .2183 + .30) / 240, 4)
        CH[cod] = ch
        T[cod] = c.execute("""INSERT INTO trabajadores(empresa_id,codigo,nombre,cargo,centro_costo_id,salario,prestaciones_pct,
                    cargas_pct,horas_mes,costo_hora) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                           (E, cod, nom, cargo, cc["CC-PROD"], sal, 21.83, 30, 240, ch)).lastrowid
    for p, t, h in [("DF-001", "OP-001", .12), ("DF-002", "OP-002", .10), ("DF-003", "OP-001", .10), ("DF-003", "OP-003", .05)]:
        c.execute("INSERT INTO producto_mod(producto_id,trabajador_id,horas_std) VALUES(?,?,?)", (P[p], T[t], h))
    # Periodos y CIF
    PER = {}
    for cod, nom, i, f, est in [("2026-08", "Agosto 2026", "2026-08-01", "2026-08-31", "cerrado"),
                                ("2026-09", "Septiembre 2026", "2026-09-01", "2026-09-30", "cerrado"),
                                ("2026-10", "Octubre 2026", "2026-10-01", "2026-10-31", "abierto")]:
        PER[cod] = c.execute("""INSERT INTO periodos(empresa_id,codigo,nombre,fecha_inicio,fecha_fin,estado,cif_base,base_presupuestada)
                    VALUES(?,?,?,?,?,?,'HMOD',195)""", (E, cod, nom, i, f, est)).lastrowid
    real = {"2026-08": (205000, 170000, 1000000), "2026-09": (231000, 176000, 1000000), "2026-10": (0, 0, 0)}
    for per, (g, s, a) in real.items():
        for cod, des, tipo, cen, pres, val in [("CIF-001", "Gas propano", "variable", "CC-PROD", 220000, g),
                                               ("CIF-002", "Servicios públicos (agua y luz)", "fijo", "CC-SRV", 165000, s),
                                               ("CIF-003", "Sueldos administrativos / supervisión", "fijo", "CC-ADM", 1000000, a)]:
            c.execute("""INSERT INTO cif(empresa_id,periodo_id,codigo,descripcion,tipo,centro_costo_id,presupuestado,valor_real)
                        VALUES(?,?,?,?,?,?,?,?)""", (E, PER[per], cod, des, tipo, cc[cen], pres, val))
    # Ordenes de produccion con consumos reales (variaciones simuladas con semilla fija)
    rnd = random.Random(2026)
    n = 0
    omp, omod = [], []          # se insertan por lotes (importa cuando la base de datos esta en internet)
    for per, (d1, d2) in {"2026-08": ("2026-08-12", "2026-08-28"), "2026-09": ("2026-09-12", "2026-09-27")}.items():
        for pcod, total in [("DF-001", 700), ("DF-002", 450), ("DF-003", 300)]:
            for k, fecha in enumerate((d1, d2)):
                n += 1
                q = total / 2
                proc, av = (20, 60) if (per == "2026-09" and pcod == "DF-003" and k == 1) else (0, 0)
                ter = q - proc
                eq = ter + proc * av / 100
                oid = c.execute("""INSERT INTO ordenes(empresa_id,periodo_id,numero,producto_id,fecha,cantidad_planeada,
                        cantidad_terminada,cantidad_proceso,avance_pct,estado) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                                (E, PER[per], f"OP-{per[2:4]}{per[5:]}-{n:03d}", P[pcod], fecha, q, ter, proc, av,
                                 "abierta" if proc else "cerrada")).lastrowid
                for m, qs, ef in R[pcod]:
                    ps = CE[m]
                    omp.append((oid, M[m], round(qs / (ef / 100) * eq * (1 + rnd.uniform(0, .06)), 3),
                                round(ps * (1 + rnd.uniform(-.02, .08)), 4)))
                for pc, tc, hs in [x for x in [("DF-001", "OP-001", .12), ("DF-002", "OP-002", .10), ("DF-003", "OP-001", .10), ("DF-003", "OP-003", .05)] if x[0] == pcod]:
                    ch = CH[tc]
                    omod.append((oid, T[tc], round(hs * eq * (1 + rnd.uniform(0, .10)), 3), round(ch * (1 + rnd.uniform(0, .04)), 4)))
    c.executemany("INSERT INTO orden_mp(orden_id,mp_id,cantidad_real,precio_real) VALUES(?,?,?,?)", omp)
    c.executemany("INSERT INTO orden_mod(orden_id,trabajador_id,horas_real,tarifa_real) VALUES(?,?,?,?)", omod)
    c.commit()
    costing.persist(c, E)
