# `TimeWatcher`

The [`TimeWatcher`](../reference/capsula/index.md#capsula.TimeWatcher) monitors the execution time of the command/function.
It can be created using the `capsula.TimeWatcher.__init__` method.

::: capsula.TimeWatcher.__init__

## Configuration example

### Via `capsula.toml`

```toml
[in-run]
watchers = [
  { type = "TimeWatcher" },
]
```

### Via `@capsula.watcher` decorator

```python
import capsula

@capsula.run()
@capsula.watcher(capsula.TimeWatcher("calculation_time"))
def func(): ...
```

## Output example

The following is an example of the output of the `TimeWatcher`, reported by the [`JsonDumpReporter`](../reporters/json_dump.md):

```json
"time": {
  "calculation_time": "0:00:00.000798"
}
```
