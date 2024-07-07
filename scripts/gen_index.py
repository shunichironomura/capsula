"""Generate the index page from README.md."""

from pathlib import Path

import mkdocs_gen_files


def main() -> None:
    src = Path(__file__).parents[1]
    readme_path = src / "README.md"
    index_path = Path("index.md")

    readme_content = readme_path.read_text()
    index_content = adjust_documentation_paths(readme_content)

    with mkdocs_gen_files.open(index_path, "w") as fd:
        fd.write(index_content)


def adjust_documentation_paths(content: str) -> str:
    """Adjust the documentation paths in the README.

    This function is used to adjust the documentation paths in the README for the index page.
    Example: `(docs/contents/cpu.md)` -> `(contents/cpu.md)`
    """
    return content.replace("(docs/", "(")


if __name__ == "__main__":
    main()
