import os

import pytest
from click.testing import CliRunner

import moduledev


@pytest.fixture
def runner(tmpdir):
    return CliRunner(env={"HOME": str(tmpdir)})


@pytest.fixture
def empty_config(tmpdir):
    cfg = moduledev.Config(_filename=tmpdir / "config.yaml")
    return cfg


@pytest.fixture
def example_config(tmpdir):
    cfg = moduledev.Config(_filename=tmpdir / "config.yaml")
    cfg.set("maintainer", "Example <example@example.com>")
    cfg.set("package_name", "package")
    cfg.set("helptext", "some help")
    cfg.set("description", "a description")
    return cfg


@pytest.fixture
def empty_module_tree(tmpdir):
    os.mkdir(tmpdir / "example")
    module_tree = moduledev.ModuleTree(tmpdir / "example")
    return module_tree


@pytest.fixture
def example_module_tree(empty_module_tree):
    empty_module_tree.setup("test")
    return empty_module_tree


@pytest.fixture
def bindir(tmpdir):
    binpath = tmpdir / "bin"
    os.mkdir(binpath)
    with open(binpath / "script", "w") as f:
        f.write("#!/bin/bash\necho Hello!\n")
    return binpath


@pytest.fixture
def example_module(example_module_tree):
    module = moduledev.Module(
        root=example_module_tree,
        name="test",
        version="1.0",
        maintainer="Test Maintainer <test@test.com>",
        helptext="A test module",
        description="The description of a test module",
    )
    return module


@pytest.fixture
def example_builder(example_module, example_module_tree):
    return example_module_tree.init_module(example_module)


_data_dir = os.path.join(os.path.dirname(__file__), "files")


@pytest.fixture
def data_dir():
    return _data_dir
