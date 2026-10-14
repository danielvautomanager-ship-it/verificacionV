# Checklist PMM (app para Android)

App web instalable (PWA) con el formato "Checklist frente Isuzu y Hino".
Se llena en el celular, genera un PDF igual al formato y lo envía como **adjunto** a:

- supervisorflotillas@pmm.com.mx
- flotillas@pmm.com.mx
- gerenciatpc@pmm.com.mx

## 1. Probar en tu computadora

```bash
cd checklist
pip install -r requirements.txt
python server.py          # abre http://localhost:5000
```

## 2. Configurar el correo que envía (obligatorio para que mande)

El envío sale desde una cuenta de correo tuya (la "cuenta remitente").
Con Gmail: activa la verificación en 2 pasos y crea una **contraseña de aplicación**
(https://myaccount.google.com/apppasswords). Luego define estas variables:

```bash
export SMTP_USER="tu_cuenta@gmail.com"
export SMTP_PASSWORD="la_contraseña_de_aplicación"
# Opcionales (por defecto Gmail): SMTP_HOST=smtp.gmail.com  SMTP_PORT=587  SMTP_FROM
```

Nunca escribas la contraseña dentro del código ni la subas a GitHub.

## 3. Publicarla en internet (necesario para usarla en Android)

Android solo permite instalar la app si se abre por **HTTPS**. Sube la carpeta `checklist`
a un hosting que corra Python (Render, Railway, Fly.io, PythonAnywhere, etc.) con:

- Comando de inicio: `gunicorn server:app`
- Variables de entorno: `SMTP_USER` y `SMTP_PASSWORD`

## 4. Instalarla en el celular Android

1. Abre la dirección HTTPS en **Chrome**.
2. Menú ⋮ → **Instalar aplicación** (o "Agregar a pantalla principal").
3. Aparece el ícono "Checklist PMM" como cualquier app.

## Cómo se usa

Llenar No. Eco, Fecha, Odómetro y Conductor → marcar niveles, luces, documentos, batería y
llantas → tocar el dibujo de la unidad para marcar golpes → **Enviar checklist**.
Si no hay internet, los datos quedan guardados en el celular y se puede reintentar,
o compartir el PDF por correo/WhatsApp.
