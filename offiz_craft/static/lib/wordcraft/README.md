# WordCraft web build — vendored payload (not committed)

This directory holds the **official WordCraft web build, as released**, served by Odoo as
static files at `/offiz_craft/static/lib/wordcraft/`. The payload (~58 MiB, mostly the
WASM binary) is git-ignored (`.gitignore`); this `README.md` is the only tracked file.

| | |
|---|---|
| App | [WordCraft](https://github.com/storytold/wordcraft) (`<app>` = `wordcraft` in the host protocol) |
| Version | 0.18.1 |
| Asset | `wordcraft-web-0.18.1.zip` (22,536,015 bytes; `wordcraft-web-bc9cdbc0b42827ee_bg.wasm` = 60,994,261 bytes) |
| SHA-256 | `3daa7c2d1f209a7eeb2527fcefa3fe31e875848fb1970d68f54edae55fe0bc9f` |
| Release URL | https://github.com/storytold/wordcraft/releases/download/v0.18.1/wordcraft-web-0.18.1.zip |
| Published sums | https://github.com/storytold/wordcraft/releases/download/v0.18.1/SHA256SUMS.txt |
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
The bundled fonts and language data keep their own licenses (`OFL-*.txt`, `ATTRIBUTION.md`).

## Entry point

`index.html?host=parent&author=<urlencoded name>` — host-bridge protocol v1 (`wordcraft:ready`,
`wordcraft:open`, `wordcraft:save`, `wordcraft:dirty`, `wordcraft:failed`), as documented in
the build's own `HOSTING.md` ("The parent bridge") and in `odd/tasks/craft-for-odoo.md`
(entry L7). The page command API is `window.wordcraft` (`request`, `execute`, `commands`,
`docInspect`, `uiInspect`, `screenshot`; every function returns a Promise).

Hosting requirements (see `HOSTING.md`, "Required server settings"): `.wasm` served as
`application/wasm` and `.js` as `text/javascript`, which Odoo's static route does; no
COOP/COEP header is needed. `static/test/host.html` is the standalone roundtrip page that
drives this build through the bridge.
