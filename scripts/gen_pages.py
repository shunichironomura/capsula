"""Generate the code reference pages."""

from pathlib import Path

import mkdocs_gen_files

root = Path(__file__).parents[1]


def gen_index_page() -> None:
    readme_path = root / "README.md"
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


def gen_ref_pages() -> None:
    nav = mkdocs_gen_files.Nav()  # type: ignore[attr-defined, no-untyped-call]

    package_root = root / "capsula"

    for path in sorted(package_root.rglob("*.py")):
        module_path = path.relative_to(root).with_suffix("")
        doc_path = path.relative_to(root).with_suffix(".md")
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
