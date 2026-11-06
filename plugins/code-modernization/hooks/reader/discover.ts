import { baseName, join, stemOf } from '../paths'
import {
  groupOfDir,
  languageOf,
  weightOf,
  type EstateModel,
  type EstateUnit,
} from './estate-model'
import { listOrEmpty, type ReaderFs } from './fs'

/**
 * Reads the estate off the legacy tree when no map exists: any language, any
 * layout. A directory with a build file of its own is one unit (a Maven or Gradle
 * module, an npm package, a .NET project, a Go module, a Python package); a tree
 * with no build files is one unit per source file when it is small enough to show,
 * else one per directory. Sizes are bytes of source: what the file system knows
 * without reading a file.
 */

/** Directories that hold what a build made or what someone else wrote, never the system's own code. */
const SKIP_DIRS = new Set([
  '.git', '.hg', '.svn', 'node_modules', 'target', 'dist', 'obj', 'build', 'out', '.gradle', '.idea', '.vscode',
  '__pycache__', '.venv', 'venv', '.tox', '.mypy_cache', '.pytest_cache', 'coverage', '.next', '.nuxt', 'Pods',
  'vendor', 'bower_components', 'site-packages',
])

const MANIFEST_NAMES = new Set([
  'pom.xml', 'build.gradle', 'build.gradle.kts', 'package.json', 'go.mod', 'Cargo.toml', 'pyproject.toml',
  'setup.py', 'composer.json', 'Gemfile', 'mix.exs', 'CMakeLists.txt', 'pubspec.yaml', 'Package.swift',
  'build.sbt', 'project.clj', 'deps.edn', 'cpanfile', 'Makefile.PL', 'BUILD.bazel', 'Project.toml',
])

const MANIFEST_SUFFIXES = ['.csproj', '.fsproj', '.vbproj', '.vcxproj']

const isManifest = (name: string): boolean => MANIFEST_NAMES.has(name) || MANIFEST_SUFFIXES.some(suffix => name.endsWith(suffix))

/** What a walk may spend: directories read, and entries seen. */
export type Budget = { dirs: number; entries: number }

export const DEFAULT_BUDGET: Budget = { dirs: 4000, entries: 80_000 }

/** A file-per-unit estate is shown only up to this many source files. */
const MAX_FILE_UNITS = 500

/** The most units an estate keeps; the rest are too small to draw. */
const MAX_UNITS = 1500

type DirInfo = {
  /** Source bytes in files directly in this directory. */
  bytes: number
  /** The same, counting files of a kind no list knows: the tree may be written in a language this one does not name. */
  lenientBytes: number
  files: { name: string; size: number; lenient: number; raw: number }[]
  dirs: string[]
  hasManifest: boolean
}

/** Reads every directory under `root` that the budget allows, keyed by path relative to it (`''` is the root). */
export async function walk(
  fs: ReaderFs,
  root: string,
  budget: Budget,
): Promise<{ dirs: Map<string, DirInfo>; isPartial: boolean; files: number; bytesByLanguage: Map<string, number> }> {
  const dirs = new Map<string, DirInfo>()
  const bytesByLanguage = new Map<string, number>()
  let queue: string[] = ['']
  let readDirs = 0
  let entries = 0
  let files = 0
  let isPartial = false

  while (queue.length > 0) {
    const room = budget.dirs - readDirs

    if (room <= 0 || entries > budget.entries) {
      isPartial = true

      break
    }

    const level = queue.slice(0, Math.min(16, room))

    queue = queue.slice(level.length)
    readDirs += level.length

    const listed = await Promise.all(level.map(rel => listOrEmpty(fs, rel === '' ? root : join(root, rel))))

    level.forEach((rel, index) => {
      const list = listed[index] ?? []
      const info: DirInfo = { bytes: 0, lenientBytes: 0, files: [], dirs: [], hasManifest: false }

      entries += list.length

      for (const entry of list) {
        if (entry.kind === 'dir') {
          if (!SKIP_DIRS.has(entry.name) && !entry.name.startsWith('.')) {
            info.dirs.push(entry.name)
            queue.push(rel === '' ? entry.name : `${rel}/${entry.name}`)
          }

          continue
        }

        if (entry.kind !== 'file') {
          continue
        }

        if (isManifest(entry.name)) {
          info.hasManifest = true
        }

        const strict = weightOf(entry.name, entry.size)
        const lenient = weightOf(entry.name, entry.size, true)

        if (lenient > 0) {
          info.files.push({ name: entry.name, size: strict, lenient, raw: entry.size })
          info.bytes += strict
          info.lenientBytes += lenient
          files += 1
        }

        const language = strict > 0 ? languageOf(entry.name) : undefined

        if (language !== undefined) {
          bytesByLanguage.set(language, (bytesByLanguage.get(language) ?? 0) + strict)
        }
      }

      dirs.set(rel, info)
    })
  }

  if (queue.length > 0) {
    isPartial = true
  }

  return { dirs, isPartial, files, bytesByLanguage }
}

/** Every file a walk counted, by path relative to its root, with its size in bytes. */
export function sizesOf(dirs: Map<string, DirInfo>): Map<string, number> {
  const sizes = new Map<string, number>()

  for (const [rel, info] of dirs) {
    for (const file of info.files) {
      sizes.set(rel === '' ? file.name : `${rel}/${file.name}`, file.raw)
    }
  }

  return sizes
}

/**
 * The files under `root` and their sizes, read with the file API alone: nothing is run inside the tree.
 * Null when the walk hit its budget, since a partial listing would call every unread file changed.
 */
export async function sourceSizes(fs: ReaderFs, root: string, budget: Budget = DEFAULT_BUDGET): Promise<Map<string, number> | null> {
  const walked = await walk(fs, root, budget)

  return walked.isPartial ? null : sizesOf(walked.dirs)
}

/** Bytes under `rel`, every directory beneath included. */
function totalBytes(dirs: Map<string, DirInfo>, rel: string): number {
  const info = dirs.get(rel)

  if (info === undefined) {
    return 0
  }

  return info.dirs.reduce(
    (sum, name) => sum + totalBytes(dirs, rel === '' ? name : `${rel}/${name}`),
    info.bytes,
  )
}

const under = (path: string, dir: string): boolean => dir === '' || path === dir || path.startsWith(`${dir}/`)

/** Units where each directory with a build file is one, sized by the bytes not inside a unit beneath it. */
function buildModules(dirs: Map<string, DirInfo>, rootLabel: string): EstateUnit[] {
  const manifestDirs = [...dirs.entries()].filter(([, info]) => info.hasManifest).map(([rel]) => rel)
  const set = new Set(manifestDirs)

  const ownBytes = (rel: string): number => {
    const info = dirs.get(rel)

    if (info === undefined) {
      return 0
    }

    return info.dirs.reduce((sum, name) => {
      const child = rel === '' ? name : `${rel}/${name}`

      return set.has(child) ? sum : sum + ownBytes(child)
    }, info.bytes)
  }

  return manifestDirs
    .map(rel => ({
      id: rel === '' ? '.' : rel,
      name: rel === '' ? rootLabel : baseName(rel),
      group: rel === '' ? rootLabel : groupOfDir(rel, rootLabel),
      size: ownBytes(rel),
      dir: rel,
    }))
    .filter(unit => unit.size > 0)
}

/** One unit per source file, grouped by the directory it sits in. */
function fileUnits(dirs: Map<string, DirInfo>, rootLabel: string): EstateUnit[] {
  const units: EstateUnit[] = []

  for (const [rel, info] of dirs) {
    for (const file of info.files) {
      if (file.size <= 0) {
        continue
      }

      const path = rel === '' ? file.name : `${rel}/${file.name}`

      units.push({
        id: path,
        name: stemOf(file.name),
        group: rel === '' ? rootLabel : rel,
        size: Math.max(1, file.size),
        file: path,
      })
    }
  }

  return units
}

/** One unit per directory: the top-level ones, and the children of a lone directory that holds nearly everything. */
function directoryUnits(dirs: Map<string, DirInfo>, rootLabel: string): EstateUnit[] {
  const total = totalBytes(dirs, '')
  let parent = ''

  for (let guard = 0; guard < 4; guard += 1) {
    const info = dirs.get(parent)
    const children = info?.dirs ?? []
    const sizes = children.map(name => ({ name, bytes: totalBytes(dirs, parent === '' ? name : `${parent}/${name}`) }))
    const largest = sizes.sort((a, b) => b.bytes - a.bytes)[0]

    if (largest === undefined || total === 0 || largest.bytes / total < 0.85 || (info?.bytes ?? 0) / total > 0.05) {
      break
    }

    parent = parent === '' ? largest.name : `${parent}/${largest.name}`
  }

  const info = dirs.get(parent)
  const units: EstateUnit[] = []

  for (const name of info?.dirs ?? []) {
    const rel = parent === '' ? name : `${parent}/${name}`
    const size = totalBytes(dirs, rel)

    if (size > 0) {
      units.push({ id: rel, name, group: parent === '' ? rootLabel : parent, size, dir: rel })
    }
  }

  if ((info?.bytes ?? 0) > 0) {
    units.push({ id: parent === '' ? '.' : parent, name: parent === '' ? `${rootLabel} (files)` : `${baseName(parent)} (files)`, group: parent === '' ? rootLabel : parent, size: info?.bytes ?? 0, dir: parent })
  }

  return units
}

/**
 * The estate of one system, read off `<root>` (its directory under the legacy tree). Null when the
 * directory holds no source.
 */
export async function discoverEstate(
  fs: ReaderFs,
  root: string,
  rootLabel: string,
  budget: Budget = DEFAULT_BUDGET,
): Promise<EstateModel | null> {
  const walked = await walk(fs, root, budget)

  if (walked.files === 0) {
    return null
  }

  // A tree written in a language nobody listed has almost no weight on a strict count: count every file of an unknown
  // kind as source then, so the estate is the tree and not the few configuration files beside it.
  const strictTotal = [...walked.dirs.values()].reduce((sum, info) => sum + info.bytes, 0)
  const lenientTotal = [...walked.dirs.values()].reduce((sum, info) => sum + info.lenientBytes, 0)

  if (lenientTotal > 0 && strictTotal < lenientTotal * 0.35) {
    for (const info of walked.dirs.values()) {
      info.bytes = info.lenientBytes

      for (const file of info.files) {
        file.size = file.lenient
      }
    }
  }

  const counted = [...walked.dirs.values()].reduce((sum, info) => sum + info.files.filter(file => file.size > 0).length, 0)
  const manifestCount = [...walked.dirs.entries()].filter(([rel, info]) => info.hasManifest && rel !== '').length

  let units: EstateUnit[]
  let granularity: EstateModel['granularity']

  if (manifestCount >= 2) {
    units = buildModules(walked.dirs, rootLabel)
    granularity = 'build module'
  } else if (counted <= MAX_FILE_UNITS) {
    units = fileUnits(walked.dirs, rootLabel)
    granularity = 'file'
  } else {
    units = directoryUnits(walked.dirs, rootLabel)
    granularity = 'directory'
  }

  if (units.length === 0) {
    return null
  }

  const total = [...walked.bytesByLanguage.values()].reduce((sum, bytes) => sum + bytes, 0)

  const languages = [...walked.bytesByLanguage.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([name, bytes]) => ({ name, share: total > 0 ? bytes / total : 0 }))

  return {
    source: 'tree',
    measure: 'bytes',
    granularity,
    units: units.sort((a, b) => b.size - a.size).slice(0, MAX_UNITS),
    files: counted,
    languages,
    isPartial: walked.isPartial,
    fileSizes: sizesOf(walked.dirs),
  }
}

