from __future__ import annotations

import inspect
from inspect import cleandoc
from typing import Generic, Mapping, Optional, Type, TypeVar

import typer
from typer.models import ArgumentInfo, CommandInfo, OptionInfo, ParameterInfo

T = TypeVar("T", covariant=True)
A = TypeVar("A", bound=ParameterInfo)


class _Arg(Generic[A]):
    def __init__(self, a: Type[A]):
        self.__a = a

    def __arg(
        self,
        doc: str,
        *names: str,
        default: Optional[T] = None,
        **kwargs,
    ):
        args = dict(allow_dash=True, help=cleandoc(doc), **kwargs)
        if self.__a is OptionInfo:
            return typer.Option(default, *names, **args)
        else:
            return typer.Argument(default, **args)

    def __path(
        self,
        doc: str,
        *names,
        default: Optional[str],
        f: bool,
        d: bool,
        out: bool,
        **kwargs,
    ) -> A:
        kwargs = {
            **dict(
                exists=not out,
                dir_okay=d,
                file_okay=f,
                readable=out,
                writable=not out,
            ),
            **kwargs,
        }
        return self.__arg(doc, *names, default=default, **kwargs)

    def out_file(self, doc: str, *names, default: Optional[str] = None, **kwargs) -> A:
        return self.__path(doc, *names, default=default, f=True, d=False, out=True, **kwargs)

    def out_dir(self, doc: str, *names, default: Optional[str] = None, **kwargs) -> A:
        return self.__path(doc, *names, default=default, f=True, d=True, out=True, **kwargs)

    def out_path(self, doc: str, *names, default: Optional[str] = None, **kwargs) -> A:
        return self.__path(
            doc,
            *names,
            default=default,
            f=True,
            d=True,
            out=False,
            exists=False,
            **kwargs,
        )

    def in_file(self, doc: str, *names, default: Optional[str] = None, **kwargs) -> A:
        return self.__path(doc, *names, default=default, f=True, d=False, out=False, **kwargs)

    def in_dir(self, doc: str, *names, default: Optional[str] = None, **kwargs) -> A:
        return self.__path(doc, *names, default=default, f=False, d=True, out=False, **kwargs)

    def in_path(self, doc: str, *names, default: Optional[str] = None, **kwargs) -> A:
        return self.__path(
            doc,
            *names,
            default=default,
            f=True,
            d=True,
            out=False,
            exists=False,
            **kwargs,
        )

    def val(self, doc: str, *names, default: Optional[T] = None, **kwargs) -> A:
        return self.__arg(doc, *names, default=default, **kwargs)

    def flag(self, doc: str, *names, **kwargs) -> A:
        return self.__arg(doc, *names, default=False, **kwargs)


Arg: _Arg[ArgumentInfo] = _Arg(ArgumentInfo)
Opt: _Arg[OptionInfo] = _Arg(OptionInfo)


class TyperUtils:
    @classmethod
    def get_help(
        cls,
        c: CommandInfo,
        *,
        hidden: bool = True,
        show_false: bool = False,
    ) -> Mapping[str, str]:
        """
        Gets options and arguments from a typer command.
        Reconstructs the typer --help text as best as possible.

        Args:
            c: Typer command
            hidden: Include commands marked with ``hidden=True``
            show_false: Show ``[default: false]`` for flags, which is normally implied

        Returns:
            A mapping from command names (inc. ``--`` for options) to descriptive text.
            For example: ``--show-full [bool]\nShows full docs.\n[default: true]``.
        """
        flag_fix = {True: "true", False: "false" if show_false else None}
        args = {}
        for k, p in inspect.signature(c.callback).parameters.items():
            v = p.default
            dtype = p.annotation
            if isinstance(dtype, str) and (
                dtype.startswith("OptionInfo(") or dtype.startswith("ArgumentInfo(")
            ):
                raise TypeError(
                    f"'{k}' annotation is {dtype}!" + "You probably meant to pass it as a default"
                )
            if dtype is inspect.Parameter.empty and isinstance(v, ParameterInfo):
                dtype = v.default.__class__.__name__.strip("'\"")
            elif dtype is inspect.Parameter.empty:
                try:
                    dtype = v.__class__.__name__.strip("'\"")
                except AttributeError:
                    dtype = None
            if isinstance(v, ParameterInfo):
                if isinstance(v, OptionInfo):
                    k = "--" + k
                k = k.replace("_", "-") if v.allow_dash else k
                if v.help is None:
                    doc = k if dtype is None else f"{k} [{dtype}]"
                else:
                    doc = f"{k}\n{v.help}" if dtype is None else f"{k} [{dtype}]\n{v.help}"
                if v.hidden and not hidden:
                    continue
                default = flag_fix.get(v.default, v.default)
                if v.show_default and default is not None:
                    doc += f"\n[default: {default}]"
            else:
                doc = k if dtype is None else f"{k} [{dtype}]"
                if v is not inspect.Parameter.empty:
                    default = flag_fix.get(v, v)
                    if default is not None:
                        doc += f"\n[default: {v}]"
            args[k] = doc
        return args


__all__ = ["Arg", "Opt", "TyperUtils"]
