# Osmosis Support Lab — static replica

A self-hosted copy of https://support.osmosis.zone, captured September 9, 2026. Includes the homepage, library, all 24 publicly linked tutorials, and 375 local assets. The original CSS, artwork, responsive image variants, fonts, layouts and article text are retained.

No Webflow account, CMS, database, Node packages, or runtime application server is required. The existing Intercom workspace (`uco7rjff`) is reused. Site content and navigation work without Webflow or Google Fonts requests.

## Preview

Requires Python 3.10 or newer. No Python packages to install.

```sh
python3 scripts/build.py
python3 scripts/serve.py
```

Open http://127.0.0.1:3000. Alternatively, `npm run dev` runs the same commands. Use `python3 scripts/serve.py --port 8080` to change the preview port.

## Deploy

Run `python3 scripts/build.py`, then upload **the contents of `dist/`** to any static web host. Preserve the directories: `/library/index.html` and `/tutorials/<slug>/index.html` keep all existing URLs working. Configure directory indexes and serve `404.html` with HTTP status 404 for missing pages. Do not use an SPA catch-all redirect.

For an existing Nginx server, use the routing in `nginx.conf`, adjust its document root and hostname, and use your normal HTTPS configuration. A Docker option is included:

```sh
docker build -t osmosis-support .
docker run --rm -p 8080:80 osmosis-support
```

The Docker configuration is supplied but was not built in this session. The Python build and local preview were tested.

After deploying and verifying the hosted copy, point `support.osmosis.zone` to that host. Canonical URLs, the sitemap and robots.txt already use that domain. DNS and the existing production site have not been changed.

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

## Verification and scope

```sh
python3 scripts/build.py
python3 scripts/verify.py
```

Verification checks all 26 routes, unchanged tutorial body text, over 1,000 local references (including image srcsets and CSS fonts), absence of remote static assets and scripts in generated pages, and the existing Intercom configuration.

The migration replaces Webflow/jQuery/Finsweet JavaScript with local behavior, removes redundant overlapping homepage navigation copies, and fixes duplicate category input IDs. Entrance-animation initial styles are removed so content remains visible without JavaScript. Layout and article content are retained; the current site's analytics snippet is omitted. External destinations such as the Osmosis app, social channels and the existing Tally support request form remain external links.

The source site's `/sitemap.xml` returned 404. Coverage is all pages discovered by recursively following public internal links from the homepage and library; unlinked or unpublished Webflow pages cannot be inventoried without account access.
