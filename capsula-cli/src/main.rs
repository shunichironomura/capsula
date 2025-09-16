use clap::{Parser, Subcommand};

#[derive(Parser, Debug)]
#[command(name = "capsula", bin_name = "capsula", version, about = "Capsula CLI")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    Capture {
        #[arg(short, long = "context")]
        contexts: Vec<String>,

        #[arg(short, long, default_value = "json")]
        format: String,
    },
}

fn main() -> anyhow::Result<()> {
    let cli = Cli::parse();
    match cli.command {
        Commands::Capture { contexts, format } => {
            println!("Contexts to be captured: {:?}", contexts);
            println!("Output format: {:?}", format);
        }
    }
    Ok(())
}
