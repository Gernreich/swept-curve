#!/usr/bin/env python3
"""An interactive view of a ribbon bore: drag to turn.

    python3 ribbon_view.py --shape=serpentine \
        --out=serpentine/ribbon-serpentine-bore10-30deg-3lobes-R72/ribbon-serpentine-bore10-30deg-3lobes-R72.html

Takes the generator's own flags, read by ribbon_bore.read_flags(), plus --out
(required), --home, --embed and --trace. The page goes beside the cut files it
belongs to, so a
design folder holds the thing you cut and the thing you turn around, and they
cannot drift apart.

It draws the AIRWAY first - the passage the air actually takes, bounded by
the wall faces at +-bore/2 and the cheeks at +-bore/2. That is why it exists:
the bore came out 3mm narrow for a week because nothing drew the space inside
it, and a picture of the plywood alone would not have shown that.

It draws the airway ALONE. It also drew the two cheek plates at full band
width for a while, so the picture would not read as a thinner object than the
part you cut, but a solid slab above and below the passage is what you look
through to see the passage, and it hid the shape this page exists to show.
Six faces, not eight. Colour by face to tell them apart.

Nothing here gates anything. check the cut files with ribbon_bore.py; this is
for looking.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ribbon_bore as B                                        # noqa: E402


def wheel(n):
    """n colours around the hue circle, kept clear of each other."""
    out = []
    for i in range(max(n, 1)):
        h = (i * 360.0 / max(n, 1) + 15) % 360
        c, x = 0.62, 0.62 * (1 - abs((h / 60) % 2 - 1))
        r, g, b = [(c, x, 0), (x, c, 0), (0, c, x),
                   (0, x, c), (x, 0, c), (c, 0, x)][int(h // 60) % 6]
        m = 0.30
        out.append('#%02x%02x%02x' % (int((r + m) * 255), int((g + m) * 255),
                                      int((b + m) * 255)))
    return out


def port_spans(c):
    """Each port as (segment index, t0, t1) along that segment, mouth first.

    THE PAGE DRAWS THE OPENING, NOT THE DRAWN LINE. port_hole() returns the
    polygon the laser follows, which is BURN under size because the kerf opens
    it; the hole in the finished part is PORT_ACROSS x PORT_ALONG exactly, and
    that is the hole air goes through. So the centre comes from the same
    PORT_FROM_TIP the generator uses and the size from the same two constants,
    with the kerf deliberately left out. 0.15mm on a 10mm port, and drawing the
    cut line here would be drawing the tool rather than the passage.
    """
    if not B.PORT:
        return []
    # Range and distinctness of --port-at are refused by port_holes(), in the
    # generator; this used to draw a page for a facet named twice.
    B.port_holes(c)
    out = []
    # WHICH SEGMENTS THE PORTS SIT ON. Under --port-at the flag says, and a
    # facet index IS a segment index, walked forward from vertex i exactly as
    # port_hole() walks it. Otherwise the two run ends, which is where the
    # generator puts them and where this drew them before the flag existed.
    #
    # This was a SECOND COPY of that rule and it had already gone wrong once in
    # the only way it could: --port-at moved the holes and this went on drawing
    # them at the seam, because it asked PORT_BOTH a question only port_holes()
    # can answer. Kept as an index-and-t rather than replaced by port_holes()
    # because the page draws the OPENING and that function returns the cut line
    # -- BURN under size -- but the PLACEMENT now comes from one flag, not two
    # readings of one.
    if B.PORT_AT is not None:
        places = [(i, +1) for i in B.PORT_AT]
    else:
        places = [(0, +1)] + ([(len(c) - 2, -1)] if B.PORT_BOTH else [])
    for i, sgn in places:
        L = B.seglen(c[i], c[i + 1])
        half = B.PORT_ALONG / 2
        lo, hi = B.PORT_FROM_TIP - half, B.PORT_FROM_TIP + half
        # measured from the TIP, which is station 0 at the mouth and the last
        # station at the far end -- so the far end's t runs the other way
        t0, t1 = (lo / L, hi / L) if sgn > 0 else (1 - hi / L, 1 - lo / L)
        if not (0 <= t0 < t1 <= 1):
            where = (f'facet {i}' if B.PORT_AT is not None
                     else 'the lead it sits on')
            raise ValueError(
                f'the port at {B.PORT_FROM_TIP:g}mm from the tip, '
                f'{B.PORT_ALONG:g}mm long, does not fit inside the '
                f'{L:.1f}mm of {where}. Lengthen --lead or move '
                f'--port-from-tip.')
        out.append((i, t0, t1))
    return out


def framed(V, a, d, h, i, t0, t1, s0, s1, top):
    """The cheek face of segment i as eight quads around a rectangular hole.

    Appends the grid's new corners to V and returns the quads. The centre cell
    is the port and is simply not emitted -- a hole in this drawing is absence,
    because the page draws the airway's boundary and not the 3mm of ply the
    hole is cut through.

    Cells of no area are dropped, which is what makes a BORE-wide square port
    work: PORT_ACROSS equals the bore, so s0 is 0 and s1 is 1, the two side
    columns collapse, and the face comes out as the two quads either side of
    the opening rather than eight with six of them degenerate.

    The grid interpolates the quad's own corners rather than stepping out from
    the centreline, so the hole's long edges follow the face they are cut in.
    Where a mitre widens that face -- 0.18mm a side at 30 degrees -- the hole
    flares by the same fraction across its length. It is a picture; the number
    is under two tenths of a millimetre, and the alternative is a hole that
    does not lie in the surface it is cut from.
    """
    z = h if top else -h
    def at(t, ss):
        ax = a[i][0] + (a[i + 1][0] - a[i][0]) * t
        ay = a[i][1] + (a[i + 1][1] - a[i][1]) * t
        dx = d[i][0] + (d[i + 1][0] - d[i][0]) * t
        dy = d[i][1] + (d[i + 1][1] - d[i][1]) * t
        V.append([round(ax + (dx - ax) * ss, 3),
                  round(ay + (dy - ay) * ss, 3), round(z, 3)])
        return len(V) - 1
    ts, ss = [0.0, t0, t1, 1.0], [0.0, s0, s1, 1.0]
    grid = [[at(t, u) for u in ss] for t in ts]
    out = []
    for r in range(3):
        for k in range(3):
            if r == 1 and k == 1:
                continue                      # the port
            if ts[r + 1] - ts[r] < 1e-9 or ss[k + 1] - ss[k] < 1e-9:
                continue                      # a cell of no area
            p00, p01 = grid[r][k], grid[r][k + 1]
            p11, p10 = grid[r + 1][k + 1], grid[r + 1][k]
            v = ([p00, p01, p11, p10] if top else [p00, p10, p11, p01])
            out.append({'v': v, 'f': 2 if top else 3, 's': i})
    return out


# --ends: the bell in the port and the mouthpiece on the far end, as the built
# spiral has them. Both are drawn from their own cut files by trumpet-elbows-
# allowed's part-view.py, read out of that checkout beside this one rather than
# copied, so a redesigned bell or mouthpiece redraws here too. The cheeks are
# not drawn (see "ribbon_view.py draws the airway" in NOTES.md), so the bell
# stands 3mm off the airway: that gap is the cheek it seats on. The mouthpiece's
# 16mm plate butts the tube end, where the walls are.
ENDS = False
PARTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                     'trumpet-elbows-allowed', 'parts')
BELL_SVG = 'bell/cut-files/bell-round10-153mm-17rings-x3-rim86-cut-files.svg'
MOUTHPIECE_SVG = 'mouthpiece/cut-files/mouthpiece-bore10-trumpet-parts-cut-files.svg'
# part-view.py's own face order is ring face, outside, the bore, underside;
# these are its four shades, so the ends read the way they do on their pages
END_SHADE = [1.06, 0.95, 0.6, 0.72]


def part_view():
    """trumpet-elbows-allowed's part-view.py, imported from its file. It reads
    bell-view.py's helpers by executing that script up to the line that reads
    argv, and that prefix checks argv is long enough, so give it two names."""
    import importlib.util
    f = os.path.join(PARTS, 'part-view.py')
    if not os.path.exists(f):
        sys.exit('ribbon_view: --ends draws the bell and mouthpiece from '
                 'trumpet-elbows-allowed, and needs that repository cloned '
                 'beside this one.')
    argv, sys.argv = sys.argv, ['part-view.py', '-', '-']
    try:
        spec = importlib.util.spec_from_file_location('part_view', f)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
    finally:
        sys.argv = argv
    return m


def place(V, Q, part, origin, ex, ez, f):
    """Append a part-view solid to V and Q, its local x along ex and z along ez.
    ey = ez x ex, so the map is a rotation and every face keeps its winding."""
    ey = [ez[1] * ex[2] - ez[2] * ex[1], ez[2] * ex[0] - ez[0] * ex[2],
          ez[0] * ex[1] - ez[1] * ex[0]]
    base = len(V)
    for x, y, z in part['V']:
        V.append([origin[k] + x * ex[k] + y * ey[k] + z * ez[k] for k in range(3)])
    for q in part['Q']:
        Q.append({'v': [base + i for i in q['v']], 'f': f, 's': 0,
                  'k': END_SHADE[q['f']]})


def ends(c, V, Q, spans, h):
    """With a port: the bell standing on the outside of the bottom cheek over
    it, and the mouthpiece on the far end, as the built spiral has them. With
    none: the mouthpiece on the mouth and the bell on the far end, each on the
    tube end. Returns what the panel says."""
    pv = part_view()
    bell = pv.data_for(os.path.join(PARTS, BELL_SVG), 32)
    mp = pv.data_for(os.path.join(PARTS, MOUTHPIECE_SVG), 32)
    if not spans:
        L = B.seglen(c[0], c[1])
        t = [(c[0][0] - c[1][0]) / L, (c[0][1] - c[1][1]) / L, 0.0]
        place(V, Q, mp, [c[0][0], c[0][1], 0.0], [-t[1], t[0], 0.0], t, 7)
        L = B.seglen(c[-2], c[-1])
        t = [(c[-1][0] - c[-2][0]) / L, (c[-1][1] - c[-2][1]) / L, 0.0]
        place(V, Q, bell, [c[-1][0], c[-1][1], 0.0], [-t[1], t[0], 0.0], t, 6)
        return {'bell': f"{bell['rings']} rings, {bell['height']:g}mm, "
                        f"\u00f8{bell['rim']:g} rim, on the far end",
                'mouthpiece': f"{mp['rings']} rings, {mp['height']:g}mm, "
                              f"on the mouth", 'port': False}
    i, t0, t1 = spans[0]
    tm = (t0 + t1) / 2
    px = c[i][0] + (c[i + 1][0] - c[i][0]) * tm
    py = c[i][1] + (c[i + 1][1] - c[i][1]) * tm
    L = B.seglen(c[i], c[i + 1])
    u = [(c[i + 1][0] - c[i][0]) / L, (c[i + 1][1] - c[i][1]) / L, 0.0]
    place(V, Q, bell, [px, py, -(h + B.THICK)], u, [0.0, 0.0, -1.0], 6)
    L = B.seglen(c[-2], c[-1])
    t = [(c[-1][0] - c[-2][0]) / L, (c[-1][1] - c[-2][1]) / L, 0.0]
    place(V, Q, mp, [c[-1][0], c[-1][1], 0.0], [-t[1], t[0], 0.0], t, 7)
    return {'bell': f"{bell['rings']} rings, {bell['height']:g}mm, "
                    f"\u00f8{bell['rim']:g} rim, on the port",
            'mouthpiece': f"{mp['rings']} rings, {mp['height']:g}mm, "
                          f"on the far end", 'port': True}


def data_for():
    """Vertices and quads for the airway, plus what each face is."""
    c = B.centreline()
    # the airway's own boundary: the wall FACES, at +-bore/2. Not wall_off(),
    # which is where the walls' centrelines sit.
    a = B.offset(c, B.BORE / 2)
    d = B.offset(c, -B.BORE / 2)
    if sum(B.seglen(p, q) for p, q in zip(a, a[1:])) > \
       sum(B.seglen(p, q) for p, q in zip(d, d[1:])):
        a, d = d, a                       # a is the inner wall
    h = B.BORE / 2

    V, Q = [], []
    for i in range(len(c)):
        V += [[a[i][0], a[i][1], -h], [a[i][0], a[i][1], h],
              [d[i][0], d[i][1], h], [d[i][0], d[i][1], -h]]
    shut = (abs(c[0][0] - c[-1][0]) < 1e-6 and abs(c[0][1] - c[-1][1]) < 1e-6)
    # A port goes through BOTH cheeks: they are one part cut twice, so the hole
    # is a socket right through and you plug the side you are not using. Both
    # cheek faces therefore lose the same rectangle.
    spans = port_spans(c)
    across = (1 - B.PORT_ACROSS / B.BORE) / 2 if B.PORT else 0.0
    # WHICH CHEEK EACH PORT IS IN. Without --port-per-cheek a port goes through
    # both, because the cheek is one part cut twice -- a socket right through,
    # and you plug the side you are not using. With it the two ports are drawn
    # on different sheets, so the mouth opens through the TOP cheek and the far
    # end through the BOTTOM, and the instrument is blown into one face with
    # the bell leaving the other. The page has to say which, because a picture
    # showing both holes in both faces is a picture of a part nobody cut.
    if B.PORT_PER_CHEEK:
        top_h = {spans[0][0]: spans[0][1:]}
        bot_h = {spans[1][0]: spans[1][1:]}
    elif ENDS:
        # Drawn as built, the bell is seated in the bottom cheek's port, and
        # the same hole in the top cheek is the side you are not using, which
        # is plugged. Drawn open, it was a window straight down the bell's
        # throat from the back (the author, 2026-10-14).
        top_h = {}
        bot_h = {i: (t0, t1) for i, t0, t1 in spans}
    else:
        top_h = bot_h = {i: (t0, t1) for i, t0, t1 in spans}
    for i in range(len(c) - 1):
        p, q = 4 * i, 4 * (i + 1)
        Q.append({'v': [p + 0, p + 1, q + 1, q + 0], 'f': 0, 's': i})   # inner
        Q.append({'v': [p + 3, q + 3, q + 2, p + 2], 'f': 1, 's': i})   # outer
        if i in top_h:
            Q += framed(V, a, d, h, i, *top_h[i], across, 1 - across, True)
        else:
            Q.append({'v': [p + 1, p + 2, q + 2, q + 1], 'f': 2, 's': i,
                      'm': [1, 3]})                                    # top
        if i in bot_h:
            Q += framed(V, a, d, h, i, *bot_h[i], across, 1 - across, False)
        else:
            Q.append({'v': [p + 0, q + 0, q + 3, p + 3], 'f': 3, 's': i,
                      'm': [0, 2]})                                    # bottom
    # 'm' names a cheek quad's two edges that run ALONG the duct. Its other two
    # lie on mitres, and a cheek is one part cut whole, so outlining every
    # facet drew it as a row of separate plates, one per wall panel (the
    # author, 2026-10-14). By face, those mitre edges take the fill colour and
    # only the edges along are outlined; by facet, every facet keeps its outline.
    # The two cheek plates used to be drawn here as well, at full band width,
    # 3mm proud of the airway top and bottom -- faces 6 and 7, 'ply, top' and
    # 'ply, bottom'. They are gone (2026-09-13): every view of the inside was
    # through a slab of ply, which is the one thing this page must not do.
    # What they were there for -- that the part is 20mm across where the
    # passage is 10 -- the numbers panel says in words, and the cut files show.

    n = len(c) - 1
    nb = len(V)                           # the airway's vertices end here
    endnote = None
    if ENDS:
        endnote = ends(c, V, Q, spans, h)
    if not shut:
        Q.append({'v': [0, 1, 2, 3], 'f': 4, 's': 0})                   # mouth
        Q.append({'v': [4*n+3, 4*n+2, 4*n+1, 4*n+0], 'f': 5, 's': n-1})  # far end
    # a closed ring has no mouth and no far end; the last station IS the first,
    # so its four vertices are already coincident with station 0's

    # The quoted radius is the generator's own, read from bend_radius(). This
    # file had a second copy of that table and both fell through to RADIUS for
    # any shape not listed, so the scallop and the racetrack pages said R30.
    R = B.bend_radius()
    return {
        'V': [[round(v, 3) for v in p] for p in V],
        'Q': Q,
        'bore': B.BORE,
        'mm': round(sum(B.seglen(p, q) for p, q in zip(c, c[1:])), 1),
        'facet': B.FACET,
        'shape': B.SHAPE,
        # What curve the vertices were placed on. Two constructions are in use
        # and the drawing cannot tell them apart, so the panel says which:
        # every shape but 'double-spiral' is built from arcs whose radius holds all
        # the way across, and 'double-spiral' samples a smooth Archimedean spiral.
        # See "Which curve each shape's vertices sit on" in NOTES.md.
        'curve': {'double-spiral': 'Archimedean spiral, sampled',
                  'double-volute': 'chain of semicircles',
                  'spiral': 'compass spiral, stepping arcs',
                  'traced': 'traced stations'}.get(
                      B.SHAPE, 'constant-radius arcs'),
        'rrange': ([round(B.SPIRAL_RI, 1), round(B.SPIRAL_RO, 1)]
                   if B.SHAPE == 'spiral' else None),
        'flat': B.SHAPE == 'spiral',
        'R': R,
        'segs': n,
        'over': round(100 * (1 / math.cos(math.radians(B.FACET) / 2) - 1), 2),
        'pal': wheel(n),
        'shut': shut,
        # always six, in face-index order; the key shows only the ones the
        # quads actually use, so a closed ring drops mouth and far end by
        # itself rather than by shifting every index after them
        # A CAP IS NOT A MOUTH, and the page said it was. cap()'s own note
        # settles which end it closes: "the mouthpiece goes into the port and
        # the run simply stops a bore further on", so the plate covers the stub
        # past the port, at the MOUTH. With --port-both there is such a stub at
        # each end and caps() draws two, so both ends are shut and the bore
        # breathes through the ports alone. Drawn as openings, those two faces
        # were the only holes on a page whose real holes it did not draw.
        'faces': ['inner wall', 'outer wall', 'top cheek', 'bottom cheek',
                  'cap (mouth)' if B.CAP else 'mouth',
                  'cap (far end)' if B.CAP and B.PORT_BOTH else 'far end',
                  'bell', 'mouthpiece'],
        'facecol': ['#5aa9e6', '#3d7ebd', '#c9d6e3', '#8fa3b8',
                    '#b08968' if B.CAP else '#1c1c20',
                    '#b08968' if B.CAP and B.PORT_BOTH else '#e0457b',
                    '#d8b445', '#8a5a2b'],
        'nb': nb,
        'ends': endnote,
        'ports': len(spans),
        'portsize': [B.PORT_ACROSS, B.PORT_ALONG] if B.PORT else None,
        'percheek': B.PORT_PER_CHEEK,
    }


HTML = r'''<title>__TITLE__</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{color-scheme:dark;--bg:#14161a;--ink:#e8eaed;--dim:#9aa3ad;--line:#2a2f36;
      --panel:#1b1e24;--accent:#e0457b;--edge:rgba(0,0,0,.30);
      --btn:#232830;--swring:rgba(255,255,255,.35)}
:root[data-theme=light]{color-scheme:light;--bg:#f7f5f1;--ink:#1b1e24;--dim:#5f6873;
      --line:#dcd7cd;--panel:#fffdf9;--btn:#efebe4;--swring:rgba(0,0,0,.28)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:14px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:14px 18px 10px;border-bottom:1px solid var(--line)}
h1{margin:0;font-size:17px;font-weight:650;letter-spacing:-.01em}
.sub{color:var(--dim);font-size:13px;margin-top:3px}
.sub b{color:var(--ink);font-weight:600}
main{display:grid;grid-template-columns:1fr 220px;gap:0;height:calc(100vh - 62px);
     min-height:420px}
#wrap{position:relative;overflow:hidden}
canvas{display:block;width:100%;height:100%;cursor:grab;touch-action:none}
canvas.drag{cursor:grabbing}
aside{border-left:1px solid var(--line);padding:14px;overflow:auto;background:var(--panel)}
h2{margin:0 0 8px;font-size:11px;letter-spacing:.09em;text-transform:uppercase;
   color:var(--dim);font-weight:600}
.grp{margin-bottom:18px}
button{font:inherit;color:var(--ink);background:var(--btn);border:1px solid var(--line);
       border-radius:6px;padding:5px 9px;cursor:pointer;margin:0 4px 4px 0}
button[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:#fff}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
input[type=range]{width:100%;accent-color:var(--accent)}
.key{display:flex;align-items:center;gap:7px;margin:3px 0;font-size:12.5px}
/* the mouth's swatch is near-black on a near-black panel, so every swatch
   gets an outline rather than that one getting a special case */
.sw{width:12px;height:12px;border-radius:3px;flex:0 0 auto;
    box-shadow:inset 0 0 0 1px var(--swring)}
.hint{color:var(--dim);font-size:12px;margin-top:10px}
.chk{display:flex;align-items:center;gap:7px;font-size:12.5px;cursor:pointer}
.chk input{accent-color:var(--accent);margin:0}
dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:2px 10px;font-size:12.5px}
dt{color:var(--dim)}dd{margin:0;text-align:right;font-variant-numeric:tabular-nums}
@media (max-width:720px){main{grid-template-columns:1fr;height:auto}
  #wrap{height:56vh}aside{border-left:0;border-top:1px solid var(--line)}}
</style>
<script>
/* Follow the theme the site's pages store, so a framed viewer matches the page around it. */
(function () {
  var r = document.documentElement;
  function apply() { var t = null; try { t = localStorage.getItem('ctg-theme'); } catch (e) {}
    if (t === 'light' || t === 'dark') r.setAttribute('data-theme', t); else r.removeAttribute('data-theme'); }
  apply(); addEventListener('storage', function (e) { if (e.key === 'ctg-theme') apply(); });
})();
</script>
<header>
  <h1>__TITLE__</h1>
  <div class="sub" id="sub"></div>
</header>
<main>
  <div id="wrap"><canvas id="c"></canvas></div>
  <aside>
    <div class="grp"><h2>Colour</h2>
      <button id="m-face" aria-pressed="true">by face</button>
      <button id="m-sec" aria-pressed="false">by facet</button>
    </div>
    <div class="grp"><h2>Reveal</h2>
      <input id="rev" type="range" min="1" max="1" value="1">
      <div class="hint" id="revn"></div>
    </div>
    <div class="grp"><h2>Key</h2><div id="key"></div></div>
    <div class="grp"><h2>Numbers</h2><dl id="nums"></dl></div>
    <div class="hint">Drag to turn. Right-drag, shift-drag or two fingers to pan. Scroll or pinch to zoom. Double-click a part to turn round it, or empty space to reset.</div>
  </aside>
</main>
<script>
const D = __DATA__;
const cv = document.getElementById('c'), cx = cv.getContext('2d');
const EDGE = getComputedStyle(document.documentElement)
  .getPropertyValue('--edge').trim() || 'rgba(0,0,0,.30)';
// A flat coil is 10mm thick against 212 across, so a near-overhead default
// reads as a drawing rather than a thing. Start it further round.
let yaw = -0.62, pitch = D.flat ? -0.95 : -0.42, zoom = 1,
    mode = 'face', reveal = D.segs;

/* --- the model, centred on its own middle so rotation feels right --- */
let showEnds = !!D.ends;
/* the vertices on show: the ends' come after the airway's, from D.nb */
const VIS = () => (showEnds || !D.nb) ? D.V : D.V.slice(0, D.nb);
let C = centre();
function centre(){
  let lo = [1e9,1e9,1e9], hi = [-1e9,-1e9,-1e9];
  for (const v of VIS()) for (let i=0;i<3;i++){ lo[i]=Math.min(lo[i],v[i]); hi[i]=Math.max(hi[i],v[i]); }
  return [(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,(lo[2]+hi[2])/2];
}
function rot(p){
  const x=p[0]-C[0], y=p[1]-C[1], z=p[2]-C[2];
  const cy=Math.cos(yaw), sy=Math.sin(yaw);
  const x1=x*cy - z*sy, z1=x*sy + z*cy;
  const cp=Math.cos(pitch), sp=Math.sin(pitch);
  return [x1, y*cp - z1*sp, y*sp + z1*cp];
}
/* extent at this angle, so the fit does not jump as it turns */
function span(){
  let lo=[1e9,1e9], hi=[-1e9,-1e9];
  for (const v of VIS()){ const r=rot(v);
    for (let i=0;i<2;i++){ lo[i]=Math.min(lo[i],r[i]); hi[i]=Math.max(hi[i],r[i]); } }
  return [hi[0]-lo[0], hi[1]-lo[1], (lo[0]+hi[0])/2, (lo[1]+hi[1])/2];
}
let panX = 0, panY = 0, pivot = null, drawn = [], lastP = null;   /* pan; the point turned round, once a part is picked; what was drawn, for picking */
function draw(){
  const dpr = Math.min(devicePixelRatio||1, 2);
  const w = cv.clientWidth, h = cv.clientHeight;
  cv.width = w*dpr; cv.height = h*dpr;
  cx.setTransform(dpr,0,0,dpr,0,0);
  cx.clearRect(0,0,w,h);
  const [sw,sh,mx,my] = span();
  const s = Math.min(w/(sw||1), h/(sh||1)) * 0.86 * zoom;
  const [ax, ay] = pivot ? rot(pivot) : [mx, my];   /* the shape's middle, or the part picked to turn round */
  const P = p => { const r = rot(p);
    return [w/2 + (r[0]-ax)*s + panX, h/2 + (r[1]-ay)*s + panY, r[2]]; };

  const items = [];
  for (const q of D.Q){
    if (q.f < 4 && q.s >= reveal) continue;
    if (q.f === 5 && reveal < D.segs) continue;
    if (q.f >= 6 && !showEnds) continue;
    if (q.f === 7 && reveal < D.segs) continue;   /* the mouthpiece is on the far end */
    const pts = q.v.map(i => P(D.V[i]));
    const z = pts.reduce((a,p)=>a+p[2],0)/pts.length;
    /* facing, from the projected winding: a back face winds the other way */
    let area = 0;
    for (let i=0;i<pts.length;i++){ const a=pts[i], b=pts[(i+1)%pts.length];
      area += a[0]*b[1] - b[0]*a[1]; }
    items.push({q, pts, z, front: area < 0});
  }
  items.sort((a,b) => a.z - b.z);          /* painter: far first */
  drawn = items; lastP = P;

  for (const it of items){
    const q = it.q;
    let col = mode === 'face' ? D.facecol[q.f]
            : (q.f >= 4 ? D.facecol[q.f] : D.pal[q.s % D.pal.length]);
    /* one flat light, so the form reads; back faces sit darker */
    const k = it.front ? 1 : 0.55;
    cx.fillStyle = shade(col, k * (q.k !== undefined ? q.k
      : q.f===2?1.06:q.f===3?0.72:q.f===0?0.86:0.95));
    cx.beginPath();
    cx.moveTo(it.pts[0][0], it.pts[0][1]);
    for (let i=1;i<it.pts.length;i++) cx.lineTo(it.pts[i][0], it.pts[i][1]);
    cx.closePath(); cx.fill();
    if (q.m && mode === 'face'){
      /* a cheek is one part: its mitre lines are no seam, so they take the
         fill, which also covers the hairline between neighbouring quads */
      cx.strokeStyle = cx.fillStyle; cx.lineWidth = 0.8; cx.stroke();
      cx.beginPath();
      for (const e of q.m){ const a = it.pts[e], b = it.pts[(e+1) % 4];
        cx.moveTo(a[0], a[1]); cx.lineTo(b[0], b[1]); }
    }
    cx.strokeStyle = EDGE; cx.lineWidth = 0.6; cx.stroke();
  }
}
function shade(hex, k){
  const n = parseInt(hex.slice(1),16);
  const f = v => Math.max(0, Math.min(255, Math.round(v*k)));
  return `rgb(${f(n>>16&255)},${f(n>>8&255)},${f(n&255)})`;
}

/* --- controls --- */
/* turn, pan, zoom: drag turns; right-drag, shift-drag or two fingers pan;
   scroll or pinch zooms about the pointer; double-click a part to turn round it */
const pts = new Map(); let drag = null, pinch = null;
const at = e => { const b = cv.getBoundingClientRect(); return [e.clientX - b.left, e.clientY - b.top]; };
const two = () => { const [a, b] = [...pts.values()];
  return { h: Math.hypot(a[0] - b[0], a[1] - b[1]), x: (a[0] + b[0]) / 2, y: (a[1] + b[1]) / 2 }; };
function zoomBy(f, x, y) {   /* about canvas point (x, y), which stays where it is */
  const z0 = zoom; zoom = Math.max(0.35, Math.min(6, zoom * f));
  const u = x - cv.clientWidth / 2, v = y - cv.clientHeight / 2, k = zoom / z0;
  panX = u - (u - panX) * k; panY = v - (v - panY) * k;
}
const mid3 = it => [0, 1, 2].map(i => it.q.v.reduce((a, j) => a + D.V[j][i], 0) / it.q.v.length);
function pick(x, y) {   /* the part drawn on top at (x, y) */
  for (let i = drawn.length - 1; i >= 0; i--) {
    const p = drawn[i].pts; let inside = false;
    for (let j = 0, k = p.length - 1; j < p.length; k = j++)
      if ((p[j][1] > y) !== (p[k][1] > y)
          && x < (p[k][0] - p[j][0]) * (y - p[j][1]) / (p[k][1] - p[j][1]) + p[j][0]) inside = !inside;
    if (inside) return mid3(drawn[i]);
  }
  return null;
}
cv.addEventListener('pointerdown', e => {
  cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, at(e)); cv.classList.add('drag');
  if (pts.size === 1) drag = { pan: e.button === 1 || e.button === 2 || e.shiftKey };
  else { drag = null; pinch = two(); }
});
cv.addEventListener('pointermove', e => {
  if (!pts.has(e.pointerId)) return;
  const [x0, y0] = pts.get(e.pointerId), [x, y] = at(e); pts.set(e.pointerId, [x, y]);
  if (pinch) {   /* two fingers: move together to pan, pinch to zoom */
    const m = two(); panX += m.x - pinch.x; panY += m.y - pinch.y;
    if (pinch.h && m.h) zoomBy(m.h / pinch.h, m.x, m.y); pinch = m;
  } else if (drag && drag.pan) { panX += x - x0; panY += y - y0; }
  else if (drag) {
    yaw += (x - x0) * 0.008;
    pitch = Math.max(-1.5, Math.min(1.5, pitch + (y - y0) * 0.008));
  }
  draw();
});
const lift = e => { pts.delete(e.pointerId); if (pts.size < 2) pinch = null;
  if (!pts.size) { drag = null; cv.classList.remove('drag'); } };
cv.addEventListener('pointerup', lift);
cv.addEventListener('pointercancel', lift);
cv.addEventListener('contextmenu', e => e.preventDefault());
cv.addEventListener('wheel', e => {
  e.preventDefault(); const [x, y] = at(e);
  zoomBy((e.deltaY < 0 ? 1.1 : 1 / 1.1), x, y); draw();
}, { passive: false });
cv.addEventListener('dblclick', e => {
  const [x, y] = at(e), p = pick(x, y);
  if (!p) { yaw = -0.62; pitch = D.flat ? -0.95 : -0.42; zoom = 1; panX = panY = 0; pivot = null; draw(); return; }
  /* p holds the middle from now on: start it where it is, then glide it in */
  const s = lastP(p); pivot = p;
  const x1 = panX = s[0] - cv.clientWidth / 2, y1 = panY = s[1] - cv.clientHeight / 2, t0 = performance.now();
  const glide = t => { const k = Math.min(1, (t - t0) / 300), f = 1 - k * (2 - k);
    panX = x1 * f; panY = y1 * f; draw(); if (k < 1) requestAnimationFrame(glide); };
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) { panX = panY = 0; draw(); }
  else requestAnimationFrame(glide);
});

const $ = id => document.getElementById(id);
function setMode(m){
  mode = m;
  $('m-face').setAttribute('aria-pressed', m === 'face');
  $('m-sec').setAttribute('aria-pressed', m === 'sec');
  key(); draw();
}
$('m-face').onclick = () => setMode('face');
$('m-sec').onclick = () => setMode('sec');

const rev = $('rev');
rev.max = D.segs; rev.value = D.segs;
rev.oninput = () => { reveal = +rev.value; revn(); draw(); };
function revn(){
  $('revn').textContent = reveal + ' of ' + D.segs + ' facets'
    + (reveal < D.segs ? '' : '  (all)');
}

function key(){
  const k = $('key');
  k.innerHTML = '';
  const rows = mode === 'face'
    ? D.faces.map((n,i) => [D.facecol[i], n, i])
        .filter(([,,i]) => (i < 6 || showEnds) && D.Q.some(q => q.f === i))
        .map(([c,n]) => [c,n])
    : (D.shut ? [] : [[D.facecol[4],D.faces[4]], [D.facecol[5],D.faces[5]]]).concat(
      [[D.pal[0], 'facet 1'], [D.pal[Math.floor(D.segs/2) % D.pal.length],
        'facet ' + (Math.floor(D.segs/2)+1)],
       [D.pal[(D.segs-1) % D.pal.length], 'facet ' + D.segs]]);
  for (const [c,n] of rows){
    const d = document.createElement('div'); d.className = 'key';
    d.innerHTML = `<span class="sw" style="background:${c}"></span><span>${n}</span>`;
    k.appendChild(d);
  }
}

/* what the openings actually are: the ports, and which ends are shut */
function portrow(){
  const caps = [4,5].filter(i => D.faces[i].startsWith('cap')).length;
  const shut = caps === 2 ? 'both ends capped'
             : caps === 1 ? 'the mouth capped' : 'neither end capped';
  const where = D.percheek ? 'one a cheek, opposite faces'
    : D.ends && D.ends.port ? 'through both cheeks, the top one plugged' : 'through both cheeks';
  return `${D.ports} \u00d7 ${D.portsize[0]} \u00d7 ${D.portsize[1]}mm, `
       + `${where}, ${shut}`;
}

$('sub').innerHTML = `<b>${D.bore} \u00d7 ${D.bore}mm</b> section, `
  + `<b>${D.mm}mm</b> of centreline, ${D.segs} facets of ${D.facet}\u00b0 `
  + `\u2014 exact along every facet, <b>+${D.over}%</b> at each mitre`;
$('nums').innerHTML = [
  ['shape', D.shape], ['curve', D.curve],
  ['bore', D.bore + ' \u00d7 ' + D.bore + 'mm'],
  ['section', (D.bore*D.bore) + 'mm\u00b2'],
  ['centreline', D.mm + 'mm'],
  ['bend radius', D.rrange ? ('R' + D.rrange[0] + ' to R' + D.rrange[1]) : (D.R + 'mm')],
  ['R / bore', D.rrange
     ? (D.rrange[0]/D.bore).toFixed(1) + ' to ' + (D.rrange[1]/D.bore).toFixed(1)
     : (D.R/D.bore).toFixed(1)],
  ['facet', D.facet + '\u00b0'], ['area at a mitre', '+' + D.over + '%'],
].concat(D.ports ? [['ports', portrow()]] : [])
 .concat(D.ends ? [['bell', D.ends.bell], ['mouthpiece', D.ends.mouthpiece]] : [])
 .map(([a,b]) => `<dt>${a}</dt><dd>${b}</dd>`).join('');

/* the ends, when the page has them: on by default, as built */
if (D.ends){
  const g = document.createElement('div'); g.className = 'grp';
  g.innerHTML = '<h2>Ends</h2><label class="chk"><input type="checkbox" id="ends" checked>'
    + ' bell and mouthpiece</label>' + (D.ends.port ? '<div class="hint">The cheeks are'
    + ' not drawn, so the bell stands 3mm off the bore: that gap is the cheek it seats'
    + ' on.</div>' : '');
  $('key').parentNode.before(g);
  $('ends').onchange = e => { showEnds = e.target.checked; C = centre(); key(); draw(); };
}

key(); revn();
addEventListener('resize', draw);
draw();
</script>
'''


EMBED = r"""<title>__TITLE__</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
/* An embed sits inside somebody else's page, so it follows the reader's
   theme. It cannot see an explicit toggle on the host - a frame is its own
   document - so this matches by default and not after a manual switch. */
:root{color-scheme:light dark;--bg:#f7f5f1;--ink:#1b1e24;--dim:#6b7480;
      --edge:rgba(0,0,0,.35)}
@media (prefers-color-scheme:dark){
  :root{--bg:#14161a;--ink:#e8eaed;--dim:#6f7883;--edge:rgba(0,0,0,.30)}}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--ink);overflow:hidden;
     font:13px/1.45 ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
canvas{display:block;width:100%;height:100%;cursor:grab;touch-action:none}
canvas.drag{cursor:grabbing}
#cap{position:absolute;left:14px;bottom:12px;right:14px;pointer-events:none}
#cap b{font-weight:650}
#cap span{color:var(--dim)}
#cap a{pointer-events:auto;color:#e0457b;text-decoration:none;
       border-bottom:1px solid rgba(224,69,123,.45)}
#cap a:hover,#cap a:focus-visible{border-bottom-color:#e0457b}
#hint{position:absolute;right:14px;top:12px;color:var(--dim);font-size:12px;
      pointer-events:none;transition:opacity .5s}
@media (prefers-reduced-motion:reduce){#hint{transition:none}}
</style>
<canvas id="c"></canvas>
<div id="hint">drag to turn</div>
<div id="cap"></div>
<script>
const D = __DATA__;
const cv = document.getElementById('c'), cx = cv.getContext('2d');
let yaw = -0.75, pitch = -0.45, zoom = 1, mode = 'sec', reveal = D.segs;
__DRAW__

/* A slow idle turn, so the thing reads as something you can move rather than
   a picture. It stops for good on the first interaction, and never starts if
   the reader has asked for less motion. */
const still = matchMedia('(prefers-reduced-motion: reduce)').matches;
let idle = !still, t0 = performance.now();
function tick(t){
  if (idle){ yaw = -0.75 + Math.sin((t - t0) / 6000) * 0.5; draw(); }
  requestAnimationFrame(tick);
}
function stop(){
  if (!idle) return;
  idle = false;
  const h = document.getElementById('hint');
  h.style.opacity = 0;
}
/* turn, pan, zoom: drag turns; right-drag, shift-drag or two fingers pan;
   scroll or pinch zooms about the pointer; double-click a part to turn round it */
const pts = new Map(); let drag = null, pinch = null;
const at = e => { const b = cv.getBoundingClientRect(); return [e.clientX - b.left, e.clientY - b.top]; };
const two = () => { const [a, b] = [...pts.values()];
  return { h: Math.hypot(a[0] - b[0], a[1] - b[1]), x: (a[0] + b[0]) / 2, y: (a[1] + b[1]) / 2 }; };
function zoomBy(f, x, y) {   /* about canvas point (x, y), which stays where it is */
  const z0 = zoom; zoom = Math.max(0.4, Math.min(5, zoom * f));
  const u = x - cv.clientWidth / 2, v = y - cv.clientHeight / 2, k = zoom / z0;
  panX = u - (u - panX) * k; panY = v - (v - panY) * k;
}
const mid3 = it => [0, 1, 2].map(i => it.q.v.reduce((a, j) => a + D.V[j][i], 0) / it.q.v.length);
function pick(x, y) {   /* the part drawn on top at (x, y) */
  for (let i = drawn.length - 1; i >= 0; i--) {
    const p = drawn[i].pts; let inside = false;
    for (let j = 0, k = p.length - 1; j < p.length; k = j++)
      if ((p[j][1] > y) !== (p[k][1] > y)
          && x < (p[k][0] - p[j][0]) * (y - p[j][1]) / (p[k][1] - p[j][1]) + p[j][0]) inside = !inside;
    if (inside) return mid3(drawn[i]);
  }
  return null;
}
cv.addEventListener('pointerdown', e => {
  stop(); cv.setPointerCapture(e.pointerId); pts.set(e.pointerId, at(e)); cv.classList.add('drag');
  if (pts.size === 1) drag = { pan: e.button === 1 || e.button === 2 || e.shiftKey };
  else { drag = null; pinch = two(); }
});
cv.addEventListener('pointermove', e => {
  if (!pts.has(e.pointerId)) return;
  const [x0, y0] = pts.get(e.pointerId), [x, y] = at(e); pts.set(e.pointerId, [x, y]);
  if (pinch) {   /* two fingers: move together to pan, pinch to zoom */
    const m = two(); panX += m.x - pinch.x; panY += m.y - pinch.y;
    if (pinch.h && m.h) zoomBy(m.h / pinch.h, m.x, m.y); pinch = m;
  } else if (drag && drag.pan) { panX += x - x0; panY += y - y0; }
  else if (drag) {
    yaw += (x - x0) * 0.008;
    pitch = Math.max(-1.5, Math.min(1.5, pitch + (y - y0) * 0.008));
  }
  draw();
});
const lift = e => { pts.delete(e.pointerId); if (pts.size < 2) pinch = null;
  if (!pts.size) { drag = null; cv.classList.remove('drag'); } };
cv.addEventListener('pointerup', lift);
cv.addEventListener('pointercancel', lift);
cv.addEventListener('contextmenu', e => e.preventDefault());
cv.addEventListener('wheel', e => {
  e.preventDefault(); stop(); const [x, y] = at(e);
  zoomBy((e.deltaY < 0 ? 1.1 : 1 / 1.1), x, y); draw();
}, { passive: false });
cv.addEventListener('dblclick', e => {
  const [x, y] = at(e), p = pick(x, y);
  if (!p) { stop(); yaw = -0.75; pitch = -0.45; zoom = 1; panX = panY = 0; pivot = null; draw(); return; }
  /* p holds the middle from now on: start it where it is, then glide it in */
  const s = lastP(p); pivot = p;
  const x1 = panX = s[0] - cv.clientWidth / 2, y1 = panY = s[1] - cv.clientHeight / 2, t0 = performance.now();
  const glide = t => { const k = Math.min(1, (t - t0) / 300), f = 1 - k * (2 - k);
    panX = x1 * f; panY = y1 * f; draw(); if (k < 1) requestAnimationFrame(glide); };
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) { panX = panY = 0; draw(); }
  else requestAnimationFrame(glide);
});

document.getElementById('cap').innerHTML =
  `<b>${D.bore} \u00d7 ${D.bore}mm</b> <span>constant section, </span>`
  + `<b>${D.mm}mm</b> <span>of bore on a planar curve \u2014 </span>`
  + `<a href="__HOME__" target="_top">swept-curve</a>`;
addEventListener('resize', draw);
if (!still) requestAnimationFrame(tick); else draw();
draw();
</script>
"""


def build(title, embed=False, home=''):
    d = data_for()
    if not embed:
        return (HTML.replace('__TITLE__', title)
                    .replace('__DATA__', json.dumps(d, separators=(',', ':'))))
    # the drawing code is shared verbatim: one place decides what this looks
    # like, so an embed cannot quietly diverge from the page it links to
    body = HTML.split('<script>\nconst D = ', 1)[1]
    draw = body.split("/* --- controls --- */", 1)[0]
    # Drop the three lines the embed declares for itself. Slicing off the
    # first line instead removed the blank line above them and left `const D`
    # declared twice, which is a SyntaxError and a blank canvas.
    drop = ('__DATA__;', 'const D =', 'const cv =', 'let yaw =')   # the split leaves the first as a line of its own
    draw = '\n'.join(l for l in draw.splitlines()
                     if not l.startswith(drop))
    assert 'function draw(' in draw and 'const D =' not in draw, 'bad extract'
    return (EMBED.replace('__TITLE__', title)
                 .replace('__DRAW__', draw)
                 .replace('__HOME__', home)
                 .replace('__DATA__', json.dumps(d, separators=(',', ':'))))


def main():
    a = sys.argv[1:]
    # THE DESIGN IS READ BY THE GENERATOR, not by a copy of it here. This file
    # kept its own flag table, its own refusals and its own per-shape defaults,
    # and each note that used to sit here recorded one more way the copy had
    # drifted: an unlisted flag drawn at its default, a facet default this file
    # did not have, --ds-half, the port flags, --trace refused. The last state of
    # it drew pages for --port-at with --cap, which the generator refuses. Only
    # the four flags that are about the page are taken out first.
    VIEW = ('--out=', '--home=', '--embed', '--trace=', '--ends')
    B.read_flags([x for x in a if not x.startswith(VIEW)])
    # --out IS REQUIRED. This used to guess the page's path from a filename rule
    # of its own, a third naming scheme beside the generator's sheet names and
    # the folder names the designs actually ship in, which are chosen by hand
    # (-800mm, -halftest, -1000mm). Measured on 2026-09-16: of 18 shipped pages,
    # 7 resolved to their own file; three would have been written over ANOTHER
    # design's page, and the torus, scallop and racetrack found no folder at
    # all. A page's path is not something this file can derive, so it asks.
    out = [x for x in a if x.startswith('--out=')]
    if not out:
        sys.exit('ribbon_view: say where the page goes with --out=PATH. It '
                 'belongs beside the cut files it describes, in the design\'s '
                 'own folder.')
    path = out[0].split('=', 1)[1]
    # --ends puts the mouthpiece and the bell on: the bell in the port and the
    # mouthpiece on the far end where there is a port, as the built spiral has
    # them, and otherwise the mouthpiece on the mouth and the bell on the far
    # end. A closed ring has no ends, so it is refused.
    global ENDS
    ENDS = '--ends' in a
    if ENDS and (B.PORT_BOTH or B.PORT_AT is not None
                 or B.SHAPE in ('torus', 'scallop', 'racetrack', 'oval')):
        sys.exit('ribbon_view: --ends needs two ends to put a mouthpiece and a '
                 'bell on: a closed ring has none, and --port-both and '
                 '--port-at move both openings into the cheeks.')

    here = os.path.dirname(os.path.abspath(__file__))
    # --trace draws a centreline from stations fixed somewhere other than this
    # generator's own parameters. A trace carries its provenance -- where it
    # came from, how it was taken, what was measured -- so a traced number is
    # one somebody can check. None ships at present.
    tr = [x for x in a if x.startswith('--trace=')]
    if tr:
        import json
        doc = json.load(open(tr[0].split('=', 1)[1]))
        pts = [tuple(q) for q in doc['stations']]
        B.BORE, B.FACET, B.SHAPE = doc['bore'], doc['facet'], 'traced'
        B.centreline = lambda: pts          # already in SVG coordinates
        seg = [B.seglen(pts[i], pts[i+1]) for i in range(len(pts)-1)]
        inner = sorted(seg)[1:-1]
        B.RADIUS = round((sum(inner) / len(inner))
                         / (2 * math.tan(math.radians(B.FACET / 2))), 3)
        # the trace names itself; this used to be hard-coded to the first
        # traced bore, which put that title on every other one
        title = (doc['name'].replace('-', ' ').title()
                 + f', {B.BORE:g}mm \u2014 traced')
        page = build(title)
        open(path, 'w').write(page)
        d = data_for()
        print(f'  {os.path.basename(path):<52}drag to turn, colour by face '
              f'or facet')
        print(f'  {"":52}{d["mm"]}mm, {d["segs"]} facets, traced')
        return 0
    if B.SHAPE == 'torus':
        # NOT "Octagonal Torus". That title was written when 45 degrees was the
        # only ring anyone had drawn, and it then headed a 13-facet ring -- a
        # page calling a thirteen-sided figure an octagon, with the facet count
        # right there in the panel below it. The ring says how many sides it
        # has.
        title = (f'Closed Ring, {int(round(360.0 / B.FACET))} Facets, '
                 f'{B.BORE:g}mm Bore')
    elif B.SHAPE == 'racetrack':
        title = (f'Closed Serpentine Racetrack, {B.LOBES} Lobes a Side, '
                 f'{B.BORE:g}mm Bore')
    elif B.SHAPE == 'oval':
        title = f'Closed Oval, Flattened Ends, {B.BORE:g}mm Bore'
    elif B.SHAPE == 'scallop':
        title = (f'Closed Serpentine, {B.LOBES} Lobes, {B.BORE:g}mm Bore')
    elif B.SHAPE == 'ess':
        title = f'Ribbon Ess, {B.BORE:g}mm Bore'
    elif B.SHAPE == 'spiral':
        title = f'Ribbon Spiral, {B.BORE:g}mm Bore'
    elif B.SHAPE == 'double-volute':
        title = f'Ribbon Double Volute, {B.BORE:g}mm Bore'
    elif B.SHAPE == 'double-spiral':
        # --ds-half is a different bore, not a view of the same one: it stops at
        # the centre and runs out from there. Without this it took the full
        # spiral's name and title, which is the mistake the else-branch below
        # exists to stop, one level further in.
        title = ('Ribbon Double Spiral, Centre Half, %gmm Bore' % B.BORE
                 if B.DS_HALF
                 else f'Ribbon Double Spiral, {B.BORE:g}mm Bore')
    elif B.SHAPE in ('serpentine', 'three-lobe-serpentine-with-collinear-ends'):
        title = ('Three-Lobe Serpentine with Collinear Ends, %gmm Bore' % B.BORE
                 if B.SHAPE == 'three-lobe-serpentine-with-collinear-ends'
                 else f'Ribbon Serpentine, {B.BORE:g}mm Bore')
    else:
        # This used to be the coupon's branch with no test on the shape, so a
        # shape added to the generator and not to this list came out headed
        # "Ribbon Coupon" over a picture of something else. The double spiral
        # did, and every check here passed while it did: the numbers panel is
        # built from the geometry and was right throughout. Only the drawing
        # showed it. The coupon is gone (2026-09-14) and the branch it used to
        # own is now nothing but this refusal, which is what it should always
        # have been.
        sys.exit(f'ribbon_view: no title for --shape={B.SHAPE}. '
                 f'Add it here as well as in ribbon_bore.centreline().')
    hm = [x for x in a if x.startswith('--home=')]
    embed = '--embed' in a
    # Built BEFORE the file is opened. open() creates the file, so a design the
    # generator refuses while the page is being built -- a facet named twice --
    # left an empty page at --out, over whatever was there, beside its refusal.
    page = build(title, embed, hm[0].split('=', 1)[1] if hm else
                 'https://gernreich.github.io/swept-curve/')
    open(path, 'w').write(page)
    d = data_for()
    print(f'  {os.path.basename(path):<52}drag to turn, colour by face '
          f'or facet')
    print(f'  {"":52}{d["mm"]}mm, {d["segs"]} facets, '
          f'{len(d["Q"])} quads')
    return 0


if __name__ == '__main__':
    # The generator refuses with a sentence written for the person at the
    # bench -- "no crossover arc reaches the eye at --vol-cross-r=22" -- and
    # that sentence came out of here as a traceback, because nothing caught it.
    # ribbon_bore's own __main__ has caught ValueError all along; this is the
    # same two lines.
    try:
        sys.exit(main())
    except ValueError as e:
        print(f'error: {e}')
        sys.exit(1)
