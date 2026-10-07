use image::{Rgb, RgbImage};
use serde_json::json;
use std::{env, time::Instant};

fn border(pixel: &Rgb<u8>) -> bool {
    let min = *pixel.0.iter().min().unwrap();
    let max = *pixel.0.iter().max().unwrap();
    (145..=210).contains(&min) && max - min <= 16
}

fn frames(image: &RgbImage) -> Vec<[u32; 4]> {
    let (width, height) = image.dimensions();
    let mut candidates = Vec::new();
    for y in 0..height {
        let mut x = 0;
        while x < width {
            if !border(image.get_pixel(x, y)) {
                x += 1;
                continue;
            }
            let left = x;
            while x < width && border(image.get_pixel(x, y)) {
                x += 1;
            }
            let right = x - 1;
            if !(60..=width / 2).contains(&(right - left + 1)) {
                continue;
            }
            for bottom in (y + 18)..(y + 66).min(height) {
                let bottom_line = (left..=right)
                    .filter(|&xx| border(image.get_pixel(xx, bottom)))
                    .count();
                let sides = (y..=bottom)
                    .filter(|&yy| {
                        border(image.get_pixel(left, yy)) && border(image.get_pixel(right, yy))
                    })
                    .count();
                if bottom_line * 10 >= (right - left + 1) as usize * 9
                    && sides * 10 >= (bottom - y + 1) as usize * 9
                {
                    if border(image.get_pixel((left + right) / 2, (y + bottom) / 2)) {
                        continue;
                    }
                    let rect = [left, y, right + 1, bottom + 1];
                    if !candidates.iter().any(|r: &[u32; 4]| {
                        r.iter().zip(rect.iter()).all(|(a, b)| a.abs_diff(*b) <= 3)
                    }) {
                        candidates.push(rect);
                    }
                    break;
                }
            }
        }
    }
    candidates
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let started = Instant::now();
    let image = image::open(env::args().nth(1).ok_or("PNG path required")?)?.to_rgb8();
    if let Some(ocr_path) = env::args().nth(2) {
        image::imageops::resize(
            &image,
            image.width() * 3,
            image.height() * 3,
            image::imageops::FilterType::CatmullRom,
        )
        .save(ocr_path)?;
    }
    println!(
        "{}",
        json!({"frames":frames(&image),"elapsed_ms":started.elapsed().as_secs_f64()*1000.0})
    );
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn accepts_closed_frame_and_rejects_open_lines() {
        let mut image = RgbImage::from_pixel(400, 100, Rgb([255, 255, 255]));
        for x in 200..350 {
            image.put_pixel(x, 20, Rgb([180, 180, 180]));
            image.put_pixel(x, 49, Rgb([180, 180, 180]));
        }
        assert!(frames(&image).is_empty());
        for y in 20..50 {
            image.put_pixel(200, y, Rgb([180, 180, 180]));
            image.put_pixel(349, y, Rgb([180, 180, 180]));
        }
        assert_eq!(frames(&image), vec![[200, 20, 350, 50]]);
    }
    #[test]
    fn filled_tab_is_not_an_input_frame() {
        let mut image = RgbImage::from_pixel(400, 100, Rgb([255, 255, 255]));
        for x in 200..350 {
            for y in 20..50 {
                image.put_pixel(x, y, Rgb([180, 180, 180]));
            }
        }
        assert!(frames(&image).is_empty());
    }
}
