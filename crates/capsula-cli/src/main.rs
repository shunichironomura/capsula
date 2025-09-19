use std::path::PathBuf;

use capsula_config::CapsulaConfig;
use capsula_core::context::{ContextParams, ContextPhase};
use clap::{Parser, Subcommand};
use std::str::FromStr;

#[derive(Parser, Debug)]
#[command(name = "capsula", bin_name = "capsula", version, about = "Capsula CLI")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    Capture,
}

fn create_registry() -> capsula_registry::ContextRegistry {
    // Use the standard registry with all built-in context types
    capsula_registry::standard_registry()
}

fn main() -> anyhow::Result<()> {
    // Create the registry with all available context types
    let registry = create_registry();

    let cli = Cli::parse();
    // TODO: Read from CLI option
    let project_root = PathBuf::from_str(".")?;
    let config_file_path = project_root.join("capsula.toml");
    let config = CapsulaConfig::from_file(&config_file_path)?;
    println!("Config: {:?}", config);

    match cli.command {
        Commands::Capture => {
            // TODO: These are only for testing. Will be loaded from config in the future.
            let params = ContextParams {
                phase: ContextPhase::PreRun,
            };

            let contexts_ok = match params.phase {
                ContextPhase::PreRun => capsula_config::build_pre_phase_contexts(
                    &config.phase.pre,
                    &project_root,
                    &registry,
                )?,
                ContextPhase::PostRun => capsula_config::build_post_phase_contexts(
                    &config.phase.post,
                    &project_root,
                    &registry,
                )?,
            };

            let context_outputs = contexts_ok
                .iter()
                .map(|ctx| {
                    let out = ctx.run_erased(&params)?;
                    Ok(out)
                })
                .collect::<Result<Vec<_>, anyhow::Error>>()?;
            let output_json = context_outputs
                .iter()
                .map(|out| out.to_json())
                .collect::<Vec<_>>();
            println!(
                "Context outputs: {:#}",
                serde_json::to_string_pretty(&output_json)?
            );
        }
    }
    Ok(())
}
