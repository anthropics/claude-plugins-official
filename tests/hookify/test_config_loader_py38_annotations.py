#!/usr/bin/env python3
"""Regression test for hookify imports on Python versions before 3.9."""

import builtins
import sys
import types
from pathlib import Path


class Py38Tuple:
    """Stand-in for Python 3.8's tuple, which is not subscriptable."""


def test_config_loader_annotations_do_not_subscript_tuple() -> None:
    source = Path("plugins/hookify/core/config_loader.py").read_text(encoding="utf-8")
    module_name = "config_loader_py38_annotation_test"
    module = types.ModuleType(module_name)
    sys.modules[module_name] = module
    namespace = module.__dict__
    namespace.update({
        "__builtins__": {
            **vars(builtins),
            "tuple": Py38Tuple,
        },
        "__name__": module_name,
    })

    try:
        exec(compile(source, "plugins/hookify/core/config_loader.py", "exec"), namespace)
        namespace["extract_frontmatter"].__annotations__
    finally:
        sys.modules.pop(module_name, None)


if __name__ == "__main__":
    test_config_loader_annotations_do_not_subscript_tuple()
