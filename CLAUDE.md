# CLAUDE.md

Rules for working on the swept-curve generator. The reasoning, history and
measurements behind each one are in `NOTES.md`, under the heading given in
brackets. Read that section before changing the code it names.

## What lives here

- **No README in this folder.** The writeup is the swept-curve section of
  `../../../../README.md`.
- Every sheet kept here is the **10mm bore**. `--bore` still takes any value.
- **No 45 degree ring is kept here**: it belongs to another build. The 13-facet
  torus in `torus/` is kept. `--trace=` is kept but unused.
- `ribbon_bore.py` is the authority. Its SVGs are regenerated, never edited.
  3mm birch, xTool P2S.
- `TOOTH = 2 * THICK` is Boxes.py's tooth and does **not** scale with the bore.
  Boxes.py (Florian Festi, GPL-3.0-or-later) is an external checkout, not a copy.
- `lyre_harp.py` is a separate closed-duct generator that imports from
  `ribbon_bore`. Its output goes to `~/LaserMadeMusic/GIT/lyre-harp/`, where
  nothing gates it. [`lyre_harp.py`: a closed duct whose width changes]

## Geometry rules

- The centreline polyline **is** the facet plan. Keep the assert in `walls()`
  that checks which side came out inner. [The geometry, in one paragraph]
- `dspiral` samples an Archimedean spiral and the other shapes are
  constant-radius arcs. Neither is the "correct" one.
  [Which curve each shape's vertices sit on]
- Walls are offset to their **faces**: `wall_off() = (BORE + THICK)/2`.
  `wall_off()`, `cheek_off()`, `band()` and `caps()` must stay **functions**,
  not constants, or `--bore` is ignored. [The walls are offset to their FACES]
- The tooth, not the geometry, sets the minimum bend: R25 at 30 degree facets,
  R35 at 20, R45 at 15 (10mm bore). `build()` refuses below it.
  [What limits a bend]
- Solve radii against the **faceted** centreline, never a smooth arc (a chord is
  1.14% short). [A half-circle advances 2/pi]
- `flip()` negates y once, at the end of `centreline()`, and **nowhere else**.
  Never assume handedness: measure outward directions.
  [The geometry is worked out y-up]
- When checking that a change moved nothing, compare cut groups as
  position-independent shapes, since the packer may reorder.
  [Long panels get more than one tooth]
- A trace file carries its stations **and their provenance**. Its total turning
  should be 0. If the parameters ever turn up, generate the shape from them and
  delete the trace. [A traced centreline is kept with how it was taken]

## Closed rings

- `--radius` is the **circumradius** of the centreline polygon, not an apothem.
- `offset()` and `turn_at()` both wrap at the seam: on a ring the first and last
  vertex are one vertex. [The seam is not a free end]
- A ring cheek is written as **separate closed paths** (`contours()` splits at
  1e-9). The check `no cut line crosses the airway` guards it.
  [A ring cheek is two cuts]
- `--oval` defaults are the shipped smallest design. The stadium is
  `--oval-end-deg=90` with a side straight. [The oval…; The stadium…]
- `--port-at=i,j` replaces `--port-both`. The two together are refused, and
  `--cap` is refused with it. [Two ports on a ring are two paths]
- The port separation K (1 to `n//2`) tunes the ring. An odd n cannot give equal
  paths, and that is intended. [The port separation is the ring's tuning dial]
- Ported-ring floor: `R >= 17 / (2 sin(pi/n))`. The ceiling is the cheek against
  the bed. **Two bed limits**: a sheet is checked against 600 x 308, a part
  against 580 x 288 (`pack()` margin). Never read the ceiling off the sheet size.
  Always say which n a number is for. [A ported ring's window depends on n]
- `--facet=60` has no passing radius. **Zero FAIL lines can mean zero checks
  ran**: always look at the PASS count too. Sweep across a boundary before
  naming it. [`--facet=60` has no passing radius]
- A 13 ring needs `--facet=27.6923076923` (the divisibility guard is 1e-9).

## Sheets, kerf and parts

- The cheek file holds **one** cheek and is cut twice (`-cheek-x2-`). Panels go on
  their own sheet. Never pack panels onto the cheek sheet.
  [The cheek gets its own file]
- `pack()` fills the bed minus a margin. A part too big for it is a refusal, not a
  smaller sheet. [One sheet per bedful]
- Kerf: panels are drawn `BURN` over, slots `BURN` under, and `PLAY` per side comes
  off the slot, never the tab. [Kerf goes opposite ways]
- `flippable()` and `rotatable()` **report** and do not guess. Match points as a
  nearest-point bijection; never zip sorted lists. [Both cheeks are the same part]
- To change the cheek rim, change `WEB` (2mm; 1.5mm is the floor), not `MARGIN`.
  Panel numbers are engraved in the channel. [The cheek stops 2mm outboard]
- Lyre-harp kerf is 0.17 via `lyre_harp.KERF`. **Never raise `BURN` here**: it
  would redraw every shipped ribbon sheet.
- A port seats a **bell**. No mouthpiece has been seated in one. The 1000mm double
  spiral ships three sheet sets, and its page names are the reverse of its sheet
  names. `cap()`'s docstring describes the unbuilt arrangement.
  [A port seats a BELL in 3mm of ply]
- The round-ported designs sit at **zero margin** on *the ply between two holes
  survives the kerf*. After any change to `MIN_FEATURE`, `BURN` or `THICK`,
  re-measure them all. [Every check, against geometry it should reject]

## Checks

- A check earns its place by being **watched to fail**. Some checks here cannot
  fail by construction; NOTES.md lists which, so don't count them as evidence.
  [Every check, against geometry it should reject]
- `volute.py`'s two failing checks fail on purpose. [volute.py and ribbon_view.py]
- Every check prints a count. A check comparing two sets of coordinates must first
  establish that both are in the same space (same sheet).
- **Screenshot the SVG after any change to drawing code.** The checks do not see
  the drawing. [Look at the render]
- To pull path data out of an SVG, match `(?:^|\s)d="` (plain `d="` also matches
  `id="`).
- **A failing run deletes its output.** Use `--out` or `--no-write` for trials.
- Run the flat gate with `--min-edge 1.5`. Its *holes are inside the outline* and
  *hole is big enough* checks are noise on these sheets. [The flat gate applies here]

## Viewer and previews

- `ribbon_view.py` draws the airway only, never the cheek plates, and reuses
  `offset()`. It reads flags through `ribbon_bore.read_flags()`. **`--out` is
  required.** A new flag must be added to its `known` set.
  [`ribbon_view.py` draws the airway…]
- `--embed` extracts its drawing code from the full page. Never copy it.
  all-gates.sh gates the Gernreich.github.io embed and the design pages.
  **Look at the page after changing it.**
- Rebuild `previews/` whenever a cut file changes. `previews/old/` mirrors
  `cut-files/old/`. Every `old/` is gitignored. [Previews…]
- Cut order by colour: **blue engraves, then green → orange → cyan → black**.
  Violet `#8000ff` means skip.

## Cut files belong to the author

- **Stage by name.** Never `git add -A` or `git add .`.
- Do not regenerate a cut file the author has hand-edited without asking.
- Commit straight to `main`. Push only when asked.

## Commands

Defaults are 3.0mm ply and 0.15mm kerf, matching `bore_split.py`. Sheets in
`cut-files/old/` need `--sheet=2.94 --kerf=0.13`. Every shipped sheet is
`--narrow`, so a bare `ribbon_bore.py` reproduces none of them and drops stray
files in this folder. Each flag's full rationale is in NOTES.md, Commands.

```sh
G=~/LaserMadeMusic/GIT/lasermade-tools

python3 ribbon_bore.py --no-write          # checks only, writes nothing
python3 ribbon_bore.py --out=/tmp/x.svg    # a trial
python3 ribbon_bore.py --port --out=x-ported.svg
    # --out must contain "ported", or the run refuses
python3 ribbon_bore.py --port --port-square --out=x-ported-square.svg
    # a BORE x BORE port; implies --merge-lead. Never hard-code 9.87
python3 ribbon_bore.py --port --port-both --port-square --out=x-ported-both-square.svg
    # --out must say "-both"; folds the tail lead too; --cap then makes two caps.
    # Coupon: --ds-half --ds-facets=2 --lead=42 (same lead as the 1000mm design)
python3 ribbon_bore.py --port --port-both --port-per-cheek --port-square \
    --out=x-ported-both-square.svg
    # one port per cheek: cheek-a and cheek-b, each cut once
python3 ribbon_bore.py --merge-lead --out=x-merged.svg   # names itself "-merged"
python3 ribbon_bore.py --port --cap --out=x-ported.svg
    # one cap per ported end, on the panels sheet; refused without --port
python3 ribbon_bore.py --port --port-from-tip=8 --out=x-ported.svg   # default 10
python3 ribbon_bore.py --narrow --out=x-narrow.svg
    # rim flush to the mortices; same naming rule; NOT --web=0
python3 ribbon_view.py --shape=serpentine \
    --out=serpentine/ribbon-serpentine-bore10-30deg-3lobes-R72/ribbon-serpentine-bore10-30deg-3lobes-R72.html

# Gernreich.github.io embed: regenerate when the geometry changes
python3 ribbon_view.py --shape=serpentine --embed \
    --out=../../../../../Gernreich.github.io/bore-viewer.html \
    --home=https://gernreich.github.io/trumpet-elbows-allowed/

# Every current sheet into the ONE previews/ here (explicit output path)
for f in $(find . -path '*/cut-files/*.svg' -not -path '*/old/*'); do
  python3 $G/make-preview.py "$f" "previews/$(basename $f)"
done

python3 $G/flat-part-check.py --dir . --min-edge 1.5
python3 $G/svg-stroke-check.py --dir . --quiet

# The writeup is the root README; regenerate and audit it there
cd ../../../.. && python3 $G/md2html.py README.md index.html
python3 $G/doc-audit.py README.md --html index.html \
    --rebuild "python3 $G/md2html.py {md} {out}" --links
```

**Read the audit output before pushing.** It ends with a pass/fail tally.
