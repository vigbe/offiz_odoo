# Ofizz Craft

Edit the documents attached to any record's chatter **in the browser**: Word, Excel,
PowerPoint and PDF, saved straight back to Odoo. No document server, no external
service — the editors are the official web builds of the ArtCraft apps (Rust compiled
to WebAssembly) and Odoo stores the files.

## What it does

| Attachment format | Opens in |
| --- | --- |
| `.docx` `.odt` `.rtf` `.html` `.md` `.txt` | [WordCraft](https://github.com/storytold/wordcraft) |
| `.xlsx` | [GridCraft](https://github.com/storytold/gridcraft) |
| `.pptx` | [DeckCraft](https://github.com/storytold/deckcraft) |
| `.pdf` | [PdfCraft](https://github.com/storytold/pdfcraft) |

* In the chatter of any record, open the **Files** box: every attachment with one of
  these formats gets an *"Edit with …"* action that opens the editor in a new tab.
* The editor loads with the document; **saving overwrites the same attachment** on the
  record (same name, new content) and the chatter refreshes.
* The tab saves by itself: 10 s after a change while there are unsaved changes, plus a
  **Save** button. Closing with unsaved changes asks first
  (*"¿Guardar los cambios en línea antes de cerrar?"*, with a *do not ask again* box).
* *Save As / Export* to another format (PDF, PNG, ODT…) **downloads the copy** to share
  it; the record keeps its original file.
* The editor interfaces are localized by the apps themselves (they follow the browser
  language, Spanish included); this module's own texts follow the user's Odoo language
  (English and Spanish shipped).

## Permissions and safety

* Every internal user can edit by default (group *Ofizz Craft / User*); remove the group
  from a user to withdraw the tool — the button disappears and the save route refuses.
* Saves go through one route with the usual Odoo gates: group, attachment exists,
  belongs to a record with a chatter, the user may write that record, payload limits
  (64 MiB). Every refusal leaves the file untouched.

## Requirements and setup

* Odoo 18.
* The editors are about 200 MB of WebAssembly and are **not committed**; fetch them once
  from the repository root after cloning:

      offiz_craft/scripts/fetch_web_builds.sh

  The script downloads the pinned release assets, verifies each SHA-256 against the
  published sums, and unpacks them under `offiz_craft/static/lib/<app>/`. Re-run it when
  the pinned versions change.
* Browsers need WebGL2 (the editors render with it).
* Behind a reverse proxy, allow request bodies of at least ~90 MB (saves travel as
  base64; the module caps files at 64 MiB).

## Limits

* The editors are alpha software (as their own READMEs state); they run sandboxed in an
  iframe inside their tab, so a failure only affects that tab.
* Saving overwrites — there is no version history.
* Legacy `.ppt`, `.ods` and `.csv` get no editor: the apps only open them (or do not
  support them), and a format that cannot be saved back would leave the document
  stranded.

## Tests

The module ships its test suite: the protocol roundtrip of the four editors, the format
router (unit tests), the chatter integration in a browser and every gate of the save
route. After fetching the editor builds, run it with Odoo's own test flags:

    odoo-bin -d test_db -i offiz_craft --test-enable --test-tags /offiz_craft \
        --stop-after-init --without-demo

## Licenses and credits

* This module: **LGPL-3** (see `LICENSE`), © Victor Bastías Escobar — https://vicbas.com
* The editors are © ArtCraft / the storytold authors, dual-licensed **MIT OR Apache-2.0**
  with their license texts and `NOTICE` traveling inside each build under
  `static/lib/<app>/`. The ArtCraft name and logos are trademarks of their owner and are
  not part of those licenses: this module only integrates the apps and names them to
  identify them, without claiming any affiliation.

## Adding editors

Every Craft app with a web build follows the same host protocol. Adding one is a block
of rows in `static/src/js/craft_router.js`, one entry in the `BUILDS` table of
`scripts/fetch_web_builds.sh`, and the `?control` opt-in in `static/src/js/craft_bridge.js`
when that app needs it (only PdfCraft does today).

## Intellectual-property and maturity notice

Names and trademarks belong to their respective owners. Their use identifies
technologies or compatibility only and does not imply affiliation, sponsorship,
endorsement or commercial partnership.

The editor applications are in alpha. Their status, format support and maturity
should be evaluated separately from the Ofizz Craft integration. Keep this status
visible in publications and releases.

The Ofizz Craft module is LGPL-3. The editor applications retain separate MIT OR
Apache-2.0 licenses, and bundled fonts, dictionaries, icons, OCR models and other
third-party assets retain their own licenses. The licenses do not make every part
of the ecosystem a creation or property of the Ofizz Craft author.
