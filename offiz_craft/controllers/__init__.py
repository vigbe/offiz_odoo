# Local dev environments do not ship the odoo package; the runtime imports
# are resolved inside the odoo:19 container. Same suppression pattern as the
# sibling `excalidraw_for_odoo` module.
# pyright: reportMissingImports=false
from . import main
