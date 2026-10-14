-- Esquema de base de datos (SQLite). Portable a MySQL cambiando
-- AUTOINCREMENT por AUTO_INCREMENT y REAL por DECIMAL(18,4).
CREATE TABLE usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE, nombre TEXT NOT NULL,
  password_hash TEXT NOT NULL, salt TEXT NOT NULL,
  rol TEXT NOT NULL CHECK (rol IN ('admin','usuario','estudiante')),
  activo INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE actividad (
  id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT NOT NULL, usuario TEXT,
  accion TEXT NOT NULL, entidad TEXT, detalle TEXT
);
CREATE TABLE empresas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nit TEXT NOT NULL UNIQUE, razon_social TEXT NOT NULL, nombre_comercial TEXT,
  regimen TEXT, tarifa_iva REAL DEFAULT 0, retencion_fuente REAL DEFAULT 0,
  actividad_ciiu TEXT, direccion TEXT, ciudad TEXT, telefono TEXT, email TEXT
);
CREATE TABLE periodos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  empresa_id INTEGER NOT NULL REFERENCES empresas(id),
  codigo TEXT NOT NULL, nombre TEXT, fecha_inicio TEXT NOT NULL, fecha_fin TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'abierto',
  cif_base TEXT NOT NULL DEFAULT 'HMOD',          -- HMOD | UNIDADES
  base_presupuestada REAL NOT NULL DEFAULT 1,      -- horas MOD o unidades presupuestadas
  UNIQUE (empresa_id, codigo)
);
CREATE TABLE unidades (
  id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT NOT NULL UNIQUE, nombre TEXT NOT NULL
);
CREATE TABLE centros_costo (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  empresa_id INTEGER NOT NULL REFERENCES empresas(id),
  codigo TEXT NOT NULL, nombre TEXT NOT NULL, tipo TEXT NOT NULL DEFAULT 'productivo',
  UNIQUE (empresa_id, codigo)
);
CREATE TABLE productos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  empresa_id INTEGER NOT NULL REFERENCES empresas(id),
  codigo TEXT NOT NULL, nombre TEXT NOT NULL,
  unidad_id INTEGER REFERENCES unidades(id), precio_venta REAL NOT NULL DEFAULT 0,
  centro_costo_id INTEGER REFERENCES centros_costo(id),
  UNIQUE (empresa_id, codigo)
);
CREATE TABLE materias_primas (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  empresa_id INTEGER NOT NULL REFERENCES empresas(id),
  codigo TEXT NOT NULL, descripcion TEXT NOT NULL, proveedor TEXT, presentacion TEXT,
  unidad_id INTEGER REFERENCES unidades(id),          -- unidad estandar
  costo_compra REAL NOT NULL DEFAULT 0,               -- precio de la presentacion
  contenido REAL NOT NULL DEFAULT 1,                  -- unidades estandar por presentacion
  merma_pct REAL NOT NULL DEFAULT 0, logistica_pct REAL NOT NULL DEFAULT 0,
  costo_estandar REAL NOT NULL DEFAULT 0,             -- por unidad estandar (calculado)
  UNIQUE (empresa_id, codigo)
);
CREATE TABLE producto_mp (                             -- receta estandar
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  producto_id INTEGER NOT NULL REFERENCES productos(id),
  mp_id INTEGER NOT NULL REFERENCES materias_primas(id),
  cantidad_std REAL NOT NULL, eficiencia_pct REAL NOT NULL DEFAULT 100,
  UNIQUE (producto_id, mp_id)
);
CREATE TABLE trabajadores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  empresa_id INTEGER NOT NULL REFERENCES empresas(id),
  codigo TEXT NOT NULL, nombre TEXT NOT NULL, cargo TEXT NOT NULL,
  centro_costo_id INTEGER REFERENCES centros_costo(id),
  salario REAL NOT NULL, prestaciones_pct REAL NOT NULL DEFAULT 0, cargas_pct REAL NOT NULL DEFAULT 0,
  horas_mes REAL NOT NULL DEFAULT 240, costo_hora REAL NOT NULL DEFAULT 0,   -- tarifa estandar (calculada)
  UNIQUE (empresa_id, codigo)
);
CREATE TABLE producto_mod (                            -- hora estandar por unidad
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  producto_id INTEGER NOT NULL REFERENCES productos(id),
  trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
  horas_std REAL NOT NULL, UNIQUE (producto_id, trabajador_id)
);
CREATE TABLE cif (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  empresa_id INTEGER NOT NULL REFERENCES empresas(id),
  periodo_id INTEGER NOT NULL REFERENCES periodos(id),
  codigo TEXT NOT NULL, descripcion TEXT NOT NULL,
  tipo TEXT NOT NULL CHECK (tipo IN ('fijo','variable')),
  centro_costo_id INTEGER REFERENCES centros_costo(id),
  presupuestado REAL NOT NULL DEFAULT 0, valor_real REAL NOT NULL DEFAULT 0,
  UNIQUE (periodo_id, codigo)
);
CREATE TABLE ordenes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  empresa_id INTEGER NOT NULL REFERENCES empresas(id),
  periodo_id INTEGER NOT NULL REFERENCES periodos(id),
  numero TEXT NOT NULL, producto_id INTEGER NOT NULL REFERENCES productos(id),
  fecha TEXT NOT NULL, cantidad_planeada REAL NOT NULL,
  cantidad_terminada REAL NOT NULL DEFAULT 0, cantidad_proceso REAL NOT NULL DEFAULT 0,
  avance_pct REAL NOT NULL DEFAULT 0, estado TEXT NOT NULL DEFAULT 'abierta',
  UNIQUE (empresa_id, numero)
);
CREATE TABLE orden_mp (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  orden_id INTEGER NOT NULL REFERENCES ordenes(id) ON DELETE CASCADE,
  mp_id INTEGER NOT NULL REFERENCES materias_primas(id),
  cantidad_real REAL NOT NULL, precio_real REAL NOT NULL, UNIQUE (orden_id, mp_id)
);
CREATE TABLE orden_mod (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  orden_id INTEGER NOT NULL REFERENCES ordenes(id) ON DELETE CASCADE,
  trabajador_id INTEGER NOT NULL REFERENCES trabajadores(id),
  horas_real REAL NOT NULL, tarifa_real REAL NOT NULL, UNIQUE (orden_id, trabajador_id)
);
-- Resultados calculados (se regeneran automaticamente al registrar datos)
CREATE TABLE costos_estandar (
  id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER NOT NULL,
  periodo_id INTEGER NOT NULL REFERENCES periodos(id), producto_id INTEGER NOT NULL REFERENCES productos(id),
  mp_unit REAL, mod_unit REAL, cif_unit REAL, total_unit REAL, UNIQUE (periodo_id, producto_id)
);
CREATE TABLE costos_reales (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  orden_id INTEGER NOT NULL UNIQUE REFERENCES ordenes(id) ON DELETE CASCADE,
  mp REAL, mano_obra REAL, cif REAL, total REAL, unidades_equiv REAL, costo_unit REAL
);
CREATE TABLE variaciones (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  orden_id INTEGER NOT NULL REFERENCES ordenes(id) ON DELETE CASCADE,
  tipo TEXT NOT NULL, valor REAL NOT NULL, clasificacion TEXT NOT NULL
);
