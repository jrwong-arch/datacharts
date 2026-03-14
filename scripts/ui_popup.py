# -*- coding: utf-8 -*-
"""Rhino 8 Eto popup for quickly previewing web-based charts."""

import System
import Rhino
import Eto.Forms as forms
import Eto.Drawing as drawing

DEFAULT_URL = "https://public.flourish.studio/visualisation/28056071/"
MODE_URL = "Flourish URL"
MODE_ANIMATED = "Animated Treemap (local server)"
LOCAL_SERVER_TREEMAP_URL = "http://127.0.0.1:8765/bin/animated_treemap.html"
_DIALOG = None


class WebGraphDialog(forms.Form):
    """Simple modeless form that embeds a web page in an Eto WebView."""

    def __init__(self, start_mode=MODE_URL):
        super(WebGraphDialog, self).__init__()

        self.Title = "Web Graph Prototype"
        self.ClientSize = drawing.Size(1100, 760)
        self.Padding = drawing.Padding(10)
        self.Resizable = True

        self.mode_dropdown = forms.DropDown()
        self.mode_dropdown.DataStore = [MODE_URL, MODE_ANIMATED]

        self.url_box = forms.TextBox()
        self.url_box.Text = DEFAULT_URL

        self.load_button = forms.Button()
        self.load_button.Text = "Load URL"

        self.reload_button = forms.Button()
        self.reload_button.Text = "Reload"

        self.close_button = forms.Button()
        self.close_button.Text = "Close"

        self.status_label = forms.Label()
        self.status_label.Text = "Paste an embed URL and click Load URL."
        self.web = forms.WebView()

        self.load_button.Click += self._on_load_clicked
        self.reload_button.Click += self._on_reload_clicked
        self.close_button.Click += self._on_close_clicked
        self.mode_dropdown.SelectedIndexChanged += self._on_mode_changed
        self.web.DocumentLoaded += self._on_document_loaded
        self.web.DocumentLoading += self._on_document_loading

        top_row = forms.StackLayout()
        top_row.Orientation = forms.Orientation.Horizontal
        top_row.Spacing = 6
        top_row.Items.Add(forms.StackLayoutItem(self.mode_dropdown, False))
        top_row.Items.Add(forms.StackLayoutItem(self.url_box, True))
        top_row.Items.Add(forms.StackLayoutItem(self.load_button, False))
        top_row.Items.Add(forms.StackLayoutItem(self.reload_button, False))
        top_row.Items.Add(forms.StackLayoutItem(self.close_button, False))

        header_layout = forms.StackLayout()
        header_layout.Orientation = forms.Orientation.Vertical
        header_layout.Spacing = 8
        header_layout.Items.Add(forms.StackLayoutItem(top_row, False))
        header_layout.Items.Add(forms.StackLayoutItem(self.status_label, False))

        splitter = forms.Splitter()
        splitter.Orientation = forms.Orientation.Vertical
        splitter.FixedPanel = forms.SplitterFixedPanel.Panel1
        splitter.Position = 72
        splitter.Panel1 = header_layout
        splitter.Panel2 = self.web
        self.Content = splitter

        self._set_mode(start_mode)
        self._load_current_url()

    def _load_current_url(self):
        """Navigate WebView to URL currently in textbox."""
        if self._current_mode() == MODE_ANIMATED:
            self._load_local_animated_treemap()
            return

        raw_url = (self.url_box.Text or "").strip()
        if not raw_url:
            self.status_label.Text = "URL is empty."
            return

        try:
            normalized_url = self._normalize_flourish_url(raw_url)
            if normalized_url != raw_url:
                self.url_box.Text = normalized_url

            self.web.Url = System.Uri(normalized_url)
            self.status_label.Text = "Loading..."
        except Exception as exc:
            self.status_label.Text = "Invalid URL: {0}".format(exc)

    def _load_local_animated_treemap(self):
        """Load animated treemap from local HTTP server in the WebView."""
        try:
            self.web.Url = System.Uri(LOCAL_SERVER_TREEMAP_URL)
            self.status_label.Text = "Loading animated treemap from local server..."
        except Exception as exc:
            self.status_label.Text = "Failed to load local server URL: {0}".format(exc)

    @staticmethod
    def _normalize_flourish_url(raw_url):
        """Convert known Flourish public URLs to embed URLs for WebView."""
        lower = raw_url.lower()
        if "public.flourish.studio/visualisation/" in lower and "/embed" not in lower:
            return raw_url.rstrip("/") + "/embed"
        return raw_url

    def _on_load_clicked(self, sender, e):
        self._load_current_url()

    def _on_mode_changed(self, sender, e):
        self._set_mode(self._current_mode())
        self._load_current_url()

    def _on_reload_clicked(self, sender, e):
        try:
            self.web.Reload()
            self.status_label.Text = "Reloading..."
        except Exception as exc:
            self.status_label.Text = "Reload failed: {0}".format(exc)

    def _on_close_clicked(self, sender, e):
        self.Close()

    def _on_document_loaded(self, sender, e):
        self.status_label.Text = "Page loaded."

    def _on_document_loading(self, sender, e):
        # Lightweight JS -> Rhino bridge placeholder.
        # In page JS:
        #   window.location.href = "myapp://eventName?foo=bar";
        uri = e.Uri
        if uri and uri.Scheme and uri.Scheme.lower() == "myapp":
            e.Cancel = True
            self.status_label.Text = "Bridge event: {0}{1}".format(uri.Host, uri.Query)

    def _set_mode(self, mode):
        options = [MODE_URL, MODE_ANIMATED]
        if mode not in options:
            mode = MODE_URL
        self.mode_dropdown.SelectedIndex = options.index(mode)

        is_url_mode = mode == MODE_URL
        self.url_box.Enabled = is_url_mode
        self.load_button.Text = "Load URL" if is_url_mode else "Load Treemap"
        if is_url_mode:
            self.status_label.Text = "Paste an embed URL and click Load URL."
        else:
            self.status_label.Text = "Load animated treemap from http://127.0.0.1:8765."

    def _current_mode(self):
        idx = self.mode_dropdown.SelectedIndex
        return MODE_URL if idx != 1 else MODE_ANIMATED


def show_dialog(start_mode=MODE_URL):
    """Open dialog as Rhino-owned modeless popup."""
    global _DIALOG

    if _DIALOG is not None and _DIALOG.Visible:
        _DIALOG._set_mode(start_mode)
        _DIALOG._load_current_url()
        _DIALOG.BringToFront()
        return

    dlg = WebGraphDialog(start_mode=start_mode)
    dlg.Owner = Rhino.UI.RhinoEtoApp.MainWindow

    def _on_closed(sender, e):
        global _DIALOG
        _DIALOG = None

    dlg.Closed += _on_closed
    Rhino.UI.EtoExtensions.Show(dlg, Rhino.RhinoDoc.ActiveDoc)
    _DIALOG = dlg
