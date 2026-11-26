# The odoo package is provided by the Odoo server at runtime, not by this
# repository's tooling.
# pyright: reportMissingImports=false
"""Chatter integration (T3/T4/T7, S2-S4), in headless Chrome against the real web client.

A record with ``.docx``, ``.pdf`` and ``.png`` attachments offers "Edit with WordCraft" and
"Edit with PdfCraft" only on the first two; the action opens the editor page in a new tab
(``window.open``) with the attachment id, its name and the user language. On that page, editing
the ``.docx`` in WordCraft and saving there overwrites the attachment on the server, under its
name.
"""

import base64
import json
from pathlib import Path

from odoo.tests import HttpCase, tagged

FIXTURES = Path(__file__).parent / "fixtures"
EDITOR_PAGE = "/offiz_craft/static/editor/index.html"
# 1x1 RGB PNG (69 bytes), built with zlib + struct; verified with `file`.
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)

OPEN_EDITOR_TAB_JS = r"""
(async () => {
    const check = (condition, message) => { if (!condition) { throw new Error(message); } };
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const waitFor = async (probe, message, ms = 30000) => {
        const started = performance.now();
        let value;
        while (!(value = probe())) {
            check(performance.now() - started < ms, message);
            await sleep(100);
        }
        return value;
    };
    // The chatter's "Files" box (the AttachmentList) is folded until its button is clicked, and
    // the button ignores the click until the thread's attachments have arrived (count badge).
    // That arrival re-renders the button, so it is looked up again on every poll.
    let openBox = null;
    const loaded = performance.now();
    while (!(openBox = document.querySelector(".o_ChatterTopbar_buttonAttachmentsCount"))) {
        check(performance.now() - loaded < 30000, "the chatter's attachment count never appeared");
        await sleep(100);
    }
    check(openBox.textContent.trim() === "3", "attachment count: " + openBox.textContent);
    // The button re-renders when the attachments arrive: click the fresh button until the
    // Files box stays open.
    const boxSelector = ".o_Chatter_attachmentBox .o_AttachmentList_attachment";
    const openedAt = performance.now();
    while (!document.querySelector(boxSelector)) {
        check(performance.now() - openedAt < 30000, "the Files box did not open");
        const attachButton = document.querySelector(".o_ChatterTopbar_buttonAttachments");
        if (attachButton && !attachButton.disabled && !attachButton.querySelector(".fa-spin")) {
            attachButton.click();
        }
        await sleep(100);
    }
    const buttons = [...document.querySelectorAll(".o_AttachmentCard [data-craft-editor]")];
    const apps = buttons.map((button) => button.dataset.craftEditor).sort();
    check(JSON.stringify(apps) === JSON.stringify(["pdfcraft", "wordcraft"]),
        "editors offered: " + JSON.stringify(apps));
    check(document.querySelectorAll(".o_Chatter_attachmentBox .o_AttachmentList_attachment").length === 3,
        "the chatter should list the 3 attachments");
    // The action opens a tab: capture the call instead of opening a target headless Chrome
    // would not drive. The store re-renders the card list on updates: click the fresh
    // button until the tab opens, not a stale node.
    const opened = [];
    window.open = (url, target) => { opened.push({ url, target }); return null; };
    const clickedAt = performance.now();
    while (opened.length === 0) {
        check(performance.now() - clickedAt < 30000, "window.open calls: " + opened.length);
        const pdfButton = document.querySelector('[data-craft-editor="pdfcraft"]');
        if (pdfButton) {
            pdfButton.click();
        }
        await sleep(100);
    }
    check(opened.length === 1, "window.open calls: " + opened.length);
    check(!document.querySelector(".o_craft_editor_dialog"), "a dialog opened instead of a tab");
    // The tab is the editor page for that attachment, with its name and the user language.
    const url = new URL(opened[0].url, location.origin);
    check(opened[0].target === "_blank", "target: " + opened[0].target);
    check(url.origin === location.origin && url.pathname === %(editor_page)s, "url: " + opened[0].url);
    check(url.searchParams.get("attachment_id") === %(attachment_id)s, "attachment_id: " + url.searchParams.get("attachment_id"));
    check(url.searchParams.get("name") === %(name)s, "name: " + url.searchParams.get("name"));
    check(url.searchParams.get("lang") === "en_US", "lang: " + url.searchParams.get("lang"));
    console.log("test successful");
})()
"""

EDIT_AND_SAVE_JS = r"""
(async () => {
    const check = (condition, message) => { if (!condition) { throw new Error(message); } };
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const waitFor = async (probe, message, ms = 120000) => {
        const started = performance.now();
        let value;
        while (!(value = probe())) {
            check(performance.now() - started < ms, message);
            await sleep(100);
        }
        return value;
    };
    const status = () => document.getElementById("status").dataset.text || "";
    await waitFor(() => status() === "Opened" || status().startsWith("Error"), "status: " + status());
    check(status() === "Opened", "status: " + status());
    // Make a change through WordCraft's page command API, then the Save button.
    const api = document.getElementById("frame").contentWindow.wordcraft;
    check(api && typeof api.execute === "function", "no page command API");
    await api.execute("text.insert", { text: "Ofizz Craft saved this." });
    await waitFor(() => !document.getElementById("dirty").hidden, "the document did not become dirty");
    const save = document.getElementById("save");
    check(!save.disabled, "the Save button is disabled while there are unsaved changes");
    save.click();
    await waitFor(() => status() === "Saved" || status().startsWith("Error"), "status: " + status());
    check(status() === "Saved", "status: " + status());
    check(document.getElementById("dirty").hidden, "still dirty after saving");
    console.log("test successful");
})()
"""

AUTOSAVE_JS = r"""
(async () => {
    const check = (condition, message) => { if (!condition) { throw new Error(message); } };
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const waitFor = async (probe, message, ms = 120000) => {
        const started = performance.now();
        let value;
        while (!(value = probe())) {
            check(performance.now() - started < ms, message);
            await sleep(100);
        }
        return value;
    };
    const status = () => document.getElementById("status").dataset.text || "";
    await waitFor(() => status() === "Opened" || status().startsWith("Error"), "status: " + status());
    check(status() === "Opened", "status: " + status());
    const api = document.getElementById("frame").contentWindow.wordcraft;
    await api.execute("text.insert", { text: "Ofizz Craft autosaved this." });
    await waitFor(() => !document.getElementById("dirty").hidden, "the document did not become dirty");
    // Nobody clicks Save: the page saves by itself (autosave=1 in the URL).
    await waitFor(() => status() === "Saved" || status().startsWith("Error"), "status: " + status());
    check(status() === "Saved", "status: " + status());
    console.log("test successful");
})()
"""

CLOSE_PROMPT_JS = r"""
(async () => {
    const check = (condition, message) => { if (!condition) { throw new Error(message); } };
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const waitFor = async (probe, message, ms = 120000) => {
        const started = performance.now();
        let value;
        while (!(value = probe())) {
            check(performance.now() - started < ms, message);
            await sleep(100);
        }
        return value;
    };
    const status = () => document.getElementById("status").dataset.text || "";
    const seen = () => `status=${JSON.stringify(status())} html=${document.getElementById("status").outerHTML} lang=${document.documentElement.lang} title=${document.title} module=${window.__craftModuleRan} href=${location.href} frames=${document.querySelectorAll("iframe").length} ready=${document.readyState}`;
    await waitFor(() => status() === "Abierto" || status().startsWith("Error"), seen());
    check(document.title.startsWith("Editando documento"), "title: " + document.title);
    check(document.getElementById("title").textContent === "Editando documento", "header: " + document.getElementById("title").textContent);
    const api = document.getElementById("frame").contentWindow.wordcraft;
    await api.execute("text.insert", { text: "unsaved" });
    await waitFor(() => !document.getElementById("dirty").hidden, "the document did not become dirty");
    // This tab was not opened by script: observe the close instead of closing.
    let closed = false;
    window.close = () => { closed = true; };
    document.getElementById("close").click();
    await waitFor(() => document.getElementById("close-dialog").open, "the close question did not appear");
    const question = document.getElementById("close-question").textContent;
    check(question === "¿Guardar los cambios en línea antes de cerrar?", "question: " + question);
    check(document.getElementById("close-yes").textContent === "Sí" && document.getElementById("close-no").textContent === "No", "buttons");
    check(document.getElementById("dont-show-again-label").textContent === "No volver a mostrar", "remember label");
    document.getElementById("close-no").click();
    await waitFor(() => closed, "closing after \"No\" did not happen");
    check(!document.getElementById("close-dialog").open, "the question is still shown");
    console.log("test successful");
})()
"""


EXPORT_DOWNLOAD_JS = r"""
(async () => {
    const check = (condition, message) => { if (!condition) { throw new Error(message); } };
    const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
    const waitFor = async (probe, message, ms = 120000) => {
        const started = performance.now();
        let value;
        while (!(value = probe())) {
            check(performance.now() - started < ms, message);
            await sleep(100);
        }
        return value;
    };
    const status = () => document.getElementById("status").dataset.text || "";
    // Downloads are observed, not written to disk.
    const downloads = [];
    const named = () => downloads.filter((d) => d.name).map((d) => d.name);
    URL.createObjectURL = (blob) => { downloads.push({ size: blob.size, type: blob.type }); return "blob:test"; };
    URL.revokeObjectURL = () => {};
    HTMLAnchorElement.prototype.click = function () { downloads.push({ name: this.download }); };
    await waitFor(() => status() === "Opened" || status().startsWith("Error"), "status: " + status());
    check(status() === "Opened", "status: " + status());
    const api = document.getElementById("frame").contentWindow.wordcraft;
    await api.execute("text.insert", { text: "Ofizz Craft exports this." });
    await waitFor(() => !document.getElementById("dirty").hidden, "the document did not become dirty");
    // Export as PDF: a copy (the document stays the .docx), downloaded, not stored on the record.
    await api.execute("file.saveAs", { path: "letter.pdf" });
    await waitFor(() => status().startsWith("Downloaded") || status().startsWith("Error"), "status: " + status());
    check(status() === "Downloaded: letter.pdf", "status: " + status());
    const pdf = downloads.find((d) => d.type === "application/pdf");
    check(pdf && pdf.size > 100, "pdf copy: " + JSON.stringify(downloads));
    // Save As .odt: the document becomes that file; its saves are copies too.
    await api.execute("file.saveAs", { path: "letter.odt" });
    await waitFor(() => named().includes("letter.odt") || status().startsWith("Error"), "downloads: " + JSON.stringify(downloads));
    check(status() === "Downloaded: letter.odt", "status: " + status());
    // Autosave (1 s here) stays paused while the document is the .odt: nothing more is downloaded
    // until Save is clicked.
    await api.execute("text.insert", { text: "more" });
    await waitFor(() => !document.getElementById("dirty").hidden, "the document did not become dirty again");
    await sleep(4000);
    check(JSON.stringify(named()) === JSON.stringify(["letter.pdf", "letter.odt"]), "downloaded by autosave: " + JSON.stringify(named()));
    document.getElementById("save").click();
    await waitFor(() => named().length === 3, "Save did not download: " + JSON.stringify(named()));
    check(named()[2] === "letter.odt", "third download: " + JSON.stringify(named()));
    console.log("test successful");
})()
"""


@tagged("post_install", "-at_install", "standard")
class TestChatter(HttpCase):

    def _partner_with_attachments(self):
        partner = self.env["res.partner"].create({"name": "Craft chatter test"})
        # ir.attachment.datas is base64: encode the file content before writing it.
        files = [
            ("letter.docx", (FIXTURES / "sample.docx").read_bytes(), False),
            ("report.pdf", (FIXTURES / "sample.pdf").read_bytes(), False),
            ("image.png", PNG_1X1, True),
        ]
        attachments = self.env["ir.attachment"].create(
            [
                {
                    "name": name,
                    "datas": base64.b64encode(content),
                    "res_model": "res.partner",
                    "res_id": partner.id,
                    **({"mimetype": "image/png"} if is_png else {}),
                }
                for name, content, is_png in files
            ]
        )
        return partner, attachments

    def test_edit_action_opens_the_editor_tab(self):
        partner, attachments = self._partner_with_attachments()
        report = attachments.filtered(lambda a: a.name == "report.pdf")
        self.browser_js(
            url_path=f"/web#id={partner.id}&model=res.partner&view_type=form",
            code=OPEN_EDITOR_TAB_JS % {
                "editor_page": json.dumps(EDITOR_PAGE),
                "attachment_id": json.dumps(str(report.id)),
                "name": json.dumps("report.pdf"),
            },
            ready="document.querySelector('.o_ChatterTopbar_buttonAttachments') !== null",
            login="admin",
            timeout=300,
        )

    def _open_editor(self, letter, code, user="admin", lang="en_US", extra=""):
        self.browser_js(
            url_path=f"{EDITOR_PAGE}?attachment_id={letter.id}&name=letter.docx&lang={lang}{extra}",
            code=code,
            ready="window.__craftModuleRan === true",
            login=user,
            timeout=300,
        )

    @staticmethod
    def _saved_letter(letter, original):
        letter.invalidate_cache()
        saved = base64.b64decode(letter.datas)
        assert saved != original, "the attachment did not change"
        assert saved.startswith(b"PK"), "the saved file is not a .docx"
        assert letter.name == "letter.docx"
        assert letter.mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def test_edit_and_save_updates_the_attachment(self):
        _partner, attachments = self._partner_with_attachments()
        letter = attachments.filtered(lambda a: a.name == "letter.docx")
        original = base64.b64decode(letter.datas)
        self._open_editor(letter, EDIT_AND_SAVE_JS, extra="&autosave=0")
        # The save went through the controller, in this transaction.
        self._saved_letter(letter, original)

    def test_autosave_updates_the_attachment(self):
        _partner, attachments = self._partner_with_attachments()
        letter = attachments.filtered(lambda a: a.name == "letter.docx")
        original = base64.b64decode(letter.datas)
        self._open_editor(letter, AUTOSAVE_JS, extra="&autosave=1")
        self._saved_letter(letter, original)

    def test_export_in_another_format_downloads_a_copy(self):
        _partner, attachments = self._partner_with_attachments()
        letter = attachments.filtered(lambda a: a.name == "letter.docx")
        original = base64.b64decode(letter.datas)
        self._open_editor(letter, EXPORT_DOWNLOAD_JS, extra="&autosave=1")
        # The record keeps its file: only the copy was downloaded.
        letter.invalidate_cache()
        self.assertEqual(base64.b64decode(letter.datas), original)

    def test_close_with_unsaved_changes_asks_in_spanish(self):
        _partner, attachments = self._partner_with_attachments()
        letter = attachments.filtered(lambda a: a.name == "letter.docx")
        original = base64.b64decode(letter.datas)
        # The Odoo tab passes the user's language in the URL: Spanish here.
        self._open_editor(letter, CLOSE_PROMPT_JS, lang="es", extra="&autosave=0")
        # "No" discards: nothing reached the server.
        letter.invalidate_cache()
        self.assertEqual(base64.b64decode(letter.datas), original)
