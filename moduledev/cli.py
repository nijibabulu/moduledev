import os
from subprocess import call

import click

from . import Config, Module, ModuleTree, Path, util
from ._color import (
    GROUP_CLR,
    INFO_CLR,
    INTERACT_CLR,
    SETUP_CLR,
    ModuleDevCommand,
    ModuleDevGroup,
)
from ._options import (
    force_option,
    module_arg,
    path_add_options,
    version_arg,
    version_option,
)

EDITOR = os.environ.get("EDITOR", "vim")


def log_error(err):
    click.secho(err, fg="red", err=True)


def log_error_and_wait_for_confirmation(err):  # pragma: no cover
    log_error(err)
    click.pause(err=True)


def log_error_and_exit(err):
    log_error(err)
    raise ValueError


def warn_unfulfilled_paths(module_tree, module, parse_error_handler=log_error):
    """
    Alert the user of any paths defined in the module's modulefile but not
    existing in the current module directory.
    """
    loader = module_tree.load_module(module.name, module.version, parse_error_handler)
    unfulfilled_paths = [
        path for path in loader.module.paths if not loader.path_exists(path)
    ]
    if len(unfulfilled_paths):
        click.secho(
            f"The module {module.name}-{module.version} defines paths which are not yet present:",
            fg="red",
        )
        for unfulfilled_path in unfulfilled_paths:
            click.secho(f"{unfulfilled_path}", fg="red")


class CliCfg:
    def __init__(self, root, maintainer):
        self.config, self.root, self.maintainer = (Config(), root, maintainer)

    def check_root(self):
        """
        Check that the root exists and return it

        :return: a path to the root
        """
        result = self.root or self.config.get("root")
        if result is None:
            raise SystemExit(
                "No module root set. Add it to the configuration "
                "or specify it on the commandline"
            )

        return result

    def check_module_tree(self):
        """
        Check that the root exists and has a valid module tree.

        :return: the resulting module tree.
        """
        used_root = self.check_root()
        module_tree = ModuleTree(used_root)
        if not module_tree.valid():
            raise SystemExit(f"Module tree not set up. Run moduledev setup first.")
        return module_tree

    def check_module(
        self, module_tree, module_name, version, parse_error_handler=log_error
    ):
        """
        Check for the presence of a module on the module tree and return it if it
        exists. If it does not exist, inform the user and exit.
        """

        if not module_tree.module_exists(module_name, version):
            module_display = f"{module_name}"
            if version is not None:
                module_display += f"-{version}"
            raise SystemExit(f"Module {module_display} does not exist.")
        try:
            loader = module_tree.load_module(module_name, version, parse_error_handler)
        except ValueError as e:
            raise SystemExit(f"Error loading module: {e}")
        return loader


@click.group(cls=ModuleDevGroup)
@click.option(
    "--maintainer", help="Set the package maintainer, overriding configuration"
)
@click.option("--root", help="Set the module root directory, overriding configuration")
@click.pass_context
def mdcli(ctx, maintainer, root):
    """
    Create and maintain environment modules.  Create an environment module
    repository with the setup subcommand. Initialize a new module with the
    init subcommand. Add paths with the update subcommand. Adjust global
    configuration with the config subcommand.
    """
    ctx.obj = CliCfg(root, maintainer)


@mdcli.command(cls=ModuleDevCommand, short_help_color=SETUP_CLR)
@force_option
@click.option(
    "--category", help="Set a category for the module (defaults to the repo name)"
)
@click.option(
    "--shared/--detached",
    "shared",
    default=True,
    help="Use a shared module file (default) that has the same "
    "relative paths and description as all versions of the package, "
    "or a detached version-specific module file.",
)
@module_arg
@click.argument("VERSION")
@click.argument("DESCRIPTION", default="", required=False)
@click.argument("HELPTEXT", default="", required=False)
@click.pass_context
def init(ctx, shared, force, module_name, version, helptext, description, category):
    """
    Create a new module or add a module version. For example, the
    command

    moduledev init --root /path/to/root hello 1.0

    creates the folloing directory structure:

    \b
    /path/to/root
    |-- hello
    |   |-- .modulefile
    |   |-- 1.0
    `-- modulefile
        `-- eg
            `-- hello
                |-- 1.0 -> /path/to/root/module/example_modulefile

    Subsequently paths can be added to the module structure.
    Note moduledev setup must be run before this command.
    """
    maintainer = ctx.obj.maintainer or ctx.obj.config.get("maintainer")
    if maintainer is None:
        click.echo("Warning: maintainer not set; defaulting to nomaintainer", err=True)
        maintainer = "nomaintainer"

    def check_string_for_newlines(name, string):
        if "\n" in string:
            click.secho(
                f"Newlines not allowed in {name}. Replacing with spaces", fg="red"
            )
        return string.replace("\n", " ")

    if not util.valid_version(version):
        click.secho(
            f'"{version}" is not a valid version. Versions may '
            f"contain tokens separated by .s and -s. Tokens may contain"
            f"a number, a character, or a number followed by a character",
            fg="red",
        )
        raise SystemExit("")

    if not util.valid_package_name(module_name):
        click.secho(
            f'"{module_name}" is not a valid package name. Package names '
            f"may contain only alphanumeric characters and underscores.",
            fg="red",
        )
        raise SystemExit("")

    module_tree = ctx.obj.check_module_tree()
    shared_module = module_tree.shared_module(
        module_name, version, error_handler=log_error
    )
    if shared and shared_module is not None:
        click.secho("Module file already exists. Not updating.", fg="red")
        m = shared_module
        m.version = version
    else:
        m = Module(
            module_tree,
            module_name,
            version,
            check_string_for_newlines("maintainer", maintainer),
            check_string_for_newlines("helptext", helptext),
            check_string_for_newlines("description", description),
            category=category,
            shared=shared,
        )
    if not module_tree.module_clean(m) and not force:
        raise SystemExit(
            f"Some file exist where the module should be "
            f"installed. Use --force to overwrite them."
        )
    module_tree.init_module(m, overwrite=force)
    warn_unfulfilled_paths(module_tree, m)


@mdcli.command(cls=ModuleDevCommand, short_help_color=SETUP_CLR)
@force_option
@module_arg
@version_arg
@click.pass_context
def rm(ctx, module_name, force, version):
    """Remove a module. Will default to the latest version of the module if no
    version is provided."""
    module_tree = ctx.obj.check_module_tree()
    loader = ctx.obj.check_module(module_tree, module_name, version)
    if not force:  # pragma: no cover
        if not click.confirm(f"Really delete {loader.module}?  "):
            raise SystemExit("Operation cancelled by user")
    loader.clear()


@mdcli.command(cls=ModuleDevCommand, short_help_color=SETUP_CLR)
@click.argument("REPO_NAME")
@click.pass_context
def setup(ctx, repo_name):
    """
    Set up the root directory structure. The root
    itself should be set either here in the configuration (as "root"). This will
    create new directories of the following structure:

    \b
    ${ROOT}
    |-- module
    |   `-- ${REPO_NAME}_modulefile
    `-- modulefile

    The ${REPO_NAME}_modulefile contains boilerplate header for all modules and will
    be invoked for every module that is created. The file itself searches for
    the modulefile specific to the module. See the init subcommand for details.
    """
    used_root = ctx.obj.check_root()
    module_tree = ModuleTree(used_root)
    if not module_tree.can_setup(repo_name):
        click.secho(
            "Module tree root must be set up in an empty, "
            "writeable directory. Change the root location\neither "
            "with the --root option or via moduledev config.",
            bold=True,
            fg="red",
        )
        raise SystemExit(" ")
    module_tree.setup(repo_name)
    click.echo("Module repository successfully setup in\n")
    click.secho(f"{used_root}\n", bold=True)
    click.echo(
        "You can now start using the repository by adding the "
        "following to your ~/.bashrc (or whatever login scripts "
        "you use):\n"
    )
    click.secho(f"module use --append {used_root}/modulefile", bold=True)
    click.secho(f"module use --append {used_root}/modulefile/{repo_name}", bold=True)
    click.echo(
        "If you haven't already, it would be useful to configure "
        "a global maintainer and root:\n"
    )
    click.secho(f"moduledev config set root {used_root}", bold=True)
    click.secho(f'moduledev config set maintainer "Me <me@me.me>"\n', bold=True)
    click.echo("Create a new module using ", nl=False)
    click.secho("module init", bold=True, nl=False)
    click.echo("\n")


@mdcli.group(cls=ModuleDevGroup, short_help_color=GROUP_CLR)
def config():
    """Manage the global configuration."""
    pass


@config.command(cls=ModuleDevCommand, short_help_color=INFO_CLR)
@click.argument("SETTING", required=False)
@click.pass_context
def get(ctx, setting):
    """Show a setting from the configuration. If no setting is given, dump all settings
       in YAML format"""
    print(f"{ctx.obj.config.dump(setting)}")


@config.command(cls=ModuleDevCommand, short_help_color=SETUP_CLR)
@click.argument("SETTING")
@click.argument("VALUE")
@click.pass_context
def set(ctx, setting, value):
    """Give a configuration setting a value."""
    ctx.obj.config.set(setting, value)
    ctx.obj.config.save()


@mdcli.group(cls=ModuleDevGroup, short_help_color=GROUP_CLR)
def path():
    """Add, remove, or show module paths"""
    pass


def path_add(
    ctx, version, module_name, variable_name, src_path, dst_path, copy, overwrite, verb,
):
    if not os.path.exists(src_path):
        raise SystemExit(f"Cannot add path: source path {src_path} does not exist.")
    if dst_path is None:
        dst_path = src_path
    module_tree = ctx.obj.check_module_tree()
    loader = ctx.obj.check_module(
        module_tree, module_name, version, parse_error_handler=log_error_and_exit
    )
    path_obj = Path(dst_path, f"{verb}", variable_name)
    if loader.path_exists(path_obj):
        if overwrite:
            loader.remove_path(path_obj)
        else:
            raise SystemExit(
                f"Path {path_obj.path} already exists. " f"Use --overwrite to force."
            )
    loader.add_path(src_path, path_obj, not copy)
    loader.save_module_file()
    warn_unfulfilled_paths(module_tree, loader.module, log_error)


@path.command(cls=ModuleDevCommand, short_help_color=SETUP_CLR)
@path_add_options
@click.pass_context
def prepend(*args, **kwargs):
    """Prepend a path to a path variable in a module"""
    path_add(*args, **kwargs, verb="prepend-path")


@path.command(cls=ModuleDevCommand, short_help_color=SETUP_CLR)
@path_add_options
@click.pass_context
def append(*args, **kwargs):
    """Append a path to a path variable in a module"""
    path_add(*args, **kwargs, verb="append-path")


@path.command(cls=ModuleDevCommand, short_help_color=SETUP_CLR)
@path_add_options
@click.pass_context
def setenv(*args, **kwargs):
    """Set a path name to a single value. This implies that the path is mutually
       exclusive with any other value."""
    path_add(*args, **kwargs, verb="setenv")


@path.command(name="rm", cls=ModuleDevCommand, short_help_color=SETUP_CLR)
@version_option
@module_arg
@click.argument("SRC_PATH")
@click.pass_context
def path_rm(ctx, module_name, src_path, version):
    """Remove a path from a module"""
    module_tree = ctx.obj.check_module_tree()
    loader = ctx.obj.check_module(
        module_tree, module_name, version, parse_error_handler=log_error_and_exit
    )
    path_obj = Path(src_path)
    loader.remove_path(path_obj)
    loader.save_module_file()


@path.command(name="list", cls=ModuleDevCommand, short_help_color=INFO_CLR)
@version_option
@click.argument("MODULE_NAME")
@click.pass_context
def path_list(ctx, module_name, version):
    """List all paths in a module"""
    module_tree = ctx.obj.check_module_tree()
    loader = ctx.obj.check_module(module_tree, module_name, version)
    print(
        "\n".join(
            f"{str(p)} -> {p.resolve(loader.module_path())}"
            for p in loader.module.paths
        )
    )


@mdcli.command(cls=ModuleDevCommand, short_help_color=INTERACT_CLR)
@click.option("--editor", help="Specify the editor", default=EDITOR, show_default=True)
@version_option
@module_arg
@click.pass_context
def edit(ctx, module_name, version, editor):
    """Edit the module file for a package"""
    module_tree = ctx.obj.check_module_tree()
    loader = ctx.obj.check_module(
        module_tree, module_name, version, log_error_and_wait_for_confirmation
    )
    call([editor, loader.moduledotfile_path()])


@mdcli.command(cls=ModuleDevCommand, short_help_color=INFO_CLR)
@version_option
@click.argument("MODULE_NAME")
@click.pass_context
def show(ctx, module_name, version):
    """Show the contents of a module's module file"""
    module_tree = ctx.obj.check_module_tree()
    loader = ctx.obj.check_module(module_tree, module_name, version)
    click.echo("".join(open(loader.moduledotfile_path()).readlines()))


@mdcli.command(cls=ModuleDevCommand, short_help_color=INFO_CLR)
@click.option(
    "--all",
    "all_versions",
    is_flag=True,
    help="Show all versions of each module (default is to show "
    "the current version only)",
)
@click.pass_context
def list(ctx, all_versions):
    """Show all available modules"""
    module_tree = ctx.obj.check_module_tree()
    for module in module_tree.modules(all_versions):
        click.echo(f"{module.name} {module.version}")


@mdcli.command(cls=ModuleDevCommand, short_help_color=INFO_CLR)
@version_option
@click.argument("MODULE_NAME")
@click.pass_context
def location(ctx, module_name, version):
    """Get the directory of a module by name"""
    module_tree = ctx.obj.check_module_tree()
    loader = ctx.obj.check_module(module_tree, module_name, version)
    click.echo(loader.module_path())
