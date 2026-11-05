/* SPDX-License-Identifier: GPL-3.0-only
 * ReplicantFM1: the hard techno flavour table.
 *
 * A factory preset (preset_t, felucca_engine.h) carries only P_E0..P_E7, the envelope, ENV -> FILTER, the voice
 * mode and the four sends. The things that make a hard techno sound what it is -- the 303's glide, the INSERT
 * that drives the bass into the mix, the crush on a stab -- live in parameters a preset has no field for, so a
 * preset load resets them to their defaults (ui.c param_kept).
 *
 * This table adds them back: one row per (engine, preset) that wants more than its preset_t can say. ui.c
 * apply_preset_to calls ht_flavor_apply after the preset's own values, so a load, a browse, a favourite and the
 * power-on defaults all get the same sound. A preset with no row keeps the defaults (no glide, INSERT OFF):
 * the table never changes a sound it does not name.
 *
 * Values are the parameters' own: GLIDE 0..127 (P_GLIDE, F_TIME), the INSERT's TYPE (IT_*, fx.c) and its three
 * values A B C (P_IA..P_IC, what they mean per type: params.c INS_DESC) and MIX (P_IMIX, 0..127).
 *
 * Include after fx.c (IT_*, P_*, track_t). */
#ifndef HT_FLAVOR_C
#define HT_FLAVOR_C

enum { HT_NONE = 0 };

typedef struct {
    uint8_t eng;                 /* engine index (engines.c ENGINES[]) */
    uint8_t preset;              /* index into that engine's presets[] */
    uint8_t glide;               /* P_GLIDE: portamento time, 0 = off */
    uint8_t ins;                 /* P_ITYPE: IT_OFF .. IT_CHORUS */
    uint8_t ia, ib, ic, imix;    /* P_IA .. P_IC and P_IMIX */
} ht_flavor_t;

/* ANALOG is engine 0, DRUM 10 */
static const ht_flavor_t HT_FLAVOR[] = {
    /* HT BASS: HARD insert -- a driven saw that sits under the kick without mush; no glide (a bass wants pitch) */
    {0, 12, 0, IT_HARD, 104, 66, 112, 118},
    /* HT RUMBLE: SOFT insert only, a hint of drive on the sub; the glide is kept short so the sub never slides */
    {0, 13, 4, IT_SOFT, 44, 38, 112, 92},
    /* ACID HT: no INSERT -- its clipper would flatten the filter sweep into a square; the DIST send does the damage */
    {0, 14, 38, IT_OFF, 64, 96, 96, 127},
    /* ACID 2: the same, one notch meaner */
    {0, 15, 30, IT_OFF, 64, 96, 96, 127},
    /* HT STAB: SOFT insert, no glide (chords) */
    {0, 16, 0, IT_SOFT, 78, 64, 112, 96},
    /* HT SCREAM: long glide into the sync sweep, HARD insert */
    {0, 17, 64, IT_HARD, 72, 90, 112, 100},
    /* HT SUB: nothing added; it is the clean bottom of the mix */
    {0, 18, 0, IT_OFF, 64, 96, 96, 127},
};

static const ht_flavor_t *ht_flavor_of(uint32_t eng, uint32_t preset)
{
    uint32_t i;
    for (i = 0; i < NELEM(HT_FLAVOR); i++)
        if (HT_FLAVOR[i].eng == eng && HT_FLAVOR[i].preset == preset)
            return &HT_FLAVOR[i];
    return 0;
}

/* after the preset's own values: its extras, or the defaults when it has no row */
static void ht_flavor_apply(track_t *t, uint32_t eng, uint32_t preset)
{
    const ht_flavor_t *f = ht_flavor_of(eng, preset);
    t->p[P_GLIDE] = f ? (int16_t)f->glide : TP[P_GLIDE].def;
    t->p[P_ITYPE] = f ? (int16_t)f->ins : TP[P_ITYPE].def;
    t->p[P_IA] = f ? (int16_t)f->ia : TP[P_IA].def;
    t->p[P_IB] = f ? (int16_t)f->ib : TP[P_IB].def;
    t->p[P_IC] = f ? (int16_t)f->ic : TP[P_IC].def;
    t->p[P_IMIX] = f ? (int16_t)f->imix : TP[P_IMIX].def;
}

#endif
