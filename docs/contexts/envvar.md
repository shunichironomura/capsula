# `EnvVarContext`

The [`EnvVarContext`](../reference/capsula/index.md#capsula.EnvVarContext) captures an environment variable.
It can be created using the `capsula.EnvVarContext.__init__` method.

::: capsula.EnvVarContext.__init__

## Configuration example

### Via `capsula.toml`

```toml
[pre-run]
contexts = [
  { type = "EnvVarContext", name = "HOME" },
]
```

### Via `@capsula.context` decorator

```python
import capsula

@capsula.run()
@capsula.context(capsula.EnvVarContext("HOME"), mode="pre")
def func(): ...
```

## Output example

The following is an example of the output of the `EnvVarContext`, reported by the [`JsonDumpReporter`](../reporters/json_dump.md):

```json
"env": {
  "HOME": "/home/nomura"
}
```
