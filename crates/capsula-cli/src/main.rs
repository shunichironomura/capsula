use capsula_core::captured::Captured;
use capsula_core::context::{Context, ContextParams, ContextPhase};
use capsula_cwd_context::CwdContext;
use clap::{Parser, Subcommand};

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
    match cli.command {
        Commands::Capture => {
            let context = CwdContext::default();
            let params = ContextParams {
                phase: ContextPhase::PreRun,
            };
            let captured = context.run(&params)?;
            let json = captured.to_json();
            println!("{}", serde_json::to_string_pretty(&json)?);
        }
    }
    Ok(())
}
