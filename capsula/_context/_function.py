from __future__ import annotations

import inspect
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Mapping, Sequence, TypedDict

from capsula._run import FuncInfo

from ._base import ContextBase

if TYPE_CHECKING:
    from collections.abc import Container

    from capsula._run import CapsuleParams


class _FunctionContextData(TypedDict):
    file_path: Path
    first_line_no: int
    bound_args: Mapping[str, Any]


class FunctionContext(ContextBase):
    @classmethod
    def builder(
        cls,
        *,
        ignore: Container[str] = (),
    ) -> Callable[[CapsuleParams], FunctionContext]:
        def build(params: CapsuleParams) -> FunctionContext:
            if not isinstance(params.exec_info, FuncInfo):
                msg = "FunctionContext can only be built from a FuncInfo."
                raise TypeError(msg)

            return cls(
                params.exec_info.func,
                args=params.exec_info.args,
                kwargs=params.exec_info.kwargs,
                ignore=ignore,
                _remove_pre_run_capsule_before_binding=params.exec_info.pass_pre_run_capsule,
            )

        return build

    def __init__(
        self,
        function: Callable[..., Any],
        *,
        args: Sequence[Any],
        kwargs: Mapping[str, Any],
        ignore: Container[str] = (),
        _remove_pre_run_capsule_before_binding: bool = False,
    ) -> None:
        self._function = function
        self._args = args
        self._kwargs = kwargs
        self._ignore = ignore
        self._remove_pre_run_capsule_before_binding = _remove_pre_run_capsule_before_binding

    def encapsulate(self) -> _FunctionContextData:
        file_path = Path(inspect.getfile(self._function))
        _, first_line_no = inspect.getsourcelines(self._function)
        sig = inspect.signature(self._function)

        if self._remove_pre_run_capsule_before_binding:
            sig = sig.replace(parameters=tuple(p for p in sig.parameters.values() if p.name != "pre_run_capsule"))

        ba = sig.bind(*self._args, **self._kwargs)
        ba.apply_defaults()
        ba_wo_ignore = {k: v for k, v in ba.arguments.items() if k not in self._ignore}
        return {
            "file_path": file_path,
            "first_line_no": first_line_no,
            "bound_args": ba_wo_ignore,
        }

    def default_key(self) -> tuple[str, str]:
        return ("function", self._function.__name__)
