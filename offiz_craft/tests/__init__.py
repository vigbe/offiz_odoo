# The odoo package is provided by the Odoo server at runtime, not by this
# repository's tooling.
# pyright: reportMissingImports=false
from . import test_chatter, test_host_page, test_save_controller
# Odoo 19 only collects `tests` package attributes whose name starts with `test_`
# (odoo/tests/loader.py _get_tests_modules), hence the alias for the JS-suite runner.
from .js import python_tests as test_python_tests
