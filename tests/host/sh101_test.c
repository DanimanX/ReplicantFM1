/* SPDX-License-Identifier: GPL-3.0-only */
/* Roland SH-101 engine unit tests for ReplicantFM1 */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <assert.h>
#include "sh101.h"

int main(void)
{
    sh101_t s;
    sh101_init(&s);

    printf("testing sh101...\n");

    /* 1. Parameter ranges and defaults */
    assert(sh101_nparams() == SH101_NPARAMS);
    for (int i = 0; i < SH101_NPARAMS; i++) {
        const x0x_param_t *p = sh101_param(i);
        assert(p != NULL);
        assert(p->name != NULL);
        assert(sh101_get(&s, i) == p->def);

        /* Set to max, min, restore */
        sh101_set(&s, i, p->max);
        assert(sh101_get(&s, i) == p->max);
        sh101_set(&s, i, 0);
        assert(sh101_get(&s, i) == 0);
        sh101_set(&s, i, p->def);
    }
    printf("  ok param defaults and get/set\n");

    /* 2. Initial state is idle */
    assert(sh101_active(&s) == 0);

    /* 3. Note triggering */
    sh101_note_on(&s, 60, 0, 0); /* Middle C */
    assert(sh101_active(&s) == 1);

    /* Render a block */
    float dry_l[256], dry_r[256], rev[256], dly[256];
    sh101_render_st(&s, dry_l, dry_r, rev, dly, 256);

    float energy = 0.0f;
    for (int i = 0; i < 256; i++) {
        energy += dry_l[i] * dry_l[i] + dry_r[i] * dry_r[i];
    }
    assert(energy > 1e-4f);
    printf("  ok note trigger and audio generation (energy=%.4f)\n", (double)energy);

    /* 4. Release note and verify idle transition */
    sh101_set(&s, SH101_RELEASE, 0); /* fast release */
    sh101_note_off(&s);
    for (int i = 0; i < 50; i++) {
        sh101_render_st(&s, dry_l, dry_r, rev, dly, 256);
    }
    assert(sh101_active(&s) == 0);
    printf("  ok release and idle transition\n");

    /* 5. VCA GATE mode */
    sh101_set(&s, SH101_VCA_MODE, SH101_VCA_GATE);
    sh101_set(&s, SH101_RELEASE, 0);
    sh101_note_on(&s, 48, 0, 0);
    sh101_render_st(&s, dry_l, dry_r, rev, dly, 256);
    energy = 0.0f;
    for (int i = 0; i < 256; i++) energy += dry_l[i] * dry_l[i];
    assert(energy > 1e-4f);

    sh101_note_off(&s);
    for (int i = 0; i < 50; i++) {
        sh101_render_st(&s, dry_l, dry_r, rev, dly, 256);
    }
    assert(sh101_active(&s) == 0);
    printf("  ok VCA GATE mode\n");

    /* 6. Filter self-oscillation check */
    sh101_set(&s, SH101_VCA_MODE, SH101_VCA_ENV);
    sh101_set(&s, SH101_SAW, 0);
    sh101_set(&s, SH101_PULSE, 0);
    sh101_set(&s, SH101_SUB, 0);
    sh101_set(&s, SH101_NOISE, 0);
    sh101_set(&s, SH101_RESO, 127); /* Full resonance -> self oscillation */
    sh101_set(&s, SH101_CUTOFF, 80);
    sh101_set(&s, SH101_SUSTAIN, 127);
    sh101_note_on(&s, 60, 0, 0);

    /* Prime filter */
    for (int i = 0; i < 10; i++) {
        sh101_render_st(&s, dry_l, dry_r, rev, dly, 256);
    }
    energy = 0.0f;
    for (int i = 0; i < 256; i++) {
        energy += dry_l[i] * dry_l[i];
    }
    assert(energy > 1e-5f);
    printf("  ok filter resonance self-oscillation (energy=%.4f)\n", (double)energy);

    /* 7. Sub-oscillator types */
    sh101_init(&s);
    sh101_set(&s, SH101_SAW, 0);
    sh101_set(&s, SH101_PULSE, 0);
    sh101_set(&s, SH101_SUB, 100);
    for (int t = 0; t <= 2; t++) {
        sh101_set(&s, SH101_SUB_TYPE, t);
        sh101_note_on(&s, 40, 0, 0);
        sh101_render_st(&s, dry_l, dry_r, rev, dly, 256);
        energy = 0.0f;
        for (int i = 0; i < 256; i++) energy += dry_l[i] * dry_l[i];
        assert(energy > 1e-4f);
    }
    printf("  ok sub-oscillator modes\n");

    /* 8. Portamento glide */
    sh101_set(&s, SH101_GLIDE_MODE, SH101_GLIDE_ON);
    sh101_set(&s, SH101_GLIDE, 80);
    sh101_note_on(&s, 36, 0, 0);
    sh101_render_st(&s, dry_l, dry_r, rev, dly, 256);
    sh101_note_on(&s, 60, 0, 1); /* Slide up 2 octaves */
    assert(s.cur_freq < s.target_freq); /* Glide is in progress */
    sh101_render_st(&s, dry_l, dry_r, rev, dly, 256);
    printf("  ok portamento glide\n");

    printf("ALL SH-101 TESTS PASSED!\n");
    return 0;
}
