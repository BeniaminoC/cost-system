# Publicar el Sistema de Costos en Internet
GitHub + Vercel + Aiven, paso a paso

## Qué vas a lograr
Un enlace como `https://delicious-food-costos.vercel.app` que abre el sistema desde cualquier celular o computador. Tres servicios gratuitos trabajan juntos: **Aiven** guarda la base de datos MySQL, **GitHub** guarda el código y **Vercel** lo ejecuta y te da el enlace.

Antes de empezar ten a mano: la carpeta `delicious-food-costos` ya descomprimida (clic derecho sobre el .zip → Extraer todo), tu correo y una contraseña inventada para el usuario **admin** del sistema en línea (mínimo 8 caracteres, con letras y números). Anótala en papel.

> Los planes gratuitos de estos servicios cambian con el tiempo. Si algún botón tiene otro nombre, busca el equivalente.

## Parte 1. La base de datos en Aiven (unos 10 minutos)
1. Entra a aiven.io y pulsa **Get started for free** / **Sign up** (puedes usar tu cuenta de Google).
2. Si pide nombre de organización o proyecto, escribe cualquiera (por ejemplo `costos`).
3. Pulsa **Create service** y elige **MySQL**.
4. En el plan elige **Free**. Si deja escoger región, elige una de Estados Unidos (ideal Virginia / N. Virginia), cerca de los servidores de Vercel.
5. Nombre: `costos-mysql`. Pulsa **Create service**.
6. Espera a que el estado diga **Running** (2 a 5 minutos).
7. En la página del servicio, en **Connection information**, copia la **Service URI** (botón de copiar). Es una línea que empieza con `mysql://avnadmin:` y termina con `?ssl-mode=REQUIRED`. Pégala en el Bloc de notas.

La Service URI es la llave de la base de datos: no la publiques ni la envíes por chats.

## Parte 2. El código en GitHub (unos 5 minutos)
1. Entra a github.com y crea una cuenta (**Sign up**).
2. Arriba a la derecha: **+ → New repository**. Nombre: `sistema-costos`. Marca **Private**. **Create repository**.
3. En la página que aparece pulsa el enlace **uploading an existing file**.
4. Abre en tu computador la carpeta `delicious-food-costos`, **entra a ella**, selecciona todo lo que hay adentro (Ctrl + A) y arrástralo a la página de GitHub.
5. Espera a que terminen de subir los archivos y pulsa **Commit changes**.
6. Revisa el repositorio: deben verse `backend`, `config`, `database`, `docs`, `public` y los archivos `wsgi.py`, `vercel.json`, `requirements.txt`.

Lo importante: arrastra el **contenido** de la carpeta, no la carpeta. Si subes la carpeta completa, `wsgi.py` queda dentro de `delicious-food-costos` y Vercel no lo encuentra (solución en «Problemas frecuentes»).

## Parte 3. Publicar en Vercel (unos 5 minutos)
1. Entra a vercel.com, **Sign Up**, plan **Hobby** (gratis, uso personal) y **Continue with GitHub**. Autoriza.
2. **Add New… → Project**. Aparece `sistema-costos`; si no, pulsa **Configure GitHub App** y dale acceso a ese repositorio. Pulsa **Import**.
3. En la pantalla de configuración, **Framework Preset** debe decir **Flask** (si dice Other, revisa que `requirements.txt` y `wsgi.py` estén en la raíz del repositorio). No cambies nada más.
4. Abre **Environment Variables** y agrega:

| Nombre (Key) | Valor (Value) |
|---|---|
| `DATABASE_URL` | La Service URI que copiaste de Aiven |
| `ADMIN_PASSWORD` | La contraseña que inventaste para admin (mín. 8, letras y números) |

5. Pulsa **Deploy** y espera 1 o 2 minutos hasta que aparezca **Congratulations**.
6. **Continue to Dashboard**. En **Domains** está tu enlace (`sistema-costos-xxxx.vercel.app`). Ese es el que compartes. Los enlaces largos de la sección Deployments piden iniciar sesión en Vercel; el que se comparte es el de Domains.

## Parte 4. Primer ingreso
Abre tu enlace. **La primera vez tarda entre 10 y 30 segundos**: el sistema crea solo todas las tablas y carga una empresa de ejemplo. Si ves un error de «tiempo agotado», espera un minuto y recarga la página.

Entra con usuario `admin` y la contraseña de `ADMIN_PASSWORD`. Los usuarios `usuario` y `estudiante` **no existen** en línea (por seguridad): créalos en **Administración → Usuarios**.

Para empezar sin la empresa de ejemplo, agrega antes de desplegar la variable `CARGAR_DATOS_EJEMPLO` = `false`.

## Parte 5. Llevar los datos que ya tienes en tu PC
1. En el sistema de tu computador (abierto con `iniciar.bat`) entra con admin: **Administración → Copias de seguridad → Descargar copia ahora**. Se guarda un archivo `.json`.
2. En el sistema en línea (admin): **Copias de seguridad → Restaurar desde un archivo**, elige el .json, pulsa **Restaurar archivo** y escribe `RESTAURAR`. Antes de reemplazar, el sistema descarga solo una copia de lo que había en línea.
3. Vuelve a iniciar sesión: los usuarios y contraseñas ahora son los del computador (incluida la de admin, que será la del PC, no la de `ADMIN_PASSWORD`).
4. Funciona también al revés. Tamaño máximo del archivo: 4 MB.

## Parte 6. Cuidar el sistema en línea
- **Copias de seguridad:** el sistema no hace copias automáticas. Descarga una de vez en cuando y siempre antes de una presentación.
- **Si Aiven apaga la base:** el plan gratuito puede apagar el servicio por inactividad y avisa por correo. Si el sistema dice «No se pudo conectar con la base de datos…», entra a Aiven, abre el servicio y enciéndelo (**Power on**).
- **Cambiar una variable** (por ejemplo `DATABASE_URL`): Vercel → proyecto → **Settings → Environment Variables**, cambia el valor, luego **Deployments** → menú de tres puntos del primero → **Redeploy**. Los cambios solo se aplican después de un Redeploy.
- **`ADMIN_PASSWORD` solo se usa la primera vez** (cuando se crean las tablas). Para cambiar la clave de admin después, usa el botón **Cambiar clave** dentro del sistema.
- **Actualizar el programa:** en GitHub, **Add file → Upload files**, arrastra los archivos nuevos (reemplazan a los viejos) y **Commit changes**. Vercel publica solo en un minuto.

## Problemas frecuentes
| Lo que ves | Qué hacer |
|---|---|
| «Falta la variable DATABASE_URL en Vercel» | No quedó guardada. Agrégala en Settings → Environment Variables y haz Redeploy. |
| «La base de datos rechazó el usuario o la contraseña» | La Service URI está incompleta. Cópiala otra vez con el botón de Aiven, reemplázala y Redeploy. |
| «No se pudo conectar con la base de datos…» | El servicio de Aiven está apagado o aún se crea. Debe decir Running. |
| «Por seguridad… no se permite la contraseña inicial» | Falta `ADMIN_PASSWORD` o es débil (mín. 8, letras y números). Corrígela y Redeploy. |
| Vercel con 404: NOT_FOUND | Subiste la carpeta y no su contenido. En Vercel → Settings → General → **Root Directory** escribe `delicious-food-costos`, guarda y Redeploy. |
| El sistema está lento | La base de Aiven quedó en una región lejana (p. ej. Europa). Descarga una copia, crea el servicio de nuevo en Estados Unidos, cambia `DATABASE_URL` y restaura la copia. |
| «El archivo supera el máximo de 4 MB» | Límite de Vercel por petición. |
| «Su sesión expiró» | La sesión dura 60 minutos sin actividad. Inicia sesión de nuevo. |
| Error 500 al desplegar o al abrir | En Vercel → Deployments → tu despliegue → **Logs**; ahí aparece el error exacto. |
