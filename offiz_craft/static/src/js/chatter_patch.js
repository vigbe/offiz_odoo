/** @odoo-module */
// Odoo 16 integration: the attachment card is a messaging model (components are thin
// wrappers whose template scope is the record), so the patch extends the model's
// record methods instead of patching a component prototype. The user group is enforced
// server-side by the save route: 16's user service has an async hasGroup, unusable in
// a template expression, so the button's gate here is the file format only.
import { registerPatch } from "@mail/model/model_core";
import { session } from "@web/session";
import { editorFor } from "@offiz_craft/js/craft_router";

const EDITOR_PAGE = "/offiz_craft/static/editor/index.html";
const SAVED_MESSAGE = "offiz_craft:saved";

// The origin thread of the last opened attachment: refreshed after a save in the editor tab.
let clientThread = null;

registerPatch({
    name: "AttachmentCard",
    recordMethods: {
        /**
         * The editor for this attachment, or false (the template's t-if): the format must
         * have one. The save route checks the user group; Odoo 16's async hasGroup cannot
         * gate a template expression.
         */
        craftEditorFor() {
            return editorFor(this.attachment.displayName);
        },

        /** Opens the editor on this attachment in a new tab (feature doc S2, L15). */
        onClickCraftEdit() {
            const editor = editorFor(this.attachment.displayName);
            if (!editor) {
                return;
            }
            clientThread = this.attachment.originThread || null;
            const query = new URLSearchParams({
                attachment_id: String(this.attachment.id),
                name: this.attachment.displayName,
                lang: session.user_context?.lang || "en_US",
            });
            window.open(`${EDITOR_PAGE}?${query}`, "_blank");
        },
    },
});

/** The editor tab reports its saves: refresh the record's chatter (thumbnail, size). */
window.addEventListener("message", (event) => {
    if (event.origin !== window.location.origin || event.source === window) {
        return;
    }
    const data = event.data;
    if (data && data.type === SAVED_MESSAGE && data.res_model && data.res_id) {
        // Odoo 16 has no chatter reload event: re-fetch the thread's attachments, the
        // store re-renders the chatter's attachment box from the fresh data.
        clientThread?.fetchData(["attachments"]);
    }
});
