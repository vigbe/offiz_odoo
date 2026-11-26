import { AttachmentList } from "@mail/core/common/attachment_list";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";
import { session } from "@web/session";
import { editorFor } from "./craft_router";

const GROUP_USER = "offiz_craft.group_craft_user";
const EDITOR_PAGE = "/offiz_craft/static/editor/index.html";
const SAVED_MESSAGE = "offiz_craft:saved";

// The web client's event bus, taken from the first attachment list rendered (it is the same
// object for every component of the client); it refreshes the chatter after a save in the tab.
let clientEnv = null;

/** "Edit with <App>" on the chatter attachments whose format an editor opens (feature doc S2). */
patch(AttachmentList.prototype, {
    setup() {
        super.setup();
        clientEnv = this.env;
    },

    /** The editor for an attachment, or false (the template's t-if): the format must have one
     * and the user must be allowed to edit documents (the save route checks the same group). */
    craftEditorFor(attachment) {
        if (!user.hasGroup(GROUP_USER)) {
            return false;
        }
        return editorFor(attachment.name);
    },

    /** Opens the editor on the attachment in a new tab (feature doc S2, L15). */
    onClickCraftEdit(attachment) {
        const editor = editorFor(attachment.name);
        if (!editor) {
            return;
        }
        const query = new URLSearchParams({
            attachment_id: String(attachment.id),
            name: attachment.name,
            lang: session.user_context?.lang || "en_US",
        });
        window.open(`${EDITOR_PAGE}?${query}`, "_blank");
    },

    /** Mobile: the same entry in the attachment's Actions dropdown, under the same gate. */
    getActions(attachment) {
        // The patched original is reached with native super (patch() installs the extension
        // methods on a prototype chain); this._super is the legacy widget convention and
        // crashes the render wherever getActions is called.
        const actions = super.getActions(...arguments);
        const editor = this.craftEditorFor(attachment);
        if (editor) {
            actions.push({
                icon: "fa fa-pencil",
                label: _t("Edit with %s", editor.label),
                onSelect: () => this.onClickCraftEdit(attachment),
            });
        }
        return actions;
    },
});

/** The editor tab reports its saves: refresh the record's chatter (thumbnail, size). */
window.addEventListener("message", (event) => {
    if (event.origin !== window.location.origin || event.source === window) {
        return;
    }
    const data = event.data;
    if (data && data.type === SAVED_MESSAGE && data.res_model && data.res_id) {
        clientEnv?.bus.trigger("MAIL:RELOAD-THREAD", { model: data.res_model, id: data.res_id });
    }
});
