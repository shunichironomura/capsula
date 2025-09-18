use capsula_core::error::CoreResult;
use serde::Deserialize;
use std::path::PathBuf;
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

#[derive(Deserialize, Debug, Clone, Default)]
pub struct CwdContextSpec {}

#[derive(Deserialize, Debug, Clone)]
pub struct GitContextSpec {
    #[serde(default = "default_current_dir")]
    pub path: PathBuf,
    #[serde(default)]
    pub allow_dirty: bool,
}

#[derive(Deserialize, Debug, Clone)]
pub struct FileContextSpec {
    pub path: PathBuf,
    #[serde(default)]
    pub copy: bool,
    #[serde(default)]
    pub hash: bool,
}

#[derive(Deserialize, Debug, Clone)]
pub struct EnvContextSpec {
    pub key: String,
}

#[derive(Deserialize, Debug, Clone)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum WatcherSpec {
    Time(TimeWatcherSpec),
}

#[derive(Deserialize, Debug, Clone, Default)]
pub struct TimeWatcherSpec {
    #[serde(default)]
    pub interval_ms: Option<u64>,
}

fn default_current_dir() -> PathBuf {
    PathBuf::from(".")
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
    pub fn build(self) -> CoreResult<Box<dyn capsula_core::context::ContextErased>> {
        match self {
            ContextSpec::Cwd(_spec) => Ok(Box::new(capsula_cwd_context::CwdContext::default())),
            ContextSpec::Git(spec) => {
                let mut context = capsula_git_context::GitContext::default();
                context.working_dir = spec.path;
                context.allow_dirty = spec.allow_dirty;
                Ok(Box::new(context))
            }
            ContextSpec::File(_spec) => Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                "File context not yet implemented",
            )
            .into()),
            ContextSpec::Env(_spec) => Err(std::io::Error::new(
                std::io::ErrorKind::Other,
                "Env context not yet implemented",
            )
            .into()),
        }
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

    #[test]
    fn test_build_contexts() {
        let cwd_spec = ContextSpec::Cwd(CwdContextSpec::default());
        let cwd_context = cwd_spec.build().unwrap();
        assert_eq!(cwd_context.type_name(), "CwdContext");

        let git_spec = ContextSpec::Git(GitContextSpec {
            path: PathBuf::from("."),
            allow_dirty: true,
        });
        let git_context = git_spec.build().unwrap();
        assert_eq!(git_context.type_name(), "GitContext");
    }
}
