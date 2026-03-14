# -*- coding: utf-8 -*-
"""Rhino button entrypoint script for opening animated treemap mode."""

import os
import sys
import importlib

THIS_DIR = os.path.dirname(__file__)
if THIS_DIR not in sys.path:
    sys.path.append(THIS_DIR)

import ui_popup

# Always reload to pick up the newest edits during prototyping.
importlib.reload(ui_popup)


def _ensure_cpython():
    """Guard against running this script in legacy IronPython."""
    if getattr(sys.implementation, "name", "") != "cpython":
        message = (
            "This script is intended for Rhino 8 CPython (Python 3). "
            "Please run it from RhinoCode/Python 3."
        )
        try:
            import Rhino

            Rhino.RhinoApp.WriteLine(message)
        except Exception:
            pass
        raise RuntimeError(message)


if __name__ == "__main__":
    _ensure_cpython()
    ui_popup.show_dialog(start_mode=ui_popup.MODE_ANIMATED)
