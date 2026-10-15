-- Dump MySQL para Aiven: esquema + datos de delicious_food.db
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS=0;

DROP TABLE IF EXISTS variaciones;
DROP TABLE IF EXISTS costos_reales;
DROP TABLE IF EXISTS costos_estandar;
DROP TABLE IF EXISTS orden_mod;
DROP TABLE IF EXISTS orden_mp;
DROP TABLE IF EXISTS ordenes;
DROP TABLE IF EXISTS cif;
DROP TABLE IF EXISTS producto_mod;
DROP TABLE IF EXISTS trabajadores;
DROP TABLE IF EXISTS producto_mp;
DROP TABLE IF EXISTS materias_primas;
DROP TABLE IF EXISTS productos;
DROP TABLE IF EXISTS centros_costo;
DROP TABLE IF EXISTS unidades;
DROP TABLE IF EXISTS periodos;
DROP TABLE IF EXISTS empresas;
DROP TABLE IF EXISTS actividad;
DROP TABLE IF EXISTS usuarios;

-- ===== ESQUEMA =====
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

-- ===== DATOS =====
-- usuarios (3 filas)
INSERT INTO usuarios (id, username, nombre, password_hash, salt, rol, activo) VALUES
(1, 'admin', 'Administrador', '9ea6541223b20a3d49f0b631dfb8a5d0eb0b133e1acbc4dd8e1596319587bce5', 'ee96e4671b45325e86a4e050504f4b0b', 'admin', 1),
(2, 'usuario', 'Usuario operativo', '1d0f6836e33f7d17a80348d4bafa678e467e83c32f01130011cbba7da716a2d1', 'd29175b266fb427553fce81c1a37c43a', 'usuario', 1),
(3, 'estudiante', 'Estudiante', '76e955bb7ddcc5614aff08d5fd2925db40e65b69b0cc14029643a4403f041934', 'ab9340f557528946acc59c7ba48912d9', 'estudiante', 1);

-- actividad (1 filas)
INSERT INTO actividad (id, fecha, usuario, accion, entidad, detalle) VALUES
(1, '2026-10-14 19:00:48', 'admin', 'inicio_sesion', 'usuarios', 'Rol admin');

-- empresas (1 filas)
INSERT INTO empresas (id, nit, razon_social, nombre_comercial, regimen, tarifa_iva, retencion_fuente, actividad_ciiu, direccion, ciudad, telefono, email) VALUES
(1, '900000001-1', 'Delicious Food S.A.S. (ejemplo)', 'Delicious Food', 'Régimen simple de tributación', 0.0, 0.0, '5611', NULL, 'Bucaramanga', NULL, 'info@deliciousfood.example');

-- periodos (3 filas)
INSERT INTO periodos (id, empresa_id, codigo, nombre, fecha_inicio, fecha_fin, estado, cif_base, base_presupuestada) VALUES
(1, 1, '2026-08', 'Agosto 2026', '2026-08-01', '2026-08-31', 'cerrado', 'HMOD', 195.0),
(2, 1, '2026-09', 'Septiembre 2026', '2026-09-01', '2026-09-30', 'cerrado', 'HMOD', 195.0),
(3, 1, '2026-10', 'Octubre 2026', '2026-10-01', '2026-10-31', 'abierto', 'HMOD', 195.0);

-- unidades (12 filas)
INSERT INTO unidades (id, codigo, nombre) VALUES
(1, 'PZA', 'Pieza'),
(2, 'POR', 'Porción'),
(3, 'KG', 'Kilo'),
(4, 'LB', 'Libra'),
(5, 'GR', 'Gramo'),
(6, 'LT', 'Litro'),
(7, 'ML', 'Mililitro'),
(8, 'OZ', 'Onza'),
(9, 'GAL', 'Galón'),
(10, 'M3', 'Metro cúbico'),
(11, 'ROL', 'Rollo'),
(12, 'HR', 'Hora');

-- centros_costo (3 filas)
INSERT INTO centros_costo (id, empresa_id, codigo, nombre, tipo) VALUES
(1, 1, 'CC-PROD', 'Cocina - Producción', 'productivo'),
(2, 1, 'CC-SRV', 'Servicios generales', 'servicio'),
(3, 1, 'CC-ADM', 'Administración', 'administrativo');

-- productos (3 filas)
INSERT INTO productos (id, empresa_id, codigo, nombre, unidad_id, precio_venta, centro_costo_id) VALUES
(1, 1, 'DF-001', 'Arepa de chorizo', 1, 7000.0, 1),
(2, 1, 'DF-002', 'Perro caliente', 1, 7000.0, 1),
(3, 1, 'DF-003', 'Suizo', 1, 10000.0, 1);

-- materias_primas (12 filas)
INSERT INTO materias_primas (id, empresa_id, codigo, descripcion, proveedor, presentacion, unidad_id, costo_compra, contenido, merma_pct, logistica_pct, costo_estandar) VALUES
(1, 1, 'MP-001', 'Arepa', 'Proveedor local', 'Paquete x10', 1, 4800.0, 10.0, 0.0, 0.0, 480.0),
(2, 1, 'MP-002', 'Chorizo', 'Proveedor local', 'Paquete x8', 1, 9700.0, 8.0, 0.0, 0.0, 1212.5),
(3, 1, 'MP-003', 'Jamón', 'Proveedor local', 'Paquete x24', 1, 8800.0, 24.0, 0.0, 0.0, 366.6666666666667),
(4, 1, 'MP-004', 'Queso', 'Proveedor local', 'Paquete x22', 1, 10700.0, 22.0, 0.0, 0.0, 486.3636363636364),
(5, 1, 'MP-005', 'Queso costeño', 'Proveedor local', 'Libra (500 g)', 5, 14000.0, 500.0, 0.0, 0.0, 28.0),
(6, 1, 'MP-006', 'Recorte de papa', 'Proveedor local', 'Kilo (1000 g)', 5, 10500.0, 1000.0, 0.0, 0.0, 10.5),
(7, 1, 'MP-007', 'Salsas', 'Proveedor local', 'Presentación 14,35 kg', 5, 23000.0, 14350.0, 0.0, 0.0, 1.602787456445993),
(8, 1, 'MP-008', 'Pan de perro', 'Proveedor local', 'Paquete x10', 1, 5200.0, 10.0, 0.0, 0.0, 520.0),
(9, 1, 'MP-009', 'Salchicha long', 'Proveedor local', 'Paquete x22', 1, 28800.0, 22.0, 0.0, 0.0, 1309.090909090909),
(10, 1, 'MP-010', 'Suiza', 'Proveedor local', 'Paquete x8 (4 porciones c/u)', 2, 40800.0, 32.0, 0.0, 0.0, 1275.0),
(11, 1, 'MP-011', 'Papa', 'Proveedor local', 'Bulto 2,5 kg', 5, 15800.0, 2500.0, 0.0, 0.0, 6.32),
(12, 1, 'MP-012', 'Lechuga', 'Proveedor local', 'Unidad (9,6 porciones)', 2, 3500.0, 9.6, 0.0, 0.0, 364.58333333333337);

-- producto_mp (19 filas)
INSERT INTO producto_mp (id, producto_id, mp_id, cantidad_std, eficiencia_pct) VALUES
(1, 1, 1, 1.0, 98.0),
(2, 1, 2, 1.0, 100.0),
(3, 1, 3, 1.0, 100.0),
(4, 1, 4, 1.0, 100.0),
(5, 1, 5, 10.0, 100.0),
(6, 1, 6, 10.0, 95.0),
(7, 1, 7, 4.79, 95.0),
(8, 2, 8, 1.0, 100.0),
(9, 2, 9, 1.0, 100.0),
(10, 2, 6, 10.0, 95.0),
(11, 2, 7, 4.79, 95.0),
(12, 2, 5, 10.0, 100.0),
(13, 3, 10, 1.0, 100.0),
(14, 3, 2, 0.5, 100.0),
(15, 3, 11, 10.0, 100.0),
(16, 3, 12, 1.0, 90.0),
(17, 3, 6, 1.0, 95.0),
(18, 3, 5, 10.0, 100.0),
(19, 3, 7, 4.79, 95.0);

-- trabajadores (3 filas)
INSERT INTO trabajadores (id, empresa_id, codigo, nombre, cargo, centro_costo_id, salario, prestaciones_pct, cargas_pct, horas_mes, costo_hora) VALUES
(1, 1, 'OP-001', 'Cocinero 1', 'Cocinero', 1, 1300000.0, 21.83, 30.0, 240.0, 8224.125),
(2, 1, 'OP-002', 'Cocinero 2', 'Cocinero', 1, 1300000.0, 21.83, 30.0, 240.0, 8224.125),
(3, 1, 'OP-003', 'Auxiliar de cocina', 'Auxiliar', 1, 920000.0, 21.83, 30.0, 240.0, 5820.15);

-- producto_mod (4 filas)
INSERT INTO producto_mod (id, producto_id, trabajador_id, horas_std) VALUES
(1, 1, 1, 0.12),
(2, 2, 2, 0.1),
(3, 3, 1, 0.1),
(4, 3, 3, 0.05);

-- cif (9 filas)
INSERT INTO cif (id, empresa_id, periodo_id, codigo, descripcion, tipo, centro_costo_id, presupuestado, valor_real) VALUES
(1, 1, 1, 'CIF-001', 'Gas propano', 'variable', 1, 220000.0, 205000.0),
(2, 1, 1, 'CIF-002', 'Servicios públicos (agua y luz)', 'fijo', 2, 165000.0, 170000.0),
(3, 1, 1, 'CIF-003', 'Sueldos administrativos / supervisión', 'fijo', 3, 1000000.0, 1000000.0),
(4, 1, 2, 'CIF-001', 'Gas propano', 'variable', 1, 220000.0, 231000.0),
(5, 1, 2, 'CIF-002', 'Servicios públicos (agua y luz)', 'fijo', 2, 165000.0, 176000.0),
(6, 1, 2, 'CIF-003', 'Sueldos administrativos / supervisión', 'fijo', 3, 1000000.0, 1000000.0),
(7, 1, 3, 'CIF-001', 'Gas propano', 'variable', 1, 220000.0, 0.0),
(8, 1, 3, 'CIF-002', 'Servicios públicos (agua y luz)', 'fijo', 2, 165000.0, 0.0),
(9, 1, 3, 'CIF-003', 'Sueldos administrativos / supervisión', 'fijo', 3, 1000000.0, 0.0);

-- ordenes (12 filas)
INSERT INTO ordenes (id, empresa_id, periodo_id, numero, producto_id, fecha, cantidad_planeada, cantidad_terminada, cantidad_proceso, avance_pct, estado) VALUES
(1, 1, 1, 'OP-2608-001', 1, '2026-08-12', 350.0, 350.0, 0.0, 0.0, 'cerrada'),
(2, 1, 1, 'OP-2608-002', 1, '2026-08-28', 350.0, 350.0, 0.0, 0.0, 'cerrada'),
(3, 1, 1, 'OP-2608-003', 2, '2026-08-12', 225.0, 225.0, 0.0, 0.0, 'cerrada'),
(4, 1, 1, 'OP-2608-004', 2, '2026-08-28', 225.0, 225.0, 0.0, 0.0, 'cerrada'),
(5, 1, 1, 'OP-2608-005', 3, '2026-08-12', 150.0, 150.0, 0.0, 0.0, 'cerrada'),
(6, 1, 1, 'OP-2608-006', 3, '2026-08-28', 150.0, 150.0, 0.0, 0.0, 'cerrada'),
(7, 1, 2, 'OP-2609-007', 1, '2026-09-12', 350.0, 350.0, 0.0, 0.0, 'cerrada'),
(8, 1, 2, 'OP-2609-008', 1, '2026-09-27', 350.0, 350.0, 0.0, 0.0, 'cerrada'),
(9, 1, 2, 'OP-2609-009', 2, '2026-09-12', 225.0, 225.0, 0.0, 0.0, 'cerrada'),
(10, 1, 2, 'OP-2609-010', 2, '2026-09-27', 225.0, 225.0, 0.0, 0.0, 'cerrada'),
(11, 1, 2, 'OP-2609-011', 3, '2026-09-12', 150.0, 150.0, 0.0, 0.0, 'cerrada'),
(12, 1, 2, 'OP-2609-012', 3, '2026-09-27', 150.0, 130.0, 20.0, 60.0, 'abierta');

-- orden_mp (76 filas)
INSERT INTO orden_mp (id, orden_id, mp_id, cantidad_real, precio_real) VALUES
(1, 1, 1, 359.695, 494.5208),
(2, 1, 2, 360.748, 1292.5251),
(3, 1, 3, 352.155, 367.5204),
(4, 1, 4, 362.622, 503.7054),
(5, 1, 5, 3664.508, 28.9739),
(6, 1, 6, 3845.698, 11.0965),
(7, 1, 7, 1844.259, 1.6647),
(8, 2, 1, 359.516, 509.6045),
(9, 2, 2, 359.443, 1287.04),
(10, 2, 3, 364.389, 384.2443),
(11, 2, 4, 354.415, 488.869),
(12, 2, 5, 3705.782, 30.0421),
(13, 2, 6, 3862.188, 11.3396),
(14, 2, 7, 1819.118, 1.583),
(15, 3, 8, 228.944, 533.3873),
(16, 3, 9, 236.832, 1375.0659),
(17, 3, 6, 2450.476, 10.316),
(18, 3, 7, 1182.861, 1.629),
(19, 3, 5, 2306.999, 28.5566),
(20, 4, 8, 226.572, 535.9307),
(21, 4, 9, 235.127, 1361.4762),
(22, 4, 6, 2438.199, 11.2526),
(23, 4, 7, 1152.079, 1.638),
(24, 4, 5, 2375.041, 28.7817),
(25, 5, 10, 152.021, 1265.9474),
(26, 5, 2, 75.22, 1273.6903),
(27, 5, 11, 1579.814, 6.2584),
(28, 5, 12, 172.89, 374.4286),
(29, 5, 6, 162.462, 10.5304),
(30, 5, 5, 1579.733, 29.1947),
(31, 5, 7, 777.045, 1.646),
(32, 6, 10, 156.028, 1288.7225),
(33, 6, 2, 78.599, 1249.1053),
(34, 6, 11, 1543.1, 6.7526),
(35, 6, 12, 170.997, 368.0241),
(36, 6, 6, 160.443, 10.3248),
(37, 6, 5, 1559.008, 29.1124),
(38, 6, 7, 777.11, 1.6545),
(39, 7, 1, 368.099, 510.0563),
(40, 7, 2, 366.967, 1255.8879),
(41, 7, 3, 369.053, 389.8181),
(42, 7, 4, 356.65, 521.2268),
(43, 7, 5, 3520.659, 29.3701),
(44, 7, 6, 3857.755, 10.8309),
(45, 7, 7, 1812.694, 1.7254),
(46, 8, 1, 367.41, 473.4862),
(47, 8, 2, 355.596, 1248.6835),
(48, 8, 3, 352.03, 386.7435),
(49, 8, 4, 358.638, 498.4933),
(50, 8, 5, 3502.947, 27.4406);
INSERT INTO orden_mp (id, orden_id, mp_id, cantidad_real, precio_real) VALUES
(51, 8, 6, 3812.563, 11.2688),
(52, 8, 7, 1773.532, 1.698),
(53, 9, 8, 235.15, 559.3311),
(54, 9, 9, 234.024, 1366.0898),
(55, 9, 6, 2390.413, 10.6191),
(56, 9, 7, 1174.162, 1.6941),
(57, 9, 5, 2378.241, 28.8176),
(58, 10, 8, 228.01, 540.1726),
(59, 10, 9, 237.937, 1397.5846),
(60, 10, 6, 2440.145, 10.3787),
(61, 10, 7, 1179.981, 1.7206),
(62, 10, 5, 2355.764, 30.002),
(63, 11, 10, 157.272, 1315.8039),
(64, 11, 2, 75.885, 1189.9635),
(65, 11, 11, 1509.552, 6.7547),
(66, 11, 12, 167.18, 369.9434),
(67, 11, 6, 161.243, 11.098),
(68, 11, 5, 1502.321, 28.8691),
(69, 11, 7, 771.189, 1.6194),
(70, 12, 10, 148.858, 1269.121),
(71, 12, 2, 73.214, 1240.8249),
(72, 12, 11, 1448.663, 6.5717),
(73, 12, 12, 164.201, 359.8258),
(74, 12, 6, 153.053, 10.4953),
(75, 12, 5, 1498.508, 27.5667),
(76, 12, 7, 739.381, 1.7052);

-- orden_mod (16 filas)
INSERT INTO orden_mod (id, orden_id, trabajador_id, horas_real, tarifa_real) VALUES
(1, 1, 1, 43.008, 8426.1767),
(2, 2, 1, 43.43, 8407.5067),
(3, 3, 2, 23.818, 8388.0993),
(4, 4, 2, 23.665, 8232.4729),
(5, 5, 1, 16.394, 8548.8877),
(6, 5, 3, 7.909, 5950.4739),
(7, 6, 1, 15.734, 8527.2694),
(8, 6, 3, 7.695, 5933.1934),
(9, 7, 1, 46.063, 8501.2582),
(10, 8, 1, 43.041, 8428.4368),
(11, 9, 2, 24.121, 8268.4907),
(12, 10, 2, 23.189, 8359.6715),
(13, 11, 1, 15.489, 8264.0524),
(14, 11, 3, 8.212, 5953.2262),
(15, 12, 1, 14.842, 8472.3981),
(16, 12, 3, 7.234, 5985.6624);

-- costos_estandar (9 filas)
INSERT INTO costos_estandar (id, empresa_id, periodo_id, producto_id, mp_unit, mod_unit, cif_unit, total_unit) VALUES
(1, 1, 1, 1, 2953.9339602569935, 986.895, 852.3076923076923, 4793.136652564685),
(2, 1, 1, 2, 2227.6986479502525, 822.4125, 710.2564102564103, 3760.3675582066626),
(3, 1, 1, 3, 2648.6766472414097, 1113.42, 1065.3846153846155, 4827.481262626025),
(4, 1, 2, 1, 2953.9339602569935, 986.895, 852.3076923076923, 4793.136652564685),
(5, 1, 2, 2, 2227.6986479502525, 822.4125, 710.2564102564103, 3760.3675582066626),
(6, 1, 2, 3, 2648.6766472414097, 1113.42, 1065.3846153846155, 4827.481262626025),
(7, 1, 3, 1, 2953.9339602569935, 986.895, 852.3076923076923, 4793.136652564685),
(8, 1, 3, 2, 2227.6986479502525, 822.4125, 710.2564102564103, 3760.3675582066626),
(9, 1, 3, 3, 2648.6766472414097, 1113.42, 1065.3846153846155, 4827.481262626025);

-- costos_reales (12 filas)
INSERT INTO costos_reales (id, orden_id, mp, mano_obra, cif, total, unidades_equiv, costo_unit) VALUES
(1, 1, 1108150.3241071, 362393.0075136, 325543.7565027828, 1796087.0881234827, 350.0, 5131.677394638522),
(2, 3, 540861.4678684, 199787.74912740002, 180287.41611754283, 920936.6331133428, 225.0, 4093.051702725968),
(3, 5, 411989.2795829, 187212.76302889996, 183958.5638552625, 783160.6064670624, 150.0, 5221.070709780416),
(4, 2, 1117110.1972707, 365138.015981, 328738.0335034379, 1810986.2467551378, 350.0, 5174.246419300393),
(5, 4, 539227.6060569, 194821.4711785, 179129.30147038586, 913178.3787057858, 225.0, 4058.5705720257147),
(6, 6, 420934.910673, 179823.9799526, 177342.92855058823, 778101.8191761882, 150.0, 5187.345461174588),
(7, 7, 1126692.3942053, 391593.4564666, 355729.1029743511, 1874014.953646251, 350.0, 5354.328438989289),
(8, 9, 547132.8878942999, 199444.2641747, 186278.39465176655, 932855.5467207665, 225.0, 4146.024652092296),
(9, 11, 415692.1931264, 176889.801178, 183034.87548781224, 775616.8697922122, 150.0, 5170.779131948081),
(10, 8, 1075011.811757, 362768.34830879996, 332391.21032323217, 1770171.3703890322, 350.0, 5057.632486825806),
(11, 10, 553735.2812443, 193852.4224135, 179080.8711736584, 926668.5748314584, 225.0, 4118.526999250927),
(12, 12, 392544.5529852, 169047.6144018, 170485.5453891795, 732077.7127761795, 142.0, 5155.4768505364755);

-- variaciones (72 filas)
INSERT INTO variaciones (id, orden_id, tipo, valor, clasificacion) VALUES
(1, 1, 'Precio de materiales', 46658.11137000784, 'Desfavorable'),
(2, 1, 'Cantidad de materiales', 27615.32664714443, 'Desfavorable'),
(3, 1, 'Tarifa de mano de obra', 8689.8395136, 'Desfavorable'),
(4, 1, 'Eficiencia de mano de obra', 8289.918000000021, 'Desfavorable'),
(5, 1, 'Presupuesto de CIF', -3047.7554335567, 'Favorable'),
(6, 1, 'Volumen de CIF', 30283.819628647198, 'Desfavorable'),
(7, 3, 'Precio de materiales', 19554.124913062682, 'Desfavorable'),
(8, 3, 'Cantidad de materiales', 20075.147166530493, 'Desfavorable'),
(9, 3, 'Tarifa de mano de obra', 3905.539877399997, 'Desfavorable'),
(10, 3, 'Eficiencia de mano de obra', 10839.39675000001, 'Desfavorable'),
(11, 3, 'Presupuesto de CIF', 4256.24900878952, 'Desfavorable'),
(12, 3, 'Volumen de CIF', 16223.474801060998, 'Desfavorable'),
(13, 5, 'Precio de materiales', 6757.204623805922, 'Desfavorable'),
(14, 5, 'Cantidad de materiales', 7930.577872882582, 'Desfavorable'),
(15, 5, 'Tarifa de mano de obra', 6354.89142889999, 'Desfavorable'),
(16, 5, 'Eficiencia de mano de obra', 13844.871599999986, 'Desfavorable'),
(17, 5, 'Presupuesto de CIF', 7927.396746509163, 'Desfavorable'),
(18, 5, 'Volumen de CIF', 16223.474801060998, 'Desfavorable'),
(19, 2, 'Precio de materiales', 55503.48207668668, 'Desfavorable'),
(20, 2, 'Cantidad de materiales', 27729.829104065593, 'Desfavorable'),
(21, 2, 'Tarifa de mano de obra', 7964.267230999996, 'Desfavorable'),
(22, 2, 'Eficiencia de mano de obra', 11760.498749999997, 'Desfavorable'),
(23, 2, 'Presupuesto de CIF', 146.52156709837072, 'Desfavorable'),
(24, 2, 'Volumen de CIF', 30283.819628647198, 'Desfavorable'),
(25, 4, 'Precio de materiales', 19658.772605047012, 'Desfavorable'),
(26, 4, 'Cantidad de materiales', 18336.63766304621, 'Desfavorable'),
(27, 4, 'Tarifa de mano de obra', 197.5530535000157, 'Desfavorable'),
(28, 4, 'Eficiencia de mano de obra', 9581.105624999993, 'Desfavorable'),
(29, 4, 'Presupuesto de CIF', 3098.134361632554, 'Desfavorable'),
(30, 4, 'Volumen de CIF', 16223.474801060998, 'Desfavorable'),
(31, 6, 'Precio de materiales', 8020.457262721253, 'Desfavorable'),
(32, 6, 'Cantidad de materiales', 15612.956324067274, 'Desfavorable'),
(33, 6, 'Tarifa de mano de obra', 5639.542952599992, 'Desfavorable'),
(34, 6, 'Eficiencia de mano de obra', 7171.437000000002, 'Desfavorable'),
(35, 6, 'Presupuesto de CIF', 1311.7614418348894, 'Desfavorable'),
(36, 6, 'Volumen de CIF', 16223.474801060998, 'Desfavorable'),
(37, 7, 'Precio de materiales', 54286.11975730084, 'Desfavorable'),
(38, 7, 'Cantidad de materiales', 38529.3883580514, 'Desfavorable'),
(39, 7, 'Tarifa de mano de obra', 12765.586591600011, 'Desfavorable'),
(40, 7, 'Eficiencia de mano de obra', 33414.61987500002, 'Desfavorable'),
(41, 7, 'Presupuesto de CIF', 25184.7653675135, 'Desfavorable'),
(42, 7, 'Volumen de CIF', 32236.645299145275, 'Desfavorable'),
(43, 9, 'Precio de materiales', 24924.180359773556, 'Desfavorable'),
(44, 9, 'Cantidad de materiales', 20976.51174571962, 'Desfavorable'),
(45, 9, 'Tarifa de mano de obra', 1070.145049700007, 'Desfavorable'),
(46, 9, 'Eficiencia de mano de obra', 13331.306624999988, 'Desfavorable'),
(47, 9, 'Presupuesto de CIF', 9201.070933817839, 'Desfavorable'),
(48, 9, 'Volumen de CIF', 17269.631410256396, 'Desfavorable'),
(49, 11, 'Precio de materiales', 7674.328763984218, 'Desfavorable'),
(50, 11, 'Cantidad de materiales', 10716.367276204319, 'Desfavorable');
INSERT INTO variaciones (id, orden_id, tipo, valor, clasificacion) VALUES
(51, 11, 'Tarifa de mano de obra', 1711.2572530000111, 'Desfavorable'),
(52, 11, 'Eficiencia de mano de obra', 8165.543925000004, 'Desfavorable'),
(53, 11, 'Presupuesto de CIF', 5957.551769863501, 'Desfavorable'),
(54, 11, 'Volumen de CIF', 17269.6314102564, 'Desfavorable'),
(55, 8, 'Precio de materiales', 23031.690928945947, 'Desfavorable'),
(56, 8, 'Cantidad de materiales', 18103.234738106337, 'Desfavorable'),
(57, 8, 'Tarifa de mano de obra', 8793.784183799977, 'Desfavorable'),
(58, 8, 'Eficiencia de mano de obra', 8561.314124999974, 'Desfavorable'),
(59, 8, 'Presupuesto de CIF', 1846.8727163945805, 'Desfavorable'),
(60, 8, 'Volumen de CIF', 32236.645299145275, 'Desfavorable'),
(61, 10, 'Precio de materiales', 30214.74436229176, 'Desfavorable'),
(62, 10, 'Cantidad de materiales', 22288.34109320142, 'Desfavorable'),
(63, 10, 'Tarifa de mano de obra', 3143.187788500009, 'Desfavorable'),
(64, 10, 'Eficiencia de mano de obra', 5666.422125, 'Desfavorable'),
(65, 10, 'Presupuesto de CIF', 2003.5474557097004, 'Desfavorable'),
(66, 10, 'Volumen de CIF', 17269.631410256396, 'Desfavorable'),
(67, 12, 'Precio de materiales', 207.77881619885514, 'Desfavorable'),
(68, 12, 'Cantidad de materiales', 16224.69026072098, 'Desfavorable'),
(69, 12, 'Tarifa de mano de obra', 4882.1860518000085, 'Desfavorable'),
(70, 12, 'Eficiencia de mano de obra', 6059.7883499999925, 'Desfavorable'),
(71, 12, 'Presupuesto de CIF', 2852.3456028546934, 'Desfavorable'),
(72, 12, 'Volumen de CIF', 16348.584401709391, 'Desfavorable');

SET FOREIGN_KEY_CHECKS=1;
