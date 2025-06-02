"""Generate the code reference pages."""

from pathlib import Path

import mkdocs_gen_files

PROJECT_ROOT = Path(__file__).parents[1]


def gen_index_page() -> None:
    readme_path = PROJECT_ROOT / "README.md"
    index_path = Path("index.md")

    readme_content = readme_path.read_text()
    index_content = adjust_documentation_paths(readme_content)
    index_content = remove_lines_with_documentation_link(index_content)

    with mkdocs_gen_files.open(index_path, "w") as fd:
        fd.write(index_content)


def adjust_documentation_paths(content: str) -> str:
    """Adjust the documentation paths in the README.

    This function is used to adjust the documentation paths in the README for the index page.
    Example: `(docs/contents/cpu.md)` -> `(contents/cpu.md)`
    """
    return content.replace("(docs/", "(")


def remove_lines_with_documentation_link(content: str) -> str:
    """Remove lines with documentation links.

    This function is used to remove the lines with documentation links from the README for the index page.
    """
    return "\n".join(
        line for line in content.split("\n") if "(https://shunichironomura.github.io/capsula/)" not in line
    )


def convert_to_mkdocs_admonition(content: str) -> str:
    """Convert the GitHub-style alert to mkdocs admonition format.

    This function is used to convert the GitHub-style alert to mkdocs admonition format.

    Example:
    ```markdown
    > [!NOTE]
    > This is a note.
    > This is still a note.
    ```
    becomes:
    ```markdown
    !!! note
        This is a note.
        This is still a note.
    ```

    """
    lines = content.split("\n")

    alert_start_line_indices = [i for i, line in enumerate(lines) if line.startswith("> [!")]
    for start_index in alert_start_line_indices:
        end_index = start_index + 1
        while end_index < len(lines) and lines[end_index].startswith("> "):
            end_index += 1

        alert_lines = lines[start_index:end_index]
        alert_type = alert_lines[0][len("> [!") : alert_lines[0].index("]")]
        alert_content_lines = [line[2:] for line in alert_lines[1:]]
        lines[start_index:end_index] = [
            f"!!! {alert_type.lower()}",
            *(f"    {line}" for line in alert_content_lines),
        ]

    return "\n".join(lines)


def gen_ref_pages() -> None:
    nav = mkdocs_gen_files.Nav()  # type: ignore[attr-defined, no-untyped-call]

    src_dir = PROJECT_ROOT / "src"
    package_root = src_dir / "capsula"

    for path in sorted(package_root.rglob("*.py")):
        module_path = path.relative_to(src_dir).with_suffix("")
        doc_path = path.relative_to(src_dir).with_suffix(".md")
        full_doc_path = Path("reference", doc_path)

        parts = tuple(module_path.parts)

        if parts[-1] == "__init__":
            parts = parts[:-1]
            if parts[-1].startswith("_"):
                continue
            doc_path = doc_path.with_name("index.md")
            full_doc_path = full_doc_path.with_name("index.md")
        elif parts[-1] == "__main__" or parts[-1].startswith("_"):
            continue

        nav[parts] = doc_path.as_posix()

        with mkdocs_gen_files.open(full_doc_path, "w") as fd:
            identifier = ".".join(parts)
            print("::: " + identifier, file=fd)

        mkdocs_gen_files.set_edit_path(full_doc_path, path)

    with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
        nav_file.writelines(nav.build_literate_nav())


gen_index_page()
gen_ref_pages()
