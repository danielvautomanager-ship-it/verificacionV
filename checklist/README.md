# Checklist PMM (app para Android)

App web instalable (PWA) con el formato "Checklist frente Isuzu y Hino".
Se llena en el celular, genera un PDF igual al formato y lo envía por **WhatsApp** al **311 141 6176**.

## Cómo se usa
1. Llenar No. Eco, Fecha, Odómetro y Conductor; marcar niveles, luces, documentos, batería y llantas;
   tocar el dibujo de la unidad para marcar golpes.
2. Tocar **Enviar por WhatsApp**.
3. Android abre el menú de compartir con el PDF adjunto: elegir **WhatsApp** y el contacto 311 141 6176
   y tocar enviar. (WhatsApp exige que una persona confirme el envío; ninguna app puede mandarlo sola.)

Si el celular no soporta el menú de compartir, la app descarga el PDF y abre el chat de WhatsApp
con el número ya puesto para adjuntar el archivo.

## Probar en tu computadora
```bash
cd checklist/static
python3 -m http.server 8000     # abre http://localhost:8000
```

## Publicarla (necesario para instalarla en Android)
Android solo instala la app si se abre por **HTTPS**. Son archivos estáticos, no necesita servidor.

**Opción A – la más rápida (1 minuto, sin cuenta de programador):**
1. Descarga `checklist/Checklist-PMM-app.zip` y descomprímelo en una carpeta.
2. Entra a https://app.netlify.com/drop, arrastra la carpeta descomprimida.
3. Netlify te da una dirección `https://....netlify.app`. Esa es tu app.

**Opción B – GitHub Pages (automática):** al unir (merge) esta rama a la rama principal del repositorio,
el archivo `.github/workflows/pages.yml` la publica solo. Antes, una sola vez: Settings → Pages →
Source: **GitHub Actions**.

## Instalarla en el celular
1. Abrir la dirección HTTPS en **Chrome**.
2. Menú ⋮ → **Instalar aplicación**.
3. Queda el ícono "Checklist PMM" como cualquier app y abre incluso sin internet.
