use chrono::{DateTime, Utc};
use serde::ser::SerializeStruct;
use serde::{Deserialize, Serialize, Serializer};
use std::io::{self, Read, Write};
use std::process::{Command, ExitStatus, Stdio};
use std::thread;
use std::time::{Duration, Instant};
use ulid::Ulid;

#[derive(Debug, Clone, Deserialize)]
pub struct Run {
    pub id: Ulid,
    pub name: String,
    pub command: Vec<String>,
}

impl Serialize for Run {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: Serializer,
    {
        let mut state = serializer.serialize_struct("Run", 4)?;
        state.serialize_field("id", &self.id)?;
        state.serialize_field("name", &self.name)?;
        state.serialize_field("command", &self.command)?;
        state.serialize_field("timestamp", &self.timestamp().to_rfc3339())?;
        state.end()
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunOutput {
    pub exit_code: i32,
    pub stdout: String,
    pub stderr: String,
    pub duration: Duration,
}

fn exit_code_from_status(status: ExitStatus) -> i32 {
    match status.code() {
        Some(c) => c,
        None => {
            // On Unix, process may be terminated by a signal.
            #[cfg(unix)]
            {
                use std::os::unix::process::ExitStatusExt;
                status.signal().map(|s| 128 + s).unwrap_or(1)
            }
            #[cfg(not(unix))]
            {
                1
            }
        }
    }
}

impl Run {
    pub fn timestamp(&self) -> DateTime<Utc> {
        // Calculate start time from ULID timestamp
        let dt: DateTime<Utc> = self.id.datetime().into();
        dt
    }

    pub fn run_dir(&self, vault_dir: impl AsRef<std::path::Path>) -> std::path::PathBuf {
        let timestamp = self.timestamp();
        let date_str = timestamp.format("%Y-%m-%d").to_string();
        let time_str = timestamp.format("%H%M%S").to_string();

        // Prefix the run directory with time because
        // folders are sorted in natural order, not in lexicographical order,
        // For example, on macOS Finder, the order is:
        // 1. 01K5K478KNQ2ZXZG68MWM1Z9X6
        // 2. 01K5K4571FGKBFTTRJCG1J3DCZ
        // which is not the correct chronological order.
        // By adding time prefix, it will be sorted correctly.
        let run_dir_name = format!("{}-{}--{}", time_str, self.name, self.id.to_string());
        vault_dir.as_ref().join(date_str).join(&run_dir_name)
    }

    pub fn setup_run_dir(
        &self,
        vault_dir: impl AsRef<std::path::Path>,
    ) -> std::io::Result<std::path::PathBuf> {
        let run_dir = self.run_dir(&vault_dir);
        std::fs::create_dir_all(&run_dir)?;
        Ok(run_dir)
    }

    pub fn exec(&self) -> std::io::Result<RunOutput> {
        if self.command.is_empty() {
            return Err(io::Error::new(io::ErrorKind::InvalidInput, "empty command"));
        }
        let program = &self.command[0];
        let args: Vec<&str> = self.command[1..].iter().map(|s| s.as_str()).collect();

        let start = Instant::now();

        let mut child = Command::new(program)
            .args(&args)
            .env("CAPSULA_RUN_ID", self.id.to_string())
            .env("CAPSULA_RUN_NAME", &self.name)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()?;

        let mut child_stdout = child.stdout.take().expect("piped stdout");
        let mut child_stderr = child.stderr.take().expect("piped stderr");

        let t_out = thread::spawn(move || -> io::Result<Vec<u8>> {
            let mut cap = Vec::with_capacity(8 * 1024);
            let mut buf = [0u8; 8192];
            let mut console = io::stdout().lock();

            loop {
                let n = child_stdout.read(&mut buf)?;
                if n == 0 {
                    break;
                }
                console.write_all(&buf[..n])?;
                cap.extend_from_slice(&buf[..n]);
            }
            console.flush()?;
            Ok(cap)
        });

        let t_err = thread::spawn(move || -> io::Result<Vec<u8>> {
            let mut cap = Vec::with_capacity(8 * 1024);
            let mut buf = [0u8; 8192];
            let mut console = io::stderr().lock();

            loop {
                let n = child_stderr.read(&mut buf)?;
                if n == 0 {
                    break;
                }
                console.write_all(&buf[..n])?;
                cap.extend_from_slice(&buf[..n]);
            }
            console.flush()?;
            Ok(cap)
        });

        let status = child.wait()?;
        let duration = start.elapsed();
        let cap_out = t_out.join().unwrap()?;
        let cap_err = t_err.join().unwrap()?;

        let exit_code = exit_code_from_status(status);

        Ok(RunOutput {
            exit_code,
            stdout: String::from_utf8_lossy(&cap_out).to_string(),
            stderr: String::from_utf8_lossy(&cap_err).to_string(),
            duration,
        })
    }
}
