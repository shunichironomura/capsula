mod config;
use crate::config::FileContextFactory;
use capsula_core::captured::Captured;
use capsula_core::context::{Context, ContextFactory, RuntimeParams};
use capsula_core::error::{CoreError, CoreResult};
use glob::glob;
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

pub const KEY: &str = "file";

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum CaptureMode {
    Copy,
    Move,
    None,
}
impl Default for CaptureMode {
    fn default() -> Self {
        CaptureMode::Copy
    }
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum HashAlgorithm {
    Sha256,
    Md5,
    None,
}

impl Default for HashAlgorithm {
    fn default() -> Self {
        HashAlgorithm::Sha256
    }
}

#[derive(Debug)]
pub struct FileContext {
    pub glob: String,
    pub mode: CaptureMode,
    pub hash: HashAlgorithm,
}

#[derive(Debug)]
pub struct FileCapturedPerFile {
    pub path: PathBuf,
    pub copied_path: Option<PathBuf>,
    pub hash: Option<String>,
}

#[derive(Debug)]
pub struct FileCaptured {
    pub files: Vec<FileCapturedPerFile>,
}

impl Captured for FileCaptured {
    fn to_json(&self) -> serde_json::Value {
        serde_json::json!({
            "type": KEY.to_string(),
            "files": self.files.iter().map(|f| {
                serde_json::json!({
                    "path": f.path.to_string_lossy(),
                    "copied_path": f.copied_path.as_ref().map(|p| p.to_string_lossy()),
                    "hash": f.hash,
                })
            }).collect::<Vec<_>>(),
        })
    }
}

impl Context for FileContext {
    type Output = FileCaptured;

    fn run(&self, params: &RuntimeParams) -> CoreResult<Self::Output> {
        glob(&self.glob)
            .unwrap()
            .filter_map(Result::ok)
            .map(|path| capture_file(&path, &params))
            .collect::<Result<Vec<_>, CoreError>>()
            .map(|files| FileCaptured { files })
    }
}

fn capture_file(path: &PathBuf, runtime_params: &RuntimeParams) -> CoreResult<FileCapturedPerFile> {
    // Compute hash if needed
    let hash = Some("dummy_hash".to_string()); // Placeholder for actual hash computation

    // Copy or move file if needed
    let copied_path = Some(path.clone()); // Placeholder for actual file operation

    Ok(FileCapturedPerFile {
        path: path.clone(),
        copied_path,
        hash,
    })
}

pub fn create_factory() -> Box<dyn ContextFactory> {
    Box::new(FileContextFactory)
}
