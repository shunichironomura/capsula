mod config;
mod hash;

use crate::config::FileContextFactory;
use crate::hash::file_digest_sha256;
use capsula_core::captured::Captured;
use capsula_core::context::{Context, ContextFactory, RuntimeParams};
use capsula_core::error::{CoreError, CoreResult};
use globwalk::GlobWalkerBuilder;
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

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
    // Md5,
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
        GlobWalkerBuilder::from_patterns(&params.project_root, &[&self.glob])
            .max_depth(1)
            .build()
            .map_err(|e| CoreError::from(std::io::Error::new(std::io::ErrorKind::Other, e)))?
            .filter_map(Result::ok)
            .map(|entry| self.capture_file(entry.path(), &params))
            .collect::<Result<Vec<_>, CoreError>>()
            .map(|files| FileCaptured { files })
    }
}

impl FileContext {
    fn capture_file(
        &self,
        path: &Path,
        runtime_params: &RuntimeParams,
    ) -> CoreResult<FileCapturedPerFile> {
        // Compute hash if needed
        let hash = match self.hash {
            HashAlgorithm::Sha256 => Some(format!("sha256:{}", file_digest_sha256(path)?)),
            HashAlgorithm::None => None,
        };

        // Copy or move file if needed
        let copied_path = match self.mode {
            CaptureMode::Copy | CaptureMode::Move => {
                let run_dir = runtime_params.run_dir.as_ref().ok_or_else(|| {
                    CoreError::from(std::io::Error::new(
                        std::io::ErrorKind::InvalidInput,
                        "run_dir is required for Copy or Move mode",
                    ))
                })?;
                let file_name = path
                    .file_name()
                    .ok_or_else(|| {
                        CoreError::from(std::io::Error::new(
                            std::io::ErrorKind::InvalidInput,
                            "Invalid file name",
                        ))
                    })?
                    .to_os_string();
                let dest_path = run_dir.join(file_name);
                match self.mode {
                    CaptureMode::Copy => {
                        std::fs::copy(path, &dest_path)?;
                    }
                    CaptureMode::Move => {
                        std::fs::rename(path, &dest_path)?;
                    }
                    _ => unreachable!(),
                }
                Some(dest_path)
            }
            CaptureMode::None => None,
        };

        Ok(FileCapturedPerFile {
            path: path.to_path_buf(),
            copied_path,
            hash,
        })
    }
}

pub fn create_factory() -> Box<dyn ContextFactory> {
    Box::new(FileContextFactory)
}
