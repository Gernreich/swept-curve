//! A ribbon bore as a parametric SolidCraft design (2026-11-08):
//! `ribbon_view --solidcraft=FILE` with the design's own flags writes it, and
//! SolidCraft builds the STEP file from it.
//!
//! The centreline's vertices are the design's parameters, `c0_x`, `c0_y` and
//! on, as the generator lays them out; the bore and the ply are parameters,
//! and so are the sheet, the kerf and the slot's tightening that set how far
//! each cheek runs past its walls. Everything else follows as the generator
//! works it out, as read-only parameters: each wall offset (bore + ply)/2 from
//! the centreline, mitred where its neighbouring offset lines meet; the
//! cheeks offset the same way to their rims; each panel along its wall,
//! trimmed ply/2 tan(turn/2) at each end so the concave corners just touch.
//! Move a vertex and the walls, cheeks and panels move with it.
//!
//! The panels are plain boxes, without teeth, and the cheeks have no
//! mortices, ports or caps. The bore lies in XY as the cut files draw it, the
//! cheeks at Z = +-bore/2.
use crate::{contours, Cfg, P, R};
use lasermade_tools::solidcraft::{n as nn, Script};

/// A point: its coordinates as parameter names, and its value at the defaults.
#[derive(Clone)]
struct Sp {
    x: String,
    y: String,
    v: P,
}

/// A unit vector: its parameter names and value.
#[derive(Clone)]
struct V {
    x: String,
    y: String,
    v: P,
}

fn pt(s: &mut Script, name: &str, x: String, y: String, v: P, what: &str) -> Sp {
    let (nx, ny) = (format!("{name}_x"), format!("{name}_y"));
    s.len(&nx, x, what);
    s.len(&ny, y, if what.starts_with("read only") { "read only" } else { what });
    Sp { x: nx, y: ny, v }
}

fn worst(got: &[Sp], want: &[P]) -> f64 {
    if got.len() != want.len() {
        return f64::INFINITY;
    }
    got.iter().zip(want).map(|(g, w)| (g.v.0 - w.0).hypot(g.v.1 - w.1)).fold(0.0, f64::max)
}

pub fn script(cfg: &Cfg) -> R<String> {
    let (c, inn, out, parts, _) = cfg.build()?;
    let mut s = Script::new();
    s.len("bore", format!("{} mm", nn(cfg.bore)), "the airway, wall face to wall face and cheek to cheek");
    s.len("ply", format!("{} mm", nn(cfg.thick)), "the ply the walls and cheeks are cut from, nominal");
    if cfg.narrow {
        s.len("sheet", format!("{} mm", nn(cfg.sheet)), "what the sheet actually calipers; the mortices are this wide");
        s.len("kerf", format!("{} mm", nn(cfg.burn)), "the beam, the full width the laser takes out");
        s.len("slot_tighten", format!("{} mm", nn(cfg.slot_tighten)), "how much narrower the mortices are drawn than the sheet");
        s.len("cheek_past", "(sheet - slot_tighten)/2 - kerf/2", "read only: the narrow cheek's rim past each wall's centreline, its mortice's edge");
    } else {
        s.len("web", format!("{} mm", nn(cfg.web)), "the cheek's web outboard of each mortice");
        s.len("cheek_past", "ply/2 + web", "read only: the cheek's rim past each wall's centreline");
    }
    s.len("wall_off", "bore/2 + ply/2", "read only: each wall's centreline from the bore's");
    s.len("cheek_off", "wall_off + cheek_past", "read only: each cheek's rim from the bore's centreline");
    // the centreline: its vertices, the design's own numbers
    let n = c.len();
    let shut = (c[0].0 - c[n - 1].0).abs() < 1e-9 && (c[0].1 - c[n - 1].1).abs() < 1e-9;
    let m = if shut { n - 1 } else { n };
    let mut cl: Vec<Sp> = (0..m).map(|k| pt(&mut s, &format!("c{k}"), format!("{} mm", nn(c[k].0)), format!("{} mm", nn(c[k].1)), c[k], "a vertex of the centreline")).collect();
    if shut {
        cl.push(cl[0].clone());
    }
    // each segment's normal, and each vertex's mitre (n1 + n2)/(1 + n1.n2);
    // a free end is square to its segment
    let mut nrm: Vec<V> = vec![];
    for k in 0..n - 1 {
        let (a, b) = (&cl[k], &cl[k + 1]);
        let l = format!("sqrt(({} - {})^2 + ({} - {})^2)", b.x, a.x, b.y, a.y);
        let (ux, uy) = (b.v.0 - a.v.0, b.v.1 - a.v.1);
        let lv = ux.hypot(uy);
        let (x, y) = (format!("n{k}_x"), format!("n{k}_y"));
        s.num(&x, format!("-({} - {})/({l})", b.y, a.y), "read only: a segment's normal");
        s.num(&y, format!("({} - {})/({l})", b.x, a.x), "read only");
        nrm.push(V { x, y, v: (-uy / lv, ux / lv) });
    }
    // and the trims, ply/2 tan(turn/2) = ply/2 |n1 x n2|/(1 + n1.n2)
    let mut mit: Vec<V> = vec![];
    let mut trim: Vec<(String, f64)> = vec![];
    for k in 0..n {
        let pair = if k > 0 && k < n - 1 {
            Some((&nrm[k - 1], &nrm[k]))
        } else if shut {
            Some((&nrm[n - 2], &nrm[0]))
        } else {
            None
        };
        match pair {
            Some((n1, n2)) => {
                let den = format!("(1 + {}*{} + {}*{})", n1.x, n2.x, n1.y, n2.y);
                let dv = 1.0 + n1.v.0 * n2.v.0 + n1.v.1 * n2.v.1;
                let (x, y) = (format!("m{k}_x"), format!("m{k}_y"));
                s.num(&x, format!("({} + {})/{den}", n1.x, n2.x), "read only: a vertex's mitre");
                s.num(&y, format!("({} + {})/{den}", n1.y, n2.y), "read only");
                mit.push(V { x, y, v: ((n1.v.0 + n2.v.0) / dv, (n1.v.1 + n2.v.1) / dv) });
                let e = format!("e{k}");
                s.len(&e, format!("ply/2*abs({}*{} - {}*{})/{den}", n1.x, n2.y, n1.y, n2.x), "read only: a panel end's trim at this vertex");
                trim.push((e, cfg.thick / 2.0 * (n1.v.0 * n2.v.1 - n1.v.1 * n2.v.0).abs() / dv));
            }
            None => {
                mit.push(if k == 0 { nrm[0].clone() } else { nrm[n - 2].clone() });
                trim.push(("0 mm".into(), 0.0));
            }
        }
    }
    // the centreline moved d along each mitre
    let side = |s: &mut Script, name: &str, d: &str, dv: f64| -> Vec<Sp> {
        let mut p: Vec<Sp> = (0..m)
            .map(|k| {
                let (a, mk) = (&cl[k], &mit[k]);
                pt(s, &format!("{name}{k}"), format!("{} + ({d})*{}", a.x, mk.x), format!("{} + ({d})*{}", a.y, mk.y), (a.v.0 + dv * mk.v.0, a.v.1 + dv * mk.v.1), "read only: a point of the bore")
            })
            .collect();
        if shut {
            p.push(p[0].clone());
        }
        p
    };
    let (w, cp) = (cfg.wall_off(), cfg.cheek_off());
    let wa = side(&mut s, "wa", "wall_off", w);
    let wb = side(&mut s, "wb", "-wall_off", -w);
    // which side is the inner wall: the generator's own choice, the shorter;
    // an S-bore's two are the same length to its last digit, so take its word
    let (wi, wo) = if worst(&wa, &inn) < worst(&wb, &inn) { (wa, wb) } else { (wb, wa) };
    if worst(&wi, &inn) > 1e-9 || worst(&wo, &out) > 1e-9 {
        return Err("the design's walls are off the generator's".into());
    }
    let ra = side(&mut s, "ra", "cheek_off", cp);
    let rb = side(&mut s, "rb", "-cheek_off", -cp);
    let mut want = cfg.cheek(&c);
    let rims: Vec<Vec<Sp>> = if shut {
        vec![ra[..m].to_vec(), rb.iter().rev().take(m).cloned().collect()]
    } else {
        let mut o = ra.clone();
        o.extend(rb.iter().rev().cloned());
        vec![o]
    };
    let wc = contours(&want);
    let mut off = 0.0f64;
    for (r, w) in rims.iter().zip(&wc) {
        let mut w = w.clone();
        if shut {
            w.pop();
        }
        off = off.max(worst(r, &w));
    }
    want.clear();
    if rims.len() != wc.len() || off > 1e-9 {
        return Err(format!("the design's cheek rims are {off:e} off the generator's"));
    }
    // the panels: inner wall first, then outer, as the generator numbers them
    struct Pn {
        name: String,
        mid: Sp,
        len: String,
        n: V,
    }
    let mut pans: Vec<Pn> = vec![];
    let mut k_part = 0;
    for (wall, q) in [("inner", &wi), ("outer", &wo)] {
        // each facet's panel: (length expression and value, middle as
        // expressions and value, normal), before any lead is folded
        struct Seg {
            len: (String, f64),
            mid: (String, String, P),
            n: V,
            u: (String, String, P),
        }
        let mut segs: Vec<Option<Seg>> = vec![];
        for i in 1..n {
            let (a, b) = (&q[i - 1], &q[i]);
            let (e0, e1) = (&trim[i - 1], &trim[i]);
            let nk = &nrm[i - 1];
            let (ux, uy) = (nk.y.clone(), format!("(-{})", nk.x));
            let (uxv, uyv) = (nk.v.1, -nk.v.0);
            let len = format!("sqrt(({} - {})^2 + ({} - {})^2) - {} - {}", b.x, a.x, b.y, a.y, e0.0, e1.0);
            let lv = (b.v.0 - a.v.0).hypot(b.v.1 - a.v.1) - e0.1 - e1.1;
            let sh = format!("({} - {})/2", e0.0, e1.0);
            let mv = ((a.v.0 + b.v.0) / 2.0 + (e0.1 - e1.1) / 2.0 * uxv, (a.v.1 + b.v.1) / 2.0 + (e0.1 - e1.1) / 2.0 * uyv);
            let mid = (format!("({} + {})/2 + {sh}*{ux}", a.x, b.x), format!("({} + {})/2 + {sh}*{uy}", a.y, b.y), mv);
            segs.push(Some(Seg { len: (len, lv), mid, n: nk.clone(), u: (ux, uy, (uxv, uyv)) }));
        }
        // --merge-lead: the lead panel folds into the next, which lies in line
        // with it, as merge_lead() folds it (and the last into the one before
        // it with --port-both)
        if cfg.merge_lead {
            let ns = segs.len();
            let mut folds = vec![(0usize, 1usize, -1.0f64)];
            if cfg.port_both {
                folds.push((ns - 1, ns - 2, 1.0));
            }
            for (li, ni, sg) in folds {
                let lead = segs[li].take().unwrap();
                let nx = segs[ni].as_mut().unwrap();
                let half = format!("({})/2", lead.len.0);
                let hv = lead.len.1 / 2.0;
                nx.mid = (
                    format!("{} + {}*{half}*{}", nx.mid.0, nn(sg), nx.u.0),
                    format!("{} + {}*{half}*{}", nx.mid.1, nn(sg), nx.u.1),
                    (nx.mid.2 .0 + sg * hv * nx.u.2 .0, nx.mid.2 .1 + sg * hv * nx.u.2 .1),
                );
                nx.len = (format!("{} + {}", lead.len.0, nx.len.0), lead.len.1 + nx.len.1);
            }
        }
        for sg in segs.into_iter().flatten() {
            let p = &parts[k_part];
            if p.wall != wall || (p.mid.0 - sg.mid.2 .0).hypot(p.mid.1 - sg.mid.2 .1) > 1e-9 || (p.len - sg.len.1).abs() > 1e-9 {
                return Err(format!("the design's {wall} panel {} is off the generator's", p.tag));
            }
            let tag = p.tag.clone();
            let w1 = &wall[..1];
            let len = format!("p{tag}{w1}_len");
            s.len(&len, sg.len.0, "read only: a panel's length");
            let mid = pt(&mut s, &format!("p{tag}{w1}_mid"), sg.mid.0, sg.mid.1, sg.mid.2, "read only: a panel's middle");
            pans.push(Pn { name: format!("{wall} panel {tag}"), mid, len, n: sg.n });
            k_part += 1;
        }
    }
    if k_part != parts.len() {
        return Err("the design has a different number of panels from the generator".into());
    }
    let xy = |p: &Sp| [p.x.clone(), p.y.clone()];
    for (name, z) in [("top cheek", "bore/2"), ("bottom cheek", "-bore/2 - ply")] {
        let sk = s.sketch("XY", Some(z), &format!("{name} sketch"));
        for r in &rims {
            let pts: Vec<[String; 2]> = r.iter().map(xy).collect();
            s.poly(&pts);
        }
        s.finish();
        s.extrude(&sk, "ply", false, "new", &[], name);
    }
    for p in &pans {
        let sk = s.sketch("XY", Some("-bore/2"), &format!("{} sketch", p.name));
        let corner = |a: f64, b: f64| -> [String; 2] {
            [
                format!("{} + {}*{}/2*{} + {}*ply/2*{}", p.mid.x, nn(a), p.len, p.n.y, nn(b), p.n.x),
                format!("{} - {}*{}/2*{} + {}*ply/2*{}", p.mid.y, nn(a), p.len, p.n.x, nn(b), p.n.y),
            ]
        };
        s.poly(&[corner(-1.0, -1.0), corner(1.0, -1.0), corner(1.0, 1.0), corner(-1.0, 1.0)]);
        s.finish();
        s.extrude(&sk, "bore", false, "new", &[], &p.name);
    }
    s.measure();
    Ok(s.text())
}
