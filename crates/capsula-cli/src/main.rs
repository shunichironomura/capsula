use capsula_core::captured::Captured;
use capsula_core::context::{Context, ContextParams, ContextPhase};
use capsula_cwd_context::CwdContext;
use capsula_git_context::GitContext;
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
            // TODO: These are only for testing. Will be loaded from config in the future.
            let params = ContextParams {
                phase: ContextPhase::PreRun,
            };

            // Capture current working directory
            let cwd_context = CwdContext::default();
            let cwd_captured = cwd_context.run(&params)?;
            let cwd_json = cwd_captured.to_json();

            // Capture git repository info (auto-detect from current directory)
            let git_context = GitContext {
                name: "main_repo".to_string(),
                working_dir: std::env::current_dir()?, // Use current directory, git2 will find the repo
                allow_dirty: true,                     // Allow testing with uncommitted changes
            };
            let git_captured = git_context.run(&params)?;
            let git_json = git_captured.to_json();

            // Combine and print results
            let combined = serde_json::json!({
                "cwd": cwd_json,
                "git": git_json,
            });
            println!("{}", serde_json::to_string_pretty(&combined)?);
        }
    }
    Ok(())
}
