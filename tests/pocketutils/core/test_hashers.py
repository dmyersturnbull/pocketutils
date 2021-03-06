import pytest

from pocketutils.core.exceptions import HashValidationError, IllegalStateError
from pocketutils.core.hashers import *

raises = pytest.raises
from . import load


class TestHasher:
    def test_to_write(self):
        path = load("hashable.txt")
        hasher = Hasher("sha1")
        x = hasher.to_write(path)
        try:
            assert isinstance(x, PostHashedFile)
            assert not x.files_exist
            assert x.hash_path.name == "hashable.txt.sha1"
            assert x.expected is None
            assert x.actual == "03cfd743661f07975fa2f1220c5194cbaff48451"
            assert not x.hash_path.exists()
            with pytest.raises(IllegalStateError):
                x.precomputed()
            x.write()
            assert x.hash_path.exists()
            assert (
                x.hash_path.read_text(encoding="utf8") == "03cfd743661f07975fa2f1220c5194cbaff48451"
            )
            y = x.precomputed()
            assert x.expected is None
            assert y.expected == "03cfd743661f07975fa2f1220c5194cbaff48451"
            assert y.matches
            y.match_or_raise()
        finally:
            x.hash_path.unlink(missing_ok=True)
        with pytest.raises(IllegalStateError):
            hasher.to_verify(path)

    def test_to_verify(self):
        hasher = Hasher("sha1")
        with pytest.raises(IllegalStateError):
            hasher.to_verify(load("hashable.txt"))
        x = hasher.to_verify(load("already_hashed.txt"))
        assert x.actual is not None
        assert x.actual == "03cfd743661f07975fa2f1220c5194cbaff48451"
        assert x.actual == x.expected
        assert x.matches
        x.match_or_raise()

    def test_fail_verify(self):
        hasher = Hasher("sha1")
        x = hasher.to_verify(load("bad_hash.txt"))
        assert not x.matches
        with pytest.raises(HashValidationError):
            x.match_or_raise()


if __name__ == "__main__":
    pytest.main()
