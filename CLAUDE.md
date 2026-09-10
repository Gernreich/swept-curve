# CLAUDE.md


**The README is gone.** Every `README.md` and `index.html` under `trumpet/` was
removed on 2026-09-05, pending one new writeup for the trumpet as a whole once
the renaming and reorganising is finished. Git has them all. Until it exists,
this file is the documentation, and any recipe below that renders or audits a
README is waiting on that writeup rather than describing something present.

**Every sheet kept here is 10mm.** `--bore` is untouched and takes any value; nothing
is shipped at another.

**The octagonal work left this repository on 2026-09-05** - the torus and the traced
octagonal trumpet, their two viewer pages, and the trace they were drawn from. They are
not in git at all now. `--shape=torus` and `--trace=` stay, because they are general and
the next closed ring or measured curve will want them.

## Working in this repository

A laser-cutting build repository. `ribbon_bore.py` is the generator and the
authority; the SVG beside it is its output and is regenerated, not edited.
Everything is 3mm birch on an xTool P2S.

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

**Constant-radius arcs** — `coupon`, `serpentine`, `opposed`, `wave`, `spiral`,
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
centred on the offset line, so offsetting to `BORE/2` puts the wall *faces* at
`(BORE - THICK)/2` and the airway comes out **`BORE - THICK`** wide. This
generator did exactly that until 2026-09-03: a bore asked to be 10 x 10 was cut
**7 x 10**, 70mm2 against 100. Reported by the author from a measurement of a
finished part.

**The check did not catch it because the check was wrong in the same way.** It
measured the distance between the two offset polylines and called that the
bore. It now subtracts one wall thickness and is named *the airway is the bore
along every facet*, which is the thing that matters — a check named for the
quantity it measures is harder to write against the wrong one.

The height was right throughout: a panel's shoulders bear on the cheeks' inner
faces, so shoulder-to-shoulder is the bore. Only the width was wrong, which is
why the measured section was 10 x 7 and not 7 x 7.

`wall_off()`, `cheek_off()` and `band()` are **functions**. They were constants
for one run, and a `--bore` on the command line kept the default figure — caught
immediately by the corrected airway check reporting the whole difference as error,
which is what a check named for its quantity buys you.

## What limits a bend, and it is not what you would guess

The inner wall is the centreline offset inward by `bore/2`, so there is no bore
at all below `R = bore/2`. **But the tooth runs out long before the geometry
does.** A ribbon/Boxes.py tooth is `2 × thickness` and does *not* scale with the bore —
the same fact that forced `pin_width()` in `bore_split.py` to floor at the
tooth. At the 10mm bore and 30° facets:

    R 15   inner panel 5.09mm   shorter than one tooth
    R 20   inner panel 7.67mm   still no room for shoulders
    R 25   inner panel 10.26mm  fits, 2.13mm shoulders

R 25 is why this coupon is R 25. Coarser facets need less radius, finer facets
need more: 20° wants R 35, 15° wants R 45. `build()` refuses rather than
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
pivots about the tab and the seam opens. Every coupon panel is short enough to
want exactly one, so the coupon's cut geometry did not move when this arrived —
checked by comparing the cut groups as position-independent shapes, which is
the only comparison that means anything once the packer may have reordered
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
because that mistake was made and cut. The volute's openings come out 135
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

## The cheek gets its own file, and that file is cut twice

The two cheeks are the same part, so one file run twice is the whole job -
**but only if nothing else is on that sheet.** `pack()` used to fill the second
cheek's sheet with panels, so cutting one sheet twice left you thirteen panels
short with nothing to notice it but counting. `items_for()` emits ONE cheek and
`sheet()` packs cheeks and panels as separate groups:

    ...-ribbon/cheek-x2-cut-files.svg     one cheek. Cut it twice.
    ...-ribbon/panels-cut-files.svg       every wall panel. Cut once.

`x2` is the bell's convention - `bell-round10-...-x3-...` means three plies -
so the count of copies lives in the name, where a reader looking at a folder
finds it.

It also nests better: the serpentine went from three sheets to two, because the
panels no longer have to fit around a cheek.

## One sheet per bedful

`pack()` row-wraps into `BED - 2 x margin`, not into the bed. Filling to the
edge produced a sheet **600 x 307 on a 600 x 308 bed** — passes a fits-the-bed
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
reports it and does not guess. The coupon's U *is* congruent to its own mirror:
turn it over, rotate 180 degrees, and every tab lands. The serpentine is not, at
any angle. The instruction is the same either way, because a flipped cheek
carries its numbers mirrored and facing into the bore - so one cheek always has
its numbers on the inside, which is the cheaper of the two mistakes.

That was documented backwards until 2026-09-03, on the strength of a test that
zipped two sorted point lists. **Sorting is unstable under a small
perturbation**: two nearly equal points swap order and every pair after them is
compared with the wrong partner. A 0.025mm difference read as 20.7mm of error
and answered the question the wrong way round. `flippable()` matches nearest
points as a bijection instead.

## The cheek stops 2mm outboard of its slots

`WEB`, not `MARGIN`, is the number to change — `MARGIN` is derived from it.
The band is `bore + 2 × (thickness/2 + WEB)`: 17mm at the 10mm bore. Asked for
"as thin as possible" and 2mm is the answer that still cuts; 1.5mm is the floor
in 3mm birch.

The knock-on is that there is no flange left to engrave on, so the cheek's
panel numbers moved **into the channel**, which is the floor of the bore. Two
checks hold that: no engraved point off its own part, and none inside a slot.

## The flat gate applies here, with one flag

`flat-part-check.py` reads these sheets since stroke inheritance was fixed on
2026-09-09, and it is worth running -- it is what found the port cutting into a
tab slot, which every check in this file had passed. Run it as

    python3 $G/flat-part-check.py --dir . --min-edge 1.5

**The flag is not optional.** Its default floor is 3.0mm because it was written
for a bullroarer's cord hole, which is under string tension and tears out; a
cheek slot is not. Without it every ported cheek fails at 1.66mm against 3.00
and the noise hides anything real. With it they pass 18 checks, 0 failed.

Two of its checks do not apply to these files at all. *holes are inside the
outline* assumes one part per sheet, and a panels sheet carries twenty; *hole is
big enough* then measures the gaps between parts. Read those two as noise here.

## Every check, audited against geometry it should reject

Done 2026-09-08, after the dspiral halftest was cut and its panel corners
jammed at every mitre with eleven checks passing. The method: give each check
something it ought to fail, and see whether it does. A check nobody has watched
fail is a check nobody has tested.

**Effective — observed to fail on bad geometry:**

- *the ply between two holes survives the kerf* — 0.030mm where 1.5mm is
  needed, on every ported cheek in the project. The best-evidenced check here:
  it is not a mutation that makes it fail but the shipped design, and it is
  what refuses a port that would break into a tab slot.
- *the two walls stand a bore apart* — 3mm on a hairpin tighter than its own wall
- *no two wall panels share plan area* — one jamming pair per mitre, all eight designs
- *the cheek outline does not cross itself* — four packed spirals and a tight dspiral
- *every slot corner is inside its cheek* — the wave at a R25 trough
- *the web outboard of a slot is cuttable* — the same wave, and any WEB under 1.5
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

**Asks the wrong question:** *no two slots overlap*. The audit first recorded
this as merely unreached -- eighteen mutations and none got to it. That was too
kind. On 2026-09-09 it was found passing a real defect: the port sat 0.029mm
from a slot on all ten ported cheeks, which is not an overlap and IS one hole
once a 0.13mm kerf has been down both edges. Overlap is not the question;
surviving material is. *the ply between two holes survives the kerf* now asks
that, and it is what refuses every ported design today.

A check can be worse than unproven. This one was actively wrong, and it took a
different tool -- `flat-part-check`, which had never been pointed at these files
-- to say so.

**The pattern in all three failures.** Each vacuous check compared a thing with
itself: two offsets of one polyline, a guard with its own precondition, a
constant with a constant. **A check earns its place by being watched to fail.**

## volute.py and ribbon_view.py, audited too

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

## `ribbon_view.py` draws the airway, and the ply around it

One self-contained page per design, beside the cut files it belongs to, so the
thing you cut and the thing you turn around cannot drift apart. Same flags as
the generator.

**It draws the passage, bounded by the wall faces at ±bore/2.** That is the
whole reason it exists: the bore was cut 3mm narrow for a week and nothing here
drew the space inside it. A picture of the plywood alone would not have shown
it; a picture of the airway would.

**The two cheek plates were added later**, at full band width, because the
airway on its own reads as a much thinner object than the part you cut. So a
current page has eight faces, not four — `ply, top` and `ply, bottom` after the
six airway ones. A page with only four was drawn before that and is stale.

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

**Nothing gates it.** The lesson from the stretched-lattice fork applies —
a render can be wrong while every check passes. Look at the page after changing
it.

## Previews, because a cut file is invisible on a page

`previews/` holds a readable rendering of every cut file, built by
`ribbon/lasermade-tools/make-preview.py`. Same geometry, same cut order, thicker
strokes, and the three inks that fail contrast on a light ground darkened.
Rebuild them whenever a cut file changes — verified by comparing the path data,
which must be identical to the source.

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
python3 ribbon_bore.py                 # cut file + the checks
python3 ribbon_bore.py --no-write      # the checks alone
python3 ribbon_bore.py --out=/tmp/x.svg   # a trial, somewhere it cannot hurt
python3 ribbon_view.py --shape=serpentine    # the page you turn

for f in ribbon-*.svg; do
  python3 $ribbon/G/make-preview.py "$f"       # previews/<name>, readable on a page
done

G=~/LaserMadeMusic/GIT/lasermade-tools
python3 $ribbon/G/md2html.py README.md index.html
python3 $ribbon/G/doc-audit.py README.md --html index.html \
    --rebuild "python3 $ribbon/G/md2html.py {md} {out}" --links
python3 $ribbon/G/svg-stroke-check.py --dir . --quiet
```

**Read the audit output before pushing.** It ends with a pass/fail tally.
