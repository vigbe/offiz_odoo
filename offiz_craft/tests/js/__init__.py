# The odoo package is provided by the Odoo server at runtime, not by this
# repository's tooling.
# pyright: reportMissingImports=false
# Imported for its side effect only: Odoo's test loader finds the suite through this import.
from . import python_tests  # noqa: F401
