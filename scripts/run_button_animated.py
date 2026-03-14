# -*- coding: utf-8 -*-
"""Rhino button entrypoint script for opening animated treemap mode."""

import os
import sys
import importlib
import time
import subprocess
import urllib.request
import urllib.error

THIS_DIR = os.path.dirname(__file__)
if THIS_DIR not in sys.path:
    sys.path.append(THIS_DIR)

import ui_popup

# Always reload to pick up the newest edits during prototyping.
importlib.reload(ui_popup)


HEALTHCHECK_URL = "http://127.0.0.1:8765/tree_map/data.json"
SERVER_SCRIPT = os.path.join(THIS_DIR, "local_server.py")


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


def _write_rhino_line(text):
    try:
        import Rhino

        Rhino.RhinoApp.WriteLine(text)
    except Exception:
        pass


def _server_is_alive():
    try:
        with urllib.request.urlopen(HEALTHCHECK_URL, timeout=0.8) as response:
            return response.status == 200
    except Exception:
        return False


def _start_local_server_if_needed():
    """Start local server only when health endpoint is unavailable."""
    if _server_is_alive():
        return True

    if not os.path.exists(SERVER_SCRIPT):
        _write_rhino_line("Missing local server script: {0}".format(SERVER_SCRIPT))
        return False

    creation_flags = 0
    if sys.platform.startswith("win"):
        creation_flags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )

    try:
        subprocess.Popen(
            [sys.executable, SERVER_SCRIPT],
            cwd=os.path.abspath(os.path.join(THIS_DIR, "..")),
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        _write_rhino_line("Failed to start local server: {0}".format(exc))
        return False

    # Give server a short startup window and confirm health endpoint.
    for _ in range(20):
        if _server_is_alive():
            _write_rhino_line("Local treemap server started.")
            return True
        time.sleep(0.2)

    _write_rhino_line(
        "Local server did not become ready. Start manually: {0}".format(SERVER_SCRIPT)
    )
    return False


if __name__ == "__main__":
    _ensure_cpython()
    _start_local_server_if_needed()
    ui_popup.show_dialog(start_mode=ui_popup.MODE_ANIMATED)
