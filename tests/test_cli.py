import pytest
import os
import click
import moduledev


@pytest.fixture
def root(tmpdir):
    root = tmpdir / "test"
    os.mkdir(root)
    return root


def test_help(runner):
    result = runner.invoke(moduledev.moduledev, [])
    assert result.exit_code == 0


def test_setup(runner, root):
    result = runner.invoke(moduledev.moduledev,
                           ["--root", root, "setup", "test"])
    import traceback
    traceback.print_tb(result.exc_info[2])
    assert result.exit_code == 0


def test_no_root(runner):
    result = runner.invoke(moduledev.moduledev, ["setup", "test"])
    assert type(result.exception) == SystemExit


def test_setup_bad_root(runner, root):
    result = runner.invoke(moduledev.moduledev, 
                           ["--root", root / "nonexistentdir", "setup", "test"])
    print(result.output)
    print(result.exception)
    assert type(result.exception) == SystemExit


def test_no_setup(runner, root):
    result = runner.invoke(moduledev.moduledev,
                           ["--root", root, "init", "package", "1.0"])
    assert type(result.exception) == SystemExit
    assert "moduledev setup" in str(result.exception)


def test_maintainer_in_config(runner, tmpdir, root):
    runner.invoke(moduledev.moduledev,
                  ["--root", root, "setup", "test"])
    runner.invoke(moduledev.moduledev,
                  ["config", "set", "maintainer", "testmaintainer"])
    result = runner.invoke(moduledev.moduledev,
                           ["--root", root, "init", "package", "1.0"])
    assert result.exit_code == 0
    assert 'set MAINTAINER "testmaintainer"' in "\n".join(
        open(tmpdir / "test" / "package" / ".modulefile").readlines())


def test_no_maintainer_warning(runner, root):
    runner.invoke(moduledev.moduledev,
                  ["--root", root, "setup", "test"])
    result = runner.invoke(moduledev.moduledev,
                           ["--root", root, "init", "package", "1.0"])
    assert result.exit_code == 0
    assert "maintainer not set" in result.output


def test_no_automatic_overwrite(runner, root):
    runner.invoke(moduledev.moduledev,
                  ["--root", root, "setup", "test"])
    result = runner.invoke(moduledev.moduledev,
                  ["--root", root, "init", "package", "1.0"])
    assert result.exit_code == 0
    result = runner.invoke(moduledev.moduledev,
                           ["--root", root, "init", "package", "1.0"])
    assert type(result.exception) == SystemExit
    assert "Use --force" in str(result.exception)


def test_config_get(runner):
    result = runner.invoke(moduledev.moduledev, ["config", "get"])
    assert result.exit_code == 0


def test_config_set(runner, tmpdir):
    result = runner.invoke(moduledev.moduledev,
                           ["config", "set", "setting", "value"])
    assert result.exit_code == 0

    result2 = runner.invoke(moduledev.moduledev,
                            ["config", "get", "setting"])
    assert result2.exit_code == 0
    assert result2.output == "value\n"


def setup_basic_package(runner, root):
    runner.invoke(moduledev.moduledev, ["config", "set", "root", str(root)])
    runner.invoke(moduledev.moduledev, ["setup", "test"])
    runner.invoke(moduledev.moduledev, ["config", "set", "maintainer", "testmt"])
    runner.invoke(moduledev.moduledev, ["init", "package", "1.0"])


def setup_path_package(runner, tmpdir, root):
    setup_basic_package(runner, root)
    os.mkdir(tmpdir / "bin")
    result = runner.invoke(moduledev.moduledev,
                           ["path", "add", "package", "PATH", 
                            str(tmpdir / "bin")])


def test_path_add(runner, tmpdir, root):
    setup_basic_package(runner, root)
    os.mkdir(tmpdir / "bin")
    result = runner.invoke(moduledev.moduledev,
                           ["path", "add", "package", "PATH", 
                            str(tmpdir / "bin")])
    assert result.exit_code == 0
    assert os.path.exists(root / "package" / "1.0" / "bin")
    assert "PATH $basedir/bin" in "\n".join(
        open(root / "package" / ".modulefile").readlines())


def test_path_add_nomodule(runner, tmpdir, root):
    runner.invoke(moduledev.moduledev,
                  ["config", "set", "root", str(root)])
    runner.invoke(moduledev.moduledev,
                  ["setup", "test"])
    os.mkdir(tmpdir / "bin")
    result = runner.invoke(moduledev.moduledev, 
                           ["path", "add", "--version", "1.0", "package", "PATH", str(tmpdir / "bin")])
    import traceback
    traceback.print_tb(result.exc_info[2])
    assert result.exit_code != 0
    assert type(result.exception) == SystemExit
    assert "Module package-1.0 does not exist" in str(result.exception)

def test_path_add_nooverwrite(runner, tmpdir, root):
    setup_basic_package(runner, root)
    os.mkdir(tmpdir / "bin")
    runner.invoke(moduledev.moduledev,
                           ["path", "add", "package", "PATH", str(tmpdir / "bin")])
    result = runner.invoke(moduledev.moduledev,
                           ["path", "add", "package", "PATH", str(tmpdir / "bin")])
    assert result.exit_code != 0
    assert "already exists" in str(result.output)


def test_path_add_overwrite_copy(runner, tmpdir, root):
    setup_basic_package(runner, root)
    os.mkdir(tmpdir / "bin")
    runner.invoke(moduledev.moduledev,
                  ["path", "add", "--copy", "package", "PATH", str(tmpdir / "bin")])
    os.mkdir(tmpdir / "bin" / "hi")
    result = runner.invoke(moduledev.moduledev,
                           ["path", "add", "--copy", "--overwrite", "package", "PATH", str(tmpdir / "bin")]) 
    assert result.exit_code == 0
    assert os.path.exists(root / "package" / "1.0" / "bin" / "hi")


def test_path_remove(runner, tmpdir, root):
    setup_basic_package(runner, root)
    os.mkdir(tmpdir / "bintest")
    runner.invoke(moduledev.moduledev,
                  ["path", "add", "package", "PATH", 
                   str(tmpdir / "bintest")])
    result = runner.invoke(moduledev.moduledev,
                           ["path", "remove", "package", "bintest"],
                           catch_exceptions=False)
    print(result.output)
    assert result.exit_code == 0
    assert not os.path.exists(root / "package" / "1.0" / "bintest" )
    assert not "bin" in "\n".join(
        open(root / "package" / ".modulefile").readlines())


def test_path_view(runner, tmpdir, root):
    setup_path_package(runner, tmpdir, root)
    result = runner.invoke(moduledev.moduledev, ["path", "view", "package"])
    assert result.exit_code == 0
    assert "bin" in result.output


def test_edit(runner, root):
    setup_basic_package(runner, root)
    result = runner.invoke(moduledev.moduledev, 
                           ["edit", "--editor", "cat", "package"])
    # TODO so far cannot capture stdout from the subcall it seems
    # can't test if the outoutp is ok
    assert result.exit_code == 0


def test_show(runner, root):
    setup_basic_package(runner, root)
    result = runner.invoke(moduledev.moduledev, ["show", "package"])
    assert result.exit_code == 0
    assert 'MAINTAINER' in result.output


def test_list(runner, root):
    setup_basic_package(runner, root)
    runner.invoke(moduledev.moduledev, ["init", "package", "1.1"])
    runner.invoke(moduledev.moduledev, ["init", "new_package", "1.0"])
    result = runner.invoke(moduledev.moduledev, ["list"])
    assert result.exit_code == 0
    assert len(result.output.strip().split("\n")) == 2
    result = runner.invoke(moduledev.moduledev, ["list", "--all"])
    assert result.exit_code == 0
    assert len(result.output.strip().split("\n")) == 3


def test_path(runner, root, tmpdir):
    setup_basic_package(runner, root)
    result = runner.invoke(moduledev.moduledev, ["location", "package"])
    assert result.exit_code == 0
    assert result.output.strip() == str(tmpdir / "test" / "package" / "1.0")
