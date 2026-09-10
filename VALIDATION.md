# Validation — September 9, 2026

- Exported all 26 pages discovered from public internal links: homepage, library, 24 tutorials. No discovered source page failed to download.
- `python3 scripts/verify.py`: PASS — all routes, 1,032 local references, unchanged tutorial text, local static dependencies, Intercom configuration.
- `node --check public/site.js`: PASS.
- Desktop homepage at 1728 × 941: original and local heading, introduction, hero image and Osmosis Dex heading bounding boxes matched exactly. Screenshots visually matched.
- Mobile homepage at 390 × 844: original and local screenshots visually matched, including responsive artwork placement and line wrapping.
- Mobile menu: opened, exposed navigation, followed Library successfully.
- Search: “keplr” returned 9 results; combined with Security returned 1; a nonexistent query returned 0 and displayed the original empty-state illustration/message. Clearing restored all 24 results.
- Tutorial at 390px: no horizontal overflow; image dialog opened and closed successfully.
- Intercom script loads, but its service reports the local preview domain is not allowed. Production messenger rendering could not be verified against local files. The original production app ID is preserved.

No DNS, production hosting, Webflow account, or Intercom account settings were changed. Docker configuration was not executed. Visual verification covers the homepage at two sizes and the library/tutorial layouts; it is not an automated pixel-diff of every tutorial. Original article HTML and CSS are retained, with all article text checked against the snapshots.
