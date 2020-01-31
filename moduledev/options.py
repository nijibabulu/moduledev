from click import argument, option

from . import Config
from . import ModuleTree


def force_option(f):
    return option("--force", is_flag=True, default=False)(f)


def version_option(f):
    return option("--version", help="Specify the module version (default to latest)")(f)


def copy_option(f):
    return option(
        "--copy",
        is_flag=True,
        help="Copy the files contained in the path (default is create a symlink)",
    )(f)


def overwrite_option(f):
    return option(
        "--overwrite", is_flag=True, help="Overwrite an old path if it exists."
    )(f)


def module_arg(f):
    return argument("MODULE_NAME")(f)


def version_arg(f):
    return argument("VERSION", required=False)(f)


def setup_options(f):
    f = root_option(f)
    f = maintainer_option(f)
    return f


def path_add_options(f):
    f = argument("DST_PATH", required=False)(f)
    f = argument("SRC_PATH", required=False)(f)
    f = argument("VARIABLE_NAME")(f)
    f = module_arg(f)
    f = version_option(f)
    f = copy_option(f)
    f = overwrite_option(f)
    return f
