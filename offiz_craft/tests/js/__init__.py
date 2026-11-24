# Local dev environments do not ship the odoo package; the runtime imports
# are resolved inside the odoo:19 container. Same suppression pattern as the
# sibling `excalidraw_for_odoo` module.
# pyright: reportMissingImports=false
# Imported for its side effect only: Odoo's test loader finds the suite through this import.
from . import python_tests  # noqa: F401
