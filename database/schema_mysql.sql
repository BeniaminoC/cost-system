-- Esquema MySQL (Aiven) generado a partir de schema.sql. Las llaves foraneas se declaran como restricciones de tabla
-- (MySQL ignora las REFERENCES en linea).
CREATE TABLE IF NOT EXISTS usuarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(190) NOT NULL UNIQUE,
  nombre VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  salt VARCHAR(255) NOT NULL,
  rol VARCHAR(255) NOT NULL CHECK (rol IN ('admin','usuario','estudiante')),
  activo INT NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS actividad (
  id INT AUTO_INCREMENT PRIMARY KEY,
  fecha VARCHAR(255) NOT NULL,
  usuario VARCHAR(255),
  accion VARCHAR(255) NOT NULL,
  entidad VARCHAR(255),
  detalle TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS empresas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nit VARCHAR(190) NOT NULL UNIQUE,
  razon_social VARCHAR(255) NOT NULL,
  nombre_comercial VARCHAR(255),
  regimen VARCHAR(255),
  tarifa_iva DOUBLE DEFAULT 0,
  retencion_fuente DOUBLE DEFAULT 0,
  actividad_ciiu VARCHAR(255),
  direccion VARCHAR(255),
  ciudad VARCHAR(255),
  telefono VARCHAR(255),
  email VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS periodos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT NOT NULL,
  codigo VARCHAR(190) NOT NULL,
  nombre VARCHAR(255),
  fecha_inicio VARCHAR(255) NOT NULL,
  fecha_fin VARCHAR(255) NOT NULL,
  estado VARCHAR(255) NOT NULL DEFAULT 'abierto',
  cif_base VARCHAR(255) NOT NULL DEFAULT 'HMOD',
  base_presupuestada DOUBLE NOT NULL DEFAULT 1,
  UNIQUE (empresa_id, codigo),
  FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS unidades (
  id INT AUTO_INCREMENT PRIMARY KEY,
  codigo VARCHAR(190) NOT NULL UNIQUE,
  nombre VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS centros_costo (
  id INT AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT NOT NULL,
  codigo VARCHAR(190) NOT NULL,
  nombre VARCHAR(255) NOT NULL,
  tipo VARCHAR(255) NOT NULL DEFAULT 'productivo',
  UNIQUE (empresa_id, codigo),
  FOREIGN KEY (empresa_id) REFERENCES empresas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS productos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT NOT NULL,
  codigo VARCHAR(190) NOT NULL,
  nombre VARCHAR(255) NOT NULL,
  unidad_id INT,
  precio_venta DOUBLE NOT NULL DEFAULT 0,
  centro_costo_id INT,
  UNIQUE (empresa_id, codigo),
  FOREIGN KEY (empresa_id) REFERENCES empresas(id),
  FOREIGN KEY (unidad_id) REFERENCES unidades(id),
  FOREIGN KEY (centro_costo_id) REFERENCES centros_costo(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS materias_primas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT NOT NULL,
  codigo VARCHAR(190) NOT NULL,
  descripcion VARCHAR(255) NOT NULL,
  proveedor VARCHAR(255),
  presentacion VARCHAR(255),
  unidad_id INT,
  costo_compra DOUBLE NOT NULL DEFAULT 0,
  contenido DOUBLE NOT NULL DEFAULT 1,
  merma_pct DOUBLE NOT NULL DEFAULT 0,
  logistica_pct DOUBLE NOT NULL DEFAULT 0,
  costo_estandar DOUBLE NOT NULL DEFAULT 0,
  UNIQUE (empresa_id, codigo),
  FOREIGN KEY (empresa_id) REFERENCES empresas(id),
  FOREIGN KEY (unidad_id) REFERENCES unidades(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS producto_mp (
  id INT AUTO_INCREMENT PRIMARY KEY,
  producto_id INT NOT NULL,
  mp_id INT NOT NULL,
  cantidad_std DOUBLE NOT NULL,
  eficiencia_pct DOUBLE NOT NULL DEFAULT 100,
  UNIQUE (producto_id, mp_id),
  FOREIGN KEY (producto_id) REFERENCES productos(id),
  FOREIGN KEY (mp_id) REFERENCES materias_primas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS trabajadores (
  id INT AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT NOT NULL,
  codigo VARCHAR(190) NOT NULL,
  nombre VARCHAR(255) NOT NULL,
  cargo VARCHAR(255) NOT NULL,
  centro_costo_id INT,
  salario DOUBLE NOT NULL,
  prestaciones_pct DOUBLE NOT NULL DEFAULT 0,
  cargas_pct DOUBLE NOT NULL DEFAULT 0,
  horas_mes DOUBLE NOT NULL DEFAULT 240,
  costo_hora DOUBLE NOT NULL DEFAULT 0,
  UNIQUE (empresa_id, codigo),
  FOREIGN KEY (empresa_id) REFERENCES empresas(id),
  FOREIGN KEY (centro_costo_id) REFERENCES centros_costo(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS producto_mod (
  id INT AUTO_INCREMENT PRIMARY KEY,
  producto_id INT NOT NULL,
  trabajador_id INT NOT NULL,
  horas_std DOUBLE NOT NULL,
  UNIQUE (producto_id, trabajador_id),
  FOREIGN KEY (producto_id) REFERENCES productos(id),
  FOREIGN KEY (trabajador_id) REFERENCES trabajadores(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS cif (
  id INT AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT NOT NULL,
  periodo_id INT NOT NULL,
  codigo VARCHAR(190) NOT NULL,
  descripcion VARCHAR(255) NOT NULL,
  tipo VARCHAR(255) NOT NULL CHECK (tipo IN ('fijo','variable')),
  centro_costo_id INT,
  presupuestado DOUBLE NOT NULL DEFAULT 0,
  valor_real DOUBLE NOT NULL DEFAULT 0,
  UNIQUE (periodo_id, codigo),
  FOREIGN KEY (empresa_id) REFERENCES empresas(id),
  FOREIGN KEY (periodo_id) REFERENCES periodos(id),
  FOREIGN KEY (centro_costo_id) REFERENCES centros_costo(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS ordenes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT NOT NULL,
  periodo_id INT NOT NULL,
  numero VARCHAR(190) NOT NULL,
  producto_id INT NOT NULL,
  fecha VARCHAR(255) NOT NULL,
  cantidad_planeada DOUBLE NOT NULL,
  cantidad_terminada DOUBLE NOT NULL DEFAULT 0,
  cantidad_proceso DOUBLE NOT NULL DEFAULT 0,
  avance_pct DOUBLE NOT NULL DEFAULT 0,
  estado VARCHAR(255) NOT NULL DEFAULT 'abierta',
  UNIQUE (empresa_id, numero),
  FOREIGN KEY (empresa_id) REFERENCES empresas(id),
  FOREIGN KEY (periodo_id) REFERENCES periodos(id),
  FOREIGN KEY (producto_id) REFERENCES productos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS orden_mp (
  id INT AUTO_INCREMENT PRIMARY KEY,
  orden_id INT NOT NULL,
  mp_id INT NOT NULL,
  cantidad_real DOUBLE NOT NULL,
  precio_real DOUBLE NOT NULL,
  UNIQUE (orden_id, mp_id),
  FOREIGN KEY (orden_id) REFERENCES ordenes(id) ON DELETE CASCADE,
  FOREIGN KEY (mp_id) REFERENCES materias_primas(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS orden_mod (
  id INT AUTO_INCREMENT PRIMARY KEY,
  orden_id INT NOT NULL,
  trabajador_id INT NOT NULL,
  horas_real DOUBLE NOT NULL,
  tarifa_real DOUBLE NOT NULL,
  UNIQUE (orden_id, trabajador_id),
  FOREIGN KEY (orden_id) REFERENCES ordenes(id) ON DELETE CASCADE,
  FOREIGN KEY (trabajador_id) REFERENCES trabajadores(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS costos_estandar (
  id INT AUTO_INCREMENT PRIMARY KEY,
  empresa_id INT NOT NULL,
  periodo_id INT NOT NULL,
  producto_id INT NOT NULL,
  mp_unit DOUBLE,
  mod_unit DOUBLE,
  cif_unit DOUBLE,
  total_unit DOUBLE,
  UNIQUE (periodo_id, producto_id),
  FOREIGN KEY (periodo_id) REFERENCES periodos(id),
  FOREIGN KEY (producto_id) REFERENCES productos(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS costos_reales (
  id INT AUTO_INCREMENT PRIMARY KEY,
  orden_id INT NOT NULL UNIQUE,
  mp DOUBLE,
  mano_obra DOUBLE,
  cif DOUBLE,
  total DOUBLE,
  unidades_equiv DOUBLE,
  costo_unit DOUBLE,
  FOREIGN KEY (orden_id) REFERENCES ordenes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
CREATE TABLE IF NOT EXISTS variaciones (
  id INT AUTO_INCREMENT PRIMARY KEY,
  orden_id INT NOT NULL,
  tipo VARCHAR(255) NOT NULL,
  valor DOUBLE NOT NULL,
  clasificacion VARCHAR(255) NOT NULL,
  FOREIGN KEY (orden_id) REFERENCES ordenes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
