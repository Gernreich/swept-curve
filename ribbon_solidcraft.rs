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
//! Each panel carries its teeth, `tooth` wide and a ply proud through each
//! cheek, and the cheeks their mortices, `mortice_w` along the wall and
//! `mortice_h` either side of its centreline, as cut (2026-11-09). A panel's
//! teeth are as many as fit its length, `floor((len - 2 shoulder + tooth) /
//! (2 tooth))` and at least one, patterned along a line drawn down the panel,
//! so lengthening a panel adds a tooth and turning it turns them. A panel
//! whose teeth the generator settled otherwise (a port took one, or a lead
//! was folded in) has them where the default build does. The cheeks have
//! their ports, as cut; there are no caps. The bore lies in XY as the cut files draw it, the cheeks at
//! Z = +-bore/2.
use crate::{contours, offset, Cfg, P, R};
use lasermade_tools::py::{mcos as cos, msin as sin};
use lasermade_tools::solidcraft::{n as nn, q, Script};

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

/// One panel's joints: its body, its middle, the unit vector along it and
/// the one across it (expressions), its length, and where its teeth are when
/// the generator did not lay them out from the length alone (offsets from
/// the middle along `u`).
pub struct Joint {
    pub body: String,
    pub pname: String,
    pub mid: (String, String),
    pub u: (String, String),
    pub n: (String, String),
    pub len: String,
    pub fixed: Option<Vec<f64>>,
}

/// Every panel's teeth, joined to it, and their mortices, cut through the
/// `cheeks`. Reads the parameters bore, ply, tooth, shoulder, mortice_w and
/// mortice_h. `map` turns world (x, y) into the sketch's coordinates.
pub fn joints(s: &mut Script, pans: &[Joint], cheeks: &[&str], map: &dyn Fn(String, String) -> [String; 2]) {
    for p in pans {
        // a point c + a along the panel and b across it, from its middle
        let at = |c: &str, a: &str, b: &str| -> [String; 2] {
            map(
                format!("{} + ({c} + {a})*({}) + ({b})*({})", p.mid.0, p.u.0, p.n.0),
                format!("{} + ({c} + {a})*({}) + ({b})*({})", p.mid.1, p.u.1, p.n.1),
            )
        };
        let (seeds, count) = match &p.fixed {
            None => {
                let n = format!("{}_teeth", p.pname);
                s.num(&n, format!("max(1, floor((({}) - 2*shoulder + tooth)/(2*tooth)))", p.len), "read only: a panel's teeth, as many as its length holds");
                (vec![format!("-({n} - 1)*tooth")], Some(n))
            }
            Some(cs) => (cs.iter().map(|c| format!("{} mm", nn(*c))).collect(), None),
        };
        let half = format!("({})/2", p.len);
        let guide = [at("0 mm", &format!("-{half}"), "0 mm"), at("0 mm", &half, "0 mm")];
        for (what, hu, hn, op, targets) in [("teeth", "tooth/2", "ply/2", "join", vec![p.body.as_str()]), ("mortices", "mortice_w/2", "mortice_h", "cut", cheeks.to_vec())] {
            let sk = s.sketch("XY", Some("-bore/2 - ply"), &format!("{} {what} sketch", p.body));
            // l1, the line the teeth are patterned along
            s.cmd("sketch.line", format!("{{\"points\":[[{},{}],[{},{}]],\"closed\":false}}", q(&guide[0][0]), q(&guide[0][1]), q(&guide[1][0]), q(&guide[1][1])));
            for c in &seeds {
                let (mu, mn) = (format!("-{hu}"), format!("-{hn}"));
                s.poly(&[at(c, &mu, &mn), at(c, hu, &mn), at(c, hu, hn), at(c, &mu, hn)]);
            }
            if let Some(n) = &count {
                // l2 to l5, the first tooth
                s.cmd("sketch.pattern.rectangular", format!("{{\"entities\":[\"l2\",\"l3\",\"l4\",\"l5\"],\"count\":{},\"spacing\":\"2*tooth\",\"direction\":\"l1\"}}", q(n)));
            }
            s.finish();
            s.extrude(&sk, "bore + 2*ply", false, op, &targets, &format!("{} {what}", p.body));
        }
    }
}

/// The joints' own parameters, after bore, ply, sheet and slot_tighten.
pub fn joint_params(s: &mut Script, cfg: &Cfg, play: &str) {
    s.len("tooth", format!("{} mm", nn(cfg.tooth)), "each tooth along its panel, and each gap between two");
    s.len("shoulder", format!("{} mm", nn(cfg.shoulder)), "the least of a panel left past its end teeth");
    s.len("play", play, "each mortice's play a side along its tooth");
    s.len("mortice_w", "tooth + 2*play - slot_tighten", "read only: a mortice along its wall, as cut");
    s.len("mortice_h", "(sheet - slot_tighten)/2", "read only: a mortice either side of its wall's centreline, as cut");
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
        s.len("cheek_past", "(sheet - slot_tighten)/2 - kerf", "read only: the narrow cheek's rim past each wall's centreline, as cut: the line is drawn on its mortices' edge, and the beam takes half a kerf inside it");
    } else {
        s.len("sheet", format!("{} mm", nn(cfg.sheet)), "what the sheet actually calipers; the mortices are this wide");
        s.len("slot_tighten", format!("{} mm", nn(cfg.slot_tighten)), "how much narrower the mortices are drawn than the sheet");
        s.len("kerf", format!("{} mm", nn(cfg.burn)), "the beam, the full width the laser takes out");
        s.len("web", format!("{} mm", nn(cfg.web)), "the cheek's web outboard of each mortice, as drawn");
        s.len("cheek_past", "ply/2 + web - kerf/2", "read only: the cheek's rim past each wall's centreline, as cut: the beam takes half a kerf inside the line");
    }
    joint_params(&mut s, cfg, &format!("{} mm", nn(cfg.play())));
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
    // the centreline moved d along each mitre; a cut rim's free ends also
    // half a kerf in along their segments, as the beam takes them
    let side = |s: &mut Script, name: &str, d: &str, dv: f64, cut: bool| -> Vec<Sp> {
        let mut p: Vec<Sp> = (0..m)
            .map(|k| {
                let (a, mk) = (&cl[k], &mit[k]);
                // the segment's direction, u = (n.y, -n.x), pointing inward
                let inw = if cut && !shut && (k == 0 || k == m - 1) {
                    let (nk, sg) = if k == 0 { (&nrm[0], 1.0) } else { (&nrm[n - 2], -1.0) };
                    Some((nk, sg))
                } else {
                    None
                };
                let (ex, ey, ev) = match inw {
                    Some((nk, sg)) => (
                        format!(" + {}*kerf/2*{}", nn(sg), nk.y),
                        format!(" - {}*kerf/2*{}", nn(sg), nk.x),
                        (sg * cfg.burn / 2.0 * nk.v.1, -sg * cfg.burn / 2.0 * nk.v.0),
                    ),
                    None => (String::new(), String::new(), (0.0, 0.0)),
                };
                pt(s, &format!("{name}{k}"), format!("{} + ({d})*{}{ex}", a.x, mk.x), format!("{} + ({d})*{}{ey}", a.y, mk.y), (a.v.0 + dv * mk.v.0 + ev.0, a.v.1 + dv * mk.v.1 + ev.1), "read only: a point of the bore")
            })
            .collect();
        if shut {
            p.push(p[0].clone());
        }
        p
    };
    // the cheek's rim as cut: the generator draws it on the line, with no
    // kerf added, so the beam leaves it half a kerf inside
    let (w, cp) = (cfg.wall_off(), cfg.cheek_off() - cfg.burn / 2.0);
    let wa = side(&mut s, "wa", "wall_off", w, false);
    let wb = side(&mut s, "wb", "-wall_off", -w, false);
    // which side is the inner wall: the generator's own choice, the shorter;
    // an S-bore's two are the same length to its last digit, so take its word
    let (wi, wo) = if worst(&wa, &inn) < worst(&wb, &inn) { (wa, wb) } else { (wb, wa) };
    if worst(&wi, &inn) > 1e-9 || worst(&wo, &out) > 1e-9 {
        return Err("the design's walls are off the generator's".into());
    }
    let ra = side(&mut s, "ra", "cheek_off", cp, true);
    let rb = side(&mut s, "rb", "-cheek_off", -cp, true);
    let mut want = {
        let mut a = offset(&c, cp);
        a.extend(offset(&c, -cp).into_iter().rev());
        if !shut {
            // the free ends, half a kerf in
            let h = cfg.burn / 2.0;
            let u = |p: P, q: P| {
                let l = (q.0 - p.0).hypot(q.1 - p.1);
                ((q.0 - p.0) / l * h, (q.1 - p.1) / l * h)
            };
            let (u0, u1) = (u(c[0], c[1]), u(c[n - 1], c[n - 2]));
            let k = a.len();
            for (i, d) in [(0, u0), (m - 1, u1), (m, u1), (k - 1, u0)] {
                a[i] = (a[i].0 + d.0, a[i].1 + d.1);
            }
        }
        a
    };
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
        pname: String,
        fixed: Option<Vec<f64>>,
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
            // the teeth, unless the generator's are the length's own: then
            // where it put them, along this panel's u = (n.y, -n.x)
            let mine = p.teeth.clone().unwrap_or_else(|| cfg.teeth(p.len));
            let fixed = if mine == cfg.teeth(p.len) {
                None
            } else {
                let sg = if cos(p.ang) * sg.n.v.1 - sin(p.ang) * sg.n.v.0 < 0.0 { -1.0 } else { 1.0 };
                Some(mine.iter().map(|c| sg * c).collect())
            };
            let len = format!("p{tag}{w1}_len");
            s.len(&len, sg.len.0, "read only: a panel's length");
            let mid = pt(&mut s, &format!("p{tag}{w1}_mid"), sg.mid.0, sg.mid.1, sg.mid.2, "read only: a panel's middle");
            pans.push(Pn { name: format!("{wall} panel {tag}"), mid, len, n: sg.n, pname: format!("p{tag}{w1}"), fixed });
            k_part += 1;
        }
    }
    if k_part != parts.len() {
        return Err("the design has a different number of panels from the generator".into());
    }
    let xy = |p: &Sp| [p.x.clone(), p.y.clone()];
    // the ports, as cut: port_across by port_along on the centreline,
    // port_from_tip along its facet (the generator draws them half a kerf
    // small); under --port-per-cheek the top cheek has the first, the
    // bottom the second, else both have every one
    let mut ports: Vec<Vec<[String; 2]>> = vec![];
    if cfg.port {
        s.len("port_across", format!("{} mm", nn(cfg.port_across)), "a port across the bore, as cut");
        s.len("port_along", format!("{} mm", nn(cfg.port_along)), "a port along it, as cut");
        s.len("port_from_tip", format!("{} mm", nn(cfg.port_from_tip)), "a port's middle along its facet");
        let ends: Vec<(usize, usize)> = match &cfg.port_at {
            Some(at) => at.iter().map(|&i| (i as usize, i as usize + 1)).collect(),
            None => {
                let mut v = vec![(0, 1)];
                if cfg.port_both {
                    v.push((n - 1, n - 2));
                }
                v
            }
        };
        let want = cfg.port_holes(&c)?;
        for (k, &(ia, ib)) in ends.iter().enumerate() {
            let (a, b) = (&cl[ia], &cl[ib]);
            let l = format!("sqrt(({} - {})^2 + ({} - {})^2)", b.x, a.x, b.y, a.y);
            let (ux, uy) = (format!("port{k}_ux"), format!("port{k}_uy"));
            s.num(&ux, format!("({} - {})/({l})", b.x, a.x), "read only: a port's facet, its direction");
            s.num(&uy, format!("({} - {})/({l})", b.y, a.y), "read only");
            let (uv, m) = ((b.v.0 - a.v.0, b.v.1 - a.v.1), (b.v.0 - a.v.0).hypot(b.v.1 - a.v.1));
            let uv = (uv.0 / m, uv.1 / m);
            let mut got: Vec<P> = vec![];
            let mut ring: Vec<[String; 2]> = vec![];
            for (su, sn) in [(1.0, 1.0), (1.0, -1.0), (-1.0, -1.0), (-1.0, 1.0)] {
                // n = (-u.y, u.x)
                ring.push([
                    format!("{} + port_from_tip*{ux} + {}*port_along/2*{ux} - {}*port_across/2*{uy}", a.x, nn(su), nn(sn)),
                    format!("{} + port_from_tip*{uy} + {}*port_along/2*{uy} + {}*port_across/2*{ux}", a.y, nn(su), nn(sn)),
                ]);
                let (al, ac) = (cfg.port_along / 2.0, cfg.port_across / 2.0);
                got.push((a.v.0 + cfg.port_from_tip * uv.0 + su * al * uv.0 - sn * ac * uv.1, a.v.1 + cfg.port_from_tip * uv.1 + su * al * uv.1 + sn * ac * uv.0));
            }
            // the generator's, grown half a kerf to as cut
            let e = cfg.burn / 2.0;
            let w = &want[k];
            let wc = ((w[0].0 + w[2].0) / 2.0, (w[0].1 + w[2].1) / 2.0);
            let grown: Vec<P> = w[..4].iter().map(|q| {
                let (dx, dy) = (q.0 - wc.0, q.1 - wc.1);
                let (al, ac) = (dx * uv.0 + dy * uv.1, -dx * uv.1 + dy * uv.0);
                let (al, ac) = (al + e * al.signum(), ac + e * ac.signum());
                (wc.0 + al * uv.0 - ac * uv.1, wc.1 + al * uv.1 + ac * uv.0)
            }).collect();
            let off = got.iter().map(|g| grown.iter().map(|q| (g.0 - q.0).hypot(g.1 - q.1)).fold(f64::MAX, f64::min)).fold(0.0, f64::max);
            if off > 1e-9 {
                return Err(format!("the design's port {k} is {off:e} off the generator's"));
            }
            ports.push(ring);
        }
    }
    for (ci, (name, z)) in [("top cheek", "bore/2"), ("bottom cheek", "-bore/2 - ply")].into_iter().enumerate() {
        let sk = s.sketch("XY", Some(z), &format!("{name} sketch"));
        for r in &rims {
            let pts: Vec<[String; 2]> = r.iter().map(xy).collect();
            s.poly(&pts);
        }
        for (k, ring) in ports.iter().enumerate() {
            if !cfg.port_per_cheek || k == ci {
                s.poly(ring);
            }
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
    let js: Vec<Joint> = pans
        .iter()
        .map(|p| Joint {
            body: p.name.clone(),
            pname: p.pname.clone(),
            mid: (p.mid.x.clone(), p.mid.y.clone()),
            u: (p.n.y.clone(), format!("(-{})", p.n.x)),
            n: (p.n.x.clone(), p.n.y.clone()),
            len: p.len.clone(),
            fixed: p.fixed.clone(),
        })
        .collect();
    joints(&mut s, &js, &["top cheek", "bottom cheek"], &|x, y| [x, y]);
    s.measure();
    Ok(s.text())
}
