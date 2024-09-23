# `SlackReporter`

!!! note
    The `SlackReporter` is still in development and lacks some features, such as specifying the token via environment variables, file attachments, detailed reporting, and reporting of the in-run capsule.

The [`SlackReporter`](../reference/capsula/index.md#capsula.SlackReporter) reports the capsule to a Slack channel. Capsules with the same run name will be reported to the same thread.

It can be created using the `capsula.SlackReporter.builder` method or the `capsula.SlackReporter.__init__` method.

::: capsula.SlackReporter.builder
::: capsula.SlackReporter.__init__

## Configuration example

### Via `capsula.toml`

```toml
[pre-run]
reporters = [{ type = "SlackReporter", channel = "<channel>", token = "<token>" }]

[in-run] # the reporting of an in-run capsule is not yet supported
reporters = [{ type = "SlackReporter", channel = "<channel>", token = "<token>" }]

[post-run]
reporters = [{ type = "SlackReporter", channel = "<channel>", token = "<token>" }]
```

### Via `@capsula.reporter` decorator

```python
import capsula

@capsula.run()
@capsula.reporter(capsula.SlackReporter.builder(channel="<channel>", token="<token>"), mode="all")
def func(): ...
```

## Output

It will send a simple message to the specified Slack channel.

For example, for the pre-run capsule:

```md
Capsule run `calculate_pi_n_samples_1000_seed_42_20240923_195220_Tplk` started
```

For the post-run capsule:

```md
Capsule run `calculate_pi_n_samples_1000_seed_42_20240923_195356_GNDq` completed
```
