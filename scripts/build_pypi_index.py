"""Generate a static PEP 503 simple index from GitHub Release assets.

The index links to release assets, so the published site holds only HTML while
the distributions stay attached to the GitHub Release. Names are normalized per
PEP 503 and each link carries the asset digest as a URL fragment when GitHub
reports one.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

WHEEL_RE = re.compile(r"^(?P<name>.+?)-(?P<version>[0-9][^-]*)-.+\.whl$")
SDIST_RE = re.compile(r"^(?P<name>.+?)-(?P<version>[0-9][^-]*)\.tar\.gz$")


def normalize(project: str) -> str:
    """Return the PEP 503 normalized project name."""
    return re.sub(r"[-_.]+", "-", project).lower()


def distribution_name(filename: str) -> str | None:
    """Return the project name encoded in a wheel or sdist filename."""
    match = WHEEL_RE.match(filename) or SDIST_RE.match(filename)
    if match is None:
        return None
    return match.group("name")


def digest_fragment(asset: dict[str, Any]) -> str:
    """Return a `#sha256=...` fragment when the asset digest is available."""
    digest = asset.get("digest") or ""
    if digest.startswith("sha256:"):
        return f"#sha256={digest.removeprefix('sha256:')}"
    return ""


def collect(releases: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    """Group downloadable assets by normalized project name."""
    projects: dict[str, list[dict[str, str]]] = defaultdict(list)
    for release in releases:
        if release.get("draft"):
            continue
        for asset in release.get("assets") or []:
            filename = asset.get("name") or ""
            project = distribution_name(filename)
            url = asset.get("browser_download_url") or ""
            if project is None or not url:
                continue
            projects[normalize(project)].append(
                {"filename": filename, "url": url, "fragment": digest_fragment(asset)}
            )
    for entries in projects.values():
        entries.sort(key=lambda entry: entry["filename"])
    return dict(sorted(projects.items()))


def project_page(entries: list[dict[str, str]]) -> str:
    """Render one project page listing every available distribution."""
    links = "\n".join(
        f'    <a href="{entry["url"]}{entry["fragment"]}">{entry["filename"]}</a><br>'
        for entry in entries
    )
    return (
        "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\">"
        "<title>Simple index</title></head><body>\n"
        f"{links}\n</body></html>\n"
    )


def root_page(projects: list[str]) -> str:
    """Render the project listing shared by the site root and `simple/`."""
    links = "\n".join(f'    <a href="{name}/">{name}</a><br>' for name in projects)
    return (
        "<!DOCTYPE html>\n<html><head><meta charset=\"utf-8\">"
        "<title>Simple index</title></head><body>\n"
        f"{links}\n</body></html>\n"
    )


def build(releases: list[dict[str, Any]], out: Path) -> list[str]:
    """Write the index tree and return the published project names."""
    projects = collect(releases)
    out.mkdir(parents=True, exist_ok=True)
    # Disable Jekyll so underscore-prefixed and dashed paths are served verbatim.
    (out / ".nojekyll").write_text("", encoding="utf-8")
    listing = root_page(list(projects))
    (out / "index.html").write_text(listing, encoding="utf-8")
    simple = out / "simple"
    simple.mkdir(parents=True, exist_ok=True)
    (simple / "index.html").write_text(listing, encoding="utf-8")
    for name, entries in projects.items():
        target = simple / name
        target.mkdir(parents=True, exist_ok=True)
        (target / "index.html").write_text(project_page(entries), encoding="utf-8")
    return list(projects)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--releases-json", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    releases = json.loads(args.releases_json.read_text(encoding="utf-8"))
    if not isinstance(releases, list):
        raise SystemExit("releases JSON must be a list of release objects")
    projects = build(releases, args.out)
    print(f"indexed {len(projects)} project(s): {', '.join(projects)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
