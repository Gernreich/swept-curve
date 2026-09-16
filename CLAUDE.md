# CLAUDE.md


**There is no README in this folder.** The swept curve has its own section in the
repository's writeup at `../../../../README.md`. This file is the note that sits
beside the generator.

**Every sheet kept here is 10mm.** `--bore` is untouched and takes any value; nothing
is shipped at another.

**Nothing OCTAGONAL is kept here** - no 45 degree torus, no traced octagonal
trumpet, no viewer page or trace for either. That line used to read "no torus",
and `--shape=torus` was kept on the argument that "the next closed ring will
want it". The next closed ring turned up:
`torus/ribbon-torus-bore10-27.6923deg-R128.572-800mm` is a **13-facet ring**,
ports on facets 0 and 6, one per cheek, 800.0mm of centreline. Thirteen facets
is not eight, so the octagon sentence still holds - it is the 45 degree ring
that is not kept, and the reason is that it lives in `torus-octagonal`, not
that a ring cannot live here.

`--trace=` is still kept on the original argument, unused.

## Working in this repository

A laser-cutting build repository. `ribbon_bore.py` is the generator and the
authority; the SVG beside it is its output and is regenerated, not edited.
Everything is 3mm birch on an xTool P2S.

`ribbon_bore.py` draws its own sheets rather than going through Boxes.py, but it
keeps Boxes.py's tooth: `TOOTH = 2 * THICK` at line 180, the figure Boxes.py's
`FingerJointSettings` uses, and it does not scale with the bore.
**Boxes.py is Florian Festi's**,
GPL-3.0-or-later, at <https://github.com/florianfesti/boxes>. It is an external
dependency -- a checkout of it, not a copy in this repository.

This is the **third** way these repositories cut a bore, and the three are not
variations on each other:

| | curve | section at a turn | why it exists |
| --- | --- | --- | --- |
| `../walk` (`bore_split.py`) | 90° lattice turns | +41.4% | fits a walk into a box |
| `--shape=torus` | a circle, 45° facets | +8.2% | a closed constant-section loop |
| here | any planar curve | +3.5% at 30° | constant section on a smooth curve |

## The geometry, in one paragraph

Sweep a rectangle along a curve **in a plane**, with one axis normal to that
plane, and the duct has two flat faces and two cylindrical ones. Flat cuts from
the sheet; cylindrical does not, because 3mm birch will not bend to these
radii. So the curved pair are faceted, and the facet angle is the only dial:
the section is exactly `bore × bore` along a facet and `bore² / cos(φ/2)` at
each mitre.

**The centreline polyline IS the facet plan.** There is no separate faceting
step, so there is nothing for it to disagree with. `walls()` offsets it and
asserts which side came out inner, because the sign depends on which way round
the centreline was written and getting it backwards silently swaps every panel
length in the cut list.

## Which curve each shape's vertices sit on

The centreline polyline IS the facet plan, so the only thing separating one
shape from another is where its vertices were placed. Two constructions are in
use, and they are not variants of each other.

**Constant-radius arcs** — `serpentine`, `opposed`, `wave`, `spiral`,
`volute`. The radius holds all the way across an arc and changes only at a join,
where a mitre already expects a corner. `spiral` is the classical compass
spiral: one arc per facet, the radius stepping by a fixed amount. **`volute` is
a chain of SEMICIRCLES** of stepping radius about two alternating centres —
which is the case `volute/volute.py` exists to argue.

**A smooth Archimedean spiral, sampled** — `dspiral` alone. **Its vertices sit
on `r = R0 + b*theta`, taken every FACET degrees**, so the radius differs at
every vertex and no two consecutive facets share one.

It shows in the local radius along the centreline. The shipped double spiral
has **16 distinct values, R30 to R111.6**; the shipped double volute has **6**
— its two semicircles at R94 and R64, its crossover at R22, and the vertices
where those meet.

**The two are the same skeleton on different curves.** Both wind in, cross the
eye, wind back out, and are point-symmetric so that both ends reach the rim;
the volute reuses the double spiral's crossover solver almost verbatim. Only
the curve differs, and neither can be turned into the other: the double
spiral's vertices lie on one spiral about one centre, the volute's on circular
arcs about two alternating centres. Two shapes, not two spellings of one.

Do not read that as the volute being the correct one and the double spiral a
compromise. See the note beside `DS_PITCH`: offsetting a faceted centreline is
exact whatever placed its vertices, and the airway check measures 4.1e-14mm on
the double spiral. The constant-radius argument is about offsetting a SMOOTH
curve, which nothing here does.

## The walls are offset to their FACES, not their centrelines

`wall_off()` is `(BORE + THICK)/2`. A wall is `THICK` thick and its slot is
centred on the offset line, so offsetting to `BORE/2` instead puts the wall
*faces* at `(BORE - THICK)/2` and the airway comes out **`BORE - THICK`** wide:
a bore asked to be 10 x 10 cuts **7 x 10**, 70mm2 against 100, and only a
measurement of a finished part tells you.

**A check can be wrong in the same way.** One that measures the distance between
the two offset polylines and calls that the bore agrees with that error exactly.
The check here subtracts one wall thickness and is named *the airway is the bore
along every facet*, which is the thing that matters — a check named for the
quantity it measures is harder to write against the wrong one.

The height is not at risk: a panel's shoulders bear on the cheeks' inner faces,
so shoulder-to-shoulder is the bore. Only the width is, which is why such a
section measures 10 x 7 and not 7 x 7.

`wall_off()`, `cheek_off()` and `band()` are **functions**, not constants. As
constants a `--bore` on the command line keeps the default figure — and the
airway check reports the whole difference as error, which is what a check named
for its quantity buys you.

## What limits a bend, and it is not what you would guess

The inner wall is the centreline offset inward by `bore/2`, so there is no bore
at all below `R = bore/2`. **But the tooth runs out long before the geometry
does.** A Boxes.py tooth is `2 × thickness` and does *not* scale with the bore —
the same fact that forces `pin_width()` in `bore_split.py` to floor at the
tooth. At the 10mm bore and 30° facets:

    R 15   inner panel 5.09mm   shorter than one tooth
    R 20   inner panel 7.67mm   still no room for shoulders
    R 25   inner panel 10.26mm  fits, 2.13mm shoulders

R 25 is therefore the floor at this bore and this facet angle. Coarser facets
need less radius, finer facets need more: 20° wants R 35, 15° wants R 45. `build()` refuses rather than
drawing a panel that cannot hold its tab.

## A half-circle advances 2/pi of its own length

Which is the whole reason the serpentine has three lobes and long straight
runs. A 1000mm run of half-circles wants **637mm of width** whatever the lobe
count, and the bed is 600 — dividing it finer only claws back the lead-in and
shortens the panels until they cannot hold a tooth. The straight verticals are
what make it fit, because they buy length in y where there is room.

**Solve the radius against this generator's own faceted centreline**, never
against a smooth arc: an inscribed chord is **1.14% short** of the arc it
spans, so a radius picked from the arc comes out 11mm long over a metre.

## The geometry is worked out y-up and flipped once, in flip()

SVG's y runs down, so writing y-up coordinates straight out renders the shape
upside down — a hump becomes a trough, and a cut file that does not look like
the thing it makes is a cut file you check twice. `flip()` negates y at the end
of `centreline()` and **nowhere else**, so every offset, normal, mitre and label
angle downstream is computed in the flipped space and comes out right. Glyphs
are not flipped: `label()` already draws them for SVG.

The flip reverses handedness, which broke one thing that had assumed it: the
outward direction for a panel's number was a left normal with a sign flip for
the inner wall, and that is only right for one handedness. **122 of 504 engraved
points landed off the material.** It is now measured — from the centreline
segment's midpoint out to the wall segment's — which has no handedness to get
wrong.

## Long panels get more than one tooth

`teeth(L)` gives `floor((L - 2*SHOULDER + TOOTH) / (2*TOOTH))`, alternating
tooth and gap of equal width. One tab in a 90mm straight run is a hinge: it
pivots about the tab and the seam opens. It was written so that every panel on
the short test piece then shipping still took exactly one and that sheet's cut
geometry did not move — checked by comparing the cut groups as
position-independent shapes, which is the only comparison that means anything
once the packer may have reordered
them.

## A traced centreline is kept with how it was taken

`--trace=` draws a bore from stations somebody else's drawing or script fixed,
rather than from parameters this generator holds. It exists for a curve whose
shape is written down somewhere other than here.

A trace file carries the stations **and the provenance** - where they came
from, how they were taken, and what was measured off them. A traced number
without that is a number nobody can check. `traces/volute.json` is the one kept:
six semicircles of stepping radius from `volute/volute.py`, with its closest
approach and the angle between its openings recorded beside them.

**The total turning of a trace is worth checking, and it is 0.** An opening
faces out of the tube, so the mouth faces back along the run and the bell
forwards; they are opposed when the turns cancel. 180 degrees is the wrong
answer and puts both openings on the same heading - `--shape=opposed` exists
to get it right. The volute's openings come out 135
degrees apart, and its bore comes within 7.75mm of itself, which is why it is
drawn and not cut.

A trace measured off a cut file is not exact: widths scatter, turns land a few
degrees off, and stations a few millimetres apart have to be merged against the
shortest real facet, `2*R*tan(FACET/2)`. **If the parameters ever turn up,
generate it instead and delete the trace.**

## A closed ring is a shape too

`--shape=torus` is a closed regular ring of FACET turns, and `offset()` mitres
a closed polyline's seam like any other vertex. Without that the two facets
either side of the join come out over-long - 53.35mm against 48.17 - and the
ring does not close.

At FACET 45 that is an octagon: eight facets, sitting at apothem
`RADIUS*cos(22.5)`, and offsetting by `+-bore/2` gives the two airway apothems.
`--radius` is the CIRCUMRADIUS of the centreline polygon, not an apothem, which
is the one thing to get right before comparing a ring here against a ring
measured off a cut file.

`ribbon_view.py` draws a closed loop with no mouth and no far end, because the
last station is the first.

### The seam is not a free end, and every torus ever drawn failed for it

`build()` trims each panel end back by `THICK/2*tan(phi/2)`, because a panel end
is a square cut and two neighbours meeting at a mitre otherwise jam on the
concave side before either is seated. `turn_at()` decided how far to trim, and
answered **0 at the first and last vertex** — *"a free end turns through 0"*,
which is right for a run and wrong for a ring. A closed polyline's first and
last vertex are one vertex and it turns there like any other.

So the two panels either side of the seam kept the ply the trim exists to take
off, and **`no two wall panels share plan area` failed with exactly 2 jamming
pairs — one per wall — on every torus at every facet count and every radius**.
0.37mm a panel at 13 facets, 0.62mm at 8, which is the 1.24mm the trim's own
comment quotes from the bench. `turn_at()` now wraps, the way `offset()`
already did at the seam mitre and for the same reason.

Nothing open moves: `poly[0] != poly[-1]` on a run, so it takes the old branch.
Checked rather than assumed — all six shapes, plain, `--port` and
`--port-both`, compared as geometry: **18 of 18 identical**.

### Two ports on a ring are two paths, and that is not a duct

`--port-at=i,j` puts the ports on **named facets** instead of at the two ends of
the run. Facet `i` runs from vertex `i` to vertex `i+1`, and the hole goes
`--port-from-tip` along it from vertex `i` — so `--port-at=0` **is** the mouth
port, verified identical on all six shapes, and the flag subsumes the old path
rather than sitting beside it.

It exists because a closed ring has no ends. `cline[0]` and `cline[-1]` are one
vertex on a torus, so `--port-both` put both ports 19.4mm apart either side of
the seam and nothing moved them. Almost nothing else had to learn about it: the
per-cheek split, `teeth_kept()`, the label dodge, three checks and the
narrow-rim web all read `port_holes()` and never ask where a port came from.

The list length is the port count, so it **replaces** `--port-both` rather than
joining it, and the two together are refused — each answers "how many ports and
where", and two answers is one too many. `--cap` is refused with it too:
`caps()` counts ported *run ends* and `--port-at` ports none of them.

### The port separation is the ring's tuning dial

**Two ports on a ring leave the air two paths, and here that is the point.** The
ring is a resonator with two parallel branches, not a duct, and it is not trying
to be one. Ports on facets `0` and `K` split an n-ring into `K` facets one way
and `n-K` the other, so **K is the dial** and it runs 1 to `n//2` — most
lopsided at 1, nearest balanced at `n//2`.

The 13 ring, every K it has, at both ends of its radius band. The **difference**
sets the first destructive null, `c/2d` at 343m/s, plane-wave and no end
correction — indicative, not a measurement:

| K | paths (facets) | ratio | R40 difference | null | R135 difference | null |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 / 12 | 1:12 | 210.6mm | 814 Hz | 710.8mm | 241 Hz |
| 2 | 2 / 11 | 2:11 | 172.3mm | 995 Hz | 581.5mm | 295 Hz |
| 3 | 3 / 10 | 3:10 | 134.0mm | 1280 Hz | 452.3mm | 379 Hz |
| 4 | 4 / 9 | 4:9 | 95.7mm | 1792 Hz | 323.1mm | 531 Hz |
| 5 | 5 / 8 | 5:8 | 57.4mm | 2986 Hz | 193.8mm | 885 Hz |
| 6 | 6 / 7 | 6:7 | 19.1mm | 8958 Hz | 64.6mm | 2654 Hz |

**K=6 is the least uneven split a 13 ring has, not the most**, which is worth
saying because `--port-at=0,6` reads like the natural middle and is one end of
the range. At R40 its difference is a single facet and the first null is up at
9kHz, near enough no audible branch effect at all; K=1 at R135 puts it at 241Hz,
in the playing register.

**An odd n cannot produce equal paths.** An even ring has `K = n/2` exactly
antipodal — two identical branches, in phase, the effect gone. 13 has no such K;
its closest split still differs by one facet. That is a reason to choose an odd
facet count, not an accident of having chosen one. More lopsided than 1:12 means
a bigger n: `--facet=14.4` is n=25, floor R68 (it grows as `17/(2 sin(pi/n))`),
ceiling R134, and K=1 there is 1:24 — 33mm against 782mm at R130, first null
229Hz.

Every K from 1 to `n//2` passes all twelve checks at every radius in the band,
measured at n=13 R40 and R135 and at n=25. The checks are all geometric and have
no opinion about any of this; they say it can be cut, not that it is in tune.

If a **single** path is ever wanted instead, the ring has to be blocked between
the ports, and the only block position leaving no dead side-branch is one
adjacent to both of them — which forces the ports adjacent to each other, which
is the end-based placement again. Recorded because it is the question a reader
asks at this point, not because anything here wants it.

### A ported ring's window depends on n, and the table has to say which n

**Every number in this section is from this command**, which is the thing the
first version of it left out and the reason two readers got two answers:

    python3 ribbon_bore.py --shape=torus --facet=F --radius=R \
            --port --port-at=0,K --no-write

`n = round(360/F)` facets, `K = n//2` so the ports sit opposite. A DEFAULT torus
is `--facet=30`, so n=12 and 24 wall panels; the 13 ring is
`--facet=27.6923076923`, n=13, 26 panels. **The two rings have different floors
and different ceilings**, and a table that names neither its facet angle nor its
port facets is a table about no particular ring.

| | n = 12 (`--facet=30`) | n = 13 (`--facet=27.6923076923`) |
| --- | --- | --- |
| floor | **R32.9** (R32.8 refuses, 16.98mm of facet) | **R36** (R35.5 refuses, 16.99mm) |
| ceiling | **R133**, sheet 594 x 307 | **R135**, sheet 599 x 306 |
| first refused | R134, *"a part is 289 x 289mm"* | R136, *"a part is 290 x 288mm"* |
| duct at the ceiling | 826mm | 840mm |

The FLOOR is not the bend radius and not the tooth. A port needs
`PORT_FROM_TIP + PORT_ALONG/2` = **17mm of the facet it is measured along**, and
a ring's facet is `2*R*sin(pi/n)`, so

    R >= 17 / (2 sin(pi/n))          32.84 at n=12,  35.52 at n=13

and the generator refuses below it by name — *"the port spans 3.00 to 17.00mm
along facet 0, which is 16.99mm long"* — which reads like a port problem and is
one. **Radius is the dial.** A reader reaching for `--port-at` on a default ring
(R30, 15.53mm of facet) hits this before anything else.

The CEILING is the cheek against the bed. It is one part and a disc, so the
bed's **288mm of usable height** is what runs out, not its 580mm of width. The
1000mm the shipped designs run to needs R160.7 at n=13 and a 338 x 336mm cheek;
nesting cannot save it, because the cheek is one part.

**Do not read the ceiling off the sheet size.** There are TWO bed limits and
they are measured against different things:

| | limit | set in | applies to |
| --- | --- | --- | --- |
| *the sheet* | 600 x 308 | the `every sheet fits the P2S bed` check, `w > BED_W or h > BED_H` | a finished sheet |
| *the part* | 580 x 288 | `pack()`, `use_w, use_h = BED_W - 2*margin, BED_H - 2*margin` | one part, and it is what a refusal quotes |

The part limit is the smaller because `pack()` packs into the bed **minus a
margin all round**, and its docstring says why: filling to the edge gave *"a
sheet 600 x 307 on a 600 x 308 bed, which passes a fits-the-bed check and
cannot be positioned on a real machine"*.

So a ring at its ceiling prints a sheet taller than 288 — 599 x 306 at n=13 —
and is correct, because that number is measured against 308 and not against
288. Reading `306 > 288` off that row concludes the opposite, and it is the
inference the two limits invite: the row that reports a sheet sits directly
beneath refusals that quote a part.

### `--facet=60` has no passing radius, and changes how it fails at R133

Coarsening `--facet` widens the facet and does not rescue a ring. At
`--facet=60` — n=6, so the comparable run is `--port-at=0,3` — the ring clears
the port check and fails *the web outboard of a slot is cuttable* at **0.951mm**
against the 1.5mm needed. Not a radius failure: 0.951mm at R30, R60, R120, R130
and R132 alike, because 60 degree facets put the mortices that close to the rim
whatever the ring's size.

At **R133** it stops failing that check and starts failing before any check
runs — the bed refuses the cheek outright, *"a part is 250 x 289mm"*. The
conclusion is unchanged, and R133 is the crossover: R132 reaches the checks,
R133 does not.

That is worth saying because of how the upper end reads if you count one signal.
`--facet=60 --radius=300` prints **zero FAIL lines**, and zero FAIL lines there
means zero checks, not a clean run. Every row in `all-gates.sh` asserts the PASS
count as well for exactly this reason, and its header says so: absence of bad
news is not good news.

**Both numbers in this section were wrong once for the same reason** — an
absolute written from samples that could not disprove it. "R120 is the smallest
radius that passes" came from probing only 120 and up; "the mode changes at
R150" came from probing 120 then 150 and never narrowing. Sweep across the
boundary you mean to name, not away from it.

`--facet` wants eleven decimal places for a 13 ring. The divisibility guard is
`1e-9` absolute, so `--facet=27.692307692` is refused and `27.6923076923` is
accepted. A facet *count* would be the better flag, and is not written.

## The cheek gets its own file, and that file is cut twice

The two cheeks are the same part, so one file run twice is the whole job -
**but only if nothing else is on that sheet.** A `pack()` that fills the second
cheek's sheet with panels leaves you thirteen panels short when you cut one sheet
twice, with nothing to notice it but counting. `items_for()` emits ONE cheek and
`sheet()` packs cheeks and panels as separate groups:

    ...-cheek-x2-cut-files.svg     one cheek. Cut it twice.
    ...-panels-cut-files.svg       every wall panel. Cut once.

`x2` is the bell's convention - `bell-round10-...-x3-...` means three plies -
so the count of copies lives in the name, where a reader looking at a folder
finds it.

It also nests better: the serpentine takes two sheets rather than three, because
the panels do not have to fit around a cheek.

## One sheet per bedful

`pack()` row-wraps into `BED - 2 x margin`, not into the bed. Filling to the
edge gives a sheet **600 x 307 on a 600 x 308 bed** — which passes a fits-the-bed
check and cannot be positioned on a real machine. A part bigger than the usable
area is a refusal, not a smaller sheet.

## Kerf goes opposite ways on a part and on a hole

The laser removes `BURN` centred on the line, so a part comes out `BURN` under
and a hole `BURN` over. Every panel dimension is therefore drawn `BURN` **over**
and every slot `BURN` **under**, plus `PLAY` per side taken out of the slot and
never off the tab — `bore_split.py`'s standing rule, and its 0.025mm figure for
the 10mm bore.

Measured back out of the written file rather than asserted: a 6.100mm drawn tab
and a 5.950mm drawn slot give a 6.000mm tab in a 6.050mm slot, 0.025mm a side.

## Both cheeks are the same part, and both go on the same way up

Outline, slots and engraving are identical - checked against the written files,
not assumed.

**Whether a flipped cheek would fit depends on the shape**, so `flippable()`
reports it and does not guess. A simple U *is* congruent to its own mirror:
turn it over, rotate 180 degrees, and every tab lands. The serpentine is not, at
any angle. The instruction is the same either way, because a flipped cheek
carries its numbers mirrored and facing into the bore - so one cheek always has
its numbers on the inside, which is the cheaper of the two mistakes.

**`flippable()` matches nearest points as a bijection**, and must not zip two
sorted point lists. Sorting is unstable under a small perturbation: two nearly
equal points swap order and every pair after them is compared with the wrong
partner, so a 0.025mm difference reads as 20.7mm of error and answers the
question the wrong way round.

## The cheek stops 2mm outboard of its slots

`WEB`, not `MARGIN`, is the number to change — `MARGIN` is derived from it.
The band is `bore + 2 × (thickness/2 + WEB)`: 17mm at the 10mm bore. Asked for
"as thin as possible" and 2mm is the answer that still cuts; 1.5mm is the floor
in 3mm birch.

The knock-on is that there is no flange left to engrave on, so the cheek's
panel numbers moved **into the channel**, which is the floor of the bore. Two
checks hold that: no engraved point off its own part, and none inside a slot.

## The flat gate applies here, with one flag

`flat-part-check.py` reads these sheets, and it is worth running -- it is what
catches a port cutting into a tab slot, which every check in this file passes.
Run it as

    python3 $G/flat-part-check.py --dir . --min-edge 1.5

**The flag is not optional.** Its default floor is 3.0mm because it was written
for a bullroarer's cord hole, which is under string tension and tears out; a
cheek slot is not. Without it every ported cheek fails at 1.66mm against 3.00
and the noise hides anything real. With it they pass 18 checks, 0 failed.

Two of its checks do not apply to these files at all. *holes are inside the
outline* assumes one part per sheet, and a panels sheet carries twenty; *hole is
big enough* then measures the gaps between parts. Read those two as noise here.

## Every check, against geometry it should reject

The method: give each check something it ought to fail, and see whether it does.
A check nobody has watched fail is a check nobody has tested. Eleven checks can
pass on panel corners that jam at every mitre.

**Effective — observed to fail on bad geometry:**

- *the ply between two holes survives the kerf* — the best-evidenced check here,
  because what made it fail was a shipped design rather than a mutation: 0.030mm
  where 1.5mm was needed. It is what refuses a port that would break into a tab
  slot. Nothing shipped fails it — see the note on the round port's zero margin
  below, which is why.
- *the two walls stand a bore apart* — 3mm on a hairpin tighter than its own wall
- *no two wall panels share plan area* — one jamming pair per mitre, all eight designs
- *the cheek outline does not cross itself* — four packed spirals and a tight dspiral
- *every slot corner is inside its cheek* — the wave at a R25 trough
- *the web outboard of a slot is cuttable* — the same wave, and any WEB under 1.5
- *panels merged by `--merge-lead` keep their own teeth and numbers* — not a
  check but a rule, and the reason `merge_lead()` is forty lines rather than
  four. `teeth()` reads a panel's length alone, so the 43.2mm merged panel
  would get three teeth at -12, 0, +12 where its 23.2mm half had two at -6, +6,
  and one of the three lands at 9.6mm along the duct, inside a port spanning
  3.07 to 12.94. Tags are worse: `build()` numbers by position, so dropping two
  panels renumbers all 36 that remain and a panel already cut reads a number
  that now means a different one. The label is pinned separately from the
  midpoint, or it slides half a lead off the mortices it names.
- *`--port-both` has four panels a wall to fold* — watched to fail at three and
  to pass at four, but ONLY by calling `merge_lead()` directly with a made-up
  wall. No shape reaches it from the command line: any lead that bends into its
  first facet trips the collinearity refusal first, and the shortest double
  spiral that builds at all — `--ds-half --ds-facets=1`, 160.6mm — still has
  panels to spare. Keep it: without it the two folds meet in the middle and the
  second reads a length the first has already changed, re-spacing the teeth of
  a panel whose mortices are settled. But do not read it as evidence the way
  the checks above are read. What has been watched is the function, not a
  design.
- *the rim is flush with every mortice* — `--narrow` only, in place of the web
  check, which under `--narrow` could not fail. Watched fail twice: pushing
  `cheek_off()` 0.2mm off `slot_half()` reported 0.2000mm against 0.065 allowed,
  and `--shape=serpentine --narrow` reports 1.2182mm, because a narrow rim cuts
  into twelve mortices on the tight lobe. The serpentine cannot be cut narrow,
  and the two checks that say so both refuse it and write nothing.
- *every engraved point is on its own part* — found 18 points off, the two cheek labels
- *no engraving lands in a slot* — see the section above; it has been wrong twice
  and was caught both times by the count printed beside the verdict

**Cannot fail, and should not be read as evidence:**

- *the airway is the bore along every facet* — it compares two offsets of ONE
  polyline, which are parallel to each facet at a fixed separation by
  construction. It returns the bore for a straight line, a hairpin tighter than
  its own wall, and a zigzag reversing at every vertex. Keep it: it is the
  arithmetic of the section, and it would catch a mistake in `offset()`. But the
  check that answers "is the airway the bore" is *the two walls stand a bore
  apart*, which measures the walls as bodies.
- *the shortest panel still holds a tooth* — `build()` raises on the identical
  condition before `checks()` runs, so this restates a guard that has already
  fired. The number it prints is real; the verdict is not.
- *every sheet fits the P2S bed* — `sheet()` raises on an oversized part first.
  Every attempt to make a sheet overflow tripped that instead.

**Asks the wrong question:** *no two slots overlap*. Eighteen mutations never
reach it, and it passes a real defect: a port 0.029mm from a slot is not an
overlap, and IS one hole once a kerf has been down both edges. Overlap is not
the question; surviving material is. *the ply between two holes survives the
kerf* asks that, and it is what decides where a port may sit.

**The round port is placed hard against that limit, by construction.** `port()`
keeps a tooth only where the gap clears `MIN_FEATURE + BURN`, so the surviving
tooth lands exactly on the minimum: every round-ported design — serpentine,
opposed and the R35to113 spiral — reports 1.650mm drawn, 1.500mm left, against
1.5mm needed. A margin of **zero**, and it passes only because
the comparison carries a 1e-9 slack; without it the sum came out
1.6499999999999986 and the design was refused over 1.3e-15mm.

The square port is nothing like as tight, because `--merge-lead` gives it a
whole facet to sit in: 2.2 to 4.5mm of margin across the eight square-ported
designs, the volute narrowest at 3.736mm and the R36to144 spiral widest at
5.950mm. The eighth is the 1000mm double spiral, which is square-ported at BOTH
ends and reports the same 4.672mm at each -- `--port-both` folds the tail lead
as well, so its far port gets the whole facet the mouth's does.

## A port seats a BELL in 3mm of ply. Nothing has seated a mouthpiece in one

The stack is 16mm through and a port is cut in ONE cheek, so whatever goes into
it meets 3mm of birch and not the whole sandwich. That reads thin on paper and
it is the first thing anyone asks about this joint.

**For a bell it holds, and there is a photograph of it holding.** The R35to113
spiral is square-ported and glued up, and its bell is seated in the port — a
ring-stack shank standing up out of the plane of the coil, carried by a 10 x 10mm
hole through one 3mm cheek.

![The R35to113 spiral bore glued up in pale birch, its finger joints and
engraved panel numbers visible along every seam, with the ring-stack bell
standing vertically out of the plane of the coil where its shank seats in the
square port, and the mouthpiece on the lead at the far
end](../../../../built/ribbon-spiral-bore10-45deg-R35to113/ribbon-spiral-bore10-45deg-R35to113-1000mm-ported-square-narrow-cheek-x2-glued-up_web.jpg)

**THE MOUTHPIECE IS NOT ON A PORT ON EITHER BUILT INSTRUMENT.** Look at the
photograph again: the bell stands in the port, and the mouthpiece is out on the
lead, seated in the TUBE END where the four walls grip the full 16mm depth. The
three-turn trumpet does the same at both of its ends.

![The built three-turn trumpet laid flat: a square-section lattice bore in
scorched, shellacked birch with its finger joints alternating light and dark
along every seam, the stacked-ring mouthpiece seated in the end of the square
run at one end and the flared ring-stack bell at the
other](../../../../built/coil-fold2-long-straight-3t/bore10-coil-fold2-long-straight-3t_web.jpg)

They are different joints, and only one of the two has been asked to hold a
mouthpiece. A bell sits where it is put; a mouthpiece takes lip pressure and
whatever the player leans into it, which is the load the 3mm has never seen.
Do not read the bell in that port as settling the mouthpiece.

**SO THE 1000mm DOUBLE SPIRAL SHIPS BOTH ARRANGEMENTS**, and the folder holds
three sheet sets because of it:

    ...-1000mm-narrow-*                      no ports at all, the plain coil
    ...-1000mm-ported-square-narrow-*        ONE port, one cap, one open end
    ...-1000mm-ported-both-square-narrow-*   TWO ports, two caps, both ends shut

The one-port set is the spiral's arrangement, the one that exists in wood: the
port takes the bell, its stub is capped, and the far rim end stays open for the
mouthpiece to seat on the tube end where four walls grip 16mm. It is `--port`
without `--port-both`, and its port goes through BOTH cheeks, so one face of it
is a hole to plug — which is the cost `--port-per-cheek` exists to avoid and
which the built spiral pays.

The two-port set is the one that needs nothing plugged and puts the mouthpiece
and the bell on opposite faces. It is also the one whose mouth port has never
been made. Cut the 240mm coupon first if that is the one you want.

Each has a page of its own, because the airways differ. In
`dspiral/ribbon-dspiral-bore10-30deg-R62-pitch46-1000mm/`, the page named for
the folder is the TWO-port bore and the one whose name ends `-ported-square` is
the one-port — which is the opposite of how the sheets read, where the plainer
name is the plainer part. The page takes the folder's name because that is what
every other design does and what `ribbon_view.py` writes without `--out`.

`cap()`'s own docstring has it the other way round — *"the mouthpiece goes into
the port and the run simply stops a bore further on"* — and the built spiral
does the opposite, putting the bell there. The generator is not wrong about the
geometry, which does not care which end is which, but the sentence describes an
instrument nobody has made.

**So a change to `MIN_FEATURE`, `BURN` or `THICK` is a change to whether the
four round-ported designs draw at all**, and they will fail together rather
than one at a time. The square-ported eight have room to absorb it. Measure
after any such change rather than assuming the check is quiet because nothing
is close to it.

A check can be worse than unproven. This one was actively wrong, and it took a
different tool -- `flat-part-check`, which had never been pointed at these files
-- to say so.

**The pattern in all three failures.** Each vacuous check compared a thing with
itself: two offsets of one polyline, a guard with its own precondition, a
constant with a constant. **A check earns its place by being watched to fail.**

## volute.py and ribbon_view.py, checked the same way

**`volute.py`.** Two of its four checks are failing on the shipped design right
now — *the bore stays clear of itself* at 7.75mm against the 20mm band, and
*the two openings are opposed* at 135 degrees — which is the file's whole point
and makes them the best-evidenced checks in the repository. *the cheek fits the
P2S bed* fires from `--r0=200` up. Its two refusals hold: an arc under the tooth
floor, and a facet angle that does not divide a semicircle.

Those two failing checks are one condition stated twice, and they agree: the run
turns 1035 degrees, 315 past a whole number of turns, and an opening faces out
of the tube, so the openings sit (315 + 180) mod 360 = 135 degrees apart.

*every arc holds a tooth* cannot fail — `centreline()` raises on the same
condition first, exactly as `the shortest panel still holds a tooth` does in
`ribbon_bore.py`.

**`ribbon_view.py`.** Its guards hold: an unknown flag is refused by name, and a
shape with no title or filename exits saying to add one. The check that matters
for this file is whether it still agrees with the generator, since it has
diverged twice — it does, on all seven shapes, to the tenth of a millimetre.

One rough edge fixed: a refusal from the generator escaped as a traceback
instead of the sentence the generator wrote. `ribbon_bore`'s `__main__` has
caught `ValueError` all along; this one now does too.

## Look at the render. The checks do not see the drawing

Two defects in this generator got through every check and were caught by
screenshotting the SVG:

- **Every glyph was mirrored top to bottom.** The glyph table's y runs up and
  SVG's runs down. A `2` came out as something that is not a `2`, and no
  geometric invariant cares.
- **The cheek's own number was engraved in the hole in the middle of the arch.**
  The centre of a U's bounding box is air.

`checks()` now includes *every engraved point is on its own part*, which found
the second one immediately — 18 points off, exactly the two cheek labels. It is
there because the render found it first. **Screenshot the SVG after any change
to drawing code.**

A third, from the same family: *no engraving lands in a slot* was written
comparing ink in sheet coordinates against slots rebuilt at design
coordinates. Two spaces that cannot overlap, so it passed, and the tell was
that it said **16 slots on a sheet that has 32**. A count printed beside a
verdict is what makes that visible. Both now come out of `sheet()`, which is
the only place that knows where anything was actually put.

Then it failed the same way again once there were several sheets: it compared
ink on sheet 3 against slots on sheet 1. Two sheets are two files and their
coordinates have nothing to do with each other. Both are now tagged with their
sheet. **Twice in one file is a pattern, not bad luck: any check comparing two
sets of coordinates must first establish what space they are both in.**

Every check reports its own count (`40 stations`, `504 points`, `120 pairs`) so
a check that measured nothing cannot print the same clean line as one that
measured everything.

## `id="..."` contains `d="..."`

Measuring the output with `re.findall(r'd="([^"]+)"')` matches the `id`
attribute too and hands you `slots` where a coordinate should be. Use
`(?:^|\s)d="`. The octagonal writeup records the same trap; it still cost
a run here.

**A failing run deletes its output**, which is right — a sheet that failed a
check should not be sitting there looking cuttable. It also means a copy of
this script tried out in this folder writes to, and then deletes, the real cut
file. That happened. Use `--out` for trials.

## `ribbon_view.py` draws the airway, and nothing else

One self-contained page per design, beside the cut files it belongs to, so the
thing you cut and the thing you turn around cannot drift apart. Same flags as
the generator.

**It draws the passage, bounded by the wall faces at ±bore/2.** That is the
whole reason it exists: the bore was cut 3mm narrow for a week and nothing here
drew the space inside it. A picture of the plywood alone would not have shown
it; a picture of the airway would.

**The page draws the airway and not the cheek plates.** Drawing the plates at
full band width answers a real objection — the airway on its own reads as a much
thinner object than the part you cut — but it makes every look inside a look
through a solid slab of ply, which is the one thing this page must not make
hard. A page has six faces: the four wall-and-cheek ones, plus `mouth` and
`far end` where the bore is not a closed ring. `ply, top` and `ply, bottom` in a
key belong to no page this generator draws. What the plates would say — 20mm of
band around a 10mm passage — the numbers panel says in words and the cut files
show to scale.

**A flag missing from the `known` set is refused by the guard that reads it.**
`--trace` has its own handler forty lines below that guard, and leaving it out
of `known` makes the traced page impossible to redraw at all — while the copy in
the repository goes stale without anyone finding out. A guard listing what is
allowed has to be edited when something is added, and this is the second thing
in this file that a second copy of the argument handling can quietly lose.

It reuses `offset()` for the wall faces rather than reading the cut files, so
it cannot disagree with the generator about where anything is. It is *not* the
lattice viewer in `../../../../tools/viewer.py`: that one is built on integer cells and cube
faces with occupancy-based hidden-face removal, and there is no lattice here.

`--embed` writes a compact build for an iframe: canvas only, a caption, a slow
idle turn that stops on the first interaction and never starts under
`prefers-reduced-motion`. **The drawing code is extracted from the full page's
own `<script>` rather than copied**, so an embed cannot quietly diverge from
the page it links to. It drops three lines the embed declares for itself; the
first version sliced off the leading blank line instead, left `const D`
declared twice, and rendered a blank canvas.

`gernreich.github.io` embeds one. Regenerate it from here when the geometry
changes:

```sh
python3 ribbon_view.py --shape=serpentine --embed \
    --out=../../../../../Gernreich.github.io/bore-viewer.html \
    --home=https://gernreich.github.io/trumpet/
```

An embed follows `prefers-color-scheme`, because it sits inside somebody
else's page. It cannot see an explicit theme toggle on the host — a frame is
its own document — so it matches by default and not after a manual switch.

**all-gates.sh gates it**, by running the command above into a temp file and
comparing. It is the only artefact crossing two repositories, so without that
gate the published copy drifts from what this generator draws and nothing
reports it.

That gate compares bytes, which is not the same as looking: a render can be
wrong while every check passes. Look at the page after changing it.

## Previews, because a cut file is invisible on a page

`previews/` holds a readable rendering of every cut file, built by
`lasermade-tools/make-preview.py`. Same geometry, same cut order, thicker
strokes, and the three inks that fail contrast on a light ground darkened.
Rebuild them whenever a cut file changes — verified by comparing the path data,
which must be identical to the source.

`previews/old/` mirrors each design's `cut-files/old/` and holds the previews of
the superseded sheets. They are kept for the same reason the sheets are: a
preview is the only readable picture of what a superseded sheet cut. They sit
out of `previews/` rather than in it because `all-gates.sh` walks every
`previews/` directory and asks each file for its cut file — a preview whose
sheet has moved reads as stale, correctly, and a pile of them would drown the
one real staleness the gate exists to report.

Every `old/` in this repository is gitignored, this one
included. They are a local archive on the working disk, not part of what the
repository ships, and a fresh clone has none of them — so the pictures above
are the only readable record of the full-width sheets, and they are one disk
deep.

## Colour is the cut order

Shared across all these repositories: **blue engraves, then green → orange →
cyan → black**; black frees the part; violet `#8000ff` means skip. This sheet
uses three — blue for the numbers, orange for the slots so the cheek is cut
while the sheet still holds it, black for the outlines.

## Cut files belong to the author

- **Stage by name.** Never `git add -A` or `git add .`.
- Do not regenerate a cut file the author has hand-edited without asking.
- Commit straight to `main`. Push only when asked.

## Commands

```sh
G=~/LaserMadeMusic/GIT/lasermade-tools

# The ply is 3.0 and the kerf 0.15 by default, and bore_split.py's SHEET and
# KERF are the same two numbers. They have to agree: one instrument, one
# machine. Every sheet in this tree comes back at THOSE DEFAULTS -- no --sheet
# or --kerf needed; the sheets in each cut-files/old/ were drawn at 2.94 and
# 0.13 and need --sheet=2.94 --kerf=0.13 to come back.
#
# "at the default ply and kerf" is NOT the same as a bare `ribbon_bore.py`.
# Every shipped sheet is --narrow, so the bare run reproduces none of them: it
# draws a FULL-WIDTH double spiral and, having no --out, drops two files named
# like cut files into THIS DIRECTORY rather than into any cut-files/ -- which is
# where a stray sheet in this folder comes from. Use --no-write to run the checks,
# or --out to send a trial somewhere harmless.
python3 ribbon_bore.py --no-write      # the checks alone, writes nothing
python3 ribbon_bore.py --out=/tmp/x.svg   # a trial, somewhere it cannot hurt
python3 ribbon_bore.py --port --out=x-ported.svg   # with the mouthpiece slot;
                                       # the name must carry "ported" or it
                                       # refuses, so it cannot overwrite the
                                       # plain sheets
python3 ribbon_bore.py --port --port-square --out=x-ported-square.svg
                                       # a BORE x BORE port instead of 7 x 14.
                                       # Implies --merge-lead, because the
                                       # lead panel's one tooth sits where the
                                       # port wants to be; folding the lead
                                       # into the facet it is already collinear
                                       # with is what buys the room, and unlike
                                       # a longer --lead it moves no coil.
                                       # Size is BORE and the kerf is taken off
                                       # at draw time, so the opening is BORE
                                       # exactly at any --kerf. Never write the
                                       # 9.87 down: it is one kerf's answer
python3 ribbon_bore.py --port --port-both --port-square \
    --out=x-ported-both-square.svg     # the SAME port at both ends, not just
                                       # the mouth. Both ends are leads built
                                       # by the same tail(), so the far end
                                       # takes one on the mouth's terms; only
                                       # the count changes. Names itself
                                       # "-both" and --out must say so -- a
                                       # two-port cheek is one more hole and,
                                       # under --port-square, two more panels
                                       # folded away, and nobody counts holes
                                       # in a thumbnail. --merge-lead folds the
                                       # TAIL lead too under this flag, or the
                                       # far port lands on that lead's only
                                       # tooth and teeth_kept() refuses --
                                       # correctly. --cap then makes TWO caps,
                                       # because two ends are open.
                                       #
                                       # `--ds-half --ds-facets=2 --lead=42`
                                       # is the coupon for it, 240mm on two
                                       # sheets. It carries the SAME 42mm lead
                                       # as the shipped 1000mm design, not the
                                       # 20mm the 196mm halftest has, and that
                                       # is the point: a merged panel is
                                       # lead + facet, so a coupon at another
                                       # lead proves a different panel and puts
                                       # its teeth somewhere else. It is for
                                       # the tail fold and the far port, the
                                       # parts of this flag that are new, the
                                       # way the 196mm one is for the crossover
python3 ribbon_bore.py --port --port-both --port-per-cheek --port-square \
    --out=x-ported-both-square.svg     # the two ports SPLIT between the two
                                       # cheeks instead of each going through
                                       # both. No geometry moves -- same coil,
                                       # same panels, the same two holes in the
                                       # same two places -- only which SHEET
                                       # each hole is drawn on, and that turns
                                       # one sheet cut twice into cheek-a and
                                       # cheek-b, each cut once.
                                       #
                                       # What it buys: a port through both
                                       # cheeks is a socket right through, and
                                       # the side you are not using is an open
                                       # hole to plug. Two ports make four of
                                       # them and two are waste. One a cheek
                                       # makes two, both wanted.
                                       #
                                       # What it costs is worth saying out
                                       # loud, because it IS the instrument:
                                       # the mouthpiece enters one FACE and the
                                       # bell leaves the other. The openings
                                       # stop being in the plane of the coil,
                                       # so the total-turning-zero argument
                                       # that puts the two RIM ends on opposite
                                       # headings no longer describes how the
                                       # thing is played -- those ends are the
                                       # capped ones now.
                                       #
                                       # rotatable() REPORTS whether the two
                                       # sheets are the same part half a turn
                                       # apart, as flippable() reports its own
                                       # question and for the same reason:
                                       # neither answer is a fault. On the
                                       # double spiral they are, to 9e-16mm, so
                                       # one sheet cut twice with one turned
                                       # round would do -- at the price of
                                       # numbers upside down on the turned one,
                                       # which is why two sheets is the default
python3 ribbon_bore.py --merge-lead --out=x-merged.svg   # the merge on its own,
                                       # to look at. Names itself "-merged";
                                       # --port-square does not, because
                                       # "square" already means merged
python3 ribbon_bore.py --port --cap --out=x-ported.svg
                                       # ONE CAP PER PORTED END -- one here,
                                       # two under --port-both, and caps() is
                                       # a function for the reason band() is.
                                       # On the PANELS sheet, the
                                       # band by the stack: 15.81 x 16 narrow,
                                       # 20 x 16 not. A ported bore breathes
                                       # through the port, so the open end
                                       # needs closing or the air takes it.
                                       # Glued, unnumbered, and NOT square -
                                       # the band and the stack are unrelated
                                       # numbers that happen to be close.
                                       # Refuses without --port, which would
                                       # seal the only opening. It goes on the
                                       # panels sheet because the cheek sheet
                                       # is cut twice and would give you two
python3 ribbon_bore.py --port --port-from-tip=8 --out=x-ported.svg
                                       # move the port along the lead; the
                                       # default 10 is a bore back from the tip
python3 ribbon_bore.py --narrow --out=x-narrow.svg   # the cheek trimmed flush
                                       # to the mortices: no web, band 15.81
                                       # instead of 20, and every slot open at
                                       # the rim. Same naming rule as --port,
                                       # and for a stronger reason - the two
                                       # sheets differ by one contour and make
                                       # different joints. It is NOT --web=0,
                                       # which leaves an uncuttable 0.095mm
                                       # rib; --narrow follows the drawn slot
                                       # edge, so it tracks --kerf and --sheet
python3 ribbon_view.py --shape=serpentine    # the page you turn
python3 ribbon_view.py                       # NOT harmless. --shape defaults
                                       # to dspiral now that the coupon is
                                       # gone, and the page lands beside the
                                       # cut files it belongs to -- so a bare
                                       # run REWRITES the 1506mm double
                                       # spiral's page rather than dropping a
                                       # stray. Correct output, and it is how
                                       # the staleness below was found, but it
                                       # is not a no-op

# THE DESIGN PAGES ARE GATED, since 2026-09-15, and were not before. The embed
# gate watches the ONE page that crosses into Gernreich.github.io; the twelve
# that sit beside their cut files were watched by nothing, and ten of them were
# a viewer revision behind before anyone looked. Two were worse than behind --
# their vertices did not match the flags their folder names claim, so they drew
# a bore nobody had drawn. `design pages match their generator` rebuilds each
# into a temp and compares, which is `previews current with their cut files`
# applied to the pages instead of the sheets.

# Every current sheet, from every design folder, into the ONE previews/ here.
# `ribbon-*.svg` matched nothing once the sheets moved down into per-design
# cut-files/ folders, and make-preview.py's default output is previews/ beside
# ITS SOURCE -- so the bare loop wrote eleven scattered previews/ directories
# and left the real one stale. The output path is given explicitly for that
# reason, and -not -path '*/old/*' keeps superseded sheets out.
for f in $(find . -path '*/cut-files/*.svg' -not -path '*/old/*'); do
  python3 $G/make-preview.py "$f" "previews/$(basename $f)"
done

python3 $G/md2html.py README.md index.html
python3 $G/doc-audit.py README.md --html index.html \
    --rebuild "python3 $G/md2html.py {md} {out}" --links
python3 $G/svg-stroke-check.py --dir . --quiet
```

**Read the audit output before pushing.** It ends with a pass/fail tally.
