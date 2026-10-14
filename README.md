# Delicious Food – Sistema de Costos Estándar

El mismo código funciona de dos formas:

| Modo | Cómo se inicia | Base de datos |
|---|---|---|
| **Local (sin internet)** | `iniciar.bat` (Windows) o `./iniciar.sh`, luego http://127.0.0.1:8080 | SQLite (`data/delicious_food.db`) |
| **En internet** | Vercel (ver `docs/DESPLIEGUE_VERCEL.md`) | MySQL en Aiven (variable `DATABASE_URL`) |

Usuarios de prueba **solo en modo local**: `admin/admin123`, `usuario/usuario123`, `estudiante/estudiante123`.
En internet solo existe `admin`, con la contraseña de la variable `ADMIN_PASSWORD`.

Guía paso a paso para publicar: `docs/DESPLIEGUE_VERCEL.md` (también en Word: `docs/DESPLIEGUE_VERCEL.docx`).
Manual técnico: `docs/MANUAL_TECNICO.md`.

## Estructura
- `wsgi.py` – entrada para Vercel (Flask). `vercel.json`, `requirements.txt` – configuración de despliegue.
- `backend/` – API y lógica (`server.py`, `db.py`, `costing.py`, …). `database/` – esquemas SQLite y MySQL.
- `public/` – interfaz web (HTML/CSS/JS). `installer/` – generación del .exe para Windows.
