"""Inline data.json into the dashboard template -> index.html + index_offline.html.

Run this after build_data.py. The dashboard is deliberately a single
self-contained file (no server, no CORS problems opening it from disk), so the
data has to be baked in rather than fetched. This script does that baking, so
the page stays in sync with the pipeline instead of drifting.

  index.html          fonts + Chart.js from CDN, ~70 KB, best typography
  index_offline.html  everything vendored, ~270 KB, ZERO external requests
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
tpl = (HERE / "_template.html").read_text(encoding="utf-8")
data = (HERE / "data.json").read_text(encoding="utf-8").replace("</script>", "<\\/script>")

online = tpl.replace("__DATA__", data)
(HERE / "index.html").write_text(online, encoding="utf-8")
print(f"  index.html          {len(online)/1024:>6.0f} KB")

chart = (HERE / "vendor" / "chart.umd.js").read_text(encoding="utf-8")
off = online.replace(
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>',
    "<script>/* Chart.js 4.4.1 UMD, vendored for offline use */\n" + chart + "\n</script>")
off = re.sub(r'<link rel="preconnect"[^>]*>\s*', "", off)
off = re.sub(r'<link href="https://fonts\.googleapis[^>]*>\s*', "", off)
for a, b in [("'Poppins',system-ui", "'Poppins','Segoe UI',system-ui"),
             ("'IBM Plex Sans',system-ui", "'IBM Plex Sans','Segoe UI',system-ui"),
             ("'IBM Plex Mono',ui-monospace", "'IBM Plex Mono','Consolas',ui-monospace")]:
    off = off.replace(a, b)
off = off.replace("<title>Smart Buy", "<title>Smart Buy (offline)")

assert "cdnjs" not in off and "fonts.googleapis" not in off, "external request survived"
(HERE / "index_offline.html").write_text(off, encoding="utf-8")
print(f"  index_offline.html  {len(off)/1024:>6.0f} KB   (no external requests)")
