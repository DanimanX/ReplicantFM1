/* SPDX-License-Identifier: GPL-3.0-only */
/* Roland SH-101 monophonic synthesizer engine for ReplicantFM1.
 *
 * Models the classic Roland SH-101 (1982) analog synthesizer:
 *  - CEM3340 VCO core: band-limited Saw, Pulse with manual/LFO/ENV PWM,
 *    Sub-oscillator (-1 oct square, -2 oct square, -2 oct narrow pulse),
 *    and analog Noise generator.
 *  - Roland IR3109 4-pole (24 dB/oct) resonant low-pass filter with self-oscillation
 *    and non-linear OTA saturation.
 *  - True ADSR exponential envelope generator.
 *  - Multi-waveform LFO (Triangle, Square, Random S&H, Noise).
 *  - Switchable VCA modes (ENV vs GATE).
 *  - Portamento / Glide with Auto (legato/slide only) and On modes.
 *  - Accent dynamics and analog soft-clipping overdrive.
 */
#pragma once
#include <stdint.h>
#include "x0x_param.h"

#define SH101_SR 44100.0f
#define SH101_MAX_BLOCK 256

enum {
    /* Page 1: VCO */
    SH101_OCTAVE,      /* 0..3: "16'", "8'", "4'", "2'" */
    SH101_SAW,         /* 0..127: Sawtooth level */
    SH101_PULSE,       /* 0..127: Pulse/Square level */
    SH101_SUB,         /* 0..127: Sub-oscillator level */

    /* Page 2: PULSE */
    SH101_PW,          /* 0..127: Pulse width (manual duty 50%..95%) */
    SH101_PWM_SRC,     /* 0..2: PWM Source: "MAN", "LFO", "ENV" */
    SH101_PWM_AMT,     /* 0..127: PWM modulation amount */
    SH101_NOISE,       /* 0..127: Noise generator level */

    /* Page 3: VCF */
    SH101_CUTOFF,      /* 0..127: Cutoff frequency (~16 Hz .. 20 kHz) */
    SH101_RESO,        /* 0..127: Resonance (0 .. self-oscillation) */
    SH101_ENVMOD,      /* 0..127: Filter envelope modulation depth */
    SH101_KYBD,        /* 0..127: Keyboard tracking (0 .. 100%) */

    /* Page 4: ENV */
    SH101_ATTACK,      /* 0..127: Attack time (1 ms .. 4.0 s) */
    SH101_DECAY,       /* 0..127: Decay time (2 ms .. 10.0 s) */
    SH101_SUSTAIN,     /* 0..127: Sustain level (0 .. 100%) */
    SH101_RELEASE,     /* 0..127: Release time (2 ms .. 10.0 s) */

    /* Page 5: MOD */
    SH101_LFO_RATE,    /* 0..127: LFO rate (0.1 Hz .. 30 Hz) */
    SH101_LFO_WAVE,    /* 0..3: LFO Waveform: "TRI", "SQR", "RND", "NOIS" */
    SH101_VCF_MOD,     /* 0..127: LFO to VCF modulation depth */
    SH101_VCA_MODE,    /* 0..1: VCA Mode: "ENV", "GATE" */

    /* Page 6: VOICE */
    SH101_GLIDE,       /* 0..127: Portamento time (0 .. 500 ms) */
    SH101_GLIDE_MODE,  /* 0..1: Glide Mode: "AUTO", "ON" */
    SH101_SUB_TYPE,    /* 0..2: Sub-oscillator type: "1OCT", "2OCT", "PULS" */
    SH101_VOLUME,      /* 0..127: Master volume */

    /* Page 7: PERF / EXTRA */
    SH101_TUNE,        /* 0..127: Master tune (64 = centre A440) */
    SH101_ACCENT,      /* 0..127: Accent boost */
    SH101_DRIVE,       /* 0..127: Overdrive / saturation */
    SH101_PAN,         /* 0..127: Stereo pan (64 = centre) */

    SH101_NPARAMS
};

/* VCA modes */
enum { SH101_VCA_ENV, SH101_VCA_GATE };
/* PWM sources */
enum { SH101_PWM_MAN, SH101_PWM_LFO, SH101_PWM_ENV };
/* LFO waves */
enum { SH101_LFO_TRI, SH101_LFO_SQR, SH101_LFO_RND, SH101_LFO_NOIS };
/* Sub types */
enum { SH101_SUB_1OCT_SQ, SH101_SUB_2OCT_SQ, SH101_SUB_2OCT_PULSE };
/* Glide modes */
enum { SH101_GLIDE_AUTO, SH101_GLIDE_ON };

typedef struct {
    uint8_t pot[SH101_NPARAMS];

    /* Oscillators */
    float phase;
    float phase_sub;
    float cur_freq;
    float target_freq;
    float glide_step;
    int oct_shift;
    int cur_note;

    /* Noise */
    uint32_t rng;

    /* LFO */
    float lfo_phase;
    float lfo_val;
    float lfo_sh_val;
    float lfo_sh_next;

    /* Envelope (ADSR) */
    int env_stage;     /* 0: IDLE, 1: ATTACK, 2: DECAY, 3: SUSTAIN, 4: RELEASE */
    float env_val;
    float atk_coef;
    float dec_coef;
    float sus_lvl;
    float rel_coef;

    /* VCF (4-pole IR3109 cascade) */
    float vcf_s[4];
    float vcf_g;
    float vcf_k;

    /* Voice / Gate state */
    int gate;
    int slide;
    int accent;
    int idle;
    int quiet;

    /* Pan */
    float pan_cur_l, pan_cur_r;
} sh101_t;

void sh101_init(sh101_t *s);
void sh101_note_on(sh101_t *s, int note, int accent, int slide);
void sh101_note_off(sh101_t *s);
void sh101_all_off(sh101_t *s);
void sh101_render(sh101_t *s, float *out, int n);
void sh101_render_st(sh101_t *s, float *dry_l, float *dry_r, float *rev, float *dly, int n);
void sh101_pan_settle(sh101_t *s);
int sh101_active(const sh101_t *s);

int sh101_nparams(void);
const x0x_param_t *sh101_param(int i);
void sh101_set(sh101_t *s, int i, int value);
int sh101_get(const sh101_t *s, int i);
