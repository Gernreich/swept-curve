//! A bore of constant cross-section swept along a planar curve: the
//! swept-curve generator. Rust since 2026-11-07 (ribbon_bore.py until then;
//! the move changed no byte of any cut file, page or report).
//!
//!     target/release/ribbon_bore                  # the 10mm 30-degree double spiral
//!     target/release/ribbon_bore --no-write       # the numbers, no file
//!
//! Sweep a rectangle along a curve that lies in a plane, with one axis normal
//! to that plane, and the duct has two FLAT faces and two CYLINDRICAL ones.
//! The flat pair are the cheeks and cut straight from the sheet. The curved
//! pair are the whole problem: 3mm birch will not bend to these radii, so they
//! are faceted - short flat panels, each finger-jointed into both cheeks.
//!
//! The section is exactly bore x bore along every facet. At each facet joint
//! the walls mitre, and the area there is bore^2 / cos(phi/2): +3.5% at 30
//! degrees. So the facet angle is the whole design dial, and it trades against
//! part count and against how short the inner panels get.
//!
//! WHAT LIMITS THE BEND is the tooth, not the geometry: a Boxes.py tooth is
//! 2 x thickness and does NOT scale with the bore, so at the 10mm bore and 30
//! degrees the inner panel holds no tooth at all until R = 25mm.
//!
//! Every design flag the Python's module globals held is a field of `Cfg`
//! here, so the lyre-harp and the viewer build their own and nothing is
//! shared by accident. The reasoning behind each number is in NOTES.md and in
//! the git history of ribbon_bore.py; the comments below keep the rules.
//!
//! The other LaserMadeMusic generators borrow `path()` from here.
use lasermade_tools::py::{self, g, hypot, matan2 as atan2, mcos as cos, msin as sin, mtan as tan};
use std::f64::consts::PI;

pub mod ribbon_solidcraft;
pub mod ribbon_view;
pub mod ribbon_view_page;

pub type P = (f64, f64);
pub type R<T> = Result<T, String>;

pub const CUT: &str = "#000000";
pub const INNER: &str = "#ff8000";
pub const MARK: &str = "#0000ff";
/// xTool P2S work area (cut-tested 2026-10-19)
pub const BED_W: f64 = 600.0;
pub const BED_H: f64 = 305.0;
/// sheet margin: the packer's and the reported size's
pub const MARGIN_S: f64 = 10.0;
pub const OPPOSED_R: f64 = 64.0;
pub const OPPOSED_RISE: f64 = 82.4539;
pub const SHAPES: [&str; 10] = [
    "double-spiral", "serpentine", "three-lobe-serpentine-with-collinear-ends", "ess", "spiral",
    "double-volute", "torus", "scallop", "racetrack", "oval",
];
const TLS: &str = "three-lobe-serpentine-with-collinear-ends";

/// 'M x,y L x,y ...' with ' Z' when closed.
pub fn path(pts: &[P], close: bool) -> String {
    let body: Vec<String> = pts.iter().map(|(x, y)| format!("{x:.3},{y:.3}")).collect();
    format!("M {}{}", body.join(" L "), if close { " Z" } else { "" })
}

/// Python's float %: the sign of the divisor.
pub fn pymod(x: f64, y: f64) -> f64 {
    let m = x % y;
    if m != 0.0 {
        if (y < 0.0) != (m < 0.0) {
            m + y
        } else {
            m
        }
    } else {
        0.0f64.copysign(y)
    }
}

/// Python's float //, as CPython's float_floor_div computes it.
pub fn floordiv(vx: f64, wx: f64) -> f64 {
    let mut m = vx % wx;
    let mut div = (vx - m) / wx;
    if m != 0.0 {
        if (wx < 0.0) != (m < 0.0) {
            m += wx;
            div -= 1.0;
        }
    }
    let _ = m;
    if div != 0.0 {
        let mut f = div.floor();
        if div - f > 0.5 {
            f += 1.0;
        }
        f
    } else {
        0.0f64.copysign(vx / wx)
    }
}

/// min/max over a list as Python's builtins answer: the first of equals.
pub fn fmin(v: impl IntoIterator<Item = f64>) -> f64 {
    let mut it = v.into_iter();
    let first = it.next().expect("min() arg is an empty sequence");
    it.fold(first, py::min)
}
pub fn fmax(v: impl IntoIterator<Item = f64>) -> f64 {
    let mut it = v.into_iter();
    let first = it.next().expect("max() arg is an empty sequence");
    it.fold(first, py::max)
}
/// sum() of floats on Python 3.9: from int 0, left to right.
pub fn fsum(v: impl IntoIterator<Item = f64>) -> f64 {
    v.into_iter().fold(0.0, |a, b| a + b)
}

#[derive(Clone, Debug)]
pub struct Cfg {
    pub bore: f64,
    pub facet: f64,
    pub radius: f64,
    /// ply, NOMINAL: what the design is dimensioned on
    pub thick: f64,
    /// what the sheet actually calipers: only the depth of a mortice reads it
    pub sheet: f64,
    pub web: f64,
    pub narrow: bool,
    /// kerf, the FULL width the laser takes out, centred on the line
    pub burn: f64,
    /// per side, a lookup of what has been cut, keyed by round(bore, 3)
    pub play_by_bore: Vec<(f64, f64)>,
    pub slot_tighten: f64,
    pub play_unmeasured: f64,
    /// Boxes.py FingerJointSettings; does not scale (2 * the import-time THICK)
    pub tooth: f64,
    pub shoulder: f64,
    pub min_feature: f64,
    pub out: Option<String>,
    pub port: bool,
    pub shape: String,
    pub lobes: i64,
    pub lobe_r: f64,
    pub rise: f64,
    pub lead: f64,
    pub port_across: f64,
    pub port_along: f64,
    pub port_from_tip: f64,
    pub port_square: bool,
    pub port_both: bool,
    pub port_per_cheek: bool,
    pub port_at: Option<Vec<i64>>,
    pub merge_lead: bool,
    pub cap: bool,
    pub spiral_facets: i64,
    pub spiral_ri: f64,
    pub spiral_ro: f64,
    pub scallop_in_r: f64,
    pub scallop_in_deg: f64,
    pub race_cap_r: f64,
    pub race_straight: f64,
    pub oval_end_r: f64,
    pub oval_end_deg: f64,
    pub oval_side_r: f64,
    pub oval_flat: f64,
    pub oval_side_flat: f64,
    pub ds_pitch: f64,
    pub ds_r0: f64,
    pub ds_facets: i64,
    pub ds_cross_r: f64,
    pub ds_half: bool,
    pub vol_r0: f64,
    pub vol_step: f64,
    pub vol_semis: i64,
    pub vol_cross_r: f64,
    pub wave_lead_arcs: i64,
    pub wave_lobe_arcs: i64,
    pub wave_rise: f64,
    pub wave_lead_r: f64,
    pub wave_trough_r: f64,
    pub wave_crest_r: f64,
}

impl Default for Cfg {
    fn default() -> Cfg {
        Cfg {
            bore: 10.0,
            facet: 30.0,
            radius: 30.0,
            thick: 3.0,
            sheet: 3.0,
            web: 2.0,
            narrow: false,
            burn: 0.15,
            play_by_bore: vec![(10.0, 0.025)],
            slot_tighten: 0.0,
            play_unmeasured: 0.025,
            tooth: 6.0,
            shoulder: 2.0,
            min_feature: 1.5,
            out: None,
            port: false,
            shape: "double-spiral".into(),
            lobes: 3,
            lobe_r: 71.754,
            rise: 90.0,
            lead: 20.0,
            port_across: 7.0,
            port_along: 14.0,
            port_from_tip: 10.0,
            port_square: false,
            port_both: false,
            port_per_cheek: false,
            port_at: None,
            merge_lead: false,
            cap: false,
            spiral_facets: 17,
            spiral_ri: 34.662,
            spiral_ro: 112.903,
            scallop_in_r: 34.0,
            scallop_in_deg: 48.0,
            race_cap_r: 132.809141,
            race_straight: 31.0,
            oval_end_r: 28.0,
            oval_end_deg: 60.0,
            oval_side_r: 72.0,
            oval_flat: 12.2,
            oval_side_flat: 12.5,
            ds_pitch: 46.0,
            ds_r0: 62.0,
            ds_facets: 14,
            ds_cross_r: 30.0,
            ds_half: false,
            vol_r0: 94.0,
            vol_step: 60.0,
            vol_semis: 2,
            vol_cross_r: 22.0,
            wave_lead_arcs: 2,
            wave_lobe_arcs: 5,
            wave_rise: 100.0,
            wave_lead_r: 90.0,
            wave_trough_r: 55.0,
            wave_crest_r: 55.0,
        }
    }
}

/// A wall panel, or a part another generator lays out the same way.
#[derive(Clone, Debug, Default)]
pub struct Part {
    pub wall: String,
    pub n: usize,
    pub len: f64,
    pub mid: P,
    pub ang: f64,
    pub out: P,
    pub tag: String,
    /// set by merge_lead(): the label stays where the unmerged panel had it
    pub label_mid: Option<P>,
    /// set by merge_lead(): the teeth stay where the surviving half had them
    pub cs: Option<Vec<f64>>,
    /// settled once in build(), so a tooth and its mortice agree
    pub teeth: Option<Vec<f64>>,
}

/// One thing to pack: its outline, the holes cut in it, and its engraving,
/// which waits on where the packer puts it.
pub struct Item<'a> {
    pub outline: Vec<P>,
    pub slots: Vec<Vec<P>>,
    pub marks: Box<dyn Fn(f64, f64) -> Vec<String> + 'a>,
    pub note: String,
}

/// (sheet file name, width, height, parts on it, note)
pub type Written = (String, f64, f64, usize, String);
/// an engraved point, the outline it must be on, and the file it is in
pub type Ink = (f64, f64, Vec<P>, String);

#[derive(Clone, Copy)]
pub enum End {
    Mouth,
    Tail,
    Facet(usize),
}

enum Seg {
    S(f64),
    A(f64, f64),
}

pub fn seglen(p: P, q: P) -> f64 {
    hypot(q.0 - p.0, q.1 - p.1)
}

pub fn rot(p: P, ang: f64, at: P) -> P {
    let (c, s) = (cos(ang), sin(ang));
    let (x, y) = (p.0 - at.0, p.1 - at.1);
    (at.0 + x * c - y * s, at.1 + x * s + y * c)
}

/// Negate y, so the file renders the way the shape is drawn. Applied once, at
/// the end of centreline(), and nowhere else.
pub fn flip(pts: Vec<P>) -> Vec<P> {
    pts.into_iter().map(|(x, y)| (x, -y)).collect()
}

/// Where two segments' infinite lines cross, or None if they are parallel.
/// The parallel test is RELATIVE: d over both lengths is a sine.
pub fn meet(s: (P, P), t: (P, P)) -> Option<P> {
    let ((x1, y1), (x2, y2)) = s;
    let ((x3, y3), (x4, y4)) = t;
    let d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
    let lu = hypot(x2 - x1, y2 - y1);
    let lv = hypot(x4 - x3, y4 - y3);
    if lu == 0.0 || lv == 0.0 || d.abs() < 1e-9 * lu * lv {
        return None;
    }
    let a = x1 * y2 - y1 * x2;
    let b = x3 * y4 - y3 * x4;
    Some(((a * (x3 - x4) - (x1 - x2) * b) / d, (a * (y3 - y4) - (y1 - y2) * b) / d))
}

/// The polyline offset sideways by d, mitred at every interior vertex by
/// intersecting the neighbouring offset LINES, and at the seam of a loop.
pub fn offset(poly: &[P], d: f64) -> Vec<P> {
    let mut segs = Vec::new();
    for w in poly.windows(2) {
        let (a, b) = (w[0], w[1]);
        let (ux, uy) = (b.0 - a.0, b.1 - a.1);
        let l = hypot(ux, uy);
        if l == 0.0 {
            // Python divided by it and stopped with a traceback; so does this
            panic!("ZeroDivisionError: float division by zero");
        }
        let (nx, ny) = (-uy / l, ux / l);
        segs.push(((a.0 + nx * d, a.1 + ny * d), (b.0 + nx * d, b.1 + ny * d)));
    }
    let shut = (poly[0].0 - poly[poly.len() - 1].0).abs() < 1e-9
        && (poly[0].1 - poly[poly.len() - 1].1).abs() < 1e-9;
    let first = if shut { meet(segs[segs.len() - 1], segs[0]) } else { None };
    let mut out = vec![first.unwrap_or(segs[0].0)];
    for w in segs.windows(2) {
        out.push(meet(w[0], w[1]).unwrap_or(w[0].1));
    }
    out.push(first.unwrap_or(segs[segs.len() - 1].1));
    out
}

/// Distance from a point to a segment.
pub fn pt_seg(q: P, a: P, b: P) -> f64 {
    let (dx, dy) = (b.0 - a.0, b.1 - a.1);
    let l2 = dx * dx + dy * dy;
    let u = if l2 == 0.0 {
        0.0
    } else {
        py::max(0.0, py::min(1.0, ((q.0 - a.0) * dx + (q.1 - a.1) * dy) / l2))
    };
    hypot(q.0 - (a.0 + u * dx), q.1 - (a.1 + u * dy))
}

/// Closest approach of two segments.
pub fn seg_gap(p1: P, p2: P, q1: P, q2: P) -> f64 {
    fmin([pt_seg(p1, q1, q2), pt_seg(p2, q1, q2), pt_seg(q1, p1, p2), pt_seg(q2, p1, p2)])
}

pub fn bbox(pts: &[P]) -> (f64, f64, f64, f64) {
    (
        fmin(pts.iter().map(|q| q.0)),
        fmin(pts.iter().map(|q| q.1)),
        fmax(pts.iter().map(|q| q.0)),
        fmax(pts.iter().map(|q| q.1)),
    )
}

/// Crossing count over a closed list (last point = first). Used to keep
/// engraving out of the port.
pub fn in_poly(poly: &[P], x: f64, y: f64) -> bool {
    let n = poly.len() - 1;
    let mut ins = false;
    for i in 0..n {
        let (x1, y1) = poly[i];
        let (x2, y2) = poly[i + 1];
        if (y1 > y) != (y2 > y) && x < x1 + (y - y1) / (y2 - y1) * (x2 - x1) {
            ins = !ins;
        }
    }
    ins
}

/// Even-odd ray cast over an open list, wrapping from the first to the last.
pub fn inside(poly: &[P], x: f64, y: f64) -> bool {
    let n = poly.len();
    let mut c = false;
    for i in 0..n {
        let (ax, ay) = poly[i];
        let (bx, by) = poly[(i + n - 1) % n];
        if (ay > y) != (by > y) && x < (bx - ax) * (y - ay) / (by - ay) + ax {
            c = !c;
        }
    }
    c
}

/// The closed loops a cheek outline is CUT as: one for an open shape, the
/// outer and inner rings apart for a closed one, so the cut is no slit.
pub fn contours(outline: &[P]) -> Vec<Vec<P>> {
    let k = (1..outline.len().saturating_sub(1))
        .find(|&i| hypot(outline[i].0 - outline[0].0, outline[i].1 - outline[0].1) < 1e-9);
    match k {
        None => vec![outline.to_vec()],
        Some(k) => vec![outline[..k + 1].to_vec(), outline[k + 1..].to_vec()],
    }
}

fn glyph(ch: char) -> &'static [&'static [P]] {
    match ch {
        '0' => &[&[(0.5, 1.0), (0.85, 0.8), (0.85, 0.2), (0.5, 0.0), (0.15, 0.2), (0.15, 0.8), (0.5, 1.0)]],
        '1' => &[&[(0.3, 0.78), (0.52, 1.0), (0.52, 0.0)], &[(0.28, 0.0), (0.78, 0.0)]],
        '2' => &[&[(0.1, 0.78), (0.3, 1.0), (0.7, 1.0), (0.9, 0.78), (0.9, 0.6), (0.1, 0.0), (0.9, 0.0)]],
        '3' => &[
            &[(0.1, 1.0), (0.9, 1.0), (0.45, 0.55)],
            &[(0.45, 0.55), (0.9, 0.55), (0.9, 0.16), (0.72, 0.0), (0.28, 0.0), (0.1, 0.16)],
        ],
        '4' => &[&[(0.7, 0.0), (0.7, 1.0), (0.12, 0.32), (0.92, 0.32)]],
        '5' => &[&[(0.85, 1.0), (0.2, 1.0), (0.15, 0.55), (0.5, 0.62), (0.8, 0.5), (0.88, 0.28), (0.75, 0.06), (0.4, 0.0), (0.15, 0.12)]],
        '6' => &[&[
            (0.82, 0.92), (0.55, 1.0), (0.25, 0.85), (0.15, 0.45), (0.15, 0.18), (0.35, 0.0), (0.62, 0.0), (0.85, 0.18),
            (0.85, 0.38), (0.62, 0.55), (0.3, 0.55), (0.15, 0.45),
        ]],
        '7' => &[&[(0.12, 1.0), (0.9, 1.0), (0.42, 0.0)]],
        '8' => &[&[
            (0.5, 0.55), (0.22, 0.68), (0.22, 0.87), (0.5, 1.0), (0.78, 0.87), (0.78, 0.68), (0.5, 0.55), (0.18, 0.4),
            (0.18, 0.14), (0.5, 0.0), (0.82, 0.14), (0.82, 0.4), (0.5, 0.55),
        ]],
        '9' => &[&[
            (0.18, 0.08), (0.45, 0.0), (0.75, 0.15), (0.85, 0.55), (0.85, 0.82), (0.65, 1.0), (0.38, 1.0), (0.15, 0.82),
            (0.15, 0.62), (0.38, 0.45), (0.7, 0.45), (0.85, 0.55),
        ]],
        'A' => &[&[(0.1, 0.0), (0.5, 1.0), (0.9, 0.0)], &[(0.26, 0.4), (0.74, 0.4)]],
        'B' => &[
            &[(0.15, 0.0), (0.15, 1.0), (0.68, 1.0), (0.88, 0.83), (0.88, 0.68), (0.68, 0.55), (0.15, 0.55)],
            &[(0.15, 0.55), (0.72, 0.55), (0.9, 0.4), (0.9, 0.16), (0.7, 0.0), (0.15, 0.0)],
        ],
        'C' => &[&[(0.9, 0.8), (0.7, 1.0), (0.3, 1.0), (0.1, 0.8), (0.1, 0.2), (0.3, 0.0), (0.7, 0.0), (0.9, 0.2)]],
        'D' => &[&[(0.15, 0.0), (0.15, 1.0), (0.58, 1.0), (0.88, 0.74), (0.88, 0.26), (0.58, 0.0), (0.15, 0.0)]],
        'E' => &[&[(0.9, 1.0), (0.15, 1.0), (0.15, 0.0), (0.9, 0.0)], &[(0.15, 0.5), (0.68, 0.5)]],
        'F' => &[&[(0.88, 1.0), (0.15, 1.0), (0.15, 0.0)], &[(0.15, 0.52), (0.68, 0.52)]],
        _ => panic!("KeyError: '{ch}'"),
    }
}

/// Hex glyphs centred on (cx, cy), with the baseline tick that says which way
/// up. Blue, so it engraves and never cuts.
pub fn label(text: &str, cx: f64, cy: f64, h: f64, ang: f64) -> Vec<String> {
    let (w, gap) = (h * 0.62, h * 0.18);
    let n = text.chars().count() as f64;
    let total = n * w + (n - 1.0) * gap;
    let mut x = -total / 2.0;
    let mut out = Vec::new();
    for ch in text.chars() {
        for st in glyph(ch) {
            let pts: Vec<P> = st
                .iter()
                .map(|&(px, py_)| rot((x + px * w, h / 2.0 - py_ * h), ang, (0.0, 0.0)))
                .map(|p| (cx + p.0, cy + p.1))
                .collect();
            out.push(path(&pts, false));
        }
        x += w + gap;
    }
    let (tg, tl) = (h * 0.16, h * 0.22);
    let a = rot((total / 2.0 + tg, h / 2.0), ang, (0.0, 0.0));
    let b = rot((total / 2.0 + tg + tl, h / 2.0), ang, (0.0, 0.0));
    out.push(path(&[(cx + a.0, cy + a.1), (cx + b.0, cy + b.1)], false));
    out
}

fn tail(lead: f64, u: P, v: P) -> P {
    let (dx, dy) = (u.0 - v.0, u.1 - v.1);
    let m = hypot(dx, dy);
    (u.0 + dx / m * lead, u.1 + dy / m * lead)
}

fn find_crossing(leg_perp: impl Fn(f64) -> f64, leg_along: impl Fn(f64) -> f64) -> Option<f64> {
    let (lo, hi, n) = (-PI * 0.99, PI * 0.99, 3000);
    let mut prev = lo;
    for i in 1..=n {
        let x = lo + (hi - lo) * i as f64 / n as f64;
        if (leg_perp(x) < 0.0) != (leg_perp(prev) < 0.0) {
            let (mut a, mut c2) = (prev, x);
            for _ in 0..120 {
                let m = (a + c2) / 2.0;
                if (leg_perp(m) < 0.0) != (leg_perp(a) < 0.0) {
                    c2 = m;
                } else {
                    a = m;
                }
            }
            let cand = (a + c2) / 2.0;
            if leg_along(cand) > 0.0 {
                return Some(cand);
            }
        }
        prev = x;
    }
    None
}

impl Cfg {
    /// Where a wall's CENTRELINE sits: its slot is centred on it, so the
    /// airway is BORE between the faces. Functions, not constants, so --bore
    /// and --web reach them.
    pub fn wall_off(&self) -> f64 {
        self.bore / 2.0 + self.thick / 2.0
    }
    /// Half the mortice across the band, from the wall's centreline: the
    /// DRAWN slot edge, half a kerf inboard of the wall's face.
    pub fn slot_half(&self) -> f64 {
        (self.sheet - self.slot_tighten) / 2.0 - self.burn / 2.0
    }
    pub fn cheek_off(&self) -> f64 {
        if self.narrow {
            return self.wall_off() + self.slot_half();
        }
        self.wall_off() + self.thick / 2.0 + self.web
    }
    pub fn band(&self) -> f64 {
        2.0 * self.cheek_off()
    }
    /// Per side, for the current bore.
    pub fn play(&self) -> f64 {
        let k = py::round_dp(self.bore, 3);
        self.play_by_bore.iter().find(|(b, _)| *b == k).map(|&(_, p)| p).unwrap_or(self.play_unmeasured)
    }
    /// How many end caps this design needs: one per ported end, else none.
    pub fn caps(&self) -> usize {
        if self.cap {
            if self.port_both {
                2
            } else {
                1
            }
        } else {
            0
        }
    }
    fn floor(&self) -> f64 {
        self.wall_off() + (self.tooth + 2.0 * self.shoulder) / 2.0 / sin(py::radians(self.facet / 2.0))
    }
    fn tight_err(&self, tight: f64, floor: f64) -> String {
        format!(
            "the tightest arc is R{} and a {}mm bore at {} degree facets needs R{:.1}.",
            g(tight),
            g(self.bore),
            g(self.facet),
            floor
        )
    }

    /// A faceted polyline from straights and arcs. Arcs are inscribed, so a
    /// chord's direction is the tangent at its midpoint.
    fn walk(&self, spec: &[Seg]) -> R<Vec<P>> {
        let (mut x, mut y, mut a) = (0.0f64, 0.0f64, 0.0f64);
        let mut pts = vec![(0.0, 0.0)];
        for item in spec {
            match *item {
                Seg::S(l) => {
                    x += cos(a) * l;
                    y += sin(a) * l;
                    pts.push((x, y));
                }
                Seg::A(deg, sign) => {
                    let n = py::round(deg / self.facet);
                    if (n as f64 * self.facet - deg).abs() > 1e-9 {
                        return Err(format!(
                            "--facet={} does not divide a {} degree turn a whole number of times; {} facets would turn {} degrees.",
                            g(self.facet),
                            g(deg),
                            n,
                            g(n as f64 * self.facet)
                        ));
                    }
                    let r = if self.shape == "serpentine" || self.shape == TLS { self.lobe_r } else { self.radius };
                    let cx = x - sign * r * sin(a);
                    let cy = y + sign * r * cos(a);
                    let t0 = atan2(y - cy, x - cx);
                    for i in 1..=n {
                        let t = t0 + sign * py::radians(deg) * i as f64 / n as f64;
                        x = cx + r * cos(t);
                        y = cy + r * sin(t);
                        pts.push((x, y));
                    }
                    a += sign * py::radians(deg);
                }
            }
        }
        Ok(pts)
    }

    /// Chord arcs of their own radius: ('s', length, _) a straight, ('a',
    /// R, sg) `k(sg)` facets turning sg each. The scallop's, the racetrack's
    /// and the oval's construction; a straight of 0 is skipped only where
    /// `skip0` (the oval's).
    fn chords(&self, items: &[(char, f64, f64)], k: impl Fn(f64) -> i64, skip0: bool) -> Vec<P> {
        let step = py::radians(self.facet);
        let (mut x, mut y, mut a) = (0.0f64, 0.0f64, 0.0f64);
        let mut pts = vec![(0.0, 0.0)];
        for &(kind, r, sg) in items {
            if kind == 's' {
                if !skip0 || r > 0.0 {
                    x += r * cos(a);
                    y += r * sin(a);
                    pts.push((x, y));
                }
                continue;
            }
            for _ in 0..k(sg) {
                let c = 2.0 * r * sin(step / 2.0);
                let turn = if skip0 { 1.0 } else { sg };
                a += turn * step / 2.0;
                x += c * cos(a);
                y += c * sin(a);
                a += turn * step / 2.0;
                pts.push((x, y));
            }
        }
        pts
    }

    /// The centreline, already faceted at FACET and flipped into SVG's y. The
    /// panels ARE its segments offset sideways.
    pub fn centreline(&self) -> R<Vec<P>> {
        let floor = self.floor();
        match self.shape.as_str() {
            "oval" => {
                let side_deg = 180.0 - 2.0 * self.oval_end_deg;
                for (flag, v) in [("--oval-flat", self.oval_flat), ("--oval-side-flat", self.oval_side_flat)] {
                    if v < 0.0 {
                        return Err(format!("{flag}={} is negative.", g(v)));
                    }
                }
                if !(0.0 < self.oval_end_deg && self.oval_end_deg <= 90.0) {
                    return Err(format!(
                        "--oval-end-deg={} has to be above 0 and at most 90: the two end arcs and the side arc share a half turn.",
                        g(self.oval_end_deg)
                    ));
                }
                if self.oval_end_deg == 90.0 && self.oval_side_flat == 0.0 {
                    return Err("--oval-end-deg=90 turns the whole half-circle at the end and leaves the side nothing, so without --oval-side-flat the two ends meet and the loop is a circle. Give the side a straight.".into());
                }
                let second = if self.oval_side_flat == 0.0 {
                    ("the side turn", side_deg)
                } else {
                    ("half the side turn", side_deg / 2.0)
                };
                for (what, deg) in [("the end turn", self.oval_end_deg), second] {
                    if (py::round(deg / self.facet) as f64 * self.facet - deg).abs() > 1e-9 {
                        return Err(format!(
                            "--facet={} does not divide {what}, {} degrees, a whole number of times.",
                            g(self.facet),
                            g(deg)
                        ));
                    }
                }
                let tight = self.bend_radius();
                if tight < floor {
                    return Err(self.tight_err(tight, floor));
                }
                // here an arc's third field is its turn in degrees, not a sign
                let mut side = Vec::new();
                if self.oval_side_flat != 0.0 {
                    side.push(('a', self.oval_side_r, side_deg / 2.0));
                    side.push(('s', self.oval_side_flat, 0.0));
                    side.push(('a', self.oval_side_r, side_deg / 2.0));
                } else {
                    side.push(('a', self.oval_side_r, side_deg));
                }
                let mut half = vec![('s', self.oval_flat, 0.0), ('a', self.oval_end_r, self.oval_end_deg)];
                half.extend(side);
                half.push(('a', self.oval_end_r, self.oval_end_deg));
                let twice: Vec<_> = half.iter().chain(half.iter()).copied().collect();
                let f = self.facet;
                let mut pts = self.chords(&twice, |deg| py::round(deg / f), true);
                let n = pts.len();
                pts[n - 1] = pts[0];
                let pts: Vec<P> = pts.into_iter().map(|(x, y)| (y, -x)).collect();
                Ok(flip(pts))
            }
            "racetrack" => {
                if self.lobes.rem_euclid(2) != 0 {
                    return Err(format!(
                        "--lobes={} is odd. The half-circles alternate, so they cancel only in pairs; an odd count leaves the half turning {} degrees instead of 180 and the loop does not close.",
                        self.lobes,
                        180 - 180 * self.lobes.rem_euclid(2)
                    ));
                }
                if self.race_straight < 0.0 {
                    return Err(format!("--race-straight={} is negative.", g(self.race_straight)));
                }
                if (py::round(180.0 / self.facet) as f64 * self.facet - 180.0).abs() > 1e-9 {
                    return Err(format!(
                        "--facet={} does not divide a half-circle a whole number of times.",
                        g(self.facet)
                    ));
                }
                let tight = py::min(self.lobe_r, self.race_cap_r);
                if tight < floor {
                    return Err(self.tight_err(tight, floor));
                }
                let mut half = vec![('a', self.race_cap_r, 1.0)];
                for i in 0..self.lobes.max(0) {
                    half.push(('a', self.lobe_r, if i % 2 == 0 { -1.0 } else { 1.0 }));
                    if self.race_straight > 0.0 {
                        half.push(('s', self.race_straight, 0.0));
                    }
                }
                let twice: Vec<_> = half.iter().chain(half.iter()).copied().collect();
                let per = py::round(180.0 / self.facet);
                let mut pts = self.chords(&twice, |_| per, false);
                let n = pts.len();
                pts[n - 1] = pts[0];
                let pts: Vec<P> = pts.into_iter().map(|(x, y)| (y, -x)).collect();
                Ok(flip(pts))
            }
            "scallop" => {
                let per = 360.0 / self.lobes as f64;
                let out_deg = self.scallop_in_deg + per;
                for (what, deg) in [("360/LOBES", per), ("the concave turn", self.scallop_in_deg), ("the convex turn", out_deg)] {
                    if (py::round(deg / self.facet) as f64 * self.facet - deg).abs() > 1e-9 {
                        return Err(format!(
                            "--facet={} does not divide {what}, {} degrees, a whole number of times. At {} lobes the facet has to divide 360/{} = {} as well as both turns.",
                            g(self.facet),
                            g(deg),
                            self.lobes,
                            self.lobes,
                            g(per)
                        ));
                    }
                }
                let tight = py::min(self.lobe_r, self.scallop_in_r);
                if tight < floor {
                    return Err(self.tight_err(tight, floor));
                }
                let mut unit = Vec::new();
                for _ in 0..py::round(out_deg / self.facet).max(0) {
                    unit.push(('a', self.lobe_r, 1.0));
                }
                for _ in 0..py::round(self.scallop_in_deg / self.facet).max(0) {
                    unit.push(('a', self.scallop_in_r, -1.0));
                }
                let mut segs = Vec::new();
                for _ in 0..self.lobes.max(0) {
                    segs.extend(unit.iter().copied());
                }
                let mut pts = self.chords(&segs, |_| 1, false);
                let n = pts.len();
                pts[n - 1] = pts[0];
                Ok(flip(pts))
            }
            "torus" => {
                let n = py::round(360.0 / self.facet);
                if (n as f64 * self.facet - 360.0).abs() > 1e-9 {
                    return Err(format!(
                        "--facet={} does not divide a full turn a whole number of times.",
                        g(self.facet)
                    ));
                }
                Ok(flip(self.walk(&[Seg::A(360.0, 1.0)])?))
            }
            "ess" => {
                let tight = fmin([self.wave_lead_r, self.wave_trough_r, self.wave_crest_r]);
                if tight < floor {
                    return Err(self.tight_err(tight, floor));
                }
                let mut segs: Vec<(char, f64, f64)> = Vec::new();
                let n = |k: i64| 0..k.max(0);
                for _ in n(self.wave_lead_arcs) {
                    segs.push(('a', self.wave_lead_r, 1.0));
                }
                for _ in n(self.wave_lobe_arcs) {
                    segs.push(('a', self.wave_trough_r, -1.0));
                }
                segs.push(('s', self.wave_rise, 0.0));
                for _ in n(self.wave_lobe_arcs) {
                    segs.push(('a', self.wave_crest_r, 1.0));
                }
                for _ in n(self.wave_lead_arcs) {
                    segs.push(('a', self.wave_lead_r, -1.0));
                }
                let step = py::radians(self.facet);
                let (mut x, mut y, mut a) = (0.0f64, 0.0f64, 0.0f64);
                let mut pts = vec![(0.0, 0.0)];
                for (kind, v, sg) in segs {
                    if kind == 's' {
                        x += cos(a) * v;
                        y += sin(a) * v;
                        pts.push((x, y));
                        continue;
                    }
                    let (cx, cy) = (x - sg * v * sin(a), y + sg * v * cos(a));
                    let t0 = atan2(y - cy, x - cx);
                    x = cx + v * cos(t0 + sg * step);
                    y = cy + v * sin(t0 + sg * step);
                    pts.push((x, y));
                    a += sg * step;
                }
                Ok(flip(self.tails(pts)))
            }
            "spiral" => {
                let sf = self.spiral_facets;
                if pymod((sf - 1) as f64 * self.facet, 360.0) > 1e-9 {
                    return Err(format!(
                        "{} facets turn the run {} degrees, which is not a whole number of turns, so the ends do not come out opposed. At {} degree facets use {}k + 1.",
                        sf,
                        g((sf - 1) as f64 * self.facet),
                        g(self.facet),
                        py::round(360.0 / self.facet)
                    ));
                }
                let tight = py::min(self.spiral_ri, self.spiral_ro);
                if tight < floor {
                    return Err(format!(
                        "the tightest arc is R{} and a {}mm bore at {} degree facets needs R{:.1}.",
                        g(tight),
                        g(self.bore),
                        g(self.facet),
                        floor
                    ));
                }
                let step = py::radians(self.facet);
                let (mut x, mut y, mut a) = (0.0f64, 0.0f64, 0.0f64);
                let mut pts = vec![(0.0, 0.0)];
                for k in 0..sf.max(0) {
                    let r = self.spiral_ri + (self.spiral_ro - self.spiral_ri) * k as f64 / (sf - 1) as f64;
                    let (cx, cy) = (x - r * sin(a), y + r * cos(a));
                    let t0 = atan2(y - cy, x - cx);
                    x = cx + r * cos(t0 + step);
                    y = cy + r * sin(t0 + step);
                    pts.push((x, y));
                    a += step;
                }
                Ok(flip(self.tails(pts)))
            }
            "double-volute" => {
                let per = py::round(180.0 / self.facet);
                if (per as f64 * self.facet - 180.0).abs() > 1e-9 {
                    return Err(format!("{} degree facets do not divide a semicircle.", g(self.facet)));
                }
                if self.vol_step / 2.0 < self.band() {
                    return Err(format!(
                        "--vol-step={} puts the two arms {}mm apart and the cheek band is {}mm wide. A single arm only needs the band; interleaving a second one needs twice it, so use --vol-step above {}.",
                        g(self.vol_step),
                        g(self.vol_step / 2.0),
                        g(self.band()),
                        g(2.0 * self.band())
                    ));
                }
                let radii: Vec<f64> =
                    (0..self.vol_semis.max(0)).map(|k| self.vol_r0 - k as f64 * self.vol_step / 2.0).collect();
                if radii.is_empty() {
                    return Err("min() arg is an empty sequence".into());
                }
                let rmin = fmin(radii.iter().copied());
                if rmin < floor {
                    return Err(format!(
                        "the tightest arc is R{:.1} and a {}mm bore at {} degree facets needs R{:.1}.",
                        rmin,
                        g(self.bore),
                        g(self.facet),
                        floor
                    ));
                }
                if self.vol_cross_r < floor {
                    return Err(format!(
                        "--vol-cross-r={} and a {}mm bore at {} degree facets needs R{:.1}.",
                        g(self.vol_cross_r),
                        g(self.bore),
                        g(self.facet),
                        floor
                    ));
                }
                let mut arm = vec![(radii[0], 0.0)];
                let mut ang = 0.0f64;
                for &r in &radii {
                    let (px, py_) = arm[arm.len() - 1];
                    let (cx, cy) = (px - r * cos(ang), py_ - r * sin(ang));
                    for i in 1..=per {
                        let th = ang + PI * i as f64 / per as f64;
                        arm.push((cx + r * cos(th), cy + r * sin(th)));
                    }
                    ang += PI;
                }
                let eye = self.vol_step / 4.0;
                let arm: Vec<P> = arm.into_iter().map(|(x, y)| (x + eye, y)).collect();
                let s = arm[arm.len() - 1];
                let h0 = atan2(s.1 - arm[arm.len() - 2].1, s.0 - arm[arm.len() - 2].0);
                let rr = self.vol_cross_r;
                let leg = |delta: f64| {
                    let sg = if delta >= 0.0 { 1.0 } else { -1.0 };
                    let cx = s.0 + rr * cos(h0 + sg * PI / 2.0);
                    let cy = s.1 + rr * sin(h0 + sg * PI / 2.0);
                    let a0 = atan2(s.1 - cy, s.0 - cx);
                    let ex = cx + rr * cos(a0 + delta);
                    let ey = cy + rr * sin(a0 + delta);
                    let h1 = h0 + delta;
                    let perp = -sin(h1) * -ex + cos(h1) * -ey;
                    let along = -ex * cos(h1) + -ey * sin(h1);
                    ((cx, cy), a0, perp, along)
                };
                let found = find_crossing(|d| leg(d).2, |d| leg(d).3).ok_or_else(|| {
                    format!(
                        "no crossover arc reaches the eye at --vol-cross-r={}, --vol-r0={}, --vol-step={}.",
                        g(self.vol_cross_r),
                        g(self.vol_r0),
                        g(self.vol_step)
                    )
                })?;
                let ((cx, cy), a0, _, _) = leg(found);
                let steps = 1i64.max((py::degrees(found).abs() / self.facet).ceil() as i64);
                let mut cross: Vec<P> = (1..=steps)
                    .map(|i| {
                        (
                            cx + rr * cos(a0 + found * i as f64 / steps as f64),
                            cy + rr * sin(a0 + found * i as f64 / steps as f64),
                        )
                    })
                    .collect();
                cross.push((0.0, 0.0));
                let mut half = arm;
                half.extend(cross);
                let mut pts = half.clone();
                pts.extend(half.iter().rev().skip(1).map(|&(x, y)| (-x, -y)));
                Ok(flip(self.tails(pts)))
            }
            "double-spiral" => {
                let b = self.ds_pitch / (2.0 * PI);
                if self.ds_cross_r < floor {
                    return Err(format!(
                        "--ds-cross-r={} and a {}mm bore at {} degree facets needs R{:.1}.",
                        g(self.ds_cross_r),
                        g(self.bore),
                        g(self.facet),
                        floor
                    ));
                }
                if self.ds_r0 <= 2.0 * self.ds_cross_r {
                    return Err(format!(
                        "--ds-r0={} is not outside twice --ds-cross-r={}, so no straight from the centre is tangent to the crossover arc and the two arms cannot be joined. Use --ds-r0 above {}.",
                        g(self.ds_r0),
                        g(self.ds_cross_r),
                        g(2.0 * self.ds_cross_r)
                    ));
                }
                let rho = py::powf(py::powf(self.ds_r0, 2.0) + py::powf(b, 2.0), 1.5)
                    / (py::powf(self.ds_r0, 2.0) + 2.0 * py::powf(b, 2.0));
                if rho < floor {
                    return Err(format!(
                        "the spiral is tightest at R{:.1} where its inner end meets the crossover, and a {}mm bore at {} degree facets needs R{:.1}.",
                        rho,
                        g(self.bore),
                        g(self.facet),
                        floor
                    ));
                }
                if self.ds_pitch / 2.0 < self.band() {
                    return Err(format!(
                        "--ds-pitch={} puts neighbouring passes {}mm apart and the cheek band is {}mm wide, so the two arms overlap. Use --ds-pitch above {}.",
                        g(self.ds_pitch),
                        g(self.ds_pitch / 2.0),
                        g(self.band()),
                        g(2.0 * self.band())
                    ));
                }
                let mut arm = Vec::new();
                for k in 0..(self.ds_facets + 1).max(0) {
                    let th = py::radians(k as f64 * self.facet);
                    let r = self.ds_r0 + b * th;
                    arm.push((r * cos(th), r * sin(th)));
                }
                let s = arm[0];
                let h0 = atan2(self.ds_r0, b) + PI;
                let rr = self.ds_cross_r;
                let leg = |delta: f64| {
                    let sg = if delta >= 0.0 { 1.0 } else { -1.0 };
                    let cx = s.0 + rr * cos(h0 + sg * PI / 2.0);
                    let cy = s.1 + rr * sin(h0 + sg * PI / 2.0);
                    let a0 = atan2(s.1 - cy, s.0 - cx);
                    let ex = cx + rr * cos(a0 + delta);
                    let ey = cy + rr * sin(a0 + delta);
                    let h1 = h0 + delta;
                    let perp = -sin(h1) * -ex + cos(h1) * -ey;
                    let along = -ex * cos(h1) + -ey * sin(h1);
                    ((cx, cy), a0, perp, along)
                };
                let found = find_crossing(|d| leg(d).2, |d| leg(d).3).ok_or_else(|| {
                    format!(
                        "no crossover arc reaches the centre at --ds-cross-r={}, --ds-r0={}.",
                        g(self.ds_cross_r),
                        g(self.ds_r0)
                    )
                })?;
                let ((cx, cy), a0, _, _) = leg(found);
                let steps = 1i64.max((py::degrees(found).abs() / self.facet).ceil() as i64);
                let mut cross: Vec<P> = (1..=steps)
                    .map(|i| {
                        (
                            cx + rr * cos(a0 + found * i as f64 / steps as f64),
                            cy + rr * sin(a0 + found * i as f64 / steps as f64),
                        )
                    })
                    .collect();
                cross.push((0.0, 0.0));
                let mut half: Vec<P> = arm.iter().rev().copied().collect();
                half.extend(cross);
                let mut pts = half.clone();
                pts.extend(half.iter().rev().skip(1).map(|&(x, y)| (-x, -y)));
                if self.ds_half {
                    pts = half.iter().rev().copied().collect();
                }
                Ok(flip(self.tails(pts)))
            }
            "serpentine" | TLS => {
                let mut spec = vec![Seg::S(self.lead), Seg::A(90.0, 1.0)];
                for i in 0..self.lobes.max(0) {
                    spec.push(Seg::A(180.0, if i % 2 == 0 { -1.0 } else { 1.0 }));
                    if i < self.lobes - 1 {
                        spec.push(Seg::S(self.rise));
                    }
                }
                if self.shape == TLS {
                    spec.push(Seg::A(90.0, 1.0));
                }
                spec.push(Seg::S(self.lead));
                Ok(flip(self.walk(&spec)?))
            }
            _ => {
                let mut known: Vec<&str> = SHAPES.to_vec();
                known.sort();
                Err(format!("--shape={} is not a shape here. Known: {}.", self.shape, known.join(" ")))
            }
        }
    }

    fn tails(&self, pts: Vec<P>) -> Vec<P> {
        let n = pts.len();
        let mut out = vec![tail(self.lead, pts[0], pts[1])];
        let last = tail(self.lead, pts[n - 1], pts[n - 2]);
        out.extend(pts);
        out.push(last);
        out
    }

    /// (inner, outer) offset polylines, named by which one is actually inside.
    pub fn walls(&self, poly: &[P]) -> (Vec<P>, Vec<P>) {
        let w = self.wall_off();
        let (a, b) = (offset(poly, w), offset(poly, -w));
        let la = fsum(a.windows(2).map(|s| seglen(s[0], s[1])));
        let lb = fsum(b.windows(2).map(|s| seglen(s[0], s[1])));
        if la < lb {
            (a, b)
        } else {
            (b, a)
        }
    }

    /// Where the tabs sit along a panel of length L, as offsets from centre:
    /// as many alternating tooth-and-gap as fit.
    pub fn teeth(&self, l: f64) -> Vec<f64> {
        let n = 1i64.max(floordiv(l - 2.0 * self.shoulder + self.tooth, 2.0 * self.tooth) as i64);
        (0..n).map(|i| (i as f64 - (n - 1) as f64 / 2.0) * 2.0 * self.tooth).collect()
    }

    /// One wall panel, flat, centred on the origin, kerf already taken out:
    /// every edge with material behind it is drawn BURN/2 outboard.
    pub fn panel(&self, l: f64, cs: Option<&[f64]>) -> Vec<P> {
        let e = self.burn / 2.0;
        let (hl, ht) = (l / 2.0 + e, self.tooth / 2.0 + e);
        let (hb, tip) = (self.bore / 2.0 + e, self.bore / 2.0 + self.thick + e);
        let own;
        let cs = match cs {
            Some(c) => c,
            None => {
                own = self.teeth(l);
                &own[..]
            }
        };
        let mut out = vec![(-hl, -hb)];
        for &c in cs {
            out.extend([(c - ht, -hb), (c - ht, -tip), (c + ht, -tip), (c + ht, -hb)]);
        }
        out.extend([(hl, -hb), (hl, hb)]);
        for &c in cs.iter().rev() {
            out.extend([(c + ht, hb), (c + ht, tip), (c - ht, tip), (c - ht, hb)]);
        }
        out.push((-hl, hb));
        out
    }

    /// The plate that closes the duct's open end: square, 2*THICK + BORE a
    /// side, kerf over, glued not tabbed.
    pub fn cap_poly(&self) -> Vec<P> {
        let e = self.burn / 2.0;
        let hw = (2.0 * self.thick + self.bore) / 2.0 + e;
        vec![(-hw, -hw), (hw, -hw), (hw, hw), (-hw, hw)]
    }

    /// The cheek's mortice for one tab: drawn BURN UNDER size, PLAY per side
    /// out of the notch and never off the tab.
    pub fn slot(&self, mid: P, ang: f64) -> Vec<P> {
        let e = self.burn / 2.0;
        let hw = (self.tooth + 2.0 * self.play() - self.slot_tighten) / 2.0 - e;
        let hh = self.slot_half();
        [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
            .iter()
            .map(|p| (mid.0 + p.0 * cos(ang) - p.1 * sin(ang), mid.1 + p.0 * sin(ang) + p.1 * cos(ang)))
            .collect()
    }

    /// Every mortice for one panel, one per tooth, placed on its segment.
    pub fn slots_for(&self, part: &Part) -> Vec<Vec<P>> {
        let (mx, my) = part.mid;
        let (ca, sa) = (cos(part.ang), sin(part.ang));
        let own;
        let cs = match &part.teeth {
            Some(t) => t,
            None => {
                own = self.teeth(part.len);
                &own
            }
        };
        cs.iter().map(|&c| self.slot((mx + c * ca, my + c * sa), part.ang)).collect()
    }

    /// The flat face: a ribbon of the bore plus a flange each side, out along
    /// one offset and back along the other.
    pub fn cheek(&self, poly: &[P]) -> Vec<P> {
        let d = self.cheek_off();
        let mut a = offset(poly, d);
        let b = offset(poly, -d);
        a.extend(b.into_iter().rev());
        a
    }

    /// This part's teeth, less any a port would cut into. A panel left with
    /// none is refused.
    pub fn teeth_kept(&self, part: &Part, portpolys: &[Vec<P>]) -> R<Vec<f64>> {
        let cs = part.cs.clone().unwrap_or_else(|| self.teeth(part.len));
        if portpolys.is_empty() {
            return Ok(cs);
        }
        let (mx, my) = part.mid;
        let (ca, sa) = (cos(part.ang), sin(part.ang));
        let mut out = Vec::new();
        for &c in &cs {
            let s = self.slot((mx + c * ca, my + c * sa), part.ang);
            let mut gs = Vec::new();
            for pp in portpolys {
                for i in 0..s.len() {
                    for j in 0..pp.len() {
                        gs.push(seg_gap(s[i], s[(i + 1) % s.len()], pp[j], pp[(j + 1) % pp.len()]));
                    }
                }
            }
            let gmin = fmin(gs);
            if gmin >= self.min_feature + self.burn - 1e-9 {
                out.push(c);
            }
        }
        if !cs.is_empty() && out.is_empty() {
            return Err(format!(
                "the port takes the only tooth on {} panel {} ({:.1}mm), which would leave it with no tab. A bore-square port passes within 0.16mm of a slot wherever it sits, so the room has to come from somewhere: narrow the port (7mm clears at the mouth by 1.66mm), or accept a glued panel.",
                part.wall, part.n, part.len
            ));
        }
        Ok(out)
    }

    /// Fold each wall's lead panel into its neighbour, keeping the
    /// neighbour's tag and teeth; under --port-both the tail lead too.
    pub fn merge_lead(&self, parts: Vec<Part>) -> R<Vec<Part>> {
        let mut parts = parts;
        let mut walls: Vec<String> = Vec::new();
        for p in &parts {
            if !walls.contains(&p.wall) {
                walls.push(p.wall.clone());
            }
        }
        let (mut dropped, mut gone) = (Vec::new(), Vec::new());
        for wall in &walls {
            let mut ps: Vec<usize> = (0..parts.len()).filter(|&i| &parts[i].wall == wall).collect();
            ps.sort_by_key(|&i| parts[i].n);
            let mut folds = vec![(ps[0], ps[1], -1.0)];
            if self.port_both {
                if ps.len() < 4 {
                    return Err(format!(
                        "--port-both needs at least four panels on each wall to fold a lead into a neighbour at both ends, and {} has {}.",
                        wall,
                        ps.len()
                    ));
                }
                folds.push((ps[ps.len() - 1], ps[ps.len() - 2], 1.0));
            }
            for (li, ni, sgn) in folds {
                let (lead, nxt) = (parts[li].clone(), parts[ni].clone());
                let d = (pymod(nxt.ang - lead.ang + PI, 2.0 * PI) - PI).abs();
                if py::degrees(d) > 1e-6 {
                    return Err(format!(
                        "{} panels {} and {} meet at {:.3} degrees, not in line, so merging them would move the airway. --merge-lead only folds a straight lead into the facet it already lies on.",
                        wall,
                        lead.n,
                        nxt.n,
                        py::degrees(d)
                    ));
                }
                let half = lead.len / 2.0;
                let (ux, uy) = (cos(nxt.ang), sin(nxt.ang));
                let q = &mut parts[ni];
                q.label_mid = Some(q.mid);
                q.mid = (q.mid.0 + sgn * ux * half, q.mid.1 + sgn * uy * half);
                q.cs = Some(self.teeth(nxt.len).into_iter().map(|c| c - sgn * half).collect());
                q.len = lead.len + nxt.len;
                dropped.push(format!("{} {}", wall, lead.tag));
                gone.push((wall.clone(), lead.n));
            }
        }
        let out: Vec<Part> = parts.into_iter().filter(|p| !gone.contains(&(p.wall.clone(), p.n))).collect();
        println!(
            "  --merge-lead: folded the {} into its neighbour on both walls, dropping {}; every other panel keeps its number and its teeth",
            if self.port_both { "lead panel at each END" } else { "lead panel" },
            dropped.join(", ")
        );
        Ok(out)
    }

    /// Every part, in millimetres, with the numbers each one carries.
    pub fn build(&self) -> R<(Vec<P>, Vec<P>, Vec<P>, Vec<Part>, Vec<(String, String, f64)>)> {
        let c = self.centreline()?;
        let (inn, out) = self.walls(&c);
        let mut parts = Vec::new();
        let mut report = Vec::new();
        let mut seq = 0usize;
        let cl = &c;
        // How far the wall turns at vertex k. A free end turns through 0; a
        // closed polyline has no free end, and wraps.
        let turn_at = |poly: &[P], k: usize| -> f64 {
            let n = poly.len();
            let shut = (poly[0].0 - poly[n - 1].0).abs() < 1e-9 && (poly[0].1 - poly[n - 1].1).abs() < 1e-9;
            if k == 0 || k >= n - 1 {
                if !shut {
                    return 0.0;
                }
                let h1 = atan2(poly[n - 1].1 - poly[n - 2].1, poly[n - 1].0 - poly[n - 2].0);
                let h2 = atan2(poly[1].1 - poly[0].1, poly[1].0 - poly[0].0);
                return (pymod(h2 - h1 + PI, 2.0 * PI) - PI).abs();
            }
            let h1 = atan2(poly[k].1 - poly[k - 1].1, poly[k].0 - poly[k - 1].0);
            let h2 = atan2(poly[k + 1].1 - poly[k].1, poly[k + 1].0 - poly[k].0);
            (pymod(h2 - h1 + PI, 2.0 * PI) - PI).abs()
        };
        for (name, poly) in [("inner", &inn), ("outer", &out)] {
            for i in 1..poly.len() {
                let (a, b) = (poly[i - 1], poly[i]);
                // A panel end is a SQUARE cut, so on the concave side its ply
                // runs past the mitre and jams; trim each end back to where
                // the concave corners just touch.
                let e0 = self.thick / 2.0 * tan(turn_at(poly, i - 1) / 2.0);
                let e1 = self.thick / 2.0 * tan(turn_at(poly, i) / 2.0);
                let l = seglen(a, b) - e0 - e1;
                if l < self.tooth + 2.0 * self.shoulder {
                    return Err(format!(
                        "{name} panel {i} is {l:.2}mm and a {}mm tooth with {}mm shoulders needs {}mm. Open the bend radius or coarsen --facet; the tooth does not scale with the bore.",
                        g(self.tooth),
                        g(self.shoulder),
                        g(self.tooth + 2.0 * self.shoulder)
                    ));
                }
                let ang = atan2(b.1 - a.1, b.0 - a.0);
                let mid = (
                    (a.0 + b.0) / 2.0 + (e0 - e1) / 2.0 * cos(ang),
                    (a.1 + b.1) / 2.0 + (e0 - e1) / 2.0 * sin(ang),
                );
                // away from the bore, measured from the centreline's midpoint
                let m0 = ((cl[i - 1].0 + cl[i].0) / 2.0, (cl[i - 1].1 + cl[i].1) / 2.0);
                let (dx, dy) = (mid.0 - m0.0, mid.1 - m0.1);
                let mut dl = hypot(dx, dy);
                if dl == 0.0 {
                    dl = 1.0;
                }
                seq += 1;
                let tag = format!("{seq:X}");
                parts.push(Part {
                    wall: name.into(),
                    n: i,
                    len: l,
                    mid,
                    ang,
                    out: (dx / dl, dy / dl),
                    tag: tag.clone(),
                    ..Default::default()
                });
                report.push((tag, name.to_string(), l));
            }
        }
        if self.merge_lead {
            parts = self.merge_lead(parts)?;
            report = parts.iter().map(|q| (q.tag.clone(), q.wall.clone(), q.len)).collect();
        }
        let portpolys = self.port_holes(&c)?;
        for k in 0..parts.len() {
            let t = self.teeth_kept(&parts[k], &portpolys)?;
            parts[k].teeth = Some(t);
        }
        Ok((c, inn, out, parts, report))
    }

    /// A slot through the cheek at an end of the run, or on a named facet:
    /// PORT_ACROSS x PORT_ALONG, PORT_FROM_TIP along, drawn BURN under size.
    pub fn port_hole(&self, cline: &[P], end: End) -> R<Vec<P>> {
        let n = cline.len();
        let (a, b) = match end {
            End::Facet(i) => (cline[i], cline[i + 1]),
            End::Mouth => (cline[0], cline[1]),
            End::Tail => (cline[n - 1], cline[n - 2]),
        };
        let (mut ux, mut uy) = (b.0 - a.0, b.1 - a.1);
        let m = hypot(ux, uy);
        if self.port_from_tip - self.port_along / 2.0 < 0.0 || self.port_from_tip + self.port_along / 2.0 > m {
            let wh = match end {
                End::Facet(i) => format!("facet {i}"),
                End::Mouth => "the mouth lead".into(),
                End::Tail => "the tail lead".into(),
            };
            return Err(format!(
                "the port spans {:.2} to {:.2}mm along {}, which is {:.2}mm long. Move it along with --port-from-tip, or name a facet with room for it.",
                self.port_from_tip - self.port_along / 2.0,
                self.port_from_tip + self.port_along / 2.0,
                wh,
                m
            ));
        }
        ux /= m;
        uy /= m;
        let (nx, ny) = (-uy, ux);
        let ha = self.port_across / 2.0 - self.burn / 2.0;
        let hl = self.port_along / 2.0 - self.burn / 2.0;
        let mid = (a.0 + ux * self.port_from_tip, a.1 + uy * self.port_from_tip);
        Ok(vec![
            (mid.0 + ux * hl + nx * ha, mid.1 + uy * hl + ny * ha),
            (mid.0 + ux * hl - nx * ha, mid.1 + uy * hl - ny * ha),
            (mid.0 - ux * hl - nx * ha, mid.1 - uy * hl - ny * ha),
            (mid.0 - ux * hl + nx * ha, mid.1 - uy * hl + ny * ha),
            (mid.0 + ux * hl + nx * ha, mid.1 + uy * hl + ny * ha),
        ])
    }

    /// Every port on this design, mouth first. Empty without --port. ONE
    /// place decides how many there are.
    pub fn port_holes(&self, cline: &[P]) -> R<Vec<Vec<P>>> {
        if !self.port {
            return Ok(vec![]);
        }
        if let Some(at) = &self.port_at {
            let n = cline.len() as i64 - 1;
            for &i in at {
                if !(0 <= i && i < n) {
                    return Err(format!(
                        "--port-at names facet {i} and this centreline has {n}, numbered 0 to {}.",
                        n - 1
                    ));
                }
            }
            let mut seen = at.clone();
            seen.sort();
            seen.dedup();
            if seen.len() != at.len() {
                return Err(format!(
                    "--port-at names the same facet twice: {}. Two holes in one facet would be two mouths a bore apart, which is not a thing this file knows how to cut.",
                    py::ints_repr(at)
                ));
            }
            return at.iter().map(|&i| self.port_hole(cline, End::Facet(i as usize))).collect();
        }
        let mut v = vec![self.port_hole(cline, End::Mouth)?];
        if self.port_both {
            v.push(self.port_hole(cline, End::Tail)?);
        }
        Ok(v)
    }

    /// (the cheeks, the panels): ONE cheek cut twice, or one per port under
    /// --port-per-cheek; then the panels and any caps.
    pub fn items_for<'a>(&'a self, parts: &'a [Part], cheekpoly: &[P], cline: &'a [P]) -> R<(Vec<Item<'a>>, Vec<Item<'a>>)> {
        let mut out = Vec::new();
        let holes_all = self.port_holes(cline)?;
        let subsets: Vec<Vec<Vec<P>>> = if !self.port_per_cheek {
            vec![holes_all.clone()]
        } else {
            holes_all.iter().map(|p| vec![p.clone()]).collect()
        };
        for (k, mine) in subsets.into_iter().enumerate() {
            let mine2 = mine.clone();
            let marks = move |dx: f64, dy: f64| -> Vec<String> {
                let mut m = Vec::new();
                let mut dropped: Vec<String> = Vec::new();
                let holes: Vec<Vec<P>> =
                    mine2.iter().map(|pp| pp.iter().map(|q| (q.0 + dx, q.1 + dy)).collect()).collect();
                // Does a label of n glyphs, h tall, at this angle, hit a port?
                let fouls_at = |px: f64, py_: f64, ang: f64, h: f64, n: usize| -> bool {
                    if holes.is_empty() {
                        return false;
                    }
                    let (w, gap) = (h * 0.62, h * 0.18);
                    let total = n as f64 * w + (n as f64 - 1.0) * gap;
                    let (lo, hi) = (-total / 2.0, total / 2.0 + h * 0.38);
                    let (ca, sa) = (cos(ang), sin(ang));
                    for pp in &holes {
                        for i in 0..5 {
                            let u = lo + (hi - lo) * i as f64 / 4.0;
                            for v in [-h / 2.0, 0.0, h / 2.0] {
                                if in_poly(pp, px + u * ca - v * sa, py_ + u * sa + v * ca) {
                                    return true;
                                }
                            }
                        }
                    }
                    false
                };
                for q in parts {
                    let anchor = q.label_mid.unwrap_or(q.mid);
                    let (mx, my) = (anchor.0 + dx, anchor.1 + dy);
                    let (ox, oy) = q.out;
                    let off = self.thick / 2.0 + 1.5;
                    let (mut lx, mut ly) = (mx - ox * off, my - oy * off);
                    let nt = q.tag.chars().count();
                    let fouls = |px: f64, py_: f64| fouls_at(px, py_, q.ang, 2.0, nt);
                    if fouls(lx, ly) {
                        let b = self.bore;
                        let mut moved = false;
                        for d in [b, 2.0 * b, 3.0 * b, -b, b / 2.0, -b / 2.0, -2.0 * b] {
                            let (cx, cy) = (cos(q.ang) * d, sin(q.ang) * d);
                            if !fouls(lx + cx, ly + cy) {
                                lx += cx;
                                ly += cy;
                                moved = true;
                                break;
                            }
                        }
                        if !moved {
                            dropped.push(q.tag.clone());
                            continue;
                        }
                    }
                    m.extend(label(&q.tag, lx, ly, 2.0, q.ang));
                }
                let n = cline.len();
                let ends: Vec<(P, P)> = if self.port {
                    vec![(cline[n - 1], cline[n - 2]), (cline[0], cline[1])]
                } else {
                    vec![(cline[0], cline[1])]
                };
                let mut placed = false;
                'ends: for (a0, a1) in ends {
                    let ang = atan2(a1.1 - a0.1, a1.0 - a0.0);
                    for t in [0.22, 0.12, 0.35, 0.5, 0.75] {
                        let gx = a0.0 + (a1.0 - a0.0) * t + dx;
                        let gy = a0.1 + (a1.1 - a0.1) * t + dy;
                        if !fouls_at(gx, gy, ang, 2.6, 1) {
                            m.extend(label("0", gx, gy, 2.6, ang));
                            placed = true;
                            break 'ends;
                        }
                    }
                }
                if !placed {
                    dropped.push("0".into());
                }
                if !dropped.is_empty() {
                    println!(
                        "  note: {} cheek label(s) left off, {} -- no clear spot beside the port. The panels carry the same tags.",
                        dropped.len(),
                        dropped.join(", ")
                    );
                }
                m
            };
            let mut cheek_slots: Vec<Vec<P>> = parts.iter().flat_map(|q| self.slots_for(q)).collect();
            cheek_slots.extend(mine.iter().cloned());
            let note = if !self.port_per_cheek {
                "the cheek - CUT THIS SHEET TWICE".to_string()
            } else {
                format!(
                    "cheek {} - CUT THIS SHEET ONCE - carries {}",
                    ["A", "B"][k],
                    match &self.port_at {
                        Some(at) => format!("the port on facet {}", at[k]),
                        None => format!("the {} port", if k == 0 { "mouth" } else { "far end" }),
                    }
                )
            };
            out.push(Item { outline: cheekpoly.to_vec(), slots: cheek_slots, marks: Box::new(marks), note });
        }
        let mut pan = Vec::new();
        for q in parts {
            let w = q.len + self.burn;
            let h2 = (self.bore + 2.0 * self.thick + self.burn) / 2.0;
            let poly: Vec<P> =
                self.panel(q.len, q.teeth.as_deref()).into_iter().map(|(px, py_)| (px + w / 2.0, py_ + h2)).collect();
            let tag = q.tag.clone();
            pan.push(Item {
                outline: poly,
                slots: vec![],
                marks: Box::new(move |dx, dy| label(&tag, w / 2.0 + dx, h2 + dy, 3.2, 0.0)),
                note: String::new(),
            });
        }
        for _ in 0..self.caps() {
            let cw = 2.0 * self.thick + self.bore + self.burn;
            let poly: Vec<P> = self.cap_poly().into_iter().map(|(px, py_)| (px + cw / 2.0, py_ + cw / 2.0)).collect();
            pan.push(Item { outline: poly, slots: vec![], marks: Box::new(|_, _| vec![]), note: String::new() });
        }
        Ok((out, pan))
    }

    /// The tightest arc the centreline is built from, as a report quotes it.
    pub fn bend_radius(&self) -> f64 {
        match self.shape.as_str() {
            "ess" => fmin([self.wave_lead_r, self.wave_trough_r, self.wave_crest_r]),
            "spiral" => py::min(self.spiral_ri, self.spiral_ro),
            "double-spiral" => self.ds_cross_r,
            "double-volute" => self.vol_cross_r,
            "serpentine" | TLS => self.lobe_r,
            "scallop" => py::min(self.lobe_r, self.scallop_in_r),
            "racetrack" => py::min(self.lobe_r, self.race_cap_r),
            "oval" => {
                if self.oval_end_deg == 90.0 {
                    self.oval_end_r
                } else {
                    py::min(self.oval_end_r, self.oval_side_r)
                }
            }
            _ => self.radius,
        }
    }
}

/// Row-wrap into sheets inside BED minus a margin; a part bigger than that is
/// a refusal, not a smaller sheet.
pub fn pack<'a, 'b>(items: &[&'b Item<'a>], margin: f64, gap: f64) -> R<Vec<Vec<(&'b Item<'a>, f64, f64)>>> {
    let (use_w, use_h) = (BED_W - 2.0 * margin, BED_H - 2.0 * margin);
    let mut sheets = Vec::new();
    let mut cur = Vec::new();
    let (mut x, mut y, mut rowh) = (margin, margin, 0.0f64);
    for &it in items {
        let (x0, y0, x1, y1) = bbox(&it.outline);
        let (w, h) = (x1 - x0, y1 - y0);
        if w > use_w || h > use_h {
            return Err(format!(
                "a part is {w:.0} x {h:.0}mm and the usable area is {use_w:.0} x {use_h:.0} on a {} x {} bed. Nothing written. Shorten the bore, or add lobes so each half-circle is smaller.",
                g(BED_W),
                g(BED_H)
            ));
        }
        if x > margin && x + w > margin + use_w {
            if y + rowh + gap + h > margin + use_h {
                sheets.push(std::mem::take(&mut cur));
                x = margin;
                y = margin;
                rowh = 0.0;
            } else {
                x = margin;
                y = y + rowh + gap;
                rowh = 0.0;
            }
        }
        cur.push((it, x - x0, y - y0));
        x += w + gap;
        rowh = py::max(rowh, h);
    }
    if !cur.is_empty() {
        sheets.push(cur);
    }
    Ok(sheets)
}

fn grp(ds: &[String], col: &str, name: &str) -> String {
    if ds.is_empty() {
        return String::new();
    }
    let body: Vec<String> = ds.iter().map(|d| format!("    <path d=\"{d}\"/>")).collect();
    format!("  <g id=\"{name}\" fill=\"none\" stroke=\"{col}\" stroke-width=\"0.2\">\n{}\n  </g>\n", body.join("\n"))
}

/// os.path.splitext
pub fn splitext(p: &str) -> (String, String) {
    let base_at = p.rfind('/').map(|i| i + 1).unwrap_or(0);
    let base = &p[base_at..];
    let lead = base.len() - base.trim_start_matches('.').len();
    match base[lead..].rfind('.') {
        Some(i) => {
            let at = base_at + lead + i;
            (p[..at].to_string(), p[at..].to_string())
        }
        None => (p.to_string(), String::new()),
    }
}
pub fn basename(p: &str) -> &str {
    p.rsplit('/').next().unwrap_or(p)
}

impl Cfg {
    /// Write the cut files: the cheek on its own sheet, the panels on theirs.
    /// Colour is the cut order: blue engraves, then orange, then black.
    pub fn sheet(&self, parts: &[Part], cheekpoly: &[P], cline: &[P], path_out: &str, write: bool)
        -> R<(Vec<Written>, Vec<Ink>, Vec<(Vec<P>, String)>)> {
        let (cheeks, panels) = self.items_for(parts, cheekpoly, cline)?;
        self.sheet_items(parts, &cheeks, &panels, path_out, write)
    }

    /// sheet() for items already made: what lyre-harp uses, to cut its one
    /// cheek as two (in Python it swapped items_for() out for the call).
    pub fn sheet_items(&self, parts: &[Part], cheeks: &[Item], panels: &[Item], path_out: &str, write: bool)
        -> R<(Vec<Written>, Vec<Ink>, Vec<(Vec<P>, String)>)> {
        let over = 100.0 * (1.0 / cos(py::radians(self.facet) / 2.0) - 1.0);
        let (stem, ext) = splitext(path_out);
        let mut ink: Vec<Ink> = Vec::new();
        let mut cut_slots: Vec<(Vec<P>, String)> = Vec::new();
        let mut written: Vec<Written> = Vec::new();
        let mut write_sheet = |placed: &[(&Item, f64, f64)], path_here: String, note: &str, n: usize, of: usize| -> R<()> {
            let (mut marks, mut holes, mut cuts) = (Vec::new(), Vec::new(), Vec::new());
            for &(it, dx, dy) in placed {
                let here: Vec<P> = it.outline.iter().map(|q| (q.0 + dx, q.1 + dy)).collect();
                for ring in contours(&it.outline) {
                    let moved: Vec<P> = ring.iter().map(|q| (q.0 + dx, q.1 + dy)).collect();
                    cuts.push(path(&moved, true));
                }
                for sl in &it.slots {
                    let moved: Vec<P> = sl.iter().map(|q| (q.0 + dx, q.1 + dy)).collect();
                    holes.push(path(&moved, true));
                    cut_slots.push((moved, path_here.clone()));
                }
                for d in (it.marks)(dx, dy) {
                    for tok in d.replace("M ", "").replace('Z', "").split(" L ") {
                        let (a, b) = tok.trim().split_once(',').unwrap();
                        ink.push((a.parse().unwrap(), b.parse().unwrap(), here.clone(), path_here.clone()));
                    }
                    marks.push(d);
                }
            }
            let w = fmax(placed.iter().map(|&(it, dx, _)| bbox(&it.outline).2 + dx)) + MARGIN_S;
            let h = fmax(placed.iter().map(|&(it, _, dy)| bbox(&it.outline).3 + dy)) + MARGIN_S;
            let of_txt = if of > 1 { format!(", sheet {n} of {of}") } else { String::new() };
            let narrow = if self.narrow {
                "NARROW: the cheek is only as wide as the duct, so every mortice is open at the rim and each tab is held across its thickness on one side only. "
            } else {
                ""
            };
            let capt = if !self.cap {
                String::new()
            } else if self.caps() == 1 {
                format!(
                    "The plain {}mm square on the panels sheet is the end cap: it glues over the open end of the duct so the air turns into the port, it carries no number, and ONE is needed. ",
                    g(2.0 * self.thick + self.bore)
                )
            } else {
                format!(
                    "The two plain {}mm squares on the panels sheet are the end caps: each glues over one open end of the duct so the air turns into its port, they carry no number, and BOTH are needed. ",
                    g(2.0 * self.thick + self.bore)
                )
            };
            let body = format!(
                "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{w:.2}mm\" height=\"{h:.2}mm\" viewBox=\"0 0 {w:.2} {h:.2}\">\n<title>Ribbon bore, {} - {note}{of_txt} - {}mm square bore, {} degree facets</title>\n<desc>1 user unit = 1mm. {note}. A duct of constant {} x {}mm section swept along a planar curve; the two cheeks are the same part and both go on the same way up. {} wall panels in all, numbered along the flow. The airway is exact along every facet and {over:.1}% over at each mitre. {}mm ply, slots cut for a {}mm sheet at {}mm kerf, {}mm play per side taken out of the slot and never off the tab. {narrow}{capt}blue #0000ff engraves, orange #ff8000 cuts the slots first, black #000000 frees the parts.</desc>\n{}{}{}</svg>\n",
                self.shape,
                g(self.bore),
                g(self.facet),
                g(self.bore),
                g(self.bore),
                parts.len(),
                g(self.thick),
                g(self.sheet),
                g(self.burn),
                g(self.play()),
                grp(&marks, MARK, "numbers"),
                grp(&holes, INNER, "slots"),
                grp(&cuts, CUT, "outlines"),
            );
            if write {
                std::fs::write(&path_here, body).map_err(|e| format!("{e}"))?;
            }
            written.push((basename(&path_here).to_string(), w, h, placed.len(), note.to_string()));
            Ok(())
        };
        let mut groups: Vec<(String, Vec<&Item>, String)> = Vec::new();
        if cheeks.len() == 1 {
            groups.push(("cheek-x2".into(), vec![&cheeks[0]], cheeks[0].note.clone()));
        } else {
            for (i, ck) in cheeks.iter().enumerate() {
                groups.push((format!("cheek-{}", ["a", "b"][i]), vec![ck], ck.note.clone()));
            }
        }
        groups.push(("panels".into(), panels.iter().collect(), "the wall panels".into()));
        for (gname, items, note) in groups {
            let sheets = pack(&items, MARGIN_S, 4.0)?;
            let ns = sheets.len();
            for (n, placed) in sheets.into_iter().enumerate() {
                let tail = if ns > 1 { format!("-sheet{}", n + 1) } else { String::new() };
                write_sheet(&placed, format!("{stem}-{gname}{tail}-cut-files{ext}"), &note, n + 1, ns)?;
            }
        }
        Ok((written, ink, cut_slots))
    }

    /// Is cheek B cheek A turned half a turn about the ports' midpoint? Worst
    /// mismatch in mm, or None. Reported, not checked.
    pub fn rotatable(&self, cheekpoly: &[P], parts: &[Part], cline: &[P]) -> R<Option<f64>> {
        let ports = self.port_holes(cline)?;
        if ports.len() != 2 {
            return Ok(None);
        }
        let ctr = |pp: &[P]| (fsum(pp[..4].iter().map(|q| q.0)) / 4.0, fsum(pp[..4].iter().map(|q| q.1)) / 4.0);
        let ((ax, ay), (bx, by)) = (ctr(&ports[0]), ctr(&ports[1]));
        let (ox, oy) = ((ax + bx) / 2.0, (ay + by) / 2.0);
        let turned = |pts: &[P]| -> Vec<P> { pts.iter().map(|&(x, y)| (2.0 * ox - x, 2.0 * oy - y)).collect() };
        let worst = |a: &[P], b: &[P]| -> Option<f64> {
            if a.len() != b.len() {
                return None;
            }
            let mut rem: Vec<usize> = (0..b.len()).collect();
            let mut w = 0.0f64;
            for q in a {
                let mut best = 0usize;
                for (pos, &k) in rem.iter().enumerate() {
                    if hypot(q.0 - b[k].0, q.1 - b[k].1) < hypot(q.0 - b[rem[best]].0, q.1 - b[rem[best]].1) {
                        best = pos;
                    }
                }
                let j = rem[best];
                w = py::max(w, hypot(q.0 - b[j].0, q.1 - b[j].1));
                rem.remove(best);
            }
            Some(w)
        };
        let mort: Vec<P> = parts.iter().flat_map(|p| self.slots_for(p)).flatten().collect();
        let ws = [
            worst(cheekpoly, &turned(cheekpoly)),
            worst(&mort, &turned(&mort)),
            worst(&ports[0][..4], &turned(&ports[1][..4])),
        ];
        if ws.iter().any(|w| w.is_none()) {
            return Ok(None);
        }
        Ok(Some(fmax(ws.iter().map(|w| w.unwrap()))))
    }

    /// Can a cheek be turned over and still meet every tab? The angle in
    /// degrees at which its mirror matches it, or None. Reported, not checked.
    pub fn flippable(&self, cheekpoly: &[P], parts: &[Part]) -> Option<f64> {
        let mut pts: Vec<P> = cheekpoly.to_vec();
        pts.extend(parts.iter().flat_map(|p| self.slots_for(p)).flatten());
        let shift = |ps: Vec<P>| -> Vec<P> {
            let x0 = fmin(ps.iter().map(|q| q.0));
            let y0 = fmin(ps.iter().map(|q| q.1));
            ps.into_iter().map(|q| (q.0 - x0, q.1 - y0)).collect()
        };
        let base = shift(pts.clone());
        for k in 0..720 {
            let a = py::radians(k as f64 * 0.5);
            let (c, sn) = (cos(a), sin(a));
            let t = shift(pts.iter().map(|&(x, y)| (x * c + y * sn, x * sn - y * c)).collect());
            if t.len() != base.len() {
                continue;
            }
            let mut left: Vec<usize> = (0..t.len()).collect();
            let mut worst = 0.0f64;
            for u in &base {
                let key = |i: usize| py::powf(t[i].0 - u.0, 2.0) + py::powf(t[i].1 - u.1, 2.0);
                let mut best = 0usize;
                let mut bk = key(left[0]);
                for (pos, &i) in left.iter().enumerate().skip(1) {
                    let kk = key(i);
                    if kk < bk {
                        bk = kk;
                        best = pos;
                    }
                }
                let j = left[best];
                let d = hypot(t[j].0 - u.0, t[j].1 - u.1);
                if d > worst {
                    worst = d;
                }
                if worst > 0.02 {
                    break;
                }
                left.remove(best);
            }
            if worst <= 0.02 && left.is_empty() {
                return Some(k as f64 * 0.5);
            }
        }
        None
    }
}

/// (ok, what, detail)
pub type Check = (bool, String, String);

fn overlap(p: &[P], q: &[P]) -> bool {
    for r in [p, q] {
        for k in 0..4 {
            let ex = r[(k + 1) % 4].0 - r[k].0;
            let ey = r[(k + 1) % 4].1 - r[k].1;
            let (nx, ny) = (-ey, ex);
            let a: Vec<f64> = p.iter().map(|&(x, y)| nx * x + ny * y).collect();
            let b: Vec<f64> = q.iter().map(|&(x, y)| nx * x + ny * y).collect();
            if fmin(a.iter().copied()) >= fmax(b.iter().copied()) - 1e-7
                || fmin(b.iter().copied()) >= fmax(a.iter().copied()) - 1e-7
            {
                return false;
            }
        }
    }
    true
}

impl Cfg {
    fn plan_rect(&self, q: &Part) -> Vec<P> {
        let (hl, ht) = (q.len / 2.0, self.thick / 2.0);
        let (ca, sa) = (cos(q.ang), sin(q.ang));
        let (mx, my) = q.mid;
        [(-1.0, -1.0), (1.0, -1.0), (1.0, 1.0), (-1.0, 1.0)]
            .iter()
            .map(|&(u, v): &(f64, f64)| (mx + u * hl * ca - v * ht * sa, my + u * hl * sa + v * ht * ca))
            .collect()
    }

    /// What has to be true, said out loud with the number that makes it true.
    #[allow(clippy::too_many_arguments)]
    pub fn checks(&self, c: &[P], inn: &[P], out: &[P], parts: &[Part], cheekpoly: &[P], written: &[Written],
                  ink: &[Ink], cut_slots: &[(Vec<P>, String)]) -> R<Vec<Check>> {
        let mut res: Vec<Check> = Vec::new();
        let mut note = |ok: bool, what: &str, detail: String| res.push((ok, what.to_string(), detail));
        let (bore, burn) = (self.bore, self.burn);

        // the whole point: the section is the bore, everywhere along a facet
        let (mut worst, mut n) = (0.0f64, 0usize);
        for (s, t) in inn.windows(2).zip(out.windows(2)) {
            let (a, b, p, q) = (s[0], s[1], t[0], t[1]);
            for tt in [0.15, 0.35, 0.5, 0.65, 0.85] {
                let m = (a.0 + (b.0 - a.0) * tt, a.1 + (b.1 - a.1) * tt);
                let (ux, uy) = (q.0 - p.0, q.1 - p.1);
                let l2 = ux * ux + uy * uy;
                let s = ((m.0 - p.0) * ux + (m.1 - p.1) * uy) / l2;
                let f = (p.0 + ux * s, p.1 + uy * s);
                let air = hypot(f.0 - m.0, f.1 - m.1) - self.thick;
                worst = py::max(worst, (air - bore).abs());
                n += 1;
            }
        }
        note(n > 0 && worst < 1e-9, "the airway is the bore along every facet",
             format!("{n} stations, worst {}mm from {} (wall face to wall face)", py::e(worst, 2), g(bore)));

        // every slot has to be in the cheek, or a tab has nothing to enter
        let mortices: Vec<Vec<P>> = parts.iter().flat_map(|p| self.slots_for(p)).collect();
        let ports = self.port_holes(c)?;
        let mut allslots = mortices.clone();
        allslots.extend(ports.iter().cloned());
        let np = cheekpoly.len();
        let held = |pt: P| -> bool {
            if inside(cheekpoly, pt.0, pt.1) {
                return true;
            }
            self.narrow && fmin((0..np).map(|i| pt_seg(pt, cheekpoly[(i + np - 1) % np], cheekpoly[i]))) <= burn / 2.0
        };
        let off = allslots.iter().flatten().filter(|&&pt| !held(pt)).count();
        note(off == 0 && !allslots.is_empty(), "every slot corner is inside its cheek",
             format!("{} corners on {} slots, {off} outside", 4 * allslots.len(), allslots.len()));

        // and no two slots may run into each other: separating axis
        let apart = |a: &[P], b: &[P]| -> bool {
            for r in [a, b] {
                for i in 0..r.len() {
                    let (ax, ay) = (r[(i + 1) % r.len()].0 - r[i].0, r[(i + 1) % r.len()].1 - r[i].1);
                    let (px, py_) = (-ay, ax);
                    let pa: Vec<f64> = a.iter().map(|q| q.0 * px + q.1 * py_).collect();
                    let pb: Vec<f64> = b.iter().map(|q| q.0 * px + q.1 * py_).collect();
                    if fmax(pa.iter().copied()) <= fmin(pb.iter().copied())
                        || fmax(pb.iter().copied()) <= fmin(pa.iter().copied())
                    {
                        return true;
                    }
                }
            }
            false
        };
        let pairs: Vec<(usize, usize)> =
            (0..allslots.len()).flat_map(|i| (i + 1..allslots.len()).map(move |j| (i, j))).collect();
        let bad = pairs.iter().filter(|&&(i, j)| !apart(&allslots[i], &allslots[j])).count();
        note(!pairs.is_empty() && bad == 0, "no two slots overlap", format!("{} pairs, {bad} overlapping", pairs.len()));

        // and OVERLAP is the wrong question: ask for material after the kerf
        let (mut tight, mut worst) = (0usize, f64::INFINITY);
        for &(i, j) in &pairs {
            let (a, b) = (&allslots[i], &allslots[j]);
            let mut gv = Vec::with_capacity(a.len() * b.len());
            for x in 0..a.len() {
                for y in 0..b.len() {
                    gv.push(seg_gap(a[x], a[(x + 1) % a.len()], b[y], b[(y + 1) % b.len()]));
                }
            }
            let gg = fmin(gv);
            worst = py::min(worst, gg);
            if gg - burn < self.min_feature - 1e-9 {
                tight += 1;
            }
        }
        note(!pairs.is_empty() && tight == 0, "the ply between two holes survives the kerf",
             if !pairs.is_empty() {
                 format!("narrowest {worst:.3}mm drawn, {:.3}mm left after a {}mm kerf, against {}mm needed",
                         worst - burn, g(burn), g(self.min_feature))
             } else {
                 "no two holes to measure between".into()
             });

        // the panels have to fit round the bend as SOLIDS, not as lines
        let mut walls: Vec<(String, Vec<Vec<P>>)> = Vec::new();
        for q in parts {
            match walls.iter_mut().find(|(w, _)| *w == q.wall) {
                Some((_, v)) => v.push(self.plan_rect(q)),
                None => walls.push((q.wall.clone(), vec![self.plan_rect(q)])),
            }
        }
        let (mut npair, mut jam) = (0usize, 0usize);
        for (_, rs) in &walls {
            for i in 0..rs.len() {
                for j in i + 1..rs.len() {
                    npair += 1;
                    if overlap(&rs[i], &rs[j]) {
                        jam += 1;
                    }
                }
            }
        }
        note(npair > 0 && jam == 0, "no two wall panels share plan area",
             format!("{npair} pairs on {} walls, {jam} jamming", walls.len()));

        // the walls as SOLIDS, against their neighbours along the run
        let rect_dist = |p: &[P], q: &[P]| -> f64 {
            if overlap(p, q) {
                return 0.0;
            }
            let mut v = Vec::with_capacity(16);
            for i in 0..4 {
                for j in 0..4 {
                    v.push(seg_gap(p[i], p[(i + 1) % 4], q[j], q[(j + 1) % 4]));
                }
            }
            fmin(v)
        };
        const NEAR: usize = 3;
        let ins: Vec<Vec<P>> = parts.iter().filter(|q| q.wall == "inner").map(|q| self.plan_rect(q)).collect();
        let ous: Vec<Vec<P>> = parts.iter().filter(|q| q.wall == "outer").map(|q| self.plan_rect(q)).collect();
        let (mut gap, mut npr) = (f64::INFINITY, 0usize);
        for (i, a) in ins.iter().enumerate() {
            for j in i.saturating_sub(NEAR)..ous.len().min(i + NEAR + 1) {
                gap = py::min(gap, rect_dist(a, &ous[j]));
                npr += 1;
            }
        }
        note(npr > 0 && gap >= bore - 1e-6, "the two walls stand a bore apart",
             format!("{npr} neighbouring panel pairs, narrowest gap {gap:.4}mm against {}mm", g(bore)));

        // the tooth does not scale, so short panels are the failure mode
        let short = fmin(parts.iter().map(|p| p.len));
        note(short >= self.tooth + 2.0 * self.shoulder, "the shortest panel still holds a tooth",
             format!("{short:.2}mm against {}mm needed", g(self.tooth + 2.0 * self.shoulder)));

        let off = ink.iter().filter(|(x, y, owner, _)| !inside(owner, *x, *y)).count();
        note(off == 0 && !ink.is_empty(), "every engraved point is on its own part",
             format!("{} points, {off} off the material", ink.len()));

        // a number engraved over a slot is engraved into a hole
        let over = ink
            .iter()
            .filter(|(x, y, _, f)| cut_slots.iter().any(|(sl, f2)| f2 == f && inside(sl, *x, *y)))
            .count();
        let ncheek = if self.port_per_cheek { 2 } else { 1 };
        let want = mortices.len() * ncheek + ports.len();
        note(over == 0 && cut_slots.len() == want, "no engraving lands in a slot",
             format!("{} points against {} slots ({} mortices on {ncheek} cheek sheet(s) plus {} port(s), so {want} expected), {over} inside one",
                     ink.len(), cut_slots.len(), mortices.len(), ports.len()));

        // the cheek is one piece and it must not cross itself
        let edges_cross = |a: P, b: P, c: P, d: P| -> bool {
            let d1 = (b.0 - a.0, b.1 - a.1);
            let d2 = (d.0 - c.0, d.1 - c.1);
            let den = d1.0 * d2.1 - d1.1 * d2.0;
            if den.abs() < 1e-12 {
                return false;
            }
            let u = ((c.0 - a.0) * d2.1 - (c.1 - a.1) * d2.0) / den;
            let v = ((c.0 - a.0) * d1.1 - (c.1 - a.1) * d1.0) / den;
            1e-9 < u && u < 1.0 - 1e-9 && 1e-9 < v && v < 1.0 - 1e-9
        };
        let ring = cheekpoly;
        let m = ring.len() - 1;
        let mut bad_edges = Vec::new();
        for i in 0..m {
            for j in i + 2..m {
                if !(i == 0 && j == m - 1) && edges_cross(ring[i], ring[i + 1], ring[j], ring[j + 1]) {
                    bad_edges.push((i, j));
                }
            }
        }
        note(bad_edges.is_empty(), "the cheek outline does not cross itself",
             format!("{m} edges, {} crossing{}", bad_edges.len(),
                     bad_edges.first().map(|(i, j)| format!(", first at ({i}, {j})")).unwrap_or_default()));

        // the web, measured off the drawing over the contours as cut
        let rim: Vec<(P, P)> = contours(ring).iter().flat_map(|r| r.windows(2).map(|w| (w[0], w[1])).collect::<Vec<_>>()).collect();
        let to_rim = |sl: &[P]| -> f64 { fmin(sl.iter().flat_map(|&q| rim.iter().map(move |&(a, b)| pt_seg(q, a, b)))) };
        if self.narrow {
            let gap = if mortices.is_empty() { 0.0 } else { fmax(mortices.iter().map(|sl| to_rim(sl))) };
            note(gap <= burn / 2.0, "the rim is flush with every mortice",
                 format!("furthest of {} mortices {gap:.4}mm from the rim against {}mm allowed, band {}mm wide, and every mortice open at the rim",
                         mortices.len(), g(burn / 2.0), g(self.band())));
            if self.port {
                let pw = fmin(ports.iter().map(|pp| to_rim(pp)));
                note(pw >= 1.5, "the port keeps a cuttable web",
                     format!("{} port(s), narrowest port to rim {pw:.3}mm against 1.5mm needed", ports.len()));
            }
        } else {
            let web = if allslots.is_empty() { 0.0 } else { fmin(allslots.iter().map(|sl| to_rim(sl))) };
            note(web >= 1.5, "the web outboard of a slot is cuttable",
                 format!("narrowest slot to rim {web:.3}mm against 1.5mm needed, band {}mm wide", g(self.band())));
        }

        // no cut line runs through the airway
        let nc = c.len();
        let shut = hypot(c[0].0 - c[nc - 1].0, c[0].1 - c[nc - 1].1) < 1e-9;
        let off_air = |q: P| -> bool {
            let dist = fmin(c.windows(2).map(|w| pt_seg(q, w[0], w[1])));
            if !shut && fmin([c[0], c[nc - 1]].iter().map(|e| hypot(q.0 - e.0, q.1 - e.1))) <= dist + 1e-6 {
                return true;
            }
            dist >= bore / 2.0 - 1e-6
        };
        let cs = contours(cheekpoly);
        let mut across = 0usize;
        for r in &cs {
            for w in r.windows(2) {
                let (a, b) = (w[0], w[1]);
                for t in [0.25, 0.5, 0.75] {
                    if !off_air((a.0 + (b.0 - a.0) * t, a.1 + (b.1 - a.1) * t)) {
                        across += 1;
                    }
                }
            }
        }
        note(across == 0, "no cut line crosses the airway",
             format!("{} cheek contour(s), {across} point(s) inside the airway", cs.len()));

        let big = written.iter().filter(|w| w.1 > BED_W || w.2 > BED_H).count();
        note(big == 0 && !written.is_empty(), "every sheet fits the P2S bed",
             format!("{} sheet(s), largest {:.0} x {:.0}mm against {} x {}", written.len(),
                     fmax(written.iter().map(|w| w.1)), fmax(written.iter().map(|w| w.2)), g(BED_W), g(BED_H)));
        Ok(res)
    }

    fn what(&self, r: f64) -> String {
        let s = self.shape.as_str();
        match s {
            "ess" => format!("an ess: a trough of R{} and a crest of R{}, level at both ends", g(self.wave_trough_r), g(self.wave_crest_r)),
            "spiral" => format!("a flat coil, {} facets, R{} at the centre out to R{} at the rim", self.spiral_facets, g(self.spiral_ri), g(self.spiral_ro)),
            "double-spiral" => format!(
                "two arms half a turn apart on an Archimedean spiral, {} facets each from R{}, rising {}mm a turn, crossed at the centre by a straight off R{}",
                self.ds_facets, g(self.ds_r0), g(self.ds_pitch), g(self.ds_cross_r)),
            "double-volute" => format!(
                "a double volute: a chain of {} semicircles an arm from R{} stepping {}mm a turn, the return arm interleaved half a turn away, joined at the eye by an arc off R{}",
                self.vol_semis, g(self.vol_r0), g(self.vol_step), g(self.vol_cross_r)),
            "serpentine" | TLS => format!("{} half-circles of R{} joined by {}mm straights{}", self.lobes, g(r), g(self.rise),
                if s == TLS { ", then a quarter turn to bring the ends opposed" } else { "" }),
            "torus" => format!("a closed ring of {} facets, R{} circumradius to the centreline vertices", py::round(360.0 / self.facet), g(r)),
            "scallop" => format!("a closed serpentine: {} lobes, a {} degree bulge of R{} against a {} degree scoop of R{}",
                self.lobes, g(self.scallop_in_deg + 360.0 / self.lobes as f64), g(self.lobe_r), g(self.scallop_in_deg), g(self.scallop_in_r)),
            "racetrack" => format!(
                "a closed serpentine racetrack: {} half-circles a side of R{}, alternating, joined by {}mm straights, and two 180 degree caps of R{}",
                self.lobes, g(self.lobe_r), g(self.race_straight), g(self.race_cap_r)),
            "oval" if self.oval_end_deg == 90.0 => format!("a stadium: two half-circles of R{} joined by two {}mm parallel straights{}",
                g(self.oval_end_r), g(self.oval_side_flat),
                if self.oval_flat != 0.0 { format!(", with a {}mm flat across each end", g(self.oval_flat)) } else { String::new() }),
            "oval" => format!(
                "a flattened oval: two {}mm flats across the long ends, each between two {} degree arcs of R{}, joined along the sides by {} degree arcs of R{}{}",
                g(self.oval_flat), g(self.oval_end_deg), g(self.oval_end_r), g(180.0 - 2.0 * self.oval_end_deg), g(self.oval_side_r),
                if self.oval_side_flat != 0.0 { format!(" with a {}mm straight in the middle of each", g(self.oval_side_flat)) } else { String::new() }),
            _ => unreachable!(),
        }
    }

    /// The file stem a design is written under, and the refusals that keep
    /// one design's sheets off another's.
    pub fn stem(&self, l: f64) -> R<String> {
        let (b, f) = (g(self.bore), g(self.facet));
        let mut stem = match self.shape.as_str() {
            "ess" => format!("ribbon-ess-bore{b}-{f}deg-{}arc-{l:.0}mm.svg", self.wave_lobe_arcs),
            "spiral" => format!("ribbon-spiral-bore{b}-{f}deg-R{:.0}to{:.0}-{l:.0}mm.svg", self.spiral_ri, self.spiral_ro),
            "double-spiral" => format!("ribbon-double-spiral-bore{b}-{f}deg-R{:.0}-pitch{:.0}-{}{l:.0}mm.svg",
                self.ds_r0, self.ds_pitch, if self.ds_half { "half-" } else { "" }),
            "double-volute" => format!("ribbon-double-volute-bore{b}-{f}deg-R{:.0}-step{:.0}-{l:.0}mm.svg", self.vol_r0, self.vol_step),
            "serpentine" | TLS => format!("{}-bore{b}-{f}deg-{}lobes-R{:.0}-{l:.0}mm.svg",
                if self.shape == TLS { TLS } else { "ribbon-serpentine" }, self.lobes, self.lobe_r),
            "torus" => format!("ribbon-torus-bore{b}-{f}deg-R{}.svg", g(self.radius)),
            "scallop" => format!("ribbon-scallop-bore{b}-{f}deg-{}lobes-R{}-in{}-{l:.0}mm.svg", self.lobes, g(self.lobe_r), g(self.scallop_in_r)),
            "racetrack" => format!("ribbon-racetrack-bore{b}-{f}deg-{}lobes-R{}-cap{}-{l:.0}mm.svg", self.lobes, g(self.lobe_r), g(self.race_cap_r)),
            "oval" if self.oval_end_deg == 90.0 => format!("ribbon-oval-bore{b}-{f}deg-R{}{}-straight{}-{l:.0}mm.svg", g(self.oval_end_r),
                if self.oval_flat != 0.0 { format!("-flat{}", g(self.oval_flat)) } else { String::new() }, g(self.oval_side_flat)),
            "oval" => format!("ribbon-oval-bore{b}-{f}deg-end{}-R{}-side-R{}-flat{}{}-{l:.0}mm.svg", g(self.oval_end_deg), g(self.oval_end_r),
                g(self.oval_side_r), g(self.oval_flat),
                if self.oval_side_flat != 0.0 { format!("-sideflat{}", g(self.oval_side_flat)) } else { String::new() }),
            _ => return Err(format!("no filename rule for --shape={}.", self.shape)),
        };
        let out_base = self.out.as_deref().map(basename);
        let add = |stem: &mut String, tag: &str| {
            *stem = format!("{}-{tag}.svg", &stem[..stem.len() - 4]);
        };
        if self.port {
            add(&mut stem, "ported");
            if let (Some(o), Some(b)) = (&self.out, out_base) {
                if !b.contains("ported") {
                    return Err(format!("--port with --out={o} would write the ported sheets under a name that does not say so, over the unported twin. Put \"ported\" in the --out name."));
                }
            }
        }
        if self.port_both {
            add(&mut stem, "both");
            if let (Some(o), Some(b)) = (&self.out, out_base) {
                if !b.contains("both") {
                    return Err(format!("--port-both with --out={o} would write the two-port sheets under a name that does not say so, over the one-port twin. Put \"both\" in the --out name."));
                }
            }
        }
        if let Some(at) = &self.port_at {
            let tag = format!("at{}", at.iter().map(|i| i.to_string()).collect::<Vec<_>>().join("-"));
            add(&mut stem, &tag);
            if let (Some(o), Some(b)) = (&self.out, out_base) {
                if !b.contains(&tag) {
                    return Err(format!("--port-at with --out={o} would write sheets whose ports are on facets {} under a name that does not say so, over the sheets of another placement. Put \"{tag}\" in the --out name.", py::ints_repr(at)));
                }
            }
        }
        if self.merge_lead && !self.port_square {
            add(&mut stem, "merged");
            if let (Some(o), Some(b)) = (&self.out, out_base) {
                if !b.contains("merged") {
                    return Err(format!("--merge-lead with --out={o} would write a sheet with two panels merged under a name that does not say so, over the unmerged twin. Put \"merged\" in the --out name."));
                }
            }
        }
        if self.port_square {
            add(&mut stem, "square");
            if let (Some(o), Some(b)) = (&self.out, out_base) {
                if !b.contains("square") {
                    return Err(format!("--port-square with --out={o} would write the square-ported sheets under a name that does not say so, over the 7 x 14 twin. Put \"square\" in the --out name."));
                }
            }
        }
        if self.narrow {
            add(&mut stem, "narrow");
            if let (Some(o), Some(b)) = (&self.out, out_base) {
                if !b.contains("narrow") {
                    return Err(format!("--narrow with --out={o} would write the narrow sheets under a name that does not say so, over the full-width twin. Put \"narrow\" in the --out name."));
                }
            }
        }
        Ok(stem)
    }

    /// The report, the sheets and the checks; 1 if a check failed.
    pub fn main(&self, write: bool) -> R<i32> {
        let (c, inn, out, parts, report) = self.build()?;
        let over = 100.0 * (1.0 / cos(py::radians(self.facet) / 2.0) - 1.0);
        let r = self.bend_radius();
        let what = self.what(r);
        let bore = self.bore;
        println!("ribbon bore, {}   {}mm square, {} degree facets", self.shape, g(bore), g(self.facet));
        println!("  {what}");
        let l = fsum(c.windows(2).map(|w| seglen(w[0], w[1])));
        println!("  centreline {l:.1}mm, section {} x {} = {:.0}mm2, +{over:.1}% at each mitre", g(bore), g(bore), bore * bore);
        let known = self.play_by_bore.iter().any(|(b, _)| *b == py::round_dp(bore, 3));
        println!("  bend R/bore = {:.1}; the inner wall runs at R{}", r / bore, g(r - bore / 2.0));
        println!("  play {}mm per side{}\n", g(self.play()),
                 if known { String::new() } else {
                     format!("  (the {}mm bore is not in PLAY_BY_BORE; this is the small-joint default. Measure it and add a row.)", g(bore))
                 });
        println!("  part   wall     length     tooth   shoulders");
        for (tag, wall, len) in &report {
            println!("  {tag:<5}  {wall:<7}  {len:>6.2}mm   {}mm    {:>5.2}mm", g(self.tooth), (len - self.tooth) / 2.0);
        }
        let cheekpoly = self.cheek(&c);
        let stem = self.stem(l)?;
        let out_path = match &self.out {
            Some(o) => o.clone(),
            None => format!("{}/{}", env!("CARGO_MANIFEST_DIR"), stem),
        };
        let (written, ink, cut_slots) = self.sheet(&parts, &cheekpoly, &c, &out_path, write)?;
        if self.port_per_cheek {
            let spin = self.rotatable(&cheekpoly, &parts, &c)?;
            println!("\n  the two cheeks are DIFFERENT parts: {}", match &self.port_at {
                Some(at) => format!("cheek A carries the port on facet {}, cheek B the one on facet {}.", at[0], at[1]),
                None => "cheek A carries the mouth port, cheek B the far one.".into(),
            });
            println!("  {}", match spin {
                Some(s) if s < 1e-6 => format!("  (they are the same part half a turn apart, to {}mm -- so one sheet cut twice with one turned round would do, at the price of numbers upside down on it)", py::e(s, 0)),
                _ => "  (not the same part at any angle, so both sheets are needed)".into(),
            });
            println!("    the mouthpiece enters one FACE and the bell leaves the other{}",
                     if self.port_at.is_some() || self.shape == "torus" { "." } else { "; both rim ends are capped." });
        } else {
            let turn = self.flippable(&cheekpoly, &parts);
            println!("\n  the two cheeks are identical, and go on the same way up.");
            println!("  {}", match turn {
                Some(t) => format!("  (geometrically one could be flipped and turned {} deg, but its numbers would then read mirrored and face into the bore)", g(t)),
                None => "  (a flipped cheek meets no tab at any angle)".into(),
            });
        }
        let caps = self.caps();
        println!("\n  {} wall panels + 2 cheeks{} = {} parts, {} sheet{}", parts.len(),
                 if !self.cap { String::new() } else if caps == 1 { " + 1 end cap".into() } else { format!(" + {caps} end caps") },
                 parts.len() + 2 + caps, written.len(), if written.len() > 1 { "s" } else { "" });
        for (name, w, h, k, note) in &written {
            println!("    {name:<62}{k:>3} parts  {w:.0} x {h:.0}mm  {note}");
        }
        let mut bad = 0;
        println!();
        for (ok, what, detail) in self.checks(&c, &inn, &out, &parts, &cheekpoly, &written, &ink, &cut_slots)? {
            println!("  {}  {what:<44} {detail}", if ok { "pass" } else { "FAIL" });
            bad += (!ok) as i32;
        }
        if write && bad == 0 {
            println!("\n  wrote {} file(s)", written.len());
        } else if bad != 0 {
            if write {
                let dir = std::path::Path::new(&out_path).parent().map(|p| p.to_path_buf()).unwrap_or_default();
                for (name, ..) in &written {
                    let f = dir.join(name);
                    if f.exists() {
                        let _ = std::fs::remove_file(f);
                    }
                }
            }
            println!("\n  {bad} check(s) failed. Nothing written.");
        }
        Ok(if bad != 0 { 1 } else { 0 })
    }
}

/// --name=value flags, in the order the refusal lists them.
pub const FLAGS: &[&str] = &[
    "out", "shape", "bore", "facet", "radius", "lobes", "lobe-r", "rise", "lead", "web", "wave-rise", "wave-trough-r",
    "wave-crest-r", "wave-lead-r", "spiral-facets", "spiral-ri", "spiral-ro", "ds-pitch", "ds-r0", "ds-facets",
    "ds-cross-r", "vol-r0", "vol-step", "vol-semis", "vol-cross-r", "sheet", "kerf", "scallop-in-r", "scallop-in-deg",
    "race-cap-r", "race-straight", "oval-end-r", "oval-end-deg", "oval-side-r", "oval-flat", "oval-side-flat",
    "port-from-tip", "port-at",
];
pub const SWITCHES: [&str; 9] =
    ["port", "ds-half", "narrow", "port-square", "port-both", "port-per-cheek", "merge-lead", "cap", "no-write"];

impl Cfg {
    /// Set the design from a command line, or refuse it in a sentence (the
    /// Err is what Python's SystemExit printed). The viewer calls this too, so
    /// a page and its sheets read one line, refusals included.
    pub fn read_flags(&mut self, a: &[String]) -> R<()> {
        let names = FLAGS;
        for x in a {
            let (name, eq) = match x.strip_prefix("--") {
                Some(r) => match r.split_once('=') {
                    Some((n, _)) => (n, true),
                    None => (r, false),
                },
                None => ("", false),
            };
            if !(names.contains(&name) && eq) && !(SWITCHES.contains(&name) && !eq) {
                return Err(format!(
                    "error: {x} is not a flag this generator reads. It takes {} and {}.",
                    names.iter().map(|f| format!("--{f}=")).collect::<Vec<_>>().join(", "),
                    SWITCHES.iter().map(|f| format!("--{f}")).collect::<Vec<_>>().join(", ")
                ));
            }
        }
        for flag in names.iter() {
            let pre = format!("--{flag}=");
            let hit: Vec<&String> = a.iter().filter(|x| x.starts_with(&pre)).collect();
            if hit.len() > 1 {
                return Err(format!("error: --{flag} is given twice."));
            }
            if hit.is_empty() || *flag == "port-at" {
                continue;
            }
            let v = &hit[0][pre.len()..];
            let fl = || py::float(v).ok_or_else(|| format!("error: {} is not a number.", hit[0]));
            let int = || -> R<i64> {
                let t = v.trim();
                let t2 = t.strip_prefix('+').unwrap_or(t);
                if t2.is_empty() || !t2.trim_start_matches('-').chars().all(|c| c.is_ascii_digit() || c == '_') {
                    return Err(format!("error: {} is not a whole number.", hit[0]));
                }
                t.replace('_', "").parse::<i64>().map_err(|_| format!("error: {} is not a whole number.", hit[0]))
            };
            match *flag {
                "out" => self.out = if v.is_empty() { None } else { Some(v.to_string()) },
                "shape" => self.shape = v.to_string(),
                "bore" => self.bore = fl()?,
                "facet" => self.facet = fl()?,
                "radius" => self.radius = fl()?,
                "lobes" => self.lobes = int()?,
                "lobe-r" => self.lobe_r = fl()?,
                "rise" => self.rise = fl()?,
                "lead" => self.lead = fl()?,
                "web" => self.web = fl()?,
                "wave-rise" => self.wave_rise = fl()?,
                "wave-trough-r" => self.wave_trough_r = fl()?,
                "wave-crest-r" => self.wave_crest_r = fl()?,
                "wave-lead-r" => self.wave_lead_r = fl()?,
                "spiral-facets" => self.spiral_facets = int()?,
                "spiral-ri" => self.spiral_ri = fl()?,
                "spiral-ro" => self.spiral_ro = fl()?,
                "ds-pitch" => self.ds_pitch = fl()?,
                "ds-r0" => self.ds_r0 = fl()?,
                "ds-facets" => self.ds_facets = int()?,
                "ds-cross-r" => self.ds_cross_r = fl()?,
                "vol-r0" => self.vol_r0 = fl()?,
                "vol-step" => self.vol_step = fl()?,
                "vol-semis" => self.vol_semis = int()?,
                "vol-cross-r" => self.vol_cross_r = fl()?,
                "sheet" => self.sheet = fl()?,
                "kerf" => self.burn = fl()?,
                "scallop-in-r" => self.scallop_in_r = fl()?,
                "scallop-in-deg" => self.scallop_in_deg = fl()?,
                "race-cap-r" => self.race_cap_r = fl()?,
                "race-straight" => self.race_straight = fl()?,
                "oval-end-r" => self.oval_end_r = fl()?,
                "oval-end-deg" => self.oval_end_deg = fl()?,
                "oval-side-r" => self.oval_side_r = fl()?,
                "oval-flat" => self.oval_flat = fl()?,
                "oval-side-flat" => self.oval_side_flat = fl()?,
                "port-from-tip" => self.port_from_tip = fl()?,
                _ => unreachable!(),
            }
        }
        let has = |p: &str| a.iter().any(|x| x.starts_with(p));
        let sw = |s: &str| a.iter().any(|x| x == s);
        if self.shape == TLS {
            if !has("--lobe-r=") {
                self.lobe_r = OPPOSED_R;
            }
            if !has("--rise=") {
                self.rise = OPPOSED_RISE;
            }
        }
        let by_shape = match self.shape.as_str() {
            "ess" | "spiral" | "double-volute" | "racetrack" => Some(45.0),
            "scallop" => Some(24.0),
            _ => None,
        };
        if let Some(f) = by_shape {
            if !has("--facet=") {
                self.facet = f;
            }
        }
        self.port = sw("--port");
        self.ds_half = sw("--ds-half");
        self.narrow = sw("--narrow");
        self.port_square = sw("--port-square");
        self.port_both = sw("--port-both");
        self.port_at = None;
        self.port_per_cheek = sw("--port-per-cheek");
        if let Some(h) = a.iter().find(|x| x.starts_with("--port-at=")) {
            let mut v = Vec::new();
            for s in h["--port-at=".len()..].split(',') {
                if s.is_empty() {
                    continue;
                }
                let t = s.trim();
                let ok = !t.is_empty() && t.strip_prefix(['+', '-']).unwrap_or(t).chars().all(|c| c.is_ascii_digit());
                match t.parse::<i64>() {
                    Ok(n) if ok => v.push(n),
                    _ => return Err(format!("error: {h} is not a comma-separated list of facet numbers.")),
                }
            }
            if v.is_empty() {
                return Err("error: --port-at= names no facet at all. Give it one index per port, e.g. --port-at=0,6.".into());
            }
            self.port_at = Some(v);
        }
        self.merge_lead = sw("--merge-lead") || (self.port_square && self.port_at.is_none());
        self.cap = sw("--cap");
        if self.port_both && !self.port {
            return Err("error: --port-both without --port draws no port at all, at either end. Pass both.".into());
        }
        if self.port_at.is_some() && !self.port {
            return Err("error: --port-at without --port draws no port at all, on any facet. Pass both.".into());
        }
        if self.port_at.is_some() && self.port_both {
            return Err("error: --port-at and --port-both are two answers to the same question. --port-at says how many ports there are and which facets they sit on; --port-both says there are two and they sit at the ends. Pass one. Two ports at the ends is --port-both; two ports anywhere else is --port-at=i,j.".into());
        }
        if self.port_at.is_some() && self.cap {
            return Err("error: --cap counts ported run ends and --port-at ports none of them. A closed ring has no open end to cap; an open run under --port-at has two, and neither is a port. Cap them by hand or say what the rule should be.".into());
        }
        if let (true, Some(at)) = (self.port_per_cheek, &self.port_at) {
            if at.len() != 2 {
                return Err(format!("error: --port-per-cheek splits the ports between TWO cheeks and --port-at names {}. There are two cheeks.", at.len()));
            }
        }
        if self.port_per_cheek && self.port_at.is_none() && !self.port_both {
            return Err("error: --port-per-cheek without --port-both has one port and two cheeks, so there is nothing to split. It exists to put the two ports on different sheets.".into());
        }
        if self.cap && !self.port {
            return Err("error: --cap without --port closes the only opening the bore has. The cap exists so a PORTED bore stops breathing through its mouth; with no port there is nothing left to breathe through.".into());
        }
        if self.port_square {
            self.port_across = self.bore;
            self.port_along = self.bore;
            if !self.port {
                return Err("error: --port-square without --port draws no port at all. Pass both.".into());
            }
        }
        Ok(())
    }
}

/// The ribbon_bore program.
pub fn cli() -> i32 {
    // A geometry the code cannot follow at all (a zero-length segment) stops
    // the run as Python's traceback did: its last line on stderr, exit 1.
    std::panic::set_hook(Box::new(|info| {
        let msg = info.payload().downcast_ref::<String>().cloned()
            .or_else(|| info.payload().downcast_ref::<&str>().map(|s| s.to_string()))
            .unwrap_or_default();
        eprintln!("{msg}");
        std::process::exit(1);
    }));
    let a: Vec<String> = std::env::args().skip(1).collect();
    let mut cfg = Cfg::default();
    if let Err(e) = cfg.read_flags(&a) {
        eprintln!("{e}");
        return 1;
    }
    match cfg.main(!a.iter().any(|x| x == "--no-write")) {
        Ok(rc) => rc,
        Err(e) => {
            println!("error: {e}");
            1
        }
    }
}
