# `CommandContext`

The [`CommandContext`](../reference/capsula/#capsula.CommandContext) captures the output of shell commands.
It can be created using the `capsula.CommandContext.builder` method or the `capsula.CommandContext.__init__` method.

::: capsula.CommandContext.builder
::: capsula.CommandContext.__init__

## Output example

The following is an example of the output of the `CommandContext`, reported by the [`JsonDumpReporter`](../reporters/json_dump.md):

```json
"command": {
    "poetry check --lock": {
        "command": "poetry check --lock",
        "cwd": null,
        "returncode": 0,
        "stdout": "All set!\n",
        "stderr": ""
    },
}
```
