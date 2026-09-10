#!/usr/bin/env python3
"""Re-encode the mirrored raster assets to WebP and shorten their filenames.

Run once after `mirror.py`, then commit the result. `build.py` stays offline and
dependency-free; this is an import-time step, like the mirror itself.

The mirror keeps Webflow's original PNGs, which is 130 MB of git history for a
24-article site. It also keeps Webflow's filenames, and a handful of those are
long enough (123 characters) that the repository will not check out on Windows
inside a moderately deep path.

Both problems are fixed by rewriting `source/manifest.json`: every reference in
the page snapshots is a remote URL that `build.py` maps through the manifest, so
changing the local path there is enough — no HTML is touched.

Sizes are unchanged. Webflow's responsive variants (`-p-500`, `-p-800`) are
separate assets with their own manifest entries, so the `srcset` widths in the
snapshots stay honest.

    python scripts/optimize.py [--quality 85] [--dry-run]

Requires Pillow (`pip install Pillow`). Safe to re-run: assets already converted
are left alone.
"""
import argparse, json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'public/assets'
MANIFEST = ROOT / 'source/manifest.json'

CONVERT = {'.png', '.jpg', '.jpeg'}
# 12-char hash + hyphen + this + '.webp' keeps every path well inside the
# Windows limit while staying readable in a diff.
NAME_BUDGET = 40


def shorten(local):
    """`/assets/<hash>-<very long webflow name>.png` -> `/assets/<hash>-<trimmed>.webp`"""
    stem = Path(local).stem
    prefix, _, rest = stem.partition('-')
    return f'/assets/{prefix}-{rest[:NAME_BUDGET].rstrip("._-")}.webp'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--quality', type=int, default=85, help='WebP quality (default 85)')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    assets = manifest['assets']

    converted = skipped = 0
    before = after = 0
    taken = {v for v in assets.values()}
    failures = []

    for url, local in list(assets.items()):
        if Path(local).suffix.lower() not in CONVERT:
            continue
        src = ROOT / 'public' / local.lstrip('/')
        if not src.is_file():
            failures.append(f'missing source for {local}')
            continue

        target_local = shorten(local)
        if target_local != local and target_local in taken:
            failures.append(f'name collision on {target_local}')
            continue
        dest = ROOT / 'public' / target_local.lstrip('/')

        if dest.is_file() and dest != src:
            skipped += 1
            assets[url] = target_local
            continue

        original = src.stat().st_size
        if args.dry_run:
            converted += 1
            before += original
            continue

        try:
            with Image.open(src) as im:
                # Palette images with transparency need RGBA to survive the trip.
                im = im.convert('RGBA' if im.mode in ('P', 'LA', 'RGBA') else 'RGB')
                im.save(dest, 'WEBP', quality=args.quality, method=6)
        except Exception as err:  # a corrupt or unsupported source should not be silent
            failures.append(f'{local}: {err}')
            continue

        src.unlink()
        taken.discard(local)
        taken.add(target_local)
        assets[url] = target_local
        converted += 1
        before += original
        after += dest.stat().st_size

    if not args.dry_run:
        MANIFEST.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

    mb = lambda n: n / 1024 / 1024
    print(f'{"[dry run] " if args.dry_run else ""}{converted} converted, {skipped} already WebP')
    if after:
        print(f'{mb(before):.1f} MB -> {mb(after):.1f} MB ({100 - after / before * 100:.0f}% smaller)')
    longest = max(len(Path(v).name) for v in assets.values())
    print(f'longest asset filename: {longest} characters')
    if failures:
        print(f'\n{len(failures)} failures:\n  ' + '\n  '.join(failures))
        raise SystemExit(1)


if __name__ == '__main__':
    main()
