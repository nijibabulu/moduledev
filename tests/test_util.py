import os
import stat

import moduledev


def test_version_key():
    assert moduledev.version_key("1.2.0") > moduledev.version_key("0.2.5")
    assert moduledev.version_key("1.2.0b") > moduledev.version_key("1.2.0a")
    assert moduledev.version_key("b") > moduledev.version_key("a")


def test_writeable_dir(tmpdir):
    assert not moduledev.writeable_dir(tmpdir / "test")
    with open(tmpdir / "file", "w") as f:
        f.write("text")
    assert not moduledev.writeable_dir(tmpdir / "file")
    os.mkdir(tmpdir / "test")
    os.chmod(tmpdir / "test", stat.S_IRUSR)
    assert not moduledev.writeable_dir(tmpdir / "test")


def test_valid_version():
    assert not moduledev.valid_version("b1.0")


def test_package_name():
    assert moduledev.valid_package_name("abc1234-_")
    assert not moduledev.valid_package_name("abc1234 ")
    assert not moduledev.valid_package_name("abc*&%^*&%1234")
