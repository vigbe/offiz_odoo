/** @odoo-module */
/** The Craft editor that opens a chatter attachment, by file extension (feature doc S3). */

const PDFCRAFT = { app: "pdfcraft", label: "PdfCraft" };
const WORDCRAFT = { app: "wordcraft", label: "WordCraft" };
const GRIDCRAFT = { app: "gridcraft", label: "GridCraft" };
const DECKCRAFT = { app: "deckcraft", label: "DeckCraft" };

// extension (lower case) → editor: one row per format, for the formats the app opens and saves.
// a new editor (spreadsheets, presentations) is one more block of rows here.
const EDITOR_BY_EXTENSION = new Map([
    ["pdf", PDFCRAFT],
    ["docx", WORDCRAFT],
    ["odt", WORDCRAFT],
    ["rtf", WORDCRAFT],
    ["html", WORDCRAFT],
    ["md", WORDCRAFT],
    ["txt", WORDCRAFT],
    // GridCraft opens and saves .xlsx workbooks.
    ["xlsx", GRIDCRAFT],
    // DeckCraft opens and saves .pptx presentations (legacy .ppt only opens, so not here).
    ["pptx", DECKCRAFT],
]);

/**
 * @param {string|undefined|null} fileName
 * @returns {{app: string, label: string}|false} the editor for the file's extension, else false
 */
export function editorFor(fileName) {
    if (typeof fileName !== "string") {
        return false;
    }
    const dot = fileName.lastIndexOf(".");
    // No extension, or a dot-file such as ".txt" (nothing before the dot).
    if (dot <= 0) {
        return false;
    }
    return EDITOR_BY_EXTENSION.get(fileName.slice(dot + 1).toLowerCase()) || false;
}
