use crate::scan::Graph;
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

const RADIUS_PER_DEPTH: f32 = 6.0;

/// Radial tree layout, projected onto a sphere-ish 3D shape:
/// each node gets an angular slice proportional to its subtree size (leaf_count),
/// radius grows with depth, and elevation is nudged per-node (stable hash of the
/// path) so the tree reads as a 3D dome/bloom instead of a flat disk when rotated.
pub fn layout(graph: &mut Graph) {
    assign(graph, graph.root, 0.0, std::f32::consts::TAU, 0.0);
}

fn stable_unit(path: &std::path::Path) -> f32 {
    let mut hasher = DefaultHasher::new();
    path.hash(&mut hasher);
    (hasher.finish() % 10_000) as f32 / 10_000.0
}

fn assign(graph: &mut Graph, idx: usize, angle_start: f32, angle_end: f32, elevation_bias: f32) {
    let depth = graph.nodes[idx].depth;
    let angle_mid = (angle_start + angle_end) * 0.5;
    let radius = depth as f32 * RADIUS_PER_DEPTH;

    let jitter = (stable_unit(&graph.nodes[idx].path) - 0.5) * 0.6;
    let elevation = elevation_bias + jitter;
    let polar = std::f32::consts::FRAC_PI_2 - elevation.clamp(-1.4, 1.4);

    let x = radius * polar.sin() * angle_mid.cos();
    let y = radius * polar.cos();
    let z = radius * polar.sin() * angle_mid.sin();
    graph.nodes[idx].pos = [x, y, z];

    let children = graph.nodes[idx].children.clone();
    if children.is_empty() {
        return;
    }
    let total_leaves: f32 = children
        .iter()
        .map(|c| graph.nodes[*c].leaf_count as f32)
        .sum();
    let mut cursor = angle_start;
    let span = angle_end - angle_start;
    for c in children {
        let share = graph.nodes[c].leaf_count as f32 / total_leaves.max(1.0);
        let child_start = cursor;
        let child_end = cursor + span * share;
        let child_bias = elevation_bias + (stable_unit(&graph.nodes[c].path) - 0.5) * 0.5;
        assign(graph, c, child_start, child_end, child_bias);
        cursor = child_end;
    }
}
