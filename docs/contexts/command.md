# `CommandContext`

The [`CommandContext`](../../reference/capsula/#capsula.CommandContext) captures the output of shell commands.
It can be created using the `capsula.CommandContext.builder` method or the `capsula.CommandContext.__init__` method.

::: capsula.CommandContext.builder
::: capsula.CommandContext.__init__

## Configuration example

### Via `capsula.toml`

```toml
[pre-run]
contexts = [
  { type = "CommandContext", command = "poetry check --lock", cwd = ".", cwd_relative_to_project_root = true },
]
```

### Via `@capsula.context` decorator

```python
import capsula
PROJECT_ROOT = capsula.search_for_project_root(__file__)

@capsula.run()
@capsula.context(capsula.CommandContext("poetry check --lock", cwd=PROJECT_ROOT), mode="pre")
def func(): ...
```

## Output example

The following is an example of the output of the `CommandContext`, reported by the [`JsonDumpReporter`](../reporters/json_dump.md):

```json
"poetry check --lock": {
  "command": "poetry check --lock",
  "cwd": "/home/nomura/ghq/github.com/shunichironomura/capsula",
  "returncode": 0,
  "stdout": "All set!\n",
  "stderr": ""
}
```
