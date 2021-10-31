from datetime import date, datetime, timezone

import pytest

from pocketutils.core.dot_dict import *


class TestDotDict:
    def test_keys(self):
        t = NestedDotDict({"a": "0", "b": 1, "c": {"c1": 8, "c2": ["abc", "xyz"]}})
        assert list(t.keys()) == ["a", "b", "c"]

    def test_bad(self):
        with pytest.raises(ValueError):
            NestedDotDict({"a.b": "c"})
        with pytest.raises(ValueError):
            NestedDotDict({"a": {"b.c": "d"}})
        with pytest.raises(ValueError):
            # noinspection PyTypeChecker
            NestedDotDict({1: 2})
        with pytest.raises(ValueError):
            NestedDotDict({"a.b": {5: 2}})

    def test_iter(self):
        t = NestedDotDict(dict(a=dict(b=555)))
        assert len(t) == 1
        assert list(iter(t)) == ["a"]
        assert t.items() == [("a", {"b": 555})]

    def test_get(self):
        t = NestedDotDict(dict(a=dict(b=dict(c="hello"))))
        assert t.get("a") == dict(b=dict(c="hello"))
        assert t.get("a.b") == dict(c="hello")
        assert t.get("a.b.c") == "hello"
        assert t["a"] == dict(b=dict(c="hello"))
        assert t["a.b"] == dict(c="hello")
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

    def test_get_as(self):
        t = NestedDotDict(
            {
                "animal": "kitten",
                "size": 4.3,
                "number": 8,
                "birthday": "2020-01-17",
                "birthdayzulu": "2020-01-17Z",
                "birthdatetime": "2020-01-17T15:22:11",
                "birthdatetimezulu": "2020-01-17T15:22:11Z",
            }
        )
        assert t.get_as("animal", str) == "kitten"
        assert t.get_as("size", float) == 4.3
        assert t.get_as("size", str) == "4.3"
        assert t.get_as("number", int) == 8
        assert t.get_as("birthday", date) == date(2020, 1, 17)
        assert t.get_as("birthdatetime", datetime) == datetime(2020, 1, 17, 15, 22, 11)
        assert t.get_as("birthdatetimezulu", datetime) == datetime(
            2020, 1, 17, 15, 22, 11, tzinfo=timezone.utc
        )
        # parsing a date string as datetime is dangerous because it fills in 00:00:00
        with pytest.raises(ValueError):
            assert t.get_as("birthdayzulu", datetime)
        with pytest.raises(ValueError):
            assert t.get_as("birthday", datetime)
        with pytest.raises(ValueError):
            assert t.get_as("birthdayzulu", date)
        with pytest.raises(ValueError):
            t.get_as("birthdatetime", date)
        with pytest.raises(ValueError):
            t.get_as("animal", int)

    def test_get_list_as(self):
        t = NestedDotDict({"kittens": ["dory", "johnson", "robin", "jack"], "ages": [3, 5, 7, 11]})
        assert t.get_list_as("kittens", str) == ["dory", "johnson", "robin", "jack"]
        assert t.get_list_as("ages", int) == [3, 5, 7, 11]
        assert t.get_list_as("ages", str) == ["3", "5", "7", "11"]
        assert t.get_list_as("hobbies", str) is None
        with pytest.raises(ValueError):
            t.get_list_as("kittens", float)

    def test_req(self):
        t = NestedDotDict(
            {
                "kittens": ["dory", "johnson", "robin", "jack"],
                "ages": [3, 5, 7, 11],
                "carrots": "yes",
            }
        )
        assert t.req_as("carrots", str) == "yes"
        assert t.req_list_as("ages", int) == [3, 5, 7, 11]
        with pytest.raises(LookupError):
            t.req_list_as("hobbies", str)

    def test_nested(self):
        t = NestedDotDict(
            {"kittens": {"names": ["dory", "johnson", "robin", "jack"], "ages": [3, 5, 7, 11]}}
        )
        assert isinstance(t.get("kittens"), NestedDotDict)
        assert t.get_list_as("kittens.ages", int) == [3, 5, 7, 11]

    def test_leaves(self):
        t = NestedDotDict(dict(a=dict(b=1), b=2, c=dict(a=dict(a=3))))
        assert t.leaves() == {"a.b": 1, "b": 2, "c.a.a": 3}

    def test_string(self):
        t = NestedDotDict(dict(a=dict(b=1), b=2, c=dict(a=dict(a=3))))
        assert str(t) == str(t._x)
        lines = t.pretty_str().splitlines()
        assert len(lines) == 5
        assert lines[0] == "{"
        assert lines[-1] == "}"
        assert lines[1] == '  "a.b": 1,'

    def test_as_exactly(self):
        t = NestedDotDict({"zoo": {"animals": "jackets"}, "what": 0.1})
        assert t.exactly("zoo.animals", str) == "jackets"
        assert t.exactly("what", float) == 0.1
        with pytest.raises(TypeError):
            t.exactly("what", str)


if __name__ == "__main__":
    pytest.main()
