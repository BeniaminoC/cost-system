# Manual técnico – Delicious Food · Sistema de Costos Estándar

## 1. Arquitectura
| Capa | Tecnología | Archivos |
|---|---|---|
| Frontend | HTML + CSS + JavaScript puro (sin librerías, sin CDN) | `public/` |
| Backend | Python 3.9+ (solo biblioteca estándar: `http.server`, `sqlite3`) | `backend/` |
| Base de datos | SQLite local (archivo único `data/delicious_food.db`) | `database/schema.sql` |
| Comunicación | API REST JSON sobre HTTP local (`/api/...`) con token Bearer | `backend/server.py` |
| Configuración | `config/config.ini` | |

Todo funciona **sin internet**: no hay fuentes, scripts ni gráficos cargados desde la red (los gráficos se dibujan con `<canvas>`; Excel y PDF se generan en Python sin librerías).

> **Sobre la base de datos:** se usó SQLite porque es embebida (no requiere instalar ni administrar un servidor), ideal para un sistema que debe ejecutarse localmente. `schema.sql` está escrito de forma portable a MySQL (cambiar `AUTOINCREMENT`→`AUTO_INCREMENT`, `REAL`→`DECIMAL`) si se prefiere migrar.

## 2. Estructura de carpetas
```
delicious-food-costos/
├─ config/config.ini        Parámetros del sistema (puerto, BD, sesión, seguridad)
├─ backend/
│  ├─ server.py             Servidor HTTP + rutas de la API + sesiones + bitácora
│  ├─ db.py                 Configuración, conexión SQLite, hash de contraseñas
│  ├─ entities.py           Metadatos de entidades, permisos por rol y validaciones
│  ├─ costing.py            Motor de costos estándar y variaciones
│  ├─ reports.py            Definición de los 7 reportes
│  ├─ exports.py            Exportación a Excel (.xlsx) y PDF
│  └─ seed.py               Usuarios iniciales y datos de ejemplo (Excel Delicious Food)
├─ database/schema.sql      Tablas
├─ public/                  index.html · css/styles.css · js/app.js
├─ data/                    Base de datos generada al primer arranque
├─ installer/               build_exe.bat · instalador.iss
├─ docs/MANUAL_TECNICO.md
├─ iniciar.bat / iniciar.sh Arranque rápido
└─ requirements.txt
```

## 3. Instalación y ejecución
### 3.1 Opción A – con Python (más simple)
1. Instalar Python 3.9 o superior (marcar *Add python to PATH*).
2. Copiar la carpeta del proyecto al equipo.
3. Doble clic en `iniciar.bat` (Windows) o `./iniciar.sh` (Linux/Mac).
4. Se abre el navegador en `http://127.0.0.1:8080`. Cerrar la ventana negra detiene el sistema.

### 3.2 Opción B – ejecutable `.exe` e instalador
En un equipo Windows con Python e internet (solo para generar):
1. Ejecutar `installer\build_exe.bat` → crea `dist\DeliciousFoodCostos\DeliciousFoodCostos.exe` (ya funciona solo, sin Python).
2. Instalar [Inno Setup](https://jrsoftware.org/isinfo.php), abrir `installer\instalador.iss` y pulsar **Compilar** → crea `dist\DeliciousFoodCostos_Setup.exe`.
3. Entregar el `Setup.exe`: instala, crea accesos directos y no requiere internet ni Python.

## 4. Configuración (`config/config.ini`)
| Sección / clave | Descripción |
|---|---|
| `[servidor] host, puerto` | Dirección y puerto (por defecto 127.0.0.1:8080) |
| `abrir_navegador` | Abrir el navegador automáticamente |
| `[base_datos] ruta` | Ubicación del archivo de BD |
| `cargar_datos_ejemplo` | `true` carga el caso Delicious Food al crear la BD; `false` deja solo usuarios y unidades |
| `[seguridad] minutos_sesion` | Inactividad máxima antes de cerrar sesión |
| `iteraciones_hash` | Iteraciones PBKDF2 para contraseñas |
| `intentos_maximos_login, bloqueo_segundos` | Bloqueo temporal tras intentos fallidos |

Para **reiniciar la base de datos**: cerrar el sistema, borrar `data/delicious_food.db` y volver a iniciar.

## 5. Usuarios, roles y permisos
Usuarios iniciales (**cambiar las contraseñas** en «Cambiar clave» o en Administración › Usuarios):

| Usuario | Clave | Rol | Permisos |
|---|---|---|---|
| admin | admin123 | Administrador | Todo: crear, editar, eliminar, usuarios y bitácora |
| usuario | usuario123 | Usuario | Consultar, crear y editar datos de costos (no elimina, no administra usuarios) |
| estudiante | estudiante123 | Estudiante | Solo consulta, reportes y exportación |

Las contraseñas se guardan con PBKDF2-SHA256 + sal. Las sesiones usan un token aleatorio que expira por inactividad. La **bitácora** (Administración › Registro de actividades) guarda inicios/cierres de sesión, intentos fallidos, creación, edición y eliminación de registros, y exportaciones.

## 6. Modelo de datos
`usuarios`, `actividad`, `empresas`, `periodos`, `unidades`, `centros_costo`, `productos`, `materias_primas`, `producto_mp` (receta: cantidad y eficiencia), `trabajadores`, `producto_mod` (horas estándar), `cif`, `ordenes`, `orden_mp` (consumo real), `orden_mod` (horas reales) y las tablas de resultados `costos_estandar`, `costos_reales` y `variaciones` (se regeneran automáticamente con cada cambio).

## 7. Fórmulas
Convención: variación **positiva = desfavorable**, **negativa = favorable**.

* **Costo estándar MP por unidad** de materia prima = `costo_compra ÷ contenido × (1+merma%) × (1+logística%)`.
* **Cantidad estándar permitida** = `cantidad_std ÷ eficiencia% × unidades equivalentes`.
* **Unidades equivalentes** = `terminadas + en proceso × % avance`.
* **Tarifa estándar MOD** = `salario × (1 + prestaciones% + cargas%) ÷ horas del mes`.
* **Tasa predeterminada CIF** = `CIF presupuestado ÷ base presupuestada` (horas MOD o unidades, según el período). Se separa en tasa fija y variable.
* **CIF aplicado** = `tasa × base estándar permitida`. El CIF real del período se reparte entre órdenes según su base real.
* Variaciones:
  * Precio MP = `(Pr − Pe) × Qr`  ·  Cantidad MP = `(Qr − Qe permitida) × Pe`
  * Tarifa MOD = `(Tr − Te) × Hr`  ·  Eficiencia MOD = `(Hr − He permitidas) × Te`
  * Presupuesto CIF = `CIF real − presupuesto flexible` (fijo + tasa variable × base estándar permitida)
  * Volumen CIF = `CIF fijo presupuestado − tasa fija × base estándar permitida`
  * Total = real − estándar = suma de las seis variaciones.
* **Margen** = `precio × unidades terminadas − costo real de lo terminado`.

> Las variaciones solo son representativas cuando la orden tiene registrados **todos** sus consumos reales (MP y horas). Una orden con consumos parciales mostrará variaciones favorables artificiales.

## 8. API (resumen)
Todas las rutas (salvo `login`) requieren `Authorization: Bearer <token>`.

| Método y ruta | Uso |
|---|---|
| `POST /api/login` · `POST /api/logout` · `GET /api/meta` | Sesión y metadatos |
| `GET/POST /api/e/<entidad>?empresa_id=` · `GET/PUT/DELETE /api/e/<entidad>/<id>` | CRUD de todas las entidades |
| `GET /api/opciones/<entidad>` | Listas para selectores |
| `GET /api/dashboard?empresa_id&periodo_id&producto_id` | Indicadores y gráficos |
| `GET /api/reporte/<tipo>?formato=json\|xlsx\|pdf` | Reportes (`hoja_costos, materiales, mod, cif, produccion, variaciones, estado_costos`) |
| `POST /api/recalcular` · `GET /api/cif-resumen` | Recalcular y tasas CIF |

Códigos: `401` sesión inválida, `403` sin permiso, `409` registro en uso, `422` validación (lista `errores` en español).

## 9. Validaciones implementadas
Obligatorios no vacíos · números válidos y no negativos · cantidades mayores a cero · porcentajes 0–100 · fechas válidas y dentro del período · fecha final ≥ inicial · códigos duplicados por empresa · períodos cerrados bloquean órdenes y CIF · mensajes comprensibles · confirmación antes de eliminar · registros relacionados impiden eliminar (409).

## 10. Solución de problemas
* **«Puerto en uso»**: cambiar `puerto` en `config.ini`.
* **Pantalla en blanco**: confirmar que la ventana del servidor sigue abierta y abrir `http://127.0.0.1:8080`.
* **Olvidó la clave de admin**: borrar `data/delicious_food.db` (se pierde la información) o restaurar una copia. **Respaldo**: copiar el archivo `data/delicious_food.db`.


## Versión web (Vercel + Aiven + GitHub)
* Mismo código; el modo web se activa si existe la variable `DATABASE_URL` (o se ejecuta en Vercel).
* `backend/db.py` abre MySQL con PyMySQL (SQLite en modo local). Las consultas usan `?` y se traducen a `%s`; los `||` funcionan con `PIPES_AS_CONCAT`.
* `database/schema_mysql.sql` es el esquema MySQL (llaves foráneas como restricciones de tabla). Se crea solo en el primer arranque, bajo un candado `GET_LOCK` para que dos instancias no lo hagan a la vez.
* Sesiones: token firmado con HMAC (sin memoria del servidor, necesario porque Vercel es sin estado); se renueva en cada petición (cabecera `X-Token`). Clave: `SECRET_KEY` o derivada de `DATABASE_URL` + `ADMIN_PASSWORD`.
* El bloqueo por intentos de login se cuenta en la tabla `actividad` (no en memoria).
* `backend/costing.py` carga los datos de la empresa en pocas consultas y guarda resultados por lotes (la base está en internet y cada consulta cuesta).
* Copias de seguridad en JSON (menú Administración → Copias de seguridad); sirven entre SQLite y MySQL.
* Variables de entorno: `DATABASE_URL` y `ADMIN_PASSWORD` (obligatorias); opcionales `SECRET_KEY`, `CARGAR_DATOS_EJEMPLO` (true/false), `USUARIO_PASSWORD`, `ESTUDIANTE_PASSWORD`, `ZONA_HORARIA_HORAS` (por defecto -5), `MYSQL_CA_CERT` (certificado CA de Aiven para verificar TLS).
* Probar MySQL en local: `DATABASE_URL="mysql://usuario:clave@127.0.0.1:3306/base?ssl-mode=DISABLED" ADMIN_PASSWORD=Clave2026x python3 backend/server.py` (requiere `pip install PyMySQL`).
