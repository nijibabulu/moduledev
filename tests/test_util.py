import os
import stat

import pytest

import moduledev


def test_version_key():
    assert moduledev.version_key("1.2.0") > moduledev.version_key("0.2.5")
    assert moduledev.version_key("1.2.0b") > moduledev.version_key("1.2.0a")
    assert moduledev.version_key("b") > moduledev.version_key("a")


def test_writeable_dir(tmpdir):
    assert moduledev.writeable_dir(tmpdir / "test") == False
    with open(tmpdir / "file", "w") as f:
        f.write("text")
    assert moduledev.writeable_dir(tmpdir / "file") == False
    os.mkdir(tmpdir / "test")
    os.chmod(tmpdir / "test", stat.S_IRUSR)
    assert moduledev.writeable_dir(tmpdir / "test") == False


def test_valid_version():
    assert moduledev.valid_version("b1.0") == False
