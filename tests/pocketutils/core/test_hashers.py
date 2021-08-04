import pytest

from pocketutils.core.exceptions import HashValidationError, IllegalStateError
from pocketutils.core.hashers import *

from . import load


raises = pytest.raises


class TestHasher:
    def test_to_write(self):
        path = load("hashable.txt")
        hasher = Hasher("sha1")
        x = hasher.to_write(path)
        # note: this is of the FILE (binary)
        expected = "cc27c28c5554ac4042688e121e8a8af6377195b0"
        try:
            assert isinstance(x, PostHashedFile)
            assert not x.files_exist
            assert x.hash_path.name == "hashable.txt.sha1"
            assert x.expected is None
            assert x.actual == expected
            assert not x.hash_path.exists()
            with pytest.raises(IllegalStateError):
                x.precomputed()
            x.write()
            assert x.hash_path.exists()
            assert x.hash_path.read_text(encoding="utf8") == expected
            y = x.precomputed()
            assert x.expected is None
            assert y.expected == expected
            assert y.matches
            y.match_or_raise()
        finally:
            x.hash_path.unlink(missing_ok=True)
        with pytest.raises(IllegalStateError):
            hasher.to_verify(path)

    def test_to_verify(self):
        hasher = Hasher("sha1")
        # note: this is of the FILE (binary)
        expected = "cc27c28c5554ac4042688e121e8a8af6377195b0"
        with pytest.raises(IllegalStateError):
            hasher.to_verify(load("hashable.txt"))
        x = hasher.to_verify(load("already_hashed.txt"))
        assert x.actual is not None
        assert x.actual == expected
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
