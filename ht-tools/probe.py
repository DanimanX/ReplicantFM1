#!/usr/bin/env python3
"""Compare synth presets side by side with the sends off, so the oscillator and filter can be judged.

  ht-tools/probe.py ENGINE PRESET [ENGINE PRESET ...] [--pset id:v,...] [--oct N] [--note K]

Prints, per preset: peak, RMS, the brightness rolloff and the high-band share in an
attack window and a body window (the acid's whole point is the filter closing).
"""
import argparse
import os
import subprocess
import wave
import array

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTSIM = os.path.join(ROOT, "build", "hostsim")

# P_* ids as the firmware counts them (firmware/src/core.h)
P_ED_FLT, P_DIST, P_CHOR, P_DLY, P_REV, P_ITYPE, P_E0 = 5, 33, 34, 35, 36, 96, 106
P_E4, P_E5, P_E6 = P_E0 + 4, P_E0 + 5, P_E0 + 6


def render(engine, preset, note=7, octave=None, secs=1.0, pset=None, mono=True):
    env = dict(os.environ, PRESET="1", SECS=str(secs), NOTE=str(note))
    if octave is not None:
        env["OCT"] = str(octave)
    base = {"%d" % P_DIST: 0, "%d" % P_CHOR: 0, "%d" % P_DLY: 0, "%d" % P_REV: 0}
    if pset:
        base.update({str(k): v for k, v in pset.items()})
    env["PSET"] = ",".join(f"{k}:{v}" for k, v in base.items())
    out = f"/tmp/probe-{engine}-{preset}.wav"
    subprocess.run([HOSTSIM, str(engine), str(preset), "1" if mono else "0", out],
                   env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with wave.open(out) as w:
        sr = w.getframerate()
        a = array.array("h")
        a.frombytes(w.readframes(w.getnframes()))
    return np.array(a[0::2], dtype=np.float32) / 32768.0, sr


def window(x, sr, t0, t1):
    s = x[int(t0 * sr):int(t1 * sr)]
    if len(s) < 256:
        return 0.0, 0.0
    sp = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2
    f = np.fft.rfftfreq(len(s), 1 / sr)
    tot = sp.sum() + 1e-12
    roll = f[min(len(f) - 1, int(np.searchsorted(np.cumsum(sp) / tot, 0.85)))]
    return roll, sp[f > 2000].sum() / tot


def report(engine, preset, name, note, octave, pset):
    x, sr = render(engine, preset, note, octave, 1.0, pset)
    peak = 20 * np.log10(max(float(np.max(np.abs(x))), 1e-9))
    rms = 20 * np.log10(max(float(np.sqrt((x ** 2).mean())), 1e-9))
    a_roll, a_hi = window(x, sr, 0.055, 0.10)
    b_roll, b_hi = window(x, sr, 0.20, 0.40)
    print(f"{name:14} peak {peak:6.1f} rms {rms:6.1f} | attack roll85 {a_roll:6.0f} Hz hi {a_hi*100:5.1f}%"
          f" | body roll85 {b_roll:6.0f} Hz hi {b_hi*100:5.1f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs", nargs="+", help="ENGINE PRESET ...")
    ap.add_argument("--pset", default="")
    ap.add_argument("--oct", type=int)
    ap.add_argument("--note", type=int, default=7)
    a = ap.parse_args()
    pset = {}
    for kv in filter(None, a.pset.split(",")):
        k, v = kv.split(":")
        pset[int(k)] = int(v)
    vals = list(map(int, a.pairs))
    for i in range(0, len(vals), 2):
        report(vals[i], vals[i + 1], f"e{vals[i]}p{vals[i+1]}", a.note, a.oct, pset)


if __name__ == "__main__":
    main()
