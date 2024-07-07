# `GitRepositoryContext`

The `GitRepositoryContext` captures the information of a Git repository.
It can be created using the `capsula.GitRepositoryContext.builder` method or the `capsula.GitRepositoryContext.__init__` method.

::: capsula.GitRepositoryContext.builder
::: capsula.GitRepositoryContext.__init__

## Configuration example

### Via `capsula.toml`

```toml
[pre-run]
contexts = [
  { type = "GitRepositoryContext", name = "capsula", path = ".", path_relative_to_project_root = true },
]
```

### Via `@capsula.context` decorator

```python
import capsula

@capsula.run()
@capsula.context(capsula.GitRepositoryContext.builder("capsula"), mode="pre")
def func(): ...
```

## Output example

The following is an example of the output of the `GitRepositoryContext`, reported by the [`JsonDumpReporter`](../reporters/json_dump.md):

```json
"git": {
  "capsula": {
    "working_dir": "/home/nomura/ghq/github.com/shunichironomura/capsula",
    "sha": "2fa930db2b9c00c467b4627e7d1c7dfb06d41279",
    "remotes": {
      "origin": "ssh://git@github.com/shunichironomura/capsula.git"
    },
    "branch": "improve-docs-index",
    "is_dirty": true,
    "diff_file": "/home/nomura/ghq/github.com/shunichironomura/capsula/vault/20240708_024409_coj0/capsula.diff"
  }
}
```
