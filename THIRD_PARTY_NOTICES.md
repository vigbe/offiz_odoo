# Third-party notices

## Scope

This repository integrates the following official ArtCraft web builds. These
applications are third-party projects; they are not created or owned by the
Ofizz Craft/Odoo integration and retain their respective MIT OR Apache-2.0
licensing terms, copyright notices, attribution files and trademark restrictions.

The Ofizz Craft module itself is licensed under LGPL-3. The licenses below belong
to the editor applications and their bundled dependencies and assets; they do
not expand or replace the module license.

## Editor builds

| App | Pinned version | Release asset | SHA-256 | Source and license |
| --- | --- | --- | --- | --- |
| WordCraft | 0.18.1 | `wordcraft-web-0.18.1.zip` | `3daa7c2d1f209a7eeb2527fcefa3fe31e875848fb1970d68f54edae55fe0bc9f` | [wordcraft](https://github.com/storytold/wordcraft); MIT OR Apache-2.0 |
| PdfCraft | 0.22.0 | `pdfcraft-web-0.22.0.zip` | `5da6db0d6d0d5ae517e9bb62c39eb57285f8befd81ef6555e9a807ccf5da5954` | [pdfcraft](https://github.com/storytold/pdfcraft); MIT OR Apache-2.0 |
| GridCraft | 0.19.1 | `gridcraft-web-0.19.1.zip` | `48c5d1b101befebb3c5ba3b7a14914f01c3207934813ed07dc4251b7ae116a78` | [gridcraft](https://github.com/storytold/gridcraft); MIT OR Apache-2.0 |
| DeckCraft | 0.18.1 | `deckcraft-web-0.18.1.zip` | `3196e537fcfab538aaa2e88584bc74e29bb584459b916ab584ac22fbafe32db5` | [deckcraft](https://github.com/storytold/deckcraft); MIT OR Apache-2.0 |

The fetch script downloads these exact release assets and verifies the SHA-256
before unpacking:

- `offiz_craft/scripts/fetch_web_builds.sh`

The unpacked builds retain the upstream `LICENSE-MIT`, `LICENSE-APACHE`, `NOTICE`
and `ATTRIBUTION.md` files under `offiz_craft/static/lib/<app>/`.

## Intellectual-property notice

Names and trademarks such as ArtCraft, WordCraft, GridCraft, DeckCraft, PdfCraft,
Odoo, Microsoft Office, LibreOffice and ONLYOFFICE belong to their respective
owners. Naming them identifies compatibility or technology only and does not
imply affiliation, sponsorship or endorsement.

The editor applications themselves are in alpha and may have incomplete features,
compatibility limitations or format-loss risks. No trademark or brand assets are
licensed merely by naming their associated products.

## Third-party assets and dependencies

Each official build carries its own upstream notices. In particular, the distributed
builds may include fonts, icons, dictionaries, OCR models, PDF parsing/rendering
code and language data with licenses including SIL OFL 1.1, ISC, BSD, CC0-1.0,
Unicode-3.0 and other terms. The exact required notices are preserved in the
build directories and must not be removed from redistributions.

The Ofizz Craft package is not a claim of ownership over the ArtCraft applications,
their source code, assets, documentation or trademarks.
