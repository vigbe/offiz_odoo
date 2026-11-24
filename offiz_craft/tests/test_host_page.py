# The odoo package is provided by the Odoo server at runtime, not by this
# repository's tooling.
# pyright: reportMissingImports=false
"""Headless-Chrome proof of the craft-web-host roundtrip inside Odoo's origin (T2, S1/S5).

Drives ``static/test/host.html`` (a plain page without Odoo assets) against the vendored
builds in ``static/lib/<app>/``: the app boots in its iframe and answers ``<app>:ready``,
accepts ``<app>:open`` with a fixture, and hands the saved document back through
``<app>:save`` when its page command API runs ``file.save``.

Run from the repository root (the payloads come from ``scripts/fetch_web_builds.sh``;
``-i`` the first time on a fresh database and ``-u`` afterwards, because Odoo only runs the
at-install tests of the modules it installs or upgrades)::

    odoo-bin -d test_db -i offiz_craft --test-enable \
    --test-tags /offiz_craft --stop-after-init --without-demo
"""

import json

from odoo.tests import HttpCase, tagged

HOST_PAGE = "/offiz_craft/static/test/host.html"
FIXTURE_URL = "/offiz_craft/static/test/fixtures/%s"
# 61-69 MB of WASM compiled by headless Chrome under SwiftShader (observed: about 0.3 s).
BOOT_TIMEOUT = 180
SETTLE_SECONDS = 3
CALL_TIMEOUT = 30

# app: fixture, the page command that makes the document dirty (none for a PDF), the
# magic bytes of a valid saved file.
APPS = {
    "wordcraft": {"fixture": "sample.docx", "edit": ("text.insert", {"text": "Ofizz Craft roundtrip"}), "magic": "PK\x03\x04"},
    "pdfcraft": {"fixture": "sample.pdf", "edit": None, "magic": "%PDF"},
    "gridcraft": {"fixture": "sample.xlsx", "edit": None, "magic": "PK\x03\x04"},
    "deckcraft": {"fixture": "sample.pptx", "edit": None, "magic": "PK\x03\x04"},
}

ROUNDTRIP_JS = r"""
(async () => {
    const app = %(app)s;
    const fixture = %(fixture)s;
    const edit = %(edit)s;
    const magic = %(magic)s;
    const check = (condition, message) => { if (!condition) { throw new Error(app + ": " + message); } };
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const host = window.craftHost;
    const kinds = () => host.messages.map((message) => message.type);

    // 1. Boot: framed with ?host=parent, the app answers <app>:ready (protocol v1, reading bytes).
    await host.load(app, %(boot_timeout_ms)d);
    check(host.ready === true, "no " + app + ":ready");
    const ready = host.messages.find((message) => message.type === app + ":ready");
    check(ready && String(ready.version) === "1", "not protocol version 1: " + JSON.stringify(ready));
    check(ready && ready.file === false, "the app did not ask for bytes: " + JSON.stringify(ready));

    // 2. Open: the fixture goes through <app>:open and nothing answers <app>:failed.
    check((await host.openUrl(fixture)) === true, "the fixture was queued instead of sent");
    await sleep(%(settle_ms)d);
    check(kinds().indexOf(app + ":failed") === -1, "failed: " + JSON.stringify(host.messages));

    // 3. Edit, when the app has a command for it: the document becomes dirty.
    if (edit) {
        const result = await host.execute(edit[0], edit[1]);
        check(!result || result.ok !== false, "edit rejected: " + JSON.stringify(result));
        check(host.dirty === true, "the document is not dirty after the edit");
    }

    // 4. Save: file.save hands the bytes back through <app>:save, under the opened name.
    const saved = host.waitForSave(%(call_timeout)d * 1000);
    const result = await host.execute("file.save");
    check(!result || result.ok !== false, "file.save rejected: " + JSON.stringify(result));
    const save = await saved;
    check(save, "no " + app + ":save within %(call_timeout)d s");
    check(save.name === fixture.split("/").pop(), "saved as " + save.name + ", not as the opened file");
    check(save.saveAs === false, "reported as a Save As");
    check(save.size > 0, "empty bytes");
    const bytes = new Uint8Array(await (await fetch(save.url)).arrayBuffer());
    const head = String.fromCharCode.apply(null, bytes.subarray(0, magic.length));
    check(head === magic, "the saved bytes do not start with " + JSON.stringify(magic));
    console.log("test successful");
})()
"""


@tagged("post_install", "-at_install", "standard")
class TestHostPage(HttpCase):
    """One roundtrip per editor: boot, open, (edit), save."""

    def test_wordcraft_roundtrip(self):
        self._roundtrip("wordcraft")

    def test_pdfcraft_roundtrip(self):
        self._roundtrip("pdfcraft")

    def test_gridcraft_roundtrip(self):
        self._roundtrip("gridcraft")

    def test_deckcraft_roundtrip(self):
        self._roundtrip("deckcraft")

    def _roundtrip(self, app):
        config = APPS[app]
        code = ROUNDTRIP_JS % {
            "app": json.dumps(app),
            "fixture": json.dumps(FIXTURE_URL % config["fixture"]),
            "edit": json.dumps(config["edit"]),
            "magic": json.dumps(config["magic"]),
            "boot_timeout_ms": BOOT_TIMEOUT * 1000,
            "settle_ms": SETTLE_SECONDS * 1000,
            "call_timeout": CALL_TIMEOUT,
        }
        self.browser_js(
            url_path=HOST_PAGE,
            code=code,
            ready="typeof window.craftHost === 'object'",
            timeout=BOOT_TIMEOUT + SETTLE_SECONDS + 2 * CALL_TIMEOUT + 30,
        )
