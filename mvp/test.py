import json, os, threading
import scriptcontext as sc
import Rhino, Rhino.Display as rd, System.Drawing as sd, System.IO, System
from http.server import HTTPServer, SimpleHTTPRequestHandler

SERVE_DIR   = r"C:\Users\Dell\Documents\GitHub\dataviz"
OUTPUT_JSON = os.path.join(SERVE_DIR, "gh_dashboard.json")

# writing data
message = str(globals().get("text_input") or "Hello Hackathon")
with open(OUTPUT_JSON, "w") as f:
    json.dump({"message": message}, f)

# hosting the server
if "GH_VP_STARTED" not in sc.sticky:
    class _H(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=SERVE_DIR, **kw)
        def do_POST(self):
            if self.path == "/screenshot":
                n = int(self.headers.get("Content-Length", 0))
                sc.sticky["GH_VP_PNG_BYTES"] = self.rfile.read(n) 
                self.send_response(200)
                self.end_headers()
                sc.sticky["GH_VP_NEEDS_REDRAW"] = True
        def log_message(self, *a): pass

    threading.Thread(target=lambda: HTTPServer(("", 8080), _H).serve_forever(), daemon=True).start()
    sc.sticky["GH_VP_STARTED"] = True

# converting the chart into a rhino bitmap
if "GH_VP_IDLE" not in sc.sticky:
    def _idle(sender, e):
        if sc.sticky.get("GH_VP_NEEDS_REDRAW"):
            sc.sticky["GH_VP_NEEDS_REDRAW"] = False
            data = sc.sticky.get("GH_VP_PNG_BYTES")
            if data:
                ms = System.IO.MemoryStream(System.Array[System.Byte](data))
                sc.sticky["GH_VP_BMP"] = rd.DisplayBitmap(sd.Bitmap(ms))
            Rhino.RhinoDoc.ActiveDoc.Views.Redraw()
            
    Rhino.RhinoApp.Idle += _idle
    sc.sticky["GH_VP_IDLE"] = _idle

# draw the bitmap
if "GH_VP_CH" in sc.sticky:
    rd.DisplayPipeline.DrawForeground -= sc.sticky["GH_VP_CH"]
    
def _draw(sender, e):
    if "GH_VP_BMP" in sc.sticky:
        e.Display.DrawBitmap(sc.sticky["GH_VP_BMP"], 20, 60)
        
rd.DisplayPipeline.DrawForeground += _draw
sc.sticky["GH_VP_CH"] = _draw