//! The volute: a metre of bore wound flat, drawn as semicircles of stepping
//! radius. Rust since 2026-11-07 (volute.py until then; the move changed no
//! byte of volute.json or of the report).
//!
//!     target/release/volute [--r0=82.3] [--step=24] [--semis=6] [--facet=45]
//!
//! A spiral whose radius is still changing across a facet cannot be offset
//! correctly: offset() mitres a vertex assuming the curvature either side of
//! it is constant, true of an arc and false of a spiral, and building this
//! shape smooth cost 6.44mm of a 10mm airway. So the curve here is a chain of
//! semicircles: the radius holds across each one and steps only at the joins,
//! where a mitre already expects a corner.
//!
//! WHAT THIS IS NOT. Two things are unsolved, and both are recorded here
//! because there is no cut file: the inner end is enclosed (its lead comes
//! within 7.75mm of the rest of the bore where it needs 20), and the ends are
//! not opposed (24 facets at 45 degrees turn the run 1035 degrees). Two of
//! its four checks fail, on purpose.
//!
//! DONE, 2026-09-08, as `ribbon_bore --shape=double-volute`: interleaving a
//! return arm, half a turn round the eye, fixed both. This file stays as the
//! single arm, the clearest statement of why the arcs are semicircles rather
//! than a spiral.
use lasermade_tools::py::{self, dist, g, hypot, mcos as cos, msin as sin};
use ribbon_bore::{fmax, fmin, fsum, pymod, P};
use std::f64::consts::PI;

const BORE: f64 = 10.0;
const THICK: f64 = 3.0;
const WEB: f64 = 2.0;
/// 20mm: two runs need this much apart
const BAND: f64 = BORE + 2.0 * THICK + 2.0 * WEB;
const LEAD: f64 = 20.0;

/// Tightest arc that still leaves a tooth on the inner panel.
fn floor_radius(facet: f64) -> f64 {
    (BORE + THICK) / 2.0 + 10.0 / 2.0 / sin(py::radians(facet / 2.0))
}

/// Semicircles of stepping radius, each starting where the last ended.
fn centreline(r0: f64, step: f64, semis: i64, facet: f64) -> Result<(Vec<P>, Vec<f64>), String> {
    let per = py::round(180.0 / facet);
    if (per as f64 * facet - 180.0).abs() > 1e-9 {
        return Err(format!("{} degree facets do not divide a semicircle.", g(facet)));
    }
    let radii: Vec<f64> = (0..semis.max(0)).map(|k| r0 - k as f64 * step / 2.0).collect();
    if radii.is_empty() {
        return Err("min() arg is an empty sequence".into());
    }
    if fmin(radii.iter().copied()) < floor_radius(facet) {
        return Err(format!(
            "the tightest arc is R{:.1} and a {}mm bore at {} degree facets needs R{:.1}.",
            fmin(radii.iter().copied()),
            g(BORE),
            g(facet),
            floor_radius(facet)
        ));
    }
    let mut pts = vec![(radii[0], 0.0)];
    let mut ang = 0.0f64;
    for &r in &radii {
        let (px, py_) = pts[pts.len() - 1];
        let (cx, cy) = (px - r * cos(ang), py_ - r * sin(ang));
        for i in 1..=per {
            let th = ang + PI * i as f64 / per as f64;
            pts.push((cx + r * cos(th), cy + r * sin(th)));
        }
        ang += PI;
    }
    let out = |p: P, q: P| {
        let (dx, dy) = (p.0 - q.0, p.1 - q.1);
        let n = hypot(dx, dy);
        (p.0 + dx / n * LEAD, p.1 + dy / n * LEAD)
    };
    let n = pts.len();
    let mut c = vec![out(pts[0], pts[1])];
    let last = out(pts[n - 1], pts[n - 2]);
    c.extend(pts);
    c.push(last);
    Ok((c, radii))
}

fn seg_gap(a: P, b: P, c: P, d: P) -> f64 {
    let pt = |p: P, u: P, v: P| {
        let (ux, uy) = u;
        let (dx, dy) = (v.0 - ux, v.1 - uy);
        let l = dx * dx + dy * dy;
        let t = if l == 0.0 { 0.0 } else { py::max(0.0, py::min(1.0, ((p.0 - ux) * dx + (p.1 - uy) * dy) / l)) };
        hypot(p.0 - (ux + t * dx), p.1 - (uy + t * dy))
    };
    fmin([pt(a, c, d), pt(b, c, d), pt(c, a, b), pt(d, a, b)])
}

/// Nearest approach of the bore to itself, ignoring its own neighbourhood.
fn closest(pts: &[P], along: f64) -> f64 {
    let mut run = vec![0.0f64];
    for i in 0..pts.len() - 1 {
        let last = run[run.len() - 1];
        run.push(last + dist(pts[i], pts[i + 1]));
    }
    let mut worst = f64::INFINITY;
    for i in 0..pts.len() - 1 {
        for j in i + 1..pts.len() - 1 {
            if run[j] - run[i + 1] < along {
                continue;
            }
            worst = py::min(worst, seg_gap(pts[i], pts[i + 1], pts[j], pts[j + 1]));
        }
    }
    worst
}

/// Degrees between the two openings; opposed is 180.
fn openings(pts: &[P]) -> f64 {
    let n = pts.len();
    let (ax, ay) = (pts[1].0 - pts[0].0, pts[1].1 - pts[0].1);
    let (bx, by) = (pts[n - 1].0 - pts[n - 2].0, pts[n - 1].1 - pts[n - 2].1);
    let (mx, my) = (-ax, -ay);
    let dot = (mx * bx + my * by) / (hypot(mx, my) * hypot(bx, by));
    py::degrees(py::macos(py::max(-1.0, py::min(1.0, dot))))
}

/// This file's own offset, with an absolute parallel test, as it always had.
fn offset(poly: &[P], d: f64) -> Vec<P> {
    let mut segs = Vec::new();
    for w in poly.windows(2) {
        let (a, b) = (w[0], w[1]);
        let (dx, dy) = (b.0 - a.0, b.1 - a.1);
        let n = hypot(dx, dy);
        let (nx, ny) = (-dy / n * d, dx / n * d);
        segs.push(((a.0 + nx, a.1 + ny), (b.0 + nx, b.1 + ny)));
    }
    let meet = |s: (P, P), t: (P, P)| -> P {
        let ((x1, y1), (x2, y2)) = s;
        let ((x3, y3), (x4, y4)) = t;
        let den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4);
        if den.abs() < 1e-12 {
            return s.1;
        }
        let u = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den;
        (x1 + u * (x2 - x1), y1 + u * (y2 - y1))
    };
    let mut out = vec![segs[0].0];
    out.extend(segs.windows(2).map(|w| meet(w[0], w[1])));
    out.push(segs[segs.len() - 1].1);
    out
}

/// json.dump with its default separators, ', ' and ': '.
fn pts_json(v: &[P]) -> String {
    let items: Vec<String> = v.iter().map(|p| format!("[{}, {}]", py::repr(p.0), py::repr(p.1))).collect();
    format!("[{}]", items.join(", "))
}
fn nums_json(v: &[f64]) -> String {
    let items: Vec<String> = v.iter().map(|&x| py::repr(x)).collect();
    format!("[{}]", items.join(", "))
}

fn run(a: &[String]) -> Result<i32, String> {
    let flag = |name: &str| a.iter().find(|x| x.starts_with(&format!("--{name}="))).map(|x| x.split_once('=').unwrap().1);
    let fl = |name: &str, default: f64| -> Result<f64, String> {
        match flag(name) {
            None => Ok(default),
            Some(v) => py::float(v).ok_or_else(|| format!("could not convert string to float: {}", py::str_repr(v))),
        }
    };
    let r0 = fl("r0", 82.3)?;
    let step = fl("step", 24.0)?;
    let semis = match flag("semis") {
        None => 6,
        Some(v) => v.trim().parse::<i64>().map_err(|_| format!("invalid literal for int() with base 10: {}", py::str_repr(v)))?,
    };
    let facet = fl("facet", 45.0)?;

    let (c, radii) = centreline(r0, step, semis, facet)?;
    let length = fsum(c.windows(2).map(|w| dist(w[0], w[1])));
    let gap = closest(&c, 80.0);
    let facets = c.len() as i64 - 3;
    let turn = (facets - 1) as f64 * facet;
    let xs: Vec<f64> = c.iter().map(|p| p.0).collect();
    let ys: Vec<f64> = c.iter().map(|p| p.1).collect();

    println!("volute   {}mm square, {} degree facets", g(BORE), g(facet));
    println!("  {semis} semicircles, R{} down to R{}, {}mm step", g(radii[0]), g(radii[radii.len() - 1]), g(step));
    println!("  centreline {length:.1}mm, section {} x {} = {:.0}mm2", g(BORE), g(BORE), BORE * BORE);
    println!("  {facets} facets turn the run {} degrees ({} past a whole number of turns)\n", g(turn), g(pymod(turn, 360.0)));

    let note = |ok: bool, what: &str, detail: String| println!("  {}  {what:<40} {detail}", if ok { "pass" } else { "FAIL" });
    let span = |v: &[f64]| fmax(v.iter().copied()) - fmin(v.iter().copied());
    let rmin = fmin(radii.iter().copied());
    note(gap >= BAND, "the bore stays clear of itself", format!("{gap:.2}mm against the {}mm cheek band", g(BAND)));
    note((openings(&c) - 180.0).abs() < 1e-6, "the two openings are opposed", format!("{:.0} degrees apart, 180 is opposed", openings(&c)));
    note(rmin >= floor_radius(facet), "every arc holds a tooth", format!("R{rmin:.1} against R{:.1} needed", floor_radius(facet)));
    note(span(&xs) + BAND <= 580.0 && span(&ys) + BAND <= 288.0, "the cheek fits the P2S bed",
         format!("{:.0} x {:.0}mm against 580 x 288", span(&xs) + BAND, span(&ys) + BAND));

    let (band_in, band_out) = (offset(&c, -BAND / 2.0), offset(&c, BAND / 2.0));
    let (air_in, air_out) = (offset(&c, -BORE / 2.0), offset(&c, BORE / 2.0));
    let bxs: Vec<f64> = band_out.iter().chain(&band_in).map(|p| p.0).collect();
    let bys: Vec<f64> = band_out.iter().chain(&band_in).map(|p| p.1).collect();
    let bbox = [
        py::round_dp(fmin(bxs.iter().copied()), 1),
        py::round_dp(fmin(bys.iter().copied()), 1),
        py::round_dp(span(&bxs), 1),
        py::round_dp(span(&bys), 1),
    ];
    let radii_r: Vec<f64> = radii.iter().map(|&r| py::round_dp(r, 1)).collect();
    let body = format!(
        "{{\"centre\": {}, \"radii\": {}, \"band_in\": {}, \"band_out\": {}, \"air_in\": {}, \"air_out\": {}, \"len\": {}, \"gap\": {}, \"openings\": {}, \"bbox\": {}}}",
        pts_json(&c),
        nums_json(&radii_r),
        pts_json(&band_in),
        pts_json(&band_out),
        pts_json(&air_in),
        pts_json(&air_out),
        py::repr(py::round_dp(length, 1)),
        py::repr(py::round_dp(gap, 2)),
        py::round(openings(&c)),
        nums_json(&bbox)
    );
    let here = format!("{}/volute", env!("CARGO_MANIFEST_DIR"));
    std::fs::write(format!("{here}/volute.json"), body).map_err(|e| e.to_string())?;
    println!("\n  wrote volute.json  ({} x {}mm cheek)", py::repr(bbox[2]), py::repr(bbox[3]));
    Ok(0)
}

fn main() {
    let a: Vec<String> = std::env::args().skip(1).collect();
    std::process::exit(match run(&a) {
        Ok(rc) => rc,
        Err(e) => {
            println!("error: {e}");
            1
        }
    });
}
