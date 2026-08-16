/* ============================================================
   FAQ Hub — Lógica completa (pestañas FAQs / Guías)
   Lee data/faq_data.json, busca con Fuse.js y renderiza
   ============================================================ */

let DATA = null;
let FUSE_FAQS = null;
let FUSE_GUIDES = null;
const state = { tab: 'faqs', src: 'all', cat: 'all', query: '' };

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
    DATA.guides = DATA.guides || [];
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
  FUSE_FAQS = new Fuse(DATA.faqs, {
    keys: [
      { name: 'question', weight: 0.5 },
      { name: 'answer',   weight: 0.3 },
      { name: 'tags',     weight: 0.2 }
    ],
    threshold: 0.35, ignoreLocation: true, includeScore: true, minMatchCharLength: 2
  });
  FUSE_GUIDES = new Fuse(DATA.guides, {
    keys: [
      { name: 'title',   weight: 0.5 },
      { name: 'summary', weight: 0.3 },
      { name: 'topic',   weight: 0.2 },
      { name: 'tags',    weight: 0.1 }
    ],
    threshold: 0.35, ignoreLocation: true, includeScore: true, minMatchCharLength: 2
  });
}

/* ---------- Estadísticas ---------- */
function renderStats() {
  $('statFaqs').textContent = DATA.faqs.length;
  $('statGuides').textContent = DATA.guides.length;
  $('statSources').textContent = DATA.sources.length;
  const d = new Date(DATA.meta.extracted_date);
  $('statUpdated').textContent = d.toLocaleDateString('es-ES', { day: 'numeric', month: 'short' });
  $('footDate').textContent = 'Actualizado el ' + d.toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });
}

function currentItems() {
  return state.tab === 'faqs' ? DATA.faqs : DATA.guides;
}

/* ---------- Filtros ---------- */
function buildFilters() {
  const srcWrap = $('sourceFilters');
  srcWrap.innerHTML = '';
  const items = currentItems();

  srcWrap.appendChild(mkSrcBtn('all', 'Todas las fuentes', items.length));

  const sourcesInTab = [...new Set(items.map(i => i.source))];
  DATA.sources.filter(s => sourcesInTab.includes(s.id)).forEach(s => {
    const n = items.filter(i => i.source === s.id).length;
    srcWrap.appendChild(mkSrcBtn(s.id, s.name, n));
  });

  const catWrap = $('catFilters');
  catWrap.innerHTML = '';
  const allCat = document.createElement('button');
  allCat.className = 'cat-btn active';
  allCat.dataset.cat = 'all';
  allCat.innerHTML = '🗂️ Todas las categorías';
  allCat.onclick = () => { state.cat = 'all'; render(); };
  catWrap.appendChild(allCat);

  const catsInTab = [...new Set(items.map(i => i.category))];
  DATA.categories.filter(c => catsInTab.includes(c.id)).forEach(c => {
    const n = items.filter(i => i.category === c.id).length;
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
      const items = currentItems();
      if (!items.some(i => i.source === id && i.category === state.cat)) state.cat = 'all';
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
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === state.tab));

  $('faqActions').style.display = state.tab === 'faqs' ? '' : 'none';

  const q = state.query.trim();
  let results;

  if (state.tab === 'faqs') {
    results = (q.length >= 2 && FUSE_FAQS) ? FUSE_FAQS.search(q).map(r => r.item) : [...DATA.faqs];
  } else {
    results = (q.length >= 2 && FUSE_GUIDES) ? FUSE_GUIDES.search(q).map(r => r.item) : [...DATA.guides];
  }

  if (state.src !== 'all') results = results.filter(i => i.source === state.src);
  if (state.cat !== 'all') results = results.filter(i => i.category === state.cat);

  const byCat = new Map();
  results.forEach(i => {
    if (!byCat.has(i.category)) byCat.set(i.category, []);
    byCat.get(i.category).push(i);
  });

  let shown = 0, html = '';
  byCat.forEach((items, catId) => {
    const cat = DATA.categories.find(c => c.id === catId) || { name: catId, icon: '📌' };
    shown += items.length;
    html += `<section class="cat-section">
      <div class="cat-head">
        <div class="ico">${cat.icon || '📌'}</div>
        <h2>${highlight(cat.name, q)}</h2>
        <span class="src-tag">${items.length} ${state.tab === 'faqs' ? 'pregunta' : 'guía'}${items.length !== 1 ? 's' : ''}</span>
      </div>`;
    html += state.tab === 'faqs'
      ? items.map(renderFaq).join('')
      : items.map(renderGuide).join('');
    html += `</section>`;
  });

  $('content').innerHTML = html;
  $('emptyState').classList.toggle('show', shown === 0);
  const label = state.tab === 'faqs' ? 'preguntas' : 'guías';
  $('resultCount').innerHTML =
    `Mostrando <b>${shown}</b> ${label}` +
    (q ? ` para «<b>${esc(q)}</b>»` : '');
}

function renderFaq(f) {
  const src = DATA.sources.find(s => s.id === f.source) || { name: f.source, url: '#' };
  return `<article class="faq-item ${f.source}">
    <button class="faq-q" aria-expanded="false" onclick="toggleFaq(this)">
      <span>${highlight(f.question, state.query)}</span>
      <span class="chev">⌄</span>
    </button>
    <div class="faq-a"><div class="faq-a-in"><div class="faq-a-body">
      <p>${highlight(f.answer || '', state.query)}</p>
      <div class="src-line">
        <span class="src-tag">${esc(src.name)}</span>
        <a href="${esc(f.url_original || src.url)}" target="_blank" rel="noopener">Ver fuente original ↗</a>
      </div>
    </div></div></div>
  </article>`;
}

function renderGuide(g) {
  const src = DATA.sources.find(s => s.id === g.source) || { name: g.source, url: '#' };
  const date = g.published_date
    ? new Date(g.published_date).toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' })
    : '';
  const topic = DATA.categories.find(c => c.id === g.category)?.name || g.topic || '';
  const url = g.url || g.url_original || '#';
  const isPdf = /\.pdf(\?|$)/i.test(url);
  const btn = isPdf ? 'Descargar PDF' : 'Ver guía';
  return `<article class="guide-item ${g.source}">
    <div class="guide-top">
      <div class="guide-icon">${isPdf ? '📄' : '📘'}</div>
      <div class="guide-body">
        <span class="guide-topic">${highlight(topic, state.query)}</span>
        <h3 class="guide-title">${highlight(g.title, state.query)}</h3>
        ${g.summary ? `<p class="guide-summary">${highlight(g.summary, state.query)}</p>` : ''}
        <div class="guide-meta">
          <span class="guide-date">${date}</span>
          <span class="src-tag">${esc(src.name)}</span>
          <a class="guide-link" href="${esc(url)}" target="_blank" rel="noopener">${btn}</a>
        </div>
      </div>
    </div>
  </article>`;
}

function toggleFaq(btn) {
  const item = btn.closest('.faq-item');
  const open = item.classList.toggle('open');
  btn.setAttribute('aria-expanded', open);
}

/* ---------- Drawer móvil ---------- */
function closeDrawer() { $('sidebar').classList.remove('open'); }
$('filtersToggle').onclick = () => $('sidebar').classList.toggle('open');

/* ---------- Pestañas ---------- */
document.querySelectorAll('.tab-btn').forEach(b => {
  b.onclick = () => {
    state.tab = b.dataset.tab;
    state.src = 'all';
    state.cat = 'all';
    $('searchInput').value = '';
    state.query = '';
    $('clearSearch').classList.remove('show');
    buildFilters();
    render();
  };
});

/* ---------- Búsqueda ---------- */
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
  $('searchInput').value = '';
  state.query = '';
  $('clearSearch').classList.remove('show');
  render();
  $('searchInput').focus();
};
$('expandAll').onclick = () => document.querySelectorAll('.faq-item').forEach(i => i.classList.add('open'));
$('collapseAll').onclick = () => document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('open'));
$('resetFilters').onclick = () => {
  state.src = 'all';
  state.cat = 'all';
  state.query = '';
  $('searchInput').value = '';
  $('clearSearch').classList.remove('show');
  render();
  buildFilters();
};

/* ---------- Teclado ---------- */
document.addEventListener('keydown', (ev) => {
  if (ev.key === '/' && document.activeElement !== $('searchInput')) {
    ev.preventDefault();
    $('searchInput').focus();
  }
  if (ev.key === 'Escape' && document.activeElement === $('searchInput')) {
    $('searchInput').value = '';
    state.query = '';
    $('clearSearch').classList.remove('show');
    render();
    $('searchInput').blur();
  }
});

/* ---------- Volver arriba ---------- */
window.addEventListener('scroll', () => {
  $('toTop').classList.toggle('show', window.scrollY > 500);
}, { passive: true });
$('toTop').onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });

/* ---------- Arranque ---------- */
loadData();
