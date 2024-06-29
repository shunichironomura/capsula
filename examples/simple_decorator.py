import random
from pathlib import Path

import capsula


@capsula.run()
@capsula.context(capsula.FileContext.default(Path(__file__).parent / "pi.txt", move=True), mode="post")
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

    with (Path(__file__).parent / "pi.txt").open("w") as output_file:
        output_file.write(f"Pi estimate: {pi_estimate}.")


if __name__ == "__main__":
    calculate_pi(n_samples=1_000)
