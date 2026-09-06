#!/usr/bin/env python3
"""The volute: a metre of bore wound flat, drawn as semicircles of stepping radius.

    python3 volute.py [--r0=82.3] [--step=24] [--semis=6] [--facet=45]

A spiral whose radius is still changing across a facet cannot be offset
correctly. offset() in ribbon_bore.py mitres a vertex assuming the curvature
either side of it is constant, which is true of an arc and false of a spiral,
and building this shape as a smooth spiral cost 6.44mm of a 10mm airway - the
same class of fault as a bore that measures 10 by 7. So the curve here is a
chain of semicircles: the radius holds across each one and steps only at the
joins, where a mitre already expects a corner. It is the classical compass
construction of a spiral, and it is what every other shape in this repository
already relies on.

WHAT THIS IS NOT, YET. Two things are unsolved, and both are recorded here
rather than in a cut file, because there is no cut file:

  1. The inner end is enclosed. A volute winds inward and stops at the centre,
     and that end has nowhere to go: measured against the rest of the bore its
     lead comes within 7.75mm where it needs 20, and a straight lead leaving
     the centre runs 1mm before it is inside the coil. One opening reaches the
     rim; the other cannot.

  2. The ends are not opposed. A chord's direction is the tangent at its arc's
     midpoint, so F facets turn the run (F-1) facets, not F. Six semicircles at
     45 degrees is 24 facets, which turns 1035 degrees and leaves the openings
     135 degrees apart. Opposed needs (F-1) a whole number of turns, so at 45
     degree facets F must be 8k+1 - one facet more than any whole number of
     semicircles can give.

Both are geometry, not parameters. Interleaving a return arm so that both ends
reach the rim is the piece of work that would fix (1) and, with one extra
facet, (2) with it.
"""
import json, math, os, sys

BORE, THICK, WEB = 10.0, 3.0, 2.0
BAND = BORE + 2 * THICK + 2 * WEB          # 20mm: two runs need this much apart
LEAD = 20.0


def floor_radius(facet):
    """Tightest arc that still leaves a tooth on the inner panel.

    The inner wall sits (BORE + THICK) / 2 inside the centreline and its facet
    is a chord 2r sin(phi/2), which has to carry a 6mm tooth with a 2mm
    shoulder either side. R26 at 30 degree facets, R20 at 45 - which is the
    whole reason this shape is drawn at 45.
    """
    return (BORE + THICK) / 2 + 10.0 / 2 / math.sin(math.radians(facet / 2))


def centreline(r0, step, semis, facet):
    """Semicircles of stepping radius, each starting where the last ended."""
    per = int(round(180.0 / facet))
    if abs(per * facet - 180.0) > 1e-9:
        raise ValueError(f'{facet:g} degree facets do not divide a semicircle.')
    radii = [r0 - k * step / 2 for k in range(semis)]
    if min(radii) < floor_radius(facet):
        raise ValueError(
            f'the tightest arc is R{min(radii):.1f} and a {BORE:g}mm bore at '
            f'{facet:g} degree facets needs R{floor_radius(facet):.1f}.')
    pts = [(radii[0], 0.0)]
    ang = 0.0
    for r in radii:
        px, py = pts[-1]
        cx, cy = px - r * math.cos(ang), py - r * math.sin(ang)
        for i in range(1, per + 1):
            th = ang + math.pi * i / per
            pts.append((cx + r * math.cos(th), cy + r * math.sin(th)))
        ang += math.pi

    def out(p, q):
        dx, dy = p[0] - q[0], p[1] - q[1]
        n = math.hypot(dx, dy)
        return (p[0] + dx / n * LEAD, p[1] + dy / n * LEAD)

    return [out(pts[0], pts[1])] + pts + [out(pts[-1], pts[-2])], radii


def seg_gap(a, b, c, d):
    def pt(p, u, v):
        ux, uy = u
        dx, dy = v[0] - ux, v[1] - uy
        L = dx * dx + dy * dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - ux) * dx + (p[1] - uy) * dy) / L))
        return math.hypot(p[0] - (ux + t * dx), p[1] - (uy + t * dy))
    return min(pt(a, c, d), pt(b, c, d), pt(c, a, b), pt(d, a, b))


def closest(pts, along=80.0):
    """Nearest approach of the bore to itself, ignoring its own neighbourhood."""
    run = [0.0]
    for i in range(len(pts) - 1):
        run.append(run[-1] + math.dist(pts[i], pts[i + 1]))
    worst = float('inf')
    for i in range(len(pts) - 1):
        for j in range(i + 1, len(pts) - 1):
            if run[j] - run[i + 1] < along:
                continue
            worst = min(worst, seg_gap(pts[i], pts[i + 1], pts[j], pts[j + 1]))
    return worst


def openings(pts):
    """Degrees between the two openings. An opening faces OUT of the tube, so
    the mouth faces back along the run and the far end forwards; opposed is
    180 and it is what a mouthpiece and a bell want."""
    ax, ay = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
    bx, by = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
    mx, my = -ax, -ay
    dot = (mx * bx + my * by) / (math.hypot(mx, my) * math.hypot(bx, by))
    return math.degrees(math.acos(max(-1.0, min(1.0, dot))))


def offset(poly, dist):
    segs = []
    for a, b in zip(poly, poly[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        n = math.hypot(dx, dy)
        nx, ny = -dy / n * dist, dx / n * dist
        segs.append(((a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny)))

    def meet(s, t):
        (x1, y1), (x2, y2) = s
        (x3, y3), (x4, y4) = t
        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
        if abs(den) < 1e-12:
            return s[1]
        u = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        return (x1 + u * (x2 - x1), y1 + u * (y2 - y1))

    return ([segs[0][0]] + [meet(s, t) for s, t in zip(segs, segs[1:])]
            + [segs[-1][1]])


def main():
    a = sys.argv[1:]

    def flag(name, cast, default):
        hit = [x for x in a if x.startswith(f'--{name}=')]
        return cast(hit[0].split('=', 1)[1]) if hit else default

    r0 = flag('r0', float, 82.3)
    step = flag('step', float, 24.0)
    semis = flag('semis', int, 6)
    facet = flag('facet', float, 45.0)

    c, radii = centreline(r0, step, semis, facet)
    length = sum(math.dist(c[i], c[i + 1]) for i in range(len(c) - 1))
    gap = closest(c)
    facets = len(c) - 3
    turn = (facets - 1) * facet
    xs = [p[0] for p in c]
    ys = [p[1] for p in c]

    print(f'volute   {BORE:g}mm square, {facet:g} degree facets')
    print(f'  {semis} semicircles, R{radii[0]:g} down to R{radii[-1]:g}, '
          f'{step:g}mm step')
    print(f'  centreline {length:.1f}mm, section {BORE:g} x {BORE:g} = '
          f'{BORE * BORE:.0f}mm2')
    print(f'  {facets} facets turn the run {turn:g} degrees '
          f'({turn % 360:g} past a whole number of turns)\n')

    def note(ok, what, detail):
        print(f'  {"pass" if ok else "FAIL"}  {what:<40} {detail}')

    note(gap >= BAND, 'the bore stays clear of itself',
         f'{gap:.2f}mm against the {BAND:g}mm cheek band')
    note(abs(openings(c) - 180.0) < 1e-6, 'the two openings are opposed',
         f'{openings(c):.0f} degrees apart, 180 is opposed')
    note(min(radii) >= floor_radius(facet), 'every arc holds a tooth',
         f'R{min(radii):.1f} against R{floor_radius(facet):.1f} needed')
    note(max(xs) - min(xs) + BAND <= 580 and max(ys) - min(ys) + BAND <= 288,
         'the cheek fits the P2S bed',
         f'{max(xs) - min(xs) + BAND:.0f} x {max(ys) - min(ys) + BAND:.0f}mm '
         f'against 580 x 288')

    here = os.path.dirname(os.path.abspath(__file__))
    data = {'centre': c, 'radii': [round(r, 1) for r in radii],
            'band_in': offset(c, -BAND / 2), 'band_out': offset(c, BAND / 2),
            'air_in': offset(c, -BORE / 2), 'air_out': offset(c, BORE / 2),
            'len': round(length, 1), 'gap': round(gap, 2),
            'openings': round(openings(c))}
    bxs = [p[0] for p in data['band_out']] + [p[0] for p in data['band_in']]
    bys = [p[1] for p in data['band_out']] + [p[1] for p in data['band_in']]
    data['bbox'] = [round(min(bxs), 1), round(min(bys), 1),
                    round(max(bxs) - min(bxs), 1), round(max(bys) - min(bys), 1)]
    with open(os.path.join(here, 'volute.json'), 'w') as f:
        json.dump(data, f)
    print(f'\n  wrote volute.json  ({data["bbox"][2]} x {data["bbox"][3]}mm cheek)')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except ValueError as e:
        print(f'error: {e}')
        sys.exit(1)
