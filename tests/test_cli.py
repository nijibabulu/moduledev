import os

import pytest

from moduledev.cli import mdcli


@pytest.fixture
def root(tmpdir):
    root = tmpdir / "test"
    os.mkdir(root)
    return root


def test_help(runner):
    result = runner.invoke(mdcli, [])
    assert result.exit_code == 0


def test_setup(runner, root):
    result = runner.invoke(mdcli, ["--root", root, "setup", "test"])
    import traceback

    traceback.print_tb(result.exc_info[2])
    assert result.exit_code == 0


def test_no_root(runner):
    result = runner.invoke(mdcli, ["setup", "test"])
    assert type(result.exception) == SystemExit


def test_setup_bad_root(runner, root):
    result = runner.invoke(mdcli, ["--root", root / "nonexistentdir", "setup", "test"])
    assert type(result.exception) == SystemExit


def test_no_setup(runner, root):
    result = runner.invoke(mdcli, ["--root", root, "init", "package", "1.0"])
    assert type(result.exception) == SystemExit
    assert "moduledev setup" in str(result.exception)


def test_init_cli(runner, tmpdir, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    result = runner.invoke(
        mdcli, ["--root", root, "init", "package", "1.0", "description", "helptext"]
    )
    assert result.exit_code == 0
    assert 'set DESCRIPTION "description"' in "\n".join(
        open(tmpdir / "test" / "package" / ".modulefile").readlines()
    )
    assert 'set HELPTEXT "helptext"' in "\n".join(
        open(tmpdir / "test" / "package" / ".modulefile").readlines()
    )
    assert 'set MAINTAINER "nomaintainer"' in "\n".join(
        open(tmpdir / "test" / "package" / ".modulefile").readlines()
    )


def test_init_two_versions(runner, tmpdir, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    runner.invoke(
        mdcli, ["--root", root, "init", "package", "1.0", "description", "helptext"]
    )
    result = runner.invoke(mdcli, ["--root", root, "init", "package", "1.1"])
    assert result.exit_code == 0
    assert "already exists" in result.output
    assert 'set DESCRIPTION "description"' in "\n".join(
        open(tmpdir / "test" / "package" / ".modulefile").readlines()
    )
    assert 'set HELPTEXT "helptext"' in "\n".join(
        open(tmpdir / "test" / "package" / ".modulefile").readlines()
    )
    assert 'set MAINTAINER "nomaintainer"' in "\n".join(
        open(tmpdir / "test" / "package" / ".modulefile").readlines()
    )


def test_init_two_versions_with_paths(runner, tmpdir, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    runner.invoke(
        mdcli, ["--root", root, "init", "package", "1.0", "description", "helptext"]
    )
    os.mkdir(tmpdir / "bin")
    runner.invoke(
        mdcli,
        ["--root", root, "path", "prepend", "package", "PATH", str(tmpdir / "bin/")],
    )
    result = runner.invoke(mdcli, ["--root", root, "init", "package", "1.1"])
    assert result.exit_code == 0
    assert "already exists" in result.output
    assert "defines paths which are not yet present" in result.output
    assert "prepend-path PATH $basedir/bin" in result.output


def test_init_detached_cli(runner, tmpdir, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    result = runner.invoke(
        mdcli,
        [
            "--root",
            root,
            "init",
            "--detached",
            "package",
            "1.0",
            "description",
            "helptext",
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(tmpdir / "test" / "package" / "1.0" / ".modulefile")
    assert 'set DESCRIPTION "description"' in "\n".join(
        open(tmpdir / "test" / "package" / "1.0" / ".modulefile").readlines()
    )
    assert 'set HELPTEXT "helptext"' in "\n".join(
        open(tmpdir / "test" / "package" / "1.0" / ".modulefile").readlines()
    )
    assert 'set MAINTAINER "nomaintainer"' in "\n".join(
        open(tmpdir / "test" / "package" / "1.0" / ".modulefile").readlines()
    )


def test_newlines_in_info_strings(runner, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    result = runner.invoke(
        mdcli, ["--root", root, "init", "package", "1.0", "helptext\ntoolong"]
    )
    assert "Newlines not allowed" in result.output
    assert result.exit_code == 0
    result = runner.invoke(mdcli, ["--root", root, "show", "package"])
    assert result.exit_code == 0
    assert "parse error" not in result.output
    assert "toolong" in result.output

    result = runner.invoke(
        mdcli,
        [
            "--root",
            root,
            "init",
            "packagedesc",
            "1.0",
            "helptext",
            "description\ntoolong",
        ],
    )
    assert "Newlines not allowed" in result.output
    assert result.exit_code == 0
    result = runner.invoke(mdcli, ["--root", root, "show", "packagedesc"])
    assert result.exit_code == 0
    assert "parse error" not in result.output
    assert "toolong" in result.output

    runner.invoke(mdcli, ["config", "set", "maintainer", "maintainer\ntoolong"])
    result = runner.invoke(mdcli, ["--root", root, "init", "packagemaint", "1.0",])
    assert "Newlines not allowed" in result.output
    assert result.exit_code == 0
    result = runner.invoke(mdcli, ["--root", root, "show", "packagedesc"])
    assert result.exit_code == 0
    assert "parse error" not in result.output
    assert "toolong" in result.output


def test_trailing_shash(runner, tmpdir, root):
    runner.invoke(mdcli, ["config", "set", "root", str(root)])
    runner.invoke(mdcli, ["setup", "test"])
    runner.invoke(mdcli, ["init", "package", "1.0"])
    os.mkdir(tmpdir / "bin")
    result = runner.invoke(
        mdcli, ["path", "append", "package", "PATH", str(tmpdir / "bin/")]
    )
    assert result.exit_code == 0
    assert os.path.exists(tmpdir / "test" / "package" / "1.0" / "bin")


def test_broken_link(runner, root, tmpdir):
    # this has a problem with a broken link because path_exists returns false
    # when it uses os.path.exists() under the hood.
    runner.invoke(mdcli, ["config", "set", "root", str(root)])
    runner.invoke(mdcli, ["setup", "test"])
    runner.invoke(mdcli, ["init", "package", "1.0"])
    os.mkdir(tmpdir / "bin")
    runner.invoke(mdcli, ["path", "append", "package", "PATH", str(tmpdir / "bin")])
    os.rmdir(tmpdir / "bin")
    os.makedirs(tmpdir / "b" / "bin")
    result = runner.invoke(
        mdcli,
        ["path", "append", "--overwrite", "package", "PATH", str(tmpdir / "b" / "bin")],
    )

    assert result.exit_code == 0
    assert os.path.exists(tmpdir / "test" / "package" / "1.0" / "bin")


def test_bad_version(runner, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    result = runner.invoke(mdcli, ["--root", root, "init", "package", "b1.0"])
    assert "not a valid version" in result.output
    assert type(result.exception) == SystemExit


def test_bad_package_name(runner, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    result1 = runner.invoke(mdcli, ["--root", root, "init", "abc1234 ", "1.0"])
    result2 = runner.invoke(mdcli, ["--root", root, "init", "abc*&%^*&%1234", "1.0"])

    assert type(result1.exception) == SystemExit
    assert type(result2.exception) == SystemExit

    assert "not a valid package" in result1.output
    assert "not a valid package" in result2.output


def test_maintainer_in_config(runner, tmpdir, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    runner.invoke(mdcli, ["config", "set", "maintainer", "testmaintainer"])
    result = runner.invoke(mdcli, ["--root", root, "init", "package", "1.0"])
    assert result.exit_code == 0
    assert 'set MAINTAINER "testmaintainer"' in "\n".join(
        open(tmpdir / "test" / "package" / ".modulefile").readlines()
    )


def test_no_maintainer_warning(runner, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    result = runner.invoke(mdcli, ["--root", root, "init", "package", "1.0"])
    assert result.exit_code == 0
    assert "maintainer not set" in result.output


def test_no_automatic_overwrite(runner, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    result = runner.invoke(mdcli, ["--root", root, "init", "package", "1.0"])
    assert result.exit_code == 0
    result = runner.invoke(mdcli, ["--root", root, "init", "package", "1.0"])
    assert type(result.exception) == SystemExit
    assert "Use --force" in str(result.exception)


def test_category_init(runner, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    result = runner.invoke(
        mdcli, ["--root", root, "init", "--category", "testcategory", "package", "1.0"],
    )
    assert result.exit_code == 0


def test_remove(runner, root):
    runner.invoke(mdcli, ["--root", root, "setup", "test"])
    runner.invoke(mdcli, ["--root", root, "init", "package", "1.0"])
    result = runner.invoke(mdcli, ["--root", root, "rm", "--force", "package"])
    assert result.exit_code == 0
    result = runner.invoke(mdcli, ["--root", root, "list"])
    assert result.exit_code == 0
    assert len(result.output.strip()) == 0


def test_config_get(runner):
    result = runner.invoke(mdcli, ["config", "get"])
    assert result.exit_code == 0


def test_config_set(runner, tmpdir):
    result = runner.invoke(mdcli, ["config", "set", "setting", "value"])
    assert result.exit_code == 0

    result2 = runner.invoke(mdcli, ["config", "get", "setting"])
    assert result2.exit_code == 0
    assert result2.output == "value\n"


def setup_basic_package(runner, root):
    runner.invoke(mdcli, ["config", "set", "root", str(root)])
    runner.invoke(mdcli, ["setup", "test"])
    runner.invoke(mdcli, ["config", "set", "maintainer", "testmt"])
    runner.invoke(mdcli, ["init", "package", "1.0"])


def setup_path_package(runner, tmpdir, root, action="append"):
    setup_basic_package(runner, root)
    os.mkdir(tmpdir / "bin")
    return runner.invoke(
        mdcli, ["path", action, "package", "PATH", str(tmpdir / "bin")]
    )


def test_path_append(runner, tmpdir, root):
    setup_basic_package(runner, root)
    os.mkdir(tmpdir / "bin")
    result = runner.invoke(
        mdcli, ["path", "append", "package", "PATH", str(tmpdir / "bin")]
    )
    assert result.exit_code == 0
    assert os.path.exists(root / "package" / "1.0" / "bin")
    assert "PATH $basedir/bin" in "\n".join(
        open(root / "package" / ".modulefile").readlines()
    )
    assert "append-path PATH $basedir/bin" in "\n".join(
        open(root / "package" / ".modulefile").readlines()
    )


def test_path_prepend(runner, tmpdir, root):
    result = setup_path_package(runner, tmpdir, root, action="prepend")
    assert result.exit_code == 0
    assert os.path.exists(root / "package" / "1.0" / "bin")
    assert "prepend-path PATH $basedir/bin" in "\n".join(
        open(root / "package" / ".modulefile").readlines()
    )


def test_path_setenv(runner, tmpdir, root):
    result = setup_path_package(runner, tmpdir, root, action="setenv")
    assert result.exit_code == 0
    assert os.path.exists(root / "package" / "1.0" / "bin")
    assert "setenv PATH $basedir/bin" in "\n".join(
        open(root / "package" / ".modulefile").readlines()
    )


def test_path_append_dest(runner, tmpdir, root):
    setup_basic_package(runner, root)
    os.mkdir(tmpdir / "bin")
    result = runner.invoke(
        mdcli, ["path", "append", "package", "PATH", str(tmpdir / "bin"), "testbin"]
    )
    assert result.exit_code == 0
    assert os.path.exists(root / "package" / "1.0" / "testbin")
    assert "PATH $basedir/testbin" in "\n".join(
        open(root / "package" / ".modulefile").readlines()
    )


def test_path_append_notexists(runner, tmpdir, root):
    setup_basic_package(runner, root)
    result = runner.invoke(
        mdcli, ["path", "append", "package", "PATH", str(tmpdir / "bin")]
    )
    assert result.exit_code != 0
    assert type(result.exception) == SystemExit
    assert "does not exist" in str(result.exception)


def test_path_append_nomodule(runner, tmpdir, root):
    runner.invoke(mdcli, ["config", "set", "root", str(root)])
    runner.invoke(mdcli, ["setup", "test"])
    os.mkdir(tmpdir / "bin")
    result = runner.invoke(
        mdcli,
        ["path", "append", "--version", "1.0", "package", "PATH", str(tmpdir / "bin")],
    )
    import traceback

    traceback.print_tb(result.exc_info[2])
    assert result.exit_code != 0
    assert type(result.exception) == SystemExit
    assert "Module package-1.0 does not exist" in str(result.exception)


def test_path_append_nooverwrite(runner, tmpdir, root):
    setup_basic_package(runner, root)
    os.mkdir(tmpdir / "bin")
    runner.invoke(mdcli, ["path", "append", "package", "PATH", str(tmpdir / "bin")])
    result = runner.invoke(
        mdcli, ["path", "append", "package", "PATH", str(tmpdir / "bin")]
    )
    assert result.exit_code != 0
    assert "already exists" in str(result.output)


def test_path_append_overwrite_copy(runner, tmpdir, root):
    setup_basic_package(runner, root)
    os.mkdir(tmpdir / "bin")
    runner.invoke(
        mdcli, ["path", "append", "--copy", "package", "PATH", str(tmpdir / "bin")],
    )
    os.mkdir(tmpdir / "bin" / "hi")
    result = runner.invoke(
        mdcli,
        [
            "path",
            "append",
            "--copy",
            "--overwrite",
            "package",
            "PATH",
            str(tmpdir / "bin"),
        ],
    )
    assert result.exit_code == 0
    assert os.path.exists(root / "package" / "1.0" / "bin" / "hi")


def test_path_remove(runner, tmpdir, root):
    setup_basic_package(runner, root)
    os.mkdir(tmpdir / "bintest")
    runner.invoke(mdcli, ["path", "append", "package", "PATH", str(tmpdir / "bintest")])
    result = runner.invoke(
        mdcli, ["path", "rm", "package", "bintest"], catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert not os.path.exists(root / "package" / "1.0" / "bintest")
    assert "bin" not in "\n".join(open(root / "package" / ".modulefile").readlines())


def test_path_list(runner, tmpdir, root):
    setup_path_package(runner, tmpdir, root)
    result = runner.invoke(mdcli, ["path", "list", "package"])
    assert result.exit_code == 0
    assert "bin" in result.output


def test_path_append_unparseable_file(runner, tmpdir, root):
    setup_path_package(runner, tmpdir, root)
    with open(root / "package" / ".modulefile", "a") as f:
        f.write('unparseable "line\n')
    os.mkdir(tmpdir / "unwriteabletest")
    result = runner.invoke(
        mdcli, ["path", "append", "package", "PATH", str(tmpdir / "unwriteabletest")]
    )
    assert result.exit_code == 1
    assert type(result.exception) == SystemExit
    assert "parse error" in result.output


def test_path_list_unparseable_file(runner, tmpdir, root):
    setup_path_package(runner, tmpdir, root)
    with open(root / "package" / ".modulefile", "a") as f:
        f.write('unparseable "line\n')
    os.mkdir(tmpdir / "unwriteabletest")
    result = runner.invoke(mdcli, ["path", "list", "package"])
    assert result.exit_code == 0
    assert "parse error" in result.output


def test_list_with_unparseable_file(runner, tmpdir, root):
    setup_path_package(runner, tmpdir, root)
    with open(root / "package" / ".modulefile", "a") as f:
        f.write('unparseable "line\n')
    os.mkdir(tmpdir / "unwriteabletest")
    result = runner.invoke(mdcli, ["list"])
    assert result.exit_code == 0


def test_edit(runner, root):
    setup_basic_package(runner, root)
    result = runner.invoke(mdcli, ["edit", "--editor", "cat", "package"])
    # TODO so far cannot capture stdout from the subcall it seems
    # can't test if the outoutp is ok
    assert result.exit_code == 0


def test_show(runner, root):
    setup_basic_package(runner, root)
    result = runner.invoke(mdcli, ["show", "package"])
    assert result.exit_code == 0
    assert "MAINTAINER" in result.output


def test_list(runner, root):
    setup_basic_package(runner, root)
    runner.invoke(mdcli, ["init", "package", "1.1"])
    runner.invoke(mdcli, ["init", "new_package", "1.0"])
    result = runner.invoke(mdcli, ["list"])
    assert result.exit_code == 0
    assert len(result.output.strip().split("\n")) == 2
    result = runner.invoke(mdcli, ["list", "--all"])
    assert result.exit_code == 0
    assert len(result.output.strip().split("\n")) == 3


def test_path(runner, root, tmpdir):
    setup_basic_package(runner, root)
    result = runner.invoke(mdcli, ["location", "package"])
    assert result.exit_code == 0
    assert result.output.strip() == str(tmpdir / "test" / "package" / "1.0")
