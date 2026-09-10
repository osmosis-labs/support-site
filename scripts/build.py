#!/usr/bin/env python3
"""Build a portable static site from the checked-in snapshot; no network/dependencies."""
import datetime, html, json, re, shutil
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
ROOT = Path(__file__).resolve().parents[1]
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())

class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []
    def has_class(self, name): return name in self.attrs.get('class', '').split()
    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child, Node): yield from child.walk()
    def remove(self): self.parent.children.remove(self)
    def render(self):
        inside = ''.join(c.render() if isinstance(c, Node) else c for c in self.children)
        if not self.tag: return inside
        attrs = ''.join(' ' + k + ('' if v is None else '="' + html.escape(str(v), quote=True) + '"') for k,v in self.attrs.items())
        return '<' + self.tag + attrs + '>' + ('' if self.tag in VOID else inside + '</' + self.tag + '>')

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=False); self.root = Node(); self.current = self.root; self.feed(text)
    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.current); self.current.children.append(n)
        if tag not in VOID: self.current = n
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag, attrs)
    def handle_endtag(self, tag):
        n = self.current
        while n.parent:
            if n.tag == tag: self.current = n.parent; return
            n = n.parent
    def handle_data(self, data): self.current.children.append(data)
    def handle_entityref(self, name): self.handle_data('&' + name + ';')
    def handle_charref(self, name): self.handle_data('&#' + name + ';')
    def handle_decl(self, decl): self.handle_data('<!' + decl + '>')
    def handle_comment(self, data): pass


def main():
    manifest = json.loads((ROOT / 'source/manifest.json').read_text(encoding='utf-8'))
    dist = ROOT / 'dist'
    if dist.exists(): shutil.rmtree(dist)
    shutil.copytree(ROOT / 'public', dist)
    def localize(text):
        for remote, local in sorted(manifest['assets'].items(), key=lambda item: -len(item[0])):
            text = text.replace(remote, local).replace(html.escape(remote, quote=True), local)
        return text
    for css in (dist / 'assets').glob('*.css'): css.write_text(localize(css.read_text(encoding='utf-8')), encoding='utf-8')
    (dist / 'assets/fonts.css').write_text(localize((ROOT / 'source/fonts.css').read_text(encoding='utf-8')), encoding='utf-8')
    for route, source in manifest['pages'].items():
        doc = Document(localize((ROOT / source).read_text(encoding='utf-8'))); nav_seen = False
        for n in list(doc.root.walk()):
            a = n.attrs
            if n.tag == 'script' or (n.tag == 'meta' and a.get('name') == 'generator') or (n.tag == 'link' and (a.get('rel') == 'preconnect' or 'zoom.css' in a.get('href',''))):
                n.remove(); continue
            if n.has_class('w-nav'):
                if nav_seen: n.remove(); continue
                nav_seen = True
            if 'data-w-id' in a and 'style' in a:
                # Webflow stores entrance animation start values inline. Show final state without its runtime.
                a['style'] = re.sub(r'(?:opacity|(?:-webkit-|-moz-|-ms-)?transform(?:-style)?):[^;]+;?', '', a['style'])
                if not a['style'].strip(): del a['style']
            if n.tag == 'meta' and (a.get('property') == 'og:image' or a.get('name') == 'twitter:image') and a.get('content', '').startswith('/assets/'):
                a['content'] = 'https://support.osmosis.zone' + a['content']
            if n.tag == 'a':
                href = a.get('href', '')
                if href.startswith('https://support.osmosis.zone'): a['href'] = href.removeprefix('https://support.osmosis.zone') or '/'
                if a.get('target') == '_blank': a['rel'] = 'noopener noreferrer'
            if n.has_class('w-nav-button'):
                n.tag = 'button'; a.update({'type':'button','aria-label':'Open menu','aria-expanded':'false','aria-controls':'main-navigation'})
            if n.has_class('w-nav-menu'): a['id'] = 'main-navigation'
            if n.tag == 'input' and a.get('type') == 'checkbox':
                label = next((c for c in n.parent.walk() if c.has_class('tag-label')), None)
                name = ''.join(label.children) if label else 'Filter'
                a.update({'id':'filter-' + name.lower(), 'name':'category', 'value':name, 'aria-label':name})
                if label: label.attrs.pop('for', None)
            if n.has_class('blog-search'): a['aria-label'] = 'Search for topic'
            if n.has_class('results'): a.update({'role':'status','aria-live':'polite'})
            if a.get('fs-cmsfilter-element') == 'results-count': n.children = ['24']
            if a.get('fs-cmsfilter-element') == 'empty': a['hidden'] = None
            if a.get('id') == 'year': n.children = [str(datetime.date.today().year)]
        head = next(n for n in doc.root.walk() if n.tag == 'head')
        head.children.extend(['<link rel="stylesheet" href="/assets/fonts.css">', '<link rel="stylesheet" href="/site.css">', '<script defer src="/site.js"></script>'])
        if not any(n.tag == 'link' and n.attrs.get('rel') == 'canonical' for n in doc.root.walk()):
            head.children.append('<link rel="canonical" href="https://support.osmosis.zone' + route + '">')
        dest = dist / route.strip('/') / 'index.html'; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(doc.root.render(), encoding='utf-8')
    (dist / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>https://support.osmosis.zone' + html.escape(r) + '</loc></url>' for r in sorted(manifest['pages'])) + '</urlset>\n', encoding='utf-8')
    (dist / 'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: https://support.osmosis.zone/sitemap.xml\n', encoding='utf-8')
    print(f"Built {len(manifest['pages'])} pages in dist/ with {len(manifest['assets'])} local assets.")

if __name__ == '__main__': main()
