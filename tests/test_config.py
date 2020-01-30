import os

import pytest

import moduledev


def test_construct(empty_config):
    pass


def test_load(data_dir):
    cfg = moduledev.Config(_filename=os.path.join(data_dir, "good_config.yaml"))
    assert cfg.get("maintainer") == "Example <example@example.com>"


def test_makedirs_failure(tmpdir):
    baddir = tmpdir / "baddir"
    os.mkdir(str(baddir), mode=0o444)
    cfg = moduledev.Config(_filename=os.path.join(baddir, "subdir", "config.yml"))
    with pytest.raises(SystemExit):
        cfg.save()
    os.chmod(baddir, mode=0o777)


def test_makeconfig_failure(tmpdir):
    baddir = tmpdir / "baddir"
    os.mkdir(str(baddir), mode=0o444)
    cfg = moduledev.Config(_filename=os.path.join(baddir, "config.yml"))
    with pytest.raises(SystemExit):
        cfg.save()
    os.chmod(baddir, mode=0o777)


def test_empty_dump(empty_config):
    assert empty_config.dump() == ""


def test_unformatted_config(example_config):
    assert example_config.dump("package_name") == "package"


def test_load_nothing():
    cfg = moduledev.Config(_filename="nonexistentfile")
    assert len(cfg.config) == 0


def test_load_unparseable(data_dir):
    with pytest.raises(SystemExit):
        moduledev.Config(_filename=os.path.join(data_dir, "bad_config.yaml"))


def test_save_load(empty_config):
    empty_config.set("test_setting", "test_value")
    empty_config.save()

    loaded_config = moduledev.Config(_filename=empty_config.filename())
    assert loaded_config.get("test_setting") == "test_value"
