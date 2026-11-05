#!/usr/bin/env python3
"""Render a Felucca/Replicant engine preset with the host renderer and report what it sounds like.

  ht-tools/analyze.py ENGINE PRESET [--drums] [--mono] [--secs N] [--steps a,b,c]

Prints peak / RMS in dBFS, spectral centroid, the low band (<120 Hz) share, and a
1/3-octave band summary. Numbers only: enough to tell a kick from a hi-hat.
"""
import argparse
import json
import os
import subprocess
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOSTSIM = ROOT / "build" / "hostsim"
TMP = Path("/tmp/ht-render")


def render(engine, preset, drums=False, mono=False, secs=None, steps=None):
    TMP.mkdir(parents=True, exist_ok=True)
    out = TMP / f"e{engine}p{preset}{'-d' if drums else ''}.wav"
    env = dict(os.environ)
    env["PRESET"] = "1"
    if secs:
        env["SECS"] = str(secs)
    if drums:
        env["DRUMS"] = "1"
    if steps:
        env["STEPS"] = steps
    cmd = [str(HOSTSIM), str(engine), str(preset), "1" if mono else "0", str(out)]
    subprocess.run(cmd, check=True, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out


def load(path):
    with wave.open(str(path)) as w:
        n = w.getnframes()
        raw = w.readframes(n)
        sr = w.getframerate()
    import array
    a = array.array("h")
    a.frombytes(raw)
    return [x / 32768.0 for x in a[0::2]], [x / 32768.0 for x in a[1::2]], sr


def dbfs(x):
    import math
    return -120.0 if x <= 1e-9 else 20.0 * math.log10(x)


def analyze(path, sr):
    import numpy as np
    l, r, _ = load(path)
    x = np.array([(a + b) * 0.5 for a, b in zip(l, r)])
    if len(x) == 0:
        return {"error": "empty"}
    peak = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(x ** 2)))
    # drop digital silence at the tail for the spectral figures
    nz = np.nonzero(np.abs(x) > 1e-4)[0]
    seg = x[nz[0]:nz[-1] + 1] if len(nz) else x
    win = np.hanning(len(seg))
    spec = np.abs(np.fft.rfft(seg * win))
    freqs = np.fft.rfftfreq(len(seg), 1 / sr)
    power = spec ** 2
    total = float(power.sum()) or 1.0
    centroid = float((freqs * power).sum() / total)
    bands = {
        "sub<60": float(power[(freqs < 60)].sum() / total),
        "60-120": float(power[(freqs >= 60) & (freqs < 120)].sum() / total),
        "120-500": float(power[(freqs >= 120) & (freqs < 500)].sum() / total),
        "0.5-2k": float(power[(freqs >= 500) & (freqs < 2000)].sum() / total),
        "2-6k": float(power[(freqs >= 2000) & (freqs < 6000)].sum() / total),
        ">6k": float(power[(freqs >= 6000)].sum() / total),
    }
    # decay: time from peak to -20 dB relative to peak
    env = np.abs(x)
    k = max(1, sr // 200)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    pi = int(np.argmax(env))
    thr = env[pi] * 0.1
    idx = np.nonzero(env[pi:] < thr)[0]
    t20 = float(idx[0] / sr) if len(idx) else float((len(env) - pi) / sr)
    clip = int(np.sum(np.abs(x) > 0.999))
    return {
        "peak_dbfs": round(dbfs(peak), 2),
        "rms_dbfs": round(dbfs(rms), 2),
        "crest_db": round(dbfs(peak) - dbfs(rms), 2),
        "centroid_hz": round(centroid, 1),
        "decay_to_-20db_s": round(t20, 3),
        "clipped_samples": clip,
        "bands": {k: round(v, 3) for k, v in bands.items()},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine", type=int)
    ap.add_argument("preset", type=int)
    ap.add_argument("--drums", action="store_true")
    ap.add_argument("--mono", action="store_true")
    ap.add_argument("--secs", type=float)
    ap.add_argument("--steps")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    wav = render(a.engine, a.preset, a.drums, a.mono, a.secs, a.steps)
    l, r, sr = load(wav)
    res = analyze(wav, sr)
    res["wav"] = str(wav)
    if a.json:
        print(json.dumps(res, indent=2))
    else:
        print(f"{wav}")
        for k, v in res.items():
            if k != "bands":
                print(f"  {k:18} {v}")
        for k, v in res.get("bands", {}).items():
            print(f"  band {k:10} {v*100:5.1f} %")


if __name__ == "__main__":
    main()
