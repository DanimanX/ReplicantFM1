/* SPDX-License-Identifier: GPL-3.0-only
 * Copyright (C) 2026 Leo Kuroshita (@kurogedelic), Hügelton Instruments */
/* Small-canvas renderer (no full framebuffer). Draw text/lines into
 * an off-screen strip, then blit it in one DMA transfer. Pixels are stored
 * byte-swapped (the panel takes RGB565 big-endian). */
typedef struct {               /* proportional, see tools/gen_font.py */
    uint8_t h;
    uint8_t pad;               /* bitmap starts this many pixels left of the pen */
    uint8_t first, last;
    const uint8_t *adv;        /* advance per glyph */
    const uint8_t *bw;         /* bitmap width per glyph (starts FONT_PAD left of the pen) */
    const uint16_t *off;       /* byte offset of each glyph */
    const uint8_t *data;
} felucca_font_t;
#include "felucca_font.h"

#define CV_MAX (240u * 144u)      /* X0X: the main area, both bands, is 240 x 144 */
static uint16_t cv_px[CV_MAX] __attribute__((section(".pool")));
static uint32_t cv_w, cv_h;
static int32_t cv_oy;            /* y offset for graph drawing */
static int32_t cv_y0, cv_y1;     /* X0X: the rows drawing may touch (cv_band) */

#define RGB(r, g, b) ((uint16_t)((((r) >> 3) << 11) | (((g) >> 2) << 5) | ((b) >> 3)))
#define C_WHITE 0xFFFFu              /* accent only: what is being touched / where we are */
/* The screen's five steps, darkest to brightest, plus white; picked as THEME in GLOBAL. */
typedef struct {
    const char *name;
    uint16_t bg;
    uint16_t c[5];
} palette_t;
/* X0X: the first three steps are neutral greys in standard themes (structure: rules, empty cells,
 * labels); only the two brightest carry the theme's hue (values, highlights).
 * VIRUS: ReplicantFM1's default toxic green theme with near-black green ground, phosphor green
 * and acid lime highlights. */
#define NEUTRALS RGB(34, 34, 40), RGB(74, 74, 82), RGB(150, 150, 158)
static const palette_t PALETTES[] = {
    {"VIRUS", RGB(5, 13, 8), {RGB(18, 48, 25), RGB(38, 92, 48), RGB(104, 210, 114), RGB(104, 242, 96), RGB(214, 255, 64)}},
    {"GREEN", 0x0000u, {NEUTRALS, RGB(80, 220, 120), RGB(150, 255, 175)}},
    {"AMBER", 0x0000u, {NEUTRALS, RGB(232, 136, 30), RGB(255, 184, 70)}},
    {"CYAN", 0x0000u, {NEUTRALS, RGB(60, 180, 235), RGB(150, 225, 255)}},
    {"RED", 0x0000u, {NEUTRALS, RGB(232, 76, 60), RGB(255, 132, 112)}},
    {"MONO", 0x0000u, {NEUTRALS, RGB(196, 196, 202), RGB(236, 236, 240)}},
};
#define NPALETTES (sizeof(PALETTES) / sizeof(PALETTES[0]))
static uint16_t pal_bg = RGB(5, 13, 8);
#define C_BLACK pal_bg
static uint16_t pal[5] = {RGB(18, 48, 25), RGB(38, 92, 48), RGB(104, 210, 114), RGB(104, 242, 96), RGB(214, 255, 64)};
#define C_LINE pal[0]                /* 1 rules, separators */
#define C_DIM pal[1]                 /* 2 inactive, empty steps, units */
#define C_GRAY pal[2]                /* 3 labels */
#define C_AMB pal[3]                 /* 4 secondary text */
#define C_HI pal[4]                  /* 5 values, curves */

static void palette_set(uint32_t i)
{
    uint32_t k;
    pal_bg = PALETTES[i % NPALETTES].bg;
    for (k = 0; k < 5u; k++)
        pal[k] = PALETTES[i % NPALETTES].c[k];
}

static inline uint16_t swap16(uint32_t c) { return (uint16_t)(((c >> 8) & 0xFFu) | ((c & 0xFFu) << 8)); }

static void cv_begin(uint32_t w, uint32_t h, uint16_t bg)
{
    uint32_t i, n;
    if (w * h > CV_MAX)
        h = CV_MAX / w;
    lcd_sync();                     /* the last blit may still read cv_px */
    cv_w = w;
    cv_h = h;
    cv_oy = cv_y0 = 0;
    cv_y1 = (int32_t)h;
    n = w * h;
    for (i = 0; i < n; i++)
        cv_px[i] = swap16(bg);
}

/* X0X: draw the next things as if the canvas were rows y0 .. y0+h-1 alone (one band of a
 * canvas that holds several, sent in one transfer so the bands change on screen together) */
static void cv_band(int32_t y0, int32_t h)
{
    cv_oy = cv_y0 = y0;
    cv_y1 = y0 + h;
}

static void cv_blit(uint32_t x, uint32_t y) { lcd_blit(x, y, cv_w, cv_h, cv_px); }

/* canvas rows r0 .. cv_h-1 only, to screen row y + r0 */
static void cv_blit_from(uint32_t x, uint32_t y, uint32_t r0)
{
    if (r0 < cv_h)
        lcd_blit(x, y + r0, cv_w, cv_h - r0, cv_px + r0 * cv_w);
}

static inline void cv_pset(int32_t x, int32_t y, uint16_t c)
{
    y += cv_oy;
    if ((uint32_t)x < cv_w && y >= cv_y0 && y < cv_y1)
        cv_px[(uint32_t)y * cv_w + (uint32_t)x] = swap16(c);
}

static void cv_rect(int32_t x, int32_t y, int32_t w, int32_t h, uint16_t c)
{
    int32_t x1 = x + w, y1 = y + h + cv_oy, i;
    uint16_t sc = swap16(c);
    y += cv_oy;                             /* clipped once, then filled row by row */
    if (x < 0)
        x = 0;
    if (y < cv_y0)
        y = cv_y0;
    if (x1 > (int32_t)cv_w)
        x1 = (int32_t)cv_w;
    if (y1 > cv_y1)
        y1 = cv_y1;
    for (; y < y1; y++)
        for (i = x; i < x1; i++)
            cv_px[(uint32_t)y * cv_w + (uint32_t)i] = sc;
}

static void cv_line(int32_t x0, int32_t y0, int32_t x1, int32_t y1, uint16_t c)
{
    int32_t dx = x1 > x0 ? x1 - x0 : x0 - x1, sx = x0 < x1 ? 1 : -1;
    int32_t dy = y1 > y0 ? y0 - y1 : y1 - y0, sy = y0 < y1 ? 1 : -1;
    int32_t err = dx + dy, guard = 2000;
    while (guard--) {                       /* bounded: a line is never longer than 480 px */
        int32_t e2 = 2 * err;               /* both tests use the same error value */
        cv_pset(x0, y0, c);
        if (x0 == x1 && y0 == y1)
            break;
        if (e2 >= dy) {
            err += dy;
            x0 += sx;
        }
        if (e2 <= dx) {
            err += dx;
            y0 += sy;
        }
    }
}

/* glyph index of a character: lower case folds to upper case when the font
 * has none, anything missing (and C1 controls) draws as '?' */
static uint32_t glyph(const felucca_font_t *f, uint32_t ch)
{
    if (ch >= 'a' && ch <= 'z' && f->last < 'a')
        ch -= 32u;
    if (ch < f->first || ch > f->last || (ch >= 127u && ch < 160u))
        ch = '?';
    return ch - f->first;
}

/* text in colour c, each pixel's coverage blended over what is already on the canvas (an
 * anti-aliased face on a coloured box gets no dark fringe); returns the end x */
static int32_t cv_text(int32_t x, int32_t y, const felucca_font_t *f, const char *s, uint16_t c)
{
    uint32_t r = c >> 11, g = (c >> 5) & 63u, b = c & 31u;
    for (; *s; s++) {
        uint32_t gi = glyph(f, (uint8_t)*s), gx, gy, w, bpr;
        const uint8_t *gd;
        w = f->bw[gi];
        bpr = (w + 1u) / 2u;
        gd = f->data + f->off[gi];
        for (gy = 0; gy < f->h; gy++)
            for (gx = 0; gx < w; gx++) {
                uint32_t a = gd[gy * bpr + gx / 2u];
                int32_t px = x - f->pad + (int32_t)gx, py = y + (int32_t)gy + cv_oy;
                a = (gx & 1u) ? (a & 15u) : (a >> 4);
                if (!a || (uint32_t)px >= cv_w || py < cv_y0 || py >= cv_y1)
                    continue;
                if (a == 15u) {
                    cv_px[(uint32_t)py * cv_w + (uint32_t)px] = swap16(c);
                } else {
                    uint32_t bg = swap16(cv_px[(uint32_t)py * cv_w + (uint32_t)px]);
                    uint32_t br = bg >> 11, bgg = (bg >> 5) & 63u, bb = bg & 31u;
                    uint32_t nr = (r * a + br * (15u - a)) / 15u, ng = (g * a + bgg * (15u - a)) / 15u,
                             nb = (b * a + bb * (15u - a)) / 15u;
                    cv_px[(uint32_t)py * cv_w + (uint32_t)px] = swap16((nr << 11) | (ng << 5) | nb);
                }
            }
        x += f->adv[gi];
    }
    return x;
}

static int32_t text_w(const felucca_font_t *f, const char *s)
{
    int32_t w = 0;
    for (; *s; s++)
        w += f->adv[glyph(f, (uint8_t)*s)];
    return w;
}

/* one-shot: text in a box, cleared to black, blitted */
static void draw_text_box(uint32_t x, uint32_t y, uint32_t w, const felucca_font_t *f, const char *s,
                          uint16_t c, int align)
{
    int32_t tw = text_w(f, s), tx = 0;
    cv_begin(w, f->h, C_BLACK);
    if (align == 1)
        tx = ((int32_t)w - tw) / 2;
    else if (align == 2)
        tx = (int32_t)w - tw;
    cv_text(tx, 0, f, s, c);
    cv_blit(x, y);
    lcd_sync();                     /* one-shots (boot, crash, UBOOT, update) finish here */
}

static void cv_line_t(int32_t x0, int32_t y0, int32_t x1, int32_t y1, uint16_t c, int32_t thick)
{
    int32_t t;
    for (t = -thick / 2; t <= thick / 2; t++)
        cv_line(x0, y0 + t, x1, y1 + t, c);
}

/* The power-on splash: ReplicantFM1 virus particle */
#define SPL_BG   0x0061u         /* near-black green ground: RGB565 (5, 13, 8) */
#define SPL_GRN  0x6F8Cu         /* phosphor green: (104, 242, 96) */
#define SPL_DIM  0x1244u         /* capsid body: (22, 74, 34) */
#define SPL_MID  0x3C47u         /* spikes: green blended 45 % into ground */
#define SPL_SOFT 0x662Fu         /* quiet green: (96, 196, 120) */
#define SPL_ACC  0xD7E8u         /* acid lime: (214, 255, 64) */
#define SPL_TXT  0xD7FAu         /* text: (208, 255, 214) */
#define SPL_CX   120             /* particle centre */
#define SPL_CY   116
#define SPL_R    38              /* capsid radius */
#define SPL_SPIKE 13             /* spike length past capsid */
#define SPL_KNOB 5               /* knob at spike end */
#define SPL_TOP  50              /* canvas blit top */
#define SPL_CVH  130

static const int8_t SPL_DIR[8][2] = {
    {100, 0}, {71, 71}, {0, 100}, {-71, 71},
    {-100, 0}, {-71, -71}, {0, -100}, {71, -71}
};

static uint32_t spl_isqrt(uint32_t v)
{
    uint32_t r = 0, b = 1u << 30;
    while (b > v)
        b >>= 2;
    while (b) {
        if (v >= r + b) {
            v -= r + b;
            r = (r >> 1) + b;
        } else {
            r >>= 1;
        }
        b >>= 2;
    }
    return r;
}

static uint16_t spl_mix(uint16_t a, uint16_t b, uint32_t pct)
{
    static const uint8_t SH[3] = {11, 5, 0};
    static const uint16_t MK[3] = {31, 63, 31};
    uint32_t out = 0, k;
    for (k = 0; k < 3u; k++) {
        int32_t x = (a >> SH[k]) & MK[k], d = (int32_t)((b >> SH[k]) & MK[k]) - x;
        int32_t v = x + (int32_t)((d * (int32_t)pct + (d >= 0 ? 50 : -50)) / 100);
        if (v < 0)
            v = 0;
        else if ((uint32_t)v > MK[k])
            v = MK[k];
        out |= (uint32_t)v << SH[k];
    }
    return (uint16_t)out;
}

static void spl_px(int32_t x, int32_t y, uint16_t c, uint32_t pct)
{
    uint32_t i;
    if (x < 0 || y < 0 || (uint32_t)x >= cv_w || (uint32_t)y >= cv_h)
        return;
    i = (uint32_t)y * cv_w + (uint32_t)x;
    cv_px[i] = swap16(spl_mix(swap16(cv_px[i]), c, pct));
}

static void spl_disc(int32_t cx, int32_t cy, int32_t r, uint16_t c, uint32_t pct)
{
    int32_t y;
    if (r <= 0)
        return;
    for (y = cy - r; y <= cy + r; y++) {
        int32_t dy = y - cy, q, w, x;
        uint32_t rr = (uint32_t)(r * r) - (uint32_t)(dy * dy);
        q = (int32_t)spl_isqrt(rr * 16u);
        w = q >> 2;
        for (x = cx - w + 1; x <= cx + w - 1; x++)
            spl_px(x, y, c, pct);
        spl_px(cx - w, y, c, (pct * (4u - ((uint32_t)q & 3u))) / 4u);
        spl_px(cx + w, y, c, (pct * (4u - ((uint32_t)q & 3u))) / 4u);
    }
}

static void spl_spikes(int32_t cx, int32_t cy)
{
    uint32_t i;
    for (i = 0; i < 8u; i++) {
        int32_t dx = SPL_DIR[i][0], dy = SPL_DIR[i][1];
        int32_t x0 = cx + dx * (SPL_R - 12) / 100, y0 = cy + dy * (SPL_R - 12) / 100;
        int32_t x1 = cx + dx * (SPL_R + SPL_SPIKE) / 100, y1 = cy + dy * (SPL_R + SPL_SPIKE) / 100;
        cv_line_t(x0, y0, x1, y1, SPL_MID, 5);
        spl_disc(x1, y1, SPL_KNOB, SPL_GRN, 100);
        spl_disc(x1, y1, SPL_KNOB - 2, SPL_ACC, 100);
    }
}

static void spl_virus(int32_t cx, int32_t cy)
{
    uint32_t i;
    for (i = 0; i < 11u; i++)
        spl_disc(cx, cy, SPL_R + 22 - (int32_t)i * 2, SPL_GRN, 4);
    spl_spikes(cx, cy);
    spl_disc(cx, cy, SPL_R, SPL_GRN, 100);
    spl_disc(cx, cy, SPL_R - 4, SPL_DIM, 100);
    for (i = 0; i < 8u; i++) {
        int32_t x = cx + SPL_DIR[i][0] * (SPL_R - 9) / 100, y = cy + SPL_DIR[i][1] * (SPL_R - 9) / 100;
        spl_disc(x, y, 4, SPL_GRN, 55);
    }
    spl_disc(cx, cy, 15, SPL_BG, 100);
    spl_disc(cx, cy, 11, SPL_ACC, 90);
    spl_disc(cx - 4, cy - 4, 3, SPL_TXT, 75);
}

static void draw_splash(void)
{
    lcd_fill(0, 0, 240, 240, SPL_BG);
    cv_begin(240, SPL_CVH, SPL_BG);
    spl_virus(SPL_CX, SPL_CY - SPL_TOP);
    cv_blit(0, SPL_TOP);
    draw_text_box(0, 10, 240, &FONT_M, "REPLICANT FM-1", SPL_TXT, 1);
    draw_text_box(0, 34, 240, &FONT_S, "ACID GROOVEBOX", SPL_ACC, 1);
    draw_text_box(0, 192, 240, &FONT_B, "909 . 101 . 303 . BREAK", SPL_GRN, 1);
    draw_text_box(0, 214, 240, &FONT_S, "BY DANIMANX", SPL_SOFT, 1);
    lcd_sync();
}
