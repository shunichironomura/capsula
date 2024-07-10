# `FunctionContext`

The `FunctionContext` captures the arguments of a function.
It can be created using the `capsula.FunctionContext.builder` method or the `capsula.FunctionContext.__init__` method.

::: capsula.FunctionContext.builder
::: capsula.FunctionContext.__init__

## Configuration example

### Via `capsula.toml`

!!! warning
    Configuring the `FunctionContext` via `capsula.toml` is not recommended because `capsula enc` will fail as there is no target function to capture.

```toml
[pre-run]
contexts = [
  { type = "FunctionContext" },
]
```

### Via `@capsula.context` decorator

```python
import capsula

@capsula.run()
@capsula.context(capsula.FunctionContext.builder(), mode="pre")
def func(arg1, arg2): ...
```

## Output example

The following is an example of the output of the `FunctionContext`, reported by the [`JsonDumpReporter`](../reporters/json_dump.md):

```json
"function": {
  "calculate_pi": {
    "file_path": "examples/simple_decorator.py",
    "first_line_no": 6,
    "bound_args": {
      "n_samples": 1000,
      "seed": 42
    }
  }
}
```
