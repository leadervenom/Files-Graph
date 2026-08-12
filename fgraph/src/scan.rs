use std::path::{Path, PathBuf};
use walkdir::WalkDir;

pub struct Node {
    pub name: String,
    pub path: PathBuf,
    pub is_dir: bool,
    pub size: u64,
    pub depth: u32,
    pub parent: Option<usize>,
    pub children: Vec<usize>,
    pub leaf_count: u32,
    pub pos: [f32; 3],
}

pub struct Graph {
    pub nodes: Vec<Node>,
    pub root: usize,
}

/// Scans `root_path` up to `max_depth` levels deep and builds a parent/child graph.
/// Depth is capped to keep the scan and layout fast on large trees (e.g. a whole user profile).
pub fn scan(root_path: &Path, max_depth: u32, max_entries: usize) -> Graph {
    let mut nodes: Vec<Node> = Vec::new();

    let root_name = root_path
        .file_name()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_else(|| root_path.to_string_lossy().to_string());

    nodes.push(Node {
        name: root_name,
        path: root_path.to_path_buf(),
        is_dir: true,
        size: 0,
        depth: 0,
        parent: None,
        children: Vec::new(),
        leaf_count: 0,
        pos: [0.0, 0.0, 0.0],
    });

    // path -> index, so we can attach children to the right parent as WalkDir streams entries.
    let mut index_of: std::collections::HashMap<PathBuf, usize> = std::collections::HashMap::new();
    index_of.insert(root_path.to_path_buf(), 0);

    let walker = WalkDir::new(root_path)
        .max_depth(max_depth as usize)
        .into_iter()
        .filter_map(|e| e.ok());

    for entry in walker {
        if nodes.len() >= max_entries {
            break;
        }
        let path = entry.path();
        if path == root_path {
            continue;
        }
        let parent_path = match path.parent() {
            Some(p) => p.to_path_buf(),
            None => continue,
        };
        let parent_idx = match index_of.get(&parent_path) {
            Some(i) => *i,
            None => continue, // parent was skipped (e.g. permission denied) -> skip child too
        };

        let is_dir = entry.file_type().is_dir();
        let size = if is_dir {
            0
        } else {
            entry.metadata().map(|m| m.len()).unwrap_or(0)
        };
        let depth = nodes[parent_idx].depth + 1;
        let name = entry.file_name().to_string_lossy().to_string();

        let idx = nodes.len();
        nodes.push(Node {
            name,
            path: path.to_path_buf(),
            is_dir,
            size,
            depth,
            parent: Some(parent_idx),
            children: Vec::new(),
            leaf_count: 0,
            pos: [0.0, 0.0, 0.0],
        });
        nodes[parent_idx].children.push(idx);
        if is_dir {
            index_of.insert(path.to_path_buf(), idx);
        }
    }

    compute_leaf_counts(&mut nodes, 0);

    Graph { nodes, root: 0 }
}

fn compute_leaf_counts(nodes: &mut [Node], idx: usize) -> u32 {
    let children = nodes[idx].children.clone();
    if children.is_empty() {
        nodes[idx].leaf_count = 1;
        return 1;
    }
    let mut total = 0;
    for c in children {
        total += compute_leaf_counts(nodes, c);
    }
    nodes[idx].leaf_count = total;
    total
}
