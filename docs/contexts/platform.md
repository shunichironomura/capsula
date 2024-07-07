# `PlatformContext`

The [`PlatformContext`](../reference/capsula/index.md#capsula.PlatformContext) captures the Python version.
It can be created by `capsula.PlatformContext()` with no arguments.

## Configuration example

### Via `capsula.toml`

```toml
[pre-run]
contexts = [
  { type = "PlatformContext" },
]
```

### Via `@capsula.context` decorator

```python
import capsula

@capsula.run()
@capsula.context(capsula.PlatformContext(), mode="pre")
def func(): ...
```

## Output example

The following is an example of the output of the `PlatformContext`, reported by the [`JsonDumpReporter`](../reporters/json_dump.md):

```json
"platform": {
  "machine": "x86_64",
  "node": "SHUN-DESKTOP",
  "platform": "Linux-5.15.153.1-microsoft-standard-WSL2-x86_64-with-glibc2.34",
  "release": "5.15.153.1-microsoft-standard-WSL2",
  "version": "#1 SMP Fri Mar 29 23:14:13 UTC 2024",
  "system": "Linux",
  "processor": "x86_64",
  "python": {
    "executable_architecture": {
      "bits": "64bit",
      "linkage": "ELF"
    },
    "build_no": "default",
    "build_date": "Jul  7 2024 07:23:53",
    "compiler": "GCC 11.4.0",
    "branch": "",
    "implementation": "CPython",
    "version": "3.8.19"
  }
}
```
