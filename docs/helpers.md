# Helper Functions and Variables

Capsula provides several helper functions and variables:

- [`capsula.__version__`](reference/capsula/index.md#capsula.__version__) - The version of Capsula.
- [`capsula.record`](reference/capsula/index.md#capsula.record) - You can record any value to the current run. Useful for quickly recording the intermediate results.
- [`capsula.current_run_name`](reference/capsula/index.md#capsula.current_run_name) - You can access the current run name. Useful for embedding the run name in the output files.
- [`capsula.pass_pre_run_capsule`](reference/capsula/index.md#capsula.pass_pre_run_capsule) - You can pass the pre-run capsule to the function. Useful for accessing the captured contexts such as Git SHA.
- [`capsula.search_for_project_root`](reference/capsula/index.md#capsula.search_for_project_root) - You can search for the project root directory. Useful for specifying the paths relative to the project root.
