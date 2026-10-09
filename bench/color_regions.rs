//! Bounded CPU color components. Experimental; no PDF semantics are inferred.
use std::io::{self, Read};

#[derive(Clone)]
struct Region {
    bbox: [usize; 4],
    area: usize,
    sum: [u64; 3],
    perimeter: usize,
    dark_edges: usize,
    border: bool,
}
fn number(args: &[String], key: &str, default: usize) -> Result<usize, String> {
    match args.iter().position(|s| s == key) {
        Some(i) => args
            .get(i + 1)
            .ok_or(format!("missing {key}"))?
            .parse()
            .map_err(|_| format!("invalid {key}")),
        None => Ok(default),
    }
}
fn reserve<T>(v: &mut Vec<T>, n: usize) -> Result<(), String> {
    v.try_reserve_exact(n)
        .map_err(|_| "allocation refused".into())
}
fn run() -> Result<(), String> {
    let args: Vec<String> = std::env::args().collect();
    let w = number(&args, "--width", 0)?;
    let h = number(&args, "--height", 0)?;
    let count = w.checked_mul(h).ok_or("pixel size overflow")?;
    if count > number(&args, "--max-pixels", 4_000_000)? || count > u32::MAX as usize {
        return Err("pixel limit".into());
    }
    let distance = number(&args, "--color-distance", 18)?;
    let luma = number(&args, "--luminance-distance", 18)?;
    let white = number(&args, "--background-white", 248)?;
    if distance > 442 || luma > 255 || white > 256 {
        return Err("threshold out of range".into());
    }
    let connectivity = number(&args, "--connectivity", 4)?;
    if connectivity != 4 && connectivity != 8 {
        return Err("connectivity must be 4 or 8".into());
    }
    let min_area = number(&args, "--min-area", 64)?;
    let max_components = number(&args, "--max-components", 65_536)?;
    let max_regions = number(&args, "--max-regions", 4096)?;
    let bytes = count.checked_mul(3).ok_or("byte size overflow")?;
    let mut rgb = Vec::new();
    reserve(&mut rgb, bytes + 1)?;
    io::stdin()
        .take((bytes + 1) as u64)
        .read_to_end(&mut rgb)
        .map_err(|e| e.to_string())?;
    if rgb.len() != bytes {
        return Err("RGB payload size mismatch".into());
    }
    let mut seen = Vec::new();
    reserve(&mut seen, count)?;
    seen.resize(count, 0u8);
    let mut queue: Vec<u32> = Vec::new();
    reserve(&mut queue, count)?;
    let mut regions = Vec::new();
    let mut components = 0;
    let luminance = |p: usize| -> i32 {
        (2126 * rgb[p * 3] as i32 + 7152 * rgb[p * 3 + 1] as i32 + 722 * rgb[p * 3 + 2] as i32)
            / 10000
    };
    for start in 0..count {
        if seen[start] != 0 {
            continue;
        }
        components += 1;
        if components > max_components {
            return Err("component limit".into());
        }
        queue.clear();
        queue.push(start as u32);
        seen[start] = 2;
        let mut r = Region {
            bbox: [w, h, 0, 0],
            area: 0,
            sum: [0; 3],
            perimeter: 0,
            dark_edges: 0,
            border: false,
        };
        let mut head = 0;
        while head < queue.len() {
            let p = queue[head] as usize;
            head += 1;
            let x = p % w;
            let y = p / w;
            r.area += 1;
            r.bbox[0] = r.bbox[0].min(x);
            r.bbox[1] = r.bbox[1].min(y);
            r.bbox[2] = r.bbox[2].max(x + 1);
            r.bbox[3] = r.bbox[3].max(y + 1);
            r.border |= x == 0 || y == 0 || x + 1 == w || y + 1 == h;
            for c in 0..3 {
                r.sum[c] += rgb[p * 3 + c] as u64;
            }
            for (dx, dy) in [
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
                (-1, -1),
                (1, -1),
                (-1, 1),
                (1, 1),
            ]
            .into_iter()
            .take(connectivity)
            {
                let nx = x as isize + dx;
                let ny = y as isize + dy;
                if nx < 0 || ny < 0 || nx >= w as isize || ny >= h as isize {
                    continue;
                }
                let q = ny as usize * w + nx as usize;
                let mut d2 = 0i32;
                for c in 0..3 {
                    let d = rgb[p * 3 + c] as i32 - rgb[q * 3 + c] as i32;
                    d2 += d * d;
                }
                let similar = d2 <= (distance * distance) as i32
                    && (luminance(p) - luminance(q)).unsigned_abs() as usize <= luma;
                if similar && seen[q] == 0 {
                    seen[q] = 2;
                    queue.push(q as u32);
                }
            }
        }
        // Measure the final component boundary, not color edges inside a
        // transitively connected component. Current members have marker 2.
        for &pixel in &queue {
            let p = pixel as usize;
            let x = p % w;
            let y = p / w;
            for (dx, dy) in [(-1, 0), (1, 0), (0, -1), (0, 1)] {
                let nx = x as isize + dx;
                let ny = y as isize + dy;
                if nx < 0 || ny < 0 || nx >= w as isize || ny >= h as isize {
                    r.perimeter += 1;
                    continue;
                }
                let q = ny as usize * w + nx as usize;
                if seen[q] != 2 {
                    r.perimeter += 1;
                    if luminance(q) + 10 < luminance(p) {
                        r.dark_edges += 1;
                    }
                }
            }
        }
        for &pixel in &queue {
            seen[pixel as usize] = 1;
        }
        if r.area >= min_area
            && !(r.border && r.sum.iter().all(|sum| *sum >= white as u64 * r.area as u64))
        {
            if regions.len() >= max_regions {
                return Err("region limit".into());
            }
            reserve(&mut regions, 1)?;
            regions.push(r);
        }
    }
    // All admissions finish before any stdout, so refusal never exposes partial output.
    let mut output = String::new();
    output
        .try_reserve(regions.len().saturating_mul(512))
        .map_err(|_| "allocation refused")?;
    use std::fmt::Write;
    output.push('[');
    for (i, r) in regions.iter().enumerate() {
        if i != 0 {
            output.push(',');
        }
        write!(&mut output, "{{\"bbox\":[{},{},{},{}],\"area\":{},\"mean_rgb\":[{:.4},{:.4},{:.4}],\"perimeter\":{},\"dark_boundary_fraction\":{:.6},\"touches_border\":{}}}",
            r.bbox[0],r.bbox[1],r.bbox[2],r.bbox[3],r.area,r.sum[0] as f64/r.area as f64,r.sum[1] as f64/r.area as f64,r.sum[2] as f64/r.area as f64,r.perimeter,r.dark_edges as f64/r.perimeter.max(1) as f64,r.border).map_err(|e| e.to_string())?;
    }
    output.push(']');
    println!("{output}");
    Ok(())
}
fn main() {
    if let Err(error) = run() {
        eprintln!("color-regions: {error}");
        std::process::exit(2);
    }
}
