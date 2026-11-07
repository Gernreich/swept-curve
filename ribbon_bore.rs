//! ribbon_bore.py's path writer, in Rust, for the generators that borrow it
//! (the panpipes and the chanters): points to an SVG path's d, three
//! decimals, closed or open. ribbon_bore.py keeps its own for the bores.

/// 'M x,y L x,y ...' with ' Z' when closed.
pub fn path(pts: &[(f64, f64)], close: bool) -> String {
    let body: Vec<String> = pts.iter().map(|(x, y)| format!("{x:.3},{y:.3}")).collect();
    format!("M {}{}", body.join(" L "), if close { " Z" } else { "" })
}
