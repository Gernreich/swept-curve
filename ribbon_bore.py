#!/usr/bin/env python3
"""A bore of constant cross-section swept along a planar curve.

    python3 ribbon_bore.py                      # the 10mm 30-degree coupon
    python3 ribbon_bore.py --no-write           # the numbers, no file

Sweep a rectangle along a curve that lies in a plane, with one axis normal to
that plane, and the duct has two FLAT faces and two CYLINDRICAL ones. The flat
pair are the cheeks and cut straight from the sheet. The curved pair are the
whole problem: 3mm birch will not bend to these radii, so they are faceted -
short flat panels, each finger-jointed into both cheeks.

The section is exactly bore x bore along every facet. At each facet joint the
walls mitre, and the area there is bore^2 / cos(phi/2):

    phi = 90 deg   +41.4%      a turn in the Minecraft lattice
    phi = 45 deg    +8.2%      the octagonal torus
    phi = 30 deg    +3.5%      this
    phi = 15 deg    +0.9%

So the facet angle is the whole design dial, and it trades against part count
and against how short the inner panels get.

WHAT LIMITS THE BEND. The inner wall is the centreline offset inward by
bore/2, so its radius is R - bore/2 and there is no bore at all below
R = bore/2. Long before that the inner panel gets too short to carry a finger:
a Boxes.py tooth is 2 x thickness and does NOT scale with the bore, so at the
10mm bore and 30 degrees the inner panel holds no tooth at all until R = 25mm.
That is why this coupon is R 25 and not the R 15 it looks like it wants to be.
"""
import math
import os
import sys

BORE = 10.0          # the square section, mm
FACET = 30.0         # degrees of turn per wall panel
RADIUS = 30.0        # bend radius of the centreline; see the minimum below
TAIL = 15.0          # straight lead-in and lead-out
THICK = 3.0          # ply, NOMINAL: what the design is dimensioned on
# What the sheet actually calipers, 2026-09-09. It is a second number and it
# earns its keep: THICK carries the DRAWN dimensions -- the wall offsets, the
# cheek band, TOOTH at 2*THICK, and the radii the shapes were solved against --
# while SHEET is the MATERIAL, and the only place material thickness belongs is
# the depth of the hole it has to pass through.
#
# Setting THICK to 2.94 instead was tried first and is wrong. It moves the
# geometry: the wall offset goes 6.5 -> 6.47, the band 20 -> 19.88, and the
# tooth 6 -> 5.88, which invalidates every shape whose parameters were solved
# to land on 1000.0mm inside a 20mm band. It failed 'opposed' outright -- a
# 2.14mm panel where 9.88mm is needed -- and took the serpentine's web from
# 2.05mm to 1.106mm. The bore's walls being 0.06mm thinner than drawn opens the
# airway to 10.06mm, which is the harmless direction and not worth re-solving
# four shapes over.
SHEET = 2.94
WEB = 2.0            # material left outboard of a slot; the cheek's thin part

# Where a wall's CENTRELINE sits, and where the cheek's edge does.
#
# The wall is THICK thick and its slot is centred on this line, so its inner
# face stands THICK/2 inboard of it. Offsetting the walls to +-BORE/2 - which
# is what this did until 2026-09-03 - therefore puts the wall FACES at
# +-(BORE-THICK)/2 and makes the airway BORE-THICK wide: 7mm at the 10mm bore,
# not 10. Reported from a measurement of a cut file, and the section check did
# not catch it because it measured centreline to centreline and called that
# the bore.
# Functions, not constants: --bore and --web change these, and a module-level
# value computed at import cannot follow. WALL_OFF was a constant for exactly
# one run, and a --bore on the command line quietly kept the default figure -
# which the airway check caught, reporting the whole difference as error.
def wall_off():
    return BORE / 2 + THICK / 2


def cheek_off():
    return wall_off() + THICK / 2 + WEB


def band():
    return 2 * cheek_off()
BURN = 0.13          # kerf, MEASURED 2026-09-09; the FULL width the laser
                     # takes out, centred on the line. It was 0.1 by assumption.
# NOTE the difference from bore_split.py, which calls its own constant BURN and
# means the RADIUS, because it hands the number to Boxes.py and Boxes offsets
# each side of a line by burn. This file draws its own outlines and offsets by
# BURN/2 a side, so here the number is the whole cut. Same name, half the
# meaning; --kerf= is the flag on both, and it takes the measured width.
# Per side, and a lookup of what has actually been cut, not a curve through
# it - bore_split.py's PLAY_BY_BORE, same figure. One bore has been measured,
# and 0.025 per side is what went together on it. A bore not in the table gets
# that value too, because too loose is a worse joint and too tight is no joint
# at all.
PLAY_BY_BORE = {10.0: 0.025}
# The dspiral halftest assembled loose, and the cause was these two constants,
# not the clearance. THICK was 3.0 against a sheet that calipers at 2.94, and
# BURN was 0.1 against a kerf of 0.13. Every kerf compensation in the file was
# therefore 0.03mm out, in the direction that makes parts smaller and holes
# bigger, and the ply was 0.06mm thinner than the slot cut for it:
#
#                          along the tooth   across the ply
#     as it was cut             +0.110mm         +0.090mm
#     with the true numbers     +0.050mm         +0.000mm
#
# The first row is the joint that was loose - twice the slack the design asks
# for in one direction and, in the other, 0.09mm of slack where it specifies
# none. The second row is what this file always meant to cut.
#
# So the fix is the constants, and this knob goes back to nothing. It is kept
# at zero rather than deleted because it is the lever to reach for if a joint
# is still wrong once the numbers under it are right: it takes its value off
# the slot, in both directions, and never off the tab.
SLOT_TIGHTEN = 0.0
PLAY_UNMEASURED = 0.025


def play():
    """Per side, for the current bore.

    A function for the same reason wall_off() is one: it was a global that
    only main() assigned, so anything importing this module and calling
    build() got whichever bore's figure happened to be baked in at import -
    0 - and drew slots 0.025mm off. Nothing shipped wrong, because main()
    did set it, but every check written against the library disagreed with
    the file by exactly the play.
    """
    return PLAY_BY_BORE.get(round(BORE, 3), PLAY_UNMEASURED)
TOOTH = 2 * THICK    # Boxes.py FingerJointSettings; does not scale
SHOULDER = 2.0       # least material either side of a tooth
# The narrowest rib of ply the gate will pass, the same 1.5mm bore_split.py,
# check.py and flat-part-check.py all use. Measured AFTER the kerf, since two
# lines 0.1mm apart are one line once the laser has been down both.
MIN_FEATURE = 1.5

CUT, INNER, MARK = '#000000', '#ff8000', '#0000ff'
OUT = None           # --out=PATH, for trying a change without touching the file
PORT = False         # --port: a bore-square opening through the cheek at the
                     # mouth, so a mouthpiece or a bell can go in at 90
                     # degrees to the plane the bore is wound in
BED_W, BED_H = 600.0, 308.0        # xTool P2S work area

# --shape. 'coupon' is the 180 degree test piece; 'serpentine' is a run of
# alternating half-circles joined by straight verticals, which is the drawn
# shape generalised. LOBES/LOBE_R/RISE describe it.
SHAPE = 'coupon'
# Solved against this generator's own faceted centreline, not a smooth arc:
# an inscribed chord is 1.14% short of the arc it spans, so a radius picked
# from the arc comes out 11mm long over a metre. R here gives 1000.0mm.
# The rise is chosen to balance the cheek on the bed rather than to be small:
# a half-circle advances only 2/pi of its own length in x, so a 1000mm run
# wants 637mm of width and the bed has 600 - a straight vertical run buys
# length in y, where there is room. At rise 90 the cheek is 532 x 254mm.
LOBES, LOBE_R, RISE, LEAD = 3, 71.754, 90.0, 20.0
# A PORTED bore leads longer, and nothing else does. The port is a bore-square
# hole on the centreline and the tab slots run up both walls at wall_off, so a
# full-width port passes within 0.16mm of a slot wherever it sits -- measured
# along every design, the best any of them manages is 1.45mm against the 1.63mm
# that leaves 1.5mm of ply after the kerf. The room has to come from the teeth,
# not the placement.
#
# At 20mm the lead panel carries ONE tooth, dead centre, right where the port
# is. At 30mm it carries two, at 9mm and 21mm from the tip, and the port spans
# 5.07 to 14.94 -- so the second one clears and the panel keeps a tab. The
# first is dropped by teeth_kept() below. The next slot after that is 7.72mm
# away, which is room to spare.
#
# Applied only when --port is set, so every plain design keeps the length it
# was cut at.
# The port is a SLOT, not a square, and that is the whole trick. The tab slots
# run up both walls at wall_off the entire length of the bore, so what a port
# has to clear is measured ACROSS the run and nothing else -- a bore-square
# 10 x 10 passes within 0.16mm of one wherever it is put, on every shape here.
# Length ALONG the run costs no clearance at all, so it is free, and it buys
# back the area that narrowing takes away:
#
#     across  along   clearance   opening
#         10     10      0.16mm     100mm2   the old square, uncuttable
#          7      7      1.66mm      49mm2
#          7     14      1.66mm      98mm2   this
#        6.6     20      1.86mm     132mm2
#
# 7 x 14 is 98mm2 against the bore's own 100, so the air sees no restriction
# worth the name, and every panel keeps its tab. A mouthpiece has to plug in
# 7 x 14 or seat over the hole; it will not take a 10mm square spigot.
PORT_ACROSS, PORT_ALONG, PORT_FROM_TIP = 7.0, 14.0, 10.0
# TRIED AND REJECTED, 2026-09-09. It does clear the port: the coupon goes from
# 0.030mm of ply to 2.931mm and passes every check. But the lead is part of the
# centreline, so lengthening it moves the whole coil -- the spiral's cheek
# starts crossing itself, the volute puts 39 slot corners outside its cheek and
# its web collapses to 0.080mm, and four more shapes lose a label into a slot.
# The label-sliding code below already says this in one line, which was written
# before and should have been read first: "the alternative, giving the port a
# bore of extra lead, moves the whole coil and was what made the cheek cross
# itself". Kept as a number so the next person does not spend the afternoon
# rediscovering it.
PORT_LEAD_REJECTED = 30.0
# 'opposed' cannot reuse those. Its closing quarter turn runs outward rather
# than folding back inside the lobes, which spends 82mm of width the
# serpentine never spends, and R71.754 puts the cheek at 614mm on a bed with
# 580 of usable width. A half-circle advances 2/pi of its own length in x
# however the run is divided, so more lobes would not buy anything: the arc
# itself has to come down and the straights take up the slack. These give
# exactly 1000.0mm again, with the cheek at 562 x 231mm.
OPPOSED_R, OPPOSED_RISE = 64.0, 82.4539
# 'spiral' is the drawn shape: a flat coil of two and a bit turns with a lead
# at each end. Every facet is its own constant-radius arc and the radius steps
# by a fixed amount, which is the classical compass spiral and, more to the
# point, the only construction offset() can follow - it mitres a vertex
# assuming the curvature either side is constant, true of an arc and false of
# a smooth spiral, and building this smoothly cost 6.44mm of a 10mm airway.
#
# 17 facets is not a free choice. A chord's direction is the tangent at its
# arc's midpoint, so F facets turn the run (F-1) facets, and the openings are
# opposed only when that is a whole number of turns: F = 8k+1 at 45 degrees.
# The radii then follow from wanting 1000mm with 22mm between neighbouring
# passes, against the 20mm the cheek band needs.
SPIRAL_FACETS, SPIRAL_RI, SPIRAL_RO = 17, 34.662, 112.903
# The angle each shape is drawn at, where it is not FACET's default 30.
FACET_BY_SHAPE = {'wave': 45.0, 'spiral': 45.0, 'volute': 45.0}
# 'dspiral' is two spiral arms half a turn apart about one centre, crossed at
# the middle by a straight - the double spiral. Arm B IS arm A rotated 180
# degrees, so the whole path is point-symmetric about the centre and the gap
# between neighbouring passes is DS_PITCH/2 by construction rather than by
# search. Pick the pitch and you have picked the gap; the cheek band needs 20.
#
# Its vertices sit on a smooth Archimedean spiral r = R0 + b*theta sampled every
# FACET degrees, NOT on the stepping-radius arcs 'spiral' uses. The note above
# says that is the one construction offset() cannot follow. That note is about
# offsetting the smooth curve and faceting the result separately; offsetting the
# faceted centreline is exact whatever placed its vertices, and the airway check
# measures 4.1e-14mm of error here against the 10mm bore. The stepping-radius
# construction cannot be used for this shape anyway: its polar radius advances
# unevenly - 7mm across one half turn and 32mm across another on the shipped
# spiral - and two arms interleaved at those radii collide.
#
# The crossover is one arc of DS_CROSS_R swinging off the arm's inner end onto a
# heading that points at the centre, then a straight through it. Both are solved,
# not chosen. A tangent from the centre to that arc only exists when the arm's
# inner end is outside twice the arc radius, so DS_R0 > 2 * DS_CROSS_R is a hard
# floor and the reason the middle is open rather than tight.
# These are the shipped design, so a bare --shape=dspiral rebuilds the sheets
# beside this file rather than something near them. R28 was the default while
# the design was cut at R30, and a bare run refused on a 9.77mm inner panel.
DS_PITCH, DS_R0, DS_FACETS, DS_CROSS_R = 46.0, 62.0, 14, 30.0
# --ds-half: stop at the centre instead of carrying on into the second arm,
# and run out from there. The crossover is the part of this shape that had
# to be solved rather than chosen, so it is the part a coupon should test.
DS_HALF = False
# 'volute' is the same idea drawn the way volute.py argued it should be: not a
# smooth spiral sampled at facets, but a chain of semicircles whose radius holds
# across each arc and steps only at the joins, where a mitre already expects a
# corner. offset() mitres a vertex assuming the curvature either side is
# constant, which is true of an arc and false of a spiral, and building the
# volute smooth once cost 6.44mm of a 10mm airway.
#
# volute.py recorded two things it could not do, and both were the single arm,
# not the construction. A volute winds inward and STOPS, so the inner end is
# enclosed -- it came within 7.75mm of the rest of the bore where it needs 20 --
# and six semicircles at 45 degrees turn 1035 degrees, leaving the openings 135
# apart when opposed needs (F-1) a whole number of turns, i.e. F = 8k+1 at 45.
#
# Interleaving a return arm answers both, which is what that file said the work
# was. Two centres, so the arm is a classical two-centre volute and its eye is
# the midpoint of them, at (-VOL_STEP/4, 0); put the eye on the origin and arm B
# is arm A turned through 180 degrees, exactly as in 'dspiral'. Then there is no
# inner end to enclose, and the openings come out 180.00 degrees apart from the
# symmetry alone -- the 8k+1 rule never binds, because the two ends are one end
# and its own half-turn.
#
# The price is spacing, and it is why this is not a metre. One arm's passes are
# VOL_STEP apart; interleaving puts a pass every VOL_STEP/2, so the step has to
# carry twice the band, and a bigger step needs a bigger R0 to keep the arcs
# off the floor. Clearance alone stops at 1078mm. The tooth stops it sooner:
# the crossover's last chord is a part facet, so its panel is shorter than the
# floor radius predicts, and R20 there gives a 9.69mm inner panel against the
# 10mm a 6mm tooth needs. R22 is the first that clears. The shipped numbers are
# what came back from sweeping the generator itself rather than the geometry:
# 1179.9mm, 21.28mm of clearance, and the openings 180.00 degrees apart.
VOL_R0, VOL_STEP, VOL_SEMIS, VOL_CROSS_R = 94.0, 60.0, 2, 22.0
# 'wave' is the drawn shape: level, down into a trough, up over a crest,
# and out level again. It is the easiest bore here and worth saying why -
# nothing nests. A coil has to hold every pass 20mm off every other pass it
# wraps around, which is what made the spiral hard; a wave only has to
# clear its own two lobes, and it does that by 97mm.
#
# Equal arc counts either side of the middle make the turns cancel, so the
# openings come out opposed with no facet-counting to get right.
WAVE_LEAD_ARCS, WAVE_LOBE_ARCS = 2, 5
# A straight between the trough and the crest, for the same reason the
# serpentine has one between its lobes: curvature reverses there, and the two
# offset walls cross each other if that reversal happens at a single vertex.
# Without it the airway came out 67mm wrong on a 10mm bore.
WAVE_RISE = 100.0
WAVE_LEAD_R, WAVE_TROUGH_R, WAVE_CREST_R = 90.0, 55.0, 55.0


def walk(spec):
    """A faceted polyline from a list of ('s', mm) and ('a', degrees, sign).

    Arcs are inscribed, so a chord's direction is the tangent at its midpoint
    and the junction where a straight meets an arc turns by half a facet, not
    a whole one. That is a smaller mitre and less area error, and it falls out
    of inscribing rather than having to be arranged.
    """
    pts, x, y, a = [(0.0, 0.0)], 0.0, 0.0, 0.0
    for item in spec:
        if item[0] == 's':
            x, y = x + math.cos(a) * item[1], y + math.sin(a) * item[1]
            pts.append((x, y))
        else:
            _, deg, sign = item
            n = int(round(deg / FACET))
            if abs(n * FACET - deg) > 1e-9:
                raise ValueError(
                    f'--facet={FACET:g} does not divide a {deg:g} degree turn '
                    f'a whole number of times; {n} facets would turn '
                    f'{n * FACET:g} degrees.')
            R = LOBE_R if SHAPE in ('serpentine', 'opposed') else RADIUS
            cx = x - sign * R * math.sin(a)
            cy = y + sign * R * math.cos(a)
            t0 = math.atan2(y - cy, x - cx)
            for i in range(1, n + 1):
                t = t0 + sign * math.radians(deg) * i / n
                x, y = cx + R * math.cos(t), cy + R * math.sin(t)
                pts.append((x, y))
            a += sign * math.radians(deg)
    return pts


def flip(pts):
    """Negate y, so the file renders the way the shape is drawn.

    Everything here is worked out with y running up, the way the geometry
    reads. SVG runs y down, so writing those coordinates straight out renders
    the shape upside down - a hump becomes a trough. The cut part is identical
    either way, being a mirror of itself turned over, but a cut file that does
    not look like the thing it makes is a cut file you check twice.

    Applied here and nowhere else, so every offset, normal, mitre and label
    angle downstream is computed in the flipped space and comes out right.
    Glyphs are NOT flipped: label() already draws them for SVG.
    """
    return [(x, -y) for x, y in pts]


def centreline():
    """The centreline, already faceted at FACET and flipped into SVG's y.

    The panels ARE the segments of this polyline offset sideways - there is no
    separate faceting step, so there is nothing for it to disagree with.
    """
    if SHAPE == 'torus':
        # A closed regular ring of FACET turns: at FACET 45 an octagon, eight
        # facets and an airway between the inner and outer apothems. RADIUS is
        # the CIRCUMRADIUS of the centreline polygon, so its facet lines sit at
        # RADIUS*cos(FACET/2) - the mean of those two apothems.
        n = int(round(360.0 / FACET))
        if abs(n * FACET - 360.0) > 1e-9:
            raise ValueError(f'--facet={FACET:g} does not divide a full turn '
                             f'a whole number of times.')
        return flip(walk([('a', 360, +1)]))
    if SHAPE == 'wave':
        floor = wall_off() + (TOOTH + 2 * SHOULDER) / 2 / math.sin(
            math.radians(FACET / 2))
        tight = min(WAVE_LEAD_R, WAVE_TROUGH_R, WAVE_CREST_R)
        if tight < floor:
            raise ValueError(
                f'the tightest arc is R{tight:g} and a {BORE:g}mm bore at '
                f'{FACET:g} degree facets needs R{floor:.1f}.')
        segs = ([('a', WAVE_LEAD_R, +1)] * WAVE_LEAD_ARCS
                + [('a', WAVE_TROUGH_R, -1)] * WAVE_LOBE_ARCS
                + [('s', WAVE_RISE, 0)]
                + [('a', WAVE_CREST_R, +1)] * WAVE_LOBE_ARCS
                + [('a', WAVE_LEAD_R, -1)] * WAVE_LEAD_ARCS)
        step = math.radians(FACET)
        x = y = a = 0.0
        pts = [(0.0, 0.0)]
        for kind, v, sg in segs:
            if kind == 's':
                x, y = x + math.cos(a) * v, y + math.sin(a) * v
                pts.append((x, y))
                continue
            cx, cy = x - sg * v * math.sin(a), y + sg * v * math.cos(a)
            t0 = math.atan2(y - cy, x - cx)
            x, y = (cx + v * math.cos(t0 + sg * step),
                    cy + v * math.sin(t0 + sg * step))
            pts.append((x, y))
            a += sg * step

        def tail(u, v):
            dx, dy = u[0] - v[0], u[1] - v[1]
            m = math.hypot(dx, dy)
            return (u[0] + dx / m * LEAD, u[1] + dy / m * LEAD)
        return flip([tail(pts[0], pts[1])] + pts + [tail(pts[-1], pts[-2])])
    if SHAPE == 'spiral':
        if (SPIRAL_FACETS - 1) * FACET % 360.0 > 1e-9:
            raise ValueError(
                f'{SPIRAL_FACETS} facets turn the run '
                f'{(SPIRAL_FACETS - 1) * FACET:g} degrees, which is not a whole '
                f'number of turns, so the ends do not come out opposed. At '
                f'{FACET:g} degree facets use {int(round(360 / FACET))}k + 1.')
        floor = wall_off() + (TOOTH + 2 * SHOULDER) / 2 / math.sin(
            math.radians(FACET / 2))
        if min(SPIRAL_RI, SPIRAL_RO) < floor:
            raise ValueError(
                f'the tightest arc is R{min(SPIRAL_RI, SPIRAL_RO):g} and a '
                f'{BORE:g}mm bore at {FACET:g} degree facets needs '
                f'R{floor:.1f}.')
        step = math.radians(FACET)
        x = y = a = 0.0
        pts = [(0.0, 0.0)]
        for k in range(SPIRAL_FACETS):
            r = SPIRAL_RI + (SPIRAL_RO - SPIRAL_RI) * k / (SPIRAL_FACETS - 1)
            cx, cy = x - r * math.sin(a), y + r * math.cos(a)
            t0 = math.atan2(y - cy, x - cx)
            x, y = cx + r * math.cos(t0 + step), cy + r * math.sin(t0 + step)
            pts.append((x, y))
            a += step

        def tail(u, v):
            dx, dy = u[0] - v[0], u[1] - v[1]
            m = math.hypot(dx, dy)
            return (u[0] + dx / m * LEAD, u[1] + dy / m * LEAD)
        return flip([tail(pts[0], pts[1])] + pts + [tail(pts[-1], pts[-2])])
    if SHAPE == 'volute':
        floor = wall_off() + (TOOTH + 2 * SHOULDER) / 2 / math.sin(
            math.radians(FACET / 2))
        per = int(round(180.0 / FACET))
        if abs(per * FACET - 180.0) > 1e-9:
            raise ValueError(
                f'{FACET:g} degree facets do not divide a semicircle.')
        if VOL_STEP / 2 < band():
            raise ValueError(
                f'--vol-step={VOL_STEP:g} puts the two arms {VOL_STEP / 2:g}mm '
                f'apart and the cheek band is {band():g}mm wide. A single arm '
                f'only needs the band; interleaving a second one needs twice '
                f'it, so use --vol-step above {2 * band():g}.')
        radii = [VOL_R0 - k * VOL_STEP / 2 for k in range(VOL_SEMIS)]
        if min(radii) < floor:
            raise ValueError(
                f'the tightest arc is R{min(radii):.1f} and a {BORE:g}mm bore '
                f'at {FACET:g} degree facets needs R{floor:.1f}.')
        if VOL_CROSS_R < floor:
            raise ValueError(
                f'--vol-cross-r={VOL_CROSS_R:g} and a {BORE:g}mm bore at '
                f'{FACET:g} degree facets needs R{floor:.1f}.')

        # one arm, rim first: semicircles of stepping radius, each starting
        # where the last ended. The centres alternate between two points on
        # the x-axis, so the eye is the midpoint of them.
        arm, ang = [(radii[0], 0.0)], 0.0
        for r in radii:
            px, py = arm[-1]
            cx, cy = px - r * math.cos(ang), py - r * math.sin(ang)
            for i in range(1, per + 1):
                th = ang + math.pi * i / per
                arm.append((cx + r * math.cos(th), cy + r * math.sin(th)))
            ang += math.pi
        eye = VOL_STEP / 4.0
        arm = [(x + eye, y) for x, y in arm]      # put the eye on the origin

        # the crossover, as in 'dspiral': an arc off the inner end and then a
        # straight that has to LAND on the eye. Solve the turn, do not pick it
        # - a turn that misses leaves the two arms not joined.
        S = arm[-1]
        h0 = math.atan2(S[1] - arm[-2][1], S[0] - arm[-2][0])

        def leg(delta):
            sg = 1.0 if delta >= 0 else -1.0
            cx = S[0] + VOL_CROSS_R * math.cos(h0 + sg * math.pi / 2)
            cy = S[1] + VOL_CROSS_R * math.sin(h0 + sg * math.pi / 2)
            a0 = math.atan2(S[1] - cy, S[0] - cx)
            ex = cx + VOL_CROSS_R * math.cos(a0 + delta)
            ey = cy + VOL_CROSS_R * math.sin(a0 + delta)
            h1 = h0 + delta
            perp = -math.sin(h1) * -ex + math.cos(h1) * -ey
            along = -ex * math.cos(h1) + -ey * math.sin(h1)
            return (cx, cy), a0, perp, along

        found = None
        lo, hi, N = -math.pi * 0.99, math.pi * 0.99, 3000
        prev = lo
        for i in range(1, N + 1):
            x = lo + (hi - lo) * i / N
            if (leg(x)[2] < 0) != (leg(prev)[2] < 0):
                a, c2 = prev, x
                for _ in range(120):
                    m = (a + c2) / 2
                    if (leg(m)[2] < 0) != (leg(a)[2] < 0):
                        c2 = m
                    else:
                        a = m
                cand = (a + c2) / 2
                if leg(cand)[3] > 0:            # the eye must be AHEAD
                    found = cand
                    break
            prev = x
        if found is None:
            raise ValueError(
                'no crossover arc reaches the eye at '
                f'--vol-cross-r={VOL_CROSS_R:g}, --vol-r0={VOL_R0:g}, '
                f'--vol-step={VOL_STEP:g}.')
        (cx, cy), a0, _, _ = leg(found)
        steps = max(1, int(math.ceil(abs(math.degrees(found)) / FACET)))
        cross = [(cx + VOL_CROSS_R * math.cos(a0 + found * i / steps),
                  cy + VOL_CROSS_R * math.sin(a0 + found * i / steps))
                 for i in range(1, steps + 1)]
        cross.append((0.0, 0.0))

        # rim -> eye, then the same thing turned through 180 degrees.
        half = arm + cross
        pts = half + [(-x, -y) for x, y in reversed(half)][1:]

        def tail(u, v):
            dx, dy = u[0] - v[0], u[1] - v[1]
            m = math.hypot(dx, dy)
            return (u[0] + dx / m * LEAD, u[1] + dy / m * LEAD)
        return flip([tail(pts[0], pts[1])] + pts + [tail(pts[-1], pts[-2])])
    if SHAPE == 'dspiral':
        b = DS_PITCH / (2 * math.pi)
        floor = wall_off() + (TOOTH + 2 * SHOULDER) / 2 / math.sin(
            math.radians(FACET / 2))
        if DS_CROSS_R < floor:
            raise ValueError(
                f'--ds-cross-r={DS_CROSS_R:g} and a {BORE:g}mm bore at '
                f'{FACET:g} degree facets needs R{floor:.1f}.')
        if DS_R0 <= 2 * DS_CROSS_R:
            raise ValueError(
                f'--ds-r0={DS_R0:g} is not outside twice --ds-cross-r='
                f'{DS_CROSS_R:g}, so no straight from the centre is tangent to '
                f'the crossover arc and the two arms cannot be joined. Use '
                f'--ds-r0 above {2 * DS_CROSS_R:g}.')
        # curvature of r = R0 + b*theta is tightest at the inner end
        rho = (DS_R0 ** 2 + b ** 2) ** 1.5 / (DS_R0 ** 2 + 2 * b ** 2)
        if rho < floor:
            raise ValueError(
                f'the spiral is tightest at R{rho:.1f} where its inner end '
                f'meets the crossover, and a {BORE:g}mm bore at {FACET:g} '
                f'degree facets needs R{floor:.1f}.')
        if DS_PITCH / 2 < band():
            raise ValueError(
                f'--ds-pitch={DS_PITCH:g} puts neighbouring passes '
                f'{DS_PITCH / 2:g}mm apart and the cheek band is '
                f'{band():g}mm wide, so the two arms overlap. Use --ds-pitch '
                f'above {2 * band():g}.')

        # one arm, inner end first, on r = R0 + b*theta every FACET degrees
        arm = []
        for k in range(DS_FACETS + 1):
            th = math.radians(k * FACET)
            r = DS_R0 + b * th
            arm.append((r * math.cos(th), r * math.sin(th)))

        # the crossover: an arc of DS_CROSS_R off the inner end, then a
        # straight that has to land on the centre. Solve the turn, do not
        # pick it - a turn that misses leaves the two arms not joined.
        S = arm[0]
        h0 = math.atan2(DS_R0, b) + math.pi        # heading, travelling in
        def leg(delta):
            sg = 1.0 if delta >= 0 else -1.0
            cx = S[0] + DS_CROSS_R * math.cos(h0 + sg * math.pi / 2)
            cy = S[1] + DS_CROSS_R * math.sin(h0 + sg * math.pi / 2)
            a0 = math.atan2(S[1] - cy, S[0] - cx)
            ex = cx + DS_CROSS_R * math.cos(a0 + delta)
            ey = cy + DS_CROSS_R * math.sin(a0 + delta)
            h1 = h0 + delta
            perp = -math.sin(h1) * -ex + math.cos(h1) * -ey
            along = -ex * math.cos(h1) + -ey * math.sin(h1)
            return (cx, cy), a0, (ex, ey), h1, perp, along

        found = None
        lo, hi, N = -math.pi * 0.99, math.pi * 0.99, 3000
        prev = lo
        for i in range(1, N + 1):
            x = lo + (hi - lo) * i / N
            if (leg(x)[4] < 0) != (leg(prev)[4] < 0):
                a, c2 = prev, x
                for _ in range(120):
                    m = (a + c2) / 2
                    if (leg(m)[4] < 0) != (leg(a)[4] < 0):
                        c2 = m
                    else:
                        a = m
                cand = (a + c2) / 2
                if leg(cand)[5] > 0:            # the centre must be AHEAD
                    found = cand
                    break
            prev = x
        if found is None:
            raise ValueError(
                'no crossover arc reaches the centre at '
                f'--ds-cross-r={DS_CROSS_R:g}, --ds-r0={DS_R0:g}.')
        (cx, cy), a0, E, h1, _, t = leg(found)
        steps = max(1, int(math.ceil(abs(math.degrees(found)) / FACET)))
        cross = [(cx + DS_CROSS_R * math.cos(a0 + found * i / steps),
                  cy + DS_CROSS_R * math.sin(a0 + found * i / steps))
                 for i in range(1, steps + 1)]
        cross.append((0.0, 0.0))

        # rim -> centre, then the same thing turned through 180 degrees.
        # Negating both coordinates IS the half-turn, and it is what makes
        # the interleave exact: arm B at any bearing is arm A half a turn
        # further along, which is DS_PITCH/2 further out.
        half = list(reversed(arm)) + cross
        pts = half + [(-x, -y) for x, y in reversed(half)][1:]
        if DS_HALF:
            # a test piece off the centre: the crossover and one arm, run
            # centre-first so the mouth is the middle of the coil. The whole
            # shape is rim to rim through the centre, so half of it is
            # exactly the part worth proving before cutting the rest.
            pts = list(reversed(half))

        def tail(u, v):
            dx, dy = u[0] - v[0], u[1] - v[1]
            m = math.hypot(dx, dy)
            return (u[0] + dx / m * LEAD, u[1] + dy / m * LEAD)
        return flip([tail(pts[0], pts[1])] + pts + [tail(pts[-1], pts[-2])])
    if SHAPE in ('serpentine', 'opposed'):
        # a lead-in, a quarter turn up, then alternating half-circles joined
        # by straight verticals, and a tail. The verticals are what make it
        # fit: a half-circle advances only 2/pi of its own length in x, so a
        # 1000mm run needs 637mm of width however it is divided, and the bed
        # is 600. A vertical run buys length in y, where there is room.
        spec = [('s', LEAD), ('a', 90, +1)]
        for i in range(LOBES):
            spec.append(('a', 180, -1 if i % 2 == 0 else +1))
            if i < LOBES - 1:
                spec.append(('s', RISE))
        # 'opposed' closes with one more quarter turn, which is the whole
        # difference between the two. What a mouthpiece and a bell want is
        # their two openings facing opposite ways - you blow towards the
        # instrument and it speaks away from you. An opening faces out of the
        # tube, so the mouth faces backwards along the run and the bell
        # forwards, and the two are opposed when the bore's total turning is
        # ZERO, not 180. The serpentine's odd count of half-circles leaves it
        # at 90; this quarter turn takes it to 0.
        #
        # The sign matters and is the whole of it. Turned the other way the
        # same quarter turn reaches 180, which puts both openings on the same
        # heading and aims the bell back into the lobes with 0.2mm to spare.
        # It costs 111.4mm of centreline and no bed at all.
        if SHAPE == 'opposed':
            spec.append(('a', 90, +1))
        spec.append(('s', LEAD))
        return flip(walk(spec))
    n = int(round(180.0 / FACET))
    if abs(n * FACET - 180.0) > 1e-9:
        raise ValueError(f'--facet={FACET:g} does not divide 180 a whole '
                         f'number of times; {n} facets would turn '
                         f'{n * FACET:g} degrees.')
    # The tails have to leave the arc along its TANGENT, or the first facet
    # turns by something that is not FACET and the panel that sits on it is
    # the wrong length. Attaching them at the arc's endpoints is not the same
    # thing as attaching them tangentially, and the first attempt here did the
    # former: it produced a 98mm panel on a coupon 78mm long.
    pts = [(RADIUS, TAIL)]                        # lead in, running -y
    for i in range(n + 1):                        # the turn, centred on origin
        a = -i * math.radians(FACET)              # (R,0) -> (0,-R) -> (-R,0)
        pts.append((RADIUS * math.cos(a), RADIUS * math.sin(a)))
    pts.append((-RADIUS, TAIL))                   # lead out, running +y
    return flip(pts)


def walls(poly):
    """(inner, outer) offset polylines, named by which one is actually inside.

    Asserted rather than assumed: the sign of the offset depends on which way
    round the centreline is written, and getting it backwards silently swaps
    every panel length in the cut list.
    """
    w = wall_off()
    a, b = offset(poly, w), offset(poly, -w)
    la = sum(seglen(p, q) for p, q in zip(a, a[1:]))
    lb = sum(seglen(p, q) for p, q in zip(b, b[1:]))
    return (a, b) if la < lb else (b, a)


def offset(poly, d):
    """The polyline offset sideways by d, mitred at every interior vertex.

    Mitred by intersecting the neighbouring offset LINES, not by moving each
    vertex along its bisector by d - those agree only for a right angle, and
    at 30 degrees the second one is wrong by 3.5%, which is exactly the
    quantity this file exists to keep track of.
    """
    segs = []
    for a, b in zip(poly, poly[1:]):
        ux, uy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ux, uy)
        nx, ny = -uy / L, ux / L                  # left normal
        segs.append(((a[0] + nx * d, a[1] + ny * d),
                     (b[0] + nx * d, b[1] + ny * d)))
    shut = (abs(poly[0][0] - poly[-1][0]) < 1e-9
            and abs(poly[0][1] - poly[-1][1]) < 1e-9)
    # A closed loop has a mitre at its seam like every other vertex. Without
    # this the two facets either side of the join come out over-long - 53.35mm
    # against 48.17 on the octagonal torus - and the ring does not close.
    first = meet(segs[-1], segs[0]) if shut else None
    out = [first or segs[0][0]]
    for a, b in zip(segs, segs[1:]):
        p = meet(a, b)
        out.append(p if p else a[1])
    out.append(first or segs[-1][1])
    return out


def meet(s, t):
    """Where two segments' infinite lines cross, or None if they are parallel."""
    (x1, y1), (x2, y2) = s
    (x3, y3), (x4, y4) = t
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(d) < 1e-12:
        return None
    a = x1 * y2 - y1 * x2
    b = x3 * y4 - y3 * x4
    return ((a * (x3 - x4) - (x1 - x2) * b) / d,
            (a * (y3 - y4) - (y1 - y2) * b) / d)


def seglen(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


def rot(p, ang, at=(0.0, 0.0)):
    c, s = math.cos(ang), math.sin(ang)
    x, y = p[0] - at[0], p[1] - at[1]
    return (at[0] + x * c - y * s, at[1] + x * s + y * c)


def path(pts, close=True):
    d = 'M ' + ' L '.join(f'{x:.3f},{y:.3f}' for x, y in pts)
    return d + (' Z' if close else '')


def teeth(L):
    """Where the tabs sit along a panel of length L, as offsets from centre.

    One tooth was enough at the coupon's 10-16mm panels and is a hinge at 90mm:
    a straight run held by a single 6mm tab in its middle pivots about it and
    the seam opens. Alternating tooth and gap of equal width, as Boxes.py does,
    so a panel gets as many as it has room for:

        n = floor((L - 2*SHOULDER + TOOTH) / (2*TOOTH))

    which is 1 up to 17.9mm, 3 at 34mm and 7 at 90mm, and still 1 for every
    panel on the coupon - so the coupon's cut file does not move.
    """
    n = max(1, int((L - 2 * SHOULDER + TOOTH) // (2 * TOOTH)))
    return [(i - (n - 1) / 2.0) * 2 * TOOTH for i in range(n)]


def panel(L, cs=None):
    """One wall panel, flat, centred on the origin, kerf already taken out.

    The laser removes BURN centred on the line, so every edge with material
    behind it is drawn BURN/2 outboard of where the material should end. Draw
    the true shape and the panel comes out BURN under in each dimension and
    the tab rattles.

    Shoulder to shoulder is the bore height exactly, because that is the gap
    between the cheeks' inner faces. The tab passes through its cheek and sits
    flush with the outside.
    """
    e = BURN / 2
    hl, ht = L / 2 + e, TOOTH / 2 + e
    hb, tip = BORE / 2 + e, BORE / 2 + THICK + e
    cs = teeth(L) if cs is None else cs
    out = [(-hl, -hb)]
    for c in cs:
        out += [(c - ht, -hb), (c - ht, -tip), (c + ht, -tip), (c + ht, -hb)]
    out += [(hl, -hb), (hl, hb)]
    for c in reversed(cs):
        out += [(c + ht, hb), (c + ht, tip), (c - ht, tip), (c - ht, hb)]
    out.append((-hl, hb))
    return out


def teeth_kept(part, portpoly):
    """This part's teeth, less any the port would cut into.

    A tooth and its mortice are one thing: drop it from the panel and you must
    drop it from the cheek, or a slot opens on nothing. That is why this is
    computed once, in build(), and read from the part by both.
    """
    cs = teeth(part['len'])
    if not portpoly:
        return cs
    # A panel whose ONLY tooth clashes would come out with no tab at all, held
    # by glue and its neighbours. That is a real cost and not one to take
    # silently, so it is refused here and the caller is told which panel.
    # On every shape in this file it is the two 20mm lead panels, whose single
    # tooth sits dead centre where the port is.
    mx, my = part['mid']
    ca, sa = math.cos(part['ang']), math.sin(part['ang'])
    out = []
    for c in cs:
        S = slot((mx + c * ca, my + c * sa), part['ang'])
        g = min(seg_gap(S[i], S[(i + 1) % len(S)],
                        portpoly[j], portpoly[(j + 1) % len(portpoly)])
                for i in range(len(S)) for j in range(len(portpoly)))
        if g >= MIN_FEATURE + BURN:
            out.append(c)
    if cs and not out:
        raise ValueError(
            f'the port takes the only tooth on {part["wall"]} panel '
            f'{part["n"]} ({part["len"]:.1f}mm), which would leave it with no '
            f'tab. A bore-square port passes within 0.16mm of a slot wherever '
            f'it sits, so the room has to come from somewhere: narrow the port '
            f'(7mm clears at the mouth by 1.66mm), or accept a glued panel.')
    return out


def seg_gap(p1, p2, q1, q2):
    """Closest approach of two segments."""
    def ps(q, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((q[0] - a[0]) * dx
                                                   + (q[1] - a[1]) * dy) / L2))
        return math.hypot(q[0] - (a[0] + u * dx), q[1] - (a[1] + u * dy))
    return min(ps(p1, q1, q2), ps(p2, q1, q2), ps(q1, p1, p2), ps(q2, p1, p2))


def slots_for(part):
    """Every mortice for one panel, placed on its segment.

    One per tooth, spaced along the segment exactly as the tabs are.
    """
    mx, my = part['mid']
    ca, sa = math.cos(part['ang']), math.sin(part['ang'])
    return [slot((mx + c * ca, my + c * sa), part['ang'])
            for c in part.get('teeth', teeth(part['len']))]


def slot(mid, ang):
    """The cheek's mortice for one tab: the hole is drawn BURN UNDER size.

    Opposite sign to the panel, and for the same reason - the kerf opens a
    hole and closes a part. Plus PLAY per side, which is bore_split.py's
    figure for the 10mm bore, taken out of the notch and never off the tab.
    """
    e = BURN / 2
    # width off the DRAWN tooth, depth off the MEASURED sheet: the tab's width
    # is a line on the panel, its thickness is the plywood itself
    hw = (TOOTH + 2 * play() - SLOT_TIGHTEN) / 2 - e
    hh = (SHEET - SLOT_TIGHTEN) / 2 - e
    box = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
    return [(mid[0] + p[0] * math.cos(ang) - p[1] * math.sin(ang),
             mid[1] + p[0] * math.sin(ang) + p[1] * math.cos(ang))
            for p in box]


def cheek(poly):
    """The flat face: a ribbon of the bore plus a flange each side.

    Closed by running out along one offset and back along the other, so it is
    one contour with no island - which for a U with open tails it genuinely
    is, and a hole would have been wrong.
    """
    d = cheek_off()
    a = offset(poly, d)
    b = offset(poly, -d)
    return a + b[::-1]


GLYPH = {'0': [[(0.5, 1), (0.85, 0.8), (0.85, 0.2), (0.5, 0), (0.15, 0.2), (0.15, 0.8), (0.5, 1)]], '1': [[(0.3, 0.78), (0.52, 1), (0.52, 0)], [(0.28, 0), (0.78, 0)]], '2': [[(0.1, 0.78), (0.3, 1), (0.7, 1), (0.9, 0.78), (0.9, 0.6), (0.1, 0), (0.9, 0)]], '3': [[(0.1, 1), (0.9, 1), (0.45, 0.55)], [(0.45, 0.55), (0.9, 0.55), (0.9, 0.16), (0.72, 0), (0.28, 0), (0.1, 0.16)]], '4': [[(0.7, 0), (0.7, 1), (0.12, 0.32), (0.92, 0.32)]], '5': [[(0.85, 1), (0.2, 1), (0.15, 0.55), (0.5, 0.62), (0.8, 0.5), (0.88, 0.28), (0.75, 0.06), (0.4, 0), (0.15, 0.12)]], '6': [[(0.82, 0.92), (0.55, 1), (0.25, 0.85), (0.15, 0.45), (0.15, 0.18), (0.35, 0), (0.62, 0), (0.85, 0.18), (0.85, 0.38), (0.62, 0.55), (0.3, 0.55), (0.15, 0.45)]], '7': [[(0.12, 1), (0.9, 1), (0.42, 0)]], '8': [[(0.5, 0.55), (0.22, 0.68), (0.22, 0.87), (0.5, 1), (0.78, 0.87), (0.78, 0.68), (0.5, 0.55), (0.18, 0.4), (0.18, 0.14), (0.5, 0), (0.82, 0.14), (0.82, 0.4), (0.5, 0.55)]], '9': [[(0.18, 0.08), (0.45, 0), (0.75, 0.15), (0.85, 0.55), (0.85, 0.82), (0.65, 1), (0.38, 1), (0.15, 0.82), (0.15, 0.62), (0.38, 0.45), (0.7, 0.45), (0.85, 0.55)]], 'A': [[(0.1, 0), (0.5, 1), (0.9, 0)], [(0.26, 0.4), (0.74, 0.4)]], 'B': [[(0.15, 0), (0.15, 1), (0.68, 1), (0.88, 0.83), (0.88, 0.68), (0.68, 0.55), (0.15, 0.55)], [(0.15, 0.55), (0.72, 0.55), (0.9, 0.4), (0.9, 0.16), (0.7, 0), (0.15, 0)]], 'C': [[(0.9, 0.8), (0.7, 1.0), (0.3, 1.0), (0.1, 0.8), (0.1, 0.2), (0.3, 0.0), (0.7, 0.0), (0.9, 0.2)]], 'D': [[(0.15, 0), (0.15, 1), (0.58, 1), (0.88, 0.74), (0.88, 0.26), (0.58, 0), (0.15, 0)]], 'E': [[(0.9, 1), (0.15, 1), (0.15, 0), (0.9, 0)], [(0.15, 0.5), (0.68, 0.5)]], 'F': [[(0.88, 1), (0.15, 1), (0.15, 0)], [(0.15, 0.52), (0.68, 0.52)]]}


def label(text, cx, cy, h, ang=0.0):
    """Hex glyphs centred on (cx, cy), with the baseline tick.

    The same table and the same tick as the bore sections, the bell rings and
    the torus pieces: 6 and 9 are one shape turned over, and the tick says
    which way up. Blue, so it engraves and never cuts.
    """
    w, gap = h * 0.62, h * 0.18
    total = len(text) * w + (len(text) - 1) * gap
    x, out = -total / 2, []
    for ch in text:
        for st in GLYPH[ch]:
            # the table's y runs up and SVG's runs down, so py has to be
            # flipped - without it every glyph is mirrored top to bottom and
            # a 2 comes out as something that is not a 2
            pts = [rot((x + px * w, h / 2 - py * h), ang) for px, py in st]
            out.append(path([(cx + p[0], cy + p[1]) for p in pts], close=False))
        x += w + gap
    tg, tl = h * 0.16, h * 0.22
    a = rot((total / 2 + tg, h / 2), ang)
    b = rot((total / 2 + tg + tl, h / 2), ang)
    out.append(path([(cx + a[0], cy + a[1]), (cx + b[0], cy + b[1])], close=False))
    return out


def build():
    """Every part, in millimetres, with the numbers each one carries."""
    c = centreline()
    inn, out = walls(c)
    parts, report = [], []
    # Numbered straight through in hex rather than I1/O1: the glyph table is
    # the one the bore sections and bell rings use, and adding I and O to it
    # would put I beside 1 and O beside 0 on a part you read at the bench.
    # The number identifies a panel, not its length. On the coupon the inner
    # panels run 12.05-14.14mm and the outer 15.86-19.01mm, so length tells
    # them apart; on the serpentine both walls run 19.14-90.00mm and it tells
    # you nothing. Either way the cheek slot carries the same number.
    seq = 0
    cl = c

    def turn_at(poly, k):
        """How far the wall turns at vertex k. A free end turns through 0."""
        if k <= 0 or k >= len(poly) - 1:
            return 0.0
        h1 = math.atan2(poly[k][1] - poly[k - 1][1], poly[k][0] - poly[k - 1][0])
        h2 = math.atan2(poly[k + 1][1] - poly[k][1], poly[k + 1][0] - poly[k][0])
        return abs((h2 - h1 + math.pi) % (2 * math.pi) - math.pi)

    for name, poly in (('inner', inn), ('outer', out)):
        for i, (a, b) in enumerate(zip(poly, poly[1:]), 1):
            # A panel end is a SQUARE cut - a laser cuts through the sheet and
            # cannot mitre it - and the offset polyline is the wall's
            # centreline, so two neighbours meeting at a mitre have THICK/2 of
            # ply either side of the point where their centrelines meet. On the
            # concave side that ply runs past the mitre by (THICK/2)tan(phi/2)
            # on each panel, and the two corners jam: they butt before either
            # panel is seated. Cut and found at the bench on the dspiral
            # halftest, where it is 0.81mm a joint over 14 joints; at 45
            # degrees it is 1.24mm. Nothing saw it, because the airway check
            # compares two offsets of one polyline and cannot fail, and no
            # check looked at the panels as solids.
            #
            # So trim each end back to where the concave corners just touch.
            # The gap that opens on the convex side is a V-groove closing to
            # nothing at the far face, not a hole: on the inner wall it is on
            # the airway side, on the outer wall it is outboard.
            e0 = THICK / 2 * math.tan(turn_at(poly, i - 1) / 2)
            e1 = THICK / 2 * math.tan(turn_at(poly, i) / 2)
            L = seglen(a, b) - e0 - e1
            if L < TOOTH + 2 * SHOULDER:
                raise ValueError(
                    f'{name} panel {i} is {L:.2f}mm and a {TOOTH:g}mm tooth '
                    f'with {SHOULDER:g}mm shoulders needs '
                    f'{TOOTH + 2 * SHOULDER:g}mm. Open the bend radius or '
                    f'coarsen --facet; the tooth does not scale with the bore.')
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            # the trim is not symmetric - the two ends turn through different
            # angles - so the midpoint moves with it, and the slots follow
            mid = ((a[0] + b[0]) / 2 + (e0 - e1) / 2 * math.cos(ang),
                   (a[1] + b[1]) / 2 + (e0 - e1) / 2 * math.sin(ang))
            # Away from the bore, measured rather than assumed: from the
            # centreline's own midpoint out to the wall's. A left normal with
            # a sign flip for the inner wall works only for one handedness,
            # and flipping y into SVG's coordinates reverses it - which put
            # 122 of 504 engraved points off the material.
            m0 = ((cl[i - 1][0] + cl[i][0]) / 2, (cl[i - 1][1] + cl[i][1]) / 2)
            dx, dy = mid[0] - m0[0], mid[1] - m0[1]
            dl = math.hypot(dx, dy) or 1.0
            nx, ny = dx / dl, dy / dl
            seq += 1
            tag = f'{seq:X}'
            parts.append({'kind': 'panel', 'wall': name, 'n': i, 'len': L,
                          'mid': mid, 'ang': ang, 'out': (nx, ny), 'tag': tag})
            report.append((tag, name, L))
    # The teeth are settled here, once, because a tooth and its mortice have to
    # agree and only this function has both the parts and the port.
    portpoly = port_hole(c) if PORT else None
    for q in parts:
        q['teeth'] = teeth_kept(q, portpoly)
    return c, inn, out, parts, report


def bbox(pts):
    xs = [q[0] for q in pts]
    ys = [q[1] for q in pts]
    return min(xs), min(ys), max(xs), max(ys)


def in_poly(poly, x, y):
    """Crossing count. Used to keep engraving out of the port."""
    n = len(poly) - 1
    ins = False
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[i + 1]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) / (y2 - y1) * (x2 - x1):
            ins = not ins
    return ins


def port_hole(cline):
    """A square opening through the cheek at the mouth, for a mouthpiece.

    The airway is bounded top and bottom by the cheeks, so the only way out of
    the plane is through one. This cuts a bore-square hole in the last BORE of
    the run and the bore turns 90 degrees into z there. Both cheeks carry it,
    because they are one part cut twice and that is worth more than saving a
    hole: you get a socket right through, plug the side you are not using.

    It is a slot, not an outline cut, so it is taken in the orange stage while
    the sheet still holds the cheek - the same reason the tab slots are.
    """
    a, b = cline[0], cline[1]
    ux, uy = b[0] - a[0], b[1] - a[1]
    m = math.hypot(ux, uy)
    ux, uy = ux / m, uy / m
    nx, ny = -uy, ux
    # The sign was wrong here and the comment beside it said so: a hole is
    # drawn UNDER size, because the kerf opens it. slot() subtracts BURN/2 and
    # this added it, so the port was drawn 10.13mm for a 10mm bore and cut
    # 10.26 -- a quarter of a millimetre over, with each edge 0.065mm nearer
    # whatever it sits beside. Found 2026-09-09 by flat-part-check, which had
    # never been able to read these files.
    ha = PORT_ACROSS / 2 - BURN / 2    # the hole is a hole: kerf goes under
    hl = PORT_ALONG / 2 - BURN / 2
    # a bore back from the tip, not half a bore: centred at BORE/2 the hole
    # ran to the very end of the cheek and two of its corners fell outside
    mid = (a[0] + ux * PORT_FROM_TIP, a[1] + uy * PORT_FROM_TIP)
    return [(mid[0] + ux * hl + nx * ha, mid[1] + uy * hl + ny * ha),
            (mid[0] + ux * hl - nx * ha, mid[1] + uy * hl - ny * ha),
            (mid[0] - ux * hl - nx * ha, mid[1] - uy * hl - ny * ha),
            (mid[0] - ux * hl + nx * ha, mid[1] - uy * hl + ny * ha),
            (mid[0] + ux * hl + nx * ha, mid[1] + uy * hl + ny * ha)]


def items_for(parts, cheekpoly, cline):
    """(the cheek, the panels), each as (outline, slots, labeller).

    ONE cheek, not two. The two are the same part, so the sheet that carries
    it is cut twice - which is only possible if nothing else shares that
    sheet. The packer used to fill the second cheek's sheet with panels, so
    cutting the first sheet twice left you thirteen panels short.

    The labeller is deferred because a label's position depends on where the
    part is finally placed, and placement is the packer's business.
    """
    out = []
    for k in range(1):
        def cheek_marks(dx, dy, _p=parts, _c=cline):
            m = []
            _dropped = []
            hole = [(q[0] + dx, q[1] + dy) for q in port_hole(_c)] if PORT else None
            for q in _p:
                mx, my = q['mid'][0] + dx, q['mid'][1] + dy
                ox, oy = q['out']
                off = THICK / 2 + 1.5
                # into the channel: with WEB at 2mm there is no flange to
                # write on, and the channel is the floor of the bore
                lx, ly = mx - ox * off, my - oy * off
                # The GLYPH has to clear the hole, not its anchor. Testing
                # the anchor alone worked only while the port was wider than
                # the label's offset: at 10mm across, an anchor 3.5mm off the
                # centreline sat inside and the slide fired. At 7mm the anchor
                # is 0.065mm clear of the edge and the glyph, 2mm tall, is not
                # -- so nothing slid and nine points were engraved into the
                # hole, which is what the gate then caught.
                # Approximate on purpose: it samples the label's box rather
                # than its strokes, so a sliver of overlap smaller than the
                # sample spacing could slip through. That is safe because it is
                # not the gate -- "no engraving lands in a slot" tests every
                # ink point that was actually drawn, and would catch it. This
                # only has to be good enough to decide where to put the label.
                def _fouls(px, py, h=2.0, n=1):
                    # label()'s own extent, and it is NOT symmetric: the glyphs
                    # span +-total/2 but the baseline tick runs on to
                    # total/2 + 0.38h past them. A +-h/2 box missed the tick,
                    # which is precisely what was being engraved into the port.
                    if hole is None:
                        return False
                    w, gap = h * 0.62, h * 0.18
                    total = n * w + (n - 1) * gap
                    lo, hi = -total / 2, total / 2 + h * 0.38
                    ca, sa = math.cos(q['ang']), math.sin(q['ang'])
                    for i in range(5):
                        u = lo + (hi - lo) * i / 4
                        for v in (-h / 2, 0.0, h / 2):
                            if in_poly(hole, px + u * ca - v * sa,
                                       py + u * sa + v * ca):
                                return True
                    return False
                if _fouls(lx, ly, n=len(q['tag'])):
                    # this one sits in the opening. Slide it along its own
                    # panel until it clears - the alternative, giving the port
                    # a bore of extra lead, moves the whole coil and was what
                    # made the cheek cross itself.
                    # Along the panel first, then back the other way: on a
                    # short panel -- the coupon's run 12 to 19mm -- a whole
                    # bore forward is off the end of it.
                    for d in (BORE, 2 * BORE, 3 * BORE,
                              -BORE, BORE / 2, -BORE / 2, -2 * BORE):
                        cx, cy = math.cos(q['ang']) * d, math.sin(q['ang']) * d
                        if not _fouls(lx + cx, ly + cy, n=len(q['tag'])):
                            lx, ly = lx + cx, ly + cy
                            break
                    else:
                        # Nowhere clear. An unnumbered slot beats a number
                        # engraved into a hole; the panel carries the same tag
                        # on its own sheet. Counted, not silent.
                        _dropped.append(q['tag'])
                        continue
                m += label(q['tag'], lx, ly, 2.0, q['ang'])
            # a little way ALONG the first segment, not at its start: the
            # band begins there and half the glyph hung off the end. A
            # quarter of the way in also clears panel 1's label, which sits
            # at the segment's midpoint offset across.
            a0, a1 = _c[0], _c[1]
            t = 0.22
            if PORT:
                # the port takes the mouth end of the lead, where the cheek's
                # own '0' used to sit; put it on the tail lead instead
                a0, a1 = _c[-1], _c[-2]
                t = 0.22
            gx = a0[0] + (a1[0] - a0[0]) * t + dx
            gy = a0[1] + (a1[1] - a0[1]) * t + dy
            m += label('0', gx, gy, 2.6,
                       math.atan2(a1[1] - a0[1], a1[0] - a0[0]))
            if _dropped:
                print(f'  note: {len(_dropped)} cheek label(s) left off, '
                      f'{", ".join(_dropped)} -- no clear spot beside the port. '
                      f'The panels carry the same tags.')
            return m
        cheek_slots = [sl for q in parts for sl in slots_for(q)]
        if PORT:
            cheek_slots.append(port_hole(cline))
        out.append({'outline': cheekpoly,
                    'slots': cheek_slots,
                    'marks': cheek_marks})
    pan = []
    for q in parts:
        w = q['len'] + BURN
        h2 = (BORE + 2 * THICK + BURN) / 2
        poly = [(px + w / 2, py + h2) for px, py in panel(q['len'], q.get('teeth'))]

        def panel_marks(dx, dy, _t=q['tag'], _w=w, _h=h2):
            return label(_t, _w / 2 + dx, _h + dy, 3.2)
        pan.append({'outline': poly, 'slots': [], 'marks': panel_marks})
    return out, pan


MARGIN_S = 10.0      # sheet margin: the packer's and the reported size's


def pack(items, margin=MARGIN_S, gap=4.0):
    """Row-wrap into sheets, closing a sheet when the next row would overflow.

    Packs into BED minus a margin all round, not into the bed. Filling to the
    edge gave a sheet 600 x 307 on a 600 x 308 bed, which passes a fits-the-bed
    check and cannot be positioned on a real machine.

    A part larger than the usable area is a refusal, not a smaller sheet: it
    cannot be cut at all and saying so beats writing a file that looks fine.
    """
    use_w, use_h = BED_W - 2 * margin, BED_H - 2 * margin
    sheets, cur = [], []
    x, y, rowh = margin, margin, 0.0
    for it in items:
        x0, y0, x1, y1 = bbox(it['outline'])
        w, h = x1 - x0, y1 - y0
        if w > use_w or h > use_h:
            raise ValueError(
                f'a part is {w:.0f} x {h:.0f}mm and the usable area is '
                f'{use_w:.0f} x {use_h:.0f} on a {BED_W:g} x {BED_H:g} bed. '
                f'Nothing written. Shorten the bore, or add lobes so each '
                f'half-circle is smaller.')
        if x > margin and x + w > margin + use_w:
            if y + rowh + gap + h > margin + use_h:
                sheets.append(cur)
                cur, x, y, rowh = [], margin, margin, 0.0
            else:
                x, y, rowh = margin, y + rowh + gap, 0.0
        cur.append((it, x - x0, y - y0))
        x += w + gap
        rowh = max(rowh, h)
    if cur:
        sheets.append(cur)
    return sheets


def sheet(parts, cheekpoly, cline, path_out, write=True):
    """Write the cut files: the cheek on its own sheet, the panels on theirs.

    **The cheek's sheet is cut twice and nothing else is on it.** The two
    cheeks are the same part, so one file loaded once and run twice is the
    whole job - but only if the sheet holds nothing that should be cut once.
    The packer used to fill the second cheek's sheet with panels, which made
    that impossible without counting parts by hand.

    Colour is the cut order, shared with every repository here: blue engraves,
    then orange, then black. The slots are orange because they are inside the
    cheek and have to be cut while the sheet still holds it; black frees the
    parts.
    """
    cheeks, panels = items_for(parts, cheekpoly, cline)
    over = 100 * (1 / math.cos(math.radians(FACET) / 2) - 1)
    stem, ext = os.path.splitext(path_out)
    ink, cut_slots, written = [], [], []

    def write_sheet(placed, path_here, note, n, of):
        marks, holes, cuts = [], [], []
        for it, dx, dy in placed:
            here = [(q[0] + dx, q[1] + dy) for q in it['outline']]
            cuts.append(path(here))
            for sl in it['slots']:
                moved = [(q[0] + dx, q[1] + dy) for q in sl]
                # tagged with the file, because two sheets are two files and
                # their coordinates have nothing to do with each other
                cut_slots.append((moved, path_here))
                holes.append(path(moved))
            for d in it['marks'](dx, dy):
                marks.append(d)
                for tok in d.replace('M ', '').replace('Z', '').split(' L '):
                    a, b = tok.strip().split(',')
                    ink.append((float(a), float(b), here, path_here))
        W = max(bbox(it['outline'])[2] + dx for it, dx, dy in placed) + MARGIN_S
        H = max(bbox(it['outline'])[3] + dy for it, dx, dy in placed) + MARGIN_S

        def grp(ds, col, name):
            if not ds:
                return ''
            return (f'  <g id="{name}" fill="none" stroke="{col}" '
                    f'stroke-width="0.2">\n'
                    + '\n'.join(f'    <path d="{d}"/>' for d in ds)
                    + '\n  </g>\n')

        of_txt = f', sheet {n} of {of}' if of > 1 else ''
        body = (
            f'<?xml version="1.0" encoding="utf-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{W:.2f}mm" '
            f'height="{H:.2f}mm" viewBox="0 0 {W:.2f} {H:.2f}">\n'
            f'<title>Ribbon bore, {SHAPE} - {note}{of_txt} - {BORE:g}mm square '
            f'bore, {FACET:g} degree facets</title>\n'
            f'<desc>1 user unit = 1mm. {note}. A duct of constant '
            f'{BORE:g} x {BORE:g}mm section swept along a planar curve; the '
            f'two cheeks are the same part and both go on the same way up. '
            f'{len(parts)} wall panels in all, numbered along the flow. The '
            f'airway is exact along every facet and {over:.1f}% over at each '
            f'mitre. {THICK:g}mm ply, slots cut for a {SHEET:g}mm sheet at '
            f'{BURN:g}mm kerf, {play():g}mm play per '
            f'side taken out of the slot and never off the tab. blue #0000ff '
            f'engraves, orange #ff8000 cuts the slots first, black #000000 '
            f'frees the parts.</desc>\n'
            + grp(marks, MARK, 'numbers') + grp(holes, INNER, 'slots')
            + grp(cuts, CUT, 'outlines') + '</svg>\n')
        if write:
            open(path_here, 'w').write(body)
        written.append((os.path.basename(path_here), W, H, len(placed), note))

    for gname, items, note in (
            ('cheek-x2', cheeks, 'the cheek - CUT THIS SHEET TWICE'),
            ('panels', panels, 'the wall panels')):
        sheets = pack(items)
        for n, placed in enumerate(sheets, 1):
            tail = f'-sheet{n}' if len(sheets) > 1 else ''
            write_sheet(placed, f'{stem}-{gname}{tail}-cut-files{ext}', note,
                        n, len(sheets))
    return written, ink, cut_slots


def flippable(cheekpoly, parts):
    """Can a cheek be turned over and still meet every tab?

    Only if the cheek - outline and slots together - is congruent to its own
    mirror image. Reflection alone is not the test: the part may also be
    turned in its own plane, so a reflected copy is tried at every angle.

    Matched as a BIJECTION between nearest points, not by zipping two sorted
    lists. Sorting is unstable under a perturbation of a few hundredths: two
    nearly equal points swap order and every pair after them is compared with
    the wrong partner, which turned a 0.025mm difference into 20.7mm of
    apparent error and answered this question backwards.

    Neither answer is a fault, which is why this is reported and not checked.
    The build instruction is the same either way - both cheeks the same way
    up - because a flipped cheek carries its numbers mirrored and facing into
    the bore.
    """
    pts = list(cheekpoly) + [q for p in parts for sl in slots_for(p) for q in sl]

    def shift(ps):
        x0 = min(q[0] for q in ps)
        y0 = min(q[1] for q in ps)
        return [(q[0] - x0, q[1] - y0) for q in ps]

    base = shift(pts)
    for k in range(720):
        a = math.radians(k * 0.5)
        c, sn = math.cos(a), math.sin(a)
        t = shift([(x * c + y * sn, x * sn - y * c) for x, y in pts])
        if len(t) != len(base):
            continue
        left, worst = list(range(len(t))), 0.0
        for u in base:
            j = min(left, key=lambda i: (t[i][0] - u[0]) ** 2
                                      + (t[i][1] - u[1]) ** 2)
            d = math.hypot(t[j][0] - u[0], t[j][1] - u[1])
            if d > worst:
                worst = d
            if worst > 0.02:
                break
            left.remove(j)
        if worst <= 0.02 and not left:
            return k * 0.5
    return None


def inside(poly, x, y):
    n, c = len(poly), False
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[i - 1]
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
            c = not c
    return c


def checks(c, inn, out, parts, cheekpoly, written, ink, cut_slots):
    """What has to be true, said out loud with the number that makes it true.

    A check that measured nothing would print the same clean run as a check
    that measured everything, so each one reports its count.
    """
    res = []

    def note(ok, what, detail):
        res.append((ok, what, detail))

    # --- the whole point: the section is the bore, everywhere along a facet
    worst, n = 0.0, 0
    for (a, b), (p, q) in zip(zip(inn, inn[1:]), zip(out, out[1:])):
        for t in (0.15, 0.35, 0.5, 0.65, 0.85):
            m = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            ux, uy = q[0] - p[0], q[1] - p[1]
            L2 = ux * ux + uy * uy
            s = ((m[0] - p[0]) * ux + (m[1] - p[1]) * uy) / L2
            f = (p[0] + ux * s, p[1] + uy * s)
            # centreline to centreline MINUS one wall thickness, because
            # half a wall stands inboard on each side. Measuring the two
            # offset lines and calling the answer the bore is how a 7mm
            # airway passed this check calling itself 10mm.
            air = math.hypot(f[0] - m[0], f[1] - m[1]) - THICK
            worst = max(worst, abs(air - BORE))
            n += 1
    note(n > 0 and worst < 1e-9, 'the airway is the bore along every facet',
         f'{n} stations, worst {worst:.2e}mm from {BORE:g} '
         f'(wall face to wall face)')

    # --- every slot has to be in the cheek, or a tab has nothing to enter
    allslots = [sl for p in parts for sl in slots_for(p)]
    if PORT:
        allslots = allslots + [port_hole(c)]
    off = sum(1 for sl in allslots for pt in sl
              if not inside(cheekpoly, *pt))
    note(off == 0 and allslots, 'every slot corner is inside its cheek',
         f'{4 * len(allslots)} corners on {len(allslots)} slots, {off} outside')

    # --- and no two slots may run into each other
    # Separating axis, not centre distance: two slots 8mm apart can still
    # overlap if they are nearly parallel and 6mm long, and a centre-distance
    # test would call that clear.
    def apart(A, B):
        for R in (A, B):
            for i in range(len(R)):
                ax, ay = R[(i + 1) % len(R)][0] - R[i][0], R[(i + 1) % len(R)][1] - R[i][1]
                px, py = -ay, ax
                pa = [q[0] * px + q[1] * py for q in A]
                pb = [q[0] * px + q[1] * py for q in B]
                if max(pa) <= min(pb) or max(pb) <= min(pa):
                    return True
        return False
    boxes = allslots
    pairs = [(i, j) for i in range(len(boxes)) for j in range(i + 1, len(boxes))]
    bad = sum(1 for i, j in pairs if not apart(boxes[i], boxes[j]))
    note(bad == 0, 'no two slots overlap',
         f'{len(pairs)} pairs, {bad} overlapping')

    # --- and OVERLAP is the wrong question. Two holes 0.03mm apart do not
    # overlap and are still one hole once the laser has been through: the kerf
    # is 0.13mm and takes half from each edge. This check passed every ported
    # cheek in the project while the port sat 0.029mm from its neighbouring
    # slot, which flat-part-check found the moment it could read the files.
    # Ask for material, not for absence of intersection.
    def _sd(p1, p2, q1, q2):
        def ps(q, a, b):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L2 = dx * dx + dy * dy
            u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((q[0] - a[0]) * dx
                                                       + (q[1] - a[1]) * dy) / L2))
            return math.hypot(q[0] - (a[0] + u * dx), q[1] - (a[1] + u * dy))
        return min(ps(p1, q1, q2), ps(p2, q1, q2), ps(q1, p1, p2), ps(q2, p1, p2))
    tight, worst = 0, float('inf')
    for i, j in pairs:
        A, B = allslots[i], allslots[j]
        g = min(_sd(A[a], A[(a + 1) % len(A)], B[b], B[(b + 1) % len(B)])
                for a in range(len(A)) for b in range(len(B)))
        worst = min(worst, g)
        if g - BURN < MIN_FEATURE:
            tight += 1
    note(tight == 0, 'the ply between two holes survives the kerf',
         f'narrowest {worst:.3f}mm drawn, {worst - BURN:.3f}mm left after a '
         f'{BURN:g}mm kerf, against {MIN_FEATURE:g}mm needed')

    # --- the panels have to fit round the bend as SOLIDS, not as lines
    # The airway check compares two offsets of one polyline and cannot fail;
    # it passes a hairpin tighter than its own wall. Nothing here looked at a
    # panel as a body until the dspiral halftest was cut and its corners
    # jammed. In plan a panel is a THICK-wide rectangle on its own segment,
    # and two neighbours must not share any of it.
    def plan_rect(q):
        hl, ht = q['len'] / 2, THICK / 2
        ca, sa = math.cos(q['ang']), math.sin(q['ang'])
        mx, my = q['mid']
        return [(mx + u * hl * ca - v * ht * sa, my + u * hl * sa + v * ht * ca)
                for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1))]

    def overlap(P, Q):
        """separating-axis, on the four edge normals of two convex quads"""
        for R in (P, Q):
            for k in range(4):
                ex = R[(k + 1) % 4][0] - R[k][0]
                ey = R[(k + 1) % 4][1] - R[k][1]
                nx, ny = -ey, ex
                a = [nx * x + ny * y for x, y in P]
                b = [nx * x + ny * y for x, y in Q]
                if min(a) >= max(b) - 1e-7 or min(b) >= max(a) - 1e-7:
                    return False
        return True

    rects = {}
    for q in parts:
        rects.setdefault(q['wall'], []).append(plan_rect(q))
    npair = jam = 0
    for rs in rects.values():
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                npair += 1
                if overlap(rs[i], rs[j]):
                    jam += 1
    note(jam == 0, 'no two wall panels share plan area',
         f'{npair} pairs on {len(rects)} walls, {jam} jamming')

    # --- and the same question asked of the walls as SOLIDS, which can fail
    # The check above compares two offsets of ONE polyline. They are parallel
    # to each facet at a fixed separation by construction, so it returns the
    # bore whatever the centreline does: it passes a hairpin tighter than its
    # own wall and a zigzag that reverses at every vertex. It is worth keeping
    # - it is the arithmetic of the section - but it is not evidence.
    #
    # This one measures the gap between the two walls as bodies, over every
    # inner-panel-to-outer-panel pair, and the narrowest is the airway at its
    # narrowest. A bore that pinches anywhere fails here.
    def seg_dist(p1, p2, q1, q2):
        def pt_seg(p, a, b):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L2 = dx * dx + dy * dy
            u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx
                                                       + (p[1] - a[1]) * dy) / L2))
            return math.hypot(p[0] - (a[0] + u * dx), p[1] - (a[1] + u * dy))
        return min(pt_seg(p1, q1, q2), pt_seg(p2, q1, q2),
                   pt_seg(q1, p1, p2), pt_seg(q2, p1, p2))

    def rect_dist(P, Q):
        if overlap(P, Q):
            return 0.0
        return min(seg_dist(P[i], P[(i + 1) % 4], Q[j], Q[(j + 1) % 4])
                   for i in range(4) for j in range(4))

    # Only against its NEIGHBOURS along the run. Comparing every inner panel
    # to every outer one measures the web between a coil's passes as well as
    # the airway, and calls the narrower of the two a pinched bore: it failed
    # the shipped spiral at 8.34mm on two panels eight facets apart, at radius
    # 31.8 and 11.9 from the coil centre - different turns. Pass-to-pass
    # collision is the cheek self-crossing check's job. Three facets either
    # side reaches every mitre and no further; at that window all seven shapes
    # measure the bore exactly and a hairpin tighter than its own wall comes
    # out at 3mm.
    NEAR = 3
    ins = [plan_rect(q) for q in parts if q['wall'] == 'inner']
    ous = [plan_rect(q) for q in parts if q['wall'] == 'outer']
    gap, npr = float('inf'), 0
    for i, A in enumerate(ins):
        for j in range(max(0, i - NEAR), min(len(ous), i + NEAR + 1)):
            gap = min(gap, rect_dist(A, ous[j])); npr += 1
    note(npr > 0 and gap >= BORE - 1e-6, 'the two walls stand a bore apart',
         f'{npr} neighbouring panel pairs, narrowest gap {gap:.4f}mm '
         f'against {BORE:g}mm')

    # --- the tooth does not scale, so short panels are the failure mode
    short = min(p['len'] for p in parts)
    note(short >= TOOTH + 2 * SHOULDER, 'the shortest panel still holds a tooth',
         f'{short:.2f}mm against {TOOTH + 2 * SHOULDER:g}mm needed')

    off = sum(1 for x, y, owner, _ in ink if not inside(owner, x, y))
    note(off == 0 and len(ink) > 0, 'every engraved point is on its own part',
         f'{len(ink)} points, {off} off the material')

    # a number engraved over a slot is engraved into a hole, and what it
    # actually marks is the edge of the panel standing in it
    over = sum(1 for x, y, _, f in ink
               if any(inside(sl, x, y) for sl, f2 in cut_slots if f2 == f))
    note(over == 0 and len(cut_slots) == len(allslots),
         'no engraving lands in a slot',
         f'{len(ink)} points against {len(cut_slots)} slots, {over} inside one')

    # The cheek is one piece and it must not cross itself. Every other check
    # here asks about slots, panels or engraving, and all of them passed on a
    # cheek whose outline ran straight through a later loop of the spiral -
    # the author found it by looking at the file. A closed band can be entirely
    # self-consistent slot by slot and still be an impossible piece of wood.
    def edges_cross(a, b, c, d):
        d1 = (b[0] - a[0], b[1] - a[1])
        d2 = (d[0] - c[0], d[1] - c[1])
        den = d1[0] * d2[1] - d1[1] * d2[0]
        if abs(den) < 1e-12:
            return False
        u = ((c[0] - a[0]) * d2[1] - (c[1] - a[1]) * d2[0]) / den
        v = ((c[0] - a[0]) * d1[1] - (c[1] - a[1]) * d1[0]) / den
        return 1e-9 < u < 1 - 1e-9 and 1e-9 < v < 1 - 1e-9

    ring = cheekpoly
    m = len(ring) - 1
    bad_edges = [(i, j) for i in range(m) for j in range(i + 2, m)
                 if not (i == 0 and j == m - 1)
                 and edges_cross(ring[i], ring[i + 1], ring[j], ring[j + 1])]
    note(not bad_edges, 'the cheek outline does not cross itself',
         f'{m} edges, {len(bad_edges)} crossing'
         + (f', first at {bad_edges[0]}' if bad_edges else ''))

    # Measured off the drawing, not asserted about the constant. This read
    # "WEB >= 1.5" and printed "2mm of ply beside a 3mm slot" as though it had
    # looked: it could only ever fail if someone edited WEB, and never if the
    # geometry pinched the web at a tight mitre. The number it prints is the
    # same 2.05mm on every shape here - WEB plus half the kerf - but now it is
    # the narrowest one actually in the cheek.
    def pt_seg(q, a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L2 = dx * dx + dy * dy
        u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((q[0] - a[0]) * dx
                                                   + (q[1] - a[1]) * dy) / L2))
        return math.hypot(q[0] - (a[0] + u * dx), q[1] - (a[1] + u * dy))
    web = min((pt_seg(q, ring[i], ring[i + 1])
               for sl in allslots for q in sl for i in range(len(ring) - 1)),
              default=0.0)
    note(web >= 1.5, 'the web outboard of a slot is cuttable',
         f'narrowest slot to rim {web:.3f}mm against 1.5mm needed, '
         f'band {band():g}mm wide')

    big = [n for n, w, h, _, _ in written if w > BED_W or h > BED_H]
    note(not big and len(written) > 0, 'every sheet fits the P2S bed',
         f'{len(written)} sheet(s), largest '
         f'{max(w for _, w, _, _, _ in written):.0f} x '
         f'{max(h for _, _, h, _, _ in written):.0f}mm against '
         f'{BED_W:g} x {BED_H:g}')
    return res


def main(write=True):
    c, inn, out, parts, report = build()
    over = 100 * (1 / math.cos(math.radians(FACET) / 2) - 1)
    R = (WAVE_TROUGH_R if SHAPE == 'wave'
         else SPIRAL_RI if SHAPE == 'spiral'
         else DS_CROSS_R if SHAPE == 'dspiral'
         else VOL_CROSS_R if SHAPE == 'volute'
         else LOBE_R if SHAPE in ('serpentine', 'opposed') else RADIUS)
    what = (f'a wave: a trough of R{WAVE_TROUGH_R:g} and a crest of '
            f'R{WAVE_CREST_R:g}, level at both ends'
            if SHAPE == 'wave' else
            f'a flat coil, {SPIRAL_FACETS} facets, R{SPIRAL_RI:g} at the '
            f'centre out to R{SPIRAL_RO:g} at the rim'
            if SHAPE == 'spiral' else
            f'two arms half a turn apart on an Archimedean spiral, '
            f'{DS_FACETS} facets each from R{DS_R0:g}, rising {DS_PITCH:g}mm '
            f'a turn, crossed at the centre by a straight off R{DS_CROSS_R:g}'
            if SHAPE == 'dspiral' else
            f'a double volute: a chain of {VOL_SEMIS} semicircles an arm '
            f'from R{VOL_R0:g} stepping {VOL_STEP:g}mm a turn, the return arm '
            f'interleaved half a turn away, joined at the eye by an arc off '
            f'R{VOL_CROSS_R:g}'
            if SHAPE == 'volute' else
            f'{LOBES} half-circles of R{R:g} joined by {RISE:g}mm straights'
            + (', then a quarter turn to bring the ends opposed'
               if SHAPE == 'opposed' else '')
            if SHAPE in ('serpentine', 'opposed')
            else f'one 180 degree bend of R{R:g}')
    print(f'ribbon bore, {SHAPE}   {BORE:g}mm square, {FACET:g} degree facets')
    print(f'  {what}')
    print(f'  centreline {sum(seglen(a, b) for a, b in zip(c, c[1:])):.1f}mm, '
          f'section {BORE:g} x {BORE:g} = {BORE * BORE:.0f}mm2, '
          f'+{over:.1f}% at each mitre')
    known = round(BORE, 3) in PLAY_BY_BORE
    print(f'  bend R/bore = {R / BORE:.1f}; the inner wall runs at '
          f'R{R - BORE / 2:g}')
    print(f'  play {play():g}mm per side'
          + ('' if known else f'  (the {BORE:g}mm bore is not in PLAY_BY_BORE; '
                              f'this is the small-joint default. Measure it '
                              f'and add a row.)') + '\n')
    print('  part   wall     length     tooth   shoulders')
    for tag, wall, L in report:
        print(f'  {tag:<5}  {wall:<7}  {L:>6.2f}mm   {TOOTH:g}mm    '
              f'{(L - TOOTH) / 2:>5.2f}mm')
    cheekpoly = cheek(c)
    # --out exists because a failing run deletes its output, and a copy of
    # this script tried out in the same folder therefore deleted the real cut
    # file. A trial writes somewhere else or it does not write at all.
    L = sum(seglen(a, b) for a, b in zip(c, c[1:]))
    # the group goes before -cut-files, not after: every sheet in this
    # project ends -cut-files.svg and a reader sorts on the tail
    if SHAPE == 'wave':
        stem = (f'ribbon-wave-bore{BORE:g}-{FACET:g}deg-'
                f'{WAVE_LOBE_ARCS}arc-{L:.0f}mm.svg')
    elif SHAPE == 'spiral':
        stem = (f'ribbon-spiral-bore{BORE:g}-{FACET:g}deg-'
                f'R{SPIRAL_RI:.0f}to{SPIRAL_RO:.0f}-{L:.0f}mm.svg')
    elif SHAPE == 'dspiral':
        stem = (f'ribbon-dspiral-bore{BORE:g}-{FACET:g}deg-'
                f'R{DS_R0:.0f}-pitch{DS_PITCH:.0f}-{L:.0f}mm.svg')
    elif SHAPE == 'volute':
        stem = (f'ribbon-volute-bore{BORE:g}-{FACET:g}deg-'
                f'R{VOL_R0:.0f}-step{VOL_STEP:.0f}-{L:.0f}mm.svg')
    elif SHAPE in ('serpentine', 'opposed'):
        stem = (f'ribbon-{SHAPE}-bore{BORE:g}-{FACET:g}deg-{LOBES}lobes'
                f'-R{LOBE_R:.0f}-{L:.0f}mm.svg')
    else:
        stem = (f'ribbon-coupon-bore{BORE:g}-{FACET:g}deg'
                f'-R{RADIUS:g}-180turn.svg')
    if PORT:
        # a ported design is a different part from its unported twin - same
        # coil, one hole, and radii solved separately - so it gets its own
        # name rather than overwriting the one without
        stem = stem[:-4] + '-ported.svg'
        # --out replaces the stem outright, so it also replaces the marker
        # that keeps a ported design off its unported twin. A --port run with
        # --out therefore used to write the ported sheets over the plain ones
        # under the plain name, and nothing said so: same part count, same
        # sheet sizes, one extra contour in a 529-path file. Refuse instead.
        if OUT and 'ported' not in os.path.basename(OUT):
            raise ValueError(
                f'--port with --out={OUT} would write the ported sheets under '
                f'a name that does not say so, over the unported twin. Put '
                f'"ported" in the --out name.')
    out_path = OUT or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), stem)
    written, ink, cut_slots = sheet(parts, cheekpoly, c, out_path, write)
    turn = flippable(cheekpoly, parts)
    print(f'\n  the two cheeks are identical, and go on the same way up.')
    print('  ' + (f'  (geometrically one could be flipped and turned '
                  f'{turn:g} deg, but its numbers would then read mirrored '
                  f'and face into the bore)' if turn is not None
                  else '  (a flipped cheek meets no tab at any angle)'))
    print(f'\n  {len(parts)} wall panels + 2 cheeks = {len(parts) + 2} parts, '
          f'{len(written)} sheet{"s" if len(written) > 1 else ""}')
    for name, w, h, k, note in written:
        print(f'    {name:<62}{k:>3} parts  {w:.0f} x {h:.0f}mm')
    bad = 0
    print()
    for ok, what, detail in checks(c, inn, out, parts, cheekpoly,
                                   written, ink, cut_slots):
        print(f'  {"pass" if ok else "FAIL"}  {what:<44} {detail}')
        bad += not ok
    if write and not bad:
        print(f'\n  wrote {len(written)} file(s)')
    elif bad:
        if write:
            for name, _, _, _, _ in written:
                f = os.path.join(os.path.dirname(os.path.abspath(out_path)), name)
                if os.path.exists(f):
                    os.remove(f)
        print(f'\n  {bad} check(s) failed. Nothing written.')
    return 1 if bad else 0


if __name__ == '__main__':
    # a geometry that cannot be built is an answer, not a crash
    a = sys.argv[1:]
    for flag, cast in (('out', str), ('shape', str), ('bore', float),
                       ('facet', float), ('radius', float), ('lobes', int),
                       ('lobe-r', float), ('rise', float), ('lead', float),
                       ('web', float), ('wave-rise', float),
                       ('wave-trough-r', float), ('wave-crest-r', float),
                       ('wave-lead-r', float), ('spiral-facets', int),
                       ('spiral-ri', float), ('spiral-ro', float),
                       ('ds-pitch', float), ('ds-r0', float),
                       ('ds-facets', int), ('ds-cross-r', float),
                       ('vol-r0', float), ('vol-step', float),
                       ('vol-semis', int), ('vol-cross-r', float),
                       ('sheet', float), ('kerf', float)):
        hit = [x for x in a if x.startswith(f'--{flag}=')]
        if not hit:
            continue
        v = cast(hit[0].split('=', 1)[1])
        {'out': 'OUT', 'shape': 'SHAPE', 'bore': 'BORE', 'facet': 'FACET',
         'radius': 'RADIUS', 'lobes': 'LOBES', 'lobe-r': 'LOBE_R',
         'rise': 'RISE', 'lead': 'LEAD', 'web': 'WEB',
         'wave-rise': 'WAVE_RISE', 'wave-trough-r': 'WAVE_TROUGH_R',
         'wave-crest-r': 'WAVE_CREST_R', 'wave-lead-r': 'WAVE_LEAD_R',
         'spiral-facets': 'SPIRAL_FACETS', 'spiral-ri': 'SPIRAL_RI',
         'spiral-ro': 'SPIRAL_RO',
         'ds-pitch': 'DS_PITCH', 'ds-r0': 'DS_R0',
         'ds-facets': 'DS_FACETS', 'ds-cross-r': 'DS_CROSS_R',
         'vol-r0': 'VOL_R0', 'vol-step': 'VOL_STEP',
         'vol-semis': 'VOL_SEMIS', 'vol-cross-r': 'VOL_CROSS_R',
         'sheet': 'SHEET', 'kerf': 'BURN'}[flag]
        globals()[{'out': 'OUT', 'shape': 'SHAPE', 'bore': 'BORE',
                   'facet': 'FACET', 'radius': 'RADIUS', 'lobes': 'LOBES',
                   'lobe-r': 'LOBE_R', 'rise': 'RISE', 'lead': 'LEAD',
                   'web': 'WEB', 'wave-rise': 'WAVE_RISE',
                   'wave-trough-r': 'WAVE_TROUGH_R',
                   'wave-crest-r': 'WAVE_CREST_R',
                   'wave-lead-r': 'WAVE_LEAD_R',
                   'spiral-facets': 'SPIRAL_FACETS',
                   'spiral-ri': 'SPIRAL_RI',
                   'spiral-ro': 'SPIRAL_RO',
                   'ds-pitch': 'DS_PITCH', 'ds-r0': 'DS_R0',
                   'ds-facets': 'DS_FACETS',
                   'ds-cross-r': 'DS_CROSS_R',
                   'vol-r0': 'VOL_R0', 'vol-step': 'VOL_STEP',
                   'vol-semis': 'VOL_SEMIS',
                   'vol-cross-r': 'VOL_CROSS_R',
                   'sheet': 'SHEET', 'kerf': 'BURN'}[flag]] = v
    # per-shape defaults, and only where the caller has not spoken
    if SHAPE == 'opposed':
        if not any(x.startswith('--lobe-r=') for x in a):
            LOBE_R = OPPOSED_R
        if not any(x.startswith('--rise=') for x in a):
            RISE = OPPOSED_RISE
    # FACET defaults to the coupon's 30, and the wave and the spirals are
    # 45 degree designs. A bare --shape=wave therefore built arcs that do not
    # close and reported six check failures, not one of which said "facet";
    # a bare --shape=spiral refused, because 17 facets turn 480 degrees at 30
    # and the ends only come out opposed on a whole number of turns. Both
    # reproduce their shipped design at 45, so 45 is what they ask for when
    # the caller has not spoken.
    if SHAPE in FACET_BY_SHAPE and not any(
            x.startswith('--facet=') for x in a):
        FACET = FACET_BY_SHAPE[SHAPE]
    PORT = '--port' in a
    DS_HALF = '--ds-half' in a
    try:
        sys.exit(main(write='--no-write' not in a))
    except ValueError as e:
        print(f'error: {e}')
        sys.exit(1)
