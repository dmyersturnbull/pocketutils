from __future__ import annotations

import inspect
from inspect import cleandoc
from typing import Optional, TypeVar, Mapping

import typer
from typer.models import CommandInfo, ParameterInfo, OptionInfo

T = TypeVar("T", covariant=True)


class _Args:
    @classmethod
    def _arg(
        cls,
        doc: str,
        *names,
        default: Optional[T] = None,
        pos: bool = False,
        **kwargs,
    ):
        kwargs = dict(
            help=cleandoc(doc),
            **kwargs,
            allow_dash=True,
        )
        if pos:
            return typer.Argument(default, **kwargs)
        else:
            return typer.Option(default, *names, **kwargs)

    @classmethod
    def _path(
        cls,
        doc: str,
        *names,
        default: Optional[str],
        f: bool,
        d: bool,
        out: bool,
        pos: bool,
        **kwargs,
    ):
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
        return _Args._arg(doc, *names, default=default, pos=pos, **kwargs)


class Arg(_Args):
    @classmethod
    def _arg(cls, doc: str, *, default: Optional[T] = None, **kwargs):
        super()._arg(doc, default=default, pos=True, **kwargs)

    @classmethod
    def _path(cls, doc: str, *, default: Optional[str], f: bool, d: bool, out: bool, **kwargs):
        super()._path(doc, defualt=default, f=f, d=d, out=out, pos=True, **kwargs)

    @classmethod
    def out_file(cls, doc: str, *, default: Optional[str] = None, **kwargs):
        return cls._path(doc, default=default, f=True, d=False, out=True, **kwargs)

    @classmethod
    def out_dir(cls, doc: str, *, default: Optional[str] = None, **kwargs):
        return cls._path(doc, default=default, f=True, d=True, out=True, **kwargs)

    @classmethod
    def out_path(cls, doc: str, *, default: Optional[str] = None, **kwargs):
        return cls._path(doc, default=default, f=True, d=True, out=False, **kwargs)

    @classmethod
    def in_file(cls, doc: str, *, default: Optional[str] = None, **kwargs):
        return cls._path(doc, default=default, f=True, d=False, out=False, **kwargs)

    @classmethod
    def in_dir(cls, doc: str, *, default: Optional[str] = None, **kwargs):
        return cls._path(doc, default=default, f=False, d=True, out=False, **kwargs)

    @classmethod
    def in_path(cls, doc: str, *, default: Optional[str] = None, **kwargs):
        return cls._path(doc, default=default, f=True, d=True, out=False, **kwargs)

    @classmethod
    def val(cls, doc: str, *, default: Optional[T] = None, **kwargs):
        return cls._arg(doc, default=default, **kwargs)


class Opt(_Args):
    @classmethod
    def _arg(cls, doc: str, *names: str, default: Optional[T] = None, **kwargs):
        super()._arg(doc, default=default, **kwargs)

    @classmethod
    def _path(
        cls, doc: str, *names: str, default: Optional[str], f: bool, d: bool, out: bool, **kwargs
    ):
        super()._path(doc, defualt=default, f=f, d=d, out=out, **kwargs)

    @classmethod
    def out_file(cls, doc: str, *names, default: Optional[str] = None, **kwargs):
        return _Args._path(doc, *names, default=default, f=True, d=False, out=True, **kwargs)

    @classmethod
    def out_dir(cls, doc: str, *names, default: Optional[str] = None, **kwargs):
        return _Args._path(doc, *names, default=default, f=True, d=True, out=True, **kwargs)

    @classmethod
    def out_path(cls, doc: str, *names, default: Optional[str] = None, **kwargs):
        return _Args._path(
            doc,
            *names,
            default=default,
            f=True,
            d=True,
            out=False,
            pos=False,
            exists=False,
            **kwargs,
        )

    @classmethod
    def in_file(cls, doc: str, *names, default: Optional[str] = None, **kwargs):
        return _Args._path(doc, *names, default=default, f=True, d=False, out=False, **kwargs)

    @classmethod
    def in_dir(cls, doc: str, *names, default: Optional[str] = None, **kwargs):
        return _Args._path(doc, *names, default=default, f=False, d=True, out=False, **kwargs)

    @classmethod
    def in_path(cls, doc: str, *names, default: Optional[str] = None, **kwargs):
        return _Args._path(
            doc,
            *names,
            default=default,
            f=True,
            d=True,
            out=False,
            pos=False,
            exists=False,
            **kwargs,
        )

    @classmethod
    def val(cls, doc: str, *names, default: Optional[T] = None, **kwargs):
        return _Args._arg(doc, *names, default=default, **kwargs)

    @classmethod
    def flag(cls, doc: str, *names, **kwargs):
        return _Args._arg(doc, *names, default=False, **kwargs)


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
