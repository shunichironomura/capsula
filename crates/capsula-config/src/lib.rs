use capsula_core::error::CoreResult;
use serde::Deserialize;
use std::path::{Path, PathBuf};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ConfigError {
    #[error("Failed to parse TOML: {0}")]
    TomlParse(#[from] toml::de::Error),
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    #[error("Core error: {0}")]
    Core(#[from] capsula_core::error::CoreError),
}

pub type ConfigResult<T> = Result<T, ConfigError>;

#[derive(Deserialize, Debug, Clone)]
pub struct CapsulaConfig {
    pub vault: VaultConfig,
    pub storage: StorageConfig,
    pub phase: PhaseConfig,
}

#[derive(Deserialize, Debug, Clone)]
pub struct VaultConfig {
    pub name: String,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum StorageConfig {
    Filesystem { path: PathBuf },
}

#[derive(Deserialize, Debug, Clone, Default)]
pub struct PhaseConfig {
    #[serde(default)]
    pub pre: PrePhaseConfig,
    #[serde(rename = "in", default)]
    pub in_phase: InPhaseConfig,
    #[serde(default)]
    pub post: PostPhaseConfig,
}

#[derive(Deserialize, Debug, Clone, Default)]
pub struct PrePhaseConfig {
    #[serde(default)]
    pub contexts: Vec<ContextEnvelope>,
}

#[derive(Deserialize, Debug, Clone, Default)]
pub struct InPhaseConfig {
    #[serde(default)]
    pub watchers: Vec<WatcherSpec>,
}

#[derive(Deserialize, Debug, Clone, Default)]
pub struct PostPhaseConfig {
    #[serde(default)]
    pub contexts: Vec<ContextEnvelope>,
}

#[derive(Deserialize, Debug, Clone)]
pub struct ContextEnvelope {
    #[serde(rename = "type")]
    pub ty: String,
    #[serde(flatten)]
    pub rest: serde_json::Value,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum WatcherSpec {
    Time(TimeWatcherSpec),
}

#[derive(Deserialize, Debug, Clone, Default)]
pub struct TimeWatcherSpec {}

impl CapsulaConfig {
    pub fn from_str(content: &str) -> ConfigResult<Self> {
        Ok(toml::from_str(content)?)
    }

    pub fn from_file(path: impl AsRef<std::path::Path>) -> ConfigResult<Self> {
        let content = std::fs::read_to_string(path)?;
        Self::from_str(&content)
    }
}

/// Build contexts from envelopes using a registry
pub fn build_pre_phase_contexts(
    phase: &PrePhaseConfig,
    project_root: &Path,
    registry: &capsula_registry::ContextRegistry,
) -> CoreResult<Vec<Box<dyn capsula_core::context::ContextErased>>> {
    phase
        .contexts
        .iter()
        .map(|envelope| registry.create_context(&envelope.ty, &envelope.rest, project_root))
        .collect()
}

/// Build contexts from envelopes using a registry (for post phase)
pub fn build_post_phase_contexts(
    phase: &PostPhaseConfig,
    project_root: &Path,
    registry: &capsula_registry::ContextRegistry,
) -> CoreResult<Vec<Box<dyn capsula_core::context::ContextErased>>> {
    phase
        .contexts
        .iter()
        .map(|envelope| registry.create_context(&envelope.ty, &envelope.rest, project_root))
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_example_config() {
        let config_str = r#"
[vault]
name = "capsula"

[storage]
type = "filesystem"
path = ".capsula"

[[phase.pre.contexts]]
type = "cwd"

[[phase.pre.contexts]]
type = "git"
path = "."

[[phase.pre.contexts]]
type = "file"
path = "capsula.toml"
copy = true
hash = true

[[phase.pre.contexts]]
type = "file"
path = "Cargo.toml"
hash = true

[[phase.in.watchers]]
type = "time"

[[phase.post.contexts]]
type = "env"
key = "PATH"
"#;

        let config = CapsulaConfig::from_str(config_str).unwrap();

        assert_eq!(config.vault.name, "capsula");

        match &config.storage {
            StorageConfig::Filesystem { path } => {
                assert_eq!(path, &PathBuf::from(".capsula"));
            }
        }

        assert_eq!(config.phase.pre.contexts.len(), 4);
        assert_eq!(config.phase.pre.contexts[0].ty, "cwd");
        assert_eq!(config.phase.pre.contexts[1].ty, "git");
        assert_eq!(config.phase.pre.contexts[2].ty, "file");
        assert_eq!(config.phase.pre.contexts[3].ty, "file");

        assert_eq!(config.phase.in_phase.watchers.len(), 1);
        assert!(matches!(
            &config.phase.in_phase.watchers[0],
            WatcherSpec::Time(_)
        ));

        assert_eq!(config.phase.post.contexts.len(), 1);
        assert_eq!(config.phase.post.contexts[0].ty, "env");
    }
}
