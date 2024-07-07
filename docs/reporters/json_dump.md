# `JsonDumpReporter`

The [`JsonDumpReporter`](../reference/capsula/index.md#capsula.JsonDumpReporter) reports the capsule in JSON format.
It can be created using the `capsula.JsonDumpReporter.builder` method or the `capsula.JsonDumpReporter.__init__` method.

::: capsula.JsonDumpReporter.builder
::: capsula.JsonDumpReporter.__init__

## Configuration example

### Via `capsula.toml`

```toml
[pre-run]
reporters = [{ type = "JsonDumpReporter" }]

[in-run]
reporters = [{ type = "JsonDumpReporter" }]

[post-run]
reporters = [{ type = "JsonDumpReporter" }]
```

### Via `@capsula.reporter` decorator

```python
import capsula

@capsula.run()
@capsula.reporter(capsula.JsonDumpReporter.builder(), mode="all")
def func(): ...
```

## Output

It will output the pre-run, in-run, and post-run capsules to `in-run-report.json`, `pre-run-report.json`, and `post-run-report.json` in the run directory, respectively.
