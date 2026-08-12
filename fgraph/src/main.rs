mod camera;
mod layout;
mod render;
mod scan;

use camera::Camera;
use crossterm::event::{self, Event, KeyCode, KeyEventKind};
use crossterm::style::Color;
use crossterm::terminal;
use crossterm::{cursor, execute, queue};
use render::Canvas;
use std::io::{stdout, Write};
use std::path::PathBuf;
use std::process::Command;
use std::time::{Duration, Instant};

fn human_size(bytes: u64) -> String {
    const UNITS: [&str; 5] = ["B", "KB", "MB", "GB", "TB"];
    let mut size = bytes as f64;
    let mut unit = 0;
    while size >= 1024.0 && unit < UNITS.len() - 1 {
        size /= 1024.0;
        unit += 1;
    }
    format!("{:.1} {}", size, UNITS[unit])
}

fn depth_color(depth: u32) -> Color {
    match depth % 6 {
        0 => Color::Cyan,
        1 => Color::Green,
        2 => Color::Yellow,
        3 => Color::Magenta,
        4 => Color::Blue,
        _ => Color::White,
    }
}

/// Color by file category so the shape of the tree also reads as "what's in it"
/// at a glance: code vs media vs archives vs docs, independent of depth.
fn category_color(name: &str) -> Color {
    let ext = name
        .rsplit_once('.')
        .map(|(_, e)| e.to_ascii_lowercase())
        .unwrap_or_default();
    match ext.as_str() {
        "rs" | "py" | "js" | "ts" | "tsx" | "jsx" | "c" | "cpp" | "h" | "hpp" | "java" | "go"
        | "rb" | "php" | "cs" | "swift" | "kt" | "sh" | "ps1" => Color::Rgb { r: 90, g: 220, b: 130 },
        "md" | "txt" | "pdf" | "doc" | "docx" | "rtf" | "odt" => Color::Rgb { r: 230, g: 220, b: 130 },
        "png" | "jpg" | "jpeg" | "gif" | "svg" | "bmp" | "webp" | "ico" => {
            Color::Rgb { r: 230, g: 120, b: 220 }
        }
        "mp4" | "mov" | "avi" | "mkv" | "webm" => Color::Rgb { r: 120, g: 180, b: 230 },
        "mp3" | "wav" | "flac" | "ogg" | "m4a" => Color::Rgb { r: 230, g: 160, b: 90 },
        "zip" | "rar" | "7z" | "tar" | "gz" | "bz2" => Color::Rgb { r: 190, g: 90, b: 90 },
        "exe" | "dll" | "msi" | "bat" | "sys" => Color::Rgb { r: 255, g: 90, b: 90 },
        "json" | "yaml" | "yml" | "toml" | "xml" | "csv" | "ini" | "cfg" => {
            Color::Rgb { r: 120, g: 220, b: 220 }
        }
        _ => Color::Rgb { r: 150, g: 150, b: 150 },
    }
}

/// Radius grows with "weight" so bigger files and fuller directories stand out
/// as visibly larger nodes instead of every entry rendering as the same dot.
fn size_radius(is_dir: bool, size: u64, leaf_count: u32) -> i32 {
    if is_dir {
        match leaf_count {
            0..=1 => 1,
            2..=10 => 2,
            11..=50 => 3,
            _ => 4,
        }
    } else {
        match size {
            0..=10_240 => 1,               // < 10 KB
            10_241..=102_400 => 2,         // < 100 KB
            102_401..=1_048_576 => 3,      // < 1 MB
            _ => 4,                        // >= 1 MB
        }
    }
}

fn main() -> anyhow::Result<()> {
    let mut args = std::env::args().skip(1);
    let root_path: PathBuf = args
        .next()
        .map(PathBuf::from)
        .unwrap_or_else(|| std::env::current_dir().unwrap());
    let max_depth: u32 = args
        .next()
        .and_then(|s| s.parse().ok())
        .unwrap_or(6);

    let mut graph = scan::scan(&root_path, max_depth, 6000);
    layout::layout(&mut graph);

    let max_radius = graph
        .nodes
        .iter()
        .map(|n| (n.pos[0].powi(2) + n.pos[1].powi(2) + n.pos[2].powi(2)).sqrt())
        .fold(1.0f32, f32::max);

    let mut camera = Camera::new(max_radius);
    let mut selected: usize = 0;

    terminal::enable_raw_mode()?;
    let mut out = stdout();
    execute!(
        out,
        terminal::EnterAlternateScreen,
        terminal::Clear(terminal::ClearType::All),
        cursor::Hide
    )?;

    let result = run(&mut out, &graph, &mut camera, &mut selected);

    execute!(out, cursor::Show, terminal::LeaveAlternateScreen)?;
    terminal::disable_raw_mode()?;
    result
}

fn run(
    out: &mut impl Write,
    graph: &scan::Graph,
    camera: &mut Camera,
    selected: &mut usize,
) -> anyhow::Result<()> {
    let frame_time = Duration::from_millis(33);
    loop {
        let frame_start = Instant::now();

        while event::poll(Duration::from_millis(0))? {
            if let Event::Key(key) = event::read()? {
                if key.kind != KeyEventKind::Press {
                    continue;
                }
                match key.code {
                    KeyCode::Char('q') | KeyCode::Esc => return Ok(()),
                    KeyCode::Left | KeyCode::Char('a') => camera.yaw -= 0.1,
                    KeyCode::Right | KeyCode::Char('d') => camera.yaw += 0.1,
                    KeyCode::Up | KeyCode::Char('w') => camera.pitch -= 0.08,
                    KeyCode::Down | KeyCode::Char('s') => camera.pitch += 0.08,
                    KeyCode::Char('+') | KeyCode::Char('=') => {
                        camera.distance = (camera.distance - 3.0).max(3.0)
                    }
                    KeyCode::Char('-') | KeyCode::Char('_') => camera.distance += 3.0,
                    KeyCode::Char(' ') => camera.auto_rotate = !camera.auto_rotate,
                    KeyCode::Char('r') => {
                        camera.yaw = 0.6;
                        camera.pitch = 0.4;
                        camera.auto_rotate = true;
                    }
                    KeyCode::Tab | KeyCode::Char('n') => {
                        *selected = (*selected + 1) % graph.nodes.len()
                    }
                    KeyCode::Char('p') => {
                        *selected = (*selected + graph.nodes.len() - 1) % graph.nodes.len()
                    }
                    KeyCode::Enter | KeyCode::Char('o') => {
                        let path = &graph.nodes[*selected].path;
                        let _ = Command::new("explorer").arg(path).spawn();
                    }
                    _ => {}
                }
            }
        }

        if camera.auto_rotate {
            camera.yaw += 0.01;
        }

        let (cols, rows) = terminal::size()?;
        let info_rows = 3u16;
        let canvas_rows = rows.saturating_sub(info_rows).max(1);
        let mut canvas = Canvas::new(cols as usize, canvas_rows as usize);

        let sub_w = cols as f32 * 2.0;
        let sub_h = canvas_rows as f32 * 4.0;

        let mut projected: Vec<Option<(f32, f32, f32)>> = Vec::with_capacity(graph.nodes.len());
        for node in &graph.nodes {
            projected.push(camera.project(node.pos, sub_w, sub_h));
        }

        for (idx, node) in graph.nodes.iter().enumerate() {
            if let Some(parent) = node.parent {
                if let (Some(a), Some(b)) = (projected[parent], projected[idx]) {
                    canvas.line(
                        a.0 as i32,
                        a.1 as i32,
                        b.0 as i32,
                        b.1 as i32,
                        Color::DarkGrey,
                    );
                }
            }
        }

        for (idx, node) in graph.nodes.iter().enumerate() {
            if let Some(p) = projected[idx] {
                let color = if idx == *selected {
                    Color::Red
                } else if node.is_dir {
                    depth_color(node.depth)
                } else {
                    category_color(&node.name)
                };
                let radius = if idx == *selected {
                    size_radius(node.is_dir, node.size, node.leaf_count) + 1
                } else {
                    size_radius(node.is_dir, node.size, node.leaf_count)
                };
                canvas.point(p.0 as i32, p.1 as i32, radius, color);
            }
        }

        canvas.render(out, 0)?;

        let sel = &graph.nodes[*selected];
        let kind = if sel.is_dir { "dir" } else { "file" };
        let size_str = if sel.is_dir {
            format!("{} items", sel.leaf_count)
        } else {
            human_size(sel.size)
        };
        use terminal::{Clear, ClearType};
        queue!(
            out,
            cursor::MoveTo(0, canvas_rows),
            Clear(ClearType::CurrentLine),
            crossterm::style::Print(format!(
                "[{}] {}  ({})",
                kind,
                sel.path.display(),
                size_str,
            )),
            cursor::MoveTo(0, canvas_rows + 1),
            Clear(ClearType::CurrentLine),
            crossterm::style::Print(
                "arrows/wasd rotate  +/- zoom  tab/n/p select  enter/o open  space auto-rotate  r reset  q quit"
            ),
            cursor::MoveTo(0, canvas_rows + 2),
            Clear(ClearType::CurrentLine),
            crossterm::style::Print(
                "color: code=green docs=yellow image=pink video=blue audio=orange archive=red exe=bright-red data=cyan | size: bigger dot = bigger file/folder"
            ),
        )?;
        out.flush()?;

        let elapsed = frame_start.elapsed();
        if elapsed < frame_time {
            std::thread::sleep(frame_time - elapsed);
        }
    }
}
