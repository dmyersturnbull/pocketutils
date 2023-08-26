from datetime import date
from typing import Self

import pytest
from pocketutils.core.dot_dict import NestedDotDict


class TestDotDict:
    def test_keys(self: Self) -> None:
        t = NestedDotDict({"a": "0", "b": 1, "c": {"c1": 8, "c2": ["abc", "xyz"]}})
        assert list(t.keys()) == ["a", "b", "c"]

    def test_bad(self: Self) -> None:
        with pytest.raises(ValueError):
            NestedDotDict({"a.b": "c"})
        with pytest.raises(ValueError):
            NestedDotDict({"a": {"b.c": "d"}})
        with pytest.raises(TypeError):
            # noinspection PyTypeChecker
            NestedDotDict({1: 2})
        with pytest.raises(ValueError):
            NestedDotDict({"a.b": {5: 2}})

    def test_iter(self: Self) -> None:
        t = NestedDotDict({"a": {"b": 555}})
        assert len(t) == 1
        assert list(iter(t)) == ["a"]
        assert list(t.items()) == [("a", {"b": 555})]

    def test_get(self: Self) -> None:
        t = NestedDotDict({"a": {"b": {"c": "hello"}}})
        assert t.get("a") == {"b": {"c": "hello"}}
        assert t.get("a.b") == {"c": "hello"}
        assert t.get("a.b.c") == "hello"
        assert t["a"] == {"b": {"c": "hello"}}
        assert t["a.b"] == {"c": "hello"}
        assert t["a.b.c"] == "hello"
        assert t.get("b") is None
        assert t.get("a.x") is None
        assert t.get("a.b.x") is None
        assert t.get("a.b.c.x") is None
        assert t.get("b", default="Q") == "Q"
        with pytest.raises(LookupError):
            # noinspection PyStatementEffect
            t["b"]
        with pytest.raises(LookupError):
            # noinspection PyStatementEffect
            t["a.x"]
        with pytest.raises(LookupError):
            # noinspection PyStatementEffect
            t["a.b.c.x"]
        t = NestedDotDict({"a": {"1": "hello", "2": "ell", "3": "elle"}})
        assert t["a.1"] == "hello"
        assert t["a.2"] == "ell"
        assert t["a.3"] == "elle"

    def test_get_as(self: Self) -> None:
        t = NestedDotDict(
            {
                "animal": "kitten",
                "size": 4.3,
                "number": 8,
                "birthday": "2020-01-17",
                "birthdayzulu": "2020-01-17Z",
                "birthdatetime": "2020-01-17T15:22:11",
                "birthdatetimezulu": "2020-01-17T15:22:11Z",
            },
        )
        assert t.get_as("animal", str) == "kitten"
        assert t.get_as("size", float) == 4.3
        with pytest.raises(TypeError):
            t.get_as("size", str)
        assert t.get_as("number", int) == 8
        with pytest.raises(TypeError):
            t.get_as("birthday", date)

    def test_get_list_as(self: Self) -> None:
        t = NestedDotDict({"kittens": ["dory", "johnson", "robin", "jack"], "ages": [3, 5, 7, 11]})
        assert t.get_list_as("kittens", str) == ["dory", "johnson", "robin", "jack"]
        assert t.get_list_as("ages", int) == [3, 5, 7, 11]
        with pytest.raises(TypeError):
            t.get_list_as("ages", str)
        assert t.get_list_as("hobbies", str) == []
        with pytest.raises(TypeError):
            t.get_list_as("kittens", float)

    def test_req(self: Self) -> None:
        t = NestedDotDict(
            {
                "kittens": ["dory", "johnson", "robin", "jack"],
                "ages": [3, 5, 7, 11],
                "carrots": "yes",
            },
        )
        assert t.req_as("carrots", str) == "yes"
        assert t.req_list_as("ages", int) == [3, 5, 7, 11]
        with pytest.raises(LookupError):
            t.req_list_as("hobbies", str)

    def test_nested(self: Self) -> None:
        t = NestedDotDict(
            {"kittens": {"names": ["dory", "johnson", "robin", "jack"], "ages": [3, 5, 7, 11]}},
        )
        assert isinstance(t.get("kittens"), dict)
        assert t.get("kittens.ages") == [3, 5, 7, 11]
        assert t.get_list("kittens.ages") == [3, 5, 7, 11]
        assert t.get_list_as("kittens.ages", int) == [3, 5, 7, 11]

    def test_leaves(self: Self) -> None:
        t = NestedDotDict({"a": {"b": 1}, "b": 2, "c": {"a": {"a": 3}}})
        assert t.leaves() == {"a.b": 1, "b": 2, "c.a.a": 3}

    def test_size(self: Self) -> None:
        t = NestedDotDict({"a": {"b": 1}, "b": 2, "c": {"a": {"a": 3}}})
        assert t.n_elements_total() == 3
        t = NestedDotDict({"a": {"b": 1}, "b": [1, 2, 3], "c": {"a": {"a": 3}}})
        assert t.n_elements_total() == 5

    def test_bytes(self: Self) -> None:
        t = NestedDotDict({"a": {"b": 1}, "b": 2, "c": {"a": {"a": 3}}})
        assert t.n_bytes_total() == 84
        t = NestedDotDict({"a": {"b": 1}, "b": [1, 2, 3], "c": {"a": {"a": 3}}})
        assert t.n_bytes_total() == 140

    def test_req_as(self: Self) -> None:
        t = NestedDotDict({"zoo": {"animals": "jackets"}, "what": 0.1})
        assert t.req_as("zoo.animals", str) == "jackets"
        assert t.req_as("what", float) == 0.1
        with pytest.raises(TypeError):
            t.req_as("what", str)


if __name__ == "__main__":
    pytest.main()
