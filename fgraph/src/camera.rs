pub struct Camera {
    pub yaw: f32,
    pub pitch: f32,
    pub distance: f32,
    pub auto_rotate: bool,
    pub focal: f32,
}

impl Camera {
    pub fn new(scene_radius: f32) -> Self {
        Camera {
            yaw: 0.6,
            pitch: 0.4,
            distance: scene_radius * 2.2 + 5.0,
            auto_rotate: true,
            focal: 40.0,
        }
    }

    /// Rotates a world-space point into camera space, then perspective-projects it.
    /// Returns None if the point is behind the camera (would divide by a non-positive z).
    pub fn project(&self, p: [f32; 3], screen_w: f32, screen_h: f32) -> Option<(f32, f32, f32)> {
        let (sy, cy) = self.yaw.sin_cos();
        let (sp, cp) = self.pitch.sin_cos();

        // yaw around Y
        let x1 = p[0] * cy - p[2] * sy;
        let z1 = p[0] * sy + p[2] * cy;
        let y1 = p[1];

        // pitch around X
        let y2 = y1 * cp - z1 * sp;
        let z2 = y1 * sp + z1 * cp;

        // move away from camera
        let z3 = z2 + self.distance;
        if z3 <= 0.5 {
            return None;
        }

        let aspect_correction = 0.5; // terminal cells are ~2x taller than wide
        let sx = screen_w / 2.0 + (x1 / z3) * self.focal;
        let sy_ = screen_h / 2.0 - (y2 / z3) * self.focal * aspect_correction * 2.0;
        Some((sx, sy_, z3))
    }
}
