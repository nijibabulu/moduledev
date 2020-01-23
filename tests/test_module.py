import os
import shutil

import pytest

import moduledev


def test_empty_module_tree(empty_module_tree):
    assert empty_module_tree.name is None
    assert empty_module_tree.valid() == False


def test_setup_module_tree(empty_module_tree):
    module_tree = empty_module_tree
    module_tree.setup("test")
    assert module_tree.valid() == True
    assert module_tree.name == "test"


def test_setup_module_tree_in_bad_dir(tmpdir):
    """Setup should fail if the directory does not exist, 
       if it is not writeable or there is anything in the 
       directory"""
    module_tree = moduledev.ModuleTree(tmpdir / "example")
    with pytest.raises(ValueError):
        module_tree.setup("test")

    os.mkdir(tmpdir / "example", mode=0o444)
    with pytest.raises(ValueError):
        module_tree.setup("test")

    os.chmod(tmpdir / "example", mode=0o777)
    os.mkdir(tmpdir / "example" / "dir_should_not_be_there")
    with pytest.raises(ValueError):
        module_tree.setup("test")


def test_corrupted_module_tree(empty_module_tree):
    os.mkdir(empty_module_tree.modulefile_dir())
    assert empty_module_tree.valid() == False
    os.mkdir(empty_module_tree.module_dir())
    assert empty_module_tree.valid() == False
    f = open(empty_module_tree._master_module_file_name("test"), "w")
    f.write("testcontent")
    f.close()
    assert empty_module_tree.valid() == True


def test_init_module(example_module, example_module_tree):
    builder = example_module_tree.init_module(example_module)
    assert builder.clean() == False
    assert builder.valid() == True


def test_category(example_module, tmpdir, example_module_tree):
    example_module.name = "categoried_package"
    example_module.category = "testcategory"
    builder = example_module_tree.init_module(example_module)
    loader = example_module_tree.load_module(
        example_module.name, example_module.version
    )
    assert loader.module.category == example_module.category


def test_unclean_init_module(example_module, example_module_tree):
    example_module_tree.init_module(example_module)
    with pytest.raises(ValueError):
        example_module_tree.init_module(example_module)


def test_unclean_init_module_overwrite(example_module, example_module_tree):
    example_module_tree.init_module(example_module)
    builder = example_module_tree.init_module(example_module, overwrite=True)
    assert builder.clean() == False
    assert builder.valid() == True


def test_init_categoried_module(example_module, example_module_tree):
    example_module.category = "acategory"
    builder = example_module_tree.init_module(example_module)
    assert builder.clean() == False
    assert builder.valid() == True


def test_init_versionlevel_module(example_module, example_module_tree):
    example_module.toplevel = False
    builder = example_module_tree.init_module(example_module)
    assert builder.clean() == False
    assert builder.valid() == True


def test_load_module(example_module, example_module_tree):
    builder = example_module_tree.init_module(example_module)
    loader = example_module_tree.load_module(
        example_module.name, example_module.version
    )
    assert loader.module.name == example_module.name


def test_load_module_empty(example_module_tree):
    with pytest.raises(ValueError):
        example_module_tree.load_module("nonexistent", "1.0")


def test_bad_module_file(example_module, example_module_tree):
    builder = example_module_tree.init_module(example_module)
    with open(builder.moduledotfile_path(), "a") as f:
        f.write("set TOOSHORTLINE\n")
    with pytest.raises(ValueError):
        example_module_tree.load_module(example_module.name, example_module.version)


def test_load_module(example_module, example_module_tree):
    builder = example_module_tree.init_module(example_module)
    with open(builder.moduledotfile_path(), "a") as f:
        f.write("set EXTRAVAR True")
    loader = example_module_tree.load_module(
        example_module.name, example_module.version
    )
    assert len(loader.module.extra_vars) == 1
    assert loader.module.extra_vars["EXTRAVAR"] == "True"


def test_empty_path(example_module, example_module_tree):
    builder = example_module_tree.init_module(example_module)
    fakepath = moduledev.Path("nonexistentpath", "prepend-path", "BIN")
    assert builder.path_exists(fakepath) == False


def test_add_path(example_module, example_module_tree, bindir):
    builder = example_module_tree.init_module(example_module)
    binpath = moduledev.Path("bin", "prepend-path", "PATH")
    builder.add_path(bindir, binpath)
    assert builder.path_exists(binpath) == True


def test_save_path(example_builder, bindir):
    binpath = moduledev.Path("bin", "prepend-path", "PATH")
    example_builder.add_path(bindir, binpath)
    example_builder.save_module_file()
    dotfile_text = "\n".join(open(example_builder.moduledotfile_path()).readlines())
    assert example_builder.path_exists(binpath) == True
    assert "bin" in dotfile_text
    assert "PATH" in dotfile_text


def test_save_path(example_builder, bindir):
    binpath = moduledev.Path("bin", "prepend-path", "PATH")
    example_builder.add_path(bindir, binpath)
    example_builder.save_module_file()

    example_builder.remove_path(binpath)
    example_builder.save_module_file()
    dotfile_text = "\n".join(open(example_builder.moduledotfile_path()).readlines())
    assert example_builder.path_exists(binpath) == False
    assert "bin" not in dotfile_text
    assert "PATH" not in dotfile_text


def test_extra_commands(example_module, example_module_tree):
    builder = example_module_tree.init_module(example_module)
    with open(builder.moduledotfile_path(), "a") as f:
        f.write("extracommand\n")
    loader = example_module_tree.load_module(
        example_module.name, example_module.version
    )
    loader.save_module_file()
    assert "extracommand" in "\n".join(open(builder.moduledotfile_path()).readlines())


def test_versions(example_module_tree, example_module):
    example_module.version = "1.0"
    builder1 = example_module_tree.init_module(example_module)
    example_module.version = "1.1"
    builder2 = example_module_tree.init_module(example_module)
    loader = example_module_tree.load_module(example_module.name)
    assert loader.module.version == "1.1"
    assert loader.available_versions() == ["1.0", "1.1"]


def test_module_find(example_module_tree, example_module):
    example_module.name = "hello"
    example_module.version = "1.0"
    builder1 = example_module_tree.init_module(example_module)
    example_module.version = "1.1"
    builder2 = example_module_tree.init_module(example_module)
    example_module.name = "hey"
    builder3 = example_module_tree.init_module(example_module)
    assert set(m.name for m in example_module_tree.modules()) == set(["hey", "hello"])
    assert len(list(example_module_tree.modules(all_versions=True))) == 3


def test_module_find_in_empty(empty_module_tree):
    assert empty_module_tree.valid() == False
    with pytest.raises(RuntimeError):
        list(empty_module_tree.modules())


def test_modulefile_path(example_builder, tmpdir):
    assert example_builder.modulefile_path() == os.path.join(
        example_builder.module_tree.root_dir,
        "modulefile",
        example_builder.module_tree.name,
        "test",
        "1.0",
    )


def test_save_unloded_module(example_module_tree):
    loader = moduledev.ModuleLoader(example_module_tree, "test_name", "test_version")
    with pytest.raises(RuntimeError):
        loader.save_module_file()


def test_missing_versioned_module(example_builder, tmpdir):
    loader = example_builder.module_tree.load_module(example_builder.name())
    for p in os.listdir(os.path.dirname(loader.modulefile_path())):
        shutil.rmtree(os.path.join(loader.module_base(), p))
    for p in os.listdir(loader.module_base()):
        if p != ".modulefile":
            shutil.rmtree(os.path.join(loader.module_base(), p))
    with pytest.raises(ValueError):
        loader.version()
