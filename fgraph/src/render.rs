use crossterm::style::Color;
use std::io::Write;

const DOT_BITS: [[u8; 2]; 4] = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]];

/// A braille sub-pixel canvas: each terminal cell holds a 2x4 grid of dots,
/// giving 2x horizontal and 4x vertical resolution over plain block characters.
pub struct Canvas {
    pub cols: usize,
    pub rows: usize,
    sub_w: usize,
    sub_h: usize,
    dots: Vec<u8>,
    color: Vec<Option<Color>>,
}

impl Canvas {
    pub fn new(cols: usize, rows: usize) -> Self {
        let sub_w = cols * 2;
        let sub_h = rows * 4;
        Canvas {
            cols,
            rows,
            sub_w,
            sub_h,
            dots: vec![0u8; cols * rows],
            color: vec![None; cols * rows],
        }
    }

    pub fn clear(&mut self) {
        self.dots.iter_mut().for_each(|d| *d = 0);
        self.color.iter_mut().for_each(|c| *c = None);
    }

    pub fn set(&mut self, x: i32, y: i32, color: Color) {
        if x < 0 || y < 0 || x as usize >= self.sub_w || y as usize >= self.sub_h {
            return;
        }
        let (x, y) = (x as usize, y as usize);
        let cell_x = x / 2;
        let cell_y = y / 4;
        let bit = DOT_BITS[y % 4][x % 2];
        let idx = cell_y * self.cols + cell_x;
        self.dots[idx] |= bit;
        self.color[idx] = Some(color);
    }

    pub fn line(&mut self, x0: i32, y0: i32, x1: i32, y1: i32, color: Color) {
        let (mut x0, mut y0) = (x0, y0);
        let dx = (x1 - x0).abs();
        let dy = -(y1 - y0).abs();
        let sx = if x0 < x1 { 1 } else { -1 };
        let sy = if y0 < y1 { 1 } else { -1 };
        let mut err = dx + dy;
        loop {
            self.set(x0, y0, color);
            if x0 == x1 && y0 == y1 {
                break;
            }
            let e2 = 2 * err;
            if e2 >= dy {
                err += dy;
                x0 += sx;
            }
            if e2 <= dx {
                err += dx;
                y0 += sy;
            }
        }
    }

    /// Marks a small filled disk (node marker) rather than a single dot, so points
    /// stay visible even after the 2x/4x subpixel downsample.
    pub fn point(&mut self, cx: i32, cy: i32, radius: i32, color: Color) {
        for dy in -radius..=radius {
            for dx in -radius..=radius {
                if dx * dx + dy * dy <= radius * radius {
                    self.set(cx + dx, cy + dy, color);
                }
            }
        }
    }

    pub fn render(&self, out: &mut impl Write, origin_row: u16) -> std::io::Result<()> {
        use crossterm::cursor::MoveTo;
        use crossterm::queue;
        use crossterm::style::{ResetColor, SetForegroundColor};

        for row in 0..self.rows {
            queue!(out, MoveTo(0, origin_row + row as u16))?;
            let mut last_color: Option<Color> = None;
            let mut line = String::with_capacity(self.cols);
            for col in 0..self.cols {
                let idx = row * self.cols + col;
                let bits = self.dots[idx];
                let ch = char::from_u32(0x2800 + bits as u32).unwrap_or(' ');
                let c = self.color[idx];
                if c != last_color {
                    if !line.is_empty() {
                        queue!(out, crossterm::style::Print(&line))?;
                        line.clear();
                    }
                    match c {
                        Some(col) => queue!(out, SetForegroundColor(col))?,
                        None => queue!(out, ResetColor)?,
                    }
                    last_color = c;
                }
                line.push(ch);
            }
            queue!(out, crossterm::style::Print(&line))?;
            queue!(out, ResetColor)?;
        }
        Ok(())
    }
}
