# The odoo package is provided by the Odoo server at runtime, not by this
# repository's tooling.
# pyright: reportMissingImports=false
"""Runs the QUnit (JavaScript unit test) suite of ``offiz_craft``.

Odoo 16 has no Hoot yet: ``static/tests/*.js`` files are QUnit tests, listed in the
manifest under ``web.assets_unit_tests`` and loaded by the ``/web/tests`` page together
with every other module's tests. The ``filter`` URL parameter (a QUnit regex) selects
which ones run; the page logs ``test successful`` when the selected tests pass.

Run after fetching the editor builds::

    odoo-bin -d test_db -i offiz_craft --test-enable \
    --test-tags /offiz_craft --stop-after-init --without-demo=all
"""

import odoo.tests
from odoo.addons.web.tests.test_js import WebsuiteCommon, qunit_error_checker


@odoo.tests.tagged("post_install", "-at_install", "standard")
class CraftJsSuite(WebsuiteCommon):

    @odoo.tests.no_retry
    def test_offiz_craft(self):
        self.browser_js(
            "/web/tests?filter=/offiz_craft/",
            "",
            "",
            login="admin",
            timeout=600,
            error_checker=qunit_error_checker,
        )
