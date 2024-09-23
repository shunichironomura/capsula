import logging
import random
from datetime import datetime

from rich.logging import RichHandler

import capsula


def my_run_name_factory(func_info: capsula.FuncInfo, random_str: str, timestamp: datetime) -> str:
    timestamp_str = timestamp.astimezone().strftime(r"%Y%m%d_%H%M%S")
    return (
        f"{func_info.func.__name__}_n_samples_{func_info.bound_args['n_samples']}_seed_{func_info.bound_args['seed']}_"
        f"{timestamp_str}_{random_str}"
    )


@capsula.run(run_name_factory=my_run_name_factory)
@capsula.context(capsula.FunctionContext.builder(), mode="pre")
@capsula.context(capsula.FileContext.builder("pi.txt", move=True), mode="post")
def calculate_pi(n_samples: int = 1_000, seed: int = 42) -> None:
    random.seed(seed)
    xs = (random.random() for _ in range(n_samples))
    ys = (random.random() for _ in range(n_samples))
    inside = sum(x * x + y * y <= 1.0 for x, y in zip(xs, ys))

    # You can record values to the capsule using the `record` method.
    capsula.record("inside", inside)

    pi_estimate = (4.0 * inside) / n_samples
    print(f"Pi estimate: {pi_estimate}")
    capsula.record("pi_estimate", pi_estimate)
    print(f"Run name: {capsula.current_run_name()}")

    with open("pi.txt", "w") as output_file:
        output_file.write(f"Pi estimate: {pi_estimate}.")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(show_time=False, show_path=True)],
    )

    calculate_pi(n_samples=1_000)
