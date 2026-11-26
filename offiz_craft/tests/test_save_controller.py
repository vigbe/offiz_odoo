# The odoo package is provided by the Odoo server at runtime, not by this
# repository's tooling.
# pyright: reportMissingImports=false
"""Save endpoint of the chatter editor (feature document S4), through HTTP.

Every refusal is a JSON-RPC ``error`` (Odoo ``jsonrpc`` routes answer HTTP 200) whose
``data.name`` names the exception class; every refusal leaves the attachment untouched.
"""

import base64
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from odoo.addons.offiz_craft.controllers import main as controller_main
from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger

FIXTURES = Path(__file__).parent / "fixtures"
ORIGINAL_PDF = (FIXTURES / "sample.pdf").read_bytes()
SAVE_ROUTE = "/offiz_craft/attachment/%s/save"


def _b64(data):
    return base64.b64encode(data).decode()


@tagged("post_install", "-at_install", "standard")
class TestSaveController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # What the editor would save: the document with a few more bytes.
        cls.new_pdf = ORIGINAL_PDF + b"% overwritten by the editor\n"
        cls.partner = cls.env["res.partner"].create({"name": "Craft save test"})
        cls.attachment = cls.env["ir.attachment"].create(
            {
                "name": "report.pdf",
                "datas": _b64(ORIGINAL_PDF),
                "res_model": "res.partner",
                "res_id": cls.partner.id,
            }
        )
        # An internal user (group_craft_user is implied by base.group_user) who belongs to the
        # one group a record rule targets: that user may read the partner but never write it.
        readonly_group = cls.env["res.groups"].create({"name": "craft: partner read-only"})
        cls.editor = cls.env["res.users"].create(
            {
                "name": "Craft editor",
                "login": "craft_editor",
                "password": "craft_editor",
                "groups_id": [(6, 0, [cls.env.ref("base.group_user").id, readonly_group.id])],
            }
        )
        cls.env["ir.rule"].create(
            {
                "name": "craft: partner read-only",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "groups": [(6, 0, [readonly_group.id])],
                "domain_force": f"[('id', '=', {cls.partner.id})]",
                "perm_read": True,
                "perm_write": False,
                "perm_create": True,
                "perm_unlink": True,
            }
        )
        # A portal user never has group_craft_user.
        cls.env["res.users"].create(
            {
                "name": "Portal outsider",
                "login": "craft_outsider",
                "password": "craft_outsider",
                "groups_id": [(6, 0, [cls.env.ref("base.group_portal").id])],
            }
        )

    def _save(self, login, attachment_id, datas):
        self.authenticate(login, login)
        # Odoo 18's url_open() has no json= argument (added in 19): post the JSON-RPC
        # envelope by hand.
        response = self.url_open(
            SAVE_ROUTE % attachment_id,
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": {"datas": datas}}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    @staticmethod
    def _error_name(payload):
        assert "error" in payload, payload
        return payload["error"]["data"]["name"]

    @staticmethod
    def _error_text(payload):
        return payload["error"]["data"].get("message") or payload["error"]["data"].get("exception") or ""

    def _unchanged(self):
        attachment = self.attachment
        self.assertEqual(base64.b64decode(attachment.datas), ORIGINAL_PDF)
        self.assertEqual(attachment.name, "report.pdf")

    def test_save_overwrites_the_attachment(self):
        payload = self._save("admin", self.attachment.id, _b64(self.new_pdf))
        result = payload["result"]
        self.assertEqual(result["name"], "report.pdf")
        # ir.attachment.checksum is a SHA-1 of the content.
        self.assertEqual(result["checksum"], hashlib.sha1(self.new_pdf).hexdigest())
        self.assertEqual(result["file_size"], len(self.new_pdf))
        self.assertEqual(result["res_model"], "res.partner")
        self.assertEqual(result["res_id"], self.partner.id)
        attachment = self.attachment
        attachment.invalidate_cache()
        self.assertEqual(base64.b64decode(attachment.datas), self.new_pdf)
        self.assertEqual(attachment.name, "report.pdf")
        # Odoo 15 does not bump write_date when only datas changes (verified empirically):
        # the content, checksum and file_size above carry the proof of the save.

    def test_user_without_group_is_refused(self):
        with mute_logger("odoo.http"):
            payload = self._save("craft_outsider", self.attachment.id, _b64(self.new_pdf))
        self.assertEqual(self._error_name(payload), "odoo.exceptions.AccessError")
        self.assertIn("not allowed to edit documents", self._error_text(payload))
        self._unchanged()

    def test_unknown_attachment_is_refused(self):
        with mute_logger("odoo.http"):
            payload = self._save("admin", 999999999, _b64(self.new_pdf))
        self.assertEqual(self._error_name(payload), "odoo.exceptions.MissingError")

    def test_attachment_without_record_is_refused(self):
        loose = self.env["ir.attachment"].create({"name": "loose.pdf", "datas": _b64(ORIGINAL_PDF)})
        with mute_logger("odoo.http"):
            payload = self._save("admin", loose.id, _b64(self.new_pdf))
        self.assertEqual(self._error_name(payload), "odoo.exceptions.AccessError")
        self.assertEqual(base64.b64decode(loose.datas), ORIGINAL_PDF)

    def test_attachment_on_model_without_chatter_is_refused(self):
        country = self.env.ref("base.be")
        attached = self.env["ir.attachment"].create(
            {"name": "belgium.pdf", "datas": _b64(ORIGINAL_PDF), "res_model": "res.country", "res_id": country.id}
        )
        with mute_logger("odoo.http"):
            payload = self._save("admin", attached.id, _b64(self.new_pdf))
        self.assertEqual(self._error_name(payload), "odoo.exceptions.AccessError")
        self.assertEqual(base64.b64decode(attached.datas), ORIGINAL_PDF)

    def test_record_write_denied_is_refused(self):
        with mute_logger("odoo.http"):
            payload = self._save("craft_editor", self.attachment.id, _b64(self.new_pdf))
        self.assertEqual(self._error_name(payload), "odoo.exceptions.AccessError")
        # The refusal is the record gate, not the group gate nor Odoo's attachment ACL.
        self.assertIn("not allowed to edit the documents of this record", self._error_text(payload))
        self._unchanged()

    def test_access_is_checked_before_the_payload(self):
        # A user who may not write the record is refused even when the payload is invalid:
        # the gates run in the documented order.
        with mute_logger("odoo.http"):
            payload = self._save("craft_editor", self.attachment.id, "not*base64")
        self.assertEqual(self._error_name(payload), "odoo.exceptions.AccessError")
        self._unchanged()

    def test_invalid_payload_is_refused(self):
        # Not base64, empty, or not a string at all.
        for datas in ("not*base64", "", 42):
            with self.subTest(datas=datas), mute_logger("odoo.http"):
                payload = self._save("admin", self.attachment.id, datas)
            self.assertEqual(self._error_name(payload), "odoo.exceptions.ValidationError")
            self._unchanged()

    def test_oversized_payload_is_refused(self):
        with patch.object(controller_main, "MAX_SAVE_BYTES", 8), mute_logger("odoo.http"):
            payload = self._save("admin", self.attachment.id, _b64(self.new_pdf))
        self.assertEqual(self._error_name(payload), "odoo.exceptions.ValidationError")
        self._unchanged()
