#!/usr/bin/env python3
"""
Extract the VERSION constant from main.py for use in build scripts.
Prints the version string to stdout, or "NOTFOUND"/"NON_CONSTANT" on error.
"""

import ast
import sys
from pathlib import Path


def extract_version(source_path: Path) -> str:
    """Parse main.py and extract VERSION constant."""
    try:
        source_text = source_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"ERROR reading {source_path}: {e}", file=sys.stderr)
        return "NOTFOUND"

    try:
        tree = ast.parse(source_text, filename=str(source_path))
    except SyntaxError as e:
        print(f"Syntax error in {source_path}: {e}", file=sys.stderr)
        return "NOTFOUND"

    # Look for VERSION = "..." at module level
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "VERSION":
                    # Check if the value is a constant string
                    if isinstance(node.value, ast.Constant) and isinstance(
                        node.value.value, str
                    ):
                        return node.value.value
                    else:
                        return "NON_CONSTANT"

    return "NOTFOUND"


if __name__ == "__main__":
    main_py = Path(__file__).parent / "main.py"
    version = extract_version(main_py)
    print(version)
