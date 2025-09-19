use capsula_core::captured::Captured;
use capsula_core::context::{Context, ContextErased, ContextFactory, ContextParams};
use capsula_core::error::CoreResult;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use std::path::{Path, PathBuf};

#[derive(Debug, Default)]
pub struct CwdContext;

#[derive(Debug)]
pub struct CwdCaptured {
    pub cwd_abs: PathBuf,
}

impl Context for CwdContext {
    type Output = CwdCaptured;

    fn type_name(&self) -> &'static str {
        "CwdContext"
    }
    fn run(&self, _params: &ContextParams) -> CoreResult<Self::Output> {
        let cwd_abs = std::env::current_dir()?;
        Ok(CwdCaptured { cwd_abs })
    }
}

impl Captured for CwdCaptured {
    fn to_json(&self) -> serde_json::Value {
        json!({
            "type": "cwd",
            "cwd": self.cwd_abs.to_string_lossy(),
        })
    }
}

/// Configuration for CwdContext
#[derive(Debug, Clone, Default, Deserialize, Serialize)]
pub struct CwdContextConfig {}

/// Factory for creating CwdContext instances
pub struct CwdContextFactory;

impl ContextFactory for CwdContextFactory {
    fn key(&self) -> &'static str {
        "cwd"
    }

    fn create_context(
        &self,
        _config: &Value,
        _project_root: &Path,
    ) -> CoreResult<Box<dyn ContextErased>> {
        // Config could be deserialized if needed:
        // let _config: CwdContextConfig = serde_json::from_value(config.clone())?;
        Ok(Box::new(CwdContext::default()))
    }
}

/// Create a factory for CwdContext
pub fn create_factory() -> Box<dyn ContextFactory> {
    Box::new(CwdContextFactory)
}
