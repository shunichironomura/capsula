use capsula_core::captured::Captured;
use capsula_core::context::{Context, ContextParams};
use capsula_core::error::CoreResult;
use serde_json::json;
use std::path::PathBuf;

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
