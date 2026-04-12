/* ═══════════════════════════════════════════
   OnePulse — script.js
   ═══════════════════════════════════════════ */
fetch("https://onepulse.onrender.com/api/posts")
  .then(res => res.json())
  .then(data => {
    console.log("Backend data:", data);
  })
  .catch(err => {
    console.error("Error:", err);
  });
// ── CONFIG ──
const API = 'http://localhost:5000/api';

// ── STATE ──
let currentPlatform      = 'youtube';
let selectedScheduleTime = null;
let aiHashtags           = [];
let uploadedFile         = null;
let allPosts             = [];   // cached for search/filter

// ══════════════════════════════════════════════
// UTILITIES
// ══════════════════════════════════════════════

function showLoading(msg = 'Processing…') {
  document.getElementById('loading').classList.add('show');
  document.getElementById('loading-msg').textContent = msg;
}

function hideLoading() {
  document.getElementById('loading').classList.remove('show');
}

function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.innerHTML = (type === 'success' ? '✅ ' : '❌ ') + msg;
  t.className = `toast ${type} show`;
  setTimeout(() => t.classList.remove('show'), 3000);
}

async function apiFetch(path, opts = {}) {
  const res = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || 'Request failed');
  }
  return res.json();
}

// ══════════════════════════════════════════════
// RESPONSIVE — SIDEBAR & NAV
// ══════════════════════════════════════════════

function toggleMobileSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (!sidebar) return;
  sidebar.style.display = sidebar.style.display === 'flex' ? 'none' : 'flex';
}

function setNavActive(el) {
  document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
  el.classList.add('active');
}

// ══════════════════════════════════════════════
// PLATFORM SWITCH
// ══════════════════════════════════════════════

function switchPlatform(platform) {
  currentPlatform = platform;

  // Tab pills
  document.getElementById('tab-yt').className = 'tab' + (platform === 'youtube' ? ' active-yt' : '');
  document.getElementById('tab-ig').className = 'tab' + (platform === 'instagram' ? ' active-ig' : '');

  // Sidebar platform buttons
  const syt = document.getElementById('sbar-yt');
  const sig = document.getElementById('sbar-ig');
  if (syt) syt.classList.toggle('active', platform === 'youtube');
  if (sig) sig.classList.toggle('active', platform === 'instagram');

  // Header title
  document.getElementById('posts-heading').textContent  = platform === 'youtube' ? 'YouTube Posts' : 'Instagram Posts';
  document.getElementById('header-title').textContent   = platform === 'youtube' ? 'YouTube Dashboard' : 'Instagram Dashboard';

  loadPosts();
  loadStats();
}

// ══════════════════════════════════════════════
// STATS
// ══════════════════════════════════════════════

async function loadStats() {
  try {
    const s = await apiFetch(`/stats?platform=${currentPlatform}`);
    document.getElementById('stat-total').textContent     = s.total;
    document.getElementById('stat-scheduled').textContent = s.scheduled;
    document.getElementById('stat-posted').textContent    = s.posted;
    document.getElementById('stat-failed').textContent    = s.failed || 0;

    // Update sidebar badge
    const badge = document.getElementById('nav-scheduled-count');
    if (badge) badge.textContent = s.scheduled;
  } catch (e) {
    console.warn('Stats error:', e.message);
    setDemoStats();
  }
}

function setDemoStats() {
  document.getElementById('stat-total').textContent     = allPosts.length;
  document.getElementById('stat-scheduled').textContent = allPosts.filter(p => p.status === 'scheduled').length;
  document.getElementById('stat-posted').textContent    = allPosts.filter(p => p.status === 'posted').length;
  document.getElementById('stat-failed').textContent    = allPosts.filter(p => p.status === 'failed').length;
  const badge = document.getElementById('nav-scheduled-count');
  if (badge) badge.textContent = allPosts.filter(p => p.status === 'scheduled').length;
}

// ══════════════════════════════════════════════
// POSTS
// ══════════════════════════════════════════════

async function loadPosts() {
  try {
    const posts = await apiFetch(`/posts?platform=${currentPlatform}`);
    allPosts = posts;
    renderPosts(posts);
    renderUpcoming(posts);
    renderChart();
  } catch (e) {
    console.warn('Backend not running — using demo data:', e.message);
    loadDemoPosts();
  }
}

function loadDemoPosts() {
  const now = new Date();
  const future = (d) => { const x=new Date(now); x.setDate(x.getDate()+d); x.setHours(18,0,0,0); return x.toISOString(); };
  const past   = (d) => { const x=new Date(now); x.setDate(x.getDate()-d); x.setHours(14,0,0,0); return x.toISOString(); };

  const demo = {
    youtube: [
      { id:1, platform:'youtube', title:"Let's make this crochet charm 🌸", description:"Making this beautiful charm...", hashtags:"#crochet #handmade", scheduled_time:future(1), status:'scheduled', image_url:'https://images.unsplash.com/photo-1605518216938-7c31b7b14ad0?w=400' },
      { id:2, platform:'youtube', title:"My Morning Routine 2026 ☀️", description:"How I stay productive every day", hashtags:"#lifestyle #morning", scheduled_time:future(2), status:'scheduled', image_url:'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=400' },
      { id:3, platform:'youtube', title:"10 AI Tools You Must Try", description:"These tools changed my workflow", hashtags:"#tech #ai", scheduled_time:past(1), status:'posted', image_url:'https://images.unsplash.com/photo-1677442135703-1787eea5ce01?w=400' },
      { id:4, platform:'youtube', title:"Home Studio Setup Tour 🎙️", description:"Full breakdown of my studio gear", hashtags:"#studio #creator", scheduled_time:past(3), status:'posted', image_url:'https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?w=400' },
    ],
    instagram: [
      { id:5, platform:'instagram', title:"Golden Hour Vibes 🌅", description:"Catching the perfect light", hashtags:"#photography #golden", scheduled_time:future(1), status:'scheduled', image_url:'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400' },
      { id:6, platform:'instagram', title:"Avocado Toast Recipe 🥑", description:"The easiest breakfast ever", hashtags:"#food #recipe", scheduled_time:past(2), status:'posted', image_url:'https://images.unsplash.com/photo-1541519227354-08fa5d50c820?w=400' },
      { id:7, platform:'instagram', title:"Minimal Desk Setup ✨", description:"Clean workspace = clean mind", hashtags:"#desk #aesthetic", scheduled_time:future(3), status:'scheduled', image_url:'https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=400' },
    ]
  };

  allPosts = demo[currentPlatform] || [];
  renderPosts(allPosts);
  renderUpcoming(allPosts);
  renderChart();
  setDemoStats();
}

function renderPosts(posts) {
  const el = document.getElementById('posts-list');
  if (!posts || !posts.length) {
    el.innerHTML = `
      <div class="empty">
        <div class="empty-icon">📭</div>
        <h3>No posts yet</h3>
        <p>Schedule your first post to get started!</p>
      </div>`;
    return;
  }

  el.innerHTML = posts.map((p, i) => {
    const isYT    = p.platform === 'youtube';
    const dt      = p.scheduled_time ? new Date(p.scheduled_time) : null;
    const timeStr = dt ? dt.toLocaleString('en-US', { month:'short', day:'numeric', year:'numeric', hour:'2-digit', minute:'2-digit' }) : '—';
    const thumb   = p.image_url
      ? `<img src="${p.image_url}" onerror="this.parentElement.innerHTML='${isYT?'▶':'📸'}'" alt="thumb"/>`
      : (isYT ? '▶' : '📸');

    return `
    <div class="post-card ${isYT ? 'yt' : 'ig'}" style="animation-delay:${i * 0.05}s">
      <div class="post-thumb">${thumb}</div>
      <div class="post-body">
        <div class="post-platform-badge badge-${isYT ? 'yt' : 'ig'}">${isYT ? '▶ YouTube' : '◎ Instagram'}</div>
        <div class="post-title">${p.title}</div>
        <div class="post-desc">${p.description || p.hashtags || '—'}</div>
        <div class="post-footer">
          <div class="post-time">🕐 ${timeStr}</div>
          <div class="post-status status-${p.status}">${p.status}</div>
        </div>
      </div>
      <div class="post-actions">
        ${p.status === 'scheduled' ? `<button class="post-action-btn publish" onclick="publishNow(${p.id})">▶ Post Now</button>` : ''}
        <button class="post-action-btn delete" onclick="deletePost(${p.id})">🗑 Delete</button>
      </div>
    </div>`;
  }).join('');
}

// ── SEARCH / FILTER ──
function filterPosts(query) {
  if (!query.trim()) { renderPosts(allPosts); return; }
  const q = query.toLowerCase();
  renderPosts(allPosts.filter(p =>
    p.title.toLowerCase().includes(q) ||
    (p.description || '').toLowerCase().includes(q) ||
    (p.hashtags || '').toLowerCase().includes(q)
  ));
}

// ── UPCOMING WIDGET ──
function renderUpcoming(posts) {
  const el = document.getElementById('upcoming-list');
  if (!el) return;
  const upcoming = posts.filter(p => p.status === 'scheduled').slice(0, 4);
  if (!upcoming.length) {
    el.innerHTML = '<div style="font-size:12px;color:var(--muted);text-align:center;padding:12px 0">No upcoming posts</div>';
    return;
  }
  el.innerHTML = upcoming.map(p => {
    const isYT = p.platform === 'youtube';
    const dt   = new Date(p.scheduled_time);
    const time = dt.toLocaleDateString('en-US', { month:'short', day:'numeric' }) + ' · ' + dt.toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit' });
    return `
    <div class="quick-sched-item">
      <div class="quick-sched-dot" style="background:${isYT ? 'var(--yt)' : 'var(--ig)'}"></div>
      <div class="quick-sched-info">
        <div class="quick-sched-title">${p.title}</div>
        <div class="quick-sched-time">🕐 ${time}</div>
      </div>
      <div class="quick-sched-status status-scheduled">soon</div>
    </div>`;
  }).join('');
}

// ── ACTIVITY CHART ──
function renderChart() {
  const barsEl   = document.getElementById('chart-bars');
  const labelsEl = document.getElementById('chart-labels');
  if (!barsEl) return;

  const days  = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  const ytH   = [40,70,55,90,60,80,95];
  const igH   = [55,45,80,60,70,90,50];
  const maxH  = 100;

  barsEl.innerHTML = days.map((d,i) => `
    <div class="chart-bar yt-bar" style="height:${(ytH[i]/maxH)*100}%" title="YouTube: ${ytH[i]}%"></div>
    <div class="chart-bar ig-bar" style="height:${(igH[i]/maxH)*70}%" title="Instagram: ${igH[i]}%"></div>
  `).join('');

  labelsEl.innerHTML = days.map(d => `<div class="chart-label">${d}</div>`).join('');
}

// ══════════════════════════════════════════════
// PUBLISH / DELETE
// ══════════════════════════════════════════════

async function publishNow(postId) {
  if (!confirm('Publish this post immediately?')) return;
  showLoading('Publishing…');
  try {
    const r = await apiFetch(`/posts/${postId}/publish`, { method: 'POST' });
    showToast(r.success ? 'Posted successfully! 🎉' : 'Publish failed.', r.success ? 'success' : 'error');
    loadPosts();
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    hideLoading();
  }
}

async function deletePost(postId) {
  if (!confirm('Delete this post?')) return;
  try {
    await apiFetch(`/posts/${postId}`, { method: 'DELETE' });
    showToast('Post deleted');
    loadPosts();
  } catch (e) {
    showToast(e.message, 'error');
  }
}

// ══════════════════════════════════════════════
// MODAL
// ══════════════════════════════════════════════

function openModal() {
  document.getElementById('overlay').classList.add('open');
  selectPlatform(currentPlatform);
}

function closeModal() {
  document.getElementById('overlay').classList.remove('open');
  document.getElementById('ai-box').classList.remove('visible');
  ['f-title','f-desc','f-image','f-caption','f-hashtags','f-time'].forEach(id => {
    document.getElementById(id).value = '';
  });
  selectedScheduleTime = null;
  aiHashtags = [];
  removeFile({ stopPropagation: () => {} });
}

function handleOverlayClick(e) {
  if (e.target.id === 'overlay') closeModal();
}

// Esc key closes modal
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

function selectPlatform(platform) {
  document.getElementById('opt-yt').className = 'platform-opt' + (platform === 'youtube' ? ' sel-yt' : '');
  document.getElementById('opt-ig').className = 'platform-opt' + (platform === 'instagram' ? ' sel-ig' : '');
}

function getModalPlatform() {
  return document.getElementById('opt-yt').classList.contains('sel-yt') ? 'youtube' : 'instagram';
}

// ══════════════════════════════════════════════
// DRAG & DROP
// ══════════════════════════════════════════════

function handleDragOver(e) {
  e.preventDefault(); e.stopPropagation();
  document.getElementById('drop-zone').classList.add('drag-over');
}

function handleDragLeave(e) {
  e.preventDefault();
  document.getElementById('drop-zone').classList.remove('drag-over');
}

function handleDrop(e) {
  e.preventDefault(); e.stopPropagation();
  document.getElementById('drop-zone').classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) processFile(file);
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) processFile(file);
}

function formatBytes(bytes) {
  if (bytes < 1024)    return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
}

function getFileIcon(type) {
  if (type.startsWith('image/')) return { icon: '🖼', color: 'rgba(91,127,255,0.15)' };
  if (type.startsWith('video/')) return { icon: '🎬', color: 'rgba(255,59,48,0.15)' };
  if (type.startsWith('audio/')) return { icon: '🎵', color: 'rgba(48,209,88,0.15)' };
  if (type.includes('pdf'))      return { icon: '📄', color: 'rgba(255,159,10,0.15)' };
  return { icon: '📎', color: 'rgba(255,255,255,0.08)' };
}

function processFile(file) {
  uploadedFile = file;
  const zone    = document.getElementById('drop-zone');
  const idle    = document.getElementById('drop-idle');
  const preview = document.getElementById('drop-preview');

  zone.classList.add('has-file');
  idle.style.display    = 'none';
  preview.style.display = 'block';

  const size = formatBytes(file.size);

  if (file.type.startsWith('image/')) {
    const url = URL.createObjectURL(file);
    preview.innerHTML = `
      <img src="${url}" alt="${file.name}"/>
      <div class="drop-preview-meta">
        <span class="drop-preview-name">🖼 ${file.name}</span>
        <span class="drop-preview-size">${size}</span>
      </div>
      <button class="drop-remove" onclick="removeFile(event)">✕</button>`;
    document.getElementById('f-image').value = url;

  } else if (file.type.startsWith('video/')) {
    const url = URL.createObjectURL(file);
    preview.innerHTML = `
      <video src="${url}" controls muted playsinline></video>
      <div class="drop-preview-meta">
        <span class="drop-preview-name">🎬 ${file.name}</span>
        <span class="drop-preview-size">${size}</span>
      </div>
      <button class="drop-remove" onclick="removeFile(event)">✕</button>`;

  } else {
    const { icon, color } = getFileIcon(file.type);
    const ext = file.name.split('.').pop().toUpperCase();
    preview.innerHTML = `
      <div class="drop-file-card">
        <div class="drop-file-icon" style="background:${color}">${icon}</div>
        <div class="drop-file-info">
          <div class="drop-file-name">${file.name}</div>
          <div class="drop-file-type">${ext} · ${file.type || 'unknown type'}</div>
          <div class="drop-file-size">✅ ${size} ready to upload</div>
        </div>
        <button class="drop-remove" style="position:relative;top:auto;right:auto;flex-shrink:0" onclick="removeFile(event)">✕</button>
      </div>`;
  }
}

function removeFile(e) {
  e.stopPropagation();
  uploadedFile = null;
  const zone    = document.getElementById('drop-zone');
  const idle    = document.getElementById('drop-idle');
  const preview = document.getElementById('drop-preview');
  zone.classList.remove('has-file');
  idle.style.display    = 'block';
  preview.style.display = 'none';
  preview.innerHTML     = '';
  document.getElementById('f-file').value  = '';
  document.getElementById('f-image').value = '';
}

// ══════════════════════════════════════════════
// AI RECOMMENDATIONS
// ══════════════════════════════════════════════

async function getAIRecommendations() {
  const platform = getModalPlatform();
  const niche    = document.getElementById('f-niche').value;
  const title    = document.getElementById('f-title').value || 'My Post';
  const desc     = document.getElementById('f-desc').value  || '';

  showLoading('AI is thinking…');
  try {
    const data = await apiFetch('/ai/recommend', {
      method: 'POST',
      body: JSON.stringify({ platform, niche, title, description: desc })
    });

    document.getElementById('ai-caption').textContent = data.caption;

    aiHashtags = data.hashtags || [];
    document.getElementById('ai-tags').innerHTML = aiHashtags.map(h =>
      `<span class="ai-tag" onclick="toggleHashtag(this, '${h}')">${h}</span>`
    ).join('');

    document.getElementById('ai-times').innerHTML = (data.best_times || []).slice(0, 4).map((t, i) =>
      `<div class="ai-time-slot" id="ts-${i}" onclick="selectTimeSlot(this, '${t.datetime}')">
        <span class="ai-time-label">🕐 ${t.label}</span>
        <span class="ai-time-score">${Math.round(t.score * 100)}%</span>
      </div>`
    ).join('');

    document.getElementById('ai-box').classList.add('visible');
  } catch (e) {
    showToast('AI unavailable — make sure backend is running!', 'error');
  } finally {
    hideLoading();
  }
}

function useCaption() {
  document.getElementById('f-caption').value = document.getElementById('ai-caption').textContent;
  showToast('Caption applied!');
}

function toggleHashtag(el, tag) {
  const input = document.getElementById('f-hashtags');
  if (el.style.background.includes('0.3')) {
    el.style.background = '';
    el.style.color = '';
    input.value = input.value.replace(tag, '').replace(/\s+/g, ' ').trim();
  } else {
    el.style.background = 'rgba(91,127,255,0.3)';
    el.style.color = 'white';
    input.value = (input.value + ' ' + tag).trim();
  }
}

function selectTimeSlot(el, datetime) {
  document.querySelectorAll('.ai-time-slot').forEach(s => s.classList.remove('selected'));
  el.classList.add('selected');
  selectedScheduleTime = datetime;
  const d   = new Date(datetime);
  const pad = n => String(n).padStart(2, '0');
  document.getElementById('f-time').value =
    `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ══════════════════════════════════════════════
// SUBMIT POST
// ══════════════════════════════════════════════

async function submitPost() {
  const platform       = getModalPlatform();
  const title          = document.getElementById('f-title').value.trim();
  const desc           = document.getElementById('f-desc').value.trim();
  const caption        = document.getElementById('f-caption').value.trim();
  const hashtags       = document.getElementById('f-hashtags').value.trim();
  const image          = document.getElementById('f-image').value.trim();
  const niche          = document.getElementById('f-niche').value;
  const timeInput      = document.getElementById('f-time').value;
  const scheduled_time = timeInput ? new Date(timeInput).toISOString() : null;

  if (!title) { showToast('Please enter a title', 'error'); return; }

  showLoading('Scheduling post…');
  try {
    await apiFetch('/posts', {
      method: 'POST',
      body: JSON.stringify({ platform, title, description: desc, caption, hashtags, image_url: image, niche, scheduled_time })
    });
    showToast('Post scheduled! 🚀');
    closeModal();
    if (platform !== currentPlatform) switchPlatform(platform);
    else loadPosts();
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    hideLoading();
  }
}

// ══════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════
loadPosts();
loadStats();
renderChart();

// Auto-refresh every 60s
setInterval(() => { loadPosts(); loadStats(); }, 60000);
