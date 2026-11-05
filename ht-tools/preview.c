/* SPDX-License-Identifier: GPL-3.0-only
 * ReplicantFM1: render the firmware's own power-on set (TRK_DEF + PATTERNS) to a WAV, so the sound can be
 * judged without hardware. Built and run by ht-tools/preview.sh:
 *
 *   build/ht_preview OUT.wav [BARS] [BPM]
 *
 * It includes the firmware's DSP sources as tests/hostsim.c does, sets the four tracks up exactly as main.c
 * felucca_init does (TRK_DEF: the sound, its GLIDE and INSERT from ht_flavor.c, and the boot pattern), starts the
 * transport and plays straight to the master bus. Bars 1-2 are the bare four-track beat; from bar 3 the SLICER
 * stutters track 3 for a bar, and bar 4 is the fill pattern on the drums (as SAVE > PHRASES would load them).
 */
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define __attribute__(x)
#define memset felucca_memset
#define memcpy felucca_memcpy
#define memcmp felucca_memcmp
#include "felucca_tables.h"
#include "../firmware/bsp/chip/libc.c"
#undef memset
#undef memcpy
#undef memcmp
static struct { volatile uint32_t notes, buttons; } fm1_in;
#include "../firmware/src/core.h"
#include "../firmware/src/engines.c"
#include "../firmware/src/params.c"
#include "../firmware/src/mod.c"
#include "../firmware/src/voice.c"
#include "../firmware/src/slicer.c"
#include "../firmware/src/fx.c"
#include "../firmware/src/ht_flavor.c"
static void fm1_delay_ms(uint32_t ms) { (void)ms; }
#include "../firmware/bsp/chip/usb.c"
#include "../firmware/src/midi_uart.c"
#include "../firmware/src/song_chain.c"
#include "../firmware/src/seq.c"

/* ui.c apply_preset_to's essentials (sound, sends, GLIDE, INSERT): the same values felucca_init lands on */
static void set_preset(track_t *t, uint32_t eng, uint32_t pi)
{
    static const uint8_t FX_DEF[4] = {0, 24, 28, 36};
    const engine_t *e = ENGINES[eng % NENGINES];
    const preset_t *p;
    uint32_t i;
    t->eng_req = (uint8_t)(eng % NENGINES);
    for (i = 0; i < P_E0; i++)
        t->p[i] = TP[i].def;
    if (!e->npresets)
        return;
    pi %= e->npresets;
    t->preset = (uint8_t)pi;
    p = &e->presets[pi];
    for (i = 0; i < 8u; i++)
        t->p[P_E0 + i] = p->e[i];
    t->p[P_ATK] = p->env[0], t->p[P_DEC] = p->env[1];
    t->p[P_SUS] = p->env[2], t->p[P_REL] = p->env[3];
    t->p[P_ED_FLT] = p->fenv;
    t->p[P_VOICE] = p->mono ? V_LEGATO : V_POLY;
    for (i = 0; i < 4u; i++)
        t->p[P_DIST + i] = (int16_t)(p->fx[i] ? p->fx[i] - 1 : FX_DEF[i]);
    ht_flavor_apply(t, eng % NENGINES, pi);
    t->engine = t->eng_req;                       /* (hostsim's order: the audio side claims it after the values) */
    eng_mem_claim(t);
    fm6_track_loaded(t);
}

static void put_step(track_t *t, uint32_t i, uint32_t n, const uint8_t *notes, uint32_t time, uint32_t flags)
{
    step_t *s = &t->step[i];
    uint32_t k;
    s->n = (uint8_t)n;
    for (k = 0; k < 4u; k++)
        s->note[k] = k < n ? notes[k] : 0;
    s->time = (uint8_t)time;
    s->flags = (uint8_t)flags;
    s->vel = n ? 100 : 0;
}

/* SAVE > PHRASES' load (ui.c load_pat16) as tests/hostsim.c builds a pattern: one note a step, the flags */
static void load_pattern(track_t *t, uint32_t n)
{
    const uint8_t *note = PATTERNS[n - 1u].note, *fl = PATTERNS[n - 1u].flags;
    uint32_t i;
    for (i = 0; i < NSTEP; i++)
        put_step(t, i, note[i] ? 1u : 0u, &note[i], note[i] ? ST_NOTE : ST_REST, fl[i]);
    t->p[P_SLEN] = 16;
}

static void wav_hdr(FILE *f, uint32_t frames)
{
    uint32_t v = 36 + frames * 4;
    uint16_t a = 1, ch = 2, ba = 4, bits = 16;
    uint32_t sr = FS, br = FS * 4;
    fwrite("RIFF", 1, 4, f), fwrite(&v, 4, 1, f), fwrite("WAVEfmt ", 1, 8, f);
    v = 16, fwrite(&v, 4, 1, f), fwrite(&a, 2, 1, f), fwrite(&ch, 2, 1, f);
    fwrite(&sr, 4, 1, f), fwrite(&br, 4, 1, f), fwrite(&ba, 2, 1, f), fwrite(&bits, 2, 1, f);
    fwrite("data", 1, 4, f), v = frames * 4, fwrite(&v, 4, 1, f);
}

int main(int argc, char **argv)
{
    uint32_t i, k, bars = argc > 2 ? (uint32_t)atoi(argv[2]) : 8u;
    int32_t bpm = argc > 3 ? atoi(argv[3]) : 150;
    uint32_t frames, f, clip = 0, filled = 0, e2 = 12, p2 = 4;
    int32_t peak = 0;
    FILE *w;
    if (argc < 2) {
        fprintf(stderr, "usage: %s OUT.wav [BARS] [BPM]\n", argv[0]);
        return 2;
    }
    for (i = 0; i < G_COUNT; i++)
        song.g[i] = GP[i].def;
    song.g[G_BPM] = (int16_t)bpm;                 /* main.c felucca_init */
//    fm6_init();
    /* the boot set's patterns: HT BASS, HT STAB, HT ACID, HT KICK (PATTERNS 16, 17, 15, 14) */
    static const uint8_t BOOT_PAT[NTRK] = {16, 5, 15, 14};
    static const uint8_t ALT_PAT[NTRK] = {16, 17, 15, 14};   /* the FM track on the stab instead of the pad line */
    const uint8_t *BP = getenv("ALTPAT") ? ALT_PAT : BOOT_PAT;
    for (i = 0; i < NTRK; i++) {
        track_t *t = &trk[i];
        for (uint32_t q = 0; q < P_E0; q++)          /* track_defaults (ui.c) */
            t->p[q] = TP[q].def;
        if (i == 0 && getenv("P1"))
            sscanf(getenv("P1"), "%u:%u", &e2, &p2), set_preset(t, e2, p2);
        else if (i == 1 && getenv("P2"))
            sscanf(getenv("P2"), "%u:%u", &e2, &p2), set_preset(t, e2, p2);
        else
            set_preset(t, TRK_DEF[i][0], TRK_DEF[i][1]);
        for (uint32_t q = 0; q < NSTEP; q++)        /* track_defaults_steps (ui.c): every step a rest */
            t->step[q].time = ST_REST;
        load_pattern(t, BP[i]);              /* SEQ > PATTERNS would load these (TRK_DEF's sequencers boot empty) */
    }
    {   /* SOLO=n: only that part (the others' LEVEL 0), to judge the balance */
        const char *so = getenv("SOLO");
        if (so) {
            uint32_t n = (uint32_t)atoi(so);
            for (i = 0; i < NTRK; i++)
                if (i + 1u != n)
                    trk[i].p[P_LEVEL] = 0;
        }
    }
    song.sel = 0;
    song.master_q12 = 4096;
    if (!(w = fopen(argv[1], "wb"))) {
        perror(argv[1]);
        return 1;
    }
    frames = (uint32_t)((double)FS * 60.0 / bpm * 4.0 * bars);
    wav_hdr(w, frames);
    transport_req = 1;
    for (f = 0; f < frames; f += CTL) {
        int32_t o[2 * CTL];
        uint32_t bar = f * (uint32_t)bpm / (FS * 240u);   /* the bar it is in */
        /* a short performance: the SLICER stutters the acid on bar 3, the fill lands on bar 4, then back */
        if (bar == 2u && trk[2].p[P_SLCR] == SL_OFF) {
            trk[2].p[P_SLCR] = SL_STUT;
            trk[2].p[P_SLRATE] = 1;
        } else if (bar == 3u && trk[2].p[P_SLCR] != SL_OFF) {
            trk[2].p[P_SLCR] = SL_OFF;
            load_pattern(&trk[3], 18);                   /* the fill */
            filled = 1;
        } else if (bar == 4u && trk[3].p[P_SLEN] == 16 && filled) {
            load_pattern(&trk[3], 14);                   /* back to the beat */
        }
        mix_block(o, CTL);
        for (i = 0; i < 2u * CTL; i++) {
            if (o[i] > peak)
                peak = o[i];
            if (o[i] < -peak)
                peak = -o[i];
            if (o[i] > 32700 || o[i] < -32700)
                clip++;
        }
        for (i = 0; i < 2 * CTL; i++) {
            int16_t s = (int16_t)(o[i] > 32767 ? 32767 : o[i] < -32768 ? -32768 : o[i]);
            fwrite(&s, 2, 1, w);
        }
        (void)k;
    }
    fclose(w);
    printf("rendered %s: %u bars at %d BPM, peak %.1f dBFS, %u samples at the rail\n", argv[1], bars, bpm,
           20.0 * log10(peak / 32768.0), clip);
    return 0;
}
