#!/usr/bin/env python3
"""Render a preset with the host renderer and draw its spectrogram + waveform to a PNG.

  ht-tools/plot.py ENGINE PRESET OUT.png [--drums] [--mono] [--secs N] [--oct N] [--env KEY=VAL ...]

The picture is the closest thing to listening we have without hardware: attack shape, pitch
sweep, filter movement and decay are all visible.
"""
import argparse
import os
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
HOSTSIM = ROOT / "build" / "hostsim"
TMP = Path("/tmp/ht-render")


def load(path):
    with wave.open(str(path)) as w:
        sr = w.getframerate()
        raw = w.readframes(w.getnframes())
    import array
    a = array.array("h")
    a.frombytes(raw)
    x = np.array(a[0::2], dtype=np.float32) / 32768.0
    r = np.array(a[1::2], dtype=np.float32) / 32768.0
    return (x + r) * 0.5, sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine", type=int)
    ap.add_argument("preset", type=int)
    ap.add_argument("out")
    ap.add_argument("--drums", action="store_true")
    ap.add_argument("--mono", action="store_true")
    ap.add_argument("--secs", type=float)
    ap.add_argument("--oct", type=int)
    ap.add_argument("--steps")
    ap.add_argument("--fmax", type=int, default=12000)
    ap.add_argument("--shape", action="store_true", help="normalise each time frame (show the filter's shape)")
    a = ap.parse_args()

    TMP.mkdir(parents=True, exist_ok=True)
    wav = TMP / f"plot-e{a.engine}p{a.preset}.wav"
    env = dict(os.environ, PRESET="1")
    if a.secs:
        env["SECS"] = str(a.secs)
    if a.drums:
        env["DRUMS"] = "1"
    if a.oct is not None:
        env["OCT"] = str(a.oct)
    if a.steps:
        env["STEPS"] = a.steps
    subprocess.run([str(HOSTSIM), str(a.engine), str(a.preset), "1" if a.mono else "0", str(wav)],
                   check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    x, sr = load(wav)

    W, H = 900, 300
    nfft, hop = 1024, 128
    win = np.hanning(nfft)
    frames = max(1, (len(x) - nfft) // hop)
    spec = np.zeros((nfft // 2 + 1, frames), dtype=np.float32)
    for i in range(frames):
        seg = x[i * hop:i * hop + nfft]
        if len(seg) < nfft:
            seg = np.pad(seg, (0, nfft - len(seg)))
        spec[:, i] = np.abs(np.fft.rfft(seg * win)) ** 2
    spec = 10 * np.log10(spec + 1e-12)
    spec -= spec.max()
    freqs = np.fft.rfftfreq(nfft, 1 / sr)
    keep = freqs <= a.fmax
    spec = spec[keep]
    freqs = freqs[keep]
    if a.shape:
        # per-frame normalisation: the spectral shape at each moment, whatever the level
        spec = spec - spec.max(axis=0, keepdims=True)
    # log-frequency vertical axis
    rows = H
    fl = np.logspace(np.log10(30), np.log10(a.fmax), rows)[::-1]
    idx = np.searchsorted(freqs, fl)[:rows]
    img = np.clip((spec[idx.clip(max=spec.shape[0] - 1)] + 72) / 72, 0, 1)
    # resample time axis
    xi = (np.arange(W) * (frames / W)).astype(int).clip(0, frames - 1)
    img = img[:, xi]
    rgb = np.stack([np.clip(img * 1.6, 0, 1), np.clip(img * 1.1 - 0.15, 0, 1), np.clip(0.9 - img * 0.7, 0, 1)], -1)
    sp = Image.fromarray((rgb[::-1] * 255).astype(np.uint8)).resize((W, H))

    out = Image.new("RGB", (W, H + 130), (12, 12, 14))
    out.paste(sp, (0, 0))
    d = ImageDraw.Draw(out)
    # waveform
    wf_h = 80
    n = len(x)
    step = max(1, n // W)
    envl = np.array([np.max(np.abs(x[i:i + step])) if i < n else 0 for i in range(0, n, step)])[:W]
    y0 = H + 10 + wf_h // 2
    pts = [(i, y0 - envl[i] * wf_h / 2) for i in range(len(envl))]
    d.line(pts, fill=(90, 230, 170))
    d.line([(i, y0 + envl[i] * wf_h / 2) for i in range(len(envl))], fill=(90, 230, 170))
    d.line([(0, y0), (W, y0)], fill=(60, 60, 70))
    # frequency guides
    for hz in (50, 100, 200, 500, 1000, 2000, 5000, 10000):
        if hz > a.fmax:
            continue
        y = int(H * (1 - (np.log(hz) - np.log(30)) / (np.log(a.fmax) - np.log(30))))
        d.line([(0, y), (W, y)], fill=(70, 70, 90))
        d.text((3, max(0, y - 10)), f"{hz}", fill=(160, 160, 180))
    peak = float(np.max(np.abs(x))) if len(x) else 0
    d.text((6, H + wf_h + 14), f"engine {a.engine} preset {a.preset}   peak {20*np.log10(max(peak,1e-9)):.1f} dBFS   "
                               f"{len(x)/sr:.2f}s", fill=(220, 220, 230))
    out.save(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
