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
    pub contexts: Vec<ContextSpec>,
}

#[derive(Deserialize, Debug, Clone, Default)]
pub struct InPhaseConfig {
    #[serde(default)]
    pub watchers: Vec<WatcherSpec>,
}

#[derive(Deserialize, Debug, Clone, Default)]
pub struct PostPhaseConfig {
    #[serde(default)]
    pub contexts: Vec<ContextSpec>,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum ContextSpec {
    Cwd(CwdContextSpec),
    Git(GitContextSpec),
    File(FileContextSpec),
    Env(EnvContextSpec),
}

#[derive(Deserialize, Debug, Clone, Default, serde::Serialize)]
pub struct CwdContextSpec {}

#[derive(Deserialize, Debug, Clone, serde::Serialize)]
pub struct GitContextSpec {
    pub path: PathBuf,
    #[serde(default)]
    pub allow_dirty: bool,
}

#[derive(Deserialize, Debug, Clone, serde::Serialize)]
pub struct FileContextSpec {
    pub path: PathBuf,
    #[serde(default = "default_true")]
    pub copy: bool,
    #[serde(default = "default_true")]
    pub hash: bool,
}

#[derive(Deserialize, Debug, Clone, serde::Serialize)]
pub struct EnvContextSpec {
    pub key: String,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum WatcherSpec {
    Time(TimeWatcherSpec),
}

#[derive(Deserialize, Debug, Clone, Default)]
pub struct TimeWatcherSpec {}

fn default_true() -> bool {
    true
}

impl CapsulaConfig {
    pub fn from_str(content: &str) -> ConfigResult<Self> {
        Ok(toml::from_str(content)?)
    }

    pub fn from_file(path: impl AsRef<std::path::Path>) -> ConfigResult<Self> {
        let content = std::fs::read_to_string(path)?;
        Self::from_str(&content)
    }
}

impl ContextSpec {
    pub fn build(
        self,
        project_root: &Path,
        registry: &capsula_registry::ContextRegistry,
    ) -> CoreResult<Box<dyn capsula_core::context::ContextErased>> {
        // Convert the spec to JSON for the factory
        let config_json = match self {
            ContextSpec::Cwd(spec) => {
                let context_type = "cwd";
                let config = serde_json::to_value(spec)
                    .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
                registry.create_context(context_type, &config, project_root)?
            }
            ContextSpec::Git(spec) => {
                let context_type = "git";
                let config = serde_json::to_value(spec)
                    .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
                registry.create_context(context_type, &config, project_root)?
            }
            ContextSpec::File(spec) => {
                let context_type = "file";
                let config = serde_json::to_value(spec)
                    .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
                // Will fail with "not found" if file context isn't registered
                registry.create_context(context_type, &config, project_root)?
            }
            ContextSpec::Env(spec) => {
                let context_type = "env";
                let config = serde_json::to_value(spec)
                    .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
                // Will fail with "not found" if env context isn't registered
                registry.create_context(context_type, &config, project_root)?
            }
        };
        Ok(config_json)
    }
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
        assert!(matches!(&config.phase.pre.contexts[0], ContextSpec::Cwd(_)));
        assert!(matches!(&config.phase.pre.contexts[1], ContextSpec::Git(_)));
        assert!(matches!(
            &config.phase.pre.contexts[2],
            ContextSpec::File(_)
        ));
        assert!(matches!(
            &config.phase.pre.contexts[3],
            ContextSpec::File(_)
        ));

        assert_eq!(config.phase.in_phase.watchers.len(), 1);
        assert!(matches!(
            &config.phase.in_phase.watchers[0],
            WatcherSpec::Time(_)
        ));

        assert_eq!(config.phase.post.contexts.len(), 1);
        assert!(matches!(
            &config.phase.post.contexts[0],
            ContextSpec::Env(_)
        ));
    }
}
