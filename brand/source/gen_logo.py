"""Generate Compass CTO logo vectors (pure filled paths, true knockouts)."""
import math, os, sys
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
from shapely import affinity
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

OUT = sys.argv[1]
FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts/package/files')
os.makedirs(OUT, exist_ok=True)

NAVY = '#0f3254'
GOLD = '#c09a4c'
GOLD_STOPS = [(0, '#a37a30'), (0.38, '#e3c674'), (0.55, '#c9a253'), (0.78, '#e8cf86'), (1, '#a8802f')]
C = 500.0          # mark centre in a 1000 x 1000 box
HALO = 9           # width of the white gap around overlapping shapes
RES = 128          # arc segments per quarter circle
PAD = 30           # clear space around the mark

def pol(theta, r):
    """Compass angle in degrees (0 = north, clockwise) -> xy."""
    t = math.radians(theta)
    return (C + r * math.sin(t), C - r * math.cos(t))

def ring(r, w, gaps=(), gap_half=0):
    ann = Point(C, C).buffer(r + w / 2, RES).difference(Point(C, C).buffer(r - w / 2, RES))
    for g in gaps:
        a, b = pol(g - gap_half, r * 2), pol(g + gap_half, r * 2)
        ann = ann.difference(Polygon([(C, C), a, pol(g, r * 2.2), b]))
    return ann

def inset_triangle(p, d):
    """Offset a triangle inward by d (exact miter offset)."""
    return Polygon(p).buffer(-d, join_style=2)

def star_point(theta, R, side_r, solid, stroke=7.5):
    tip, l, r = pol(theta, R), pol(theta - 45, side_r), pol(theta + 45, side_r)
    ccw = [tip, l, (C, C)]
    cw = [tip, (C, C), r]
    solid_tri, open_tri = (ccw, cw) if solid == 'ccw' else (cw, ccw)
    outline = Polygon(open_tri).difference(inset_triangle(open_tri, stroke))
    full = Polygon([tip, l, (C, C), r])
    return unary_union([Polygon(solid_tri), outline]), full

def needle_poly():
    return Polygon([pol(45, 325), pol(135, 66), pol(225, 325), pol(315, 66)])

def build_mark():
    needle = needle_poly()
    hub = Point(C, C).buffer(27, RES)
    mains, mains_full = zip(*[star_point(t, 422, 100, 'ccw', 9) for t in (0, 90, 180, 270)])
    diags, diags_full = zip(*[star_point(t, 330, 125, 'cw', 10) for t in (45, 135, 225, 315)])
    # round joins: mitred halos spike out past the sharp tips
    needle_halo = needle.buffer(HALO, RES // 4)
    main_halo = unary_union(mains_full).buffer(HALO, RES // 4)
    diag_halo = unary_union(diags_full).buffer(HALO, RES // 4)

    rings = unary_union([
        ring(470, 13, gaps=(0, 90, 180, 270), gap_half=9.2),
        ring(368, 40, gaps=(0, 90, 180, 270), gap_half=4.6),
        dashed_ring(222, 15, 16, 0.62),
    ])
    rings = rings.difference(unary_union([main_halo, diag_halo, needle_halo]))
    diag_shapes = unary_union(diags).difference(unary_union([main_halo, needle_halo]))
    main_shapes = unary_union(mains).difference(needle_halo)
    navy = unary_union([rings, diag_shapes, main_shapes])
    gold = needle.difference(hub)
    return navy, gold

def dashed_ring(r, w, n, duty):
    parts = []
    step = 360 / n
    for i in range(n):
        a0 = i * step + step * (1 - duty) / 2 + 9   # offset so dashes sit between star points
        a1 = a0 + step * duty
        pts = [pol(a0 + (a1 - a0) * k / 24, r) for k in range(25)]
        parts.append(LineString(pts).buffer(w / 2, cap_style=2))
    return unary_union(parts)

# ---------- text to outlines ----------
class Face:
    def __init__(self, name):
        path = os.path.join(FONTS, name)
        self.tt = TTFont(path)
        self.gs = self.tt.getGlyphSet()
        self.upm = self.tt['head'].unitsPerEm
        data = open(path, 'rb').read()
        # harfbuzz needs sfnt data; fontTools decompresses the woff2 for us
        import io
        buf = io.BytesIO(); self.tt.flavor = None; self.tt.save(buf)
        self.hbfont = hb.Font(hb.Face(buf.getvalue()))
        self.order = self.tt.getGlyphOrder()

    def shape(self, text, tracking=0):
        b = hb.Buffer(); b.add_str(text); b.guess_segment_properties()
        hb.shape(self.hbfont, b, {'kern': True, 'liga': True})
        out, x = [], 0
        for info, pos in zip(b.glyph_infos, b.glyph_positions):
            out.append((self.order[info.codepoint], x + pos.x_offset, pos.y_offset))
            x += pos.x_advance + tracking
        return out, x - tracking

    def path(self, text, size, x, y, anchor='middle', tracking=0):
        glyphs, adv = self.shape(text, tracking * self.upm / size if tracking else 0)
        s = size / self.upm
        x0 = x - adv * s / 2 if anchor == 'middle' else x
        pen = SVGPathPen(self.gs)
        for name, gx, gy in glyphs:
            tp = TransformPen(pen, (s, 0, 0, -s, x0 + gx * s, y - gy * s))
            self.gs[name].draw(tp)
        return pen.getCommands(), adv * s

    def cap_height(self, size):
        bp = BoundsPen(self.gs); self.gs['H'].draw(bp)
        return bp.bounds[3] * size / self.upm

    def width(self, text, size):
        return self.shape(text)[1] * size / self.upm

def geom_to_d(g, prec=2):
    polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
    out = []
    for p in polys:
        for ringc in [p.exterior, *p.interiors]:
            pts = list(ringc.coords)[:-1]
            out.append('M' + 'L'.join(f'{x:.{prec}f},{y:.{prec}f}' for x, y in pts) + 'Z')
    return ''.join(out)

sans = Face('montserrat-latin-700-normal.woff2')
tag_face = Face('montserrat-latin-600-normal.woff2')
serif = Face('source-serif-4-latin-600-normal.woff2')

navy_geom, gold_geom = build_mark()
navy_d = geom_to_d(navy_geom)
gold_d = geom_to_d(gold_geom)

# Cardinal letters, cap height 46, centred on the outer ring
LS = 54 / sans.cap_height(1)
letters = ''
for ch, th in (('N', 0), ('E', 90), ('S', 180), ('W', 270)):
    x, y = pol(th, 470)
    d, _ = sans.path(ch, LS, x, y + 27, 'middle')
    letters += d

def gold_defs(gid, x1, y1, x2, y2):
    stops = ''.join(f'<stop offset="{o}" stop-color="{c}"/>' for o, c in GOLD_STOPS)
    return (f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" '
            f'x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}">{stops}</linearGradient>')

# gradient runs across the needle's width (perpendicular to its axis)
gx1, gy1 = pol(315, 60); gx2, gy2 = pol(135, 60)

def mark_group(navy, gold_fill, tx=0, ty=0, scale=1):
    t = f' transform="translate({tx:.2f} {ty:.2f}) scale({scale:.4f})"' if (tx or ty or scale != 1) else ''
    return (f'<g{t}><path fill="{navy}" fill-rule="evenodd" d="{navy_d}"/>'
            f'<path fill="{navy}" d="{letters}"/>'
            f'<path fill="{gold_fill}" fill-rule="evenodd" d="{gold_d}"/></g>')

def svg(w, h, body, defs='', title='Compass CTO'):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" '
            f'width="{w:.0f}" height="{h:.0f}" role="img" aria-label="{title}">'
            f'<title>{title}</title>{"<defs>" + defs + "</defs>" if defs else ""}{body}</svg>\n')

# ---------- lockups ----------
WORD, TAG = 'Compass CTO', 'Technology, AI, & Cybersecurity'
def stacked(navy, gold_fill, defs):
    word_w, tag_w = 1155, 1080
    ws = word_w / serif.width(WORD, 1)
    ts = tag_w / tag_face.width(TAG, 1)
    W = 1240
    mx = (W - 1000) / 2
    cap = serif.cap_height(ws)
    base1 = PAD + 1000 + 105 + cap
    base2 = base1 + 119
    wd, _ = serif.path(WORD, ws, W / 2, base1)
    td, _ = tag_face.path(TAG, ts, W / 2, base2)
    H = base2 + 40
    body = mark_group(navy, gold_fill, mx, PAD) + f'<path fill="{navy}" d="{wd}"/><path fill="{navy}" d="{td}"/>'
    return svg(W, H, body, defs)

def horizontal(navy, gold_fill, defs):
    m = 0.62
    msize = (1000 + 2 * PAD) * m
    ws = 760 / serif.width(WORD, 1)
    cap = serif.cap_height(ws)
    ts = 760 / tag_face.width(TAG, 1)
    tx = msize + 70
    tag_cap = tag_face.cap_height(ts)
    block = cap + 62 + tag_cap
    top = (msize - block) / 2
    base1 = top + cap
    base2 = base1 + 62 + tag_cap
    wd, _ = serif.path(WORD, ws, tx, base1, 'start')
    td, _ = tag_face.path(TAG, ts, tx, base2, 'start')
    W = tx + 760 + PAD
    body = mark_group(navy, gold_fill, PAD * m, PAD * m, m) + f'<path fill="{navy}" d="{wd}"/><path fill="{navy}" d="{td}"/>'
    return svg(W, msize, body, defs)

def mark(navy, gold_fill, defs):
    # pad so the W and E letters clear the edges
    return svg(1000 + 2 * PAD, 1000 + 2 * PAD, mark_group(navy, gold_fill, PAD, PAD), defs)

grad = gold_defs('gold', gx1, gy1, gx2, gy2)
variants = {
    # name: (navy colour, gold fill, defs)
    '': (NAVY, 'url(#gold)', grad),                 # full colour, metallic gold
    '-flat': (NAVY, GOLD, ''),                      # full colour, solid gold (print/embroidery)
    '-reversed': ('#ffffff', 'url(#gold)', grad),   # for dark backgrounds
    '-navy': (NAVY, NAVY, ''),                      # one colour
    '-white': ('#ffffff', '#ffffff', ''),           # one colour knockout
}
for suffix, (n, g, d) in variants.items():
    for kind, fn in (('logo', stacked), ('logo-horizontal', horizontal), ('mark', mark)):
        with open(os.path.join(OUT, f'compass-cto-{kind}{suffix}.svg'), 'w') as f:
            f.write(fn(n, g, d))

# pieces for the website's animated header mark
with open(os.path.join(OUT, '_web-parts.txt'), 'w') as f:
    # lighter copy for the website: simplified to 0.5 units, 1 decimal place
    f.write(f'NAVY_D={geom_to_d(navy_geom.simplify(0.5), 1)}\nLETTERS_D={letters}\nGOLD_D={geom_to_d(gold_geom.simplify(0.5), 1)}\n'
            f'NEEDLE_D={geom_to_d(needle_poly())}\nGRAD={gx1:.1f},{gy1:.1f},{gx2:.1f},{gy2:.1f}\n')
print('ok')
