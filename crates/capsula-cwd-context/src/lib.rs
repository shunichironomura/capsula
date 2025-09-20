mod config;

use crate::config::CwdContextFactory;
use capsula_core::captured::Captured;
use capsula_core::context::{Context, ContextFactory, RuntimeParams};
use capsula_core::error::CoreResult;
use serde_json::json;
use std::path::PathBuf;

pub const KEY: &str = "cwd";

#[derive(Debug, Default)]
pub struct CwdContext;

#[derive(Debug)]
pub struct CwdCaptured {
    pub cwd_abs: PathBuf,
}

impl Context for CwdContext {
    type Output = CwdCaptured;

    fn run(&self, _params: &RuntimeParams) -> CoreResult<Self::Output> {
        let cwd_abs = std::env::current_dir()?;
        Ok(CwdCaptured { cwd_abs })
    }
}

impl Captured for CwdCaptured {
    fn to_json(&self) -> serde_json::Value {
        json!({
            "type": KEY.to_string(),
            "cwd": self.cwd_abs.to_string_lossy(),
        })
    }
}

/// Create a factory for CwdContext
pub fn create_factory() -> Box<dyn ContextFactory> {
    Box::new(CwdContextFactory)
}
