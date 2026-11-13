#!/usr/bin/env python3
"""Copy every level's info/loadmap.png into ./loadmaps/<level-folder>.png.

Usage:
    python3 copy_loadmaps.py <path-to-fh2-mod-folder> [--overrides FILE] [--no-favoritemap]

<path-to-fh2-mod-folder> may be the mod folder (its "levels" subfolder is used)
or the "levels" folder itself.

The contents of ./loadmaps are cleared at the start of every run.

Source image: info/favoritemap.png if it exists (disable with --no-favoritemap),
otherwise info/loadmap.png.

Output name for each level folder, in order of preference:
  1. An entry in the overrides file (JSON: {"<level-folder>": "<output-name>"}),
     used verbatim. Default file: loadmap_overrides.json next to this script.
  2. The level folder name, normalized.

Normalizing means: trim, lowercase, whitespace runs -> "_", and characters
that are invalid in Windows file names are dropped.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

DEFAULT_OVERRIDES = Path(__file__).resolve().parent / "loadmap_overrides.json"
INVALID_CHARS_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def normalize(name: str) -> str:
    name = re.sub(r"\s+", "_", name.strip().lower())
    return INVALID_CHARS_RE.sub("", name)


def load_overrides(path: Path, explicit: bool) -> dict[str, str]:
    if not path.is_file():
        if explicit:
            sys.exit(f"Overrides file not found: {path}")
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        sys.exit(f"Invalid JSON in {path}: {e}")
    if not isinstance(data, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in data.items()
    ):
        sys.exit(f'{path} must be a JSON object of "level-folder": "output-name" strings')
    # Folder names are case-insensitive on Windows.
    return {k.lower(): v.removesuffix(".png") for k, v in data.items()}


def resolve_output_name(level_dir: Path, overrides: dict[str, str]) -> tuple[str, str]:
    """Return (output name without extension, source description)."""
    override = overrides.get(level_dir.name.lower())
    if override:
        return override, "override"
    return normalize(level_dir.name), "folder name"


def main() -> int:
    # Folder/override names may contain accents; never crash on a console that can't print them.
    sys.stdout.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description="Copy FH2 level loadmaps to ./loadmaps")
    parser.add_argument("fh2_folder", type=Path, help="FH2 mod folder or its levels folder")
    parser.add_argument(
        "--overrides",
        type=Path,
        help=f"JSON overrides file (default: {DEFAULT_OVERRIDES.name} next to this script)",
    )
    parser.add_argument(
        "--favoritemap",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="prefer info/favoritemap.png over info/loadmap.png when it exists (default: on)",
    )
    args = parser.parse_args()

    src = args.fh2_folder.resolve()
    if not src.is_dir():
        sys.exit(f"Folder not found: {src}")
    if (src / "levels").is_dir():
        src = src / "levels"

    overrides = load_overrides(args.overrides or DEFAULT_OVERRIDES, args.overrides is not None)

    dest = Path.cwd() / "loadmaps"
    dest.mkdir(exist_ok=True)
    # Clear previous output so stale/renamed loadmaps don't linger.
    for entry in dest.iterdir():
        if entry.is_dir() and not entry.is_symlink():
            shutil.rmtree(entry)
        else:
            entry.unlink()

    used: dict[str, str] = {}  # lowercase output name -> level folder that claimed it
    copied = skipped = conflicts = 0

    for level_dir in sorted(p for p in src.iterdir() if p.is_dir()):
        candidates = ["favoritemap.png", "loadmap.png"] if args.favoritemap else ["loadmap.png"]
        loadmap = next(
            (level_dir / "info" / c for c in candidates if (level_dir / "info" / c).is_file()),
            None,
        )
        if loadmap is None:
            print(f"Skipped  {level_dir.name} (no info/{' or info/'.join(candidates)})")
            skipped += 1
            continue

        out_name, source = resolve_output_name(level_dir, overrides)
        key = out_name.lower()
        if key in used:
            print(
                f"CONFLICT {level_dir.name} -> {out_name}.png already used by "
                f"{used[key]}; add an override for one of them"
            )
            conflicts += 1
            continue
        used[key] = level_dir.name

        shutil.copyfile(loadmap, dest / f"{out_name}.png")
        print(f"Copied   {level_dir.name}/info/{loadmap.name} -> {out_name}.png ({source})")
        copied += 1

    unused = set(overrides) - {p.name.lower() for p in src.iterdir() if p.is_dir()}
    for name in sorted(unused):
        print(f"Warning: override for unknown level folder {name!r}")

    print(f"\nDone: {copied} copied, {skipped} skipped, {conflicts} conflicts. Output: {dest}")
    return 1 if conflicts else 0


if __name__ == "__main__":
    sys.exit(main())
