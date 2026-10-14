"use strict";

// ───────────── Definición del formato ─────────────
const NIVELES = [
  { id: "motor", nombre: "Aceite de motor" },
  { id: "refrigerante", nombre: "Refrigerante" },
  { id: "direccion", nombre: "Aceite de dirección" },
  { id: "irrigadores", nombre: "Irrigadores" },
  { id: "freno", nombre: "Freno" },
];
const OPC_SN = [["si", "SÍ"], ["no", "NO"]];
const LUCES = [
  ["cuartos", "Cuartos"], ["direccionales", "Direccionales"], ["intermitentes", "Intermitentes"],
  ["altabaja", "Alta y baja"], ["reversa", "Reversa"], ["neblineros", "Faros neblineros"],
  ["sensor", "Sensor reversa"],
];
const BATERIA = [
  ["sulfatadas", "Terminales sulfatadas"], ["flojas", "Terminales flojas"],
  ["sujecion", "Sujeción batería"], ["fuga", "Fuga ácido"], ["tapon", "Tapón"],
];
const COLS_LLANTA = [["buenas", "Buenas condiciones"], ["golpe", "Golpe en llanta o rin"],
  ["desgastada", "Desgastada"], ["reparacion", "Llanta para reparación"]];
const POSICIONES = ["1", "2", "3", "4", "5", "6", "REFA"];
const GOLPES = [
  { id: "izq", nombre: "Lado izquierdo", img: "./golpe_lado_izq.jpg" },
  { id: "der", nombre: "Lado derecho", img: "./golpe_lado_der.jpg" },
  { id: "frente", nombre: "Frente", img: "./golpe_frente.jpg" },
  { id: "trasera", nombre: "Parte trasera", img: "./golpe_trasera.jpg" },
];

// ───────────── Estado (se guarda solo en el celular) ─────────────
const CLAVE = "checklist-pmm-borrador";
const hoy = () => new Date().toISOString().slice(0, 10);

function estadoVacio() {
  return { eco: "", fecha: hoy(), odometro: "", conductor: "", v: {}, marcas: {}, obs: {}, obs_general: "" };
}
let estado = cargar();

function cargar() {
  try {
    const g = JSON.parse(localStorage.getItem(CLAVE));
    if (g && g.v) return Object.assign(estadoVacio(), g);
  } catch (e) { /* sin almacenamiento: se usa en blanco */ }
  return estadoVacio();
}
function guardar() {
  try { localStorage.setItem(CLAVE, JSON.stringify(estado)); } catch (e) { /* ignorar */ }
}

// ───────────── Construcción de la pantalla ─────────────
const $ = (id) => document.getElementById(id);

// Botones de opción: tocar uno lo marca, tocarlo otra vez lo desmarca.
function segmento(clave, opciones) {
  const cont = document.createElement("div");
  cont.className = "seg";
  for (const [valor, texto] of opciones) {
    const b = document.createElement("button");
    b.type = "button";
    b.dataset.v = valor;
    b.textContent = texto;
    b.setAttribute("aria-pressed", String(estado.v[clave] === valor));
    b.addEventListener("click", () => {
      estado.v[clave] = estado.v[clave] === valor ? "" : valor;
      for (const x of cont.children) x.setAttribute("aria-pressed", String(x.dataset.v === estado.v[clave]));
      guardar();
    });
    cont.appendChild(b);
  }
  return cont;
}

// Barra de nivel de MIN a MAX: se desliza con el dedo y muestra el porcentaje.
const nivelValido = (v) => (typeof v === "number" && v >= 0 && v <= 100 ? v : null);

function barraNivel(clave) {
  const cont = document.createElement("div");
  cont.className = "nivel-barra";
  cont.innerHTML = `<div class="escala"><span>MIN</span><span class="pct"></span><span>MAX</span></div>
    <input type="range" min="0" max="100" step="5" aria-label="Nivel de MIN a MAX">
    <div class="marcas"><i></i><i></i><i></i><i></i><i></i></div>`;
  const rango = cont.querySelector("input");
  const pct = cont.querySelector(".pct");
  const pintar = () => {
    const v = nivelValido(estado.v[clave]);
    cont.classList.toggle("vacio", v === null);
    cont.classList.toggle("bajo", v !== null && v <= 25);
    rango.value = v === null ? 50 : v;
    rango.style.setProperty("--p", (v === null ? 50 : v) + "%");
    pct.textContent = v === null ? "Desliza para marcar" : v + "%";
  };
  rango.addEventListener("input", () => { estado.v[clave] = Number(rango.value); pintar(); guardar(); });
  pintar();
  return cont;
}

function filaSN(clave, nombre) {
  const f = document.createElement("div");
  f.className = "fila";
  f.innerHTML = `<span class="nombre"></span>`;
  f.firstChild.textContent = nombre;
  f.appendChild(segmento(clave, OPC_SN));
  return f;
}

function construir() {
  for (const id of ["eco", "fecha", "odometro", "conductor"]) {
    $(id).value = estado[id];
    $(id).addEventListener("input", () => { estado[id] = $(id).value; $(id).classList.remove("error"); guardar(); });
  }

  for (const n of NIVELES) {
    const d = document.createElement("div");
    d.className = "nivel-item";
    d.innerHTML = `<div class="nombre"></div>
      <div class="fila"><span class="etq">Nivel</span></div>
      <div class="fila"><span class="etq">Tapón</span></div>`;
    d.firstChild.textContent = n.nombre;
    d.children[1].appendChild(barraNivel(`nivel_${n.id}`));
    d.children[2].appendChild(segmento(`tapon_${n.id}`, OPC_SN));
    $("niveles").appendChild(d);
  }

  for (const [id, nombre] of LUCES) $("luces").appendChild(filaSN(`luz_${id}`, nombre));

  for (const [id, nombre] of [["tarjeta", "Tarjeta de circulación"], ["poliza", "Póliza de seguros"]]) {
    const d = document.createElement("div");
    d.className = "nivel-item";
    d.innerHTML = `<div class="nombre"></div>
      <div class="fila"><span class="etq">¿Tiene?</span></div>
      <div class="fila"><span class="etq">Vigente</span></div>
      <div class="fila"><span class="etq">Vigencia</span><input type="date" class="fecha-doc" aria-label="Fecha de vigencia"></div>`;
    d.firstChild.textContent = nombre;
    d.children[1].appendChild(segmento(`${id}_tiene`, OPC_SN));
    d.children[2].appendChild(segmento(`${id}_vigente`, OPC_SN));
    const fecha = d.querySelector(".fecha-doc");
    fecha.value = estado.v[`${id}_fecha`] || "";
    fecha.addEventListener("input", () => { estado.v[`${id}_fecha`] = fecha.value; guardar(); });
    $("docs").appendChild(d);
  }

  for (const [id, nombre] of BATERIA) $("bateria").appendChild(filaSN(`bat_${id}`, nombre));

  const tabla = document.createElement("div");
  tabla.className = "scroll";
  let html = `<table class="tabla-llantas"><thead><tr><th>Pos.</th><th>No. económico</th>`;
  for (const t of ["Buenas cond.", "Golpe llanta/rin", "Desgas-tada", "Para repar."]) html += `<th>${t.replace("-", "&shy;")}</th>`;
  html += `</tr></thead><tbody>`;
  for (const p of POSICIONES) {
    html += `<tr><td>${p === "REFA" ? "Refa:" : p + "-"}</td><td><input class="eco-llanta" data-eco="llanta_eco_${p}" autocomplete="off" aria-label="No. económico posición ${p}"></td>`;
    for (const [c] of COLS_LLANTA) html += `<td data-k="llanta_${p}_${c}"></td>`;
    html += `</tr>`;
  }
  tabla.innerHTML = html + `</tbody></table>`;
  tabla.querySelectorAll("input[data-eco]").forEach((inp) => {
    inp.value = estado.v[inp.dataset.eco] || "";
    inp.addEventListener("input", () => { estado.v[inp.dataset.eco] = inp.value; guardar(); });
  });
  tabla.querySelectorAll("td[data-k]").forEach((td) => td.appendChild(segmento(td.dataset.k, OPC_SN)));
  $("llantas").appendChild(tabla);

  for (const g of GOLPES) $("golpes").appendChild(construirGolpe(g));

  $("obs_general").value = estado.obs_general;
  $("obs_general").addEventListener("input", () => { estado.obs_general = $("obs_general").value; guardar(); });
}

// ───────────── Golpes: marcar sobre el dibujo ─────────────
const lienzos = {}; // id -> {canvas, img}

function construirGolpe(g) {
  const cont = document.createElement("div");
  cont.className = "golpe card";
  cont.innerHTML = `<label></label>
    <canvas></canvas>
    <div class="acciones"><span class="cuenta"></span><button type="button">Deshacer última marca</button></div>
    <textarea rows="2" placeholder="Describe el golpe (opcional)"></textarea>`;
  cont.querySelector("label").textContent = g.nombre;
  const canvas = cont.querySelector("canvas");
  const cuenta = cont.querySelector(".cuenta");
  const img = new Image();
  estado.marcas[g.id] = estado.marcas[g.id] || [];
  lienzos[g.id] = { canvas, img };

  const dibujar = () => {
    const ctx = canvas.getContext("2d");
    ctx.drawImage(img, 0, 0);
    const r = Math.max(14, canvas.width * 0.025);
    estado.marcas[g.id].forEach((m, i) => {
      const x = m.x * canvas.width, y = m.y * canvas.height;
      ctx.beginPath(); ctx.arc(x, y, r, 0, 7);
      ctx.fillStyle = "rgba(211,47,47,.85)"; ctx.fill();
      ctx.lineWidth = 2; ctx.strokeStyle = "#fff"; ctx.stroke();
      ctx.fillStyle = "#fff"; ctx.font = `bold ${r * 1.1}px sans-serif`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(String(i + 1), x, y + 1);
    });
    cuenta.textContent = `${estado.marcas[g.id].length} marca(s)`;
  };
  img.onload = () => { canvas.width = img.naturalWidth; canvas.height = img.naturalHeight; dibujar(); };
  img.src = g.img;
  lienzos[g.id].dibujar = dibujar;

  canvas.addEventListener("click", (e) => {
    const rc = canvas.getBoundingClientRect();
    estado.marcas[g.id].push({ x: (e.clientX - rc.left) / rc.width, y: (e.clientY - rc.top) / rc.height });
    guardar(); dibujar();
  });
  cont.querySelector("button").addEventListener("click", () => { estado.marcas[g.id].pop(); guardar(); dibujar(); });
  const ta = cont.querySelector("textarea");
  ta.value = estado.obs[g.id] || "";
  ta.addEventListener("input", () => { estado.obs[g.id] = ta.value; guardar(); });
  return cont;
}

// ───────────── Generación del PDF (2 páginas, como el formato) ─────────────
const AZUL = [18, 49, 95];

function cargarImagen(src) {
  return new Promise((ok, fallo) => { const i = new Image(); i.onload = () => ok(i); i.onerror = fallo; i.src = src; });
}
const fechaMx = (iso) => (iso ? iso.split("-").reverse().join("/") : "");
const val = (k) => estado.v[k] || "";

async function generarPDF() {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({ unit: "mm", format: "a4" });

  const banda = (txt, x, y, w) => {
    doc.setFillColor(...AZUL); doc.roundedRect(x, y, w, 7, 2, 2, "F");
    doc.setTextColor(255); doc.setFont("helvetica", "bold"); doc.setFontSize(11);
    doc.text(txt, x + w / 2, y + 5, { align: "center" }); doc.setTextColor(0);
  };
  const caja = (x, y, w, h) => { doc.setDrawColor(...AZUL); doc.setLineWidth(0.5); doc.roundedRect(x, y, w, h, 2, 2); };
  const texto = (t, x, y, tam = 9, neg = false) => {
    doc.setFont("helvetica", neg ? "bold" : "normal"); doc.setFontSize(tam); doc.text(String(t), x, y);
  };
  // Dibuja opciones con un cuadrito; el elegido lleva una X.
  const opciones = (x, y, lista, elegido) => {
    let cx = x;
    for (const [v, t] of lista) {
      doc.setDrawColor(60); doc.setLineWidth(0.3); doc.rect(cx, y - 3, 4, 4);
      if (elegido === v) texto("X", cx + 0.8, y, 9, true);
      texto(t, cx + 5.5, y, 8);
      cx += 6.5 + doc.getTextWidth(t);
    }
  };

  // Barra de nivel: relleno desde MIN hasta el valor marcado, con rayitas cada 25%.
  const barraPDF = (x, y, v) => {
    const w = 32;
    doc.setDrawColor(60); doc.setLineWidth(0.3); doc.setFillColor(255);
    doc.rect(x, y - 3.5, w, 4, "FD");
    if (v !== null) {
      v <= 25 ? doc.setFillColor(211, 47, 47) : doc.setFillColor(...AZUL);
      if (v > 0) doc.rect(x, y - 3.5, w * v / 100, 4, "F");
      doc.setDrawColor(0); doc.setLineWidth(0.7); doc.line(x + w * v / 100, y - 5, x + w * v / 100, y + 1.5);
      texto(v + "%", x + w + 2, y, 8, true);
    } else texto("-", x + w + 2, y, 8);
    doc.setDrawColor(120); doc.setLineWidth(0.2);
    [25, 50, 75].forEach((m) => doc.line(x + w * m / 100, y - 3.5, x + w * m / 100, y - 2));
    texto("MIN", x, y + 4, 5.5); texto("MAX", x + w - 5, y + 4, 5.5);
  };

  // Página 1 – encabezado
  const logo = await cargarImagen("./logo.jpg");
  doc.addImage(logo, "JPEG", 10, 6, 68, 68 * logo.naturalHeight / logo.naturalWidth);
  const campos = [["No. Eco", estado.eco], ["Fecha", fechaMx(estado.fecha)], ["Odómetro", estado.odometro], ["Conductor", estado.conductor]];
  campos.forEach(([n, v], i) => {
    const x = 10 + i * 48;
    caja(x, 27, 45, 11);
    texto(n + ":", x + 2, 31.5, 8, true);
    texto(v, x + 2, 36, 9);
  });

  // Niveles
  banda("NIVELES", 10, 41, 190);
  NIVELES.forEach((n, i) => {
    const col = i % 2, fila = Math.floor(i / 2);
    const x = 10 + col * 62, y = 52 + fila * 24;
    texto(n.nombre.toUpperCase() + ":", x, y, 8.5, true);
    texto("Nivel", x, y + 7, 8); barraPDF(x + 11, y + 7, nivelValido(estado.v[`nivel_${n.id}`]));
    texto("Tapón", x, y + 16.5, 8); opciones(x + 11, y + 16.5, OPC_SN, val(`tapon_${n.id}`));
  });
  // Luces
  caja(134, 48, 66, 74);
  texto("LUCES (¿funciona?)", 138, 54, 9, true);
  LUCES.forEach(([id, n], i) => {
    const y = 62 + i * 8;
    texto(n, 138, y, 8); opciones(172, y, OPC_SN, val(`luz_${id}`));
  });

  // Tarjeta y póliza
  caja(10, 126, 92, 42);
  texto("TARJETA DE CIRCULACIÓN / PÓLIZA SEGUROS", 13, 132, 8.5, true);
  [["tarjeta", "Tarjeta de circulación"], ["poliza", "Póliza de seguros"]].forEach(([id, n], i) => {
    const y = 140 + i * 14;
    texto(n + ":", 13, y, 8.5, true);
    texto("Vigencia:", 52, y, 8);
    doc.setDrawColor(60); doc.setLineWidth(0.3); doc.rect(65, y - 4, 34, 5.5);
    texto(fechaMx(val(`${id}_fecha`)), 67, y, 8.5);
    texto("¿Tiene?", 13, y + 6, 8); opciones(26, y + 6, OPC_SN, val(`${id}_tiene`));
    texto("Vigente", 56, y + 6, 8); opciones(70, y + 6, OPC_SN, val(`${id}_vigente`));
  });
  // Batería
  caja(106, 126, 94, 42);
  texto("CHECKLIST BATERÍA", 109, 132, 9, true);
  BATERIA.forEach(([id, n], i) => {
    const y = 138 + i * 6;
    texto(n + ":", 109, y, 8); opciones(165, y, OPC_SN, val(`bat_${id}`));
  });

  // Llantas
  banda("LLANTAS", 10, 173, 190);
  const x0 = 10, w0 = 34, wc = 39;
  doc.setFillColor(...AZUL); doc.rect(x0, 182, w0 + wc * 4, 11, "F");
  doc.setTextColor(255); doc.setFont("helvetica", "bold"); doc.setFontSize(7.5);
  doc.text("POSICIÓN /", x0 + 2, 186); doc.text("No. ECONÓMICO", x0 + 2, 190);
  COLS_LLANTA.forEach(([, t], i) => doc.text(t.toUpperCase(), x0 + w0 + wc * i + wc / 2, 186, { align: "center", maxWidth: wc - 2 }));
  doc.setTextColor(0);
  POSICIONES.forEach((p, r) => {
    const y = 193 + r * 9;
    doc.setDrawColor(150); doc.setLineWidth(0.2); doc.rect(x0, y, w0 + wc * 4, 9);
    texto(p === "REFA" ? "REFA:" : p + "-", x0 + 2, y + 6, 9, true);
    texto(val(`llanta_eco_${p}`), x0 + (p === "REFA" ? 14 : 8), y + 6, 9);
    COLS_LLANTA.forEach(([c], i) => opciones(x0 + w0 + wc * i + 4, y + 6, OPC_SN, val(`llanta_${p}_${c}`)));
  });
  doc.setDrawColor(...AZUL); doc.setLineWidth(0.5); doc.roundedRect(x0, 182, w0 + wc * 4, 74, 2, 2);

  // Página 2 – golpes y observaciones
  doc.addPage();
  banda("GOLPES", 10, 10, 100);
  banda("OBSERVACIONES", 115, 10, 85);
  let y = 20;
  for (const g of GOLPES) {
    const { canvas } = lienzos[g.id];
    const w = g.id === "trasera" ? 75 : 100;
    const h = w * canvas.height / canvas.width;
    doc.addImage(canvas.toDataURL("image/jpeg", 0.85), "JPEG", 10, y, w, h);
    doc.setDrawColor(...AZUL); doc.setLineWidth(0.5); doc.roundedRect(10, y, w, h, 2, 2);
    texto(g.nombre + ":", 115, y + 5, 8.5, true);
    const lineas = doc.splitTextToSize(estado.obs[g.id] || "", 82);
    doc.setFont("helvetica", "normal"); doc.setFontSize(9);
    doc.text(lineas.slice(0, 7), 115, y + 11);
    y += h + 6;
  }
  banda("OBSERVACIONES GENERALES", 10, y + 2, 190);
  const gen = doc.splitTextToSize(estado.obs_general || "", 186);
  doc.setFont("helvetica", "normal"); doc.setFontSize(9);
  doc.text(gen.slice(0, 12), 12, y + 14);

  doc.setFontSize(7); doc.setTextColor(120);
  doc.text(`Generado desde la app Checklist PMM - ${new Date().toLocaleString("es-MX")}`, 10, 291);
  return doc;
}

// ───────────── Envío por WhatsApp ─────────────
const WHATSAPP = "523111416176"; // 311 141 6176 (México, +52)

function modal(texto, botones) {
  $("modal-texto").textContent = texto;
  const cont = $("modal-acciones");
  cont.replaceChildren();
  for (const [t, fn, sec] of botones) {
    const b = document.createElement("button");
    b.textContent = t; if (sec) b.className = "sec";
    b.addEventListener("click", () => { $("modal").hidden = true; if (fn) fn(); });
    cont.appendChild(b);
  }
  $("modal").hidden = false;
}

function faltantes() {
  const f = [];
  for (const [id, n] of [["eco", "No. Eco"], ["fecha", "Fecha"], ["odometro", "Odómetro"], ["conductor", "Conductor"]]) {
    if (!String(estado[id]).trim()) { f.push(n); $(id).classList.add("error"); }
  }
  return f;
}

function descargar(blob, nombre) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = nombre; a.click();
}

async function enviar() {
  const falta = faltantes();
  if (falta.length) { window.scrollTo({ top: 0, behavior: "smooth" }); modal("Falta llenar: " + falta.join(", ") + ".", [["Entendido"]]); return; }

  const btn = $("enviar");
  btn.disabled = true; btn.textContent = "Preparando PDF…";
  try {
    const doc = await generarPDF();
    const nombre = `Checklist_${estado.eco.trim().replace(/[^\w-]/g, "")}_${estado.fecha}.pdf`;
    const blob = doc.output("blob");
    const archivo = new File([blob], nombre, { type: "application/pdf" });
    const texto = `Checklist unidad ${estado.eco.trim()} - ${fechaMx(estado.fecha)} - Conductor: ${estado.conductor.trim()}`;

    if (navigator.canShare && navigator.canShare({ files: [archivo] })) {
      // Abre el menú de Android: el usuario elige WhatsApp y el contacto.
      try {
        await navigator.share({ files: [archivo], text: texto });
        modal("Listo. Si ya enviaste el PDF por WhatsApp, puedes empezar un checklist nuevo.", [
          ["Nuevo checklist", () => limpiar(true)], ["Cerrar", null, true]]);
      } catch (e) {
        if (e.name !== "AbortError") throw e; // si cancela, no pasa nada
      }
    } else {
      // Plan B: descarga el PDF y abre el chat de WhatsApp para adjuntarlo.
      descargar(blob, nombre);
      modal("El PDF se descargó en tu celular. Toca 'Abrir WhatsApp' y adjunta el archivo " + nombre + " (clip → Documento).", [
        ["Abrir WhatsApp", () => window.open(`https://wa.me/${WHATSAPP}?text=${encodeURIComponent(texto)}`, "_blank")],
        ["Cerrar", null, true]]);
    }
  } catch (e) {
    modal("No se pudo preparar el PDF. Intenta de nuevo.", [["Cerrar"]]);
  } finally {
    btn.disabled = false; btn.textContent = "Enviar por WhatsApp";
  }
}

function limpiar(sinPreguntar) {
  const borrar = () => { estado = estadoVacio(); guardar(); location.reload(); };
  if (sinPreguntar === true) return borrar();
  modal("¿Borrar todo lo capturado y empezar un checklist nuevo?", [["Sí, borrar", borrar], ["Cancelar", null, true]]);
}

construir();
$("enviar").addEventListener("click", enviar);
$("limpiar").addEventListener("click", limpiar);
if ("serviceWorker" in navigator) navigator.serviceWorker.register("./sw.js").catch(() => {});
