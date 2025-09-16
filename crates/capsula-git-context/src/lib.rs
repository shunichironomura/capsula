use capsula_core::captured::Captured;
use capsula_core::context::{Context, ContextParams};
use capsula_core::error::CoreResult;
use git2::Repository;
use serde_json::json;
use std::path::PathBuf;

#[derive(Debug, Default)]
pub struct GitContext {
    pub name: String,
    pub working_dir: PathBuf,
    pub allow_dirty: bool,
}

#[derive(Debug)]
pub struct GitCaptured {
    pub name: String,
    pub working_dir: PathBuf,
    pub sha: String, // TODO: Use more suitable type
}

impl Context for GitContext {
    type Output = GitCaptured;

    fn type_name(&self) -> &'static str {
        "GitContext"
    }

    fn run(&self, _params: &ContextParams) -> CoreResult<Self::Output> {
        let repo_path = if self.working_dir.as_os_str().is_empty() {
            std::env::current_dir()?
        } else {
            self.working_dir.clone()
        };

        let repo = Repository::discover(&repo_path)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.message()))?;

        let head = repo.head()
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.message()))?;
        let oid = head.target().ok_or_else(|| {
            std::io::Error::new(std::io::ErrorKind::Other, "Failed to get HEAD target")
        })?;

        if !self.allow_dirty {
            let statuses = repo.statuses(None)
                .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.message()))?;
            if !statuses.is_empty() {
                return Err(std::io::Error::new(
                    std::io::ErrorKind::Other,
                    "Repository has uncommitted changes"
                ).into());
            }
        }

        Ok(GitCaptured {
            name: self.name.clone(),
            working_dir: repo_path,
            sha: oid.to_string(),
        })
    }
}

impl Captured for GitCaptured {
    fn to_json(&self) -> serde_json::Value {
        json!({
            "name": self.name,
            "working_dir": self.working_dir.to_string_lossy(),
            "sha": self.sha
        })
    }
}
