let allPlugins = [];
let currentCategory = 'all';
let currentSource = 'all';
let currentSort = 'name-asc';
let currentSearch = '';

let commitSkip = 0;
const commitLimit = 15;

// DOM Elements
const pluginsGrid = document.getElementById('plugins-grid');
const searchInput = document.getElementById('search-input');
const searchClear = document.getElementById('search-clear');
const categoryPillsContainer = document.getElementById('category-pills');
const sourceFilter = document.getElementById('source-filter');
const sortFilter = document.getElementById('sort-filter');
const resultsCount = document.getElementById('results-count');

const pluginModal = document.getElementById('plugin-modal');
const modalClose = document.getElementById('modal-close');
const btnCopyInstall = document.getElementById('btn-copy-install');
const modalInstallCmd = document.getElementById('modal-install-cmd');

const commitsTimeline = document.getElementById('commits-timeline');
const btnPrevCommits = document.getElementById('btn-prev-commits');
const btnNextCommits = document.getElementById('btn-next-commits');
const commitsBatchLabel = document.getElementById('commits-batch-label');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  loadStats();
  loadPlugins();
  loadCommits(0);
  bindEvents();
});

function initTabs() {
  const tabs = document.querySelectorAll('.tab-btn');
  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

      btn.classList.add('active');
      const tabId = `tab-${btn.dataset.tab}`;
      const target = document.getElementById(tabId);
      if (target) target.classList.add('active');
    });
  });
}

function bindEvents() {
  searchInput.addEventListener('input', (e) => {
    currentSearch = e.target.value.trim().toLowerCase();
    searchClear.classList.toggle('hidden', !currentSearch);
    renderFilteredPlugins();
  });

  searchClear.addEventListener('click', () => {
    searchInput.value = '';
    currentSearch = '';
    searchClear.classList.add('hidden');
    renderFilteredPlugins();
  });

  sourceFilter.addEventListener('change', (e) => {
    currentSource = e.target.value;
    renderFilteredPlugins();
  });

  sortFilter.addEventListener('change', (e) => {
    currentSort = e.target.value;
    renderFilteredPlugins();
  });

  modalClose.addEventListener('click', () => {
    pluginModal.classList.add('hidden');
  });

  pluginModal.addEventListener('click', (e) => {
    if (e.target === pluginModal) pluginModal.classList.add('hidden');
  });

  btnCopyInstall.addEventListener('click', () => {
    const cmd = modalInstallCmd.innerText;
    navigator.clipboard.writeText(cmd).then(() => {
      const originalText = btnCopyInstall.innerHTML;
      btnCopyInstall.innerText = 'Copied!';
      btnCopyInstall.style.background = '#10b981';
      setTimeout(() => {
        btnCopyInstall.innerHTML = originalText;
        btnCopyInstall.style.background = '';
      }, 1500);
    });
  });

  btnPrevCommits.addEventListener('click', () => {
    if (commitSkip >= commitLimit) {
      loadCommits(commitSkip - commitLimit);
    }
  });

  btnNextCommits.addEventListener('click', () => {
    loadCommits(commitSkip + commitLimit);
  });
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    document.getElementById('metric-plugins').innerText = data.pluginCount || 315;
    document.getElementById('metric-vendored').innerText = `${data.vendoredCount || 53}`;
    document.getElementById('metric-remote').innerText = `${(data.remoteUrlCount || 0) + (data.gitSubdirCount || 0)}`;
    document.getElementById('metric-commits').innerText = (data.commitCount || 4632).toLocaleString();
    document.getElementById('metric-branch').innerText = data.branch || 'main';
  } catch (err) {
    console.error('Failed to load stats', err);
  }
}

async function loadPlugins() {
  try {
    const res = await fetch('/api/plugins');
    const data = await res.json();
    allPlugins = data.plugins || [];
    buildCategoryPills(allPlugins);
    renderFilteredPlugins();
  } catch (err) {
    pluginsGrid.innerHTML = `<p class="error-msg">Failed to load plugins from marketplace.json</p>`;
  }
}

function buildCategoryPills(plugins) {
  const counts = {};
  plugins.forEach(p => {
    const cat = p.category || 'other';
    counts[cat] = (counts[cat] || 0) + 1;
  });

  document.getElementById('cat-all-count').innerText = plugins.length;

  const categories = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
  
  // Clear any existing extra pills
  const existingButtons = categoryPillsContainer.querySelectorAll('.pill:not([data-category="all"])');
  existingButtons.forEach(b => b.remove());

  categories.forEach(cat => {
    const btn = document.createElement('button');
    btn.className = 'pill';
    btn.dataset.category = cat;
    btn.innerText = `${cat.charAt(0).toUpperCase() + cat.slice(1)} (${counts[cat]})`;
    btn.addEventListener('click', () => {
      categoryPillsContainer.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      currentCategory = cat;
      renderFilteredPlugins();
    });
    categoryPillsContainer.appendChild(btn);
  });

  // Re-bind 'all'
  categoryPillsContainer.querySelector('[data-category="all"]').addEventListener('click', (e) => {
    categoryPillsContainer.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
    e.target.closest('.pill').classList.add('active');
    currentCategory = 'all';
    renderFilteredPlugins();
  });
}

function renderFilteredPlugins() {
  let list = allPlugins.filter(p => {
    // Category match
    if (currentCategory !== 'all' && (p.category || 'other') !== currentCategory) return false;

    // Source match
    if (currentSource === 'vendored' && typeof p.source !== 'string') return false;
    if (currentSource === 'git-subdir' && (!p.source || p.source.source !== 'git-subdir')) return false;
    if (currentSource === 'url' && (!p.source || p.source.source !== 'url' && typeof p.source === 'string')) return false;

    // Search query
    if (currentSearch) {
      const matchName = (p.name || '').toLowerCase().includes(currentSearch);
      const matchDesc = (p.description || '').toLowerCase().includes(currentSearch);
      const matchAuthor = (p.author && p.author.name && p.author.name.toLowerCase().includes(currentSearch));
      const matchCat = (p.category || '').toLowerCase().includes(currentSearch);
      if (!matchName && !matchDesc && !matchAuthor && !matchCat) return false;
    }

    return true;
  });

  // Sorting
  list.sort((a, b) => {
    if (currentSort === 'name-asc') return (a.name || '').localeCompare(b.name || '');
    if (currentSort === 'name-desc') return (b.name || '').localeCompare(a.name || '');
    if (currentSort === 'category') return (a.category || '').localeCompare(b.category || '');
    return 0;
  });

  resultsCount.innerText = `Showing ${list.length} of ${allPlugins.length} plugins`;

  if (list.length === 0) {
    pluginsGrid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: var(--text-muted);">
        <h3>No matching plugins found</h3>
        <p style="margin-top: 0.5rem;">Try adjusting your search terms or category filters</p>
      </div>`;
    return;
  }

  pluginsGrid.innerHTML = list.map(p => {
    let sourceLabel = 'Remote Git';
    let sourceClass = '';
    if (typeof p.source === 'string') {
      sourceLabel = 'Vendored';
      sourceClass = 'vendored';
    } else if (p.source && p.source.source === 'git-subdir') {
      sourceLabel = 'Git-Subdir';
    }

    const author = (p.author && p.author.name) ? p.author.name : 'Community';
    const category = p.category || 'other';

    return `
      <div class="plugin-card" onclick="openPluginModal('${escapeHtml(p.name)}')">
        <div>
          <div class="card-top">
            <span class="category-tag">${escapeHtml(category)}</span>
            <span class="source-badge ${sourceClass}">${sourceLabel}</span>
          </div>
          <h3 class="card-title">${escapeHtml(p.name)}</h3>
          <div class="card-author">by ${escapeHtml(author)}</div>
          <p class="card-desc">${escapeHtml(p.description || 'No description provided.')}</p>
        </div>
        <div class="card-footer">
          <span>/plugin install ${escapeHtml(p.name)}</span>
          <span class="view-link">Details →</span>
        </div>
      </div>
    `;
  }).join('');
}

async function openPluginModal(name) {
  const plugin = allPlugins.find(p => p.name === name);
  if (!plugin) return;

  document.getElementById('modal-name').innerText = plugin.name;
  document.getElementById('modal-category').innerText = plugin.category || 'Plugin';
  document.getElementById('modal-author').innerText = `by ${(plugin.author && plugin.author.name) ? plugin.author.name : 'Unknown'}`;
  document.getElementById('modal-desc').innerText = plugin.description || 'No description provided.';
  modalInstallCmd.innerText = `/plugin install ${plugin.name}@claude-plugins-official`;

  // Source box
  document.getElementById('modal-source').innerText = JSON.stringify(plugin.source || 'Local Vendored', null, 2);

  // Skills
  const skillsSection = document.getElementById('modal-skills-section');
  const skillsList = document.getElementById('modal-skills-list');
  if (plugin.skills && Array.isArray(plugin.skills) && plugin.skills.length > 0) {
    skillsSection.style.display = 'block';
    skillsList.innerHTML = plugin.skills.map(s => `<li>${escapeHtml(s)}</li>`).join('');
  } else {
    skillsSection.style.display = 'none';
  }

  // Readme
  const readmeSection = document.getElementById('modal-readme-section');
  const readmeBox = document.getElementById('modal-readme');
  readmeSection.style.display = 'none';

  pluginModal.classList.remove('hidden');

  // Attempt to fetch local README
  try {
    const res = await fetch(`/api/plugin-details?name=${encodeURIComponent(name)}`);
    const details = await res.json();
    if (details.readme) {
      readmeSection.style.display = 'block';
      readmeBox.innerText = details.readme;
    }
  } catch (e) {}
}

async function loadCommits(skip) {
  commitSkip = skip;
  btnPrevCommits.disabled = (commitSkip === 0);
  commitsBatchLabel.innerText = `Commits ${commitSkip + 1} - ${commitSkip + commitLimit}`;

  commitsTimeline.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-muted);">Loading commits...</div>`;

  try {
    const res = await fetch(`/api/commits?skip=${commitSkip}&limit=${commitLimit}`);
    const data = await res.json();
    const commits = data.commits || [];

    if (commits.length === 0) {
      commitsTimeline.innerHTML = `<p style="padding: 2rem; color: var(--text-muted); text-align: center;">No further commits found.</p>`;
      return;
    }

    commitsTimeline.innerHTML = commits.map((c, idx) => {
      const commitNum = commitSkip + idx + 1;
      const formattedDate = new Date(c.date).toLocaleDateString(undefined, {
        month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
      });

      return `
        <div class="commit-row">
          <div class="commit-left">
            <span class="commit-num">#${commitNum}</span>
            <span class="commit-sha" title="${c.fullSha}">${c.shortSha}</span>
            <span class="commit-subject">${escapeHtml(c.subject)}</span>
          </div>
          <div class="commit-meta">
            <span>${escapeHtml(c.author)}</span>
            <span>${formattedDate}</span>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    commitsTimeline.innerHTML = `<p class="error-msg">Failed to load commits.</p>`;
  }
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.innerText = text;
  return div.innerHTML;
}
