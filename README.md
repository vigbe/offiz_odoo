# Ofizz Craft — Word / Excel / PowerPoint / PDF in Odoo

Edit the documents attached to any record's chatter straight from the browser and save
them back to Odoo. No document server: the editors are the official web builds of the
[ArtCraft](https://getartcraft.com/) apps (Rust compiled to WebAssembly), and Odoo serves
their files and stores the documents.

Formats: `.docx .odt .rtf .html .md .txt` (WordCraft) · `.xlsx` (GridCraft) ·
`.pptx` (DeckCraft) · `.pdf` (PdfCraft).

Everything about setup, permissions, limits and licenses is in
[offiz_craft/README.md](offiz_craft/README.md). The short version: Odoo 15, then run
`offiz_craft/scripts/fetch_web_builds.sh` once to fetch the (pinned, SHA-256-verified)
editor builds.

License: LGPL-3 for the module; the editors keep their own MIT OR Apache-2.0 texts
inside `offiz_craft/static/lib/<app>/`.

## Intellectual-property and maturity notice

Names and trademarks belong to their respective owners. Their use identifies
technologies or compatibility only and does not imply affiliation, sponsorship,
endorsement or commercial partnership.

The editor applications are in alpha. Their status, format support and maturity
should be evaluated separately from the Ofizz Craft integration.

License: LGPL-3 for the Ofizz Craft module. The editor applications retain separate
MIT OR Apache-2.0 licenses, while bundled fonts, dictionaries, icons, OCR models
and other third-party assets retain their own licenses. This does not claim ownership
of the third-party applications or their assets.
