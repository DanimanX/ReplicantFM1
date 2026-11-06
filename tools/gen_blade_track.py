#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
"""Generate the complete Blade Hard Acid Techno promo simulation script."""

def generate():
    lines = []
    def emit(cmd):
        lines.append(cmd)

    emit("# BLADE ACID TECHNO // HARD RAVE REMIX (148 BPM)")
    emit("wait 300")
    emit("tempo 148")
    emit("master 3800")
    emit("splash")
    emit("shot shot_00_splash.png")

    # --- 1. Sound Design Setup ---
    # 909 BD: Hard techno kick (clean attack click, solid sub punch, no harsh fuzz)
    emit("param 0 0 0 36")   # Tune
    emit("param 0 0 1 65")   # Attack (punchy transient click)
    emit("param 0 0 2 90")   # Decay (deep sub punch)
    emit("param 0 0 3 100")  # Level (clean unity)
    emit("param 0 0 4 35")   # Pitch depth
    emit("param 0 0 5 48")   # Pitch
    emit("param 0 0 6 20")   # Drive (subtle warm punch, not harsh)
    emit("param 0 0 7 0")    # Dist type = Off (clean punchy kick)

    # 909 SD: Snappy snare for rolls
    emit("param 0 1 0 64")   # Tune
    emit("param 0 1 1 75")   # Tone
    emit("param 0 1 2 80")   # Snappy
    emit("param 0 1 4 75")   # Level
    emit("param 0 1 5 15")   # Drive (clean)

    # 909 Clap
    emit("param 0 6 0 105")  # Level
    emit("param 0 6 2 60")   # Tail
    emit("param 0 6 3 20")   # Drive (clean)
    emit("param 0 6 5 25")   # Rev send

    # 909 Hats
    emit("param 0 7 0 85")   # CH Decay
    emit("param 0 7 1 90")   # CH Level
    emit("param 0 8 0 100")  # OH Decay (sizzling open hat)
    emit("param 0 8 1 85")   # OH Level
    emit("param 0 10 1 75")  # Ride Level

    # 303 A: Blade Acid Lead (Saw, High Reso, Smooth Warm Drive)
    emit("param 2 0 0 48")   # Cutoff (starts dark)
    emit("param 2 0 1 106")  # Reso (screaming liquid diode resonance)
    emit("param 2 0 2 92")   # EnvMod
    emit("param 2 0 3 75")   # Decay
    emit("param 2 0 4 120")  # Accent
    emit("param 2 0 5 0")    # Wave = Saw
    emit("param 2 0 6 64")   # Tune
    emit("param 2 0 7 100")  # Volume (clean unity)
    emit("param 2 0 8 35")   # Drive (warm soft drive, no harsh clipping)
    emit("param 2 0 9 1")    # DrvTyp = Soft saturation
    emit("param 2 0 10 26")  # Slide time

    # 303 B: Screaming High Counter-Acid (Square, Warm Drive)
    emit("param 2 1 0 65")   # Cutoff
    emit("param 2 1 1 110")  # Reso (screaming liquid)
    emit("param 2 1 2 92")   # EnvMod
    emit("param 2 1 3 65")   # Decay
    emit("param 2 1 4 118")  # Accent
    emit("param 2 1 5 1")    # Wave = Square
    emit("param 2 1 6 64")   # Tune
    emit("param 2 1 7 92")   # Volume
    emit("param 2 1 8 35")   # Drive (clean warm drive)
    emit("param 2 1 9 1")    # DrvTyp = Soft saturation
    emit("param 2 1 10 28")  # Slide time

    # Roland SH-101: Heavy sub/saw low-end
    emit("param 1 0 0 1")    # Octave
    emit("param 1 0 1 110")  # Saw level
    emit("param 1 0 2 60")   # Pulse level
    emit("param 1 0 3 105")  # Sub-Osc level
    emit("param 1 0 8 68")   # Cutoff
    emit("param 1 0 9 35")   # Reso
    emit("param 1 0 10 70")  # EnvMod
    emit("param 1 0 12 4")   # Attack
    emit("param 1 0 13 65")  # Decay
    emit("param 1 0 14 30")  # Sustain
    emit("param 1 0 15 25")  # Release

    # Breakbeat Slicer
    emit("param 3 0 0 100")  # BRK Level
    emit("param 5 4 0 90")   # MIX BRK Level
    emit("param 5 4 2 25")   # BRK Rev send
    emit("param 5 4 3 35")   # BRK Delay send

    # Master Compressor & FX (Clean & Punchy)
    emit("param 6 0 6 14")   # Master PUMP (14 dB musical kick-keyed ducking)
    emit("param 4 0 2 15")   # Master Tube Drive (subtle analog warmth)
    emit("param 4 0 1 0")    # Master Saturation = Off (clean mix bus)
    emit("param 4 0 8 7")    # Delay Time (1/8.)
    emit("param 4 0 9 52")   # Delay Feedback
    emit("param 4 0 11 60")  # Delay Level
    emit("param 4 1 1 45")   # Ping-Pong Width

    # Mixer Levels & Sends & Stereo Pans
    emit("param 5 0 0 100")  # 909 Level
    emit("param 5 1 0 90")   # 101 Level
    emit("param 5 2 0 100")  # 303A Level
    emit("param 5 2 2 25")   # 303A Rev send
    emit("param 5 2 3 45")   # 303A Delay send
    emit("param 5 2 4 48")   # 303A Pan (slightly Left)
    emit("param 5 3 0 95")   # 303B Level
    emit("param 5 3 2 30")   # 303B Rev send
    emit("param 5 3 3 50")   # 303B Delay send
    emit("param 5 3 4 80")   # 303B Pan (slightly Right)

    # --- 2. Sequence Programming ---
    # Drums
    emit("drumclear")
    # Closed Hat on 16ths
    for s in range(16):
        emit(f"drumstep 7 {s} 1 0")
    # Open Hat on offbeats 2, 6, 10, 14
    for s in [2, 6, 10, 14]:
        emit(f"drumstep 8 {s} 1 1")

    # 303 A: The Iconic Pump Panel Blade Acid Theme
    # Note numbers: D2=38, F2=41, G2=43, G#2=44, A2=45, C3=48, D3=50, F3=53
    # flags: 1=note, 5=accent, 9=slide, 13=acc+slide
    blade_303a = [
        (0, 38, 5),   # D2 (Punchy Accent)
        (2, 50, 13),  # D3 (Accent + Slide)
        (3, 48, 1),   # C3
        (4, 38, 5),   # D2 (Accent)
        (5, 41, 1),   # F2
        (6, 43, 9),   # G2 (Slide)
        (7, 44, 5),   # G#2 (Blue note Squeal! Accent)
        (9, 38, 1),   # D2
        (10, 50, 13), # D3 (Accent + Slide)
        (11, 53, 5),  # F3 (High Screaming Accent)
        (12, 50, 1),  # D3
        (13, 48, 1),  # C3
        (14, 45, 9),  # A2 (Slide)
        (15, 48, 9),  # C3 (Slide into D2)
    ]
    emit("bclear 0")
    for st, n, fl in blade_303a:
        emit(f"bstep 0 {st} {n} {fl}")

    # 303 B: High Screaming Counterpoint
    blade_303b = [
        (1, 50, 5),   # D3 (Accent)
        (3, 53, 1),   # F3
        (6, 57, 13),  # A3 (Accent + Slide)
        (7, 60, 1),   # C4
        (9, 50, 5),   # D3 (Accent)
        (11, 53, 13), # F3 (Accent + Slide)
        (12, 55, 1),  # G3
        (14, 57, 9),  # A3 (Slide)
        (15, 62, 13), # D4 (Top Screaming D! Accent + Slide)
    ]
    emit("bclear 1")
    for st, n, fl in blade_303b:
        emit(f"bstep 1 {st} {n} {fl}")

    # Roland SH-101: Driving Sub/Saw Pulse
    blade_101 = [
        (0, 26, 5),   # D1 (Accent)
        (2, 26, 1),   # D1
        (4, 26, 5),   # D1 (Accent)
        (6, 26, 1),   # D1
        (8, 26, 5),   # D1 (Accent)
        (10, 26, 1),  # D1
        (12, 26, 5),  # D1 (Accent)
        (14, 26, 1),  # D1
        (15, 38, 9),  # D2 (Slide)
    ]
    emit("bclear 2")
    for st, n, fl in blade_101:
        emit(f"bstep 2 {st} {n} {fl}")

    # Breakbeat Slices
    for s in range(16):
        emit(f"brkstep {s} {(s % 8) + 1}")

    # --- 3. Live Arrangement Timeline (32 bars at 148 BPM = ~51.5s) ---
    emit("partmute 1 1") # mute 101
    emit("partmute 3 1") # mute 303B
    emit("partmute 4 1") # mute BREAK

    emit("tap HOME")
    emit("shot shot_01_home_ready.png")

    emit("wav promo_blade_acid.wav")
    emit("tap PLAY")

    # Bar 1-2 (0.0s - 3.2s): Dark growling intro
    emit("wait 1620")
    emit("shot shot_02_intro_mutes.png")
    emit("param 2 0 0 54")   # Cutoff creeping up
    emit("wait 1620")
    emit("param 2 0 0 62")

    # Bar 3-4 (3.2s - 6.5s): Adding claps & rising tension
    emit("drumstep 6 4 1 1")
    emit("drumstep 6 12 1 1")
    emit("param 2 0 0 70")
    emit("wait 1620")
    emit("param 2 0 0 76")
    emit("wait 1620")

    # Bar 5 (6.5s): *** KICK DROPS IN ***
    # Four-on-the-floor kick slams in! SH-101 sub-bass un-mutes!
    emit("drumstep 0 0 1 1")
    emit("drumstep 0 4 1 0")
    emit("drumstep 0 8 1 1")
    emit("drumstep 0 12 1 0")
    emit("partmute 1 0")    # un-mute SH-101
    emit("turn ALGO 1")     # view 101/909
    emit("shot shot_03_909_playing.png")
    emit("wait 1620")
    emit("param 2 0 0 82")
    emit("wait 1620")
    emit("param 2 0 0 88")
    emit("wait 1620")
    emit("param 2 0 0 94")
    emit("wait 1620")

    # Bar 9 (13.0s): *** 303 B HIGH ACID ENTERS + RIDE CYMBALS ***
    emit("partmute 3 0")    # un-mute 303 B
    for s in range(0, 16, 2):
        emit(f"drumstep 10 {s} 1 0")
    emit("turn ALGO 1")     # view 303
    emit("shot shot_04_303a_playing.png")
    emit("wait 1620")
    emit("param 2 0 0 98")
    emit("param 2 1 0 75")
    emit("wait 1620")
    emit("param 2 0 0 102")
    emit("param 2 1 0 82")
    emit("wait 1620")
    emit("param 2 0 0 106")
    emit("param 2 1 0 90")
    emit("wait 1620")

    # Bar 13 (19.5s): Peak Dual Acid Frenzy
    emit("param 2 0 0 110")
    emit("param 2 1 0 98")
    emit("wait 1620")
    emit("param 2 0 0 114")
    emit("param 2 1 0 105")
    emit("wait 1620")
    emit("param 2 0 0 118")
    emit("param 2 1 0 112")
    emit("wait 1620")
    emit("param 2 0 0 120")
    emit("param 2 1 0 116")
    emit("wait 1620")

    # Bar 17 (26.0s): *** BREAKBEAT SLICER JOINS ***
    emit("partmute 4 0")    # un-mute BREAK
    emit("turn ALGO 2")     # view break
    emit("shot shot_06_break_slicer.png")
    emit("wait 1620")
    emit("wait 1620")
    emit("wait 1620")
    emit("wait 1620")

    # Bar 21 (32.5s): *** THE BLOOD RAVE BREAKDOWN ***
    # Kick drops out! 101 drops out! Break drops out!
    emit("drumstep 0 0 0 0")
    emit("drumstep 0 4 0 0")
    emit("drumstep 0 8 0 0")
    emit("drumstep 0 12 0 0")
    emit("drumstep 10 0 0 0")
    emit("drumstep 10 2 0 0")
    emit("drumstep 10 4 0 0")
    emit("drumstep 10 6 0 0")
    emit("drumstep 10 8 0 0")
    emit("drumstep 10 10 0 0")
    emit("drumstep 10 12 0 0")
    emit("drumstep 10 14 0 0")
    emit("partmute 1 1")    # mute 101
    emit("partmute 4 1")    # mute BREAK

    # Filter sweep down into dark sub, delay feedback rises
    emit("param 2 0 0 65")
    emit("param 2 1 0 60")
    emit("param 4 0 9 70")   # increase delay feedback
    emit("shot shot_07_breakdown.png")
    emit("wait 1620")
    emit("param 2 0 0 50")
    emit("wait 1620")

    # Build tension: Snare rolls start! Filter opens explosively!
    emit("drumstep 1 12 1 0")
    emit("drumstep 1 13 1 0")
    emit("drumstep 1 14 1 0")
    emit("drumstep 1 15 1 1")
    emit("param 2 0 0 85")
    emit("param 2 1 0 80")
    emit("wait 1620")

    # 16th-note snare roll on the final bar before drop
    for s in range(16):
        emit(f"drumstep 1 {s} 1 {(1 if s%4==0 else 0)}")
    emit("param 2 0 0 115")
    emit("param 2 1 0 110")
    emit("wait 1620")

    # Bar 25 (39.0s): *** THE MAXIMUM HARD DROP ***
    # Clear snare roll, kick slams in full force! 101 in! Break in! All 5 engines firing!
    emit("drumclear")       # clean snare roll
    emit("drumstep 0 0 1 1")
    emit("drumstep 0 4 1 0")
    emit("drumstep 0 8 1 1")
    emit("drumstep 0 12 1 0")
    emit("drumstep 6 4 1 1")
    emit("drumstep 6 12 1 1")
    for s in range(16):
        emit(f"drumstep 7 {s} 1 0")
    for s in [2, 6, 10, 14]:
        emit(f"drumstep 8 {s} 1 1")
    for s in range(0, 16, 2):
        emit(f"drumstep 10 {s} 1 0")
    emit("partmute 1 0")    # un-mute 101
    emit("partmute 4 0")    # un-mute BREAK
    emit("param 2 0 0 124") # maximum screaming cutoff
    emit("param 2 1 0 120")
    emit("param 4 0 9 55")   # reset delay feedback
    emit("param 6 0 6 15")   # Master PUMP (15 dB kick ducking on the drop)
    emit("shot shot_08_drop_pump.png")
    emit("wait 1620")
    emit("wait 1620")
    emit("wait 1620")
    emit("wait 1620")
    emit("wait 1620")
    emit("wait 1620")

    # Bar 31-32 (48.7s - 51.5s): Outro Hit & Decay
    emit("drumclear")
    emit("drumstep 0 0 1 1") # final kick hit
    emit("drumstep 9 0 1 1") # crash cymbal
    emit("partmute 1 1")
    emit("partmute 3 1")
    emit("partmute 4 1")
    emit("wait 2500")        # let reverb and delay tails wash out

    emit("tap PLAY")
    emit("wait 500")
    emit("wavstop")

    out_path = "build/blade_promo.x0x"
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Generated {out_path} with {len(lines)} commands.")

if __name__ == "__main__":
    generate()
