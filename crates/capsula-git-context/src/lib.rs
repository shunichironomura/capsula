use capsula_core::captured::Captured;
use capsula_core::context::{Context, ContextErased, ContextFactory, ContextParams};
use capsula_core::error::CoreResult;
use git2::Repository;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::path::{Path, PathBuf};

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

        let head = repo
            .head()
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.message()))?;
        let oid = head.target().ok_or_else(|| {
            std::io::Error::new(std::io::ErrorKind::Other, "Failed to get HEAD target")
        })?;

        if !self.allow_dirty {
            let statuses = repo
                .statuses(None)
                .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e.message()))?;
            if !statuses.is_empty() {
                return Err(std::io::Error::new(
                    std::io::ErrorKind::Other,
                    "Repository has uncommitted changes",
                )
                .into());
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
            "type": "git",
            "name": self.name,
            "working_dir": self.working_dir.to_string_lossy(),
            "sha": self.sha
        })
    }
}

/// Configuration for GitContext
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct GitContextConfig {
    pub path: PathBuf,
    #[serde(default)]
    pub allow_dirty: bool,
}

/// Factory for creating GitContext instances
pub struct GitContextFactory;

impl ContextFactory for GitContextFactory {
    fn key(&self) -> &'static str {
        "git"
    }

    fn create_context(
        &self,
        config: &Value,
        project_root: &Path,
    ) -> CoreResult<Box<dyn ContextErased>> {
        let config: GitContextConfig = serde_json::from_value(config.clone())
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;

        let mut context = GitContext::default();
        context.working_dir = if config.path.is_absolute() {
            config.path
        } else {
            project_root.join(&config.path)
        };
        context.allow_dirty = config.allow_dirty;

        Ok(Box::new(context))
    }
}

/// Create a factory for GitContext
pub fn create_factory() -> Box<dyn ContextFactory> {
    Box::new(GitContextFactory)
}
