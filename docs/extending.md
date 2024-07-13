# Creating your own contexts, reporters, and watchers

You can extend Capsula by creating your own contexts, reporters, and watchers.
You only need to create a class that inherits from the base class of the corresponding type.

## Contexts

To create a context, you need to

- Inherit from the `capsula.ContextBase` class. This will register the class to the Capsula context registry.
- Implement the `encapsulate` method that captures the context.
- Implement the `default_key` method that returns the default key used to store the context in the capsule.

Here's an example of a custom context that captures the current time:

```python
import capsula
from zoneinfo import ZoneInfo
from datetime import datetime

class TimeContext(capsula.ContextBase):
    def __init__(self, timezone: str = "UTC"):
        self.timezone = ZoneInfo(timezone)

    def encapsulate(self) -> dict[str, datetime]:
        return {"time": datetime.now(self.timezone)}

    def default_key(self) -> str:
        return "time"
```

!!! note
    The above example uses the `zoneinfo` module, which is available in Python 3.9 and later.

Optionally, you can implement the `builder` method that returns a function that creates the context. This is useful when you need to access the runtime information ([`capsula.CapsuleParams`](reference/capsula/index.md#capsula.CapsuleParams)) when creating the context.

Here's an example of a custom context that captures the project root path:

```python
import capsula

class ProjectRootContext(capsula.ContextBase):
    def __init__(self, path: str | Path):
        self.path = str(path)

    def encapsulate(self) -> dict[str, str]:
        return {"project_root": self.path}

    def default_key(self) -> str:
        return "project_root"

    @classmethod
    def builder(cls):
        def build(params: capsula.CapsuleParams) -> "ProjectRootContext":
            return ProjectRootContext(params.project_root)
        return build
```

## Watchers

To create a watcher, you need to

- Inherit from the `capsula.WatcherBase` class. This will register the class to the Capsula watcher registry.
- Implement the `watch` method that behaves as a context manager that watches the command/function execution.
- Implement the `encapsulate` method that returns the watcher's output.
- Implement the `default_key` method that returns the default key used to store the watcher's output in the capsule.

Here's an example of a custom watcher that watches the execution time of a command/function (from the implementation of the [`TimeWatcher`](watchers/time.md) class):

```python
import capsula
import time
from datetime import timedelta
from collections.abc import Iterator
from contextlib import contextmanager

class TimeWatcher(capsula.WatcherBase):
    def __init__(
        self,
        name: str = "execution_time",
    ) -> None:
        self._name = name
        self._duration: timedelta | None = None

    def encapsulate(self) -> timedelta | None:
        return self._duration

    @contextmanager
    def watch(self) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            end = time.perf_counter()
            self._duration = timedelta(seconds=end - start)

    def default_key(self) -> tuple[str, str]:
        return ("time", self._name)
```

Like contexts, you can implement the `builder` method to create the watcher using the runtime information.

## Reporters

To create a reporter, you need to

- Inherit from the `capsula.ReporterBase` class. This will register the class to the Capsula reporter registry.
- Implement the `report` method that reports the capsule.

Here's an example of a custom reporter that dumps the capsule to a pickle file:

```python
import capsula
import pickle
from pathlib import Path

class PickleDumpReporter(capsula.ReporterBase):
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def report(self, capsule: capsula.Capsule) -> None:
        with open(self.path, "wb") as file:
            pickle.dump(capsule, file)

    @classmethod
    def builder(cls):
        def build(params: capsula.CapsuleParams) -> "PickleDumpReporter":
            return PickleDumpReporter(params.run_dir / "capsule.pkl")
        return build
```

As shown in the example, you can implement the `builder` method to create the reporter using the runtime information.
