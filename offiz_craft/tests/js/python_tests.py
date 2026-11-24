# Local dev environments do not ship the odoo package; the runtime imports
# are resolved inside the odoo:19 container. Same suppression pattern as the
# sibling `excalidraw_for_odoo` module.
# pyright: reportMissingImports=false
"""Runs the Hoot (JavaScript unit test) suite of ``offiz_craft`` (T3, S3).

The suite is the set of ``static/tests/*.test.js`` files, listed in the manifest under
``web.assets_unit_tests``. Every test module of an addon is tagged ``@<addon>``; the
``id`` URL parameter is the hash of that tag, the way Odoo 19's own ``HOOTCommon``
selects the jobs to run (``/web/tests?headless&loglevel=2&preset=desktop&id=<hash>``).

Run from the repository root::

    docker compose run --rm odoo -d offiz_test -u offiz_craft --test-enable \\
        --test-tags /offiz_craft --stop-after-init --without-demo=True
"""

import odoo.tests
from odoo.addons.web.tests.test_js import HOOTCommon, unit_test_error_checker

HOOT_TAG = "@offiz_craft"


@odoo.tests.tagged("post_install", "-at_install", "standard")
class CraftJsSuite(HOOTCommon):

    @odoo.tests.no_retry
    def test_offiz_craft(self):
        self.browser_js(
            f"/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&id={self._generate_hash(HOOT_TAG)}",
            "",
            "",
            login="admin",
            timeout=600,
            success_signal="[HOOT] Test suite succeeded",
            error_checker=unit_test_error_checker,
        )
