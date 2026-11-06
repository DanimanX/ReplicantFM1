#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Make the ReplicantFM1 site for GitHub Pages (https://danimanx.github.io/ReplicantFM1/):

  index.html                  what ReplicantFM1 is, and the ways in: install, manual, breaks, backup, source
  install/index.html          the web installer (web/x0x_installer.html, with fm1pkg.js, fm1ota.js
                              and the package's metadata inlined; Chrome or Edge, Web MIDI)
  breaks/index.html           your own break loops onto the FM-1 (web/x0x_breaks.html with
                              x0x_breaks.js inlined; Chrome or Edge, Web MIDI)
  backup/index.html           the project to a file and back (web/backup/index.html; Chrome or Edge, Web MIDI)
  manual/index.html, img/     the manual (tools/manual_html.py, from docs/MANUAL.md)
  new/index.html, img/new/    what's new in each version (the same, from docs/NEW.md)
  firmware/x0x-VERSION.fwsc   the package the installer writes; also the download

  tools/make_pages.py build/x0x-2.0.0.fwsc 2.0.0 OUT_DIR
"""
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC / "web"))
from make_site import product_of, strip_module  # noqa: E402

REPO = "https://github.com/DanimanX/ReplicantFM1"

LANDING = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ReplicantFM1 for the FM-1</title>
<meta name="description" content="Groovebox firmware for the M-VAVE FM-1: an authentic TR-909 drum machine, Roland SH-101 synthesizer, dual TB-303s with TB-3PO, and sliced breakbeat player in a toxic green VIRUS theme.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@400;600&family=Barlow+Semi+Condensed:wght@600;700&display=swap">
<style>
:root {
  --ground: #050d08;
  --ink: #68d272;
  --muted: #58a060;
  --rule: #164a22;
  --accent: #d6ff40;
  --card: #0a180e;
  --card-hover: #102416;
  color-scheme: dark;
}
body {
  background: var(--ground);
  color: var(--ink);
  margin: 0;
  padding-inline: 16px;
  padding-block: 48px 64px;
  font: 400 17px/1.6 "Barlow", "Helvetica Neue", Arial, sans-serif;
}
main { max-width: 44rem; margin: 0 auto; }
h1 {
  font: 700 2.8rem/1.1 "Barlow Semi Condensed", "Barlow", sans-serif;
  margin: 0 0 .4rem;
  color: var(--accent);
  text-shadow: 0 0 14px rgba(214,255,64,0.35);
  letter-spacing: .02em;
}
.lede { color: #a4f4ac; margin: 0 0 1.6rem; max-width: 38rem; }
.panel-img { width: 100%; height: auto; border-radius: 8px; border: 1px solid var(--rule); margin: 0 0 1.6rem; display: block; }
.status {
  border: 1px solid var(--rule);
  background: var(--card);
  border-radius: 8px;
  padding: 12px 16px;
  margin: 0 0 2rem;
  color: #8cd694;
  font-size: .95rem;
}
.ways { display: grid; gap: 12px; margin: 0 0 2rem; }
.ways a {
  display: block;
  text-decoration: none;
  color: var(--ink);
  background: var(--card);
  border: 1px solid var(--rule);
  border-radius: 10px;
  padding: 14px 18px;
  transition: border-color .15s, background .15s;
}
.ways a:hover { border-color: var(--accent); background: var(--card-hover); }
.ways a:focus-visible { border-color: var(--accent); outline: 2px solid var(--accent); outline-offset: 2px; }
.ways .card { background: var(--card); border: 1px solid var(--rule); border-radius: 10px; padding: 14px 18px; }
.ways .card a { color: var(--accent); text-decoration: none; border: 0; padding: 0; background: none; display: inline; }
.ways .card a:hover, .ways .card a:focus-visible { text-decoration: underline; }
.ways .card a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
.ways .card a.new { font: 400 .95rem "Barlow", sans-serif; margin-left: .5rem; }
.ways strong { font: 600 1.25rem "Barlow Semi Condensed", "Barlow", sans-serif; color: var(--accent); display: block; }
.ways span { color: var(--muted); font-size: .95rem; }
p.small { color: var(--muted); font-size: .9rem; }
a { color: var(--accent); }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
code { background: #0e2213; padding: 2px 6px; border-radius: 4px; font-size: .9em; color: var(--accent); }
</style>
</head>
<body>
<main>
<h1>REPLICANT FM-1</h1>
<p class="lede">Acid, techno, and big-beat groovebox firmware for the M-VAVE FM-1. An authentic <strong>TR-909</strong> drum machine, a modelled <strong>Roland SH-101</strong> monophonic synthesizer, dual <strong>TB-303</strong> basslines with <strong>TB-3PO</strong> algorithmic generator, and a real-time sliced <strong>breakbeat player</strong>, wrapped in the signature <strong>VIRUS</strong> toxic green interface.</p>
<img src="manual/img/fm1-panel.svg" alt="ReplicantFM1 Front Panel" class="panel-img">
<div class="status">ReplicantFM1 installs and uninstalls safely over USB-MIDI. The installer can restore M-VAVE stock firmware at any time.</div>
<nav class="ways" aria-label="Get ReplicantFM1">
  <div class="card"><strong><a href="install/">Install v__VERSION__</a> <a class="new" href="new/">What's new?</a></strong><span>Install directly from Chrome or Edge with the FM-1 connected via USB. No compiler or terminal required.</span></div>
  <a href="manual/"><strong>Manual</strong><span>Ten-step quick start guide, screen references, synthesizer architectures, and MIDI implementations.</span></a>
  <a href="breaks/"><strong>Your Own Breaks</strong><span>Upload custom breakbeat WAV loops directly into the BREAK slicer over Web MIDI.</span></a>
  <a href="backup/"><strong>Back Up Your Project</strong><span>Save your full device project, patterns, and motion sequences to a local file, and restore anytime.</span></a>
  <a href="firmware/__PKG__"><strong>Download __PKG__</strong><span>Direct firmware package download for offline or command-line flashing (<code>python3 tools/fm1_install.py __PKG__</code>).</span></a>
  <a href="__REPO__"><strong>Source Code</strong><span>Open source on GitHub (GPL-3.0). Built on Felucca by Hügelton Instruments and FM1-X0X by Charles Vestal.</span></a>
</nav>
<p class="small">To return to stock firmware, use the installer's "Back to the stock firmware" option or M-VAVE's official M-UPGRADE utility from
<a href="https://www.m-vave.com/download" target="_blank" rel="noopener">m-vave.com/download</a>. M-VAVE and FM-1 are trademarks of their respective owners.</p>
</main>
</body>
</html>
"""


def main(pkg, version, out):
    pkg, out = Path(pkg), Path(out)
    raw = pkg.read_bytes()
    product = product_of(raw)
    if not re.fullmatch(r"FM-1_9(\d\d|\d{6})", product) or product == "FM-1_900":
        raise SystemExit(f"{pkg}: identity {product!r}: make a release build (./build.sh --release X.Y-beta)")
    if b"FELUCCA-LOADER-1" not in raw:
        raise SystemExit(f"{pkg}: no update loader in it")
    name = f"x0x-{re.sub(r'[^A-Za-z0-9.-]', '-', version)}.fwsc"
    if out.exists():
        shutil.rmtree(out)
    for d in ("install", "manual", "firmware", "breaks", "backup", "new"):
        (out / d).mkdir(parents=True)
    shutil.copy(pkg, out / "firmware" / name)
    # also copy as ReplicantFM1 name if distinct
    rep_name = f"ReplicantFM1-{re.sub(r'[^A-Za-z0-9.-]', '-', version)}.fwsc"
    shutil.copy(pkg, out / "firmware" / rep_name)

    # the installer
    page = (SRC / "web" / "x0x_installer.html").read_text(encoding="utf-8")
    lib = strip_module((SRC / "web" / "fm1pkg.js").read_text(encoding="utf-8")) + "\n" + \
        strip_module((SRC / "web" / "fm1ota.js").read_text(encoding="utf-8"))
    meta = json.dumps({"version": version, "product": product, "pkg": "../firmware/" + name})
    for mark in ("/*LIB*/", "/*META*/"):
        if page.count(mark) != 1:
            raise SystemExit(f"x0x_installer.html must contain {mark} once")
    (out / "install" / "index.html").write_text(page.replace("/*LIB*/", lib).replace("/*META*/", meta), encoding="utf-8")

    # backward-compatibility redirect for webapp/installer
    (out / "webapp" / "installer").mkdir(parents=True, exist_ok=True)
    (out / "webapp" / "installer" / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>ReplicantFM1 Installer</title>'
        '<meta http-equiv="refresh" content="0; url=../../install/">'
        '<p>Redirecting to <a href="../../install/">installer</a>...</p>\n', encoding="utf-8")

    # the break loop uploader
    page = (SRC / "web" / "x0x_breaks.html").read_text(encoding="utf-8")
    if page.count("/*LIB*/") != 1:
        raise SystemExit("x0x_breaks.html must contain /*LIB*/ once")
    lib = strip_module((SRC / "web" / "x0x_breaks.js").read_text(encoding="utf-8"))
    (out / "breaks" / "index.html").write_text(page.replace("/*LIB*/", lib), encoding="utf-8")

    # the backup page (self-contained)
    shutil.copy(SRC / "web" / "backup" / "index.html", out / "backup" / "index.html")

    # the manual (a complete page; its images beside it)
    subprocess.run([sys.executable, str(SRC / "tools" / "manual_html.py"), str(SRC / "docs" / "MANUAL.md"),
                    str(out / "manual" / "index.html")], check=True, capture_output=True)
    shutil.copytree(SRC / "docs" / "img", out / "manual" / "img")

    # what's new (the same converter; its pictures beside it)
    subprocess.run([sys.executable, str(SRC / "tools" / "manual_html.py"), str(SRC / "docs" / "NEW.md"),
                    str(out / "new" / "index.html")], check=True, capture_output=True)
    shutil.copytree(SRC / "docs" / "img" / "new", out / "new" / "img" / "new")

    # the landing page
    (out / "index.html").write_text(LANDING.replace("__VERSION__", html.escape(version)).replace("__PKG__", name)
                                    .replace("__REPO__", REPO), encoding="utf-8")

    # emu (optional)
    emu = SRC / "build" / "emu"
    if (emu / "x0x.wasm").exists():
        shutil.copytree(emu, out / "emu")

    # the screen reader's words files (fm1-reader): every one ever made, for the devices that point at them
    if (SRC / "web" / "words").exists():
        shutil.copytree(SRC / "web" / "words", out / "words")

    (out / ".nojekyll").write_text("")
    print(f"site: {out}: index.html, install/ ({product}), manual/, breaks/, backup/, new/, firmware/{name} ({len(raw)} B)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
