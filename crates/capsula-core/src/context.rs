use crate::error::{CoreError, CoreResult};
use serde_json::Value;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ContextPhase {
    PreRun,
    PostRun,
}

#[derive(Debug, Clone)]
pub struct ContextParams {
    pub phase: ContextPhase,
}

pub trait Context {
    type Output: super::captured::Captured;
    fn type_name(&self) -> &'static str;
    fn run(&self, params: &ContextParams) -> CoreResult<Self::Output>;
}

/// Engine-facing trait (object-safe, heterogenous)
pub trait ContextErased: Send + Sync {
    fn type_name(&self) -> &'static str;
    fn run_erased(
        &self,
        parmas: &ContextParams,
    ) -> Result<Box<dyn super::captured::Captured>, CoreError>;
}

impl<T> ContextErased for T
where
    T: Context + Send + Sync + 'static,
{
    fn type_name(&self) -> &'static str {
        <T as Context>::type_name(self)
    }
    fn run_erased(
        &self,
        params: &ContextParams,
    ) -> Result<Box<dyn super::captured::Captured>, CoreError> {
        let out = <T as Context>::run(self, params)?;
        Ok(Box::new(out))
    }
}

/// Factory trait for creating contexts from configuration
pub trait ContextFactory: Send + Sync {
    /// The type key this factory handles (e.g., "cwd", "git", "file")
    fn key(&self) -> &'static str;

    /// Create a context instance from JSON configuration
    fn create_context(
        &self,
        config: &Value,
        project_root: &std::path::Path,
    ) -> CoreResult<Box<dyn ContextErased>>;
}
