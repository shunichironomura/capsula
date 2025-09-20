use crate::{GitContext, KEY};
use capsula_core::context::ContextErased;
use capsula_core::context::ContextFactory;
use capsula_core::error::CoreResult;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::path::{Path, PathBuf};

/// Configuration for GitContext
#[derive(Debug, Clone, Deserialize, Serialize)]
struct GitContextConfig {
    pub name: String,
    pub path: PathBuf,
    #[serde(default)]
    pub allow_dirty: bool,
}

/// Factory for creating GitContext instances
pub struct GitContextFactory;

impl ContextFactory for GitContextFactory {
    fn key(&self) -> &'static str {
        KEY
    }

    fn create_context(
        &self,
        config: &Value,
        project_root: &Path,
    ) -> CoreResult<Box<dyn ContextErased>> {
        let config: GitContextConfig = serde_json::from_value(config.clone())
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;

        let working_dir = if config.path.is_absolute() {
            config.path
        } else {
            project_root.join(&config.path).canonicalize()?
        };

        let context = GitContext {
            name: config.name,
            working_dir,
            allow_dirty: config.allow_dirty,
        };

        Ok(Box::new(context))
    }
}
