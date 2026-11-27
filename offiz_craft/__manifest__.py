# Odoo __manifest__.py must be a bare dict literal (read via ast.literal_eval);
# the "useless/unused expression" warnings are unavoidable false positives,
# suppressed below for both ruff (B018) and Pyright.
# pyright: reportUnusedExpression=false
{  # noqa: B018
    "name": "Ofizz Craft",
    "version": "20.0.1.0.0",
    "category": "Productivity",
    "summary": "Edit Word, Excel, PowerPoint and PDF attachments in the browser",
    "description": """
Ofizz Craft
==============

Opens record-chatter attachments in the official WordCraft, GridCraft, DeckCraft
and PdfCraft web builds (Rust compiled to WebAssembly, running entirely in the
browser, in a tab of its own) and saves the result back to the same attachment on
the Odoo server. No document server is involved: Odoo serves the editor assets and
stores the files.

* ``.docx``, ``.odt``, ``.rtf``, ``.html``, ``.md`` and ``.txt`` attachments
  open in WordCraft.
* ``.xlsx`` attachments open in GridCraft.
* ``.pptx`` attachments open in DeckCraft.
* ``.pdf`` attachments open in PdfCraft.
* Saving overwrites the attachment in place.

The bundled editor applications are third-party projects with their own licenses
and trademark restrictions. They are in alpha and are identified by name only;
this module does not claim affiliation with or endorsement by their owners.
    """,
    "author": "Victor Bastías Escobar",
    "website": "https://vicbas.com",
    "support": "contacto@vicbas.com",
    "maintainer": "Victor Bastías Escobar",
    "license": "LGPL-3",
    "depends": [
        "mail",
    ],
    "data": [
        "security/craft_security.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "offiz_craft/static/src/js/craft_router.js",
            "offiz_craft/static/src/xml/chatter_patch.xml",
            "offiz_craft/static/src/js/chatter_patch.js",
        ],
        "web.assets_unit_tests": [
            "offiz_craft/static/tests/**/*",
        ],
    },
    "images": [
        "static/description/thumbnail.png",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
