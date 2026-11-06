#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Render a high-impact promotional video for ReplicantFM1 v2.0 (Hard Techno).
Outputs build/replicant_fm1_hard_techno_promo.mp4 (1080p, 50s, 30fps).
"""
import math
import os
import subprocess
import sys
import time
import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
FPS = 30
AUDIO_FILE = "build/promo/promo_final_audio.wav"
OUT_VIDEO = "build/replicant_fm1_hard_techno_promo.mp4"

# Colors
C_BG = (5, 13, 8)
C_GRID = (14, 38, 22)
C_CARD = (9, 24, 14)
C_CARD_BORDER = (24, 72, 36)
C_GREEN = (104, 210, 114)
C_LIME = (214, 255, 64)
C_WHITE = (242, 255, 245)
C_DIM = (50, 110, 62)
C_RED = (255, 64, 64)
C_CYAN = (64, 220, 255)
C_AMBER = (255, 170, 40)
C_MAGENTA = (230, 80, 220)

def main():
    print(f"Loading audio from {AUDIO_FILE}...")
    with wave.open(AUDIO_FILE, "rb") as w:
        rate = w.getframerate()
        nframes = w.getnframes()
        raw = np.frombuffer(w.readframes(nframes), dtype=np.int16).astype(np.float32) / 32768.0
        audio = raw.reshape(-1, 2)
    
    duration = nframes / rate
    total_frames = int(duration * FPS)
    print(f"Audio duration: {duration:.2f}s -> {total_frames} video frames at {FPS} fps")

    # Load Fonts
    f_huge = ImageFont.truetype("assets/fonts/BarlowSemiCondensed-Bold.ttf", 68)
    f_title = ImageFont.truetype("assets/fonts/BarlowSemiCondensed-Bold.ttf", 52)
    f_sub = ImageFont.truetype("assets/fonts/BarlowSemiCondensed-Bold.ttf", 36)
    f_card_h = ImageFont.truetype("assets/fonts/BarlowSemiCondensed-Bold.ttf", 32)
    f_body = ImageFont.truetype("assets/fonts/BarlowSemiCondensed-Medium.ttf", 26)
    f_mono = ImageFont.truetype("assets/fonts/BarlowSemiCondensed-SemiBold.ttf", 22)
    f_pill = ImageFont.truetype("assets/fonts/BarlowSemiCondensed-Bold.ttf", 20)

    # Load Screens
    def load_img(path, size=None):
        if not os.path.exists(path):
            return None
        im = Image.open(path).convert("RGB")
        if size:
            im = im.resize(size, Image.Resampling.LANCZOS)
        return im

    splash_img = load_img("docs/img/screen-splash.png", (460, 460))
    s_909 = load_img("docs/img/screen-909.png", (400, 400))
    s_101_vcf = load_img("docs/img/screen-101-vcf.png", (400, 400))
    s_101_seq = load_img("docs/img/screen-101-seq.png", (400, 400))
    s_303 = load_img("docs/img/screen-303.png", (400, 400))
    s_tb3po = load_img("docs/img/screen-tb3po.png", (400, 400))
    s_break = load_img("docs/img/screen-break.png", (400, 400))
    s_mix = load_img("docs/img/screen-mix.png", (400, 400))
    s_fx = load_img("docs/img/screen-fx.png", (400, 400))
    s_breakdown = load_img("build/promo/shot_07_breakdown.png", (460, 460))
    panel_img = load_img("build/panel.png", (1200, 864))

    # Precompute kick detection & beat flashes
    # Sub-bass filter around 40-100Hz
    fft_win = 1024
    sub_energy = np.zeros(total_frames)
    for f in range(total_frames):
        s_idx = int(f * rate / FPS)
        if s_idx + fft_win <= len(audio):
            chunk = audio[s_idx:s_idx+fft_win, 0]
            sub = np.mean(chunk**2)
            sub_energy[f] = sub
    max_sub = np.max(sub_energy) if np.max(sub_energy) > 0 else 1.0
    sub_energy = sub_energy / max_sub

    # Setup ffmpeg process
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{W}x{H}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",
        "-i", AUDIO_FILE,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "256k",
        "-shortest",
        OUT_VIDEO
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    print("Rendering video frames...")
    t0 = time.time()

    # Pre-render background grid pattern
    base_bg = Image.new("RGB", (W, H), C_BG)
    d_base = ImageDraw.Draw(base_bg)
    # Subtle cyber grid
    for x in range(0, W, 48):
        d_base.line([(x, 0), (x, H)], fill=C_GRID, width=1)
    for y in range(0, H, 48):
        d_base.line([(0, y), (W, y)], fill=C_GRID, width=1)

    for f in range(total_frames):
        t = f / FPS
        frame = base_bg.copy()
        draw = ImageDraw.Draw(frame)

        # Beat Flash intensity
        beat_val = sub_energy[f]
        if beat_val > 0.4:
            flash_alpha = min(1.0, (beat_val - 0.4) * 2.0)
            glow_col = (int(10 + flash_alpha * 20), int(26 + flash_alpha * 40), int(16 + flash_alpha * 25))
            draw.rectangle([0, 0, W, H], outline=(int(104 + flash_alpha * 110), int(210 + flash_alpha * 45), int(64)), width=int(2 + flash_alpha * 4))

        # --- TOP HEADER BAR ---
        draw.rectangle([0, 0, W, 85], fill=(7, 18, 10))
        draw.line([(0, 85), (W, 85)], fill=C_CARD_BORDER, width=2)

        # Left Badges
        # Blinking REC dot
        rec_on = (f // 15) % 2 == 0
        rec_dot_col = C_RED if rec_on else (80, 20, 20)
        draw.ellipse([40, 32, 54, 46], fill=rec_dot_col)
        draw.text((64, 27), "LIVE HARDWARE", font=f_mono, fill=C_WHITE)
        
        # Pill 148 BPM
        draw.rectangle([210, 22, 330, 58], fill=C_CARD, outline=C_CARD_BORDER, width=1)
        draw.text((270, 40), "148.0 BPM", font=f_pill, fill=C_LIME, anchor="mm")

        draw.rectangle([345, 22, 510, 58], fill=C_CARD, outline=C_CARD_BORDER, width=1)
        draw.text((427, 40), "BLADE ACID TECHNO", font=f_pill, fill=C_GREEN, anchor="mm")

        # Center Title
        draw.text((W // 2, 32), "REPLICANT FM-1 v2.0", font=f_sub, fill=C_LIME, anchor="mm")
        draw.text((W // 2, 65), "BLADE ACID // HARD RAVE CUT (M-VAVE FM-1)", font=f_mono, fill=C_GREEN, anchor="mm")

        # Right Indicators (Part activity depending on time)
        parts_active = {
            "909": (6.5 <= t < 32.5) or (t >= 39.0 and t < 48.7),
            "101": (6.5 <= t < 32.5) or (t >= 39.0 and t < 48.7),
            "303A": t < 48.7,
            "303B": (13.0 <= t < 48.7),
            "BRK": (26.0 <= t < 32.5) or (t >= 39.0 and t < 48.7),
        }

        px = 1450
        for pname, pcol, pact in [
            ("909", C_AMBER, parts_active["909"]),
            ("101", C_MAGENTA, parts_active["101"]),
            ("303A", C_LIME, parts_active["303A"]),
            ("303B", C_CYAN, parts_active["303B"]),
            ("BRK", C_GREEN, parts_active["BRK"]),
        ]:
            bg_col = (20, 40, 25) if pact else (10, 20, 12)
            txt_col = pcol if pact else (60, 80, 65)
            bord_col = pcol if pact else (30, 50, 35)
            draw.rectangle([px, 26, px + 58, 56], fill=bg_col, outline=bord_col, width=1)
            draw.text((px + 29, 41), pname, font=f_pill, fill=txt_col, anchor="mm")
            px += 66

        # CPU badge
        draw.text((1840, 40), "CPU 62%", font=f_pill, fill=C_LIME, anchor="mm")

        # --- SCENE LOGIC ---
        if t < 6.5:
            # SCENE 1: HOOK / BLADE ACID TECHNO // BLOOD RAVE THEME
            draw.text((W // 2, 135), "BLADE ACID TECHNO // HARD RAVE REMIX", font=f_huge, fill=C_WHITE, anchor="mm")
            draw.text((W // 2, 185), "ICONIC PUMP PANEL 303 ACID RIFF • DEVILFISH RAT DISTORTION • 148 BPM", font=f_sub, fill=C_LIME, anchor="mm")

            if splash_img:
                sx = W // 2 - 230
                sy = 230
                draw.rectangle([sx - 10, sy - 10, sx + 470, sy + 470], fill=(8, 20, 12), outline=C_LIME, width=3)
                frame.paste(splash_img, (sx, sy))

            # Status Box Below
            draw.rectangle([440, 730, 1480, 810], fill=C_CARD, outline=C_CARD_BORDER, width=2)
            draw.text((W // 2, 755), "RUNNING STANDALONE VIRUS ARCHITECTURE ON THE $40 M-VAVE FM-1", font=f_card_h, fill=C_GREEN, anchor="mm")
            draw.text((W // 2, 785), "DUAL 303 DEVILFISH + TR-909 HARD KICK + SH-101 SUB + BREAK SLICER • 24-BIT USB AUDIO", font=f_mono, fill=C_WHITE, anchor="mm")

        elif t < 13.0:
            # SCENE 2: THE 909 HARD KICK DROPS IN + SH-101
            draw.text((W // 2, 125), "ENGINE 01 // ROLAND TR-909  +  ENGINE 02 // ROLAND SH-101", font=f_title, fill=C_LIME, anchor="mm")
            draw.text((W // 2, 168), "AUTHENTIC PUNCHY 909 DRUM MACHINE & PHYSICAL-MODELLED ANALOG LEAD/BASS SYNTH", font=f_mono, fill=C_WHITE, anchor="mm")

            # Left Card: TR-909
            lx, ly = 80, 200
            draw.rectangle([lx, ly, lx + 860, ly + 580], fill=C_CARD, outline=C_CARD_BORDER, width=2)
            draw.rectangle([lx, ly, lx + 860, ly + 55], fill=(14, 38, 20), outline=C_CARD_BORDER, width=1)
            draw.text((lx + 20, ly + 28), "TR-909 DRUM MACHINE (HARD CLUB PUNCH)", font=f_card_h, fill=C_AMBER, anchor="lm")
            draw.text((lx + 840, ly + 28), "[ 11 TRACKS + KIT ]", font=f_pill, fill=C_GREEN, anchor="rm")
            if s_909:
                frame.paste(s_909, (lx + 20, ly + 75))
                draw.rectangle([lx + 18, ly + 73, lx + 422, ly + 477], outline=C_AMBER, width=2)
            
            # 909 Bullet Points
            bx = lx + 440
            by = ly + 110
            bullets_909 = [
                ("Hard Punch Kick", "Tuned transient click with overdriven sub decay"),
                ("Snappy Snare & Clap", "Driven rimshot, snappy snare & layered clap on 2 & 4"),
                ("Sizzling Open Hat", "Dedicated crisp closed hat & long open hat sizzle"),
                ("Rave Ride Cymbal", "Wall-of-sound ride driving 148 BPM energy")
            ]
            for title, desc in bullets_909:
                draw.text((bx, by), "● " + title, font=f_card_h, fill=C_LIME)
                draw.text((bx, by + 34), desc, font=f_mono, fill=C_GREEN)
                by += 85

            # Right Card: SH-101
            rx, ry = 980, 200
            draw.rectangle([rx, ry, rx + 860, ly + 580], fill=C_CARD, outline=C_CARD_BORDER, width=2)
            draw.rectangle([rx, ry, rx + 860, ry + 55], fill=(14, 38, 20), outline=C_CARD_BORDER, width=1)
            draw.text((rx + 20, ry + 28), "ROLAND SH-101 SYNTHESIZER", font=f_card_h, fill=C_MAGENTA, anchor="lm")
            draw.text((rx + 840, ry + 28), "[ CEM3340 + IR3109 ]", font=f_pill, fill=C_LIME, anchor="rm")
            if s_101_vcf:
                frame.paste(s_101_vcf, (rx + 20, ry + 75))
                draw.rectangle([rx + 18, ry + 73, rx + 422, ry + 477], outline=C_MAGENTA, width=2)

            # SH-101 Bullet Points
            bx = rx + 440
            by = ry + 110
            bullets_101 = [
                ("CEM3340 VCO", "Band-limited Saw, Pulse with PWM, Sub-Osc & Noise"),
                ("IR3109 VCF", "24 dB/oct 4-pole ZDF Low-Pass with self-oscillation"),
                ("Envelopes & LFO", "Snappy ADSR envelope, Triangle/Square/S&H LFO"),
                ("Pounding Sub-Bass", "Dedicated 1-octave sub oscillator driving low end")
            ]
            for title, desc in bullets_101:
                draw.text((bx, by), "● " + title, font=f_card_h, fill=C_LIME)
                draw.text((bx, by + 34), desc, font=f_mono, fill=C_GREEN)
                by += 85

        elif t < 26.0:
            # SCENE 3: DUAL 303 + DEVILFISH RAT DISTORTION
            draw.text((W // 2, 125), "ENGINE 03 & 04 // DUAL TB-303 (DEVILFISH RAT DISTORTION)", font=f_title, fill=C_LIME, anchor="mm")
            draw.text((W // 2, 168), "TWO STEREO ACID LINES: PUMP PANEL BLADE THEME + SCREAMING COUNTERPOINT", font=f_mono, fill=C_WHITE, anchor="mm")

            # Left Card: TB-303
            lx, ly = 80, 200
            draw.rectangle([lx, ly, lx + 860, ly + 580], fill=C_CARD, outline=C_CARD_BORDER, width=2)
            draw.rectangle([lx, ly, lx + 860, ly + 55], fill=(14, 38, 20), outline=C_CARD_BORDER, width=1)
            draw.text((lx + 20, ly + 28), "DUAL 303 ACID ENGINES (303A & 303B)", font=f_card_h, fill=C_LIME, anchor="lm")
            draw.text((lx + 840, ly + 28), "[ DEVILFISH RAT DRIVE ]", font=f_pill, fill=C_CYAN, anchor="rm")
            if s_303:
                frame.paste(s_303, (lx + 20, ly + 75))
                draw.rectangle([lx + 18, ly + 73, lx + 422, ly + 477], outline=C_LIME, width=2)
            
            bx = lx + 440
            by = ly + 110
            bullets_303 = [
                ("Stereo Acid Lines", "303A panned left, 303B panned right with ping-pong delay"),
                ("Diode Ladder VCF", "Iconic acid squelch, liquid resonance & piercing scream"),
                ("Devilfish RAT Drive", "High-gain aggressive clipping distortion mod"),
                ("Acid Slides & Accents", "Authentic 60ms analog pitch glides and punchy accents")
            ]
            for title, desc in bullets_303:
                draw.text((bx, by), "● " + title, font=f_card_h, fill=C_LIME)
                draw.text((bx, by + 34), desc, font=f_mono, fill=C_GREEN)
                by += 85

            # Right Card: TB-3PO
            rx, ry = 980, 200
            draw.rectangle([rx, ry, rx + 860, ly + 580], fill=C_CARD, outline=C_CARD_BORDER, width=2)
            draw.rectangle([rx, ry, rx + 860, ry + 55], fill=(14, 38, 20), outline=C_CARD_BORDER, width=1)
            draw.text((rx + 20, ry + 28), "TB-3PO ALGORITHMIC ACID ENGINE", font=f_card_h, fill=C_CYAN, anchor="lm")
            draw.text((rx + 840, ry + 28), "[ GENERATIVE ACID ]", font=f_pill, fill=C_LIME, anchor="rm")
            if s_tb3po:
                frame.paste(s_tb3po, (rx + 20, ry + 75))
                draw.rectangle([rx + 18, ry + 73, rx + 422, ry + 477], outline=C_CYAN, width=2)

            bx = rx + 440
            by = ry + 110
            bullets_tb3po = [
                ("Algorithmic Engine", "Musical constraint models generate instant acid lines"),
                ("Live Mutation", "OCT+ for fresh patterns, OCT- to mutate current line"),
                ("Dynamic Filter Sweep", "Real-time automated cutoff sweeps opening live"),
                ("Universal Support", "Sequences SH-101, 303A, and 303B seamlessly!")
            ]
            for title, desc in bullets_tb3po:
                draw.text((bx, by), "● " + title, font=f_card_h, fill=C_LIME)
                draw.text((bx, by + 34), desc, font=f_mono, fill=C_GREEN)
                by += 85

        elif t < 32.5:
            # SCENE 4: BREAK SLICER & MASTER BUS
            draw.text((W // 2, 125), "ENGINE 05 // BREAK SLICER  +  MASTER BUS PUMP COMPRESSION", font=f_title, fill=C_LIME, anchor="mm")
            draw.text((W // 2, 168), "AMEN BREAK SLICED LIVE UNDER 909 KICK WITH KICK-KEYED DUCKING & TAPE DELAY", font=f_mono, fill=C_WHITE, anchor="mm")

            # Left Card: BREAK SLICER
            lx, ly = 80, 200
            draw.rectangle([lx, ly, lx + 860, ly + 580], fill=C_CARD, outline=C_CARD_BORDER, width=2)
            draw.rectangle([lx, ly, lx + 860, ly + 55], fill=(14, 38, 20), outline=C_CARD_BORDER, width=1)
            draw.text((lx + 20, ly + 28), "REAL-TIME BREAKBEAT SLICER", font=f_card_h, fill=C_LIME, anchor="lm")
            draw.text((lx + 840, ly + 28), "[ 8 SLICES • WAV UPLOAD ]", font=f_pill, fill=C_GREEN, anchor="rm")
            if s_break:
                frame.paste(s_break, (lx + 20, ly + 75))
                draw.rectangle([lx + 18, ly + 73, lx + 422, ly + 477], outline=C_LIME, width=2)
            
            bx = lx + 440
            by = ly + 110
            bullets_brk = [
                ("Live Slicer Engine", "Slices drum breaks into 8 triggerable sample pads"),
                ("Performance Rolls", "Granular rolls, pitch transposition, and reverse"),
                ("Bank Memory", "Built-in breaks + Web-MIDI browser WAV uploader"),
                ("Stereo Sends", "Send breaks to stereo reverb & tape delay")
            ]
            for title, desc in bullets_brk:
                draw.text((bx, by), "● " + title, font=f_card_h, fill=C_LIME)
                draw.text((bx, by + 34), desc, font=f_mono, fill=C_GREEN)
                by += 85

            # Right Card: MASTER BUS & FX
            rx, ry = 980, 200
            draw.rectangle([rx, ry, rx + 860, ly + 580], fill=C_CARD, outline=C_CARD_BORDER, width=2)
            draw.rectangle([rx, ry, rx + 860, ry + 55], fill=(14, 38, 20), outline=C_CARD_BORDER, width=1)
            draw.text((rx + 20, ry + 28), "MASTER PUMP COMPRESSOR & FX", font=f_card_h, fill=C_AMBER, anchor="lm")
            draw.text((rx + 840, ry + 28), "[ ANALOG TUBE DRIVE ]", font=f_pill, fill=C_LIME, anchor="rm")
            if s_mix:
                frame.paste(s_mix, (rx + 20, ry + 75))
                draw.rectangle([rx + 18, ry + 73, rx + 422, ry + 477], outline=C_AMBER, width=2)

            bx = rx + 440
            by = ry + 110
            bullets_fx = [
                ("Master Pump Comp", "24 dB sidechain ducking keyed directly to 909 kick!"),
                ("Master Tube Drive", "Asymmetric warm tube drive & saturation on mix"),
                ("Tape Delay", "Vintage ping-pong delay with wow/flutter tape wear"),
                ("Stereo Reverb", "Spacious room & hall reverb with dampening")
            ]
            for title, desc in bullets_fx:
                draw.text((bx, by), "● " + title, font=f_card_h, fill=C_LIME)
                draw.text((bx, by + 34), desc, font=f_mono, fill=C_GREEN)
                by += 85

        elif t < 48.7:
            # SCENE 5: BREAKDOWN & MASSIVE HARD DROP!
            if t < 39.0:
                # The Blood Rave Breakdown
                draw.text((W // 2, 130), "// THE BLOOD RAVE BREAKDOWN //", font=f_title, fill=C_AMBER, anchor="mm")
                draw.text((W // 2, 175), "909 KICK MUTED • SCREAMING DUAL 303S ECHOING IN THE DARK...", font=f_sub, fill=C_WHITE, anchor="mm")

                if s_breakdown:
                    bx = W // 2 - 230
                    by = 220
                    draw.rectangle([bx - 6, by - 6, bx + 466, by + 466], outline=C_AMBER, width=3)
                    frame.paste(s_breakdown, (bx, by))

                draw.rectangle([440, 720, 1480, 800], fill=(20, 10, 5), outline=C_AMBER, width=2)
                draw.text((W // 2, 745), "SNARE ROLLS ACCELERATING • FILTER RESONANCE AT MAXIMUM!", font=f_title, fill=C_LIME, anchor="mm")
                draw.text((W // 2, 775), "GET READY FOR THE 148 BPM HARD TECHNO DROP...", font=f_mono, fill=C_WHITE, anchor="mm")
            else:
                # THE DROP!
                flash = (t < 39.5)
                drop_col = C_WHITE if flash else C_LIME
                draw.text((W // 2, 125), "*** THE MAXIMUM HARD TECHNO DROP ***", font=f_huge, fill=drop_col, anchor="mm")
                draw.text((W // 2, 175), "ALL 5 ENGINES FIRING AT 148 BPM • 100% STANDALONE ON M-VAVE FM-1", font=f_sub, fill=C_GREEN, anchor="mm")

                # Show Front Panel
                if panel_img:
                    px = W // 2 - 600
                    py = 205
                    draw.rectangle([px - 4, py - 4, px + 1204, py + 584], outline=C_LIME, width=3)
                    # Crop panel to fit neatly
                    panel_crop = panel_img.crop((0, 80, 1200, 660))
                    frame.paste(panel_crop, (px, py))

                draw.rectangle([200, 770, 1720, 830], fill=C_CARD, outline=C_CARD_BORDER, width=2)
                draw.text((W // 2, 800), "TR-909 POUNDING • SH-101 ROLLING • DUAL 303S SCREAMING • BREAK SLICED • MASTER PUMPING", font=f_card_h, fill=C_WHITE, anchor="mm")

        else:
            # SCENE 6: GET IT FREE / OUTRO
            draw.text((W // 2, 125), "REPLICANT FM-1 v2.0", font=f_huge, fill=C_LIME, anchor="mm")
            draw.text((W // 2, 175), "100% FREE & OPEN SOURCE // GPL-3.0", font=f_sub, fill=C_WHITE, anchor="mm")

            # Center Callout Box
            cx, cy = 240, 220
            cw, ch = 1440, 560
            draw.rectangle([cx, cy, cx + cw, cy + ch], fill=(8, 22, 12), outline=C_LIME, width=3)

            draw.text((W // 2, cy + 50), "INSTALL IN 1-CLICK FROM YOUR BROWSER", font=f_huge, fill=C_WHITE, anchor="mm")
            draw.text((W // 2, cy + 115), "No compiler. No Python. No terminal. Nothing to install on your computer.", font=f_sub, fill=C_GREEN, anchor="mm")

            draw.text((W // 2, cy + 175), "Connect your M-VAVE FM-1 via USB-C in Chrome or Edge and open:", font=f_body, fill=C_WHITE, anchor="mm")

            # Glowing URL Box
            ux, uy, uw, uh = W // 2 - 450, cy + 215, 900, 95
            draw.rectangle([ux, uy, ux + uw, uy + uh], fill=(14, 38, 20), outline=C_LIME, width=3)
            draw.text((W // 2, uy + 47), "danimanx.github.io/ReplicantFM1", font=f_huge, fill=C_LIME, anchor="mm")

            # Features Recap Pills
            pills = ["ROLAND TR-909", "ROLAND SH-101", "DUAL TB-303 (TB-3PO)", "BREAK SLICER", "TAPE DELAY", "USB 24-BIT AUDIO"]
            px_start = cx + 80
            py_pill = cy + 360
            for pill in pills:
                draw.rectangle([px_start, py_pill, px_start + 190, py_pill + 44], fill=C_CARD, outline=C_CARD_BORDER, width=1)
                draw.text((px_start + 95, py_pill + 22), pill, font=f_pill, fill=C_GREEN, anchor="mm")
                px_start += 210

            # Safe note
            draw.text((W // 2, cy + 450), "100% Safe: Hold OCT- on power-on to return to stock firmware anytime.", font=f_mono, fill=C_WHITE, anchor="mm")
            draw.text((W // 2, cy + 490), "Complete online manual, project backup & custom loop uploader included.", font=f_mono, fill=C_GREEN, anchor="mm")

        # --- BOTTOM VISUALIZER DOCK ---
        # Panel frame
        draw.rectangle([40, 870, W - 40, 1050], fill=(7, 18, 11), outline=C_CARD_BORDER, width=2)
        draw.rectangle([40, 870, W - 40, 898], fill=(12, 30, 18), outline=C_CARD_BORDER, width=1)
        draw.text((60, 884), "MASTER AUDIO OUTPUT // REAL-TIME DSP TELEMETRY", font=f_pill, fill=C_LIME, anchor="lm")
        draw.text((W - 60, 884), "24-BIT 44.1 kHz STEREO", font=f_pill, fill=C_GREEN, anchor="rm")

        # 1. Left: Real-time Oscilloscope
        s_idx = int(t * rate)
        osc_len = 512
        if s_idx + osc_len < len(audio):
            osc_data = audio[s_idx:s_idx+osc_len, 0]
        else:
            osc_data = np.zeros(osc_len)
        
        ox0, oy0, ow, oh = 60, 915, 600, 115
        draw.rectangle([ox0, oy0, ox0 + ow, oy0 + oh], fill=(4, 10, 6), outline=C_CARD_BORDER, width=1)
        # Center grid line
        draw.line([(ox0, oy0 + oh // 2), (ox0 + ow, oy0 + oh // 2)], fill=(18, 48, 25), width=1)
        # Waveform trace
        pts = []
        step = max(1, osc_len // ow)
        for i in range(0, ow):
            samp_i = min(i * step, len(osc_data) - 1)
            y_val = oy0 + oh // 2 - int(osc_data[samp_i] * (oh // 2 - 4))
            pts.append((ox0 + i, max(oy0 + 2, min(oy0 + oh - 2, y_val))))
        if len(pts) > 1:
            draw.line(pts, fill=C_LIME, width=2)

        draw.text((ox0 + 10, oy0 + 12), "OSCILLOSCOPE", font=f_pill, fill=C_GREEN)

        # 2. Center: Stereo Peak VU Meters
        vx0, vy0, vw, vh = 700, 915, 260, 115
        draw.rectangle([vx0, vy0, vx0 + vw, vy0 + vh], fill=(4, 10, 6), outline=C_CARD_BORDER, width=1)
        draw.text((vx0 + 10, vy0 + 12), "STEREO VU", font=f_pill, fill=C_GREEN)
        
        chunk = audio[max(0, s_idx-256):s_idx+256]
        if len(chunk) > 0:
            peak_l = np.max(np.abs(chunk[:, 0]))
            peak_r = np.max(np.abs(chunk[:, 1]))
        else:
            peak_l = peak_r = 0.0

        bar_w = 220
        # Left bar
        fill_l = int(min(1.0, peak_l * 1.1) * bar_w)
        draw.rectangle([vx0 + 20, vy0 + 40, vx0 + 20 + bar_w, vy0 + 58], fill=(12, 28, 16), outline=C_CARD_BORDER, width=1)
        draw.rectangle([vx0 + 20, vy0 + 40, vx0 + 20 + fill_l, vy0 + 58], fill=C_LIME if peak_l < 0.9 else C_RED)
        draw.text((vx0 + 10, vy0 + 49), "L", font=f_pill, fill=C_WHITE, anchor="rm")

        # Right bar
        fill_r = int(min(1.0, peak_r * 1.1) * bar_w)
        draw.rectangle([vx0 + 20, vy0 + 72, vx0 + 20 + bar_w, vy0 + 90], fill=(12, 28, 16), outline=C_CARD_BORDER, width=1)
        draw.rectangle([vx0 + 20, vy0 + 72, vx0 + 20 + fill_r, vy0 + 90], fill=C_LIME if peak_r < 0.9 else C_RED)
        draw.text((vx0 + 10, vy0 + 81), "R", font=f_pill, fill=C_WHITE, anchor="rm")

        # 3. Right: 32-band Spectrum Analyzer
        spec_x, spec_y, spec_w, spec_h = 1000, 915, 860, 115
        draw.rectangle([spec_x, spec_y, spec_x + spec_w, spec_y + spec_h], fill=(4, 10, 6), outline=C_CARD_BORDER, width=1)
        draw.text((spec_x + 10, spec_y + 12), "SPECTRUM (32 BANDS)", font=f_pill, fill=C_GREEN)

        fft_chunk = audio[max(0, s_idx):min(len(audio), s_idx+1024), 0]
        if len(fft_chunk) == 1024:
            fft_mag = np.abs(np.fft.rfft(fft_chunk * np.hanning(1024)))
            nbands = 32
            # Logarithmic frequency distribution
            band_vals = []
            for b in range(nbands):
                low_idx = int(2 * (1.15 ** b))
                high_idx = max(low_idx + 1, int(2 * (1.15 ** (b + 1))))
                high_idx = min(high_idx, len(fft_mag))
                val = np.mean(fft_mag[low_idx:high_idx]) if low_idx < len(fft_mag) else 0.0
                band_vals.append(val)
            max_val = max(0.01, max(band_vals))
            norm_bands = [min(1.0, v / 35.0) for v in band_vals]
        else:
            norm_bands = [0.0] * 32

        bw = 20
        bgap = 6
        bx_start = spec_x + 24
        for b, nval in enumerate(norm_bands):
            bh = int(nval * 75)
            x_bar = bx_start + b * (bw + bgap)
            y_bar = spec_y + spec_h - 12 - bh
            # Segmented look
            bar_col = C_RED if b < 4 and nval > 0.8 else C_LIME if nval > 0.6 else C_GREEN
            draw.rectangle([x_bar, y_bar, x_bar + bw, spec_y + spec_h - 12], fill=bar_col)
            # Peak dot
            draw.rectangle([x_bar, y_bar - 3, x_bar + bw, y_bar - 1], fill=C_WHITE)

        # Pipe frame to ffmpeg
        proc.stdin.write(frame.tobytes())

        if f % 150 == 0 or f == total_frames - 1:
            fps_cur = (f + 1) / (time.time() - t0)
            print(f"Frame {f+1}/{total_frames} ({t:.1f}s / {duration:.1f}s) @ {fps_cur:.1f} fps")

    proc.stdin.close()
    proc.wait()
    t1 = time.time()
    print(f"Finished rendering in {t1-t0:.2f}s! Video saved to {OUT_VIDEO}")

if __name__ == "__main__":
    main()
