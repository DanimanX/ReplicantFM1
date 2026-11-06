/* SPDX-License-Identifier: GPL-3.0-only */
/* Roland SH-101 synthesizer engine for ReplicantFM1 */
#include "sh101.h"
#include "fastmath.h"

static const char *const oct_names[] = { "16'", "8'", "4'", "2'" };
static const char *const pw_src_names[] = { "MAN", "LFO", "ENV" };
static const char *const lfo_names[] = { "TRI", "SQR", "RND", "NOIS" };
static const char *const vca_names[] = { "ENV", "GATE" };
static const char *const sub_names[] = { "1OCT", "2OCT", "PULS" };
static const char *const glide_names[] = { "AUTO", "ON" };

static const x0x_param_t params[SH101_NPARAMS] = {
    /* Page 1: VCO */
    { "Octave", 3, 1, oct_names },
    { "Saw", 127, 100, 0 },
    { "Pulse", 127, 80, 0 },
    { "Sub", 127, 64, 0 },

    /* Page 2: PULSE */
    { "PW", 127, 64, 0 },
    { "PWMSrc", 2, 0, pw_src_names },
    { "PWMAmt", 127, 0, 0 },
    { "Noise", 127, 0, 0 },

    /* Page 3: VCF */
    { "Cutoff", 127, 64, 0 },
    { "Reso", 127, 30, 0 },
    { "EnvMod", 127, 70, 0 },
    { "Kybd", 127, 64, 0 },

    /* Page 4: ENV */
    { "Attack", 127, 5, 0 },
    { "Decay", 127, 60, 0 },
    { "Sust", 127, 40, 0 },
    { "Rel", 127, 30, 0 },

    /* Page 5: MOD */
    { "Rate", 127, 40, 0 },
    { "Wave", 3, 0, lfo_names },
    { "VCFMod", 127, 0, 0 },
    { "VCAMod", 1, 0, vca_names },

    /* Page 6: VOICE */
    { "Glide", 127, 10, 0 },
    { "GlMode", 1, 0, glide_names },
    { "SubTyp", 2, 0, sub_names },
    { "Volume", 127, 95, 0 },

    /* Page 7: PERF / EXTRA */
    { "Tune", 127, 64, 0 },
    { "Accent", 127, 64, 0 },
    { "Drive", 127, 15, 0 },
    { "Pan", 127, 64, 0 }
};

int sh101_nparams(void) { return SH101_NPARAMS; }
const x0x_param_t *sh101_param(int i) { return (i >= 0 && i < SH101_NPARAMS) ? &params[i] : 0; }
int sh101_get(const sh101_t *s, int i) { return (i >= 0 && i < SH101_NPARAMS) ? s->pot[i] : 0; }

static inline float poly_blep(float t, float dt)
{
    if (dt <= 1e-7f)
        return 0.0f;
    if (t < dt) {
        t /= dt;
        return t + t - t * t - 1.0f;
    } else if (t > 1.0f - dt) {
        t = (t - 1.0f) / dt;
        return t * t + t + t + 1.0f;
    }
    return 0.0f;
}

static inline float rng_next(uint32_t *state)
{
    *state = *state * 1664525u + 1013904223u;
    return (float)(*state >> 8) * (1.0f / 16777216.0f) * 2.0f - 1.0f;
}

static void update_env_times(sh101_t *s)
{
    /* Attack: 1 ms .. 4.0 s */
    float a = (float)s->pot[SH101_ATTACK] * (1.0f / 127.0f);
    float a_sec = 0.001f + 3.999f * a * a;
    s->atk_coef = 1.0f / (a_sec * SH101_SR);

    /* Decay: 2 ms .. 10.0 s */
    float d = (float)s->pot[SH101_DECAY] * (1.0f / 127.0f);
    float d_sec = 0.002f + 9.998f * d * d;
    s->dec_coef = 1.0f - fm_exp2f(-1.0f / (d_sec * SH101_SR * 0.1661f));

    /* Sustain level: 0 .. 1.0 */
    s->sus_lvl = (float)s->pot[SH101_SUSTAIN] * (1.0f / 127.0f);

    /* Release: 2 ms .. 10.0 s */
    float r = (float)s->pot[SH101_RELEASE] * (1.0f / 127.0f);
    float r_sec = 0.002f + 9.998f * r * r;
    s->rel_coef = 1.0f - fm_exp2f(-1.0f / (r_sec * SH101_SR * 0.1661f));
}

void sh101_set(sh101_t *s, int i, int value)
{
    if (i < 0 || i >= SH101_NPARAMS)
        return;
    if (value < 0)
        value = 0;
    if (value > params[i].max)
        value = params[i].max;
    s->pot[i] = (uint8_t)value;

    if (i == SH101_OCTAVE) {
        static const int OCT_SHIFTS[4] = { -12, 0, 12, 24 };
        s->oct_shift = OCT_SHIFTS[value & 3];
        if (s->cur_note >= 0) {
            float n = (float)(s->cur_note + s->oct_shift);
            float tune = (float)(s->pot[SH101_TUNE] - 64) * (1.0f / 64.0f);
            s->target_freq = 440.0f * fm_exp2f((n - 69.0f + tune) * (1.0f / 12.0f));
        }
    } else if (i == SH101_ATTACK || i == SH101_DECAY || i == SH101_SUSTAIN || i == SH101_RELEASE) {
        update_env_times(s);
    } else if (i == SH101_GLIDE) {
        float g = (float)value * (1.0f / 127.0f);
        if (g < 0.001f)
            s->glide_step = 1.0f;
        else {
            float g_sec = 0.005f + 0.495f * g * g;
            s->glide_step = 1.0f / (g_sec * SH101_SR);
        }
    } else if (i == SH101_PAN) {
        x0x_pan_gains(value, &s->pan_cur_l, &s->pan_cur_r);
    }
}

void sh101_init(sh101_t *s)
{
    int i;
    for (i = 0; i < SH101_NPARAMS; i++)
        s->pot[i] = params[i].def;

    s->phase = 0.0f;
    s->phase_sub = 0.0f;
    s->cur_freq = 220.0f;
    s->target_freq = 220.0f;
    s->oct_shift = 0;
    s->cur_note = -1;
    s->rng = 0x12345678u;

    s->lfo_phase = 0.0f;
    s->lfo_val = 0.0f;
    s->lfo_sh_val = 0.0f;
    s->lfo_sh_next = 0.0f;

    s->env_stage = 0;
    s->env_val = 0.0f;
    update_env_times(s);

    for (i = 0; i < 4; i++)
        s->vcf_s[i] = 0.0f;
    s->vcf_g = 0.1f;
    s->vcf_k = 0.0f;

    s->gate = 0;
    s->slide = 0;
    s->accent = 0;
    s->idle = 1;
    s->quiet = 0;

    {
        float g = (float)params[SH101_GLIDE].def * (1.0f / 127.0f);
        float g_sec = 0.005f + 0.495f * g * g;
        s->glide_step = 1.0f / (g_sec * SH101_SR);
    }
    x0x_pan_gains(params[SH101_PAN].def, &s->pan_cur_l, &s->pan_cur_r);
}

void sh101_note_on(sh101_t *s, int note, int accent, int slide)
{
    float n = (float)(note + s->oct_shift);
    float tune = (float)(s->pot[SH101_TUNE] - 64) * (1.0f / 64.0f);
    float target = 440.0f * fm_exp2f((n - 69.0f + tune) * (1.0f / 12.0f));

    s->target_freq = target;
    s->cur_note = note;
    s->accent = accent;
    s->slide = slide;

    int do_glide = (s->pot[SH101_GLIDE_MODE] == SH101_GLIDE_ON) || (slide && s->gate);
    if (!do_glide || s->idle)
        s->cur_freq = target;

    /* If not legato slide into new note, re-trigger envelope */
    if (!slide || !s->gate) {
        s->env_stage = 1; /* ATTACK */
        s->vcf_s[0] += 1e-4f; /* analog trigger kick to seed filter resonance */
    }

    s->gate = 1;
    s->idle = 0;
    s->quiet = 0;
}

void sh101_note_off(sh101_t *s)
{
    s->gate = 0;
    if (s->env_stage != 0)
        s->env_stage = 4; /* RELEASE */
}

void sh101_all_off(sh101_t *s)
{
    s->gate = 0;
    s->env_stage = 0;
    s->env_val = 0.0f;
    s->idle = 1;
    s->quiet = 0;
    for (int i = 0; i < 4; i++)
        s->vcf_s[i] = 0.0f;
}

int sh101_active(const sh101_t *s)
{
    return !s->idle;
}

void sh101_pan_settle(sh101_t *s)
{
    x0x_pan_gains(s->pot[SH101_PAN], &s->pan_cur_l, &s->pan_cur_r);
}

void sh101_render(sh101_t *s, float *out_buf, int n)
{
    if (s->idle) {
        for (int i = 0; i < n; i++)
            out_buf[i] = 0.0f;
        return;
    }

    /* Parameters */
    float saw_lvl = (float)s->pot[SH101_SAW] * (1.0f / 127.0f);
    float pulse_lvl = (float)s->pot[SH101_PULSE] * (1.0f / 127.0f);
    float sub_lvl = (float)s->pot[SH101_SUB] * (1.0f / 127.0f);
    float noise_lvl = (float)s->pot[SH101_NOISE] * (0.5f / 127.0f);
    int sub_type = s->pot[SH101_SUB_TYPE];

    float man_pw = 0.5f + 0.45f * ((float)s->pot[SH101_PW] * (1.0f / 127.0f));
    int pwm_src = s->pot[SH101_PWM_SRC];
    float pwm_amt = (float)s->pot[SH101_PWM_AMT] * (0.45f / 127.0f);

    float cutoff_base = (float)s->pot[SH101_CUTOFF] * (1.0f / 127.0f);
    float reso = (float)s->pot[SH101_RESO] * (1.05f / 127.0f); /* resonance up to 1.05 for self-osc */
    float env_mod = (float)s->pot[SH101_ENVMOD] * (1.0f / 127.0f);
    float kybd_track = (float)s->pot[SH101_KYBD] * (1.0f / 127.0f);
    float vcf_mod = (float)s->pot[SH101_VCF_MOD] * (1.0f / 127.0f);
    int vca_mode = s->pot[SH101_VCA_MODE];

    float lfo_rate = 0.1f + 29.9f * ((float)s->pot[SH101_LFO_RATE] * (1.0f / 127.0f));
    float lfo_dphase = lfo_rate * (1.0f / SH101_SR);
    int lfo_wave = s->pot[SH101_LFO_WAVE];

    float vol = (float)s->pot[SH101_VOLUME] * (1.0f / 127.0f);
    float acc_boost = s->accent ? (1.0f + 0.5f * (float)s->pot[SH101_ACCENT] * (1.0f / 127.0f)) : 1.0f;
    float drive = (float)s->pot[SH101_DRIVE] * (2.0f / 127.0f);

    float inv_sr = 1.0f / SH101_SR;

    for (int k = 0; k < n; k++) {
        /* Portamento / Pitch glide */
        if (s->cur_freq != s->target_freq) {
            float diff = s->target_freq - s->cur_freq;
            if (fm_fabsf(diff) < 0.05f) {
                s->cur_freq = s->target_freq;
            } else {
                s->cur_freq += diff * s->glide_step;
            }
        }

        /* LFO calculation */
        s->lfo_phase += lfo_dphase;
        if (s->lfo_phase >= 1.0f) {
            s->lfo_phase -= 1.0f;
            s->lfo_sh_val = s->lfo_sh_next;
            s->lfo_sh_next = rng_next(&s->rng);
        }

        switch (lfo_wave) {
        case SH101_LFO_TRI:
            s->lfo_val = (s->lfo_phase < 0.5f) ? (4.0f * s->lfo_phase - 1.0f) : (3.0f - 4.0f * s->lfo_phase);
            break;
        case SH101_LFO_SQR:
            s->lfo_val = (s->lfo_phase < 0.5f) ? 1.0f : -1.0f;
            break;
        case SH101_LFO_RND:
            s->lfo_val = s->lfo_sh_val;
            break;
        case SH101_LFO_NOIS:
            s->lfo_val = rng_next(&s->rng);
            break;
        default:
            s->lfo_val = 0.0f;
            break;
        }

        /* ADSR Envelope generation */
        switch (s->env_stage) {
        case 1: /* ATTACK */
            s->env_val += s->atk_coef * (1.2f - s->env_val);
            if (s->env_val >= 1.0f) {
                s->env_val = 1.0f;
                s->env_stage = 2; /* DECAY */
            }
            break;
        case 2: /* DECAY */
            s->env_val += (s->sus_lvl - s->env_val) * s->dec_coef;
            if (!s->gate)
                s->env_stage = 4; /* RELEASE */
            break;
        case 3: /* SUSTAIN */
            s->env_val = s->sus_lvl;
            if (!s->gate)
                s->env_stage = 4; /* RELEASE */
            break;
        case 4: /* RELEASE */
            s->env_val *= (1.0f - s->rel_coef);
            if (s->env_val < 1e-4f) {
                s->env_val = 0.0f;
                s->env_stage = 0; /* IDLE */
            }
            break;
        default:
            s->env_val = 0.0f;
            break;
        }

        /* Oscillator frequency and phase increment */
        float freq = s->cur_freq;
        float dt = freq * inv_sr;
        if (dt > 0.45f)
            dt = 0.45f;

        s->phase += dt;
        if (s->phase >= 1.0f)
            s->phase -= 1.0f;

        /* Sub-oscillator phase increment */
        float sub_div = (sub_type == SH101_SUB_1OCT_SQ) ? 0.5f : 0.25f;
        float dt_sub = dt * sub_div;
        s->phase_sub += dt_sub;
        if (s->phase_sub >= 1.0f)
            s->phase_sub -= 1.0f;

        /* 1. Sawtooth wave */
        float saw = 0.0f;
        if (saw_lvl > 0.001f) {
            saw = (2.0f * s->phase - 1.0f) - poly_blep(s->phase, dt);
        }

        /* 2. Pulse wave with PWM */
        float pulse = 0.0f;
        if (pulse_lvl > 0.001f) {
            float duty = man_pw;
            if (pwm_src == SH101_PWM_LFO)
                duty += s->lfo_val * pwm_amt;
            else if (pwm_src == SH101_PWM_ENV)
                duty += (s->env_val * 2.0f - 1.0f) * pwm_amt;
            duty = fm_clampf(duty, 0.05f, 0.95f);

            float raw_p = (s->phase < duty) ? 1.0f : -1.0f;
            raw_p += poly_blep(s->phase, dt);
            float p_shift = s->phase - duty;
            if (p_shift < 0.0f)
                p_shift += 1.0f;
            raw_p -= poly_blep(p_shift, dt);
            pulse = raw_p;
        }

        /* 3. Sub-oscillator */
        float sub = 0.0f;
        if (sub_lvl > 0.001f) {
            float sub_duty = (sub_type == SH101_SUB_2OCT_PULSE) ? 0.25f : 0.5f;
            float raw_s = (s->phase_sub < sub_duty) ? 1.0f : -1.0f;
            raw_s += poly_blep(s->phase_sub, dt_sub);
            float s_shift = s->phase_sub - sub_duty;
            if (s_shift < 0.0f)
                s_shift += 1.0f;
            raw_s -= poly_blep(s_shift, dt_sub);
            sub = raw_s;
        }

        /* 4. Noise generator */
        float noise = 0.0f;
        if (noise_lvl > 0.001f) {
            noise = rng_next(&s->rng);
        }

        /* Source mixer */
        float mix = 0.0f;
        if (s->gate || s->env_stage != 0) {
            mix = saw * saw_lvl + pulse * pulse_lvl + sub * sub_lvl + noise * noise_lvl;
        }

        /* Filter Cutoff Calculation (Roland IR3109 VCF) */
        /* Base range: 16 Hz to 20000 Hz exponential */
        float cut_norm = cutoff_base;
        /* Key follow */
        if (s->cur_note >= 0)
            cut_norm += (float)(s->cur_note + s->oct_shift - 60) * (kybd_track / 60.0f);
        /* Envelope mod */
        cut_norm += s->env_val * env_mod * (s->accent ? 1.25f : 1.0f);
        /* LFO mod */
        cut_norm += s->lfo_val * vcf_mod * 0.4f;

        cut_norm = fm_clampf(cut_norm, 0.001f, 1.2f);
        float fc = 16.0f * fm_exp2f(cut_norm * 10.3f);
        if (fc > 20000.0f)
            fc = 20000.0f;

        /* 4-pole cascaded OTA filter (Simper / Zavalishin ZDF style with non-linear saturation) */
        float g = fc * (FM_PI * inv_sr);
        if (g > 0.95f)
            g = 0.95f;
        float k_res = reso * 3.98f;

        /* Run 2 sub-steps for stability and resonant accuracy */
        float vcf_out = 0.0f;
        for (int sub_i = 0; sub_i < 2; sub_i++) {
            float feedback = k_res * fm_tanhf(s->vcf_s[3]);
            float in = mix - feedback;

            /* Stage 1 */
            s->vcf_s[0] += g * (fm_tanhf(in) - s->vcf_s[0]);
            /* Stage 2 */
            s->vcf_s[1] += g * (s->vcf_s[0] - s->vcf_s[1]);
            /* Stage 3 */
            s->vcf_s[2] += g * (s->vcf_s[1] - s->vcf_s[2]);
            /* Stage 4 */
            s->vcf_s[3] += g * (s->vcf_s[2] - s->vcf_s[3]);
        }
        vcf_out = s->vcf_s[3];

        /* VCA Mode */
        float amp = (vca_mode == SH101_VCA_ENV) ? s->env_val : (s->gate ? 1.0f : 0.0f);
        amp *= acc_boost * vol;

        float out = vcf_out * amp;

        /* Soft clipping overdrive */
        if (drive > 0.01f) {
            out = fm_tanhf(out * (1.0f + drive));
        }

        out_buf[k] = out;
    }

    /* Check if engine can idle to save CPU */
    if (!s->gate && s->env_stage == 0 && fm_fabsf(s->vcf_s[3]) < 1e-4f) {
        s->quiet += n;
        if (s->quiet > 4410) { /* 100 ms after silence */
            s->idle = 1;
        }
    } else {
        s->quiet = 0;
    }
}

void sh101_render_st(sh101_t *s, float *dry_l, float *dry_r, float *rev, float *dly, int n)
{
    float mono[SH101_MAX_BLOCK];
    int pos = 0;

    while (pos < n) {
        int blk = n - pos;
        if (blk > SH101_MAX_BLOCK)
            blk = SH101_MAX_BLOCK;

        sh101_render(s, mono, blk);
        if (rev) {
            for (int i = 0; i < blk; i++)
                rev[pos + i] = 0.0f;
        }
        if (dly) {
            for (int i = 0; i < blk; i++)
                dly[pos + i] = 0.0f;
        }

        float cur_l = s->pan_cur_l, cur_r = s->pan_cur_r;
        float tgt_l, tgt_r;
        x0x_pan_gains(s->pot[SH101_PAN], &tgt_l, &tgt_r);

        float step_l = x0x_glide_block(&cur_l, tgt_l, blk);
        float step_r = x0x_glide_block(&cur_r, tgt_r, blk);
        s->pan_cur_l = cur_l;
        s->pan_cur_r = cur_r;

        for (int i = 0; i < blk; i++) {
            float gl = cur_l + step_l * (float)i;
            float gr = cur_r + step_r * (float)i;
            dry_l[pos + i] = mono[i] * gl;
            dry_r[pos + i] = mono[i] * gr;
        }
        pos += blk;
    }
}
