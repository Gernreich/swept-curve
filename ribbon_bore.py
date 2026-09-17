#!/usr/bin/env python3
"""A bore of constant cross-section swept along a planar curve.

    python3 ribbon_bore.py                      # the 10mm 30-degree double spiral
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
R 25 is therefore the floor for a 10mm bore at 30 degree facets, whatever the
shape wants to do.
"""
import math
import os
import sys

BORE = 10.0          # the square section, mm
FACET = 30.0         # degrees of turn per wall panel
RADIUS = 30.0        # bend radius of the centreline; see the minimum below
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
#
# 3.0 from 2026-09-13, on the author's instruction, for stock that measures it.
# The 2.94 above was one caliper reading of one batch and it is kept in the
# prose because the reasoning is what matters, not the number: SHEET is the
# MATERIAL and belongs only in the depth of the hole it passes through. Moving
# it 2.94 -> 3.0 deepens every mortice by 0.06 and changes nothing else.
#
# IT ALSO MAKES EVERY SHEET IN THIS REPO CUT BEFORE THIS DATE STALE. Those were
# drawn for 2.94mm ply; a 3.0mm tab will not enter their slots. Redraw the
# design you are cutting rather than reaching for a file already on disk, and
# pass --sheet=2.94 if you go back to the old stock.
SHEET = 3.0
WEB = 2.0            # material left outboard of a slot; the cheek's thin part
# --narrow: put the cheek's edge ON the mortice's outboard edge, so there is no
# web at all and the band is only as wide as the duct. It was done by hand in
# Inkscape first, on the dspiral halftest, by dragging the rim onto the slot
# corners; this is that edit as an option, and it lands in the same place
# because both take their figure from the same slot_half().
#
# It is NOT --web=0. WEB leaves THICK/2 outboard of the wall's CENTRELINE,
# which is the wall's true face at 8.0mm, while the drawn mortice ends at
# 7.905mm - the face less half the kerf, because the hole is drawn BURN under
# size. --web=0 therefore leaves a 0.095mm rib that no laser can cut, and the
# hand edit did not leave one. --narrow follows the mortice instead, so it
# tracks --kerf and --sheet rather than restating a number they set.
#
# What it costs, and it is not small: the mortice loses its outboard face. A
# tab is then held across its thickness on one side only, by the cheek's inner
# lip and by glue. Nothing here decides whether that is a good trade - it is
# an option because the author cut one - but it is why every slot on a narrow
# sheet reads as open, and why the sheet says so in its own description.
NARROW = False

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


def slot_half():
    """Half the mortice across the band, from the wall's centreline.

    Where the DRAWN slot edge falls, which is not where the wall's face falls:
    the hole is drawn BURN under size, so this is half a kerf inboard of it.
    slot() and a narrow cheek_off() both read it here rather than each writing
    the expression out, because the whole point of --narrow is that the two
    agree to the last micron, and two copies of an expression do not stay
    equal through a --kerf.
    """
    return (SHEET - SLOT_TIGHTEN) / 2 - BURN / 2


def cheek_off():
    if NARROW:
        return wall_off() + slot_half()
    return wall_off() + THICK / 2 + WEB


def band():
    return 2 * cheek_off()
# 0.15 from 2026-09-13, on the author's instruction, and bore_split.py's KERF
# is the same number from the same day. They have to agree: the two generators
# cut parts of one instrument on one machine, and a bore whose cheeks were
# drawn at one kerf and whose blocks were drawn at another is a bore whose
# joints are out by the difference.
#
# Until this date the sheets on disk were drawn with an explicit --kerf=0.15
# while the default here still read 0.13, so a bare run did NOT reproduce them.
# The default is the number the tree was drawn at, or it is a trap.
BURN = 0.15          # kerf, the FULL width the laser takes out, centred on the
                     # line. 0.1 by assumption, then 0.13 measured 2026-09-09.
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
PORT = False         # --port: a 7 x 14mm opening through the cheek at the
                     # mouth, so a mouthpiece or a bell can go in at 90
                     # degrees to the plane the bore is wound in. NOT
                     # bore-square: see PORT_ACROSS for why it cannot be
BED_W, BED_H = 600.0, 308.0        # xTool P2S work area

# --shape. 'dspiral' is the double spiral, the shape this file is aimed at and
# the default; 'serpentine' is a run of alternating half-circles joined by
# straight verticals, which is that shape generalised. LOBES/LOBE_R/RISE
# describe it. The 180 degree 'coupon' that used to be the default is gone,
# deleted 2026-09-14, and with it the fall-through that drew it: an unknown
# --shape is now refused by name rather than quietly drawing a test piece.
SHAPES = ('dspiral', 'serpentine', 'opposed', 'wave', 'spiral', 'volute',
          'torus', 'scallop', 'racetrack', 'oval')
SHAPE = 'dspiral'
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
# --port-square: the bore-square port the table above calls uncuttable, at
# BORE x BORE. It is cuttable after all, but only once the thing in its way is
# gone. The table measures clearance against the tab slots of the LEAD panel,
# which carries one tooth dead centre, exactly where the port wants to be. Take
# the lead panel out and merge it into its neighbour - they are collinear, so
# the merge is exact and the airway does not change - and the nearest slot is
# 9.7mm away instead of 0.16mm.
#
# So this flag does not overrule that table, it removes its premise. The guard
# in teeth_kept() still stands: ask for a square port on a design that still
# has its lead panels and it refuses, naming the panel whose only tab the port
# would take. That refusal is the table, enforced.
#
# The SIZE is BORE, not a literal 10, so --bore carries it. The KERF is already
# a variable here: port_hole() draws the hole BURN under size, so the opening
# comes out BORE exactly at any --kerf, and the drawn square is BORE - BURN --
# 9.87mm at the measured 0.13, 9.83 at 0.17. Never hard-code the 9.87: it is
# the answer for one kerf, and the kerf is the number most likely to change.
PORT_SQUARE = False
# --port-both: the same port at BOTH ends of the run, not just the mouth. A
# duct has two ends and both are leads made the same way -- tail() extends the
# end segment's own direction -- so the far end takes a port on exactly the
# terms the mouth does: collinear lead, PORT_FROM_TIP back from the tip, drawn
# BURN under size. Nothing about the hole changes; only how many there are.
#
# It is a SEPARATE flag and not the default, because two ports make a part the
# one-port sheet is not: two more holes in a cheek that is cut twice, and under
# --port-square two more panels folded away. The stem says "both" for the same
# reason it says "ported" and "square" -- the sheets are otherwise told apart
# only by counting holes in a thumbnail.
PORT_BOTH = False
# --port-per-cheek: the two ports split between the two cheeks rather than each
# going through both. It changes no geometry -- same coil, same panels, same two
# holes in the same two places -- only WHICH SHEET each hole is drawn on, and
# that turns one sheet cut twice into two sheets cut once.
#
# The reason is what a port through both cheeks leaves you: a socket right
# through, and the side you are not using is an open hole to plug. Two ports
# make four such holes and two of them are waste. One port a cheek makes two
# holes, both of them wanted, and nothing to plug.
#
# The consequence is worth saying out loud, because it is the instrument: the
# mouthpiece goes into one FACE and the bell leaves the other. The openings no
# longer sit in the plane of the coil at all, so the total-turning-zero argument
# that puts the two RIM ends on opposite headings stops describing how the thing
# is played -- those ends are the capped ones now.
#
# It needs --port-both, having nothing to split otherwise.
PORT_PER_CHEEK = False
# --port-at=i,j: put the ports on NAMED FACETS instead of at the two ends of
# the run. Facet i is the centreline segment from vertex i to vertex i+1, and
# the hole goes PORT_FROM_TIP along it from vertex i, in the run's direction --
# so --port-at=0 is the mouth port exactly, byte for byte, and every other
# index is a place the end-based placement cannot reach.
#
# It exists because a CLOSED RING has no ends. cline[0] and cline[-1] are one
# vertex on a torus, so --port-both put both ports 19.4mm apart either side of
# the seam and no flag moved them. The two openings of a ring are wherever you
# say they are, and nothing else in this file needed to learn that: the
# per-cheek split, teeth_kept(), the label dodge, three checks and the
# narrow-rim web all read port_holes() and never ask where a port came from.
#
# The LIST LENGTH is the port count, so it replaces --port-both rather than
# joining it, and the two together are refused: each is an answer to "how many
# ports and where", and two answers is one too many.
#
# TWO PORTS ON A RING LEAVE THE AIR TWO PATHS, AND THAT IS THE POINT HERE.
# The ring is not a duct and is not meant to be one: it is a resonator with two
# parallel branches, and the SEPARATION of the ports is its tuning dial. Ports
# on facets 0 and K split an n-ring into K facets one way and n-K the other, so
# the dial is K and it runs 1 to n//2 -- most lopsided at K=1, nearest balanced
# at K=n//2. On a 13 ring at R40 that is 1:12 (19.1 against 229.7mm) down to
# 6:7 (114.9 against 134.0).
#
# PICK AN ODD n AND THE PATHS CANNOT COME OUT EQUAL. An even ring has K=n/2
# exactly antipodal, the two paths identical, the branches in phase and the
# whole effect gone. 13 has no such K: its closest split still differs by a
# facet. That is a reason to choose an odd facet count, not an accident of it.
#
# No check here has an opinion about any of this -- they are all geometric, and
# every K from 1 to n//2 passes all twelve at every radius in the ring's band.
# The dial is yours; the checks only say it can be cut.
#
# If a SINGLE path is ever wanted instead, the ring has to be blocked between
# the ports, and the only block position leaving no dead side-branch is one
# adjacent to both of them -- which forces the ports adjacent to each other and
# is the end-based placement again. Written down because it is the question a
# reader asks here, not because anything in this file wants it.
PORT_AT = None
# --port-square implies this: the square port needs the lead panel's tooth out
# of the way, and folding the lead into the facet it already lies on is the
# only move that buys the room without moving the coil. Separately settable so
# a merged lead can be drawn and looked at without a port.
#
# --port-both needs the SAME thing at the far end, so MERGE_LEAD folds the tail
# lead as well when both ends are ported. A merge that did only the mouth would
# leave the far port sitting on the tail lead's one tooth, which is the case
# teeth_kept() refuses -- the refusal would be correct and the fix is here.
MERGE_LEAD = False
# --cap: one plate that closes the duct's open end, on the panels sheet. Only
# meaningful with --port, which is what gives the air somewhere else to go, so
# it refuses on its own rather than sealing a bore with no way in. Off by
# default because every ported sheet in this repo was cut without one.
CAP = False
# TRIED AND REJECTED, 2026-09-09. It does clear the port: the tightest design
# then shipping went from 0.030mm of ply to 2.931mm and passed every check. But the lead is part of the
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
# --shape=scallop: a CLOSED serpentine. The open one runs half-circles down a
# line; this bends the same alternation round until it shuts, so the lobes sit
# on a ring and there are no ends at all.
#
# WHAT CLOSES IT IS THE SYMMETRY, not a solver. One lobe is a convex arc then a
# concave one, and if that unit turns exactly 360/LOBES the figure is invariant
# under a 360/LOBES rotation -- so LOBES of them come back to the start by
# construction, whatever the radii. Hence the one law here:
#
#     convex turn - concave turn = 360 / LOBES
#
# SCALLOP_IN_DEG is the concave turn and the convex one is derived, so the
# relation cannot be written down wrong. FACET has to divide all three of the
# concave turn, the derived convex turn and 360/LOBES; at LOBES 5 that makes
# 360/5 = 72 three facets of 24, and the shipped design is a 48 degree scoop
# against a 120 degree bulge. The measured closure is 4e-13mm.
#
# Both radii are bends and both answer to the same floor as every other shape:
# the tooth, not the geometry. At FACET 24 and a 10mm bore that is R30.6, and
# SCALLOP_IN_R is the one that will hit it first because the scoop is tighter
# than the bulge.
#
# THE SCOOP NEEDS TWO FACETS OR IT IS NOT THERE. Arcs are inscribed, so a chord
# turns half a facet at each end; a one-facet scoop between two bulges turns +half
# where the bulge turned -half, twice, and the centreline goes STRAIGHT through
# it. The first 800mm scallop (36 degree facets, a 36 degree scoop of R40) was
# drawn, gated and quoted as R40 with no inward bend anywhere: a decagon with
# rounded corners. The one that replaced it (2026-09-16) keeps 36 degree facets
# -- finer ones make panels too short for a square port to leave a tooth on --
# and scoops 72 degrees, two facets, R41 against a 144 degree bulge of R44.22.
# R41 is as tight as the pair goes with ports: from R42 no facet takes one.
SCALLOP_IN_R, SCALLOP_IN_DEG = 34.0, 48.0
# --shape=racetrack: a closed serpentine that is NOT radially symmetric, which
# is the whole reason it exists. A scallop repeats one lobe LOBES times about a
# centre, so its envelope is circular and the bed's 288mm of HEIGHT bounds it in
# both axes -- the 580mm of width goes unused, and the shipped 800mm scallop is
# already within a millimetre of the limit. 1600mm needs twice the envelope and
# there is no scallop that has it: deepening the lobes shrinks the figure, but
# the cheek starts crossing itself before it gets under 288. Measured across
# 5/8/10/12 lobes and facets 24 to 72; there is no window.
#
# So this one is 2-FOLD symmetric and long. Half the loop is a 180 degree cap
# then LOBES alternating half-circles joined by straights; the alternation nets
# zero turning, so the half turns 180 and two halves turn 360. Same argument as
# the scallop, one order lower: the figure is invariant under a half turn, so
# the second half closes it whatever the radii. Measured closure 5e-13mm.
#
# THE STRAIGHTS ARE FOR THE PORTS, not the shape. Lobes at the bend floor make
# 15mm facets whose inner panels are 11.2mm, and a bore-square port takes every
# tooth on a panel that short. A straight turns nothing, so it costs the closure
# argument nothing and buys a panel long enough to carry one.
RACE_CAP_R, RACE_STRAIGHT = 134.115704, 30.0
# --shape=oval: a closed ellipse with its two long ends flattened, and no ports.
#
# Built like the racetrack, as half a loop taken twice, so it closes by the same
# 2-fold symmetry whatever the numbers. The half is a straight across one long
# end -- the flat -- then an arc of OVAL_END_R turning OVAL_END_DEG, an arc of
# OVAL_SIDE_R turning 180 - 2 * OVAL_END_DEG along the long side, and the end arc
# again. Four arcs a loop of two radii is the draughtsman's ellipse; the flat is
# what makes the ends blunter than an ellipse's. FACET has to divide both turns.
#
# Both radii answer to the tooth floor like every other bend, and the end arc is
# the tighter of the two, so it is the one that meets it.
#
# OVAL_SIDE_FLAT puts a straight in the middle of each long side, splitting the
# side arc in two, so the two long sides carry segments parallel to each other
# and to the long axis. FACET then has to divide HALF the side turn.
#
# THE DEFAULTS ARE THE SMALLEST ONE, found by search on 2026-09-16 against every
# check here and the rules of shape: a flat at each long end, a straight in the
# middle of each long side, at least two facets on each end arc, and the long
# axis at least 1.4 times the short. At 30 degree facets that is ends of R28
# turning 60, sides of R72 turning 30 either side of a 12.5mm straight, and
# 12.2mm flats: 314.4mm of centreline, a 148 x 116mm cheek. What stops it
# shrinking is the tooth: a 12.1mm flat, a 12mm side straight or R27.5 at the
# ends leaves an inner panel too short to hold one. 22.5 degree facets, the
# only other angle that divides both turns with two facets an end, come out
# 354mm. Without the side straights the smallest was 338.7mm.
OVAL_END_R, OVAL_END_DEG, OVAL_SIDE_R, OVAL_FLAT = 28.0, 60.0, 72.0, 12.2
OVAL_SIDE_FLAT = 12.5
# The angle each shape is drawn at, where it is not FACET's default 30.
# scallop: 24 divides 72, which is 360/5, so a five-lobe ring can be built at
# all. 30 does not divide 72 and refuses; the shipped ring is 24.
FACET_BY_SHAPE = {'wave': 45.0, 'spiral': 45.0, 'volute': 45.0,
                  'scallop': 24.0, 'racetrack': 45.0}
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
# to be solved rather than chosen, so it is the part a test piece should prove.
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
    if SHAPE == 'oval':
        side_deg = 180.0 - 2 * OVAL_END_DEG
        for flag, v in (('--oval-flat', OVAL_FLAT),
                        ('--oval-side-flat', OVAL_SIDE_FLAT)):
            if v < 0:
                raise ValueError(f'{flag}={v:g} is negative.')
        if not 0 < OVAL_END_DEG < 90:
            raise ValueError(
                f'--oval-end-deg={OVAL_END_DEG:g} has to be between 0 and 90: '
                f'the two end arcs and the side arc share a half turn.')
        # A side flat splits the side arc in two, so each half has to be a
        # whole number of facets, not only the whole.
        for what, deg in (('the end turn', OVAL_END_DEG),
                          ('the side turn', side_deg)
                          if not OVAL_SIDE_FLAT else
                          ('half the side turn', side_deg / 2)):
            if abs(round(deg / FACET) * FACET - deg) > 1e-9:
                raise ValueError(
                    f'--facet={FACET:g} does not divide {what}, {deg:g} '
                    f'degrees, a whole number of times.')
        floor = wall_off() + (TOOTH + 2 * SHOULDER) / 2 / math.sin(
            math.radians(FACET / 2))
        tight = min(OVAL_END_R, OVAL_SIDE_R)
        if tight < floor:
            raise ValueError(
                f'the tightest arc is R{tight:g} and a {BORE:g}mm bore at '
                f'{FACET:g} degree facets needs R{floor:.1f}.')
        side = ([('a', OVAL_SIDE_R, side_deg / 2), ('s', OVAL_SIDE_FLAT),
                 ('a', OVAL_SIDE_R, side_deg / 2)] if OVAL_SIDE_FLAT else
                [('a', OVAL_SIDE_R, side_deg)])
        half = ([('s', OVAL_FLAT), ('a', OVAL_END_R, OVAL_END_DEG)] + side
                + [('a', OVAL_END_R, OVAL_END_DEG)])
        step = math.radians(FACET)
        x = y = a = 0.0
        pts = [(0.0, 0.0)]
        for item in half * 2:
            if item[0] == 's':
                if item[1] > 0:
                    x, y = x + item[1] * math.cos(a), y + item[1] * math.sin(a)
                    pts.append((x, y))
                continue
            _, R, deg = item
            for _ in range(int(round(deg / FACET))):
                c = 2 * R * math.sin(step / 2)
                a += step / 2
                x, y = x + c * math.cos(a), y + c * math.sin(a)
                a += step / 2
                pts.append((x, y))
        # the same snap as the racetrack and the scallop, for the same reason
        pts[-1] = pts[0]
        # The flat runs along x as built, so the long axis comes out along y.
        # A quarter turn lays it along the bed, as the racetrack does.
        pts = [(y, -x) for x, y in pts]
        return flip(pts)
    if SHAPE == 'racetrack':
        # Half the loop, taken twice. The half is a 180 degree cap and then
        # LOBES alternating half-circles joined by straights -- the OPEN
        # serpentine's own construction, which is here because the first
        # attempt was not. Lobes written as +deg then -deg at one radius do
        # net zero turning, but a pair like that advances PERPENDICULAR to the
        # heading it started with, so the straights displaced the whole run
        # instead of separating neighbours and the lobes collided: 60 slot
        # corners outside the cheek and 0.062mm of ply at the worst pair.
        # Alternating half-circles with a straight after each is the shape
        # that does not touch itself, and the serpentine's note says why the
        # straights are there at all.
        #
        # LOBES has to be EVEN. The alternation nets zero only in pairs, and
        # an odd count leaves the half turning 0 or 360 instead of 180, which
        # does not close.
        if LOBES % 2:
            raise ValueError(
                f'--lobes={LOBES} is odd. The half-circles alternate, so they '
                f'cancel only in pairs; an odd count leaves the half turning '
                f'{180 - 180 * (LOBES % 2):g} degrees instead of 180 and the '
                f'loop does not close.')
        if RACE_STRAIGHT < 0:
            raise ValueError(
                f'--race-straight={RACE_STRAIGHT:g} is negative.')
        if abs(round(180.0 / FACET) * FACET - 180.0) > 1e-9:
            raise ValueError(
                f'--facet={FACET:g} does not divide a half-circle a whole '
                f'number of times.')
        floor = wall_off() + (TOOTH + 2 * SHOULDER) / 2 / math.sin(
            math.radians(FACET / 2))
        tight = min(LOBE_R, RACE_CAP_R)
        if tight < floor:
            raise ValueError(
                f'the tightest arc is R{tight:g} and a {BORE:g}mm bore at '
                f'{FACET:g} degree facets needs R{floor:.1f}.')
        half = [('a', RACE_CAP_R, +1)]
        for i in range(LOBES):
            half.append(('a', LOBE_R, -1 if i % 2 == 0 else +1))
            if RACE_STRAIGHT > 0:
                half.append(('s', RACE_STRAIGHT, 0))
        step = math.radians(FACET)
        per = int(round(180.0 / FACET))
        x = y = a = 0.0
        pts = [(0.0, 0.0)]
        for item in half * 2:
            if item[0] == 's':
                x, y = x + item[1] * math.cos(a), y + item[1] * math.sin(a)
                pts.append((x, y))
                continue
            _, R, sg = item
            for _ in range(per):
                c = 2 * R * math.sin(step / 2)
                a += sg * step / 2
                x, y = x + c * math.cos(a), y + c * math.sin(a)
                a += sg * step / 2
                pts.append((x, y))
        # Same snap as the scallop: offset() tests its seam with an absolute
        # 1e-9 and the construction closes to 5e-13, which is not zero.
        pts[-1] = pts[0]
        # LAID ALONG THE BED. The run of half-circles marches across the
        # direction the half set out in, so the figure comes out long in y.
        # The bed is 580 x 288 and pack() does not rotate a part, so a
        # 84 x 418 cheek is refused although it fits turned. One quarter turn
        # here, where the shape is still a list of points, costs nothing.
        pts = [(y, -x) for x, y in pts]
        return flip(pts)
    if SHAPE == 'scallop':
        # A closed serpentine: LOBES lobes, each a convex arc of LOBE_R then a
        # concave one of SCALLOP_IN_R. See the note beside SCALLOP_IN_R: the
        # unit has to turn 360/LOBES for the figure to be LOBES-fold symmetric,
        # and that symmetry is what shuts it, so the convex turn is DERIVED
        # rather than given.
        per = 360.0 / LOBES
        out_deg = SCALLOP_IN_DEG + per
        for what, deg in (('360/LOBES', per), ('the concave turn',
                          SCALLOP_IN_DEG), ('the convex turn', out_deg)):
            if abs(round(deg / FACET) * FACET - deg) > 1e-9:
                raise ValueError(
                    f'--facet={FACET:g} does not divide {what}, {deg:g} '
                    f'degrees, a whole number of times. At {LOBES} lobes the '
                    f'facet has to divide 360/{LOBES} = {per:g} as well as '
                    f'both turns.')
        floor = wall_off() + (TOOTH + 2 * SHOULDER) / 2 / math.sin(
            math.radians(FACET / 2))
        tight = min(LOBE_R, SCALLOP_IN_R)
        if tight < floor:
            raise ValueError(
                f'the tightest arc is R{tight:g} and a {BORE:g}mm bore at '
                f'{FACET:g} degree facets needs R{floor:.1f}.')
        segs = ([('a', LOBE_R, +1)] * int(round(out_deg / FACET))
                + [('a', SCALLOP_IN_R, -1)] * int(round(SCALLOP_IN_DEG / FACET))
                ) * LOBES
        step = math.radians(FACET)
        x = y = a = 0.0
        pts = [(0.0, 0.0)]
        for _, R, sg in segs:
            c = 2 * R * math.sin(step / 2)
            a += sg * step / 2
            x, y = x + c * math.cos(a), y + c * math.sin(a)
            a += sg * step / 2
            pts.append((x, y))
        # Shut it EXACTLY. The construction closes to 4e-13mm, which is the
        # symmetry working, but offset() tests its seam with an absolute 1e-9
        # and a polyline that misses by even that is mitred as an open run --
        # the two seam facets come out over-long and the ring does not close.
        # Snapping costs 4e-13mm of one facet and buys the mitre.
        pts[-1] = pts[0]
        return flip(pts)
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
    # No fall-through. Every shape above returns; the 180 degree coupon used to
    # sit here and be drawn by anything that reached the end, which meant a
    # misspelt --shape produced a test piece rather than a complaint. Refusing
    # by name is the same rule --trace and the port flags already follow.
    raise ValueError(f'--shape={SHAPE} is not a shape here. '
                     f'Known: {" ".join(sorted(SHAPES))}.')


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
    """Where two segments' infinite lines cross, or None if they are parallel.

    The parallel test is RELATIVE. d is the cross product of the two direction
    vectors, so it carries their lengths: on 37mm segments a truly collinear
    pair gives d around 1e-11, which an absolute 1e-12 threshold calls
    "crossing" and then divides by. Dividing by 1e-11 is how a mitre ends up
    31.69mm from the vertex it belongs to.

    That is not hypothetical. The serpentine's centreline turns 0.000 degrees
    at v4, where its two lobes meet, and at a cheek offset of 7.905mm - which
    is exactly --narrow on 2.94mm ply at a 0.13mm kerf - v4's mitre landed
    31.69mm out. It put twelve mortices outside the cheek. At 7.895 and 7.925
    the same vertex is exact, because the noise fell the other side of the
    threshold: the failure moved with the last decimal of the ply.
    Dividing by the segment lengths makes d the sine of the angle between
    them, which is scale-free, and 1e-9 of that is 6e-8 of a degree.
    """
    (x1, y1), (x2, y2) = s
    (x3, y3), (x4, y4) = t
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    lu = math.hypot(x2 - x1, y2 - y1)
    lv = math.hypot(x4 - x3, y4 - y3)
    if lu == 0.0 or lv == 0.0 or abs(d) < 1e-9 * lu * lv:
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

    One tooth is enough at 10-16mm panels and is a hinge at 90mm:
    a straight run held by a single 6mm tab in its middle pivots about it and
    the seam opens. Alternating tooth and gap of equal width, as Boxes.py does,
    so a panel gets as many as it has room for:

        n = floor((L - 2*SHOULDER + TOOTH) / (2*TOOTH))

    which is 1 up to 17.9mm, 3 at 34mm and 7 at 90mm. It was written so that
    every panel on the short test piece then shipping still took exactly one,
    and that sheet's cut geometry did not move when this arrived.
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


def _no_description():
    raise ValueError(f'no report description for --shape={SHAPE}.')


def caps():
    """How many end caps this design needs: one per ported end, else none.

    A function and not a constant, for the same reason band() is: --port-both
    is read after this line and a constant would keep the one-cap answer. A
    sheet that drew one cap for two open ends would be short exactly one part,
    with nothing to notice it but counting -- which is the mistake items_for()
    already records about cheeks.
    """
    return (2 if PORT_BOTH else 1) if CAP else 0


def cap():
    """The plate that closes the duct's open end, flat, centred on the origin.

    A ported bore does not breathe through its mouth: the mouthpiece goes into
    the port and the run simply stops a bore further on, so the end is a hole
    the size of the airway pointing out of the coil. Air takes it. This closes
    it, and it is the only part here that is not a wall or a cheek.

    SQUARE, at 2*THICK + BORE a side: the stack, which is the two cheeks with
    the airway between them, taken in both directions. 16 x 16 on a 3mm sheet
    and a 10mm bore.

    Only one of those two sides is the face it covers. Through the stack it is
    exact. Across the band it is not: the band is band() - 15.81 narrow, 20 not
    - which is the wall offset plus half a mortice and has nothing to do with
    the stack. So on a narrow cheek the cap stands 0.095mm proud each side, and
    on a full-width one it falls 2mm short each side. Neither leaks: the airway
    is BORE wide and centred, so there is 2.9mm of cheek edge either side of it
    even at the narrow band, and the cap covers the opening with room to spare
    whichever way the error runs. Square is a choice about the part, not about
    the seal - one number to cut to, and it follows --bore and the ply.

    Kerf goes OVER, as it does on a panel: this is material kept, so the drawn
    square is BURN bigger than the part and the cut part is 2*THICK + BORE.

    It is glued, not tabbed. Nothing in the cheeks mortices it, and cutting
    mortices for it would put two more holes in the narrow rim right where the
    port already is.
    """
    e = BURN / 2
    hw = hh = (2 * THICK + BORE) / 2 + e
    return [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]


def teeth_kept(part, portpolys):
    """This part's teeth, less any a port would cut into.

    `portpolys` is the list from port_holes(): none, the mouth's, or both
    ends'. A tooth has to clear EVERY port, so the worst gap over the list is
    the one that decides -- with one port that is the old single-hole test,
    unchanged.

    A tooth and its mortice are one thing: drop it from the panel and you must
    drop it from the cheek, or a slot opens on nothing. That is why this is
    computed once, in build(), and read from the part by both.
    """
    # 'cs' is set only by merge_lead(), which pins a merged panel's teeth to
    # where its surviving half already had them. Recomputing from the new
    # length would re-space them over the whole merged panel and move every
    # mortice with them, which is the one thing a merge must not do to a
    # design whose other sheet is already cut.
    cs = part['cs'] if 'cs' in part else teeth(part['len'])
    if not portpolys:
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
                        P[j], P[(j + 1) % len(P)])
                for P in portpolys
                for i in range(len(S)) for j in range(len(P)))
        # A NANOMETRE of slack, and it is not a loosening of the gate. A
        # round-ported lead lands on this limit exactly: 1.500000mm of ply
        # after the kerf, against the 1.5mm asked for. At 3.0mm ply and a
        # 0.15mm kerf the sum came out 1.6499999999999986 against 1.65 and the
        # design was refused over 1.3e-15mm, which is not a distance. The
        # comparison has to be decidable; the limit is unchanged.
        if g >= MIN_FEATURE + BURN - 1e-9:
            out.append(c)
    if cs and not out:
        raise ValueError(
            f'the port takes the only tooth on {part["wall"]} panel '
            f'{part["n"]} ({part["len"]:.1f}mm), which would leave it with no '
            f'tab. A bore-square port passes within 0.16mm of a slot wherever '
            f'it sits, so the room has to come from somewhere: narrow the port '
            f'(7mm clears at the mouth by 1.66mm), or accept a glued panel.')
    return out


def pt_seg(q, a, b):
    """Distance from a point to a segment.

    At module level because checks() needs it twice over the same rim, once to
    ask whether a mortice corner sits on it and once to measure the web, and
    those two have to be the same measurement or --narrow could pass one and
    fail the other over the same micron.
    """
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    u = 0.0 if L2 == 0 else max(0.0, min(1.0, ((q[0] - a[0]) * dx
                                               + (q[1] - a[1]) * dy) / L2))
    return math.hypot(q[0] - (a[0] + u * dx), q[1] - (a[1] + u * dy))


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
    hh = slot_half()
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


def contours(outline):
    """The closed loops a cheek outline is CUT as.

    For an open shape the outline is one loop and this returns it. For a closed
    one -- torus, scallop, racetrack -- cheek() joins the outer ring to the inner
    one, so the list goes round the outer ring, steps across the band to the
    inner ring, goes round that, and closes back across the same step. As a
    polygon that is harmless: the two crossings coincide and cancel, and every
    inside test here reads it right. As a CUT it is a slit straight across the
    cheek band and through the airway at the seam, and every ring cheek drawn
    until 2026-09-16 carried one: one path, one M, one Z. So the drawing takes
    the rings apart here, and the cheek comes off the bed as a ring.
    """
    # Within 1e-9, the tolerance offset() shuts a loop with, not exactly: the
    # scallop's seam sits on a vertex that does not turn, offset() finds no
    # mitre there, and the two ends of its outer ring agree only to rounding.
    k = next((i for i in range(1, len(outline) - 1)
              if math.hypot(outline[i][0] - outline[0][0],
                            outline[i][1] - outline[0][1]) < 1e-9), None)
    return [outline] if k is None else [outline[:k + 1], outline[k + 1:]]


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


def merge_lead(parts):
    """Fold each wall's lead panel into its neighbour, keeping the neighbour.

    The mouth lead and the facet after it are COLLINEAR - centreline() makes
    the lead by extending the first segment's own direction - so this joins two
    panels that already lie on one line. No airway moves, no mitre changes, and
    the merged length is the exact sum.

    It exists for --port-square. The port wants the middle of the lead and the
    lead's one tooth is already there; the room has to come from the teeth, and
    this is where it comes from.

    What it deliberately does NOT do is re-space the teeth or renumber the
    panels. teeth() reads a panel's length alone, so a 43.2mm merged panel
    would get three teeth at -12, 0, +12 where its 23.2mm half had two at -6,
    +6 - and one of those three lands at 9.6mm along the duct, inside a port
    that spans 3.07 to 12.94. Every mortice in the cheek would move with them.
    The tags are worse: build() numbers by position, so dropping two panels
    renumbers all 36 that remain, and a panel already cut would read a number
    that now means a different panel.

    So the surviving half keeps its tag and keeps its teeth where they are.
    They move only because the panel's midpoint moves: half the lead's length
    along the run, which is what turns [-6, +6] into [+4, +16].
    """
    out, by_wall = [], {}
    for p in parts:
        by_wall.setdefault(p['wall'], []).append(p)
    dropped, gone = [], set()
    for wall, ps in by_wall.items():
        ps = sorted(ps, key=lambda q: q['n'])
        # The mouth lead folds FORWARD into the panel after it; under
        # --port-both the tail lead folds BACKWARD into the panel before it.
        # Same fold either way: the survivor keeps its tag and its teeth, and
        # only the sign of the slide differs, because a panel that grows
        # backwards moves its midpoint against the run and one that grows
        # forwards moves it along.
        folds = [(ps[0], ps[1], -1.0)]
        if PORT_BOTH:
            # Four distinct panels, or the two folds meet in the middle and
            # the second one reads a length the first has already changed --
            # re-spacing the teeth of a panel whose mortices are settled. A
            # wall that short cannot carry a port at each end anyway.
            if len(ps) < 4:
                raise ValueError(
                    f'--port-both needs at least four panels on each wall to '
                    f'fold a lead into a neighbour at both ends, and {wall} '
                    f'has {len(ps)}.')
            folds.append((ps[-1], ps[-2], +1.0))
        for lead, nxt, sgn in folds:
            # Refuse rather than silently fold a mitre flat: if these two are
            # not collinear the merge would cut a corner off the airway.
            d = abs((nxt['ang'] - lead['ang'] + math.pi)
                    % (2 * math.pi) - math.pi)
            if math.degrees(d) > 1e-6:
                raise ValueError(
                    f'{wall} panels {lead["n"]} and {nxt["n"]} meet at '
                    f'{math.degrees(d):.3f} degrees, not in line, so merging '
                    f'them would move the airway. --merge-lead only folds a '
                    f'straight lead into the facet it already lies on.')
            half = lead['len'] / 2
            ux, uy = math.cos(nxt['ang']), math.sin(nxt['ang'])
            # one end stays put and the panel grows the other way, so the
            # midpoint slides half the lead's length; the teeth are pinned to
            # where they already are, which is that slide taken back out
            nxt['label_mid'] = nxt['mid']
            nxt['mid'] = (nxt['mid'][0] + sgn * ux * half,
                          nxt['mid'][1] + sgn * uy * half)
            nxt['cs'] = [c - sgn * half for c in teeth(nxt['len'])]
            nxt['len'] = lead['len'] + nxt['len']
            dropped.append(f'{wall} {lead["tag"]}')
            gone.add((wall, lead['n']))
    for p in parts:
        if (p['wall'], p['n']) in gone:
            continue
        out.append(p)
    print(f'  --merge-lead: folded the '
          + ('lead panel at each END' if PORT_BOTH else 'lead panel')
          + f' into its neighbour on both walls, dropping '
          f'{", ".join(dropped)}; every other panel keeps its number and its '
          f'teeth')
    return out


def build():
    """Every part, in millimetres, with the numbers each one carries."""
    c = centreline()
    inn, out = walls(c)
    parts, report = [], []
    # Numbered straight through in hex rather than I1/O1: the glyph table is
    # the one the bore sections and bell rings use, and adding I and O to it
    # would put I beside 1 and O beside 0 on a part you read at the bench.
    # The number identifies a panel, not its length. On a tight design the
    # inner and outer panels fall in different ranges and length tells them
    # apart; on the serpentine both walls run 19.14-90.00mm and it tells
    # you nothing. Either way the cheek slot carries the same number.
    seq = 0
    cl = c

    def turn_at(poly, k):
        """How far the wall turns at vertex k. A free end turns through 0.

        A CLOSED polyline has no free end. Its first and last vertex are one
        vertex, and it turns there by a facet like every other -- so the trim
        below has to wrap, or the two panels either side of the seam keep the
        THICK/2*tan(phi/2) of ply the trim exists to take off. They then butt
        before either is seated and the ring does not close: 0.37mm a panel at
        13 facets, 0.62mm at 8, which is the 1.24mm the trim's own comment
        quotes from the bench. Every --shape=torus ever drawn failed "no two
        wall panels share plan area" with exactly 2 jamming pairs, one per
        wall, for this reason and no other.

        offset() already computes this same shut test, at the seam mitre, for
        the same reason. An open run has poly[0] != poly[-1], so it takes the
        0.0 branch exactly as before and no shipped sheet moves.
        """
        shut = (abs(poly[0][0] - poly[-1][0]) < 1e-9
                and abs(poly[0][1] - poly[-1][1]) < 1e-9)
        if k <= 0 or k >= len(poly) - 1:
            if not shut:
                return 0.0
            h1 = math.atan2(poly[-1][1] - poly[-2][1],
                            poly[-1][0] - poly[-2][0])
            h2 = math.atan2(poly[1][1] - poly[0][1], poly[1][0] - poly[0][0])
            return abs((h2 - h1 + math.pi) % (2 * math.pi) - math.pi)
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
    if MERGE_LEAD:
        parts = merge_lead(parts)
        report = [(q['tag'], q['wall'], q['len']) for q in parts]
    # The teeth are settled here, once, because a tooth and its mortice have to
    # agree and only this function has both the parts and the port.
    portpolys = port_holes(c)
    for q in parts:
        q['teeth'] = teeth_kept(q, portpolys)
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


def port_hole(cline, end=0):
    """A slot through the cheek at an end of the run, for a mouthpiece.

    `end` is 0 for the mouth and -1 for the far end. Both are leads built by
    the same tail() in centreline(), so the far end differs only in which two
    stations give the direction: the tip and the station after it, walking in.

    Under --port-at it is ('facet', i) instead, and the direction comes from
    facet i's own two stations, walked FORWARD from vertex i. The far end's
    mirror is therefore not --port-at=<last>: that measures from the last
    facet's start, where end=-1 measures from the run's tip walking back. Give
    --port-from-tip the distance you want measured along the run and there is
    one rule rather than a sign to get right.

    The airway is bounded top and bottom by the cheeks, so the only way out of
    the plane is through one. This cuts a PORT_ACROSS x PORT_ALONG hole -- 7 x
    14mm by default, not bore-square, for the reason set out beside
    PORT_ACROSS, or BORE x BORE under --port-square once the lead panel that
    stood in its way is gone -- a bore back from the tip, and the bore turns 90
    degrees into z there. It is 98mm2 against the bore's own 100 at 7 x 14, and
    the bore's own 100 exactly when square, so the air barely knows either way.
    Both cheeks carry it,
    because they are one part cut twice and that is worth more than saving a
    hole: you get a socket right through, plug the side you are not using.

    It is a slot, not an outline cut, so it is taken in the orange stage while
    the sheet still holds the cheek - the same reason the tab slots are.
    """
    if isinstance(end, tuple):          # ('facet', i), from --port-at
        a, b = cline[end[1]], cline[end[1] + 1]
    else:
        a, b = (cline[0], cline[1]) if end == 0 else (cline[-1], cline[-2])
    ux, uy = b[0] - a[0], b[1] - a[1]
    m = math.hypot(ux, uy)
    # The hole has to fit on the segment it is measured along, and until
    # --port-at it always did by construction: a lead is LEAD long, the port
    # spans PORT_FROM_TIP +- PORT_ALONG/2, and 3 to 17 of 20 needs no check.
    # A NAMED facet is whatever the shape made it, and a port that runs off the
    # end of one is drawn by extrapolating this direction -- a hole in the
    # cheek at a place the airway does not go. Refuse, with both numbers.
    if PORT_FROM_TIP - PORT_ALONG / 2 < 0 or PORT_FROM_TIP + PORT_ALONG / 2 > m:
        where = (f'facet {end[1]}' if isinstance(end, tuple)
                 else 'the mouth lead' if end == 0 else 'the tail lead')
        raise ValueError(
            f'the port spans {PORT_FROM_TIP - PORT_ALONG / 2:.2f} to '
            f'{PORT_FROM_TIP + PORT_ALONG / 2:.2f}mm along {where}, which is '
            f'{m:.2f}mm long. Move it along with --port-from-tip, or name a '
            f'facet with room for it.')
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


def port_holes(cline):
    """Every port on this design, mouth first. Empty without --port.

    ONE place decides how many there are. The hole is read by six callers --
    the teeth, the cheek's slots, its labels, two checks and the narrow-rim
    web -- and a port that some of them knew about and others did not would be
    a hole cut where a tooth still is. `port_hole(c) if PORT else None` was
    that shape of thing repeated six times; this is it written once.
    """
    if not PORT:
        return []
    if PORT_AT is not None:
        # Range and distinctness are checked HERE and not at the flag, because
        # a facet index only means something against a centreline and main()
        # has not built one yet. len(cline) - 1 facets, 0-based.
        n = len(cline) - 1
        for i in PORT_AT:
            if not 0 <= i < n:
                raise ValueError(
                    f'--port-at names facet {i} and this centreline has {n}, '
                    f'numbered 0 to {n - 1}.')
        if len(set(PORT_AT)) != len(PORT_AT):
            raise ValueError(
                f'--port-at names the same facet twice: {PORT_AT}. Two holes '
                f'in one facet would be two mouths a bore apart, which is not '
                f'a thing this file knows how to cut.')
        return [port_hole(cline, ('facet', i)) for i in PORT_AT]
    return [port_hole(cline, 0)] + ([port_hole(cline, -1)] if PORT_BOTH else [])


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
    # ONE cheek, unless --port-per-cheek, when it is one per port and they are
    # different parts. Everything else about them is identical, so the only
    # thing that varies down this loop is which ports the sheet carries -- and
    # the labels have to follow, or a number gets engraved into a hole that is
    # on this sheet while the label dodged one that is not.
    subsets = ([port_holes(cline)] if not PORT_PER_CHEEK
               else [[P] for P in port_holes(cline)])
    for k, mine in enumerate(subsets):
        def cheek_marks(dx, dy, _p=parts, _c=cline, _mine=mine):
            m = []
            _dropped = []
            holes = [[(q[0] + dx, q[1] + dy) for q in P]
                     for P in _mine]

            def _fouls_at(px, py, ang, h=2.0, n=1):
                """Does a label of n glyphs, h tall, at this angle, hit a port?

                Pulled out of the per-panel test below so the cheek's own '0'
                can ask it too. With a port at each end the '0' no longer has
                a lead that is guaranteed clear, and a placement that cannot
                be tested is a placement that gets engraved into the hole.
                """
                if not holes:
                    return False
                w, gap = h * 0.62, h * 0.18
                total = n * w + (n - 1) * gap
                lo, hi = -total / 2, total / 2 + h * 0.38
                ca, sa = math.cos(ang), math.sin(ang)
                for P in holes:
                    for i in range(5):
                        u = lo + (hi - lo) * i / 4
                        for v in (-h / 2, 0.0, h / 2):
                            if in_poly(P, px + u * ca - v * sa,
                                       py + u * sa + v * ca):
                                return True
                return False
            for q in _p:
                # 'label_mid' is set only by merge_lead(): a merged panel's
                # midpoint slides half a lead along the run, and the number
                # would slide with it, off the mortices it names and onto a
                # stretch of cheek that carried no number before. Pinning it
                # keeps every label on a sheet already cut exactly where it was.
                anchor = q['label_mid'] if 'label_mid' in q else q['mid']
                mx, my = anchor[0] + dx, anchor[1] + dy
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
                # label()'s own extent, and it is NOT symmetric: the glyphs
                # span +-total/2 but the baseline tick runs on to
                # total/2 + 0.38h past them. A +-h/2 box missed the tick,
                # which is precisely what was being engraved into the port.
                def _fouls(px, py, h=2.0, n=1, _a=q['ang']):
                    return _fouls_at(px, py, _a, h, n)
                if _fouls(lx, ly, n=len(q['tag'])):
                    # this one sits in the opening. Slide it along its own
                    # panel until it clears - the alternative, giving the port
                    # a bore of extra lead, moves the whole coil and was what
                    # made the cheek cross itself.
                    # Along the panel first, then back the other way: on a
                    # short panel -- and the tightest here run 12 to 19mm -- a
                    # whole bore forward is off the end of it.
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
            # With one port the tail lead is clear by construction and 0.22
            # along it is the answer. With a port at EACH end nothing is clear
            # by construction, so the candidates are tried and tested rather
            # than picked: the tail lead first, to keep the one-port sheets
            # byte-identical, then the mouth lead, then further in along each.
            ends = [(_c[-1], _c[-2]), (_c[0], _c[1])] if PORT else [(_c[0], _c[1])]
            placed = False
            for a0, a1 in ends:
                ang = math.atan2(a1[1] - a0[1], a1[0] - a0[0])
                for t in (0.22, 0.12, 0.35, 0.5, 0.75):
                    gx = a0[0] + (a1[0] - a0[0]) * t + dx
                    gy = a0[1] + (a1[1] - a0[1]) * t + dy
                    if not _fouls_at(gx, gy, ang, 2.6, 1):
                        m += label('0', gx, gy, 2.6, ang)
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                # Same rule as a panel's tag: an unnumbered cheek beats a
                # number in a hole, and it is counted rather than silent.
                _dropped.append('0')
            if _dropped:
                print(f'  note: {len(_dropped)} cheek label(s) left off, '
                      f'{", ".join(_dropped)} -- no clear spot beside the port. '
                      f'The panels carry the same tags.')
            return m
        cheek_slots = [sl for q in parts for sl in slots_for(q)]
        cheek_slots.extend(mine)
        out.append({'outline': cheekpoly,
                    'slots': cheek_slots,
                    'marks': cheek_marks,
                    'note': ('the cheek - CUT THIS SHEET TWICE'
                             if not PORT_PER_CHEEK else
                             f'cheek {"AB"[k]} - CUT THIS SHEET ONCE - carries '
                             + (f'the port on facet {PORT_AT[k]}'
                                if PORT_AT is not None else
                                f'the {"mouth" if k == 0 else "far end"} port'))})
    pan = []
    for q in parts:
        w = q['len'] + BURN
        h2 = (BORE + 2 * THICK + BURN) / 2
        poly = [(px + w / 2, py + h2) for px, py in panel(q['len'], q.get('teeth'))]

        def panel_marks(dx, dy, _t=q['tag'], _w=w, _h=h2):
            return label(_t, _w / 2 + dx, _h + dy, 3.2)
        pan.append({'outline': poly, 'slots': [], 'marks': panel_marks})
    for _ in range(caps()):
        # On the PANELS sheet, and that is not a detail. The cheek sheet is cut
        # twice and sheet() says in bold that nothing else may be on it; one
        # cap put there comes back as two, and the sheet stops meaning "run
        # this file twice and you are done".
        cw = ch = 2 * THICK + BORE + BURN
        poly = [(px + cw / 2, py + ch / 2) for px, py in cap()]
        # No number. Every tag in this file is a position along the flow and
        # the cap has none; borrowing the next hex would give it a name that
        # reads like a panel. It is the only square on the sheet.
        pan.append({'outline': poly, 'slots': [], 'marks': lambda dx, dy: []})
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
            for ring in contours(it['outline']):
                cuts.append(path([(q[0] + dx, q[1] + dy) for q in ring]))
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
            f'side taken out of the slot and never off the tab. '
            # The one thing about a narrow sheet an operator cannot see in the
            # drawing and must not find out at the bench.
            + (f'NARROW: the cheek is only as wide as the duct, so every '
               f'mortice is open at the rim and each tab is held across its '
               f'thickness on one side only. ' if NARROW else '')
            # The cap carries no number, so the sheet has to say what the one
            # square on it is and that it is glued rather than tabbed.
            # The one-cap sentence is REPRODUCED WORD FOR WORD, not
            # regenerated from a count. Every shipped ported sheet carries it,
            # and all-gates.sh compares those sheets byte for byte -- a tidier
            # phrasing that says the same thing rewrites twenty-two files that
            # were cut from. Only the two-cap case is new text.
            + ('' if not CAP else
               f'The plain {2 * THICK + BORE:g}mm square on the panels '
               f'sheet is the end cap: it glues over the open end of the duct '
               f'so the air turns into the port, it carries no number, and '
               f'ONE is needed. ' if caps() == 1 else
               f'The two plain {2 * THICK + BORE:g}mm squares on the panels '
               f'sheet are the end caps: each glues over one open end of the '
               f'duct so the air turns into its port, they carry no number, '
               f'and BOTH are needed. ')
            + f'blue #0000ff '
            f'engraves, orange #ff8000 cuts the slots first, black #000000 '
            f'frees the parts.</desc>\n'
            + grp(marks, MARK, 'numbers') + grp(holes, INNER, 'slots')
            + grp(cuts, CUT, 'outlines') + '</svg>\n')
        if write:
            open(path_here, 'w').write(body)
        written.append((os.path.basename(path_here), W, H, len(placed), note))

    # Each cheek gets its OWN sheet, never two on one: the x2 sheet is cut
    # twice and sheet() says in bold that nothing else may share it, and under
    # --port-per-cheek the same rule applies for a sharper reason -- two
    # different parts on one sheet would be cut in pairs and you would have two
    # of each where you want one of each.
    groups = ([('cheek-x2', cheeks, cheeks[0]['note'])] if len(cheeks) == 1
              else [(f'cheek-{"ab"[i]}', [ck], ck['note'])
                    for i, ck in enumerate(cheeks)])
    for gname, items, note in groups + [('panels', panels, 'the wall panels')]:
        sheets = pack(items)
        for n, placed in enumerate(sheets, 1):
            tail = f'-sheet{n}' if len(sheets) > 1 else ''
            write_sheet(placed, f'{stem}-{gname}{tail}-cut-files{ext}', note,
                        n, len(sheets))
    return written, ink, cut_slots


def rotatable(cheekpoly, parts, cline):
    """Is cheek B cheek A turned half a turn? Worst mismatch in mm, or None.

    REPORTED, NOT CHECKED, exactly as flippable() is: neither answer is a
    fault. It matters because when the answer is yes the two sheets
    --port-per-cheek writes are the same part twice, and you may cut either
    one of them twice and turn one round instead -- at the price of engraved
    numbers that read upside down on the one you turned. That is a choice for
    whoever is at the machine, and it needs the number to make it.

    The centre is the midpoint of the two ports, not the origin: a shape can be
    point-symmetric about somewhere other than where its coordinates happen to
    be centred, and assuming the origin would report a false no.

    Matched as a bijection between nearest points, for the reason flippable()
    spells out at length -- zipping two sorted lists answers this question
    backwards under a perturbation of a few hundredths.
    """
    ports = port_holes(cline)
    if len(ports) != 2:
        return None
    def ctr(P):
        q = P[:4]
        return (sum(x for x, _ in q) / 4, sum(y for _, y in q) / 4)
    (ax, ay), (bx, by) = ctr(ports[0]), ctr(ports[1])
    ox, oy = (ax + bx) / 2, (ay + by) / 2
    def turned(pts):
        return [(2 * ox - x, 2 * oy - y) for x, y in pts]
    def worst(A, Bb):
        rem, w = list(range(len(Bb))), 0.0
        if len(A) != len(Bb):
            return None
        for q in A:
            j = min(rem, key=lambda k: math.hypot(q[0] - Bb[k][0],
                                                  q[1] - Bb[k][1]))
            w = max(w, math.hypot(q[0] - Bb[j][0], q[1] - Bb[j][1]))
            rem.remove(j)
        return w
    mort = [q for p in parts for sl in slots_for(p) for q in sl]
    ws = [worst(cheekpoly, turned(cheekpoly)),
          worst(mort, turned(mort)),
          worst(ports[0][:4], turned(ports[1][:4]))]
    if any(w is None for w in ws):
        return None
    return max(ws)


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
    # Two lists, because the port is a hole and not a mortice. Everything that
    # asks "is this hole clear of the edge" wants both; the one thing that asks
    # "does this mortice lie ON the edge" wants only the mortices.
    mortices = [sl for p in parts for sl in slots_for(p)]
    allslots = mortices + port_holes(c)
    # A narrow cheek puts two corners of every mortice ON the rim, and inside()
    # is an even-odd ray cast, which answers a point on the boundary either way
    # depending on which side of a vertex the ray leaves. Run as it stands it
    # called 170 of 220 slots outside the cheek they are flush with. On the rim
    # is not outside it: a tab still has a hole to enter. So under --narrow a
    # corner within half a kerf of the rim counts as in, and a corner genuinely
    # beyond it still does not.
    def held(pt):
        if inside(cheekpoly, *pt):
            return True
        return NARROW and min(
            pt_seg(pt, cheekpoly[i - 1], cheekpoly[i])
            for i in range(len(cheekpoly))) <= BURN / 2
    off = sum(1 for sl in allslots for pt in sl if not held(pt))
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
    # `pairs` in the verdict, for the reason this function's own docstring gives:
    # a check that measured nothing printed the same clean run as one that
    # measured everything. Three of the notes here -- this one, the kerf one
    # below and the panel one after it -- compared a failure count to zero with
    # nothing asserting there had been anything to count.
    note(bool(pairs) and bad == 0, 'no two slots overlap',
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
        # the same nanometre as teeth_kept(), and for the same reason: a
        # round-ported lead leaves 1.500000mm against 1.5mm asked for, and
        # the two have to agree or one refuses what the other kept
        if g - BURN < MIN_FEATURE - 1e-9:
            tight += 1
    # With no pair to measure, `worst` stayed at infinity and the note passed
    # reading "narrowest infmm drawn, infmm left after a 0.13mm kerf" -- a
    # sentence that cannot be true of any drawing.
    note(bool(pairs) and tight == 0, 'the ply between two holes survives the kerf',
         f'narrowest {worst:.3f}mm drawn, {worst - BURN:.3f}mm left after a '
         f'{BURN:g}mm kerf, against {MIN_FEATURE:g}mm needed'
         if pairs else 'no two holes to measure between')

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
    note(npair > 0 and jam == 0, 'no two wall panels share plan area',
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
    # The count half of this verdict is the half that has earned its place: it
    # is what said "16 slots on a sheet that has 32" and exposed a check
    # comparing two spaces that could not overlap. So it is kept and made
    # right rather than dropped. Under --port-per-cheek the mortices are drawn
    # on BOTH cheek sheets and each carries one of the two ports, so the sheets
    # hold mortices x 2 + 2 rather than mortices + 2. Written as the general
    # sum, which is the unchanged figure when there is one cheek sheet.
    ncheek = 2 if PORT_PER_CHEEK else 1
    want = len(mortices) * ncheek + len(port_holes(c))
    note(over == 0 and len(cut_slots) == want,
         'no engraving lands in a slot',
         f'{len(ink)} points against {len(cut_slots)} slots '
         f'({len(mortices)} mortices on {ncheek} cheek sheet(s) plus '
         f'{len(port_holes(c))} port(s), so {want} expected), '
         f'{over} inside one')

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
    # over the contours as cut, not the outline as listed: on a ring cheek the
    # listed outline steps across the band at the seam, and a slot near that
    # step read it as rim.
    rim = [(r[i], r[i + 1]) for r in contours(ring) for i in range(len(r) - 1)]

    def to_rim(sl):
        return min(pt_seg(q, a, b) for q in sl for a, b in rim)
    per_slot = [to_rim(sl) for sl in allslots]
    web = min(per_slot, default=0.0)
    if NARROW:
        # There is no web to be cuttable, so asking whether it is would be a
        # check that cannot fail, and this file has a section about those. The
        # thing that CAN go wrong on a narrow sheet is the rim drifting off the
        # mortice it is supposed to lie on - a --kerf that moved slot_half()
        # while cheek_off() was computed from something else would show here as
        # a web of a few hundredths, and a rib nobody can cut is exactly what
        # --narrow exists to avoid. So measure the flushness instead. Half a
        # kerf is the tolerance because anything under it is inside one cut.
        #
        # The WORST mortice, not the closest one. Written against `web` it read
        # "the nearest of 220 slots touches the rim", which one slot satisfies
        # for all of them and which nothing this file can draw would fail. Per
        # slot and then the largest is the statement that has to hold: EVERY
        # mortice on the rim, so a cheek_off() that drifted off slot_half()
        # shows up whichever slot it drifted at.
        #
        # Mortices only. With the port in the list the ported spiral reported
        # 4.4700mm and failed a sheet whose every mortice was flush, because a
        # mouthpiece opening sits in the middle of the band and has no business
        # touching the rim. It is not unchecked, though: it keeps the web the
        # full-width sheet asks of it, 2.095mm nearer the rim than before.
        gap = max(to_rim(sl) for sl in mortices) if mortices else 0.0
        note(gap <= BURN / 2, 'the rim is flush with every mortice',
             f'furthest of {len(mortices)} mortices {gap:.4f}mm from the rim '
             f'against {BURN / 2:g}mm allowed, band {band():g}mm wide, '
             f'and every mortice open at the rim')
        if PORT:
            # the WORST of them, so a second port cannot hide behind the
            # first: with --port-both this is two numbers reported as one
            ports = port_holes(c)
            pw = min(to_rim(P) for P in ports)
            note(pw >= 1.5, 'the port keeps a cuttable web',
                 f'{len(ports)} port(s), narrowest port to rim {pw:.3f}mm '
                 f'against 1.5mm needed')
    else:
        note(web >= 1.5, 'the web outboard of a slot is cuttable',
             f'narrowest slot to rim {web:.3f}mm against 1.5mm needed, '
             f'band {band():g}mm wide')

    # --- no cut line runs through the airway. Every edge of the cheek as cut
    # has to stand at least half a bore off the centreline, except where an open
    # shape's outline closes across its own tail -- that edge IS the end of the
    # duct. Written for the slit every ring cheek carried across its band at the
    # seam: 13 checks passed on sheets that would have come off the bed cut in
    # two places, because nothing asked where the black lines were.
    shut = math.hypot(c[0][0] - c[-1][0], c[0][1] - c[-1][1]) < 1e-9

    def off_air(q):
        dist = min(pt_seg(q, a, b) for a, b in zip(c, c[1:]))
        if not shut and min(math.hypot(q[0] - e[0], q[1] - e[1])
                            for e in (c[0], c[-1])) <= dist + 1e-6:
            return True                     # the open end of the duct
        return dist >= BORE / 2 - 1e-6
    across = sum(1 for r in contours(cheekpoly) for a, b in zip(r, r[1:])
                 for t in (0.25, 0.5, 0.75)
                 if not off_air((a[0] + (b[0] - a[0]) * t,
                                 a[1] + (b[1] - a[1]) * t)))
    n_rings = len(contours(cheekpoly))
    note(across == 0, 'no cut line crosses the airway',
         f'{n_rings} cheek contour(s), {across} point(s) inside the airway')

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
    R = bend_radius()
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
            if SHAPE in ('serpentine', 'opposed') else
            f'a closed ring of {int(round(360.0 / FACET))} facets, R{R:g} '
            f'circumradius to the centreline vertices'
            if SHAPE == 'torus' else
            f'a closed serpentine: {LOBES} lobes, a {SCALLOP_IN_DEG + 360.0 / LOBES:g} '
            f'degree bulge of R{LOBE_R:g} against a {SCALLOP_IN_DEG:g} degree '
            f'scoop of R{SCALLOP_IN_R:g}'
            if SHAPE == 'scallop' else
            f'a closed serpentine racetrack: {LOBES} half-circles a side '
            f'of R{LOBE_R:g}, alternating, joined by {RACE_STRAIGHT:g}mm '
            f'straights, and two 180 degree caps of R{RACE_CAP_R:g}'
            if SHAPE == 'racetrack' else
            f'a flattened oval: two {OVAL_FLAT:g}mm flats across the long '
            f'ends, each between two {OVAL_END_DEG:g} degree arcs of '
            f'R{OVAL_END_R:g}, joined along the sides by '
            f'{180 - 2 * OVAL_END_DEG:g} degree arcs of R{OVAL_SIDE_R:g}'
            + (f' with a {OVAL_SIDE_FLAT:g}mm straight in the middle of each'
               if OVAL_SIDE_FLAT else '')
            if SHAPE == 'oval' else
            # Unreachable: centreline() refuses an unknown shape long before
            # this. Named rather than left as a fall-through, because a
            # fall-through here is what put the deleted coupon's "one 180
            # degree bend" on every torus ever reported -- the same mistake
            # the filename chain records at the bottom of this function, made
            # twice in one function and caught once.
            _no_description())
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
        # 'half-' for --ds-half, because the two are different bores of the
        # same family and the length alone does not say which: the shipped
        # test piece has been called half-196mm since it was cut, and without
        # this the generator named it 196mm and wrote a second set beside it.
        stem = (f'ribbon-dspiral-bore{BORE:g}-{FACET:g}deg-'
                f'R{DS_R0:.0f}-pitch{DS_PITCH:.0f}-'
                + ('half-' if DS_HALF else '') + f'{L:.0f}mm.svg')
    elif SHAPE == 'volute':
        stem = (f'ribbon-volute-bore{BORE:g}-{FACET:g}deg-'
                f'R{VOL_R0:.0f}-step{VOL_STEP:.0f}-{L:.0f}mm.svg')
    elif SHAPE in ('serpentine', 'opposed'):
        stem = (f'ribbon-{SHAPE}-bore{BORE:g}-{FACET:g}deg-{LOBES}lobes'
                f'-R{LOBE_R:.0f}-{L:.0f}mm.svg')
    elif SHAPE == 'torus':
        stem = (f'ribbon-torus-bore{BORE:g}-{FACET:g}deg'
                f'-R{RADIUS:g}.svg')
    elif SHAPE == 'scallop':
        stem = (f'ribbon-scallop-bore{BORE:g}-{FACET:g}deg-{LOBES}lobes'
                f'-R{LOBE_R:g}-in{SCALLOP_IN_R:g}-{L:.0f}mm.svg')
    elif SHAPE == 'racetrack':
        stem = (f'ribbon-racetrack-bore{BORE:g}-{FACET:g}deg-{LOBES}lobes'
                f'-R{LOBE_R:g}-cap{RACE_CAP_R:g}-{L:.0f}mm.svg')
    elif SHAPE == 'oval':
        stem = (f'ribbon-oval-bore{BORE:g}-{FACET:g}deg-end{OVAL_END_DEG:g}'
                f'-R{OVAL_END_R:g}-side-R{OVAL_SIDE_R:g}-flat{OVAL_FLAT:g}'
                + (f'-sideflat{OVAL_SIDE_FLAT:g}' if OVAL_SIDE_FLAT else '')
                + f'-{L:.0f}mm.svg')
    else:
        # Unreachable: centreline() refuses an unknown shape long before this.
        # Named anyway rather than left as a silent fall-through, because a
        # fall-through here is exactly what used to put the coupon's name on
        # anything that reached the end of the chain.
        raise ValueError(f'no filename rule for --shape={SHAPE}.')
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
    if PORT_BOTH:
        # Same rule a third time. A two-port cheek differs from the one-port
        # sheet by one more hole and, under --port-square, by two more panels
        # folded away - and an operator picking a file out of a folder cannot
        # count holes in a thumbnail. "both" sits straight after "ported",
        # before "square", so the tail still sorts.
        stem = stem[:-4] + '-both.svg'
        if OUT and 'both' not in os.path.basename(OUT):
            raise ValueError(
                f'--port-both with --out={OUT} would write the two-port '
                f'sheets under a name that does not say so, over the one-port '
                f'twin. Put "both" in the --out name.')
    if PORT_AT is not None:
        # Same rule as "both", and the reason is the same one: two ported
        # sheets of one shape differ by nothing an operator can see in a
        # thumbnail except which facet the hole is on, and that is exactly the
        # thing this flag varies. The facets go IN the name.
        tag = 'at' + '-'.join(str(i) for i in PORT_AT)
        stem = stem[:-4] + f'-{tag}.svg'
        if OUT and tag not in os.path.basename(OUT):
            raise ValueError(
                f'--port-at with --out={OUT} would write sheets whose ports '
                f'are on facets {PORT_AT} under a name that does not say so, '
                f'over the sheets of another placement. Put "{tag}" in the --out '
                f'name.')
    if MERGE_LEAD and not PORT_SQUARE:
        # A merged lead is two panels fewer and two longer, which is a
        # different part set from the plain design under a name that would not
        # say so. --port-square does not need this because "square" already
        # means merged - it is the only reason the merge exists.
        stem = stem[:-4] + '-merged.svg'
        if OUT and 'merged' not in os.path.basename(OUT):
            raise ValueError(
                f'--merge-lead with --out={OUT} would write a sheet with two '
                f'panels merged under a name that does not say so, over the '
                f'unmerged twin. Put "merged" in the --out name.')
    if PORT_SQUARE:
        # Same rule again, and the same reason: a square-ported cheek takes a
        # mouthpiece the 7 x 14 one will not, and the two sheets are otherwise
        # hard to tell apart. "square" sits between "ported" and "narrow", so
        # the tail still sorts.
        stem = stem[:-4] + '-square.svg'
        if OUT and 'square' not in os.path.basename(OUT):
            raise ValueError(
                f'--port-square with --out={OUT} would write the square-'
                f'ported sheets under a name that does not say so, over the '
                f'7 x 14 twin. Put "square" in the --out name.')
    if NARROW:
        # Same argument as --port, and the mistake would be worse: a narrow
        # cheek differs from its twin by one contour and by nothing an
        # operator can see in a thumbnail, while the joint it makes is a
        # different joint. It gets its own name, and --out has to say so.
        stem = stem[:-4] + '-narrow.svg'
        if OUT and 'narrow' not in os.path.basename(OUT):
            raise ValueError(
                f'--narrow with --out={OUT} would write the narrow sheets '
                f'under a name that does not say so, over the full-width '
                f'twin. Put "narrow" in the --out name.')
    out_path = OUT or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), stem)
    written, ink, cut_slots = sheet(parts, cheekpoly, c, out_path, write)
    turn = flippable(cheekpoly, parts)
    if PORT_PER_CHEEK:
        spin = rotatable(cheekpoly, parts, c)
        print(f'\n  the two cheeks are DIFFERENT parts: '
              + (f'cheek A carries the port on facet {PORT_AT[0]}, cheek B '
                 f'the one on facet {PORT_AT[1]}.'
                 if PORT_AT is not None else
                 f'cheek A carries the mouth port, cheek B the far one.'))
        print('  ' + (
            f'  (they are the same part half a turn apart, to '
            f'{spin:.0e}mm -- so one sheet cut twice with one turned round '
            f'would do, at the price of numbers upside down on it)'
            if spin is not None and spin < 1e-6 else
            f'  (not the same part at any angle, so both sheets are needed)'))
        print('    the mouthpiece enters one FACE and the bell leaves the '
              'other'
              # The rim-end sentence is an OPEN RUN's sentence. A closed ring
              # has no rim ends to cap, and under --port-at an open run's rim
              # ends are not the ported ones either -- saying "capped" there
              # would be telling an operator to close the wrong two holes.
              + ('.' if PORT_AT is not None or SHAPE == 'torus'
                 else '; both rim ends are capped.'))
    else:
        print(f'\n  the two cheeks are identical, and go on the same way up.')
        print('  ' + (f'  (geometrically one could be flipped and turned '
                      f'{turn:g} deg, but its numbers would then read mirrored '
                      f'and face into the bore)' if turn is not None
                      else '  (a flipped cheek meets no tab at any angle)'))
    print(f'\n  {len(parts)} wall panels + 2 cheeks'
          # Same rule: the one-cap line is the shipped sheets' own wording.
          + ('' if not CAP else ' + 1 end cap' if caps() == 1
             else f' + {caps()} end caps')
          + f' = {len(parts) + 2 + caps()} parts, '
          f'{len(written)} sheet{"s" if len(written) > 1 else ""}')
    for name, w, h, k, note in written:
        # The note was carried all the way here and then dropped. It goes into
        # the sheet's own <title> and <desc>, so it was not lost -- but one of
        # the two notes is "CUT THIS SHEET TWICE", which is the single thing an
        # operator has to know before starting, and the terminal listing said
        # only how many parts were on it and how big it was.
        print(f'    {name:<62}{k:>3} parts  {w:.0f} x {h:.0f}mm  {note}')
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


# THE FLAGS, READ IN ONE PLACE. --name=value flags and the globals they set.
#
# This table was written out THREE times inside __main__ and a fourth in
# ribbon_view.py, and the copies differed in the one way a copy can: this file
# ignored a flag it did not know, so --lobe-radius=50 built the default R71.754
# lobe and said nothing, while the viewer refused the same line. The viewer now
# calls read_flags() and has no table of its own.
FLAGS = {
    'out': ('OUT', str), 'shape': ('SHAPE', str), 'bore': ('BORE', float),
    'facet': ('FACET', float), 'radius': ('RADIUS', float),
    'lobes': ('LOBES', int), 'lobe-r': ('LOBE_R', float),
    'rise': ('RISE', float), 'lead': ('LEAD', float), 'web': ('WEB', float),
    'wave-rise': ('WAVE_RISE', float),
    'wave-trough-r': ('WAVE_TROUGH_R', float),
    'wave-crest-r': ('WAVE_CREST_R', float),
    'wave-lead-r': ('WAVE_LEAD_R', float),
    'spiral-facets': ('SPIRAL_FACETS', int),
    'spiral-ri': ('SPIRAL_RI', float), 'spiral-ro': ('SPIRAL_RO', float),
    'ds-pitch': ('DS_PITCH', float), 'ds-r0': ('DS_R0', float),
    'ds-facets': ('DS_FACETS', int), 'ds-cross-r': ('DS_CROSS_R', float),
    'vol-r0': ('VOL_R0', float), 'vol-step': ('VOL_STEP', float),
    'vol-semis': ('VOL_SEMIS', int), 'vol-cross-r': ('VOL_CROSS_R', float),
    'sheet': ('SHEET', float), 'kerf': ('BURN', float),
    'scallop-in-r': ('SCALLOP_IN_R', float),
    'scallop-in-deg': ('SCALLOP_IN_DEG', float),
    'race-cap-r': ('RACE_CAP_R', float),
    'race-straight': ('RACE_STRAIGHT', float),
    'oval-end-r': ('OVAL_END_R', float),
    'oval-end-deg': ('OVAL_END_DEG', float),
    'oval-side-r': ('OVAL_SIDE_R', float),
    'oval-flat': ('OVAL_FLAT', float),
    'oval-side-flat': ('OVAL_SIDE_FLAT', float),
    'port-from-tip': ('PORT_FROM_TIP', float),
    'port-at': (None, str),             # read below: a list, and refused alone
}
SWITCHES = ('port', 'ds-half', 'narrow', 'port-square', 'port-both',
            'port-per-cheek', 'merge-lead', 'cap', 'no-write')


def read_flags(a):
    """Set the design from a command line, or refuse it in a sentence.

    Every flag this file knows is in FLAGS or SWITCHES; anything else is an
    error rather than a no-op. Called by __main__ here and by ribbon_view.py,
    so a page and the sheets it belongs to are built from one reading of one
    line, refusals included.
    """
    global PORT, DS_HALF, NARROW, PORT_SQUARE, PORT_BOTH, PORT_AT
    global PORT_PER_CHEEK, MERGE_LEAD, CAP, LOBE_R, RISE, FACET
    global PORT_ACROSS, PORT_ALONG
    for x in a:
        name, eq, v = x[2:].partition('=') if x.startswith('--') else ('', '', '')
        if not (name in FLAGS and eq) and not (name in SWITCHES and not eq):
            raise SystemExit(
                f'error: {x} is not a flag this generator reads. It takes '
                + ', '.join(f'--{f}=' for f in FLAGS) + ' and '
                + ', '.join(f'--{f}' for f in SWITCHES) + '.')
    for flag, (var, cast) in FLAGS.items():
        hit = [x for x in a if x.startswith(f'--{flag}=')]
        if len(hit) > 1:
            raise SystemExit(f'error: --{flag} is given twice.')
        if not hit or var is None:
            continue
        try:
            globals()[var] = cast(hit[0].split('=', 1)[1])
        except ValueError:
            raise SystemExit(f'error: {hit[0]} is not a '
                             f'{"whole number" if cast is int else "number"}.')
    # per-shape defaults, and only where the caller has not spoken
    if SHAPE == 'opposed':
        if not any(x.startswith('--lobe-r=') for x in a):
            LOBE_R = OPPOSED_R
        if not any(x.startswith('--rise=') for x in a):
            RISE = OPPOSED_RISE
    # FACET defaults to 30, and the wave and the spirals are
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
    NARROW = '--narrow' in a
    PORT_SQUARE = '--port-square' in a
    PORT_BOTH = '--port-both' in a
    PORT_AT = None
    PORT_PER_CHEEK = '--port-per-cheek' in a
    hit = [x for x in a if x.startswith('--port-at=')]
    if hit:
        try:
            PORT_AT = [int(v) for v in hit[0].split('=', 1)[1].split(',') if v != '']
        except ValueError:
            raise SystemExit(f'error: {hit[0]} is not a comma-separated list '
                             f'of facet numbers.')
        if not PORT_AT:
            raise SystemExit('error: --port-at= names no facet at all. Give '
                             'it one index per port, e.g. --port-at=0,6.')
    # --port-square implies the merge ONLY where the ports are on leads. The
    # merge exists for one reason -- a 20mm lead panel carries a single tooth
    # dead centre, exactly where a bore-square port wants to be -- and
    # --port-at puts no port on a lead. On the 800mm ring its ports sit on
    # 57.59mm panels carrying four teeth each, so teeth_kept() drops the one
    # that clashes and three remain; there is nothing to merge and, on a ring,
    # no collinear neighbour to merge into. Forcing it there made
    # --port-square refuse every ring by way of merge_lead's own correct
    # refusal, which is a right answer to a question that should not have been
    # asked.
    MERGE_LEAD = '--merge-lead' in a or (PORT_SQUARE and PORT_AT is None)
    CAP = '--cap' in a
    if PORT_BOTH and not PORT:
        raise SystemExit('error: --port-both without --port draws no port at '
                         'all, at either end. Pass both.')
    if PORT_AT is not None and not PORT:
        raise SystemExit('error: --port-at without --port draws no port at '
                         'all, on any facet. Pass both.')
    if PORT_AT is not None and PORT_BOTH:
        raise SystemExit('error: --port-at and --port-both are two answers to '
                         'the same question. --port-at says how many ports '
                         'there are and which facets they sit on; --port-both '
                         'says there are two and they sit at the ends. Pass '
                         'one. Two ports at the ends is --port-both; two ports '
                         'anywhere else is --port-at=i,j.')
    if PORT_AT is not None and CAP:
        # caps() counts ported RUN ENDS, and --port-at ports none. On a ring
        # there is no open end to cap; on an open run the ends are still open
        # and still want capping, but they are no longer the ported ones and
        # caps() would draw the wrong number. Refuse rather than guess.
        raise SystemExit('error: --cap counts ported run ends and --port-at '
                         'ports none of them. A closed ring has no open end '
                         'to cap; an open run under --port-at has two, and '
                         'neither is a port. Cap them by hand or say what the '
                         'rule should be.')
    if PORT_PER_CHEEK and PORT_AT is not None and len(PORT_AT) != 2:
        # "AB"[k] and the A/B report have exactly two names in them, and
        # items_for() makes one cheek per port under this flag.
        raise SystemExit(f'error: --port-per-cheek splits the ports between '
                         f'TWO cheeks and --port-at names {len(PORT_AT)}. '
                         f'There are two cheeks.')
    if PORT_PER_CHEEK and PORT_AT is None and not PORT_BOTH:
        raise SystemExit('error: --port-per-cheek without --port-both has one '
                         'port and two cheeks, so there is nothing to split. '
                         'It exists to put the two ports on different sheets.')
    if CAP and not PORT:
        raise SystemExit('error: --cap without --port closes the only opening '
                         'the bore has. The cap exists so a PORTED bore stops '
                         'breathing through its mouth; with no port there is '
                         'nothing left to breathe through.')
    if PORT_SQUARE:
        # After --bore has been read, so --bore=12 gives a 12mm square port.
        PORT_ACROSS = PORT_ALONG = BORE
        if not PORT:
            raise SystemExit('error: --port-square without --port draws no '
                             'port at all. Pass both.')


def bend_radius():
    """The tightest arc the centreline is built from, as a report quotes it.

    ONE table, read by main()'s report and by ribbon_view.py's panel. It was
    written twice, once in each, and both fell through to RADIUS -- the torus
    circumradius, R30 by default -- for any shape not listed, so the scallop
    (R40) and the racetrack (R22) were both reported as R30 on their pages and
    in the terminal.

    For the spiral this is its inner radius; the page quotes the range.
    """
    if SHAPE == 'wave':
        return min(WAVE_LEAD_R, WAVE_TROUGH_R, WAVE_CREST_R)
    if SHAPE == 'spiral':
        return min(SPIRAL_RI, SPIRAL_RO)
    if SHAPE == 'dspiral':
        return DS_CROSS_R
    if SHAPE == 'volute':
        return VOL_CROSS_R
    if SHAPE in ('serpentine', 'opposed'):
        return LOBE_R
    if SHAPE == 'scallop':
        return min(LOBE_R, SCALLOP_IN_R)
    if SHAPE == 'racetrack':
        return min(LOBE_R, RACE_CAP_R)
    if SHAPE == 'oval':
        return min(OVAL_END_R, OVAL_SIDE_R)
    return RADIUS                       # torus, and a traced bore


if __name__ == '__main__':
    # a geometry that cannot be built is an answer, not a crash
    a = sys.argv[1:]
    read_flags(a)
    try:
        sys.exit(main(write='--no-write' not in a))
    except ValueError as e:
        print(f'error: {e}')
        sys.exit(1)
