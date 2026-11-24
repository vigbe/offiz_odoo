# Local dev environments do not ship the odoo package; the runtime imports
# are resolved inside the odoo:19 container. Same suppression pattern as the
# sibling `excalidraw_for_odoo` module.
# pyright: reportMissingImports=false
from . import test_chatter, test_host_page, test_save_controller
# Odoo 19 only collects `tests` package attributes whose name starts with `test_`
# (odoo/tests/loader.py _get_tests_modules), hence the alias for the JS-suite runner.
from .js import python_tests as test_python_tests
