/**
 * Host side of the craft-web-host protocol (v1) between an Odoo page and a Craft web build
 * framed in an <iframe> on the same origin (feature document, log L7).
 *
 * The build is loaded with `?host=parent` and posts `{type: "<app>:<kind>", ...}` messages to
 * its parent; the host answers with `<app>:open` / `<app>:saved`. Only messages from our own
 * frame and origin are accepted, as the build does on its side.
 */

export const CRAFT_LIB_URL = "/offiz_craft/static/lib";

// The apps whose page command API is opted in with `?control` (WordCraft always has it).
const CONTROL_OPT_IN = new Set(["pdfcraft"]);

// Largest file the builds accept to open (bytes).
export const MAX_OPEN_BYTES = 512 << 20;

export class CraftBridge {
    /**
     * @param {object} options
     * @param {"wordcraft"|"pdfcraft"} options.app
     * @param {HTMLIFrameElement} options.iframe the frame the build is loaded into
     * @param {string} options.author display name passed to the build (`?author=`)
     * @param {(ready: {version: string, appVersion: string, file: boolean}) => void} [options.onReady]
     * @param {(save: {name: string, saveAs: boolean, id?: string, bytes: ArrayBuffer}) => void} [options.onSave]
     * @param {(dirty: boolean) => void} [options.onDirty]
     * @param {(error: string, id?: string) => void} [options.onFailed]
     */
    constructor({ app, iframe, author, onReady, onSave, onDirty, onFailed }) {
        this.app = app;
        this.iframe = iframe;
        this.author = author;
        this.onReady = onReady || (() => {});
        this.onSave = onSave || (() => {});
        this.onDirty = onDirty || (() => {});
        this.onFailed = onFailed || (() => {});
        this.ready = false;
        this._onMessage = this._onMessage.bind(this);
    }

    /** URL of the build in host mode. */
    get url() {
        const query = new URLSearchParams({ host: "parent", author: this.author });
        if (CONTROL_OPT_IN.has(this.app)) {
            query.set("control", "");
        }
        return `${CRAFT_LIB_URL}/${this.app}/index.html?${query}`;
    }

    /** Starts listening and loads the build; `onReady` follows once it runs. */
    load() {
        window.addEventListener("message", this._onMessage);
        this.iframe.src = this.url;
    }

    /** Opens a document, as File › Open would. Only after `ready`. */
    open(name, bytes) {
        if (!this.ready) {
            throw new Error(`${this.app} is not ready`);
        }
        this._send({ type: `${this.app}:open`, name, bytes });
    }

    /** Runs a command of the build's page command API (same-origin `window.<app>`). */
    async execute(command, params) {
        const api = this.iframe.contentWindow && this.iframe.contentWindow[this.app];
        if (!api || typeof api.execute !== "function") {
            throw new Error(`${this.app}: page command API not installed`);
        }
        return api.execute(command, params);
    }

    /** Stops listening; the build keeps running until its frame is removed. */
    destroy() {
        window.removeEventListener("message", this._onMessage);
    }

    _send(message) {
        this.iframe.contentWindow.postMessage(message, window.location.origin);
    }

    _onMessage(event) {
        // Bridge rule: only our frame, only our own origin.
        if (event.source !== this.iframe.contentWindow || event.origin !== window.location.origin) {
            return;
        }
        const data = event.data;
        const prefix = `${this.app}:`;
        if (!data || typeof data.type !== "string" || !data.type.startsWith(prefix)) {
            return;
        }
        switch (data.type.slice(prefix.length)) {
            case "ready":
                this.ready = true;
                this.onReady({ version: data.version, appVersion: data.appVersion, file: data.file });
                break;
            case "save":
                // A save that carries an id waits for this acknowledgement.
                if (data.id !== undefined) {
                    this._send({ type: `${this.app}:saved`, id: data.id });
                }
                this.onSave({ name: data.name, saveAs: Boolean(data.saveAs), id: data.id, bytes: data.bytes });
                break;
            case "dirty":
                this.onDirty(Boolean(data.dirty));
                break;
            case "failed":
                this.onFailed(String(data.error || "failed"), data.id);
                break;
            default:
                break; // handoff, or anything newer than this host
        }
    }
}
