#!/usr/bin/env python3
"""
inline_svg.py

Reads an openapi spec on stdin, replaces any markdown image references that
point to local SVG files (relative to the repo root) with inline data URIs,
then prints it on stdout.

Usage (as part of the build pipeline):
    ... | poetry run python scripts/inline_svg.py > build/spec.json
"""
import sys
import json
import re
from pathlib import Path
from urllib.parse import quote

# Repo root is the directory containing this script's parent
REPO_ROOT = Path(__file__).resolve().parent.parent

# Matches ![alt text](path/to/file.svg) where the path is relative (no scheme)
_SVG_IMG_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+\.svg)\)')


def _try_inline(match: re.Match) -> str:
    alt = match.group(1)
    url = match.group(2)

    # Only inline relative paths (skip http/https URLs)
    if url.startswith(('http://', 'https://', 'data:')):
        return match.group(0)

    svg_path = REPO_ROOT / url
    if not svg_path.is_file():
        return match.group(0)

    svg_content = svg_path.read_text(encoding='utf-8')
    data_uri = 'data:image/svg+xml,' + quote(svg_content, safe='')
    return f'![{alt}]({data_uri})'


def main():
    data = json.loads(sys.stdin.read())

    # Walk all string values in the parsed JSON and apply substitution
    def transform(obj):
        if isinstance(obj, str):
            return _SVG_IMG_RE.sub(_try_inline, obj)
        if isinstance(obj, dict):
            return {k: transform(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [transform(item) for item in obj]
        return obj

    data = transform(data)
    sys.stdout.write(json.dumps(data, indent=2))
    sys.stdout.close()


if __name__ == '__main__':
    main()
