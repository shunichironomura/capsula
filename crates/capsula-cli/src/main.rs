use std::path::PathBuf;

use capsula_config::CapsulaConfig;
use capsula_core::captured::Captured;
use capsula_core::context::{Context, ContextErased, ContextParams, ContextPhase};
use capsula_cwd_context::CwdContext;
use capsula_git_context::GitContext;
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

fn main() -> anyhow::Result<()> {
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

            let context_specs = match params.phase {
                ContextPhase::PreRun => config.phase.pre.contexts,
                ContextPhase::PostRun => config.phase.post.contexts,
            };
            let (contexts_ok, _contexts_err) = context_specs
                .into_iter()
                .map(|spec| spec.build(&project_root))
                .partition::<Vec<_>, _>(Result::is_ok);
            let contexts_ok = contexts_ok
                .into_iter()
                .map(Result::unwrap)
                .collect::<Vec<_>>();

            // let contexts_err = contexts_err
            //     .into_iter()
            //     .map(Result::unwrap_err)
            //     .collect::<Vec<_>>();

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
