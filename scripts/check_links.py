#!/usr/bin/env python3
"""Check Markdown links in site content without external dependencies."""

from __future__ import annotations

import argparse
import re
import ssl
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)\s]+|/[^)\s]+)\)")
CONTENT_GLOBS = ("*.md", "_includes/*.md", "_data/*.yml")
SKIP_HOSTS = {"doi.org", "scholar.google.com"}
BOT_HOSTILE_HOSTS = {
    "indico.cern.ch",
    "indico.cfnssbu.physics.sunysb.edu",
    "indico.desy.de",
    "indico.ectstar.eu",
}


def iter_links(root: Path):
    for pattern in CONTENT_GLOBS:
        for path in sorted(root.glob(pattern)):
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for match in LINK_RE.finditer(line):
                    yield path, number, match.group(1)


def check_local(root: Path, url: str) -> tuple[bool, str]:
    target = url.split("#", 1)[0].strip("/")
    if not target:
        return True, "local"

    candidates = [
        root / target,
        root / f"{target}.md",
        root / target / "index.md",
        root / target / "index.html",
    ]
    return any(path.exists() for path in candidates), "local"


def check_remote(url: str, timeout: float, context: ssl.SSLContext) -> tuple[bool, str]:
    host = urlparse(url).netloc.lower()
    if host in SKIP_HOSTS:
        return True, "skipped"

    headers = {"User-Agent": "Mozilla/5.0 link checker for vskokov.github.io"}
    for method in ("HEAD", "GET"):
        request = Request(url, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout, context=context) as response:
                status = response.getcode()
                return status < 400, str(status)
        except HTTPError as error:
            if method == "HEAD":
                continue
            if host in BOT_HOSTILE_HOSTS and error.code in {400, 403, 404}:
                return True, f"browser-required:{error.code}"
            return False, str(error.code)
        except (TimeoutError, URLError) as error:
            if method == "HEAD":
                continue
            if host in BOT_HOSTILE_HOSTS:
                return True, f"browser-required:{error.__class__.__name__}"
            return False, error.__class__.__name__

    return False, "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--timeout", type=float, default=12.0)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    context = ssl.create_default_context()
    failures: list[str] = []
    checked: set[str] = set()

    for path, line, url in iter_links(root):
        if url in checked:
            continue
        checked.add(url)

        if url.startswith("/"):
            ok, detail = check_local(root, url)
        else:
            ok, detail = check_remote(url, args.timeout, context)

        status = "OK" if ok else "FAIL"
        print(f"{status:4} {detail:12} {path.relative_to(root)}:{line} {url}")
        if not ok:
            failures.append(f"{path.relative_to(root)}:{line} {url} ({detail})")

    if failures:
        print("\nBroken links:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"\nChecked {len(checked)} unique links.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
