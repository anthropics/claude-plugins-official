#!/usr/bin/env python3
"""Split a system's source into shards for per-module rule extraction.

    python3 make_shards.py <system> [module-pattern] [--workspace DIR] [--all]

The source directory is legacy/<system> (a copy, or a symlink to where the code lives). With analysis/<system>/topology.json, one shard per map
module (small modules of a domain merged); without it, one shard per directory of source
files. The list is written to analysis/<system>/extract-rules.modules.json as
[{"name", "domain", "files": [relative to the source dir], "loc"}], the form the
extract-rules workflow takes. Standard library only.
"""
import fnmatch
import json
import os
import sys

SOURCE_EXT = {
    # mainframe and legacy business languages
    '.cbl', '.cob', '.cobol', '.cpy', '.pli', '.pl1', '.jcl', '.proc', '.rpg', '.rpgle', '.sqlrpgle', '.clle', '.nat', '.ada', '.adb', '.ads',
    '.asm', '.bms', '.map', '.pas', '.dpr', '.prg', '.f', '.for', '.f90', '.f77',
    # general purpose
    '.java', '.kt', '.scala', '.groovy', '.cs', '.vb', '.vbs', '.bas', '.cls', '.frm', '.fs', '.c', '.h', '.cc', '.cpp', '.cxx', '.hpp', '.m', '.mm',
    '.go', '.rs', '.py', '.rb', '.php', '.pl', '.pm', '.js', '.jsx', '.ts', '.tsx', '.swift', '.lua', '.tcl', '.erl', '.ex', '.exs', '.clj',
    '.hs', '.ml', '.r', '.sh', '.bat', '.ps1',
    # web and data
    '.asp', '.aspx', '.ascx', '.cshtml', '.jsp', '.jspx', '.sql', '.pks', '.pkb', '.plsql', '.tf',
}
SKIP_DIRS = {
    '.git', '.svn', '.hg', 'node_modules', 'vendor', 'third_party', 'thirdparty', 'dist', 'build', 'target', 'bin', 'obj', 'out',
    '__pycache__', '.venv', 'venv', '.tox', '.gradle', '.idea', 'coverage', 'fixtures', 'testdata', 'test-data', 'generated',
}
TEST_DIRS = {'test', 'tests', '__tests__', 'spec', 'specs'}
MAX_FILES = 25
MAX_LOC = 5000
SMALL = 300
TINY_ESTATE = 30
MAX_BYTES = 5_000_000


def too_broad(path):
    """The filesystem root, the home directory or one of its parents, or a top-level system directory: never a system's code."""
    real = os.path.realpath(path)
    home = os.path.realpath(os.path.expanduser('~'))
    parts = [p for p in real.split(os.sep) if p]
    return real == os.sep or len(parts) < 2 or home == real or home.startswith(real + os.sep)


def source_dir(workspace, system):
    """The code is legacy/<system>: a copy, or a symlink to where it really lives."""
    return os.path.join(workspace, 'legacy', system)


def count_lines(path):
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None
        with open(path, 'rb') as handle:
            data = handle.read()
    except OSError:
        return None
    if b'\x00' in data[:4096]:
        return None
    return data.count(b'\n') + (1 if data and not data.endswith(b'\n') else 0)


def matcher(pattern):
    """A glob matches a name or a path (or its file name); a plain name such as `jetty-util` also matches what lies beneath it."""
    plain_name = not any(ch in pattern for ch in '*?[')
    wanted = pattern.strip('/')

    def match(text):
        if fnmatch.fnmatch(text, pattern) or fnmatch.fnmatch(os.path.basename(text), pattern):
            return True
        if plain_name:
            padded = '/' + text.strip('/') + '/'
            return padded.startswith('/' + wanted + '/') or ('/' + wanted + '/') in padded
        return False

    return match


def contained(source, rel):
    """True when `rel` under the source directory really resolves inside it (no `..`, no symlink out)."""
    root = os.path.realpath(source)
    real = os.path.realpath(os.path.join(source, rel))
    return real == root or real.startswith(root + os.sep)


def relative_to_source(path, source, system):
    """A topology `file` may be absolute, workspace-relative or source-relative: return it source-relative."""
    path = path.replace('\\', '/')
    if os.path.isabs(path):
        rel = os.path.relpath(path, source).replace(os.sep, '/')
        return None if rel.startswith('..') else rel
    for prefix in (f'legacy/{system}/', os.path.normpath(source).replace(os.sep, '/') + '/'):
        if path.startswith(prefix):
            return path[len(prefix):]
    return path


def shared_locations(modules, source):
    """Locations several map modules share, or that are directories: modules without files of their own cannot be sharded."""
    seen, shared = {}, []
    for module in modules:
        for rel in module['files']:
            seen.setdefault(rel, []).append(module['name'])
    for rel, owners in seen.items():
        if len(owners) > 1 or os.path.isdir(os.path.join(source, rel)):
            shared.append((rel, len(owners)))
    return shared


def from_topology(topology, source, system, pattern):
    modules, names, escaped = [], set(), []

    def walk(node, domain):
        kind = node.get('kind')
        if kind == 'domain':
            domain = node.get('name') or node.get('id', '')
        if kind == 'module' and node.get('file'):
            rel = relative_to_source(str(node['file']), source, system)
            if rel and not contained(source, rel):
                escaped.append(rel)
            elif rel:
                name = str(node.get('name') or node.get('id'))
                if name in names:
                    name = str(node.get('id') or name)  # names can repeat across domains; ids are unique
                names.add(name)
                modules.append({'name': name, 'domain': domain, 'files': [rel], 'loc': node.get('loc') or None})
        for child in node.get('children', []):
            walk(child, domain)

    walk(topology['root'], '')
    total = len(modules)
    unusable = shared_locations(modules, source)
    if unusable:
        raise ValueError('%d map module(s) share a location or name a directory instead of a file (first: %s)' % (len(unusable), unusable[0][0]))
    if pattern:
        match = matcher(pattern)
        modules = [m for m in modules if match(m['name']) or any(match(f) for f in m['files'])]
    # merge small modules of the same domain; never split one
    shards, pool, counter = [], {}, {}
    for module in modules:
        if module['loc'] and module['loc'] < SMALL:
            current = pool.get(module['domain'])
            if current is None or current['loc'] >= SMALL or len(current['files']) >= MAX_FILES:
                counter[module['domain']] = counter.get(module['domain'], 0) + 1
                current = pool[module['domain']] = {
                    'name': f"{module['domain'] or 'misc'}:small-{counter[module['domain']]}",
                    'domain': module['domain'], 'files': [], 'loc': 0,
                }
                shards.append(current)
            current['files'] += module['files']
            current['loc'] += module['loc']
        else:
            shards.append(module)
    return shards, len(modules), escaped, total


def from_tree(source, pattern, include_all):
    by_dir, skipped = {}, {'vendored or generated': 0, 'tests': 0, 'unreadable or binary': 0, 'symbolic links': 0}
    for root, dirs, files in os.walk(source):
        kept = []
        for d in sorted(dirs):
            if d in SKIP_DIRS or (d.startswith('.') and d not in ('.',)):
                skipped['vendored or generated'] += 1
            elif d.lower() in TEST_DIRS and not include_all:
                skipped['tests'] += 1
            else:
                kept.append(d)
        dirs[:] = kept
        for name in sorted(files):
            if os.path.splitext(name)[1].lower() not in SOURCE_EXT or name.endswith('.min.js'):
                continue
            path = os.path.join(root, name)
            if os.path.islink(path):
                skipped['symbolic links'] += 1  # a link can point outside the source directory
                continue
            lines = count_lines(path)
            if lines is None:
                skipped['unreadable or binary'] += 1
                continue
            rel = os.path.relpath(path, source).replace(os.sep, '/')
            by_dir.setdefault(os.path.dirname(rel), []).append((rel, lines))
    whole = sum(len(fs) for fs in by_dir.values())
    if pattern:
        match = matcher(pattern)
        by_dir = {d: [f for f in fs if match(f[0])] for d, fs in by_dir.items()}
    shards, total = [], 0
    for directory in sorted(by_dir):
        entries = by_dir[directory]
        total += len(entries)
        chunk, chunk_loc, part = [], 0, 1
        label = directory or '.'
        for rel, lines in entries + [(None, 0)]:
            if rel is None or (chunk and (len(chunk) >= MAX_FILES or chunk_loc + lines > MAX_LOC)):
                if chunk:
                    shards.append({'name': label if part == 1 else f'{label}#{part}', 'domain': directory,
                                   'files': [f for f, _ in chunk], 'loc': chunk_loc or None})
                    part += 1
                chunk, chunk_loc = [], 0
            if rel is not None:
                chunk.append((rel, lines))
                chunk_loc += lines
    return shards, total, skipped, whole


def main(argv):
    args = [a for a in argv[1:] if not a.startswith('--')]
    flags = [a for a in argv[1:] if a.startswith('--')]
    workspace = '.'
    if '--workspace' in argv:
        workspace = argv[argv.index('--workspace') + 1]
        args = [a for a in args if a != workspace]
    if not args:
        print('usage: make_shards.py <system> [module-pattern] [--workspace DIR] [--all]', file=sys.stderr)
        return 2
    system, pattern = args[0], (args[1] if len(args) > 1 else '')
    source = source_dir(workspace, system)
    print(f'source: {source}')
    if os.path.isdir(source) and too_broad(source):
        print(f'{source} is too broad to be one system (the filesystem root, your home directory or a top-level directory). '
              'Point --source at the directory that holds the code.', file=sys.stderr)
        return 1
    if not os.path.isdir(source):
        print(f'No code at {source}. Run preflight first (with --source <path> if the code lives elsewhere).', file=sys.stderr)
        return 1
    out = os.path.join(workspace, 'analysis', system, 'extract-rules.modules.json')
    topo_path = os.path.join(workspace, 'analysis', system, 'topology.json')
    notes = []
    if os.path.isfile(topo_path):
        try:
            with open(topo_path, encoding='utf-8') as handle:
                topology = json.load(handle)
            shards, modules, escaped, whole = from_topology(topology, source, system, pattern)
            origin = f'{modules} map modules'
            if escaped:
                notes.append(f'{len(escaped)} map file(s) resolve outside the source directory and were left out (first: {escaped[0]})')
            missing = [f for s in shards for f in s['files'] if not os.path.exists(os.path.join(source, f))]
            if missing:
                notes.append(f'{len(missing)} file(s) named by the map do not exist under the source directory (first: {missing[0]})')
        except (ValueError, KeyError, OSError) as error:
            print(f'note: the map cannot be sharded by module ({error}); reading the directory tree instead.')
            shards, files, skipped, whole = from_tree(source, pattern, '--all' in flags)
            origin = f'{files} source files (tree)'
    else:
        shards, files, skipped, whole = from_tree(source, pattern, '--all' in flags)
        origin = f'{files} source files (no topology.json: read from the directory tree)'
        left_out = ', '.join(f'{n} {k}' for k, n in skipped.items() if n)
        if left_out:
            notes.append(f'left out: {left_out}')
    if not shards:
        print('0 shards: the pattern matched nothing, or no source files were found. Nothing was written.', file=sys.stderr)
        return 1
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as handle:
        json.dump(shards, handle, indent=1)
    os.replace(tmp, out)
    file_count = sum(len(s['files']) for s in shards)
    loc = sum(s['loc'] or 0 for s in shards)
    print(f'{len(shards)} shards from {origin}, {file_count} files, {loc} lines -> {os.path.relpath(out, workspace)}')
    if whole < TINY_ESTATE:
        print(f'tiny estate: the system has fewer than {TINY_ESTATE} source files, so sharding adds little (run the workflow in lens mode).')
    for note in notes:
        print(f'note: {note}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
