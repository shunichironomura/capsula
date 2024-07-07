# `CwdContext`

The [`CwdContext`](../reference/capsula/index.md#capsula.CwdContext) captures the current working directory.
It can be created by `capsula.CwdContext()` with no arguments.

## Configuration example

### Via `capsula.toml`

```toml
[pre-run]
contexts = [
  { type = "CwdContext" },
]
```

### Via `@capsula.context` decorator

```python
import capsula

@capsula.run()
@capsula.context(capsula.CwdContext(), mode="pre")
def func(): ...
```

## Output example

The following is an example of the output of the `CwdContext`, reported by the [`JsonDumpReporter`](../reporters/json_dump.md):

```json
"cwd": "/home/nomura/ghq/github.com/shunichironomura/capsula"
```
