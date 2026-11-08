//! An interactive view of a ribbon bore: drag to turn. Rust since 2026-11-07
//! (ribbon_view.py until then; the move changed no byte of any page).
//!
//!     target/release/ribbon_view --shape=serpentine \
//!         --out=serpentine/ribbon-serpentine-bore10-30deg-3lobes-R72/ribbon-serpentine-bore10-30deg-3lobes-R72.html
//!
//! Takes the generator's own flags, read by Cfg::read_flags(), plus --out
//! (required), --home, --embed, --trace and --ends. The page goes beside the
//! cut files it belongs to.
//!
//! It draws the AIRWAY, and the airway ALONE: the passage the air takes,
//! bounded by the wall faces and the cheeks at +-bore/2. The bore came out 3mm
//! narrow for a week because nothing drew the space inside it; a slab of ply
//! above and below would hide the very shape this page exists to show.
//!
//! --ends draws the bell and the mouthpiece from their own cut files in
//! trumpet-elbows-allowed, read the way that repository's part-view.py reads
//! them (its rings_of(), sections(), prof() and solid(), below in Rust), so a
//! redesigned bell or mouthpiece redraws here too.
//!
//! Nothing here gates anything. Check the cut files with ribbon_bore; this is
//! for looking.
use crate::{fsum, offset, pymod, seglen, Cfg, P, R};
use lasermade_tools::py::{self, g, hypot, mcos as cos, msin as sin};
use lasermade_tools::turn3d::{Num::{F, I}, J};

const END_SHADE: [f64; 4] = [1.06, 0.95, 0.6, 0.72];
const BELL_SVG: &str = "bell/cut-files/bell-round10-153mm-17rings-x3-rim86-cut-files.svg";
const MOUTHPIECE_SVG: &str = "mouthpiece/cut-files/mouthpiece-bore10-trumpet-parts-cut-files.svg";

fn parts_dir() -> String {
    format!("{}/../trumpet-elbows-allowed/parts", env!("CARGO_MANIFEST_DIR"))
}

fn num(x: f64) -> J {
    J::N(F(x))
}
fn int(n: i64) -> J {
    J::N(I(n))
}

/// n colours around the hue circle, kept clear of each other.
fn wheel(n: usize) -> Vec<String> {
    let m = n.max(1);
    (0..m)
        .map(|i| {
            let h = pymod(i as f64 * 360.0 / m as f64 + 15.0, 360.0);
            let (c, x) = (0.62, 0.62 * (1.0 - (pymod(h / 60.0, 2.0) - 1.0).abs()));
            let (r, gg, b) = [(c, x, 0.0), (x, c, 0.0), (0.0, c, x), (0.0, x, c), (x, 0.0, c), (c, 0.0, x)]
                [(crate::floordiv(h, 60.0) as i64).rem_euclid(6) as usize];
            let mm = 0.30;
            format!("#{:02x}{:02x}{:02x}", ((r + mm) * 255.0) as i64, ((gg + mm) * 255.0) as i64, ((b + mm) * 255.0) as i64)
        })
        .collect()
}

/// Each port as (segment index, t0, t1) along that segment, mouth first: the
/// OPENING, PORT_ACROSS x PORT_ALONG exactly, not the line the laser follows.
fn port_spans(cfg: &Cfg, c: &[P]) -> R<Vec<(usize, f64, f64)>> {
    if !cfg.port {
        return Ok(vec![]);
    }
    cfg.port_holes(c)?; // refuses a facet out of range or named twice
    let places: Vec<(usize, i32)> = match &cfg.port_at {
        Some(at) => at.iter().map(|&i| (i as usize, 1)).collect(),
        None => {
            let mut v = vec![(0, 1)];
            if cfg.port_both {
                v.push((c.len() - 2, -1));
            }
            v
        }
    };
    let mut out = Vec::new();
    for (i, sgn) in places {
        let l = seglen(c[i], c[i + 1]);
        let half = cfg.port_along / 2.0;
        let (lo, hi) = (cfg.port_from_tip - half, cfg.port_from_tip + half);
        let (t0, t1) = if sgn > 0 { (lo / l, hi / l) } else { (1.0 - hi / l, 1.0 - lo / l) };
        if !(0.0 <= t0 && t0 < t1 && t1 <= 1.0) {
            let wh = if cfg.port_at.is_some() { format!("facet {i}") } else { "the lead it sits on".into() };
            return Err(format!(
                "the port at {}mm from the tip, {}mm long, does not fit inside the {l:.1}mm of {wh}. Lengthen --lead or move --port-from-tip.",
                g(cfg.port_from_tip),
                g(cfg.port_along)
            ));
        }
        out.push((i, t0, t1));
    }
    Ok(out)
}

fn quad(v: [usize; 4], f: i64, s: usize, m: Option<[i64; 2]>) -> J {
    let mut kv = vec![
        ("v", J::A(v.iter().map(|&i| int(i as i64)).collect())),
        ("f", int(f)),
        ("s", int(s as i64)),
    ];
    if let Some(m) = m {
        kv.push(("m", J::A(m.iter().map(|&k| int(k)).collect())));
    }
    J::obj(kv)
}

/// The cheek face of segment i as eight quads around a rectangular hole; the
/// port's own cell, and any of no area, are not emitted.
#[allow(clippy::too_many_arguments)]
fn framed(v: &mut Vec<[f64; 3]>, a: &[P], d: &[P], h: f64, i: usize, t0: f64, t1: f64, s0: f64, s1: f64, top: bool) -> Vec<J> {
    let z = if top { h } else { -h };
    let mut at = |t: f64, ss: f64| -> usize {
        let ax = a[i].0 + (a[i + 1].0 - a[i].0) * t;
        let ay = a[i].1 + (a[i + 1].1 - a[i].1) * t;
        let dx = d[i].0 + (d[i + 1].0 - d[i].0) * t;
        let dy = d[i].1 + (d[i + 1].1 - d[i].1) * t;
        v.push([py::round_dp(ax + (dx - ax) * ss, 3), py::round_dp(ay + (dy - ay) * ss, 3), py::round_dp(z, 3)]);
        v.len() - 1
    };
    let (ts, ss) = ([0.0, t0, t1, 1.0], [0.0, s0, s1, 1.0]);
    let grid: Vec<Vec<usize>> = ts.iter().map(|&t| ss.iter().map(|&u| at(t, u)).collect()).collect();
    let mut out = Vec::new();
    for r in 0..3 {
        for k in 0..3 {
            if r == 1 && k == 1 {
                continue; // the port
            }
            if ts[r + 1] - ts[r] < 1e-9 || ss[k + 1] - ss[k] < 1e-9 {
                continue; // a cell of no area
            }
            let (p00, p01) = (grid[r][k], grid[r][k + 1]);
            let (p11, p10) = (grid[r + 1][k + 1], grid[r + 1][k]);
            let vv = if top { [p00, p01, p11, p10] } else { [p00, p10, p11, p01] };
            out.push(quad(vv, if top { 2 } else { 3 }, i, None));
        }
    }
    out
}

/// part-view.py's reading of a bell or mouthpiece cut file: its rings,
/// stacked into a solid. In trumpet-elbows-allowed it is Python, and its
/// helpers come from bell-view.py; this is the same arithmetic.
mod part_view {
    use super::*;
    use lasermade_tools::re;

    /// (width, corner radius) for each subpath, whatever commands drew it.
    pub fn sections(d: &str) -> Vec<(f64, f64)> {
        let rx = re::rx(r"[MmLlHhVvZzCcSsQqAa]|-?\d*\.?\d+(?:[eE]-?\d+)?");
        let toks: Vec<&str> = re::all(&rx, d).iter().map(|m| m.get(0).unwrap().as_str()).collect();
        let mut i = 0usize;
        let (mut x, mut y) = (0.0f64, 0.0f64);
        let mut cmd: Option<char> = None;
        let mut subs: Vec<Vec<f64>> = Vec::new();
        let mut arcs: Vec<Vec<f64>> = Vec::new();
        let isl = |t: &str| t.len() == 1 && t.as_bytes()[0].is_ascii_alphabetic();
        while i < toks.len() {
            if isl(toks[i]) {
                cmd = toks[i].chars().next();
                i += 1;
                continue;
            }
            let Some(cm) = cmd else {
                i += 1;
                continue;
            };
            let rel = cm.is_ascii_lowercase();
            let mut n = || {
                let v: f64 = toks[i].parse().unwrap();
                i += 1;
                v
            };
            match cm.to_ascii_uppercase() {
                'M' => {
                    let (dx, dy) = (n(), n());
                    (x, y) = if rel { (x + dx, y + dy) } else { (dx, dy) };
                    subs.push(vec![x]);
                    arcs.push(vec![0.0]);
                    cmd = Some(if rel { 'l' } else { 'L' });
                }
                'L' => {
                    let (dx, dy) = (n(), n());
                    (x, y) = if rel { (x + dx, y + dy) } else { (dx, dy) };
                    subs.last_mut().unwrap().push(x);
                }
                'H' => {
                    let v = n();
                    x = if rel { x + v } else { v };
                    subs.last_mut().unwrap().push(x);
                }
                'V' => {
                    let v = n();
                    y = if rel { y + v } else { v };
                    subs.last_mut().unwrap().push(x);
                }
                'C' => {
                    n();
                    n();
                    n();
                    n();
                    let (dx, dy) = (n(), n());
                    (x, y) = if rel { (x + dx, y + dy) } else { (dx, dy) };
                    subs.last_mut().unwrap().push(x);
                }
                'S' | 'Q' => {
                    n();
                    n();
                    let (dx, dy) = (n(), n());
                    (x, y) = if rel { (x + dx, y + dy) } else { (dx, dy) };
                    subs.last_mut().unwrap().push(x);
                }
                'A' => {
                    let rxv = n();
                    n();
                    n();
                    n();
                    n();
                    let (dx, dy) = (n(), n());
                    (x, y) = if rel { (x + dx, y + dy) } else { (dx, dy) };
                    subs.last_mut().unwrap().push(x);
                    arcs.last_mut().unwrap().push(rxv.abs());
                }
                _ => i += 1,
            }
        }
        let _ = y;
        subs.iter()
            .zip(&arcs)
            .filter(|(v, _)| v.len() > 1)
            .map(|(v, a)| (crate::fmax(v.iter().copied()) - crate::fmin(v.iter().copied()), crate::fmax(a.iter().copied())))
            .collect()
    }

    /// A rounded square of half-width h and corner radius c, counter-clockwise.
    fn outline(h: f64, c: f64, per: usize) -> Vec<P> {
        let c = py::min(py::max(c, 0.0), h);
        let s = h - c;
        let mut pts = Vec::new();
        for ((cx, cy), a0) in [((s, -s), -90.0), ((s, s), 0.0), ((-s, s), 90.0), ((-s, -s), 180.0)] {
            if c <= 1e-9 {
                pts.push((cx, cy));
            } else {
                for k in 0..=per {
                    let t = py::radians(a0 + 90.0 * k as f64 / per as f64);
                    pts.push((cx + c * cos(t), cy + c * sin(t)));
                }
            }
        }
        pts
    }

    /// The same, as exactly n points evenly spaced along its own perimeter.
    fn prof(h: f64, c: f64, n: usize) -> Vec<P> {
        let mut p = outline(h, c, 24);
        p.push(p[0]);
        let mut run = vec![0.0f64];
        for w in p.windows(2) {
            let last = run[run.len() - 1];
            run.push(last + hypot(w[1].0 - w[0].0, w[1].1 - w[0].1));
        }
        let total = run[run.len() - 1];
        let mut out = Vec::new();
        let mut j = 0usize;
        for k in 0..n {
            let t = total * k as f64 / n as f64;
            while j + 1 < run.len() - 1 && run[j + 1] < t {
                j += 1;
            }
            let span = run[j + 1] - run[j];
            let u = if span < 1e-12 { 0.0 } else { (t - run[j]) / span };
            out.push((p[j].0 + (p[j + 1].0 - p[j].0) * u, p[j].1 + (p[j + 1].1 - p[j].1) * u));
        }
        out
    }

    type Ring = (f64, f64, f64, f64);

    /// [(aperture w, aperture c, outer w, outer c)], bottom of the stack
    /// first, plus the rise per ring.
    fn rings_of(path: &str) -> R<(Vec<Ring>, f64)> {
        let s = std::fs::read_to_string(path).map_err(|e| format!("{path}: {e}"))?;
        let paths = re::rx(r#"<path\b[^>]*\bd="([^"]+)""#);
        let grp = |colour: &str| -> Vec<Option<(f64, f64)>> {
            let g_rx = re::rx(&format!(r#"(?s)<g[^>]*stroke="{colour}"[^>]*>(.*?)</g>"#));
            match re::first(&g_rx, &s) {
                None => vec![],
                Some(m) => re::findall1(&paths, m.get(1).unwrap().as_str(), 1)
                    .iter()
                    .map(|d| sections(d).first().copied())
                    .collect(),
            }
        };
        let (aps, outs) = (grp("#ff8000"), grp("#000000"));
        let mut pairs = Vec::new();
        if !aps.is_empty() {
            if aps.len() != outs.len() {
                return Err(format!("AssertionError: {} apertures, {} outlines", aps.len(), outs.len()));
            }
            for (a, o) in aps.iter().zip(&outs) {
                if let (Some(a), Some(o)) = (a, o) {
                    pairs.push((a.0, a.1, o.0, o.1));
                }
            }
        } else {
            for d in re::findall1(&paths, &s, 1) {
                let mut w = sections(&d);
                if w.len() == 2 {
                    w.sort_by(|p, q| p.partial_cmp(q).unwrap());
                    pairs.push((w[0].0, w[0].1, w[1].0, w[1].1));
                }
            }
        }
        let rise = re::first(&re::rx(r"([\d.]+)mm of rise"), &s).map(|m| m[1].parse().unwrap()).unwrap_or(3.0);
        Ok((pairs, rise))
    }

    /// Per ring: the outside band, the bore band, the top annulus; the first
    /// ring's underside too.
    fn solid(pairs: &[Ring], rise: f64, n: usize) -> (Vec<[f64; 3]>, Vec<(Vec<usize>, usize)>) {
        let (mut v, mut q) = (Vec::new(), Vec::new());
        let mut base = 0usize;
        for (i, &(aw, ac, ow, oc)) in pairs.iter().enumerate() {
            let (z0, z1) = (i as f64 * rise, (i + 1) as f64 * rise);
            let a = prof(aw / 2.0, ac, n);
            let o = prof(ow / 2.0, oc, n);
            for z in [z0, z1] {
                v.extend(a.iter().map(|p| [p.0, p.1, z]));
                v.extend(o.iter().map(|p| [p.0, p.1, z]));
            }
            let (a0, o0) = (base, base + n);
            let (a1, o1) = (base + 2 * n, base + 3 * n);
            for k in 0..n {
                let j = (k + 1) % n;
                q.push((vec![o0 + k, o0 + j, o1 + j, o1 + k], 1));
                q.push((vec![a1 + k, a1 + j, a0 + j, a0 + k], 2));
                q.push((vec![a1 + k, o1 + k, o1 + j, a1 + j], 0));
                if i == 0 {
                    q.push((vec![a0 + j, o0 + j, o0 + k, a0 + k], 3));
                }
            }
            base += 4 * n;
        }
        (v, q)
    }

    pub struct Solid {
        pub v: Vec<[f64; 3]>,
        /// (vertex indices, face)
        pub q: Vec<(Vec<usize>, usize)>,
        pub rings: usize,
        pub height: f64,
        pub rim: f64,
    }

    pub fn data_for(path: &str, n: usize) -> R<Solid> {
        let (pairs, rise) = rings_of(path)?;
        if pairs.is_empty() {
            return Err(format!("AssertionError: no rings in {path}"));
        }
        let (v, q) = solid(&pairs, rise, n);
        Ok(Solid {
            v: v.iter().map(|p| p.map(|x| py::round_dp(x, 3))).collect(),
            q,
            rings: pairs.len(),
            height: py::round_dp(pairs.len() as f64 * rise, 1),
            rim: py::round_dp(pairs[pairs.len() - 1].2, 2),
        })
    }
}

/// Append a part-view solid, its local x along ex and z along ez; ey = ez x ex,
/// so the map is a rotation and every face keeps its winding.
fn place(v: &mut Vec<[f64; 3]>, q: &mut Vec<J>, part: &part_view::Solid, origin: [f64; 3], ex: [f64; 3], ez: [f64; 3], f: i64) {
    let ey = [ez[1] * ex[2] - ez[2] * ex[1], ez[2] * ex[0] - ez[0] * ex[2], ez[0] * ex[1] - ez[1] * ex[0]];
    let base = v.len();
    for p in &part.v {
        let (x, y, z) = (p[0], p[1], p[2]);
        v.push([0, 1, 2].map(|k| origin[k] + x * ex[k] + y * ey[k] + z * ez[k]));
    }
    for (vs, face) in &part.q {
        q.push(J::obj(vec![
            ("v", J::A(vs.iter().map(|&i| int((base + i) as i64)).collect())),
            ("f", int(f)),
            ("s", int(0)),
            ("k", num(END_SHADE[*face])),
        ]));
    }
}

/// With a port: the bell on the outside of the bottom cheek over it, and the
/// mouthpiece on the far end. With none: the mouthpiece on the mouth and the
/// bell on the far end. Returns what the panel says.
fn ends(cfg: &Cfg, c: &[P], v: &mut Vec<[f64; 3]>, q: &mut Vec<J>, spans: &[(usize, f64, f64)], h: f64) -> R<J> {
    let parts = parts_dir();
    if !std::path::Path::new(&format!("{parts}/part-view.py")).exists() {
        return Err("\x00ribbon_view: --ends draws the bell and mouthpiece from trumpet-elbows-allowed, and needs that repository cloned beside this one.".into());
    }
    let bell = part_view::data_for(&format!("{parts}/{BELL_SVG}"), 32)?;
    let mp = part_view::data_for(&format!("{parts}/{MOUTHPIECE_SVG}"), 32)?;
    let n = c.len();
    let tube = |a: P, b: P| {
        let l = seglen(a, b);
        [(b.0 - a.0) / l, (b.1 - a.1) / l, 0.0]
    };
    if spans.is_empty() {
        let t = tube(c[1], c[0]);
        place(v, q, &mp, [c[0].0, c[0].1, 0.0], [-t[1], t[0], 0.0], t, 7);
        let t = tube(c[n - 2], c[n - 1]);
        place(v, q, &bell, [c[n - 1].0, c[n - 1].1, 0.0], [-t[1], t[0], 0.0], t, 6);
        return Ok(J::obj(vec![
            ("bell", J::S(format!("{} rings, {}mm, \u{f8}{} rim, on the far end", bell.rings, g(bell.height), g(bell.rim)))),
            ("mouthpiece", J::S(format!("{} rings, {}mm, on the mouth", mp.rings, g(mp.height)))),
            ("port", J::B(false)),
        ]));
    }
    let (i, t0, t1) = spans[0];
    let tm = (t0 + t1) / 2.0;
    let px = c[i].0 + (c[i + 1].0 - c[i].0) * tm;
    let py_ = c[i].1 + (c[i + 1].1 - c[i].1) * tm;
    let u = tube(c[i], c[i + 1]);
    place(v, q, &bell, [px, py_, -(h + cfg.thick)], u, [0.0, 0.0, -1.0], 6);
    let t = tube(c[n - 2], c[n - 1]);
    place(v, q, &mp, [c[n - 1].0, c[n - 1].1, 0.0], [-t[1], t[0], 0.0], t, 7);
    Ok(J::obj(vec![
        ("bell", J::S(format!("{} rings, {}mm, \u{f8}{} rim, on the port", bell.rings, g(bell.height), g(bell.rim)))),
        ("mouthpiece", J::S(format!("{} rings, {}mm, on the far end", mp.rings, g(mp.height)))),
        ("port", J::B(true)),
    ]))
}

/// What a page shows: the drawing's data, and its two numbers for the report.
pub struct Data {
    pub json: J,
    pub mm: f64,
    pub segs: usize,
    pub quads: usize,
}

/// Vertices and quads for the airway, plus what each face is. `traced`
/// carries a traced centreline, and its bore as the trace typed it.
pub fn data_for(cfg: &Cfg, with_ends: bool, traced: Option<(&[P], J, J)>) -> R<Data> {
    let c: Vec<P> = match &traced {
        Some((pts, ..)) => pts.to_vec(),
        None => cfg.centreline()?,
    };
    // the airway's own boundary: the wall FACES, at +-bore/2
    let mut a = offset(&c, cfg.bore / 2.0);
    let mut d = offset(&c, -cfg.bore / 2.0);
    if fsum(a.windows(2).map(|w| seglen(w[0], w[1]))) > fsum(d.windows(2).map(|w| seglen(w[0], w[1]))) {
        std::mem::swap(&mut a, &mut d); // a is the inner wall
    }
    let h = cfg.bore / 2.0;
    let mut v: Vec<[f64; 3]> = Vec::new();
    let mut q: Vec<J> = Vec::new();
    for i in 0..c.len() {
        v.extend([[a[i].0, a[i].1, -h], [a[i].0, a[i].1, h], [d[i].0, d[i].1, h], [d[i].0, d[i].1, -h]]);
    }
    let nc = c.len();
    let shut = (c[0].0 - c[nc - 1].0).abs() < 1e-6 && (c[0].1 - c[nc - 1].1).abs() < 1e-6;
    let spans = port_spans(cfg, &c)?;
    let across = if cfg.port { (1.0 - cfg.port_across / cfg.bore) / 2.0 } else { 0.0 };
    // which cheek each port is in: one each under --port-per-cheek, the bottom
    // only (the top plugged) as built with --ends, else both
    let all: Vec<(usize, (f64, f64))> = spans.iter().map(|&(i, t0, t1)| (i, (t0, t1))).collect();
    let (top_h, bot_h): (Vec<(usize, (f64, f64))>, Vec<(usize, (f64, f64))>) = if cfg.port_per_cheek {
        (vec![(spans[0].0, (spans[0].1, spans[0].2))], vec![(spans[1].0, (spans[1].1, spans[1].2))])
    } else if with_ends {
        (vec![], all)
    } else {
        (all.clone(), all)
    };
    let find = |m: &[(usize, (f64, f64))], i: usize| m.iter().rev().find(|(k, _)| *k == i).map(|&(_, t)| t);
    for i in 0..nc - 1 {
        let (p, qq) = (4 * i, 4 * (i + 1));
        q.push(quad([p, p + 1, qq + 1, qq], 0, i, None)); // inner
        q.push(quad([p + 3, qq + 3, qq + 2, p + 2], 1, i, None)); // outer
        match find(&top_h, i) {
            Some((t0, t1)) => q.extend(framed(&mut v, &a, &d, h, i, t0, t1, across, 1.0 - across, true)),
            None => q.push(quad([p + 1, p + 2, qq + 2, qq + 1], 2, i, Some([1, 3]))), // top
        }
        match find(&bot_h, i) {
            Some((t0, t1)) => q.extend(framed(&mut v, &a, &d, h, i, t0, t1, across, 1.0 - across, false)),
            None => q.push(quad([p, qq, qq + 3, p + 3], 3, i, Some([0, 2]))), // bottom
        }
    }
    let n = nc - 1;
    let nb = v.len();
    let endnote = if with_ends { ends(cfg, &c, &mut v, &mut q, &spans, h)? } else { J::Null };
    if !shut {
        q.push(quad([0, 1, 2, 3], 4, 0, None)); // mouth
        q.push(quad([4 * n + 3, 4 * n + 2, 4 * n + 1, 4 * n], 5, n - 1, None)); // far end
    }
    let r = cfg.bend_radius();
    let mm = py::round_dp(fsum(c.windows(2).map(|w| seglen(w[0], w[1]))), 1);
    let quads = q.len();
    let (bore_j, facet_j) = match traced {
        Some((_, b, f)) => (b, f),
        None => (num(cfg.bore), num(cfg.facet)),
    };
    let shape = cfg.shape.as_str();
    let curve = match shape {
        "double-spiral" => "Archimedean spiral, sampled",
        "double-volute" => "chain of semicircles",
        "spiral" => "compass spiral, stepping arcs",
        "traced" => "traced stations",
        _ => "constant-radius arcs",
    };
    let strs = |v: Vec<&str>| J::A(v.into_iter().map(|s| J::S(s.into())).collect());
    let json = J::obj(vec![
        ("V", J::A(v.iter().map(|p| J::A(p.iter().map(|&x| num(py::round_dp(x, 3))).collect())).collect())),
        ("Q", J::A(q)),
        ("bore", bore_j),
        ("mm", num(mm)),
        ("facet", facet_j),
        ("shape", J::S(cfg.shape.clone())),
        ("curve", J::S(curve.into())),
        ("rrange", if shape == "spiral" {
            J::A(vec![num(py::round_dp(cfg.spiral_ri, 1)), num(py::round_dp(cfg.spiral_ro, 1))])
        } else {
            J::Null
        }),
        ("flat", J::B(shape == "spiral")),
        ("R", num(r)),
        ("segs", int(n as i64)),
        ("over", num(py::round_dp(100.0 * (1.0 / cos(py::radians(cfg.facet) / 2.0) - 1.0), 2))),
        ("pal", J::A(wheel(n).into_iter().map(J::S).collect())),
        ("shut", J::B(shut)),
        ("faces", strs(vec![
            "inner wall", "outer wall", "top cheek", "bottom cheek",
            if cfg.cap { "cap (mouth)" } else { "mouth" },
            if cfg.cap && cfg.port_both { "cap (far end)" } else { "far end" },
            "bell", "mouthpiece",
        ])),
        ("facecol", strs(vec![
            "#5aa9e6", "#3d7ebd", "#c9d6e3", "#8fa3b8",
            if cfg.cap { "#b08968" } else { "#1c1c20" },
            if cfg.cap && cfg.port_both { "#b08968" } else { "#e0457b" },
            "#d8b445", "#8a5a2b",
        ])),
        ("nb", int(nb as i64)),
        ("ends", endnote),
        ("ports", int(spans.len() as i64)),
        ("portsize", if cfg.port { J::A(vec![num(cfg.port_across), num(cfg.port_along)]) } else { J::Null }),
        ("percheek", J::B(cfg.port_per_cheek)),
    ]);
    Ok(Data { json, mm, segs: n, quads })
}

/// The page, or with `embed` the bare canvas a writeup frames, whose drawing
/// code is cut from the full page so the two cannot diverge.
pub fn build(title: &str, d: &Data, embed: bool, home: &str) -> R<String> {
    let mut data = String::new();
    d.json.dump(&mut data);
    if !embed {
        return Ok(crate::ribbon_view_page::HTML.replace("__TITLE__", title).replace("__DATA__", &data));
    }
    let html = crate::ribbon_view_page::HTML;
    let body = html.split_once("<script>\nconst D = ").map(|x| x.1).unwrap_or("");
    let draw = body.split_once("/* --- controls --- */").map(|x| x.0).unwrap_or(body);
    let drop = ["__DATA__;", "const D =", "const cv =", "let yaw ="];
    let draw: Vec<&str> = draw.lines().filter(|l| !drop.iter().any(|p| l.starts_with(p))).collect();
    let draw = draw.join("\n");
    if !(draw.contains("function draw(") && !draw.contains("const D =")) {
        return Err("AssertionError: bad extract".into());
    }
    Ok(crate::ribbon_view_page::EMBED
        .replace("__TITLE__", title)
        .replace("__DRAW__", &draw)
        .replace("__HOME__", home)
        .replace("__DATA__", &data))
}

/// str.title(): each run of letters capitalised, the rest lowered.
fn title_case(s: &str) -> String {
    let mut out = String::new();
    let mut prev_letter = false;
    for ch in s.chars() {
        if ch.is_alphabetic() {
            if prev_letter {
                out.extend(ch.to_lowercase());
            } else {
                out.extend(ch.to_uppercase());
            }
            prev_letter = true;
        } else {
            out.push(ch);
            prev_letter = false;
        }
    }
    out
}

fn report(path: &str, d: &Data, tail: &str) {
    println!("  {:<52}drag to turn, colour by face or facet", crate::basename(path));
    println!("  {:52}{}mm, {} facets, {tail}", "", py::repr(d.mm), d.segs);
}

/// An Err starting with NUL is a sys.exit(message): stderr, no "error: ".
fn run(a: &[String]) -> R<i32> {
    const VIEW: [&str; 5] = ["--out=", "--home=", "--embed", "--trace=", "--ends"];
    let mut cfg = Cfg::default();
    let design: Vec<String> = a.iter().filter(|x| !VIEW.iter().any(|p| x.starts_with(p))).cloned().collect();
    cfg.read_flags(&design).map_err(|e| format!("\x00{e}"))?;
    let path = match a.iter().find(|x| x.starts_with("--out=")) {
        Some(o) => o.split_once('=').unwrap().1.to_string(),
        None => return Err("\x00ribbon_view: say where the page goes with --out=PATH. It belongs beside the cut files it describes, in the design's own folder.".into()),
    };
    let with_ends = a.iter().any(|x| x == "--ends");
    if with_ends && (cfg.port_both || cfg.port_at.is_some() || ["torus", "scallop", "racetrack", "oval"].contains(&cfg.shape.as_str())) {
        return Err("\x00ribbon_view: --ends needs two ends to put a mouthpiece and a bell on: a closed ring has none, and --port-both and --port-at move both openings into the cheeks.".into());
    }
    if let Some(tr) = a.iter().find(|x| x.starts_with("--trace=")) {
        let f = tr.split_once('=').unwrap().1;
        let doc = J::parse(&std::fs::read_to_string(f).map_err(|e| format!("{f}: {e}"))?)?;
        let pts: Vec<P> = doc.get("stations").map(|s| s.arr().iter().map(|q| (q.arr()[0].num().f(), q.arr()[1].num().f())).collect()).unwrap_or_default();
        let (bj, fj) = (doc.get("bore").cloned().unwrap_or(J::Null), doc.get("facet").cloned().unwrap_or(J::Null));
        cfg.bore = bj.num().f();
        cfg.facet = fj.num().f();
        cfg.shape = "traced".into();
        let seg: Vec<f64> = pts.windows(2).map(|w| seglen(w[0], w[1])).collect();
        let mut inner = seg.clone();
        inner.sort_by(|x, y| x.partial_cmp(y).unwrap());
        let inner = &inner[1..inner.len() - 1];
        cfg.radius = py::round_dp(
            (fsum(inner.iter().copied()) / inner.len() as f64) / (2.0 * lasermade_tools::py::mtan(py::radians(cfg.facet / 2.0))),
            3,
        );
        let title = format!("{}, {} mm \u{2014} traced", title_case(&doc.get("name").map(|n| n.str().replace('-', " ")).unwrap_or_default()), match bj.num() { I(n) => n.to_string(), F(x) => g(x) });
        let d = data_for(&cfg, with_ends, Some((&pts, bj, fj)))?;
        let page = build(&title, &d, false, "")?;
        std::fs::write(&path, page).map_err(|e| format!("{path}: {e}"))?;
        report(&path, &d, "traced");
        return Ok(0);
    }
    let b = g(cfg.bore);
    let title = match cfg.shape.as_str() {
        "torus" => format!("Closed Ring, {} Facets, {b} mm Bore", py::round(360.0 / cfg.facet)),
        "racetrack" => format!("Closed Serpentine Racetrack, {} Lobes a Side, {b} mm Bore", cfg.lobes),
        "oval" => format!("Closed Oval, Flattened Ends, {b} mm Bore"),
        "scallop" => format!("Closed Serpentine, {} Lobes, {b} mm Bore", cfg.lobes),
        "ess" => format!("Ribbon Ess, {b} mm Bore"),
        "spiral" => format!("Ribbon Spiral, {b} mm Bore"),
        "double-volute" => format!("Ribbon Double Volute, {b} mm Bore"),
        "double-spiral" if cfg.ds_half => format!("Ribbon Double Spiral, Centre Half, {b} mm Bore"),
        "double-spiral" => format!("Ribbon Double Spiral, {b} mm Bore"),
        "three-lobe-serpentine-with-collinear-ends" => format!("Three-Lobe Serpentine with Collinear Ends, {b} mm Bore"),
        "serpentine" => format!("Ribbon Serpentine, {b} mm Bore"),
        s => {
            return Err(format!(
                "\x00ribbon_view: no title for --shape={s}. Add it here as well as in ribbon_bore.centreline()."
            ))
        }
    };
    let home = a
        .iter()
        .find(|x| x.starts_with("--home="))
        .map(|h| h.split_once('=').unwrap().1.to_string())
        .unwrap_or_else(|| "https://gernreich.github.io/swept-curve/".into());
    let embed = a.iter().any(|x| x == "--embed");
    // built BEFORE the file is opened, so a refusal leaves no empty page
    let d = data_for(&cfg, with_ends, None)?;
    let page = build(&title, &d, embed, &home)?;
    std::fs::write(&path, page).map_err(|e| format!("{path}: {e}"))?;
    report(&path, &d, &format!("{} quads", d.quads));
    Ok(0)
}

/// The ribbon_view program.
pub fn cli() -> i32 {
    let a: Vec<String> = std::env::args().skip(1).collect();
    match run(&a) {
        Ok(rc) => rc,
        Err(e) => {
            match e.strip_prefix('\x00') {
                Some(m) => eprintln!("{m}"),
                None => println!("error: {e}"),
            }
            1
        }
    }
}
