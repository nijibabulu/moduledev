import os
import shlex
import shutil
from abc import ABCMeta, abstractmethod
from glob import glob

from . import util

_modulefile_template = """#%%Module1.0
set MODULENAME [ file tail [ file dirname $ModulesCurrentModulefile ] ]
set MODULEVERSION [ file tail $ModulesCurrentModulefile ]
set MODULEBASE %s
set basedir $MODULEBASE/$MODULENAME/$MODULEVERSION

conflict $MODULENAME

if { [ file exists $MODULEBASE/$MODULENAME/.modulefile ] } {
  source $MODULEBASE/$MODULENAME/.modulefile
}

if { [ file exists $MODULEBASE/$MODULENAME/$MODULEVERSION/.modulefile ] } {
  source $MODULEBASE/$MODULENAME/$MODULEVERSION/.modulefile
}

proc ModulesHelp { } {
     global dotversion
     global MODULENAME
     global MODULEVERSION
     global DESCRIPTION
     global HELPTEXT
     global MAINTAINER
     puts stderr "\\t$MODULENAME $MODULEVERSION - $DESCRIPTION\\n\\tMaintainer: $MAINTAINER\\n"
     puts stderr "\\n$HELPTEXT"
}

module-whatis $DESCRIPTION
"""


class ModuleTree:
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)

    @property
    def name(self):
        modulefile = self.master_module_file()
        if modulefile is not None:
            return os.path.basename(modulefile).split("_")[0]
        else:
            return None

    def module_dir(self):
        return os.path.join(self.root_dir, "module")

    def modulefile_dir(self):
        return os.path.join(self.root_dir, "modulefile")

    def master_module_file(self):
        """Return the master module file if it exists, None otherwise."""
        files = glob(os.path.join(self.module_dir(), "*modulefile"))
        if len(files):
            return files[0]
        else:
            return None

    def _master_module_file_name(self, name):
        """Construct the name of the master module file"""
        return os.path.join(self.module_dir(), f"{name}_modulefile")

    def exists(self):
        """Return true if the root directory exists"""
        return os.path.exists(self.root_dir)

    def valid(self):
        """
        Check if the module root tree is set up. Exit if it appears
        corrupted.
        """
        return (
            self.exists()
            and util.writeable_dir(self.root_dir)
            and util.writeable_dir(self.modulefile_dir())
            and util.writeable_dir(self.module_dir())
            and self.master_module_file() is not None
        )

    def module_names(self):
        return [
            m for m in os.listdir(self.root_dir) if m != "module" and m != "modulefile"
        ]

    def modules(self, all_versions=False):
        if not self.valid():
            raise RuntimeError(
                "Cannot get available modules from a "
                "module tree that has not been setup"
            )
        for m in self.module_names():
            loader = self.load_module(m)
            if all_versions:
                for v in loader.available_versions():
                    version_loader = self.load_module(m, v)
                    yield version_loader.module
            else:
                yield loader.module

    def can_setup(self, name):
        """Return True if the root directory of this tree can be setup"""
        return (
            self.exists()
            and os.path.exists(self.root_dir)
            and os.access(self.root_dir, os.W_OK)
            and not len(os.listdir(self.root_dir))
        )

    def setup(self, name):
        """Set up the module root tree."""
        if not self.can_setup(name):
            raise ValueError(
                "Module tree must be set up in an empty, " "writeable directory"
            )
        os.makedirs(str(self.modulefile_dir()))
        os.makedirs(str(self.module_dir()))
        f = open(self._master_module_file_name(name), "w")
        f.write(_modulefile_template % self.root_dir)
        f.close()

    def init_module(self, module, overwrite=False):
        """
        Create a module, throwing an exception if any files are in
           the way of the module

        :return: a ModuleBuilder used to build the module.
        """
        builder = ModuleBuilder(self, module)
        if not builder.clean():
            if overwrite:
                builder.clear()
            else:
                raise ValueError(
                    f"Some files exist in the module tree " f"where {module} should be."
                )
        builder.build()
        return builder

    def module_clean(self, module):
        """
        Return True if nothing is in place where a module would be initialized.
        """
        builder = ModuleBuilder(self, module)
        return builder.clean()

    def module_exists(self, name, version=None):
        """
        Check for the existence of a valid module

        :param name: the name of the module
        :param version: a version number
        :return: True if the module is found.
        """
        loader = ModuleLoader(self, name, version)
        return loader.valid()

    def load_module(
        self, name, version=None, parse_error_handler=util.raise_value_error
    ):
        """
        Locate and parse the module from the filesystem identified by the
        given name and version.

        :param name: the name of the module
        :param version: the version of the module. if none is provided, the
            latest is loaded
        :param parse_error_handler: a function which handles parse error
            messages. If none is provided, an exception is raised.

        :return: a ModuleLoder used to load the module.
        """
        loader = ModuleLoader(self, name, version)
        if not loader.valid():
            raise ValueError(
                f"Module {name}-{version} does not appear to "
                f"be a valid module in the tree {self.root_dir}"
            )
        loader.load(parse_error_handler)
        return loader


class ModuleLocation(metaclass=ABCMeta):
    """Resolves module file locations relative to a module tree"""

    @abstractmethod
    def __init__(self, module_tree):
        self.module_tree = module_tree
        self.module = None

    @abstractmethod
    def category_name(self):
        raise NotImplementedError

    @abstractmethod
    def toplevel(self):
        raise NotImplementedError

    @abstractmethod
    def name(self):
        raise NotImplementedError

    @abstractmethod
    def version(self):
        raise NotImplementedError

    def available_versions(self):
        return [v for v in os.listdir(self.module_base()) if util.valid_version(v)]

    def moduledotfile_path(self):
        base = self.module_base()
        if self.toplevel():
            return os.path.join(base, ".modulefile")
        else:
            return os.path.join(base, self.version(), ".modulefile")

    def module_base(self):
        """
        :return: The path to the base of the module without the version
        """
        return os.path.join(self.module_tree.root_dir, self.name())

    def module_path(self):
        return os.path.join(self.module_base(), self.version())

    def modulefile_base(self):
        return os.path.join(
            self.module_tree.modulefile_dir(), self.category_name(), self.name()
        )

    def modulefile_path(self):
        return os.path.join(self.modulefile_base(), self.version())

    def clean(self):
        """Return false if files exist where the module resolves to. Note this
           does not imply validity or readability"""
        return not os.path.exists(self.module_path()) and not os.path.exists(
            self.modulefile_path()
        )

    def valid(self):
        return (
            util.writeable_dir(self.module_base())
            and self.version() is not None
            and util.writeable_dir(self.module_path())
            and os.path.exists(self.moduledotfile_path())
            and os.readlink(self.modulefile_path())
            == self.module_tree.master_module_file()
        )

    def path_exists(self, path):
        """Return true if the path that the path object implies already exists."""
        return os.path.exists(path.resolve(self.module_path()))

    def add_path(self, source, path_obj, link=True):
        """Copy or link the contents of the source path to the path implied
           in the destination path object."""
        dest = path_obj.resolve(self.module_path())
        cp = os.symlink if link else shutil.copytree
        cp(os.path.abspath(source), dest)
        self.module.paths.append(path_obj)

    def remove_path(self, path_obj):
        loc = path_obj.resolve(self.module_path())
        rm = os.unlink if os.path.islink(loc) else shutil.rmtree
        rm(path_obj.resolve(self.module_path()))
        self.module.remove_path(path_obj)

    def save_module_file(self):
        if self.module is None:
            raise RuntimeError("Cannot save unloaded module")
        with open(self.moduledotfile_path(), "w") as f:
            f.write(self.module.dump())

    def clear(self):
        if os.path.exists(self.modulefile_path()):
            os.unlink(self.modulefile_path())
        shutil.rmtree(self.module_path(), ignore_errors=True)
        if len(self.available_versions()) == 0:
            shutil.rmtree(self.module_base())
            shutil.rmtree(self.modulefile_base())


class ModuleBuilder(ModuleLocation):
    """A module builder class."""

    def __init__(self, module_tree, module):
        super(ModuleBuilder, self).__init__(module_tree)
        self.module = module

    def category_name(self):
        return self.module.category or self.module_tree.name

    def toplevel(self):
        return self.module.toplevel

    def name(self):
        return self.module.name

    def version(self):
        return self.module.version

    def build(self):
        os.makedirs(os.path.dirname(self.modulefile_path()), exist_ok=True)
        os.symlink(self.module_tree.master_module_file(), self.modulefile_path())
        os.makedirs(self.module_path())
        self.save_module_file()


class ModuleLoader(ModuleLocation):
    """A module loader class."""

    def __init__(self, module_tree, name, version=None):
        """
        Loads a module. If no version is specified, the latest version is used.

        :param module_tree: a ModuleTree object
        :param name: The name of the module
        :param version: The version of the module
        """
        super(ModuleLoader, self).__init__(module_tree)
        self._name = name
        self._version = version

    def category_name(self):
        files = glob(os.path.join(self.module_tree.modulefile_dir(), "*", self.name()))
        return os.path.basename(os.path.dirname(files[0]))

    def toplevel(self):
        return not os.path.exists(
            os.path.join(
                self.module_tree.root_dir, self.name(), self.version(), ".modulefile"
            )
        )

    def name(self):
        return self._name

    def version(self):
        if self._version is None:
            available_versions = self.available_versions()
            if len(available_versions) == 0:
                raise ValueError(f"No versions found for module {self.name()}")
            return max(available_versions, key=util.version_key)
        else:
            return self._version

    def load(self, error_handler=util.raise_value_error):
        self.module = Module.from_file(
            self.moduledotfile_path(),
            self.module_tree,
            self.name(),
            self.version(),
            self.toplevel(),
            self.category_name(),
            error_handler,
        )


class Path:
    """A module path object"""

    def __init__(self, path, operation="prepend-path", name="PATH"):
        (self.operation, self.name) = operation, name
        if "$basedir" in path:
            self.path = path
        else:
            self.path = os.path.join("$basedir", os.path.basename(path))

    def __repr__(self):
        return f"{self.operation} {self.name} {self.path}"

    def resolve(self, basedir):
        """replace the $basedir variable to the given path"""
        return self.path.replace("$basedir", basedir)


class Module:
    def __init__(
        self,
        root,
        name,
        version,
        maintainer="no_maintainer",
        helptext="",
        description="",
        extra_vars=None,
        category=None,
        toplevel=True,
        extra_commands=None,
    ):
        """
        Initialize a module.

        :param root: the ModuleTree object under which this module exists
        :param name: the name of the module (corresponding to the tool name)
        :param version: the version of the module
        :param maintainer: name and email address of the maintainer
        :param helptext: the helptext for the module
        :param description: longer form description of the module
        :param extra_vars: a dict of extra variables to add
        :param category: a category for the module
        :param toplevel: whether the module file comes at the top level or
                         (False) version level
        :param extra_commands: list of extra lines to add to the module file
        """
        if extra_commands is None:
            extra_commands = []
        if extra_vars is None:
            extra_vars = {}
        self.root = root
        self.name = name
        self.version = version
        self.maintainer = maintainer
        self.helptext = helptext
        self.description = description
        self.category = category
        self.toplevel = toplevel
        self.extra_vars = extra_vars
        self.extra_commands = extra_commands

        self.paths = []

    @classmethod
    def from_file(
        cls,
        filename,
        root,
        name,
        version,
        toplevel,
        category=None,
        error_handler=util.raise_value_error,
    ):
        """parse a module file

        :param filename: the path to the module dotfile
        :param name: the package name for the module
        :param version: the version of the module:
        :param toplevel: whether the moduledotfile is located at the toplevel
        :param category: the category of the module
        :param error_handler: a which handles any parse errors during parsing.
            If there is a parse error and a handler is provided, the line is
            not interpreted and error handler is called. The default handler
            raises a value error with the given error message.

        :return: a new module parsed from the given file
        """
        module = cls(root, name, version, toplevel=toplevel, category=category)
        for line in open(filename):
            try:
                fields = shlex.split(line.strip())
            except ValueError as e:
                error_handler(f"parse error in {filename}: {e}")
                continue
            if len(fields) == 0:
                continue
            if fields[0] == "set":
                if len(fields) < 3:
                    error_handler(f"Unparsable line in {filename}:\n{line}")
                if fields[1] == "MAINTAINER":
                    module.maintainer = fields[2]
                elif fields[1] == "HELPTEXT":
                    module.helptext = fields[2]
                elif fields[1] == "DESCRIPTION":
                    module.description = fields[2]
                else:
                    module.extra_vars.update({fields[1]: fields[2]})
            elif fields[0] == "prepend-path" or fields[0] == "append-path":
                module.paths.append(
                    Path(path=fields[2], operation=fields[0], name=fields[1])
                )
            else:
                module.extra_commands.append(line.strip())
        return module

    def remove_path(self, path_obj):
        """
        Remove the path from the module if the path_obj.path itself matches any of the paths in the module.

        :param path_obj: a path object to compare to
        :return:
        """
        self.paths = [p for p in self.paths if p.path != path_obj.path]

    def __repr__(self):
        return f"{self.name}-{self.version}"

    def dump(self):
        """Dump the module file as a string"""

        text = (
            f"""set MAINTAINER "{self.maintainer}"
set HELPTEXT "{self.helptext}"
set DESCRIPTION "{self.description}"\n"""
            + "\n".join([f'set {k} "{v}"' for k, v in self.extra_vars.items()])
            + "\n"
            + "\n".join(str(p) for p in self.paths)
            + "\n"
            + "\n".join(self.extra_commands)
        )
        return text
