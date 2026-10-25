const http = require('http');
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const PORT = process.env.PORT || 3333;
const ROOT_DIR = path.resolve(__dirname, '..');
const PUBLIC_DIR = path.join(__dirname, 'public');

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'application/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

function getMarketplaceData() {
  const marketplacePath = path.join(ROOT_DIR, '.claude-plugin', 'marketplace.json');
  if (!fs.existsSync(marketplacePath)) {
    return { error: 'marketplace.json not found' };
  }
  return JSON.parse(fs.readFileSync(marketplacePath, 'utf8'));
}

function getGitCommits(skip = 0, limit = 45) {
  try {
    const raw = execSync(`git log --skip=${skip} -n ${limit} --format="%H|%h|%an|%ad|%s" --date=iso`, { cwd: ROOT_DIR }).toString();
    const commits = raw.trim().split('\n').filter(Boolean).map(line => {
      const parts = line.split('|');
      return {
        fullSha: parts[0],
        shortSha: parts[1],
        author: parts[2],
        date: parts[3],
        subject: parts.slice(4).join('|')
      };
    });
    return commits;
  } catch (err) {
    return [];
  }
}

function getRepoStats() {
  let commitCount = 0;
  let branch = 'main';
  try {
    commitCount = parseInt(execSync('git rev-list --count HEAD', { cwd: ROOT_DIR }).toString().trim(), 10);
    branch = execSync('git rev-parse --abbrev-ref HEAD', { cwd: ROOT_DIR }).toString().trim();
  } catch (e) {}

  const mp = getMarketplaceData();
  const plugins = mp.plugins || [];
  
  const categories = {};
  const authors = {};
  let vendoredCount = 0;
  let remoteUrlCount = 0;
  let gitSubdirCount = 0;

  plugins.forEach(p => {
    const cat = p.category || 'other';
    categories[cat] = (categories[cat] || 0) + 1;

    const author = (p.author && p.author.name) ? p.author.name : 'Community';
    authors[author] = (authors[author] || 0) + 1;

    if (typeof p.source === 'string') {
      vendoredCount++;
    } else if (p.source && p.source.source === 'git-subdir') {
      gitSubdirCount++;
    } else {
      remoteUrlCount++;
    }
  });

  return {
    repo: 'sameer10237/claude-plugins-official',
    upstream: 'https://github.com/anthropics/claude-plugins-official.git',
    license: 'Apache-2.0',
    branch,
    commitCount,
    pluginCount: plugins.length,
    vendoredCount,
    remoteUrlCount,
    gitSubdirCount,
    categories,
    authors,
    renamesCount: Object.keys(mp.renames || {}).length
  };
}

const server = http.createServer((req, res) => {
  const urlObj = new URL(req.url, `http://${req.headers.host}`);
  const pathname = urlObj.pathname;

  // API Routes
  if (pathname === '/api/stats') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(getRepoStats()));
    return;
  }

  if (pathname === '/api/plugins') {
    const mp = getMarketplaceData();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(mp));
    return;
  }

  if (pathname === '/api/commits') {
    const skip = parseInt(urlObj.searchParams.get('skip') || '0', 10);
    const limit = parseInt(urlObj.searchParams.get('limit') || '30', 10);
    const commits = getGitCommits(skip, limit);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ commits, skip, limit }));
    return;
  }

  if (pathname === '/api/plugin-details') {
    const name = urlObj.searchParams.get('name');
    const mp = getMarketplaceData();
    const plugin = (mp.plugins || []).find(p => p.name === name);
    if (!plugin) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Plugin not found' }));
      return;
    }

    let readme = '';
    let isLocal = false;
    if (typeof plugin.source === 'string') {
      isLocal = true;
      const localPath = path.resolve(ROOT_DIR, plugin.source);
      const readmePath = path.join(localPath, 'README.md');
      if (fs.existsSync(readmePath)) {
        readme = fs.readFileSync(readmePath, 'utf8');
      }
    }

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ plugin, isLocal, readme }));
    return;
  }

  // Static Assets
  let filePath = path.join(PUBLIC_DIR, pathname === '/' ? 'index.html' : pathname);
  
  fs.stat(filePath, (err, stats) => {
    if (err || !stats.isFile()) {
      filePath = path.join(PUBLIC_DIR, 'index.html');
    }
    const finalExt = path.extname(filePath);
    const contentType = MIME_TYPES[finalExt] || 'application/octet-stream';

    fs.readFile(filePath, (readErr, data) => {
      if (readErr) {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('404 Not Found');
        return;
      }
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(data);
    });
  });
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Claude Plugins Marketplace Dashboard running at http://localhost:${PORT}`);
});
