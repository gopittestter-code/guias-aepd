/* ============================================================
   FAQ Hub — Lógica de la aplicación (frontend estático)
   Lee data/faq_data.json, busca con Fuse.js y renderiza
   ============================================================ */

let DATA = null;
let FUSE = null;
const state = { src: 'all', cat: 'all', query: '' };

const $ = (id) => document.getElementById(id);

/* ---------- Utilidades ---------- */
function norm(str) {
  return String(str).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}
function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function highlight(str, q) {
  const safe = esc(str);
  if (!q) return safe;
  const nHay = norm(str), nQ = norm(q);
  if (nQ.length < 2) return safe;
  let out = '', last = 0, idx = nHay.indexOf(nQ);
  while (idx !== -1) {
    out += esc(str.slice(last, idx)) + '<mark>' + esc(str.slice(idx, idx + q.length)) + '</mark>';
    last = idx + q.length;
    idx = nHay.indexOf(nQ, last);
  }
  return out + esc(str.slice(last));
}

/* ---------- Carga de datos ---------- */
async function loadData() {
  try {
    const res = await fetch('data/faq_data.json');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    DATA = await res.json();
    initFuse();
    renderStats();
    buildFilters();
    render();
    $('loading').style.display = 'none';
  } catch (err) {
    $('loading').innerHTML =
      '⚠️ Error al cargar los datos.<br>Revisa que <code>data/faq_data.json</code> exista y sea válido.<br><br>' +
      '<small>' + esc(err.message) + '</small>';
    console.error(err);
  }
}

function initFuse() {
  FUSE = new Fuse(DATA.faqs, {
    keys: [
      { name: 'question', weight: 0.5 },
      { name: 'answer',   weight: 0.3 },
      { name: 'tags',     weight: 0.2 }
    ],
    threshold: 0.35,
    ignoreLocation: true,
    includeScore: true,
    minMatchCharLength: 2
  });
}

/* ---------- Estadísticas ---------- */
function renderStats() {
  $('statTotal').textContent = DATA.meta.total_faqs;
  $('statSources').textContent = DATA.sources.length;
  $('statCats').textContent = DATA.categories.length;
  const d = new Date(DATA.meta.extracted_date);
  $('statUpdated').textContent = d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
  $('footDate').textContent = 'Actualizado el ' + d.toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });
}

/* ---------- Filtros ---------- */
function buildFilters() {
  const srcWrap = $('sourceFilters');
  srcWrap.innerHTML = '';
  srcWrap.appendChild(mkSrcBtn('all', 'Todas las fuentes', DATA.faqs.length));
  DATA.sources.forEach(s => {
    const n = DATA.faqs.filter(f => f.source === s.id).length;
    if (n) srcWrap.appendChild(mkSrcBtn(s.id, s.name, n));
  });

  const catWrap = $('catFilters');
  catWrap.innerHTML = '';
  const allCat = document.createElement('button');
  allCat.className = 'cat-btn active';
  allCat.dataset.cat = 'all';
  allCat.innerHTML = `🗂️ Todas las categorías`;
  allCat.onclick = () => { state.cat = 'all'; render(); };
  catWrap.appendChild(allCat);
  DATA.categories.forEach(c => {
    const n = DATA.faqs.filter(f => f.category === c.id).length;
    if (!n) return;
    const b = document.createElement('button');
    b.className = 'cat-btn';
    b.dataset.cat = c.id;
    b.innerHTML = `${c.icon || '📌'} ${esc(c.name)} <span class="cnt">${n}</span>`;
    b.onclick = () => {
      state.cat = (state.cat === c.id ? 'all' : c.id);
      render();
      closeDrawer();
    };
    catWrap.appendChild(b);
  });
}

function mkSrcBtn(id, name, count) {
  const b = document.createElement('button');
  b.className = 'src-btn' + (id === 'all' ? ' active' : '');
  b.dataset.src = id;
  b.innerHTML = `<span class="dot"></span> ${esc(name)} <span class="cnt">${count}</span>`;
  b.onclick = () => {
    state.src = id;
    if (state.cat !== 'all' && id !== 'all') {
      const anyMatch = DATA.faqs.some(f => f.source === id && f.category === state.cat);
      if (!anyMatch) state.cat = 'all';
    }
    render();
    closeDrawer();
  };
  return b;
}

/* ---------- Render ---------- */
function render() {
  document.querySelectorAll('.src-btn').forEach(b => b.classList.toggle('active', b.dataset.src === state.src));
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.toggle('active', b.dataset.cat === state.cat));

  const q = state.query.trim();
  let results = DATA.faqs;

  if (q.length >= 2 && FUSE) {
    results = FUSE.search(q).map(r => r.item);
  }
  if (state.src !== 'all') results = results.filter(f => f.source === state.src);
  if (state.cat !== 'all') results = results.filter(f => f.category === state.cat);

  const byCat = new Map();
  results.forEach(f => {
    if (!byCat.has(f.category)) byCat.set(f.category, []);
    byCat.get(f.category).push(f);
  });

  let shown = 0, html = '';
  byCat.forEach((items, catId) => {
    const cat = DATA.categories.find(c => c.id === catId) || { name: catId, icon: '📌' };
    shown += items.length;
    html += `<section class="cat-section">
      <div class="cat-head">
        <div class="ico">${cat.icon || '📌'}</div>
        <h2>${highlight(cat.name, q)}</h2>
        <span class="src-tag">${items.length} pregunta${items.length !== 1 ? 's' : ''}</span>
      </div>`;
    items.forEach(f => {
      const src = DATA.sources.find(s => s.id === f.source) || { name: f.source, url: '#' };
      html += `<article class="faq-item ${f.source}">
        <button class="faq-q" aria-expanded="false" onclick="toggleFaq(this)">
          <span>${highlight(f.question, q)}</span>
          <span class="chev">⌄</span>
        </button>
        <div class="faq-a"><div class="faq-a-in"><div class="faq-a-body">
          <p>${highlight(f.answer, q)}</p>
          <div class="src-line">
            <span class="src-tag">${esc(src.name)}</span>
            <a href="${esc(f.url_original || src.url)}" target="_blank" rel="noopener">Ver fuente original ↗</a>
          </div>
        </div></div></div>
      </article>`;
    });
    html += `</section>`;
  });

  $('content').innerHTML = html;
  $('emptyState').classList.toggle('show', shown === 0);
  $('resultCount').innerHTML =
    `Mostrando <b>${shown}</b> de <b>${DATA.meta.total_faqs}</b> preguntas` +
    (q ? ` para «<b>${esc(q)}</b>»` : '');
}

function toggleFaq(btn) {
  const item = btn.closest('.faq-item');
  const open = item.classList.toggle('open');
  btn.setAttribute('aria-expanded', open);
}

/* ---------- Drawer móvil ---------- */
function closeDrawer() { $('sidebar').classList.remove('open'); }
$('filtersToggle').onclick = () => $('sidebar').classList.toggle('open');

/* ---------- Eventos ---------- */
let searchTimer = null;
$('searchInput').addEventListener('input', (e) => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.query = e.target.value;
    $('clearSearch').classList.toggle('show', !!e.target.value);
    render();
  }, 120);
});
$('clearSearch').onclick = () => {
  $('searchInput').value = ''; state.query = '';
  $('clearSearch').classList.remove('show'); render();
  $('searchInput').focus();
};
$('expandAll').onclick = () => document.querySelectorAll('.faq-item').forEach(i => i.classList.add('open'));
$('collapseAll').onclick = () => document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
$('resetFilters').onclick = () => {
  state.src = 'all'; state.cat = 'all'; state.query = '';
  $('searchInput').value = ''; $('clearSearch').classList.remove('show');
  render(); buildFilters();
};

document.addEventListener('keydown', (ev) => {
  if (ev.key === '/' && document.activeElement !== $('searchInput')) {
    ev.preventDefault(); $('searchInput').focus();
  }
  if (ev.key === 'Escape' && document.activeElement === $('searchInput')) {
    $('searchInput').value = ''; state.query = '';
    $('clearSearch').classList.remove('show'); render();
    $('searchInput').blur();
  }
});

window.addEventListener('scroll', () => {
  $('toTop').classList.toggle('show', window.scrollY > 500);
}, { passive: true });
$('toTop').onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });

/* ---------- Arranque ---------- */
loadData();
