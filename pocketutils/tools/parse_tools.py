from collections.abc import Generator, Mapping, Sequence
from typing import Any, Tuple

from pocketutils import AlreadyUsedError, ParsingError


class ParseTools:
    @classmethod
    def dicts_to_toml_aot(cls, dicts: Sequence[Mapping[str, Any]]):
        """
        Make a tomlkit Document consisting of an array of tables ("AOT").

        Args:
            dicts: A sequence of dictionaries

        Returns:
            A tomlkit`AoT<https://github.com/sdispater/tomlkit/blob/master/tomlkit/items.py>`_
            (i.e. ``[[array]]``)
        """
        import tomlkit

        aot = tomlkit.aot()
        for ser in dicts:
            tab = tomlkit.table()
            aot.append(tab)
            for k, v in ser.items():
                tab.add(k, v)
            tab.add(tomlkit.nl())
        return aot

    @classmethod
    def dots_to_dict(cls, items: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        Make sub-dictionaries from substrings in ``items`` delimited by ``.``.
        Used for TOML.

        Example:
            ``Utils.dots_to_dict({"genus.species": "fruit bat"}) == {"genus": {"species": "fruit bat"}}``

        See Also:
            :meth:`dict_to_dots`
        """
        dct = {}
        cls._un_leaf(dct, items)
        return dct

    @classmethod
    def dict_to_dots(cls, items: Mapping[str, Any]) -> Mapping[str, Any]:
        """
        Performs the inverse of :meth:`dots_to_dict`.

        Example:
            ``Utils.dict_to_dots({"genus": {"species": "fruit bat"}}) == {"genus.species": "fruit bat"}``
        """
        return dict(cls._re_leaf("", items))

    @classmethod
    def _un_leaf(cls, to: typing.MutableMapping[str, Any], items: Mapping[str, Any]) -> None:
        for k, v in items.items():
            if "." not in k:
                to[k] = v
            else:
                k0, k1 = k.split(".", 1)
                if k0 not in to:
                    to[k0] = {}
                cls._un_leaf(to[k0], {k1: v})

    @classmethod
    def _re_leaf(cls, at: str, items: Mapping[str, Any]) -> Generator[tuple[str, Any], None, None]:
        for k, v in items.items():
            me = at + "." + k if len(at) > 0 else k
            if hasattr(v, "items") and hasattr(v, "keys") and hasattr(v, "values"):
                yield from cls._re_leaf(me, v)
            else:
                yield me, v

    @classmethod
    def read_lines(cls, data: str, *, ignore_comments: bool = False) -> list[str]:
        """
        Returns a list of lines in the file.
        Optionally skips lines starting with ``#`` or that only contain whitespace.
        """
        lines = []
        for line in data.splitlines():
            line = line.strip()
            if not ignore_comments or not line.startswith("#") and not len(line.strip()) == 0:
                lines.append(line)
        return lines

    @classmethod
    def parse_properties(cls, data: str) -> dict[str, str]:
        """
        Reads a .properties file.
        A list of lines with key=value pairs (with an equals sign).
        Lines beginning with # are ignored.
        Each line must contain exactly 1 equals sign.

        .. caution::
            The escaping is not compliant with the standard

        Args:
            data: Data

        Returns:
            A dict mapping keys to values, both with surrounding whitespace stripped
        """
        dct = {}
        for i, line in enumerate(data.splitlines()):
            line = line.strip()
            if len(line) == 0 or line.startswith("#"):
                continue
            if line.count("=") != 1:
                raise ParsingError(f"Bad line {i}: {line}")
            k, v = line.split("=")
            k, v = k.strip(), v.strip()
            if k in dct:
                raise AlreadyUsedError(f"Duplicate property {k} (line {i})", key=k)
            dct[k] = v
        return dct

    @classmethod
    def write_properties(cls, properties: Mapping[Any, Any]) -> str:
        """
        Writes lines of a .properties file.

        .. caution::
            The escaping is not compliant with the standard
        """
        bad_keys = []
        bad_values = []
        lines = []
        for k, v in properties.items():
            if "=" in k or "\n" in k:
                bad_keys.append(k)
            if "=" in v or "\n" in v:
                bad_values.append(k)
            lines.append(
                str(k).replace("=", "--").replace("\n", "\\n")
                + "="
                + str(v).replace("=", "--").replace("\n", "\\n")
                + "\n"
            )
        if len(bad_keys) > 0:
            raise ValueError(
                f"These keys containing '=' or \\n were escaped: {', '.join(bad_keys)}"
            )
        if len(bad_values) > 0:
            raise ValueError(
                f"These keys containing '=' or \\n were escaped: {', '.join(bad_values)}"
            )
        return "\n".join(lines)


__all__ = ["ParseTools"]
