/**
 * The file access the reader needs, narrow enough that `$.fs` and a test's
 * in-memory tree both satisfy it. Paths are relative to the session's
 * working directory or absolute, as `$.fs` takes them.
 */
export type ReaderFs = {
  read: (path: string) => Promise<string>
  /** An entry as it stands: a symbolic link is `other` (with `isLink`), whatever it leads to. `stat` says what that is. */
  list: (path: string) => Promise<{ name: string; kind: 'file' | 'dir' | 'other'; size: number; isLink?: boolean }[]>
  exists: (path: string) => Promise<boolean>
  stat: (path: string) => Promise<{ kind: 'file' | 'dir' | 'other'; size: number; mtimeMs: number }>
}

/** `read`, or null when the file is missing, unreadable or over the size cap. */
export async function readOrNull(fs: ReaderFs, path: string): Promise<string | null> {
  try {
    // `exists` never rejects; asking first keeps a missing optional file out of the error log.
    if (!(await fs.exists(path))) {
      return null
    }

    return await fs.read(path)
  } catch {
    return null
  }
}

/** `list`, or an empty list when the directory is missing. */
export async function listOrEmpty(
  fs: ReaderFs,
  path: string,
): Promise<{ name: string; kind: 'file' | 'dir' | 'other'; size: number; isLink?: boolean }[]> {
  try {
    if (!(await fs.exists(path))) {
      return []
    }

    return await fs.list(path)
  } catch {
    return []
  }
}

/** `stat`'s mtime, or null when the path is missing. */
export async function mtimeOrNull(fs: ReaderFs, path: string): Promise<number | null> {
  try {
    if (!(await fs.exists(path))) {
      return null
    }

    return (await fs.stat(path)).mtimeMs
  } catch {
    return null
  }
}

/**
 * The directories under `path`, by name. A symbolic link to a directory counts: the engine lists a link as `other`,
 * and a legacy tree is often a link to where the code really lives.
 */
export async function dirNamesOf(fs: ReaderFs, path: string): Promise<string[]> {
  const names: string[] = []

  for (const entry of await listOrEmpty(fs, path)) {
    if (entry.kind === 'dir') {
      names.push(entry.name)
    } else if (entry.kind === 'other') {
      try {
        if ((await fs.stat(`${path}/${entry.name}`)).kind === 'dir') {
          names.push(entry.name)
        }
      } catch {
        // a link that leads nowhere is not a system
      }
    }
  }

  return names
}
