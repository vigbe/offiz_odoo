/** @odoo-module */
// QUnit version of the router table (Odoo 17 has no Hoot; the /web/tests page
// loads this file through web.assets_unit_tests — see tests/js/python_tests.py).
import { editorFor } from "@offiz_craft/js/craft_router";

const PDFCRAFT = { app: "pdfcraft", label: "PdfCraft" };
const WORDCRAFT = { app: "wordcraft", label: "WordCraft" };
const GRIDCRAFT = { app: "gridcraft", label: "GridCraft" };
const DECKCRAFT = { app: "deckcraft", label: "DeckCraft" };

// fileName: the editor that opens it, or false when no editor handles its format
const CASES = [
    // .pdf opens in PdfCraft, whatever the case of the extension
    ["report.pdf", PDFCRAFT],
    ["REPORT.PDF", PDFCRAFT],
    ["v1.2.report.Pdf", PDFCRAFT],
    // .docx .odt .rtf .html .md .txt open in WordCraft
    ["letter.docx", WORDCRAFT],
    ["letter.odt", WORDCRAFT],
    ["letter.rtf", WORDCRAFT],
    ["page.html", WORDCRAFT],
    ["notes.md", WORDCRAFT],
    ["notes.txt", WORDCRAFT],
    ["Letter.DocX", WORDCRAFT],
    ["readme.MD", WORDCRAFT],
    // .xlsx opens in GridCraft, .pptx in DeckCraft
    ["budget.xlsx", GRIDCRAFT],
    ["Budget.XLSX", GRIDCRAFT],
    ["quarterly.pptx", DECKCRAFT],
    ["ROADMAP.PPTX", DECKCRAFT],
    // formats the apps only open (legacy .ppt) or do not handle get no editor
    ["image.png", false],
    ["sheet.ods", false],
    ["data.csv", false],
    ["legacy.ppt", false],
    ["setup.exe", false],
    ["archive.tar.gz", false],
    ["report.pdf.exe", false],
    ["file.pdf ", false],
    // no extension gets no editor
    ["README", false],
    [".txt", false],
    ["", false],
    // no file name at all gets no editor
    [undefined, false],
    [null, false],
    [42, false],
];

QUnit.module("offiz_craft", () => {
    QUnit.test("editorFor(fileName)", (assert) => {
        for (const [fileName, expected] of CASES) {
            assert.deepEqual(
                editorFor(fileName),
                expected,
                `editorFor(${JSON.stringify(fileName)})`
            );
        }
    });
});
