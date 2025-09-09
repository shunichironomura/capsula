# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Package Management

- `uv sync` - Install dependencies and sync the environment
- `uv lock` - Update the lockfile
- `uv run <command>` - Run commands in the project environment

### Testing

- `uv run pytest` - Run all tests
- `uv run pytest tests/test_specific.py` - Run specific test file
- `uv run pytest -k "test_name"` - Run tests matching pattern
- `uv run pytest --cov` - Run tests with coverage

### Linting and Type Checking

- `uv run ruff check` - Run linting checks
- `uv run ruff format` - Format code
- `uv run mypy .` - Run type checking
- `uv run deptry .` - Check for unused dependencies

### Pre-commit

- `pre-commit run --all-files` - Run all pre-commit hooks

### Documentation

- `uv run mkdocs serve` - Serve documentation locally
- `uv run mkdocs build` - Build documentation

## Architecture Overview

Capsula is a Python package for capturing execution context for reproducibility. The core architecture consists of:

### Core Components

**Encapsulator (`_encapsulator.py`)**

- Central orchestrator that manages the execution lifecycle
- Thread-local context stack for nested execution support
- Handles pre-run, in-run, and post-run phases

**Run (`_run.py`)**

- Represents a single execution session with unique name and directory
- Contains `FuncInfo` for function executions and `CommandInfo` for CLI executions
- Manages execution parameters and lifecycle

**Capsule (`_capsule.py`)**

- Immutable container for captured context data
- Stores both successful captures and failures
- Generic key-value store for different types of context information

### Context System (`_context/`)

- **ContextBase**: Abstract base for all context capture implementations
- **Built-in contexts**: CPU, Platform, Git, Command, File, Function, Environment variables
- Each context encapsulates specific environmental or execution data

### Watcher System (`_watcher/`)

- **WatcherBase**: Abstract base for monitoring execution
- **TimeWatcher**: Tracks execution duration
- **UncaughtExceptionWatcher**: Captures and reports exceptions

### Reporter System (`_reporter/`)

- **ReporterBase**: Abstract base for output generation
- **JsonDumpReporter**: Generates JSON reports of captured data
- **SlackReporter**: Sends notifications to Slack channels

### Configuration

- `capsula.toml` in project root defines default contexts, watchers, and reporters
- Three phases: pre-run (before execution), in-run (during execution), post-run (after execution)
- Uses TOML configuration format with type-based plugin system

### Decorator Interface (`_decorator.py`)

- `@capsula.run()` - Main decorator for function execution capture
- `@capsula.context()` - Add context-specific capture
- `@capsula.watcher()` - Add execution monitoring
- `@capsula.reporter()` - Add custom reporting

### Key Design Patterns

- Plugin architecture for contexts, watchers, and reporters
- Builder pattern for configurable components
- Thread-local storage for execution context
- Immutable data structures for captured information
- Three-phase execution model (pre/in/post-run)

The system automatically creates timestamped directories in `vault/` containing all captured context, making executions fully reproducible.
