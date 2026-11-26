# The odoo package is provided by the Odoo server at runtime, not by this
# repository's tooling.
# pyright: reportMissingImports=false
"""Runs the QUnit (JavaScript unit test) suite of ``offiz_craft``.

Odoo 15 has no Hoot: ``static/tests/*.js`` files are QUnit tests, listed in the
manifest under ``web.qunit_suite_tests`` and loaded by the ``/web/tests`` page (which
also loads the backend bundle, so imported source modules resolve). QUnit's native ``filter`` parameter (a regex) selects the module's tests and
``failfast`` stops at the first failure; the page logs ``test successful`` when they
pass.

Run after fetching the editor builds::

    odoo-bin -d test_db -i offiz_craft --test-enable \
    --test-tags /offiz_craft --stop-after-init --without-demo=all
"""

import odoo.tests


@odoo.tests.tagged("post_install", "-at_install", "standard")
class CraftJsSuite(odoo.tests.HttpCase):

    def test_offiz_craft(self):
        self.browser_js(
            "/web/tests?filter=/offiz_craft/&failfast",
            "",
            "",
            login="admin",
            timeout=600,
        )
