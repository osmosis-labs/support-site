#!/usr/bin/env python3
"""Check all exported routes, content, images/srcsets, CSS fonts and scripts offline."""
import json, re
from pathlib import Path
from urllib.parse import unquote, urlsplit
from build import Document, ROOT

manifest = json.loads((ROOT / 'source/manifest.json').read_text(encoding='utf-8'))
dist = ROOT / 'dist'
errors = []; checked = 0

def reference(url, base):
    global checked
    p = urlsplit(url)
    if p.scheme or p.netloc or not p.path: return
    target = dist / unquote(p.path).lstrip('/') if p.path.startswith('/') else base.parent / unquote(p.path)
    checked += 1
    if not target.is_file() and not (target / 'index.html').is_file(): errors.append(f'{base.relative_to(dist)}: missing {url}')

for route, source in manifest['pages'].items():
    path = dist / route.strip('/') / 'index.html'
    if not path.exists(): errors.append('Missing route ' + route); continue
    text = path.read_text(encoding='utf-8'); doc = Document(text)
    nodes = list(doc.root.walk())
    assert sum(n.has_class('w-nav') for n in nodes) == 1, route + ': duplicate navigation'
    assert any(n.tag == 'h1' for n in nodes), route + ': missing heading'
    original = Document((ROOT / source).read_text(encoding='utf-8'))
    # The article bodies must survive migration verbatim, apart from asset URLs and link rels.
    def article_text(tree):
        def words(n): return ''.join(words(c) if hasattr(c,'tag') else c for c in n.children)
        return [words(n) for n in tree.root.walk() if n.has_class('article-text')]
    assert article_text(original) == article_text(doc), route + ': article content changed'
    for n in nodes:
        for key in ('src','poster','href'):
            url = n.attrs.get(key,'')
            reference(url,path)
            if n.tag in ('script','img','source') and key=='src' and url.startswith('http'): errors.append(f'{route}: external asset {url}')
            if n.tag=='link' and n.attrs.get('rel')=='stylesheet' and url.startswith('http'): errors.append(f'{route}: external stylesheet {url}')
        for item in n.attrs.get('srcset','').split(','):
            if item.strip(): reference(item.strip().split()[0],path)
        for url in re.findall(r'url\([\"\']?([^\)\"\']+)', n.attrs.get('style','')): reference(url,path)
    assert not re.search(r'<script[^>]*src="https?://',text), route + ': remote runtime'
for path in dist.rglob('*.css'):
    for url in re.findall(r'url\([\"\']?([^\)\"\']+)',path.read_text(encoding='utf-8')):
        if url.startswith('http'): errors.append('External CSS asset ' + url)
        reference(url,path)
assert 'uco7rjff' in (dist/'site.js').read_text(encoding='utf-8'), 'Missing existing Intercom integration'
if errors: raise SystemExit('\n'.join(errors))
print(f'PASS: {len(manifest["pages"])} routes, unchanged tutorial text, {checked} local references, no hosted static dependencies, Intercom configured.')
