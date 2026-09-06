#!/usr/bin/env python3
"""An interactive view of a ribbon bore: drag to turn.

    python3 ribbon_view.py                       # the coupon
    python3 ribbon_view.py --shape=serpentine    # and so on, same flags

Writes one self-contained HTML page beside the cut files it belongs to, so a
design folder holds the thing you cut and the thing you turn around, and they
cannot drift apart.

It draws the AIRWAY first - the passage the air actually takes, bounded by
the wall faces at +-bore/2 and the cheeks at +-bore/2. That is why it exists:
the bore came out 3mm narrow for a week because nothing drew the space inside
it, and a picture of the plywood alone would not have shown that.

It also draws the two cheek plates at full band width, because the airway on
its own reads as a much thinner object than the part you cut. Eight faces, not
four: the six airway faces, then 'ply, top' and 'ply, bottom'. Colour by face
to tell them apart.

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
    for i in range(len(c) - 1):
        p, q = 4 * i, 4 * (i + 1)
        Q.append({'v': [p + 0, p + 1, q + 1, q + 0], 'f': 0, 's': i})   # inner
        Q.append({'v': [p + 3, q + 3, q + 2, p + 2], 'f': 1, 's': i})   # outer
        Q.append({'v': [p + 1, p + 2, q + 2, q + 1], 'f': 2, 's': i})   # top
        Q.append({'v': [p + 0, q + 0, q + 3, p + 3], 'f': 3, 's': i})   # bottom
    # The plywood, not just the passage. The airway above is 10mm across; the
    # cheek that carries it is 20mm across and sits 3mm proud of it top and
    # bottom, and a render of the airway alone reads as a much thinner object
    # than the part you cut. These are the two cheek plates, at full band width.
    half = B.band() / 2.0
    e = B.offset(c, half)
    g = B.offset(c, -half)
    if sum(B.seglen(p, q) for p, q in zip(e, e[1:])) > \
       sum(B.seglen(p, q) for p, q in zip(g, g[1:])):
        e, g = g, e
    base = len(V)
    for i in range(len(c)):
        V += [[e[i][0], e[i][1], h + B.THICK], [g[i][0], g[i][1], h + B.THICK],
              [e[i][0], e[i][1], -h - B.THICK], [g[i][0], g[i][1], -h - B.THICK]]
    for i in range(len(c) - 1):
        p, q = base + 4 * i, base + 4 * (i + 1)
        Q.append({'v': [p + 0, p + 1, q + 1, q + 0], 'f': 6, 's': i})   # top ply
        Q.append({'v': [p + 2, q + 2, q + 3, p + 3], 'f': 7, 's': i})   # bottom ply

    n = len(c) - 1
    if not shut:
        Q.append({'v': [0, 1, 2, 3], 'f': 4, 's': 0})                   # mouth
        Q.append({'v': [4*n+3, 4*n+2, 4*n+1, 4*n+0], 'f': 5, 's': n-1})  # far end
    # a closed ring has no mouth and no far end; the last station IS the first,
    # so its four vertices are already coincident with station 0's

    # The spiral has no single bend radius - that is the point of it - so it
    # reports the range it sweeps. Falling through to RADIUS printed the
    # coupon's R30 on a bore whose arcs run R34.7 to R112.9.
    R = (B.WAVE_TROUGH_R if B.SHAPE == 'wave'
         else B.SPIRAL_RI if B.SHAPE == 'spiral'
         else B.LOBE_R if B.SHAPE in ('serpentine', 'opposed') else B.RADIUS)
    return {
        'V': [[round(v, 3) for v in p] for p in V],
        'Q': Q,
        'bore': B.BORE,
        'mm': round(sum(B.seglen(p, q) for p, q in zip(c, c[1:])), 1),
        'facet': B.FACET,
        'shape': B.SHAPE,
        'rrange': ([round(B.SPIRAL_RI, 1), round(B.SPIRAL_RO, 1)]
                   if B.SHAPE == 'spiral' else None),
        'flat': B.SHAPE == 'spiral',
        'R': R,
        'segs': n,
        'over': round(100 * (1 / math.cos(math.radians(B.FACET) / 2) - 1), 2),
        'pal': wheel(n),
        'shut': shut,
        # always eight, in face-index order; the key shows only the ones the
        # quads actually use, so a closed ring drops mouth and far end by
        # itself rather than by shifting every index after them
        'faces': ['inner wall', 'outer wall', 'top cheek', 'bottom cheek',
                  'mouth', 'far end', 'ply, top', 'ply, bottom'],
        'facecol': ['#5aa9e6', '#3d7ebd', '#c9d6e3', '#8fa3b8',
                    '#1c1c20', '#e0457b', '#d8cbb2', '#b9a888'],
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
    : (D.shut ? [] : [[D.facecol[4],'mouth'], [D.facecol[5],'far end']]).concat(
      [[D.pal[0], 'facet 1'], [D.pal[Math.floor(D.segs/2) % D.pal.length],
        'facet ' + (Math.floor(D.segs/2)+1)],
       [D.pal[(D.segs-1) % D.pal.length], 'facet ' + D.segs]]);
  for (const [c,n] of rows){
    const d = document.createElement('div'); d.className = 'key';
    d.innerHTML = `<span class="sw" style="background:${c}"></span><span>${n}</span>`;
    k.appendChild(d);
  }
}

$('sub').innerHTML = `<b>${D.bore} \u00d7 ${D.bore}mm</b> section, `
  + `<b>${D.mm}mm</b> of centreline, ${D.segs} facets of ${D.facet}\u00b0 `
  + `\u2014 exact along every facet, <b>+${D.over}%</b> at each mitre`;
$('nums').innerHTML = [
  ['shape', D.shape], ['bore', D.bore + ' \u00d7 ' + D.bore + 'mm'],
  ['section', (D.bore*D.bore) + 'mm\u00b2'],
  ['centreline', D.mm + 'mm'],
  ['bend radius', D.rrange ? ('R' + D.rrange[0] + ' to R' + D.rrange[1]) : (D.R + 'mm')],
  ['R / bore', D.rrange
     ? (D.rrange[0]/D.bore).toFixed(1) + ' to ' + (D.rrange[1]/D.bore).toFixed(1)
     : (D.R/D.bore).toFixed(1)],
  ['facet', D.facet + '\u00b0'], ['area at a mitre', '+' + D.over + '%'],
].map(([a,b]) => `<dt>${a}</dt><dd>${b}</dd>`).join('');

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
  + `<a href="__HOME__" target="_top">bore-ribbon</a>`;
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
    for flag, cast in (('shape', str), ('bore', float), ('facet', float),
                       ('radius', float), ('lobes', int), ('lobe-r', float),
                       ('rise', float), ('lead', float), ('web', float),
                       ('spiral-facets', int), ('spiral-ri', float),
                       ('spiral-ro', float), ('wave-rise', float),
                       ('wave-trough-r', float), ('wave-crest-r', float),
                       ('wave-lead-r', float)):
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
                'wave-lead-r': 'WAVE_LEAD_R'}[flag]
        setattr(B, name, cast(hit[0].split('=', 1)[1]))

    # the opposed shape carries its own lobe; see ribbon_bore.OPPOSED_R
    if B.SHAPE == 'opposed':
        if not any(x.startswith('--lobe-r=') for x in a):
            B.LOBE_R = B.OPPOSED_R
        if not any(x.startswith('--rise=') for x in a):
            B.RISE = B.OPPOSED_RISE

    here = os.path.dirname(os.path.abspath(__file__))
    # --trace draws a centreline measured off somebody else's cut file rather
    # than one this repository generates. trumpet-octagonal's bore is the only
    # one so far: its sheet is a hand-authored band and the curve is not
    # written down anywhere as parameters, so it was traced and the trace is
    # kept, with its provenance, in traces/.
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
        stem = f'ribbon-torus-bore{B.BORE:g}-{B.FACET:g}deg-R{B.RADIUS:.0f}'
        title = f'Octagonal Torus, {B.BORE:g}mm Bore'
    elif B.SHAPE == 'wave':
        stem = (f'ribbon-wave-bore{B.BORE:g}-{B.FACET:g}deg-'
                f'{B.WAVE_LOBE_ARCS}arc')
        title = f'Ribbon Wave, {B.BORE:g}mm Bore'
    elif B.SHAPE == 'spiral':
        stem = (f'ribbon-spiral-bore{B.BORE:g}-{B.FACET:g}deg-'
                f'R{B.SPIRAL_RI:.0f}to{B.SPIRAL_RO:.0f}')
        title = f'Ribbon Spiral, {B.BORE:g}mm Bore'
    elif B.SHAPE in ('serpentine', 'opposed'):
        stem = (f'ribbon-{B.SHAPE}-bore{B.BORE:g}-{B.FACET:g}deg-'
                f'{B.LOBES}lobes-R{B.LOBE_R:.0f}')
        title = ('Ribbon Opposed-Ends Bore, %gmm' % B.BORE
                 if B.SHAPE == 'opposed'
                 else f'Ribbon Serpentine, {B.BORE:g}mm Bore')
    else:
        stem = f'ribbon-coupon-bore{B.BORE:g}-{B.FACET:g}deg-R{B.RADIUS:g}'
        title = f'Ribbon Coupon, {B.BORE:g}mm Bore'
    out = [x for x in a if x.startswith('--out=')]
    hm = [x for x in a if x.startswith('--home=')]
    embed = '--embed' in a
    path = out[0].split('=', 1)[1] if out else os.path.join(
        here, stem + ('-embed.html' if embed else '.html'))
    open(path, 'w').write(build(title, embed,
                                hm[0].split('=', 1)[1] if hm else
                                'https://gernreich.github.io/trumpet/parts/bore/concept/swept-curve/ribbon/'))
    d = data_for()
    print(f'  {os.path.basename(path):<52}drag to turn, colour by face '
          f'or facet')
    print(f'  {"":52}{d["mm"]}mm, {d["segs"]} facets, '
          f'{len(d["Q"])} quads')
    return 0


if __name__ == '__main__':
    sys.exit(main())
