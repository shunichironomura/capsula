use capsula_core::context::{ContextErased, ContextFactory};
use capsula_core::error::{CoreError, CoreResult};
use serde_json::Value;
use std::collections::HashMap;
use std::path::Path;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum RegistryError {
    #[error("Context type '{0}' not found in registry")]
    ContextTypeNotFound(String),
    #[error("Context type '{0}' already registered")]
    AlreadyRegistered(String),
}

impl From<RegistryError> for CoreError {
    fn from(err: RegistryError) -> Self {
        CoreError::from(std::io::Error::new(std::io::ErrorKind::Other, err))
    }
}

/// Context factory registry
pub struct ContextRegistry {
    factories: HashMap<String, Box<dyn ContextFactory>>,
}

impl ContextRegistry {
    /// Create a new empty registry
    pub fn new() -> Self {
        Self {
            factories: HashMap::new(),
        }
    }

    /// Register a context factory
    pub fn register(&mut self, factory: Box<dyn ContextFactory>) -> Result<(), RegistryError> {
        let context_type = factory.context_type().to_string();
        if self.factories.contains_key(&context_type) {
            return Err(RegistryError::AlreadyRegistered(context_type));
        }

        self.factories.insert(context_type, factory);
        Ok(())
    }

    /// Create a context from type name and configuration
    pub fn create_context(
        &self,
        context_type: &str,
        config: &Value,
        project_root: &Path,
    ) -> CoreResult<Box<dyn ContextErased>> {
        let factory = self
            .factories
            .get(context_type)
            .ok_or_else(|| RegistryError::ContextTypeNotFound(context_type.to_string()))?;

        factory.create_context(config, project_root)
    }

    /// Get list of registered context types
    pub fn registered_types(&self) -> Vec<String> {
        self.factories.keys().cloned().collect()
    }
}

impl Default for ContextRegistry {
    fn default() -> Self {
        Self::new()
    }
}

/// Builder for setting up a registry with standard context types
pub struct RegistryBuilder {
    registry: ContextRegistry,
}

impl RegistryBuilder {
    pub fn new() -> Self {
        Self {
            registry: ContextRegistry::new(),
        }
    }

    pub fn with_factory(mut self, factory: Box<dyn ContextFactory>) -> Result<Self, RegistryError> {
        self.registry.register(factory)?;
        Ok(self)
    }

    pub fn build(self) -> ContextRegistry {
        self.registry
    }
}

impl Default for RegistryBuilder {
    fn default() -> Self {
        Self::new()
    }
}
