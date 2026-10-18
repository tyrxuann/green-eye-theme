#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
平台无关的色彩数学（无第三方依赖）。

放在 shared/ 的原因：对比度与色差是**跨平台**的判据。
IntelliJ 的生成器自己有一份（历史原因），这里这份是给新平台用的基准实现。
"""
import colorsys


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(c)))) for c in rgb)


def hsl_hex(h, s, l):
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360.0, l / 100.0, s / 100.0)
    return rgb_to_hex([r * 255, g * 255, b * 255])


def _lin(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rel_luminance(h):
    r, g, b = (_lin(v) for v in hex_to_rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(fg, bg):
    a, b = rel_luminance(fg), rel_luminance(bg)
    hi, lo = max(a, b), min(a, b)
    return (hi + 0.05) / (lo + 0.05)


def lab(h):
    r, g, b = (_lin(v) for v in hex_to_rgb(h))
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    xn, yn, zn = 0.95047, 1.00000, 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def de2000(h1, h2):
    """CIEDE2000 色差。"""
    import math
    L1, a1, b1 = lab(h1)
    L2, a2, b2 = lab(h2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7))) if Cb else 0
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360
    h2p = math.degrees(math.atan2(b2, a2p)) % 360
    dLp, dCp = L2 - L1, C2p - C1p
    d = h2p - h1p
    dhp = d - 360 if d > 180 else (d + 360 if d < -180 else d)
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)
    Lbp, Cbp = (L1 + L2) / 2, (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    else:
        s = h1p + h2p
        hbp = (s + 360) / 2 if abs(h1p - h2p) > 180 and s < 360 else \
              ((s - 360) / 2 if abs(h1p - h2p) > 180 else s / 2)
    T = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dTh = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) if Cbp else 0
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc, Sh = 1 + 0.045 * Cbp, 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dTh)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                     + Rt * (dCp / Sc) * (dHp / Sh))


# 色觉缺陷模拟（Machado et al. 2009，severity 1.0，线性 RGB 矩阵）
CVD_MATRIX = {
    "protanopia": ((0.152286, 1.052583, -0.204868),
                   (0.114503, 0.786281, 0.099216),
                   (-0.003882, -0.048116, 1.051998)),
    "deuteranopia": ((0.367322, 0.860646, -0.227968),
                     (0.280085, 0.672501, 0.047413),
                     (-0.011820, 0.042940, 0.968881)),
}


def simulate_cvd(hex_color, kind):
    r, g, b = (_lin(v) for v in hex_to_rgb(hex_color))
    m = CVD_MATRIX[kind]
    out = [m[i][0] * r + m[i][1] * g + m[i][2] * b for i in range(3)]
    return rgb_to_hex([_lin_to_srgb(v) * 255 for v in out])


def _lin_to_srgb(c):
    c = max(0.0, min(1.0, c))
    return c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
