import click
from subprocess import call

from .config import *
from .module import *


EDITOR = os.environ.get('EDITOR', 'vim')


class CliCfg:
    def __init__(self, config, root, maintainer):
        self.config, self.root, self.maintainer = (config, root, maintainer)

    def check_root(self):
        """
        Check that the root exists and return it
        
        :return: a path to the root
        """
        result = self.root or self.config.get("root")
        if result is None:
            raise SystemExit("No module root set. Add it to the configuration "
                             "or specify it on the commandline")

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


@click.group()
@click.option("--maintainer",
              help="Set the package maintainer, overriding configuration")
@click.option("--root",
              help="Set the module root directory, overriding configuration")
@click.pass_context
def moduledev(ctx, maintainer, root):
    """
    Create and maintain environment modules.  Create an environment module
    repository with the setup subcommand. Initialize a new module with the 
    init subcommand. Add paths with the update subcommand. Adjust global
    configuration with the config subcommand.
    """
    ctx.obj = CliCfg(Config(), root, maintainer)


"""
should we support toplevel versus version-level .modulefile files?
"""

@moduledev.command()
@click.option("--force", is_flag=True, default=False)
@click.argument("PACKAGE_NAME")
@click.argument("VERSION")
@click.argument("HELPTEXT", default="", required=False)
@click.argument("DESCRIPTION", default="", required=False)
@click.pass_context
def init(ctx, force, package_name, version, helptext, description):
    """
    Initialize a new module or add a version to a module. For example, the
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
    if ctx.obj.maintainer is None:
        if ctx.obj.config.get("maintainer") is None:
            click.echo("Warning: maintainer not set; defaulting to nomaintainer",
                       err=True)
            maintainer = "nomaintainer"
        else:
            maintainer = ctx.obj.config.get("maintainer")
    module_tree = ctx.obj.check_module_tree()
    m = Module(module_tree, package_name, version, maintainer, helptext, description)
    if not module_tree.module_clean(m) and not force:
        raise SystemExit(f"Some file exist where the module should be "
                         f"installed. Use --force to overwrite them.")
    module_tree.init_module(m, overwrite=force)


@moduledev.command()
@click.argument("NAME")
@click.pass_context
def setup(ctx, name):
    """
    Set up the root directory structure of the environment modules. The root
    itself should be set either here in the configuration (as "root"). This will 
    create new directories of the following structure:
    
    \b
    ${ROOT}
    |-- module
    |   `-- ${NAME}_modulefile
    `-- modulefile

    The ${NAME}_modulefile contains boilerplate header for all modules and will
    be invoked for every module that is created. The file itself searches for
    the modulefile specific to the module. See the init subcommand for details.
    """
    used_root = ctx.obj.check_root()
    module_tree = ModuleTree(used_root)
    module_tree.setup(name)
    

@moduledev.group()
def config(): 
    """Manage the global configuration."""
    pass


@config.command()
@click.argument("SETTING", required=False)
@click.pass_context
def get(ctx, setting):
    print(f"{ctx.obj.config.dump(setting)}")


@config.command()
@click.argument("SETTING")
@click.argument("VALUE")
@click.pass_context
def set(ctx, setting, value):
    ctx.obj.config.set(setting, value)
    ctx.obj.config.save()


@moduledev.group()
def path():
    """Add, remove, or show current paths in a module"""
    pass


def check_module(module_tree, module_name, version):
    """
    Check for the presence of a module on the module tree and return it if it
    exists. If it does not exist, inform the user and exit.
    """
    if not module_tree.module_exists(module_name, version):
        module_display = f"{module_name}"
        if version is not None:
            module_display += f"-{version}"
        raise SystemExit(f"Module {module_display} does not exist.")
    return module_tree.load_module(module_name, version)


@path.command()
@click.option("--action", type=click.Choice(["prepend", "append"]),
              default="append", show_default=True,
              help="Prepend or append the evnironment variable")
@click.option("--version",
              help="Specify the module version (default to latest)")
@click.option("--copy", is_flag=True,
              help="Copy the files contained in the path (default is "
                   "create a symlink)")
@click.option("--overwrite", is_flag=True,
              help="Overwrite an old path if it exists.")
@click.argument("MODULE_NAME")
@click.argument("VARIABLE_NAME")
@click.argument("SRC_PATH")
@click.pass_context
def add(ctx, action, version, module_name, variable_name, src_path, copy, overwrite):
    """Add or update a path to a module"""
    module_tree = ctx.obj.check_module_tree()
    loader = check_module(module_tree, module_name, version)
    path_obj = Path(src_path, f"{action}-path", variable_name)
    if loader.path_exists(path_obj):
        if overwrite:
            loader.remove_path(path_obj)
        else:
            raise SystemExit(f"Path {path_obj.path} already exists. "
                             f"Use --overwrite to force.")
    loader.add_path(src_path, path_obj, not copy)
    loader.save_module_file()

@path.command()
@click.option("--version",
              help="Specify the module version (default to latest)")
@click.argument("MODULE_NAME")
@click.argument("SRC_PATH")
@click.pass_context
def remove(ctx, module_name, src_path, version):
    """Remove a path from a module"""
    module_tree = ctx.obj.check_module_tree()
    loader = check_module(module_tree, module_name, version)
    path_obj = Path(src_path)
    loader.remove_path(path_obj)
    loader.save_module_file()


@path.command()
@click.option("--version",
              help="Specify the module version (default to latest)")
@click.argument("MODULE_NAME")
@click.pass_context
def view(ctx, module_name, version):
    """List all paths in a module"""
    module_tree = ctx.obj.check_module_tree()
    loader = check_module(module_tree, module_name, version)
    print("\n".join(f"{str(p)} -> {p.resolve(loader.module_path())}"
                    for p in loader.module.paths))


@moduledev.command()
@click.option("--editor",
              help="Specify the editor", default=EDITOR, show_default=True)
@click.option("--version",
              help="Specify the module version (default to latest)")
@click.argument("MODULE_NAME")
@click.pass_context
def edit(ctx, module_name, version, editor):
    """Edit the module file for a package"""
    module_tree = ctx.obj.check_module_tree()
    loader = check_module(module_tree, module_name, version)
    call([editor, loader.moduledotfile_path()])


@moduledev.command()
@click.option("--version",
              help="Specify the module version (default to latest)")
@click.argument("MODULE_NAME")
@click.pass_context
def show(ctx, module_name, version):
    """Show the module file associated with a module"""
    module_tree = ctx.obj.check_module_tree()
    loader = check_module(module_tree, module_name, version)
    click.echo("".join(open(loader.moduledotfile_path()).readlines()))


@moduledev.command()
@click.option("--all", "all_versions", is_flag=True,
              help="Show all versions of each module (default is to show "
                   "the current version only)")
@click.pass_context
def list(ctx, all_versions):
    """Show all available modules"""
    module_tree = ctx.obj.check_module_tree()
    for module in module_tree.modules(all_versions):
        click.echo(f"{module.name} {module.version}")


@moduledev.command()
@click.option("--version",
              help="Specify the module version (default to latest)")
@click.argument("MODULE_NAME")
@click.pass_context
def location(ctx, module_name, version):
    """Get the directory of a module by name"""
    module_tree = ctx.obj.check_module_tree()
    loader = check_module(module_tree, module_name, version)
    click.echo(loader.module_path())

#if __name__ == "__main__":
    #moduledev()
