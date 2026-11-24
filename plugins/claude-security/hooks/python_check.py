"""Print this Python's version, or with --path the path of its executable.

Below Python 3.9, exit 3; --path then prints nothing. hooks.sh runs this file by its path to find a
Python that can run hooks.py.
"""

import os
import sys

if __name__ == "__main__":
    too_old = sys.version_info < (3, 9)
    if sys.argv[1:] != ["--path"]:
        sys.stdout.write(".".join(map(str, sys.version_info[:3])))
    elif not too_old:
        # hooks.sh runs this path. As text, Python on Windows can write it in the ANSI code page.
        path = sys.executable.replace("\\", "/")
        named = path.encode("utf-8", "surrogatepass") if os.name == "nt" else os.fsencode(path)
        sys.stdout.buffer.write(named)
    sys.exit(3 * too_old)
