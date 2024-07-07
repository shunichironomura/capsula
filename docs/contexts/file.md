# `FileContext`

The [`FileContext`](../reference/capsula/index.md#capsula.FileContext) captures the file information.
It can be created using the `capsula.FileContext.builder` method (recommended) or the `capsula.FileContext.__init__` method.

::: capsula.FileContext.builder
::: capsula.FileContext.__init__

## Configuration example

### Via `capsula.toml`

```toml
[pre-run]
contexts = [
  { type = "FileContext", path = "pyproject.toml", copy = true, path_relative_to_project_root = true },
]
```

### Via `@capsula.context` decorator

`@capsula.context` decorator is useful to move the output file to the run directory after the function execution.

```python
import capsula
PROJECT_ROOT = capsula.search_for_project_root(__file__)

@capsula.run()
@capsula.context(capsula.FileContext.builder(PROJECT_ROOT / "pyproject.toml", copy=True), mode="pre")
@capsula.context(capsula.FileContext.builder("output.txt", move=True), mode="post")
def func():
  with open("output.txt", "w") as output_file:
    output_file.write("Hello, world!")
```

## Output example

The following is an example of the output of the `FileContext`, reported by the [`JsonDumpReporter`](../reporters/json_dump.md):

```json
"file": {
  "/home/nomura/ghq/github.com/shunichironomura/capsula/pyproject.toml": {
    "copied_to": [
      "/home/nomura/ghq/github.com/shunichironomura/capsula/vault/20240708_024409_coj0/pyproject.toml"
    ],
    "moved_to": null,
    "hash": {
      "algorithm": "sha256",
      "digest": "1ecab310035eea9c07fad2a8b22a16f999cd4d8c59fa1732c088f754af548ad9"
    }
  },
}
```
