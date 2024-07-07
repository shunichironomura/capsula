# `UncaughtExceptionWatcher`

The [`UncaughtExceptionWatcher`](../reference/capsula/index.md#capsula.UncaughtExceptionWatcher) monitors uncaught exceptions in the command/function.
It can be created using the `capsula.UncaughtExceptionWatcher.__init__` method.

::: capsula.UncaughtExceptionWatcher.__init__

## Configuration example

### Via `capsula.toml`

```toml
[in-run]
watchers = [
  { type = "UncaughtExceptionWatcher" },
]
```

### Via `@capsula.watcher` decorator

```python
import capsula

@capsula.run()
@capsula.watcher(capsula.UncaughtExceptionWatcher("exception"))
def func(): ...
```

## Output example

The following is an example of the output of the `UncaughtExceptionWatcher`, reported by the [`JsonDumpReporter`](../reporters/json_dump.md):

```json
"exception": {
  "exception": {
    "exc_type": null,
    "exc_value": null,
    "traceback": null
  }
}
```

If an exception is caught, the following is an example of the output:

```json
"exception": {
  "exception": {
    "exc_type": "ZeroDivisionError",
    "exc_value": "float division by zero",
    "traceback": "  File \"/home/nomura/ghq/github.com/shunichironomura/capsula/capsula/_run.py\", line 288, in __call__\n    result = self._func(*args, **kwargs)\n  File \"examples/simple_decorator.py\", line 21, in calculate_pi\n    x = 10.0 / 0.0\n"
  }
}
```
