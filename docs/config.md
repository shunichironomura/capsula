# Configuration

## `capsula.toml` file

For project-wide settings, prepare a `capsula.toml` file in the root directory of your project. An example of the `capsula.toml` file is as follows:

```toml
[pre-run]
contexts = [
    { type = "CwdContext" },
    { type = "CpuContext" },
    { type = "GitRepositoryContext", name = "capsula", path = ".", path_relative_to_project_root = true },
    { type = "CommandContext", command = "uv lock --locked", cwd = ".", cwd_relative_to_project_root = true },
    { type = "FileContext", path = "pyproject.toml", copy = true, path_relative_to_project_root = true },
    { type = "FileContext", path = "uv.lock", copy = true, path_relative_to_project_root = true },
    { type = "CommandContext", command = "uv export > requirements.txt", cwd = ".", cwd_relative_to_project_root = true },
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

For encapsulating the pre-run, in-run, and post-run capsules for a specific function, you can use the [`@capsula.run()`](reference/capsula/index.md#capsula.run) decorator. You can also use the [`@capsula.context()`](reference/capsula/index.md#capsula.context), [`@capsula.watcher()`](reference/capsula/index.md#capsula.watcher), and [`@capsula.reporter()`](reference/capsula/index.md#capsula.reporter) decorators to add a context, watcher, or reporter that is specific to the function.

The following is an example of a Python script that estimates the value of π using the Monte Carlo method. The `pi.txt` file generated inside the function is encapsulated using the `FileContext` context in the post-run encapsulator.

```python
import random
import capsula

@capsula.run()
# Register a `FileContext` to the post-run encapsulator.
@capsula.context(capsula.FileContext.builder("pi.txt", move=True), mode="post")
def calculate_pi(n_samples: int = 1_000, seed: int = 42) -> None:
    random.seed(seed)
    xs = (random.random() for _ in range(n_samples))
    ys = (random.random() for _ in range(n_samples))
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))
    pi_estimate = (4.0 * inside) / n_samples

    with open("pi.txt", "w") as output_file:
        output_file.write(f"Pi estimate: {pi_estimate}.")

if __name__ == "__main__":
    calculate_pi(n_samples=1_000)
```

## Order of encapsulation

For each encapsulators, the order of encapsulation is as follows:

1. Contexts, watchers, and reporters specified in the `capsula.toml` file, in the order of appearance (from top to bottom).
2. Contexts, watchers, and reporters specified using the `@capsula.context()` and `@capsula.watcher()` decorators, in the order of appearance (from top to bottom).

!!! note
    For watchers, the order of encapsulation here means the order of entering the `watch` context manager of the watcher. The order of exiting the `watch` context manager is the reverse of the order of entering the `watch` context manager.

## `builder` method or `__init__` method?

The reason for using the `builder` method instead of the `__init__` method to create an instance of a context, watcher, or reporter is to use the runtime information, such as the run directory, to create the instance. This is why the configuration specified in the `capsula.toml` file by default uses the `builder` method to create instances of contexts, watchers, and reporters.

The `builder` method returns, instead of an instance of the class, a function that takes the runtime information ([`capsula.CapsuleParams`](reference/capsula/index.md#capsula.CapsuleParams)) as an argument and returns an instance of the class.
