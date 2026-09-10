# Osmosis Support Lab — static replica

A self-hosted copy of https://support.osmosis.zone, captured September 9, 2026. Includes the homepage, library, all 24 publicly linked tutorials, and 375 local assets. The original CSS, artwork, responsive image variants, fonts, layouts and article text are retained; artwork is re-encoded to WebP at the same dimensions, which is why the repository is around 19 MB rather than 130 MB.

No Webflow account, CMS, database, Node packages, or runtime application server is required. The existing Intercom workspace (`uco7rjff`) is reused. Site content and navigation work without Webflow or Google Fonts requests.

## Preview

Requires Python 3.10 or newer. Building, serving and verifying need no Python packages; only `scripts/optimize.py` has a dependency. On Windows the interpreter is `python` rather than `python3`.

```sh
python3 scripts/build.py
python3 scripts/serve.py
```

Open http://127.0.0.1:3000. Alternatively, `npm run dev` runs the same commands. Use `python3 scripts/serve.py --port 8080` to change the preview port.

## Deploy

`.github/workflows/deploy.yml` builds and verifies on every push to `main` and publishes `dist/` to GitHub Pages. Pull requests build and verify but do not publish. `public/CNAME` carries the custom domain into the output.

Two things are needed before the first deploy:

- **The repository must be public.** GitHub Pages does not serve private repositories on the `osmosis-labs` plan.
- **Pages must be set to "GitHub Actions"** as its source in repository settings, with HTTPS enforcement enabled once the certificate provisions.

To deploy anywhere else, run `python3 scripts/build.py` and upload **the contents of `dist/`**. Pages are written flat — `library.html`, `tutorials/<slug>.html` — because static hosts serve those at the extension-less URLs the current site uses. A host that only resolves directory indexes would 404, so it needs an `index.html`-style fallback (`try_files $uri $uri.html` in Nginx). Serve `404.html` with HTTP status 404, and do not use an SPA catch-all redirect.

Every internal link and asset reference is relative, so the output works unchanged from a domain root or from a subdirectory — which is what makes the GitHub Pages project URL (`osmosis-labs.github.io/support-site/`) a real preview rather than an unstyled shell. `verify.py` fails the build if a site-absolute reference creeps back in.

`404.html` is the one exception, and deliberately so: it is copied through unprocessed, and a host serves it in place of *any* missing path, so a relative reference in it would resolve against whatever URL the visitor got wrong. Its two references stay site-absolute, which is correct once the site is at a domain root. On a subdirectory preview the 404 page loses its webfont and its Library link — cosmetic, and only there.

For an existing Nginx server, use the routing in `nginx.conf`, adjust its document root and hostname, and use your normal HTTPS configuration. A Docker option is included:

```sh
docker build -t osmosis-support .
docker run --rm -p 8080:80 osmosis-support
```

The Docker configuration is supplied but was not built in this session. The Python build and local preview were tested.

After deploying and verifying the hosted copy, point `support.osmosis.zone` to that host — for GitHub Pages, replace the current `CNAME` to `cdn.webflow.com` with one to `osmosis-labs.github.io`. Canonical URLs, the sitemap and robots.txt already use that domain. Leave the Webflow project published for a rollback window. DNS and the existing production site have not been changed.

## Intercom

`public/site.js` loads the same public Intercom app ID and API base as the current site. Both “Get live support” and “Chat with an expert” open that messenger. Intercom continues to provide its own launcher, branding, conversations and support backend.

The existing Intercom workspace **rejects localhost / 127.0.0.1** with “This domain is not allowed for the Intercom Messenger.” The script loads successfully, but the launcher will not appear on the local preview. To test on a staging hostname, add that hostname to the workspace's allowed domains in Intercom Messenger settings. The existing production hostname remains the intended deployment target. No Intercom account settings were changed, and no test messages were sent.

## Maintain the content

- `source/pages/`: editable HTML page snapshots. Tutorial text is inside `.article-text` elements; titles, summaries, cards and category labels on the library page can be edited directly.
- `source/manifest.json`: route and original-asset mappings.
- `public/assets/`: downloaded source images, stylesheets and fonts.
- `source/fonts.css`: local-font declarations processed by the build.
- `public/site.js` and `public/site.css`: small replacements for hosted navigation, filtering, reading progress and image zoom behavior.
- `scripts/build.py`: offline, deterministic HTML/asset export (except the current footer year).

Edit source files and rebuild; do not edit generated `dist/` files. To add a tutorial, add its HTML file, add its route to the manifest, and add its card to `source/pages/library.html`.

`scripts/mirror.py` is the import tool. It reuses downloaded snapshots and assets so an interrupted import can resume. Use `--refresh-pages` to deliberately fetch the published pages again; this overwrites edits to source page snapshots. Normal builds never contact the original site.

`scripts/optimize.py` runs after an import: it re-encodes the downloaded PNGs and JPEGs to WebP, shortens their filenames, and rewrites `source/manifest.json` to match. It is the only script with a third-party dependency (Pillow), it is never part of a normal build, and its output is committed. Run it whenever `mirror.py` has pulled new raster assets, otherwise the repository grows by the original file sizes.

## Verification and scope

```sh
python3 scripts/build.py
python3 scripts/verify.py
```

Verification checks all 26 routes, unchanged tutorial body text, over 1,000 local references (including image srcsets and CSS fonts), absence of remote static assets and scripts in generated pages, and the existing Intercom configuration.

The migration replaces Webflow/jQuery/Finsweet JavaScript with local behavior, removes redundant overlapping homepage navigation copies, and fixes duplicate category input IDs. Entrance-animation initial styles are removed so content remains visible without JavaScript. Layout and article content are retained; the site's analytics snippet is dropped and not carried over, so Intercom's widget is the only third-party script the pages load. External destinations such as the Osmosis app, social channels and the existing Tally support request form remain external links.

The source site's `/sitemap.xml` returned 404. Coverage is all pages discovered by recursively following public internal links from the homepage and library; unlinked or unpublished Webflow pages cannot be inventoried without account access.
