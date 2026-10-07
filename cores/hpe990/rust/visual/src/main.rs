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
    if env::args().nth(1).as_deref() == Some("--diff") {
        let before = image::open(env::args().nth(2).ok_or("Before PNG required")?)?.to_rgb8();
        let after = image::open(env::args().nth(3).ok_or("After PNG required")?)?.to_rgb8();
        let mut result = pixel_diff(&before, &after);
        result["elapsed_ms"] = json!(started.elapsed().as_secs_f64() * 1000.0);
        println!("{result}");
        return Ok(());
    }
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

fn pixel_diff(before: &RgbImage, after: &RgbImage) -> serde_json::Value {
    if before.dimensions() != after.dimensions() {
        return json!({"changed":true,"dimension_changed":true,
            "before_size":[before.width(),before.height()],
            "after_size":[after.width(),after.height()],"regions":[]});
    }
    let (width, height) = after.dimensions();
    let mut regions = Vec::new();
    let mut total = 0_u64;
    for top in (0..height).step_by(32) {
        for left in (0..width).step_by(32) {
            let mut count = 0_u64;
            let mut bounds = [width, height, 0, 0];
            let mut example = None;
            let mut max_delta = 0_u8;
            for y in top..(top + 32).min(height) {
                for x in left..(left + 32).min(width) {
                    let a = before.get_pixel(x, y).0;
                    let b = after.get_pixel(x, y).0;
                    if a != b {
                        count += 1;
                        bounds[0] = bounds[0].min(x);
                        bounds[1] = bounds[1].min(y);
                        bounds[2] = bounds[2].max(x + 1);
                        bounds[3] = bounds[3].max(y + 1);
                        if example.is_none() {
                            example = Some(json!({"position":[x,y],"before_rgb":a,"after_rgb":b}));
                        }
                        for channel in 0..3 {
                            max_delta = max_delta.max(a[channel].abs_diff(b[channel]));
                        }
                    }
                }
            }
            if count != 0 {
                total += count;
                regions.push(json!({"rect":bounds,"changed_pixels":count,
                    "max_channel_delta":max_delta,"example":example}));
            }
        }
    }
    json!({"changed":total!=0,"dimension_changed":false,"changed_pixels":total,
        "total_pixels":u64::from(width)*u64::from(height),"regions":regions,
        "threshold":0,"rect_space":"root_screenshot_pixels"})
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn detects_single_channel_single_pixel_without_threshold() {
        let before = RgbImage::from_pixel(70, 70, Rgb([50, 60, 70]));
        let mut after = before.clone();
        assert_eq!(pixel_diff(&before, &after)["changed"], false);
        after.put_pixel(40, 50, Rgb([50, 61, 70]));
        let diff = pixel_diff(&before, &after);
        assert_eq!(diff["changed_pixels"], 1);
        assert_eq!(diff["regions"][0]["rect"], json!([40, 50, 41, 51]));
        assert_eq!(diff["regions"][0]["max_channel_delta"], 1);
    }
    #[test]
    fn records_resize_instead_of_comparing_misaligned_pixels() {
        assert_eq!(
            pixel_diff(&RgbImage::new(2, 2), &RgbImage::new(3, 2))["dimension_changed"],
            true
        );
    }
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
