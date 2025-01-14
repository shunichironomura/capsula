from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from capsula._utils import ExceptionInfo, search_for_project_root, to_flat_dict, to_nested_dict

if TYPE_CHECKING:
    from collections.abc import Hashable, Mapping, Sequence
    from pathlib import Path


def raise_exception() -> None:
    msg = "An example exception"
    raise ValueError(msg)


def test_exception_info_with_exception() -> None:
    try:
        raise_exception()
    except Exception as e:  # noqa: BLE001
        exc_info = ExceptionInfo.from_exception(e)
        assert exc_info.exc_type is not None, "exc_type should not be None"
        assert exc_info.exc_value is not None, "exc_value should not be None"
        assert exc_info.traceback is not None, "traceback should not be None"
        assert issubclass(exc_info.exc_type, BaseException), "exc_type should be the type of the exception"
        assert isinstance(exc_info.exc_value, BaseException), "exc_value should be an instance of BaseException"
        assert exc_info.traceback is not None, "traceback should not be None"
        assert exc_info.exc_type is ValueError, "exc_type should match the raised exception type"
        assert str(exc_info.exc_value) == "An example exception", "exc_value should match the raised exception"


def test_exception_info_with_none() -> None:
    exc_info = ExceptionInfo.from_exception(None)
    assert exc_info.exc_type is None, "exc_type should be None when called with None"
    assert exc_info.exc_value is None, "exc_value should be None when called with None"
    assert exc_info.traceback is None, "traceback should be None when called with None"


@pytest.mark.parametrize(
    ("input_dict", "expected_output"),
    [
        (
            {"a": 1, "b": {"c": 2, "d": 3}, "e": {"f": {"g": 4}}},
            {("a",): 1, ("b", "c"): 2, ("b", "d"): 3, ("e", "f", "g"): 4},
        ),
        ({"a": 1, "b": 2}, {("a",): 1, ("b",): 2}),
        ({}, {}),
        ({"a": {"b": {"c": {"d": 1}}}}, {("a", "b", "c", "d"): 1}),
        (({("a",): {1: {"c": 2}}, "b": 3}, {(("a",), 1, "c"): 2, ("b",): 3})),
    ],
)
def test_flat_dict_various(input_dict: Mapping[Hashable, Any], expected_output: dict[Sequence[Hashable], Any]) -> None:
    assert to_flat_dict(input_dict) == expected_output, "The dictionary was not flattened as expected"


@pytest.mark.parametrize(
    ("flat_dict", "expected_nested_dict"),
    [
        # Test for converting a flat dictionary to nested
        (
            {("a",): 1, ("b", "c"): 2, ("b", "d"): 3, ("e", "f", "g"): 4},
            {"a": 1, "b": {"c": 2, "d": 3}, "e": {"f": {"g": 4}}},
        ),
        # Test for already "nested" flat dictionary
        ({("a",): 1}, {"a": 1}),
        # Test for empty dictionary
        ({}, {}),
    ],
)
def test_to_nested_dict(flat_dict: Mapping[Sequence[Hashable], Any], expected_nested_dict: dict[Hashable, Any]) -> None:
    assert to_nested_dict(flat_dict) == expected_nested_dict, (
        "The conversion from flat to nested did not match the expected output"
    )


@pytest.mark.parametrize(
    "flat_dict",
    [
        # Test for key conflict: flat key conflicts with an existing nested structure
        {("a",): 1, ("a", "b"): 2},
        # Test for conflicting nested and flat keys
        {("a", "b"): 2, ("a",): 1},
    ],
)
def test_to_nested_dict_conflicts(
    flat_dict: Mapping[Sequence[Hashable], Any],
) -> None:
    with pytest.raises(ValueError, match="Key conflicted: .*"):
        to_nested_dict(flat_dict)


def test_search_for_project_root_found(tmp_path: Path) -> None:
    # Create a temporary directory simulating a project root
    project_root = tmp_path
    (project_root / "pyproject.toml").touch()  # Create an empty pyproject.toml file

    # Test that the search correctly identifies the project root
    assert search_for_project_root(project_root) == project_root, (
        "Failed to identify the project root when pyproject.toml is present"
    )


def test_search_for_project_root_in_parent(tmp_path: Path) -> None:
    # Create a temporary directory structure where the pyproject.toml is in a parent directory
    project_root = tmp_path
    (project_root / "pyproject.toml").touch()  # Create an empty pyproject.toml file
    child_dir = project_root / "child_dir"
    child_dir.mkdir()

    # Test that the search correctly finds the project root in the parent directory
    assert search_for_project_root(child_dir).resolve() == project_root.resolve()


def test_search_for_project_root_not_found(tmp_path: Path) -> None:
    # Create a temporary directory structure without a pyproject.toml
    start_dir = tmp_path

    # Test that searching in a directory structure without pyproject.toml raises FileNotFoundError
    with pytest.raises(FileNotFoundError, match="Project root not found."):
        search_for_project_root(start_dir)
