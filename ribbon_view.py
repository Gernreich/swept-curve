#!/usr/bin/env python3
"""An interactive view of a ribbon bore: drag to turn.

    python3 ribbon_view.py                       # the double spiral
    python3 ribbon_view.py --shape=serpentine    # and so on, same flags

Writes one self-contained HTML page beside the cut files it belongs to, so a
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
    else:
        top_h = bot_h = {i: (t0, t1) for i, t0, t1 in spans}
    for i in range(len(c) - 1):
        p, q = 4 * i, 4 * (i + 1)
        Q.append({'v': [p + 0, p + 1, q + 1, q + 0], 'f': 0, 's': i})   # inner
        Q.append({'v': [p + 3, q + 3, q + 2, p + 2], 'f': 1, 's': i})   # outer
        if i in top_h:
            Q += framed(V, a, d, h, i, *top_h[i], across, 1 - across, True)
        else:
            Q.append({'v': [p + 1, p + 2, q + 2, q + 1], 'f': 2, 's': i})  # top
        if i in bot_h:
            Q += framed(V, a, d, h, i, *bot_h[i], across, 1 - across, False)
        else:
            Q.append({'v': [p + 0, q + 0, q + 3, p + 3], 'f': 3, 's': i})  # bottom
    # The two cheek plates used to be drawn here as well, at full band width,
    # 3mm proud of the airway top and bottom -- faces 6 and 7, 'ply, top' and
    # 'ply, bottom'. They are gone (2026-09-13): every view of the inside was
    # through a slab of ply, which is the one thing this page must not do.
    # What they were there for -- that the part is 20mm across where the
    # passage is 10 -- the numbers panel says in words, and the cut files show.

    n = len(c) - 1
    if not shut:
        Q.append({'v': [0, 1, 2, 3], 'f': 4, 's': 0})                   # mouth
        Q.append({'v': [4*n+3, 4*n+2, 4*n+1, 4*n+0], 'f': 5, 's': n-1})  # far end
    # a closed ring has no mouth and no far end; the last station IS the first,
    # so its four vertices are already coincident with station 0's

    # The spiral has no single bend radius - that is the point of it - so it
    # reports the range it sweeps. Falling through to RADIUS printed R30, the
    # old coupon's radius, on a bore whose arcs run R34.7 to R112.9.
    # dspiral and volute have no single bend radius either, and both quote
    # their tightest arc, as ribbon_bore does. Neither was in this list: the
    # double spiral read R30 because DS_CROSS_R was that same 30, so the
    # fall-through was right by coincidence, and the volute inherited it
    # against arcs of R22, R64 and R94.
    R = (B.WAVE_TROUGH_R if B.SHAPE == 'wave'
         else B.SPIRAL_RI if B.SHAPE == 'spiral'
         else B.DS_CROSS_R if B.SHAPE == 'dspiral'
         else B.VOL_CROSS_R if B.SHAPE == 'volute'
         else B.LOBE_R if B.SHAPE in ('serpentine', 'opposed') else B.RADIUS)
    return {
        'V': [[round(v, 3) for v in p] for p in V],
        'Q': Q,
        'bore': B.BORE,
        'mm': round(sum(B.seglen(p, q) for p, q in zip(c, c[1:])), 1),
        'facet': B.FACET,
        'shape': B.SHAPE,
        # What curve the vertices were placed on. Two constructions are in use
        # and the drawing cannot tell them apart, so the panel says which:
        # every shape but 'dspiral' is built from arcs whose radius holds all
        # the way across, and 'dspiral' samples a smooth Archimedean spiral.
        # See "Which curve each shape's vertices sit on" in CLAUDE.md.
        'curve': {'dspiral': 'Archimedean spiral, sampled',
                  'volute': 'chain of semicircles',
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
                  'cap (far end)' if B.CAP and B.PORT_BOTH else 'far end'],
        'facecol': ['#5aa9e6', '#3d7ebd', '#c9d6e3', '#8fa3b8',
                    '#b08968' if B.CAP else '#1c1c20',
                    '#b08968' if B.CAP and B.PORT_BOTH else '#e0457b'],
        'ports': len(spans),
        'portsize': [B.PORT_ACROSS, B.PORT_ALONG] if B.PORT else None,
        'percheek': B.PORT_PER_CHEEK,
    }


HTML = r'''<title>__TITLE__</title>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{color-scheme:dark;--bg:#14161a;--ink:#e8eaed;--dim:#9aa3ad;--line:#2a2f36;
      --panel:#1b1e24;--accent:#e0457b;--edge:rgba(0,0,0,.30)}
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
button{font:inherit;color:var(--ink);background:#232830;border:1px solid var(--line);
       border-radius:6px;padding:5px 9px;cursor:pointer;margin:0 4px 4px 0}
button[aria-pressed=true]{background:var(--accent);border-color:var(--accent);color:#fff}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
input[type=range]{width:100%;accent-color:var(--accent)}
.key{display:flex;align-items:center;gap:7px;margin:3px 0;font-size:12.5px}
/* the mouth's swatch is near-black on a near-black panel, so every swatch
   gets an outline rather than that one getting a special case */
.sw{width:12px;height:12px;border-radius:3px;flex:0 0 auto;
    box-shadow:inset 0 0 0 1px rgba(255,255,255,.35)}
.hint{color:var(--dim);font-size:12px;margin-top:10px}
dl{margin:0;display:grid;grid-template-columns:auto 1fr;gap:2px 10px;font-size:12.5px}
dt{color:var(--dim)}dd{margin:0;text-align:right;font-variant-numeric:tabular-nums}
@media (max-width:720px){main{grid-template-columns:1fr;height:auto}
  #wrap{height:56vh}aside{border-left:0;border-top:1px solid var(--line)}}
</style>
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
    <div class="hint">Drag to turn. Scroll to zoom. Double-click to reset.</div>
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
const C = (() => {
  let lo = [1e9,1e9,1e9], hi = [-1e9,-1e9,-1e9];
  for (const v of D.V) for (let i=0;i<3;i++){ lo[i]=Math.min(lo[i],v[i]); hi[i]=Math.max(hi[i],v[i]); }
  return [(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,(lo[2]+hi[2])/2];
})();
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
  for (const v of D.V){ const r=rot(v);
    for (let i=0;i<2;i++){ lo[i]=Math.min(lo[i],r[i]); hi[i]=Math.max(hi[i],r[i]); } }
  return [hi[0]-lo[0], hi[1]-lo[1], (lo[0]+hi[0])/2, (lo[1]+hi[1])/2];
}
function draw(){
  const dpr = Math.min(devicePixelRatio||1, 2);
  const w = cv.clientWidth, h = cv.clientHeight;
  cv.width = w*dpr; cv.height = h*dpr;
  cx.setTransform(dpr,0,0,dpr,0,0);
  cx.clearRect(0,0,w,h);
  const [sw,sh,mx,my] = span();
  const s = Math.min(w/(sw||1), h/(sh||1)) * 0.86 * zoom;
  const P = p => { const r = rot(p);
    return [w/2 + (r[0]-mx)*s, h/2 + (r[1]-my)*s, r[2]]; };

  const items = [];
  for (const q of D.Q){
    if (q.f < 4 && q.s >= reveal) continue;
    if (q.f === 5 && reveal < D.segs) continue;
    const pts = q.v.map(i => P(D.V[i]));
    const z = pts.reduce((a,p)=>a+p[2],0)/pts.length;
    /* facing, from the projected winding: a back face winds the other way */
    let area = 0;
    for (let i=0;i<pts.length;i++){ const a=pts[i], b=pts[(i+1)%pts.length];
      area += a[0]*b[1] - b[0]*a[1]; }
    items.push({q, pts, z, front: area < 0});
  }
  items.sort((a,b) => a.z - b.z);          /* painter: far first */

  for (const it of items){
    const q = it.q;
    let col = mode === 'face' ? D.facecol[q.f]
            : (q.f >= 4 ? D.facecol[q.f] : D.pal[q.s % D.pal.length]);
    /* one flat light, so the form reads; back faces sit darker */
    const k = it.front ? 1 : 0.55;
    cx.fillStyle = shade(col, k * (q.f===2?1.06:q.f===3?0.72:q.f===0?0.86:0.95));
    cx.beginPath();
    cx.moveTo(it.pts[0][0], it.pts[0][1]);
    for (let i=1;i<it.pts.length;i++) cx.lineTo(it.pts[i][0], it.pts[i][1]);
    cx.closePath(); cx.fill();
    cx.strokeStyle = EDGE; cx.lineWidth = 0.6; cx.stroke();
  }
}
function shade(hex, k){
  const n = parseInt(hex.slice(1),16);
  const f = v => Math.max(0, Math.min(255, Math.round(v*k)));
  return `rgb(${f(n>>16&255)},${f(n>>8&255)},${f(n&255)})`;
}

/* --- controls --- */
let drag = null;
cv.addEventListener('pointerdown', e => {
  drag = [e.clientX, e.clientY]; cv.classList.add('drag');
  cv.setPointerCapture(e.pointerId);
});
cv.addEventListener('pointermove', e => {
  if (!drag) return;
  yaw += (e.clientX - drag[0]) * 0.008;
  pitch += (e.clientY - drag[1]) * 0.008;
  pitch = Math.max(-1.5, Math.min(1.5, pitch));
  drag = [e.clientX, e.clientY]; draw();
});
for (const ev of ['pointerup','pointercancel'])
  cv.addEventListener(ev, () => { drag = null; cv.classList.remove('drag'); });
cv.addEventListener('wheel', e => {
  e.preventDefault();
  zoom = Math.max(0.35, Math.min(6, zoom * (e.deltaY < 0 ? 1.1 : 1/1.1)));
  draw();
}, {passive:false});
cv.addEventListener('dblclick', () => {
  yaw = -0.62; pitch = D.flat ? -0.95 : -0.42; zoom = 1; draw();
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
        .filter(([,,i]) => D.Q.some(q => q.f === i)).map(([c,n]) => [c,n])
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
  const where = D.percheek ? 'one a cheek, opposite faces' : 'through both cheeks';
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
 .map(([a,b]) => `<dt>${a}</dt><dd>${b}</dd>`).join('');

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
let drag = null;
function stop(){
  if (!idle) return;
  idle = false;
  const h = document.getElementById('hint');
  h.style.opacity = 0;
}
cv.addEventListener('pointerdown', e => {
  stop(); drag = [e.clientX, e.clientY];
  cv.classList.add('drag'); cv.setPointerCapture(e.pointerId);
});
cv.addEventListener('pointermove', e => {
  if (!drag) return;
  yaw += (e.clientX - drag[0]) * 0.008;
  pitch = Math.max(-1.5, Math.min(1.5, pitch + (e.clientY - drag[1]) * 0.008));
  drag = [e.clientX, e.clientY]; draw();
});
for (const ev of ['pointerup','pointercancel'])
  cv.addEventListener(ev, () => { drag = null; cv.classList.remove('drag'); });
cv.addEventListener('wheel', e => {
  e.preventDefault(); stop();
  zoom = Math.max(0.4, Math.min(5, zoom * (e.deltaY < 0 ? 1.1 : 1/1.1)));
  draw();
}, {passive:false});

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
    body = HTML.split('<script>', 1)[1]
    draw = body.split("/* --- controls --- */", 1)[0]
    # Drop the three lines the embed declares for itself. Slicing off the
    # first line instead removed the blank line above them and left `const D`
    # declared twice, which is a SyntaxError and a blank canvas.
    drop = ('const D =', 'const cv =', 'let yaw =')
    draw = '\n'.join(l for l in draw.splitlines()
                     if not l.startswith(drop))
    assert 'function draw(' in draw and 'const D =' not in draw, 'bad extract'
    return (EMBED.replace('__TITLE__', title)
                 .replace('__DRAW__', draw)
                 .replace('__HOME__', home)
                 .replace('__DATA__', json.dumps(d, separators=(',', ':'))))


def main():
    a = sys.argv[1:]
    FLAGS = (('shape', str), ('bore', float), ('facet', float),
             ('radius', float), ('lobes', int), ('lobe-r', float),
             ('rise', float), ('lead', float), ('web', float),
             ('spiral-facets', int), ('spiral-ri', float),
             ('spiral-ro', float), ('wave-rise', float),
             ('wave-trough-r', float), ('wave-crest-r', float),
             ('wave-lead-r', float), ('ds-pitch', float),
             ('ds-r0', float), ('ds-facets', int), ('ds-cross-r', float),
             ('vol-r0', float), ('vol-step', float),
             ('vol-semis', int), ('vol-cross-r', float),
             ('scallop-in-r', float), ('scallop-in-deg', float),
             ('race-cap-r', float), ('race-straight', float),
             ('port-from-tip', float))
    for flag, cast in FLAGS:
        hit = [x for x in a if x.startswith(f'--{flag}=')]
        if not hit:
            continue
        name = {'shape': 'SHAPE', 'bore': 'BORE', 'facet': 'FACET',
                'radius': 'RADIUS', 'lobes': 'LOBES', 'lobe-r': 'LOBE_R',
                'rise': 'RISE', 'lead': 'LEAD', 'web': 'WEB',
                'spiral-facets': 'SPIRAL_FACETS', 'spiral-ri': 'SPIRAL_RI',
                'spiral-ro': 'SPIRAL_RO', 'wave-rise': 'WAVE_RISE',
                'wave-trough-r': 'WAVE_TROUGH_R',
                'wave-crest-r': 'WAVE_CREST_R',
                'wave-lead-r': 'WAVE_LEAD_R', 'ds-pitch': 'DS_PITCH',
                'ds-r0': 'DS_R0', 'ds-facets': 'DS_FACETS',
                'ds-cross-r': 'DS_CROSS_R', 'vol-r0': 'VOL_R0',
                'vol-step': 'VOL_STEP', 'vol-semis': 'VOL_SEMIS',
                'vol-cross-r': 'VOL_CROSS_R',
                'scallop-in-r': 'SCALLOP_IN_R',
                'scallop-in-deg': 'SCALLOP_IN_DEG',
                'race-cap-r': 'RACE_CAP_R',
                'race-straight': 'RACE_STRAIGHT',
                'port-from-tip': 'PORT_FROM_TIP'}[flag]
        setattr(B, name, cast(hit[0].split('=', 1)[1]))

    # This table is a SECOND copy of the generator's, and an unlisted flag
    # used to fall straight through it: the double spiral was drawn here at
    # its default crossover radius while the cut files beside it were cut at
    # another, and the only tell was 6.5mm of length between two reports
    # nobody was comparing. An unknown flag is now an error, so a page and
    # the sheets it belongs to cannot be built from different numbers.
    # --ds-half is a bare switch rather than --flag=value, so it is carried
    # across here instead of through FLAGS. That makes three things this second
    # copy has lacked that the generator had; the two notes above are the others.
    B.DS_HALF = '--ds-half' in a
    # The port flags, carried across the same way and for a stronger reason
    # than --ds-half: a page drawn without them shows a mouth and a far end
    # that the ported part has not got, and no hole where its openings are.
    # --port-square's implication is copied from the generator rather than
    # inferred, because the SIZE follows --bore and reading it off anything
    # else is how the two copies of this argument handling drift apart.
    B.PORT = '--port' in a
    B.PORT_BOTH = '--port-both' in a
    B.PORT_PER_CHEEK = '--port-per-cheek' in a
    B.PORT_AT = None
    hit = [x for x in a if x.startswith('--port-at=')]
    if hit:
        B.PORT_AT = [int(v) for v in hit[0].split('=', 1)[1].split(',') if v != '']
    B.CAP = '--cap' in a
    if '--port-square' in a:
        B.PORT_ACROSS = B.PORT_ALONG = B.BORE
    for flag, why in (('--port-both', 'draws no port at all, at either end'),
                      ('--port-square', 'draws no port at all'),
                      ('--port-per-cheek', 'draws no port at all'),
                      ('--cap', 'closes the only opening the bore has')):
        if flag in a and not B.PORT:
            sys.exit(f'ribbon_view: {flag} without --port {why}. Pass both.')
    # The loop above tests `flag in a`, which a flag carrying a VALUE never
    # satisfies -- '--port-at=0,6' is not '--port-at' -- so this one needs
    # saying separately rather than adding a name to that tuple.
    if B.PORT_AT is not None and not B.PORT:
        sys.exit('ribbon_view: --port-at without --port draws no port at all, '
                 'on any facet. Pass both.')
    if B.PORT_AT is not None and B.PORT_BOTH:
        sys.exit('ribbon_view: --port-at and --port-both are two answers to '
                 'the same question. Pass one.')
    if B.PORT_PER_CHEEK and B.PORT_AT is None and not B.PORT_BOTH:
        sys.exit('ribbon_view: --port-per-cheek without --port-both has one '
                 'port and two cheeks, so there is nothing to split.')
    if B.PORT_PER_CHEEK and B.PORT_AT is not None and len(B.PORT_AT) != 2:
        sys.exit(f'ribbon_view: --port-per-cheek splits the ports between TWO '
                 f'cheeks and --port-at names {len(B.PORT_AT)}.')
    # --trace belongs in this set too. It was not, so the guard rejected the
    # one flag whose handler sits forty lines below it and the traced page
    # could not be redrawn at all -- the check meant to stop a page and its
    # sheets being built from different numbers stopped a page being built.
    known = ({f'--{f}' for f, _ in FLAGS}
             | {'--out', '--home', '--embed', '--ds-half', '--trace',
                '--port', '--port-square', '--port-both', '--port-per-cheek',
                '--port-at', '--cap'})
    for x in a:
        if x.startswith('--') and x.split('=', 1)[0] not in known:
            sys.exit(f'ribbon_view: {x.split("=", 1)[0]} is not a flag here. '
                     f'Known: {" ".join(sorted(known))}')

    # the opposed shape carries its own lobe; see ribbon_bore.OPPOSED_R
    if B.SHAPE == 'opposed':
        if not any(x.startswith('--lobe-r=') for x in a):
            B.LOBE_R = B.OPPOSED_R
        if not any(x.startswith('--rise=') for x in a):
            B.RISE = B.OPPOSED_RISE
    # Read from the generator, not copied. When ribbon_bore grew a per-shape
    # facet default this file did not, and a bare --shape=wave drew 611.1mm
    # here against the generator's 836.5mm while --shape=spiral drew nothing
    # at all. That is the second time a second copy of the generator's
    # argument handling has quietly diverged in this file.
    if B.SHAPE in B.FACET_BY_SHAPE and not any(
            x.startswith('--facet=') for x in a):
        B.FACET = B.FACET_BY_SHAPE[B.SHAPE]

    here = os.path.dirname(os.path.abspath(__file__))
    # --trace draws a centreline from stations fixed somewhere other than this
    # generator's own parameters. Each trace is kept with its provenance in
    # traces/ -- where it came from, how it was taken, what was measured -- so a
    # traced number is one somebody can check.
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
        stem = f'ribbon-traced-{doc["name"]}-bore{B.BORE:g}-{B.FACET:g}deg'
        # the trace names itself; this used to be hard-coded to the octagonal
        # trumpet, which put that title on every other traced bore
        title = (doc['name'].replace('-', ' ').title()
                 + f', {B.BORE:g}mm \u2014 traced')
        out = [x for x in a if x.startswith('--out=')]
        path = out[0].split('=', 1)[1] if out else os.path.join(here, stem + '.html')
        open(path, 'w').write(build(title))
        d = data_for()
        print(f'  {os.path.basename(path):<52}drag to turn, colour by face '
              f'or facet')
        print(f'  {"":52}{d["mm"]}mm, {d["segs"]} facets, traced')
        return 0
    if B.SHAPE == 'torus':
        stem = f'ribbon-torus-bore{B.BORE:g}-{B.FACET:g}deg-R{B.RADIUS:g}'
        # NOT "Octagonal Torus". That title was written when 45 degrees was the
        # only ring anyone had drawn, and it then headed a 13-facet ring -- a
        # page calling a thirteen-sided figure an octagon, with the facet count
        # right there in the panel below it. The ring says how many sides it
        # has.
        title = (f'Closed Ring, {int(round(360.0 / B.FACET))} Facets, '
                 f'{B.BORE:g}mm Bore')
    elif B.SHAPE == 'racetrack':
        stem = (f'ribbon-racetrack-bore{B.BORE:g}-{B.FACET:g}deg-{B.LOBES}lobes'
                f'-R{B.LOBE_R:g}-cap{B.RACE_CAP_R:g}')
        title = (f'Closed Serpentine Racetrack, {B.LOBES} Lobes a Side, '
                 f'{B.BORE:g}mm Bore')
    elif B.SHAPE == 'scallop':
        stem = (f'ribbon-scallop-bore{B.BORE:g}-{B.FACET:g}deg-{B.LOBES}lobes'
                f'-R{B.LOBE_R:g}-in{B.SCALLOP_IN_R:g}')
        title = (f'Closed Serpentine, {B.LOBES} Lobes, {B.BORE:g}mm Bore')
    elif B.SHAPE == 'wave':
        stem = (f'ribbon-wave-bore{B.BORE:g}-{B.FACET:g}deg-'
                f'{B.WAVE_LOBE_ARCS}arc')
        title = f'Ribbon Wave, {B.BORE:g}mm Bore'
    elif B.SHAPE == 'spiral':
        stem = (f'ribbon-spiral-bore{B.BORE:g}-{B.FACET:g}deg-'
                f'R{B.SPIRAL_RI:.0f}to{B.SPIRAL_RO:.0f}')
        title = f'Ribbon Spiral, {B.BORE:g}mm Bore'
    elif B.SHAPE == 'volute':
        stem = (f'ribbon-volute-bore{B.BORE:g}-{B.FACET:g}deg-'
                f'R{B.VOL_R0:.0f}-step{B.VOL_STEP:.0f}')
        title = f'Ribbon Double Volute, {B.BORE:g}mm Bore'
    elif B.SHAPE == 'dspiral':
        # --ds-half is a different bore, not a view of the same one: it stops at
        # the centre and runs out from there. Without this it took the full
        # spiral's name and title, which is the mistake the else-branch below
        # exists to stop, one level further in.
        stem = (f'ribbon-dspiral-bore{B.BORE:g}-{B.FACET:g}deg-'
                f'R{B.DS_R0:.0f}-pitch{B.DS_PITCH:.0f}'
                + ('-halftest' if B.DS_HALF else ''))
        title = ('Ribbon Double Spiral, Centre Half, %gmm Bore' % B.BORE
                 if B.DS_HALF
                 else f'Ribbon Double Spiral, {B.BORE:g}mm Bore')
    elif B.SHAPE in ('serpentine', 'opposed'):
        stem = (f'ribbon-{B.SHAPE}-bore{B.BORE:g}-{B.FACET:g}deg-'
                f'{B.LOBES}lobes-R{B.LOBE_R:.0f}')
        title = ('Ribbon Opposed-Ends Bore, %gmm' % B.BORE
                 if B.SHAPE == 'opposed'
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
        sys.exit(f'ribbon_view: no title or filename for --shape={B.SHAPE}. '
                 f'Add it here as well as in ribbon_bore.centreline().')
    out = [x for x in a if x.startswith('--out=')]
    hm = [x for x in a if x.startswith('--home=')]
    embed = '--embed' in a
    # THE PAGE BELONGS BESIDE ITS CUT FILES, not at the root of swept-curve.
    # The default was `here`, which is where the traced and torus pages ship and
    # nowhere any ordinary shape's page lives: every one of the seven sits in
    # <shape>/<stem>/ with the sheets it describes. So a bare run dropped an
    # unshipped duplicate at the root, one directory up from the real page and
    # beside the one root page that is real. Found by running the file with no
    # arguments, which is the only way anyone would meet it.
    #
    # The design directory has to EXIST. ribbon_bore.py makes it when it writes
    # the sheets, so its absence means this is a shape-and-parameter combination
    # nothing has cut -- and inventing a directory for a viewer is how strays get
    # made in the first place. Say so and ask for --out instead.
    design = os.path.join(here, B.SHAPE, stem)
    if out:
        path = out[0].split('=', 1)[1]
    elif os.path.isdir(design):
        path = os.path.join(design, stem + ('-embed.html' if embed else '.html'))
    else:
        sys.exit(f'ribbon_view: no cut files at {os.path.relpath(design)}, so '
                 f'there is nowhere this page belongs.\n'
                 f'  Draw the design first, or name the file with --out=PATH.')
    open(path, 'w').write(build(title, embed,
                                hm[0].split('=', 1)[1] if hm else
                                'https://gernreich.github.io/trumpet/'))
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
