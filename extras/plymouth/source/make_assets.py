"""Assets for the Iron Man Plymouth theme: an arc reactor that powers up and
then idles (rotating coil ring, breathing glow), plus the HUD password field,
bullets, lock glyph, progress bar and J.A.R.V.I.S. captions."""
import math, os, sys

# Personalise the captions: ASSISTANT="F.R.I.D.A.Y." NAME="TONY" python3 make_assets.py theme
ASSISTANT = os.environ.get("ASSISTANT", "A.P.R.I.L.")
NAME = os.environ.get("NAME", "")
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = sys.argv[1] if len(sys.argv) > 1 else "ironman"
os.makedirs(OUT, exist_ok=True)

S = 300                      # reactor frame size (px, at 1080p)
SS = 3                       # supersampling
IDLE = 32                    # idle loop frames (one full coil step cycle)
BOOT = 24                    # power-up frames
ARC = (79, 195, 232); ICE = (232, 251, 255); GOLD = (232, 192, 122); RED = (200, 16, 46)
FONT = "/usr/share/fonts/TTF/JetBrainsMonoNerdFont-Bold.ttf"


def glow(img, radius, strength):
    g = img.filter(ImageFilter.GaussianBlur(radius))
    a = np.asarray(g).astype(float) * strength
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def over(base, top):
    return Image.alpha_composite(base, top)


def reactor(spin, power, pulse):
    """spin: coil rotation (rad); power 0..1 ignition; pulse 0..1 breathing."""
    N = S * SS
    c = N / 2
    lines = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(lines)
    def ring(r, w, col, a):
        d.ellipse([c - r, c - r, c + r, c + r], outline=col + (int(255 * a),), width=int(w))

    # outer housing
    ring(N * 0.46, N * 0.018, GOLD, 0.55 * power + 0.15)
    ring(N * 0.40, N * 0.006, GOLD, 0.35 * power + 0.1)
    # rotating copper coil segments
    segs = 10
    for k in range(segs):
        a0 = spin + k * 2 * math.pi / segs
        a1 = a0 + 2 * math.pi / segs * 0.62
        pts = []
        for t in np.linspace(a0, a1, 18):
            pts.append((c + N * 0.43 * math.cos(t), c + N * 0.43 * math.sin(t)))
        for t in np.linspace(a1, a0, 18):
            pts.append((c + N * 0.335 * math.cos(t), c + N * 0.335 * math.sin(t)))
        d.polygon(pts, fill=(150, 104, 52, int(255 * (0.25 + 0.6 * power))),
                  outline=GOLD + (int(255 * (0.3 + 0.6 * power)),))
    # inner energy ring and triangle core
    lit = power * (0.78 + 0.22 * pulse)
    ring(N * 0.30, N * 0.03, ARC, lit)
    ring(N * 0.255, N * 0.008, ICE, lit * 0.9)
    t = N * 0.20
    tri = [(c, c - t), (c + t * 0.866, c + t * 0.5), (c - t * 0.866, c + t * 0.5)]
    d.polygon(tri, outline=ARC + (int(255 * lit),), width=int(N * 0.028))
    d.ellipse([c - N * 0.07, c - N * 0.07, c + N * 0.07, c + N * 0.07], fill=ICE + (int(255 * lit),))

    base = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    # soft blue bloom behind everything, breathing
    bloom = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ImageDraw.Draw(bloom).ellipse([c - N * 0.3, c - N * 0.3, c + N * 0.3, c + N * 0.3],
                                  fill=ARC + (int(200 * lit),))
    base = over(base, glow(bloom, N * 0.09, 0.55 + 0.25 * pulse))
    base = over(base, glow(lines, N * 0.012, 1.6 * lit + 0.2))
    base = over(base, lines)
    return base.resize((S, S), Image.LANCZOS)


def ease(x):
    return x * x * (3 - 2 * x)


# power-up: dark -> flicker -> full, while the coil spins up
flick = [0, .15, 0, .35, .05, .6, .3, .8]
for i in range(BOOT):
    p = flick[i] if i < len(flick) else ease((i - len(flick)) / (BOOT - len(flick) - 1))
    spin = 2 * math.pi / 10 * (i / BOOT) ** 2 * 3
    reactor(spin, p, 0.5).save(os.path.join(OUT, "boot-%02d.png" % i), optimize=True)
# idle loop: coil advances exactly one segment per loop so it repeats seamlessly
for i in range(IDLE):
    ph = i / IDLE
    reactor(2 * math.pi / 10 * ph, 1.0, 0.5 + 0.5 * math.sin(2 * math.pi * ph)).save(
        os.path.join(OUT, "idle-%02d.png" % i), optimize=True)

# password field: dark HUD glass with a red -> gold frame
EW, EH = 420, 56
e = Image.new("RGBA", (EW, EH), (0, 0, 0, 0))
grad = Image.new("RGBA", (EW, EH))
for x in range(EW):
    f = x / (EW - 1)
    col = tuple(int(RED[k] * (1 - f) + (239, 177, 60)[k] * f) for k in range(3))
    ImageDraw.Draw(grad).line([(x, 0), (x, EH)], fill=col + (255,))
m = Image.new("L", (EW, EH), 0); md = ImageDraw.Draw(m)
md.rounded_rectangle([0, 0, EW - 1, EH - 1], 8, fill=255)
md.rounded_rectangle([3, 3, EW - 4, EH - 4], 6, fill=0)
e.paste(grad, (0, 0), m)
ImageDraw.Draw(e).rounded_rectangle([3, 3, EW - 4, EH - 4], 6, fill=(7, 8, 11, 235))
e.save(os.path.join(OUT, "entry.png"))

# bullet: glowing arc-blue dot
b = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
ImageDraw.Draw(b).ellipse([6, 6, 18, 18], fill=ARC + (255,))
b = over(glow(b, 3, 1.4), b)
ImageDraw.Draw(b).ellipse([9, 9, 15, 15], fill=ICE + (255,))
b.save(os.path.join(OUT, "bullet.png"))

# lock glyph beside the field: a small reactor
reactor(0.3, 1.0, 1.0).resize((96, 96), Image.LANCZOS).save(os.path.join(OUT, "lock.png"))

# progress bar
PW, PH = 360, 8
box = Image.new("RGBA", (PW, PH), (0, 0, 0, 0))
ImageDraw.Draw(box).rounded_rectangle([0, 0, PW - 1, PH - 1], 4, fill=(20, 24, 32, 255), outline=(60, 50, 40, 255))
box.save(os.path.join(OUT, "progress_box.png"))
bar = Image.new("RGBA", (PW - 4, PH - 4))
for x in range(PW - 4):
    f = x / (PW - 5)
    col = tuple(int(ARC[k] * (1 - f) + (239, 177, 60)[k] * f) for k in range(3))
    ImageDraw.Draw(bar).line([(x, 0), (x, PH - 4)], fill=col + (255,))
bar.save(os.path.join(OUT, "progress_bar.png"))

# captions
def caption(text, col, size, name, spacing=0.35):
    f = ImageFont.truetype(FONT, size)
    w = int(sum(f.getlength(ch) for ch in text) + len(text) * size * spacing) + 20
    im = Image.new("RGBA", (w, size + 16), (0, 0, 0, 0)); dd = ImageDraw.Draw(im); x = 10
    for ch in text:
        dd.text((x, 6), ch, font=f, fill=col + (255,)); x += f.getlength(ch) + size * spacing
    im = over(glow(im, 4, 0.9), im)
    im.save(os.path.join(OUT, name))
caption(ASSISTANT + "  ·  IDENTITY REQUIRED", (134, 226, 255), 17, "caption-ask.png")
caption("SYSTEMS ONLINE  ·  WELCOME BACK" + (", " + NAME.upper() if NAME else ""), (232, 192, 122), 17, "caption-boot.png")
print("frames:", BOOT, "boot +", IDLE, "idle")
