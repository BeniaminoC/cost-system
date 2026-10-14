/* Delicious Food - Sistema de Costos. Frontend sin dependencias (funciona sin internet). */
const $ = s => document.querySelector(s);
const S = { token: sessionStorage.getItem('tk'), user: null, meta: null, emp: null, emps: [], periodos: [], productos: [] };
const nf0 = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
const nf2 = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 });
const nf1 = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 1 });
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const money = v => '$ ' + nf0.format(v || 0);

async function api(path, { method = 'GET', body, raw } = {}) {
  const r = await fetch('/api/' + path, { method, headers: { 'Content-Type': 'application/json', ...(S.token ? { Authorization: 'Bearer ' + S.token } : {}) }, body: body ? JSON.stringify(body) : undefined });
  const nt = r.headers.get('X-Token'); if (nt && S.token) { S.token = nt; try { sessionStorage.setItem('tk', nt); } catch (e) { } }
  if (raw && r.ok) return r.blob();
  const d = await r.json().catch(() => ({}));
  if (r.status === 401 && S.user) { toast(d.error); logout(true); throw d; }
  if (!r.ok) throw d;
  return d;
}
function toast(m) { const t = $('#toast'); t.textContent = m; t.hidden = false; clearTimeout(toast.t); toast.t = setTimeout(() => t.hidden = true, 3200); }
const errBox = errs => `<div class="err"><ul>${(errs || ['Error desconocido']).map(e => `<li>${esc(e)}</li>`).join('')}</ul></div>`;

/* ---------- sesión ---------- */
$('#loginForm').onsubmit = async e => {
  e.preventDefault();
  try {
    const d = await api('login', { method: 'POST', body: { username: $('#lu').value, password: $('#lp').value } });
    S.token = d.token; sessionStorage.setItem('tk', d.token); await start();
  } catch (x) { const b = $('#loginErr'); b.hidden = false; b.textContent = x.error || 'No se pudo iniciar sesión.'; }
};
async function logout(silent) {
  if (!silent) { try { await api('logout', { method: 'POST' }); } catch (e) { } }
  sessionStorage.removeItem('tk'); S.token = null; S.user = null; $('#app').hidden = true; $('#login').hidden = false; $('#lp').value = '';
}
$('#logoutBtn').onclick = () => logout();
$('#menuBtn').onclick = () => $('#nav').classList.toggle('open');
$('#pwBtn').onclick = () => openForm({
  title: 'Cambiar contraseña', fields: [{ n: 'actual', l: 'Contraseña actual', t: 'pwd', req: true }, { n: 'nueva', l: 'Contraseña nueva (mín. 6 caracteres)', t: 'pwd', req: true }],
  save: async v => { await api('cambiar-clave', { method: 'POST', body: v }); toast('Contraseña actualizada'); }
});

async function start() {
  try { S.meta = await api('meta'); } catch (e) { return logout(true); }
  S.user = S.meta.user; $('#login').hidden = true; $('#app').hidden = false;
  document.title = S.meta.app.nombre;
  const rol = { admin: 'Administrador', usuario: 'Usuario', estudiante: 'Estudiante' }[S.user.rol];
  $('#userBox').textContent = `${S.user.username} (${rol})`;
  buildNav(); await loadEmpresas(); go(location.hash.slice(1) || 'dash');
}
async function loadEmpresas() {
  S.emps = await api('e/empresas');
  const sel = $('#empSel'); sel.innerHTML = S.emps.map(e => `<option value="${e.id}">${esc(e.razon_social)}</option>`).join('');
  if (!S.emps.find(e => e.id == S.emp)) S.emp = S.emps[0]?.id || null;
  sel.value = S.emp;
  await loadFilters();
}
$('#empSel').onchange = async e => { S.emp = +e.target.value; await loadFilters(); go(S.cur || 'dash'); };
async function loadFilters() {
  if (!S.emp) { S.periodos = []; S.productos = []; return; }
  [S.periodos, S.productos] = await Promise.all([api('opciones/periodos?empresa_id=' + S.emp), api('opciones/productos?empresa_id=' + S.emp)]);
}

/* ---------- navegación ---------- */
const REPS = { hoja_costos: 'Hoja de costos', materiales: 'Reporte de materiales', mod: 'Reporte de MOD', cif: 'Reporte de CIF', produccion: 'Reporte de producción', variaciones: 'Reporte de variaciones', estado_costos: 'Estado de costos de producción' };
function buildNav() {
  const E = S.meta.entities, has = k => k in E;
  const groups = [['Inicio', [['dash', 'Panel de control']]],
  ['Datos generales', ['empresas', 'periodos', 'productos', 'unidades', 'centros_costo'].filter(has).map(k => ['e:' + k, E[k].label])],
  ['Materias primas directas', ['materias_primas', 'receta'].map(k => ['e:' + k, E[k].label])],
  ['Mano de obra directa', ['trabajadores', 'producto_mod'].map(k => ['e:' + k, E[k].label])],
  ['Costos indirectos', [['e:cif', E.cif.label]]],
  ['Producción', ['ordenes', 'orden_mp', 'orden_mod'].map(k => ['e:' + k, E[k].label])],
  ['Costos y variaciones', [['r:hoja_costos', 'Hoja de costos'], ['r:variaciones', 'Análisis de variaciones']]],
  ['Reportes', ['materiales', 'mod', 'cif', 'produccion', 'estado_costos'].map(k => ['r:' + k, REPS[k]])],
  ['Administración', ['usuarios', 'actividad'].filter(has).map(k => ['e:' + k, E[k].label]).concat(has('usuarios') ? [['r2:respaldo', 'Copias de seguridad']] : [])]];
  $('#nav').innerHTML = '<div class="logo">Delicious Food</div>' + groups.filter(g => g[1].length).map(g => `<h4>${g[0]}</h4>` + g[1].map(i => `<a data-r="${i[0]}">${esc(i[1])}</a>`).join('')).join('');
  $('#nav').onclick = e => { const a = e.target.closest('a'); if (a) { go(a.dataset.r); $('#nav').classList.remove('open'); } };
}
function go(route) {
  S.cur = route; location.hash = route;
  document.querySelectorAll('#nav a').forEach(a => a.classList.toggle('on', a.dataset.r === route));
  const v = $('#view');
  if (!S.emp && route !== 'e:empresas') { v.innerHTML = '<div class="card empty">Primero cree una empresa en «Empresas».</div>'; if (S.meta.entities.empresas.perms.create) return go('e:empresas'); return; }
  if (route === 'dash') dashboard(); else if (route.startsWith('e:')) crud(route.slice(2)); else if (route.startsWith('r:')) reportView(route.slice(2)); else if (route === 'r2:respaldo') backupView();
}

/* ---------- CRUD genérico ---------- */
const optCache = {};
async function opts(ref) { return api(`opciones/${ref}?empresa_id=${S.emp || 0}`); }
function cellVal(fd, row) {
  const v = row[fd.n];
  if (fd.t === 'ref') return esc(row[fd.n + '__l'] ?? '');
  if (fd.t === 'sel') return esc((fd.opts.find(o => String(o[0]) === String(v)) || [0, v ?? ''])[1]);
  if (fd.t === 'pct') return nf2.format(v || 0) + ' %';
  if (typeof v === 'number') return nf2.format(v);
  return esc(v ?? '');
}
async function crud(key) {
  const E = S.meta.entities[key], v = $('#view');
  const F = Object.fromEntries(E.fields.map(f => [f.n, f]));
  const hasPer = !!F.periodo_id;
  v.innerHTML = `<div class="head"><h2>${esc(E.label)}</h2>
    ${hasPer ? `<select id="fPer"><option value="">Todos los períodos</option>${S.periodos.map(p => `<option value="${p.id}">${esc(p.label)}</option>`).join('')}</select>` : ''}
    ${E.search ? '<input id="fQ" placeholder="Buscar…" type="search">' : ''}
    ${E.perms.create ? '<button class="btn primary" id="newBtn">Nuevo</button>' : ''}</div>
    ${key === 'cif' ? '<div id="cifStrip"></div>' : ''}<div class="tw" id="tbl"></div>`;
  const load = async () => {
    const p = new URLSearchParams({ empresa_id: S.emp || 0 });
    if (hasPer && $('#fPer').value) p.set('periodo_id', $('#fPer').value);
    if (E.search && $('#fQ').value) p.set('q', $('#fQ').value);
    const rows = await api(`e/${key}?${p}`);
    const cols = E.cols.map(n => F[n]);
    $('#tbl').innerHTML = rows.length ? `<table><thead><tr>${cols.map(f => `<th class="${['num', 'pct', 'ro'].includes(f.t) ? 'n' : ''}">${esc(f.l)}</th>`).join('')}${E.perms.update || E.perms.delete ? '<th></th>' : ''}</tr></thead><tbody>${rows.map(r => `<tr>${cols.map(f => `<td class="${['num', 'pct', 'ro'].includes(f.t) && typeof r[f.n] === 'number' ? 'n' : ''}">${cellVal(f, r)}</td>`).join('')}${E.perms.update || E.perms.delete ? `<td class="n">${E.perms.update ? `<button class="btn sm" data-ed="${r.id}">Editar</button> ` : ''}${E.perms.delete ? `<button class="btn sm danger" data-del="${r.id}">Eliminar</button>` : ''}</td>` : ''}</tr>`).join('')}</tbody></table>`
      : `<div class="empty">No hay registros todavía.${E.perms.create ? ' Use «Nuevo» para crear el primero.' : ''}</div>`;
    $('#tbl').onclick = async e => {
      const ed = e.target.dataset.ed, del = e.target.dataset.del;
      if (ed) { const row = await api(`e/${key}/${ed}?empresa_id=${S.emp}`); formFor(E, key, row, load); }
      if (del) confirmDlg('¿Eliminar este registro? Esta acción no se puede deshacer.', async () => {
        try { await api(`e/${key}/${del}?empresa_id=${S.emp}`, { method: 'DELETE' }); toast('Registro eliminado'); if (key === 'empresas') await loadEmpresas(); else if (key === 'periodos' || key === 'productos') await loadFilters(); load(); }
        catch (x) { toast(x.error || 'No se pudo eliminar'); }
      });
    };
    if (key === 'cif') cifStrip();
  };
  if ($('#newBtn')) $('#newBtn').onclick = () => formFor(E, key, null, load);
  if (hasPer) $('#fPer').onchange = load;
  if (E.search) $('#fQ').oninput = () => { clearTimeout(crud.t); crud.t = setTimeout(load, 250); };
  load();
}
async function cifStrip() {
  const per = $('#fPer').value, d = await api(`cif-resumen?empresa_id=${S.emp}&periodo_id=${per}`);
  $('#cifStrip').innerHTML = `<div class="tw" style="margin-bottom:14px"><table><thead><tr><th>Período</th><th>Base de aplicación</th><th class="n">CIF fijo ppto.</th><th class="n">CIF variable ppto.</th><th class="n">CIF presupuestado</th><th class="n">Base presupuestada</th><th class="n">Tasa predeterminada</th><th class="n">CIF real</th><th class="n">CIF aplicado</th></tr></thead><tbody>${d.map(p => `<tr><td>${esc(p.codigo)}</td><td>${p.base === 'HMOD' ? 'Horas de MOD' : 'Unidades'}</td><td class="n">${money(p.fijo_p)}</td><td class="n">${money(p.var_p)}</td><td class="n">${money(p.cif_p)}</td><td class="n">${nf2.format(p.base_p)}</td><td class="n"><b>${money(p.tasa)}</b></td><td class="n">${money(p.cif_real)}</td><td class="n">${money(p.aplicado)}</td></tr>`).join('')}</tbody></table></div>`;
}
async function formFor(E, key, row, done) {
  const fields = E.fields.filter(f => f.t !== 'ro' && !(key === 'usuarios' && f.n === 'password' && false));
  for (const f of fields) if (f.t === 'ref') f._o = await opts(f.ref);
  openForm({
    title: (row ? 'Editar registro: ' : 'Nuevo registro: ') + E.label, fields, values: row,
    note: key === 'usuarios' && row ? 'Deje la contraseña vacía para conservar la actual.' : '',
    save: async v => { await api(`e/${key}${row ? '/' + row.id : ''}?empresa_id=${S.emp || 0}`, { method: row ? 'PUT' : 'POST', body: v }); toast('Registro guardado'); if (key === 'empresas') { if (!S.emp) S.emp = null; await loadEmpresas(); } if (key === 'periodos' || key === 'productos') await loadFilters(); done && done(); }
  });
}
function openForm({ title, fields, values = {}, save, note }) {
  const m = $('#modal'); values = values || {};
  const inp = f => {
    const v = values[f.n] ?? f.default ?? '', id = 'f_' + f.n;
    if (f.t === 'sel') return `<select id="${id}">${f.req ? '' : '<option value=""></option>'}${f.opts.map(o => `<option value="${o[0]}" ${String(o[0]) === String(v) ? 'selected' : ''}>${esc(o[1])}</option>`).join('')}</select>`;
    if (f.t === 'ref') return `<select id="${id}"><option value="">Seleccione…</option>${f._o.map(o => `<option value="${o.id}" ${String(o.id) === String(v) ? 'selected' : ''}>${esc(o.label)}</option>`).join('')}</select>`;
    if (f.t === 'date') return `<input id="${id}" type="date" value="${esc(v)}">`;
    if (f.t === 'pwd') return `<input id="${id}" type="password" autocomplete="new-password">`;
    return `<input id="${id}" value="${esc(v)}" ${['num', 'pct'].includes(f.t) ? 'inputmode="decimal"' : ''}>`;
  };
  m.innerHTML = `<div class="dlg" role="dialog" aria-modal="true"><h3>${esc(title)}</h3><div id="fe"></div><div class="grid">${fields.map(f => `<label>${esc(f.l)}${f.req ? ' <span class="req">*</span>' : ''}${inp(f)}</label>`).join('')}</div>${note ? `<small>${esc(note)}</small>` : ''}<div class="acts"><button class="btn" id="cx">Cancelar</button><button class="btn primary" id="ok">Guardar</button></div></div>`;
  m.hidden = false; m.querySelector('input,select')?.focus();
  $('#cx').onclick = () => m.hidden = true;
  $('#ok').onclick = async () => {
    const v = {}, errs = [];
    for (const f of fields) {
      let x = $('#f_' + f.n).value.trim(); v[f.n] = x;
      if (!x && f.req && !(f.t === 'pwd' && values.id)) errs.push(`El campo «${f.l}» es obligatorio.`);
      else if (x && ['num', 'pct'].includes(f.t)) { const n = Number(x.replace(',', '.')); if (isNaN(n)) errs.push(`«${f.l}» debe ser un número válido.`); else if (n < 0) errs.push(`«${f.l}» no puede ser negativo.`); else if (f.t === 'pct' && n > 100) errs.push(`«${f.l}» debe estar entre 0 y 100.`); }
    }
    if (errs.length) { $('#fe').innerHTML = errBox(errs); return; }
    try { await save(v); m.hidden = true; } catch (x) { $('#fe').innerHTML = errBox(x.errores || [x.error]); }
  };
}
function confirmDlg(msg, yes) {
  const m = $('#modal');
  m.innerHTML = `<div class="dlg" role="alertdialog" aria-modal="true"><h3>Confirmar eliminación</h3><p>${esc(msg)}</p><div class="acts"><button class="btn" id="cx">Cancelar</button><button class="btn danger" id="ok">Sí, eliminar</button></div></div>`;
  m.hidden = false; $('#cx').onclick = () => m.hidden = true; $('#ok').onclick = async () => { m.hidden = true; await yes(); };
}
document.addEventListener('keydown', e => { if (e.key === 'Escape') $('#modal').hidden = true; });

/* ---------- reportes ---------- */
function cellRep(t, v) {
  if (v === '' || v == null) return '';
  if (typeof v !== 'number') return v === 'Favorable' ? `<span class="fav">${v}</span>` : v === 'Desfavorable' ? `<span class="des">${v}</span>` : esc(v);
  if (t === 'money') return nf0.format(v);
  if (t === 'pct') return nf1.format(v) + ' %';
  if (t === 'var') return `<span class="${v > 0.5 ? 'des' : v < -0.5 ? 'fav' : ''}">${v > 0.5 ? '▲ ' : v < -0.5 ? '▼ ' : ''}${nf0.format(Math.abs(v))}</span>`;
  return nf2.format(v);
}
function filtersHtml(withProd = true) {
  return `<select id="rPer"><option value="">Todos los períodos</option>${S.periodos.map(p => `<option value="${p.id}">${esc(p.label)}</option>`).join('')}</select>` +
    (withProd ? `<select id="rProd"><option value="">Todos los productos</option>${S.productos.map(p => `<option value="${p.id}">${esc(p.label)}</option>`).join('')}</select>` : '');
}
const qs = () => `empresa_id=${S.emp}&periodo_id=${$('#rPer')?.value || 0}&producto_id=${$('#rProd')?.value || 0}`;
async function reportView(tipo) {
  $('#view').innerHTML = `<div class="head"><h2>${REPS[tipo]}</h2>${filtersHtml()}<span class="noprint"><button class="btn" id="bx">Exportar a Excel</button> <button class="btn" id="bp">Exportar a PDF</button> <button class="btn" id="bi">Imprimir</button></span></div><div id="sub" style="color:var(--mut);margin-bottom:10px"></div><div class="tw" id="rt"></div>`;
  const load = async () => {
    const r = await api(`reporte/${tipo}?${qs()}`);
    $('#sub').textContent = r.subtitulo;
    $('#rt').innerHTML = r.filas.length ? `<table><thead><tr>${r.columnas.map(c => `<th class="${['money', 'num', 'pct', 'var'].includes(c[1]) ? 'n' : ''}">${esc(c[0])}</th>`).join('')}</tr></thead><tbody>${r.filas.map(f => `<tr class="${/^(TOTAL|COSTO TOTAL|=|Suma)/.test(String(f[0])) || /^=/.test(String(f[1] ?? '')) ? 'tot' : ''}">${f.map((v, i) => `<td class="${['money', 'num', 'pct', 'var'].includes(r.columnas[i][1]) ? 'n' : ''}">${cellRep(r.columnas[i][1], v)}</td>`).join('')}</tr>`).join('')}</tbody></table>` : '<div class="empty">No hay datos para los filtros elegidos. Registre órdenes de producción para ver este reporte.</div>';
  };
  const exp = async fmt => {
    try { const b = await api(`reporte/${tipo}?${qs()}&formato=${fmt}`, { raw: true }); const a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = `${tipo}.${fmt}`; a.click(); URL.revokeObjectURL(a.href); toast('Archivo generado'); }
    catch (x) { toast(x.error || 'No se pudo exportar'); }
  };
  $('#rPer').onchange = $('#rProd').onchange = load; $('#bx').onclick = () => exp('xlsx'); $('#bp').onclick = () => exp('pdf'); $('#bi').onclick = () => window.print();
  load();
}

/* ---------- dashboard ---------- */
async function dashboard() {
  $('#view').innerHTML = `<div class="head"><h2>Panel de control</h2>${filtersHtml()}</div><div class="kpis" id="kp"></div><div class="charts"><div class="card"><h3>Costo unitario por producto</h3><canvas id="c1"></canvas><div class="legend"><span><i style="background:#8FA39A"></i>Estándar</span><span><i style="background:#F2B632"></i>Real</span></div></div><div class="card"><h3>Variaciones (rojo desfavorable, verde favorable)</h3><canvas id="c2"></canvas></div><div class="card"><h3>Composición del costo real</h3><canvas id="c3"></canvas><div class="legend" id="lg3"></div></div></div>`;
  const load = async () => {
    const d = await api(`dashboard?${qs()}`), k = d.kpis;
    const kp = (t, v, c = '', cls = '') => `<div class="kpi ${cls}"><small>${t}</small><b class="${c}">${v}</b></div>`;
    const vc = v => v > 0.5 ? 'des' : v < -0.5 ? 'fav' : '';
    $('#kp').innerHTML = kp('Costo estándar unitario', money(k.std_unit), '', 'main') + kp('Costo real unitario', money(k.real_unit), '', 'main') + kp('Diferencia porcentual', nf1.format(k.dif_pct) + ' %', vc(k.dif_pct)) +
      kp('Variación de materiales', money(k.v_mat), vc(k.v_mat)) + kp('Variación de MOD', money(k.v_mod), vc(k.v_mod)) + kp('Variación CIF', money(k.v_cif), vc(k.v_cif)) +
      kp('Costo total de producción', money(k.costo_total)) + kp('Ventas de lo terminado', money(k.ventas)) + kp('Margen', `${money(k.margen)} (${nf1.format(k.margen_pct)} %)`, k.margen < 0 ? 'des' : 'fav');
    bars($('#c1'), d.productos.map(p => p.nombre), [{ c: '#8FA39A', d: d.productos.map(p => p.std_unit) }, { c: '#F2B632', d: d.productos.map(p => p.real_unit) }]);
    bars($('#c2'), d.variaciones.map(x => x.n), [{ d: d.variaciones.map(x => x.v), colors: d.variaciones.map(x => x.v > 0 ? '#C2410C' : '#2E7D4F') }]);
    const cm = d.composicion, parts = [['Materiales', cm.mp, '#F2B632'], ['Mano de obra', cm.mod, '#2E7D4F'], ['CIF', cm.cif, '#6B7A8F']];
    donut($('#c3'), parts); $('#lg3').innerHTML = parts.map(p => `<span><i style="background:${p[2]}"></i>${p[0]} ${money(p[1])}</span>`).join('');
  };
  $('#rPer').onchange = $('#rProd').onchange = load; load();
}
function setup(cv) { const r = devicePixelRatio || 1, w = cv.clientWidth, h = cv.clientHeight; cv.width = w * r; cv.height = h * r; const g = cv.getContext('2d'); g.scale(r, r); g.clearRect(0, 0, w, h); g.font = '12px Segoe UI, Arial'; return [g, w, h]; }
function bars(cv, labels, series) {
  const [g, w, h] = setup(cv); if (!labels.length) { g.fillStyle = '#5E6860'; g.fillText('Sin datos', 10, 20); return; }
  const all = series.flatMap(s => s.d), mx = Math.max(0, ...all), mn = Math.min(0, ...all), pad = { l: 56, r: 8, t: 10, b: 42 }, ph = h - pad.t - pad.b, rng = (mx - mn) || 1;
  const y = v => pad.t + ph * (mx - v) / rng;
  g.strokeStyle = '#E1E5DE'; g.fillStyle = '#5E6860'; g.textAlign = 'right';
  for (let i = 0; i <= 4; i++) { const v = mn + rng * i / 4, yy = y(v); g.beginPath(); g.moveTo(pad.l, yy); g.lineTo(w - pad.r, yy); g.stroke(); g.fillText(nf0.format(v), pad.l - 6, yy + 4); }
  const gw = (w - pad.l - pad.r) / labels.length, bw = Math.min(46, gw * .7 / series.length);
  labels.forEach((lb, i) => {
    series.forEach((s, j) => { const x = pad.l + gw * i + (gw - bw * series.length) / 2 + bw * j, v = s.d[i]; g.fillStyle = s.colors ? s.colors[i] : s.c; g.fillRect(x, Math.min(y(v), y(0)), bw - 2, Math.abs(y(v) - y(0))); });
    g.fillStyle = '#1B1F1C'; g.textAlign = 'center'; const t = lb.length > 14 ? lb.slice(0, 13) + '…' : lb; g.fillText(t, pad.l + gw * i + gw / 2, h - 22);
  });
}
function donut(cv, parts) {
  const [g, w, h] = setup(cv), tot = parts.reduce((a, p) => a + p[1], 0); if (!tot) { g.fillStyle = '#5E6860'; g.fillText('Sin datos', 10, 20); return; }
  const cx = w / 2, cy = h / 2, R = Math.min(w, h) / 2 - 12; let a = -Math.PI / 2;
  parts.forEach(p => { const s = p[1] / tot * Math.PI * 2; g.beginPath(); g.moveTo(cx, cy); g.arc(cx, cy, R, a, a + s); g.fillStyle = p[2]; g.fill(); a += s; });
  g.beginPath(); g.arc(cx, cy, R * .58, 0, 7); g.fillStyle = '#fff'; g.fill(); g.fillStyle = '#1B1F1C'; g.textAlign = 'center'; g.font = '600 14px Segoe UI, Arial'; g.fillText(money(tot), cx, cy + 5);
}
window.addEventListener('resize', () => { if (S.cur === 'dash' && S.user) dashboard(); });
if (S.token) start();

/* ---------- copias de seguridad (solo administrador) ---------- */
async function descargarRespaldo() {
  const b = await api('respaldo', { raw: true });
  const a = document.createElement('a'); a.href = URL.createObjectURL(b);
  a.download = `respaldo-costos-${new Date().toISOString().slice(0, 10)}.json`; a.click(); URL.revokeObjectURL(a.href);
}
function backupView() {
  $('#view').innerHTML = `<div class="head"><h2>Copias de seguridad</h2></div>
    <div class="card"><h3>Descargar copia ahora</h3>
      <p>Guarda en su computador todos los datos (empresas, productos, órdenes, usuarios, etc.) en un archivo <b>.json</b>. Hágalo de vez en cuando y siempre antes de una presentación.</p>
      <button class="btn primary" id="bkDown">Descargar copia ahora</button></div>
    <div class="card" style="margin-top:14px"><h3>Restaurar desde un archivo</h3>
      <p>Reemplaza <b>todos</b> los datos actuales por los del archivo. Antes de reemplazar, el sistema descarga automáticamente una copia de lo que hay ahora. Sirve también para llevar los datos del sistema de su computador (SQLite) al sistema en línea, y al revés. Tamaño máximo: 4&nbsp;MB.</p>
      <input type="file" id="bkFile" accept=".json,application/json"> <button class="btn danger" id="bkUp">Restaurar archivo</button></div>`;
  $('#bkDown').onclick = async () => { try { await descargarRespaldo(); toast('Copia descargada'); } catch (e) { toast(e.error || 'No se pudo descargar'); } };
  $('#bkUp').onclick = async () => {
    const f = $('#bkFile').files[0]; if (!f) return toast('Elija primero un archivo .json');
    if (f.size > 4000000) return toast('El archivo supera el máximo de 4 MB.');
    let datos; try { datos = JSON.parse(await f.text()); } catch (e) { return toast('El archivo no es una copia válida.'); }
    const w = prompt('Se reemplazarán TODOS los datos actuales. Escriba RESTAURAR para confirmar:');
    if (!w) return;
    try {
      await descargarRespaldo();
      const r = await api('restaurar', { method: 'POST', body: { datos, confirmar: w } });
      toast(`Copia restaurada (${r.filas} registros). Inicie sesión de nuevo.`); setTimeout(() => logout(true), 1200);
    } catch (e) { toast(e.error || 'No se pudo restaurar'); }
  };
}
