# PdfCraft web build — vendored payload (not committed)

This directory holds the **official PdfCraft web build, as released**, served by Odoo as
static files at `/offiz_craft/static/lib/pdfcraft/`. The payload (~81 MiB: the WASM
binary, the OCR worker and its models) is git-ignored (`.gitignore`); this `README.md` is
the only tracked file.

| | |
|---|---|
| App | [PdfCraft](https://github.com/storytold/pdfcraft) (`<app>` = `pdfcraft` in the host protocol) |
| Version | 0.22.0 |
| Asset | `pdfcraft-web-0.22.0.zip` (37,379,269 bytes; `pdfcraft-web-c0a95e1af84f3780_bg.wasm` = 69,150,397 bytes) |
| SHA-256 | `5da6db0d6d0d5ae517e9bb62c39eb57285f8befd81ef6555e9a807ccf5da5954` |
| Release URL | https://github.com/storytold/pdfcraft/releases/download/v0.22.0/pdfcraft-web-0.22.0.zip |
| Published sums | https://github.com/storytold/pdfcraft/releases/download/v0.22.0/SHA256SUMS.txt |
| License | MIT OR Apache-2.0, ArtCraft trademarks excluded |

## Fetch command

    offiz_craft/scripts/fetch_web_builds.sh

The script downloads the asset (cache `/tmp/craft-web`, override with `CRAFT_WEB_CACHE`),
verifies the SHA-256 above and unzips it into this directory without the archive's single
top-level directory. The only change to the released tree is the name of its own
`README.md`, unpacked as `UPSTREAM-README.md` so that it does not replace this file. Every
reference inside the build is relative, so nothing else is rewritten. Re-running the
script unpacks the same bytes over the same paths.

## License

`LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE` and `ATTRIBUTION.md` in this directory are the
release's own files. The code is licensed under the MIT License or the Apache License,
Version 2.0, at your option. The ArtCraft name, wordmark and logos are trademarks of the
ArtCraft Team, are not open source and are not covered by those licenses (see `NOTICE`).
Third-party material keeps its own licenses: the PDF backend and its data under
`licenses/` (`hayro*`, ICU4X, CMap, …), the fonts (`ATTRIBUTION.md`) and the text
recognition models in `models/` (CC-BY-SA-4.0, see `models/ATTRIBUTION.txt` and the
`*.LICENCE.txt` files beside them).

## Entry point

`index.html?host=parent&author=<urlencoded name>&control` — host-bridge protocol v1
(`pdfcraft:ready`, `pdfcraft:open`, `pdfcraft:save`, `pdfcraft:dirty`, `pdfcraft:failed`),
as documented in the build's own `HOSTING.md` ("Embedding in a page") and in
`odd/tasks/craft-for-odoo.md` (entry L7). `&control` is opt-in and adds the page command
API: `window.pdfcraft` (the canvas element) gains `request`, `execute`, `commands`,
`docInspect`, `uiInspect` and `screenshot` after `pdfcraft:ready` (every function returns a
Promise).

Hosting requirements (see `HOSTING.md`, "Required server settings"): `.wasm` served as
`application/wasm` and `.js` as `text/javascript`, which Odoo's static route does. The
build also recommends `Cross-Origin-Opener-Policy: same-origin` as hardening; Odoo's static
route sends none, and the header has no effect on the iframe bridge. `static/test/host.html`
is the standalone roundtrip page that drives this build through the bridge.
