# Rhino 8 Web Graph Prototype

Minimal Rhino 8 Python setup that opens an Eto popup with a `WebView` to preview chart URLs (for example Flourish embed links).

## Project structure

- `scripts/ui_popup.py` - Eto dialog UI with two modes:
  - **Flourish URL** mode (paste/load an embed URL)
  - **Animated Treemap (local)** mode (loads `bin/animated_treemap.html`)
- `scripts/run_button.py` - simple launch script intended for a Rhino toolbar button.
- `scripts/run_button_animated.py` - launcher that opens directly in local animated treemap mode.

## Requirements

- Rhino 8
- RhinoCode CPython (Python 3) runtime
- Public chart URL that allows embedding (Flourish embed links are a common starting point)

## Run from Rhino command line

Use:

`_-RunPythonScript "C:\Users\Matea.Pinjusic\Documents\datacharts\scripts\run_button.py"`

You can also assign the same command to a Rhino toolbar button.

For direct local animated treemap mode:

`_-RunPythonScript "C:\Users\Matea.Pinjusic\Documents\datacharts\scripts\run_button_animated.py"`

## Usage

1. Run `run_button.py` from Rhino.
2. Choose mode:
   - **Flourish URL** for external embed links
   - **Animated Treemap (local)** to load `bin/animated_treemap.html`
3. In URL mode, paste your chart URL into the textbox.
4. Click **Load URL** (or **Load Treemap** in local mode).
5. Click **Reload** if you update data on the server side.

## Notes

- Use an actual embed URL, not an editor/share page URL.
- Some websites block embedding via CSP or `X-Frame-Options`; if so, the page may not render inside `WebView`.
- `ui_popup.py` includes a placeholder custom-scheme bridge (`myapp://...`) for JS -> Rhino messages.
- `run_button.py` explicitly checks for CPython and stops with a clear message in IronPython.
