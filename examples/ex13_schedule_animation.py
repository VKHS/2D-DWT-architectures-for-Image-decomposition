"""Example 13 - the six RTL schedules computing the same transform, animated.

Every panel is replayed clock by clock from ``python/rtl_model.py`` (a
bit-true model of ``rtl/dwt53_frame.v``) on the same 128 x 128 Cameraman
frame. All panels share one clock axis, so the schedules finish at their real
compute times: 0.25 N (direct 2-D), N (row-column FIR and lifting), 1.66 N
(halo tiles, TILE = 8), 1.75 N (line buffer) and 3 N (folded lifting).

* dim pixels: the intermediate frame ``mid`` of the two-pass schedules
* bright pixels: final coefficients [LL LH; HL HH] already written
* coloured pixels: coefficients written in the last frame interval

Run:  python examples/ex13_schedule_animation.py -> figures/examples/14_schedules.gif
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(ROOT / "hardware"))
import figstyle as fs  # noqa: E402
from dwt import fir, forward  # noqa: E402
from rtl_model import simulate, ARCH_NAMES  # noqa: E402
from golden import q6  # noqa: E402

FONT_DIR = Path("/usr/share/fonts/opentype/inter")
SIZE = 128            # frame side (pixels)
TILE = 8
ZOOM = 2              # display pixels per coefficient
STEPS = 72            # animation frames across 3N clocks
HOLD_MS = 2600


def font(weight: str, px: int):
    for cand in (FONT_DIR / f"Inter-{weight}.otf", Path(f"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")):
        if cand.exists():
            return ImageFont.truetype(str(cand), px)
    return ImageFont.load_default()


def hex_rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=float) / 255


def detail_glow(v, tint=(0.98, 0.93, 0.80), pct=99.6, gamma=0.55):
    lim = max(np.percentile(np.abs(v), pct), 1e-12)
    g = np.clip(np.abs(v) / lim, 0, 1) ** gamma
    return g[..., None] * np.array(tint)


def mid_image(x, vertical):
    """RGB rendering of the first-pass result [L | H] (rows) or [L; H] (columns)."""
    m = fir(x.T).T if vertical else fir(x)
    out = np.zeros(m.shape + (3,))
    if vertical:
        h = m.shape[0] // 2
        out[:h] = np.repeat(np.clip(m[:h], 0, 1)[..., None], 3, axis=2)
        out[h:] = detail_glow(m[h:])
    else:
        w = m.shape[1] // 2
        out[:, :w] = np.repeat(np.clip(m[:, :w], 0, 1)[..., None], 3, axis=2)
        out[:, w:] = detail_glow(m[:, w:])
    return out


def main():
    x8 = fs.load_image_u8("camera", SIZE)
    x = x8 / 255.0
    ref = q6(x8)
    traces = [simulate(x8, a, TILE) for a in range(6)]
    for t in traces:
        assert np.array_equal(t.coeff, ref)            # bit-exact, every schedule
    n = SIZE * SIZE
    t_end = max(t.clocks for t in traces)              # 3N (folded lifting)
    final = fs.glow_pyramid(forward(x, "lifting"), 1)
    mids = {a: mid_image(x, vertical=(a == 5)) for a in (0, 1, 5)}
    bg = hex_rgb(fs.DARK)
    colors = [hex_rgb(c) for c in fs.CAT[:6]]

    # layout ---------------------------------------------------------------
    pw = SIZE * ZOOM
    margin, gap_x, gap_y = 24, 28, 18
    head_h, label_h, foot_h = 96, 46, 44
    W = 2 * margin + 3 * pw + 2 * gap_x
    H = head_h + 2 * (label_h + pw + foot_h) + gap_y + 14
    f_title, f_sub = font("SemiBold", 22), font("Regular", 14)
    f_lab, f_name, f_foot = font("Regular", 13), font("SemiBold", 16), font("Regular", 13)
    f_clock = font("SemiBold", 16)
    ink, ink2, track = (240, 239, 236), (185, 184, 176), (42, 43, 45)

    def panel_origin(a):
        r, c = divmod(a, 3)
        return margin + c * (pw + gap_x), head_h + r * (label_h + pw + foot_h + gap_y)

    times = [round(k * t_end / STEPS) for k in range(STEPS + 1)]
    window = t_end / STEPS
    frames = []
    for t_now in times:
        im = Image.new("RGB", (W, H), tuple(int(255 * v) for v in bg))
        d = ImageDraw.Draw(im)
        d.text((margin, 18), "Six schedules, one transform, one clock", font=f_title, fill=ink)
        d.text((margin, 52), f"{SIZE} × {SIZE} Cameraman, one level, replayed clock by clock from the RTL model. "
               "Colour marks the newest writes.", font=f_sub, fill=ink2)
        clock_txt = f"clock {t_now:,}   ·   {t_now / n:.2f} N"
        cw = d.textlength(clock_txt, font=f_clock)
        d.text((W - margin - cw, 20), clock_txt, font=f_clock, fill=ink)
        for a, tr in enumerate(traces):
            ox, oy = panel_origin(a)
            done = tr.write_clock <= t_now
            fresh = done & (tr.write_clock > t_now - window)
            img = np.broadcast_to(bg, final.shape).copy()
            if a in mids:
                mdone = (tr.mid_write_clock > 0) & (tr.mid_write_clock <= t_now) & ~done
                mfresh = mdone & (tr.mid_write_clock > t_now - window)
                img[mdone] = 0.5 * mids[a][mdone] + 0.5 * bg
                img[mfresh] = 0.55 * colors[a] + 0.45 * bg       # newest intermediate writes
            img[done] = final[done]
            img[fresh] = colors[a]                               # newest coefficient writes
            tile = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8))
            im.paste(tile.resize((pw, pw), Image.Resampling.NEAREST), (ox, oy + label_h))
            d.text((ox, oy + 2), f"ARCH {a}", font=f_lab, fill=ink2)
            d.text((ox, oy + 20), ARCH_NAMES[a], font=f_name, fill=ink)
            # footer: progress bar and state
            frac = min(t_now / tr.clocks, 1.0)
            by = oy + label_h + pw + 10
            d.rounded_rectangle((ox, by, ox + pw, by + 6), radius=3, fill=track)
            if frac > 0:
                d.rounded_rectangle((ox, by, ox + max(6, int(pw * frac)), by + 6), radius=3,
                                    fill=tuple(int(255 * v) for v in colors[a]))
            if t_now >= tr.clocks:
                foot = f"done at {tr.clocks / n:.2f} N"
            elif t_now == 0:
                foot = f"needs {tr.clocks / n:.2f} N clocks"
            else:
                st = tr.states[t_now - 1]
                if st == "SEP":
                    first = t_now <= tr.clocks // 2
                    rows = (a != 5) == first
                    st = f"pass {0 if first else 1}: {'rows' if rows else 'columns'} → {'mid' if first else 'coeff'}"
                foot = f"{st}  ·  {tr.clocks / n:.2f} N total"
            d.text((ox, by + 14), foot, font=f_foot, fill=ink2)
        frames.append(im)

    # one shared palette keeps static pixels identical between frames
    picks = [STEPS // 6, STEPS // 3, STEPS // 2, 2 * STEPS // 3, 5 * STEPS // 6, STEPS]
    probe = Image.new("RGB", (W, len(picks) * H))
    for i, k in enumerate(picks):
        probe.paste(frames[k], (0, i * H))
    pal = probe.quantize(colors=255, method=Image.Quantize.MEDIANCUT)
    idx = [np.array(f.quantize(palette=pal, dither=Image.Dither.NONE)) for f in frames]
    palette = pal.getpalette()[:765] + [0, 0, 0]       # index 255 = transparent
    pframes = []
    for k, a in enumerate(idx):
        b = a.copy()
        if k:                                          # keep only pixels that changed
            b[a == idx[k - 1]] = 255
        im = Image.fromarray(b.astype(np.uint8), mode="P")
        im.putpalette(palette)
        im.info["transparency"] = 255
        pframes.append(im)
    durations = [90] * STEPS + [HOLD_MS]
    out = fs.OUT / "14_schedules.gif"
    out.parent.mkdir(parents=True, exist_ok=True)
    pframes[0].save(out, save_all=True, append_images=pframes[1:], duration=durations, loop=0,
                    optimize=False, disposal=1, transparency=255)
    frames[-1].save(fs.OUT / "14_schedules_final.png", optimize=True)
    print("wrote", out, f"({out.stat().st_size / 1e6:.2f} MB, {len(pframes)} frames)")


if __name__ == "__main__":
    main()
