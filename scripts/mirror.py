#!/usr/bin/env python3
"""Refresh the public Webflow snapshot. Run only when intentionally re-importing."""
import argparse, concurrent.futures, hashlib, html, json, re, subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://support.osmosis.zone'
PAGES = ROOT / 'source/pages'
ASSETS = ROOT / 'public/assets'
MANIFEST = ROOT / 'source/manifest.json'

class Links(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.links = []; self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('href'): self.links.append(attrs['href'])

def download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['curl', '--fail', '-L', '-sS', '--retry', '2', '--max-time', '60', url, '-o', str(dest)], check=True)

def asset_path(url):
    name = re.sub(r'[^a-zA-Z0-9._-]', '_', unquote(urlsplit(url).path.rsplit('/', 1)[-1]))
    return '/assets/' + hashlib.sha256(url.encode()).hexdigest()[:12] + '-' + name

ASSET_RE = re.compile(r'https://(?:cdn\.prod\.website-files\.com|uploads-ssl\.webflow\.com|assets\.website-files\.com|fonts\.gstatic\.com|d3e54v103j8qbb\.cloudfront\.net|rileyrichter\.github\.io)[^\s"\'<>]*')

def assets_in(text):
    return {html.unescape(u).rstrip(');,') for u in ASSET_RE.findall(text) if urlsplit(u).path and not urlsplit(u).path.endswith('.js')}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh-pages', action='store_true', help='Overwrite source HTML snapshots with freshly downloaded pages')
    args = parser.parse_args()
    PAGES.mkdir(parents=True, exist_ok=True); ASSETS.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {'pages': {}, 'assets': {}, 'unavailable_pages': {}}
    if args.refresh_pages: manifest['pages'] = {}; manifest['unavailable_pages'] = {}
    queue = {'/', '/library'}; visited = set(); assets = set()
    while queue:
        batch = sorted(queue - visited); queue.clear()
        if not batch: break
        def fetch_page(path):
            file = PAGES / ('index.html' if path == '/' else path.strip('/') + '.html')
            if args.refresh_pages or not file.exists(): download(ORIGIN + path, file)
            return path, file
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            jobs = {pool.submit(fetch_page,p): p for p in batch}
            for job in concurrent.futures.as_completed(jobs):
                path = jobs[job]; visited.add(path)
                try: path, file = job.result()
                except subprocess.CalledProcessError:
                    manifest['unavailable_pages'][path] = 'Source returned an HTTP error'; continue
                text = file.read_text(encoding='utf-8'); manifest['pages'][path] = str(file.relative_to(ROOT)); assets.update(assets_in(text))
                for link in Links(text).links:
                    parsed = urlsplit(urljoin(ORIGIN + path, link))
                    if parsed.netloc == urlsplit(ORIGIN).netloc and not Path(parsed.path).suffix:
                        queue.add(parsed.path.rstrip('/') or '/')
                print('PAGE', path, flush=True)
    # Fetch exactly the font families/weights used by the source; no Google Fonts runtime.
    font_url = 'https://fonts.googleapis.com/css2?family=Inter:wght@100;200;300;400;500;600;700;800;900&family=Poppins:wght@100;200;300;400;500;600;700;800;900&display=swap'
    fonts = ROOT / 'source/fonts.css'
    if not fonts.exists(): download(font_url, fonts)
    assets.update(assets_in(fonts.read_text(encoding='utf-8')))
    completed = set()
    while assets - completed:
        batch = sorted(assets - completed)
        def fetch_asset(url):
            local = asset_path(url); dest = ROOT / 'public' / local.lstrip('/')
            if not dest.exists(): download(url, dest)
            return url, local, dest
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            for url, local, dest in pool.map(fetch_asset, batch):
                completed.add(url); manifest['assets'][url] = local
                if dest.suffix == '.css': assets.update(assets_in(dest.read_text(encoding='utf-8')))
        print('ASSETS', len(completed), flush=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f"Saved {len(manifest['pages'])} pages and {len(manifest['assets'])} assets. Unavailable: {manifest['unavailable_pages']}")

if __name__ == '__main__': main()
