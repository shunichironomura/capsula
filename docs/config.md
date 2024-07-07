# Configuration

## `capsula.toml` file

For project-wide settings, prepare a `capsula.toml` file in the root directory of your project. An example of the `capsula.toml` file is as follows:

```toml
[pre-run]
contexts = [
    { type = "CwdContext" },
    { type = "CpuContext" },
    { type = "GitRepositoryContext", name = "capsula", path = ".", path_relative_to_project_root = true },
    { type = "CommandContext", command = "poetry check --lock", cwd = ".", cwd_relative_to_project_root = true },
    { type = "FileContext", path = "pyproject.toml", copy = true, path_relative_to_project_root = true },
    { type = "FileContext", path = "poetry.lock", copy = true, path_relative_to_project_root = true },
    { type = "CommandContext", command = "pip freeze --exclude-editable > requirements.txt", cwd = ".", cwd_relative_to_project_root = true },
    { type = "FileContext", path = "requirements.txt", move = true, path_relative_to_project_root = true },
]
reporters = [{ type = "JsonDumpReporter" }]

[in-run]
watchers = [{ type = "UncaughtExceptionWatcher" }, { type = "TimeWatcher" }]
reporters = [{ type = "JsonDumpReporter" }]

[post-run]
reporters = [{ type = "JsonDumpReporter" }]
```

This configuration file specifies the contexts, watchers, and reporters to be used in the pre-run, in-run, and post-run encapsulators. The `JsonDumpReporter` is used to dump the captured contexts into JSON files.

For each context, watcher, or reporter, the `type` field specifies the class name of the context, watcher, or reporter. The other fields are used as the keyword arguments to the `builder` method of the class to create an instance of the class. If the class does not implement the `builder` method, the `__init__` method is used instead.

## Decorators

For encapsulating the pre-run, in-run, and post-run capsules for a specific function, you can use the `@capsula.run()` decorator. You can also use the `@capsula.context()`, `@capsula.watcher()`, and `@capsula.reporter()` decorators to add a context, watcher, or reporter respectively to the function.

The following is an example of a Python script that estimates the value of π using the Monte Carlo method:

```python
import random
import capsula

@capsula.run()
# Register a `FileContext` to the post-run encapsulator.
@capsula.context(capsula.FileContext.default("pi.txt", move=True), mode="post")
def calculate_pi(n_samples: int = 1_000, seed: int = 42) -> None:
    random.seed(seed)
    xs = (random.random() for _ in range(n_samples))
    ys = (random.random() for _ in range(n_samples))
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))
    pi_estimate = (4.0 * inside) / n_samples

    # You can record values to the capsule using the `record` method.
    capsula.record("pi_estimate", pi_estimate)
    # You can access the current run name using the `current_run_name` function.
    print(f"Run name: {capsula.current_run_name()}")

    with open("pi.txt", "w") as output_file:
        output_file.write(f"Pi estimate: {pi_estimate}.")

if __name__ == "__main__":
    calculate_pi(n_samples=1_000)
```

## Order of encapsulation

For each encapsulators, the order of encapsulation is as follows:

1. Contexts, watchers, and reporters specified in the `capsula.toml` file, in the order of appearance (from top to bottom).
2. Contexts, watchers, and reporters specified using the `@capsula.context()` and `@capsula.watcher()` decorators, in the order of appearance (from top to bottom).
