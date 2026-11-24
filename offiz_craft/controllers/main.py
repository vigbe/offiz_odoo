# The odoo package is provided by the Odoo server at runtime, not by this
# repository's tooling.
# pyright: reportMissingImports=false
"""Save endpoint of the chatter editor (feature document S4).

``POST /offiz_craft/attachment/<id>/save`` overwrites the attachment's content with the
bytes the editor saved and keeps its name. Gates, in this order: group membership, the
attachment exists, it belongs to a record of a chatter-capable model, the user may write that
record, the payload is valid. Every refusal raises before anything is written, so the
attachment is left untouched. As every Odoo ``jsonrpc`` route, a refusal is an HTTP 200
carrying a JSON-RPC ``error`` whose ``data.name`` is the exception class.
"""

import base64
import binascii
import logging

from odoo import _, http
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

_GROUP_USER = "offiz_craft.group_craft_user"

# Largest file accepted for saving, in bytes. Odoo caps a request body at 128 MiB
# (``max_content_length``, http.py) and base64 inflates it by 4/3, so anything above this
# limit is refused here with a validation error instead of dying as an HTTP 413 earlier.
MAX_SAVE_BYTES = 64 << 20


class CraftEditorController(http.Controller):
    """Receives what the Craft editors save from a record chatter."""

    @http.route(
        "/offiz_craft/attachment/<int:attachment_id>/save",
        type="jsonrpc",
        auth="user",
        methods=["POST"],
    )
    def save_attachment(self, attachment_id, datas, **kwargs):
        if not request.env.user.has_group(_GROUP_USER):
            raise AccessError(_("You are not allowed to edit documents with the Craft editors."))

        attachment = request.env["ir.attachment"].browse(attachment_id).exists()
        if not attachment:
            raise MissingError(_("The attachment does not exist or has been deleted."))

        record = self._chatter_record(attachment)
        if not record.has_access("write"):
            raise AccessError(_("You are not allowed to edit the documents of this record."))

        self._decode(datas)  # validates the payload; the write stores the base64 text as given
        attachment.write({"datas": datas})
        _logger.info("craft: attachment %s overwritten by %s", attachment.id, request.env.user.login)
        return {
            "id": attachment.id,
            "name": attachment.name,
            "checksum": attachment.checksum,
            "file_size": attachment.file_size,
            "res_model": attachment.res_model,
            "res_id": attachment.res_id,
        }

    @staticmethod
    def _chatter_record(attachment):
        """The record the attachment belongs to; it must be able to carry a chatter."""
        if not attachment.res_model or not attachment.res_id:
            raise AccessError(_("This attachment does not belong to a record."))
        model = attachment.res_model
        if model not in request.env or not hasattr(request.env[model], "message_post"):
            raise AccessError(_("The record of this attachment does not support the chatter."))
        record = request.env[model].browse(attachment.res_id).exists()
        if not record:
            raise MissingError(_("The record of this attachment no longer exists."))
        return record

    @staticmethod
    def _decode(datas):
        """The decoded file content; the payload is validated after the access gates."""
        if not isinstance(datas, str):
            raise ValidationError(_("The file content must be sent as base64 text."))
        try:
            content = base64.b64decode(datas, validate=True)
        except (binascii.Error, ValueError) as ex:
            raise ValidationError(_("The file content is not valid base64.")) from ex
        if not content:
            raise ValidationError(_("The file content is empty."))
        if len(content) > MAX_SAVE_BYTES:
            raise ValidationError(
                _("The file is too large to save (limit: %d MiB).", MAX_SAVE_BYTES >> 20)
            )
        return content
