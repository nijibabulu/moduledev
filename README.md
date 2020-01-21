[![Build Status](https://travis-ci.com/nijibabulu/moduledev.svg?branch=master)](https://travis-ci.com/nijibabulu/moduledev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage Status](https://codecov.io/gh/nijibabulu/moduledev/branch/master/graph/badge.svg)](https://codecov.io/gh/nijibabulu/moduledev)

# moduledev

With [Environment Modules](http://modules.sourceforge.net/), one can create pluggable software modules without installing alongside other packages. This is especially useful for supercomputing environments, where many different library versions may be necessary to be installed. `moduledev` greatly simplifies the process of creating and maintaining the directory structure behind environment modules.  Here's is an example of how you might set up a repository and add a new environment module:

```
$ REPO_ROOT=$HOME/modules
$ moduledev config set root $REPO_ROOT
$ moduledev setup mymodules
# ...
```

Now we can activate our new repository with the module installation:
```
module use --append $HOME/modules/modulefile
module use --append $HOME/modules/modulefile/mymodules
```

## Module Creation

First we'll build and install a package in a non-system stage area (e.g. in the source directory):
```
$ curl -O https://ftp.gnu.org/gnu/hello/hello-2.10.tar.gz
$ tar xf hello-2.10.tar.gz
$ cd hello-2.10
$ ./configure --prefix=$(pwd)/stage
$ make install
$ ls stage
bin share
```

To populate the module, we will simply want to add `bin` to our PATH and `share/man` to our MANPATH:

```
$ moduledev init hello 2.10
$ moduledev path add hello PATH stage/bin
$ moduledev path add hello MANPATH stage/share/man
$ tree $(moduledev location hello)
${ROOT}/modules/hello/2.10
|-- bin -> $HOME/builds/hello-2.10/stage/bin
`-- man -> $HOME/builds/hello-2.10/stage/share/man
```

We can see that the directories havebeen linked off of the stage directory we created above. Note that these will be non-portable with links. If you wish to copy the files to the module tree, you may use the `--copy` option with `module path add`.

## Module Viewing and Editing

We can also see that a modulefile has been created
which points the environment variables to where we want them to go:

```
$ moduledev show hello
set MAINTAINER "nomaintainer"
set HELPTEXT ""
set DESCRIPTION ""

append-path PATH $basedir/bin
append-path MANPATH $basedir/man
```

This is spartan in terms of information. We could have set `HELPTEXT`
and `DESCRIPTION` at the `init` phase, and we could also set the `MAINTAINER`
using `moduledev config`.  We can also easily edit the file
directly:

```
$ env EDITOR="nano" moduledev edit hello  # editor defaults to "vim"
```

## Using `moduledev` modules

We can already load and run `hello` using `module`:

```
$ module load hello
$ hello
Hello, world!
```

You can use `moduledev list` to view the list of the your custom modules. But we can also view these directly from the environment modules interface, since all of our modules fall under the directory that we setup `${NAME}`:

```
$ module avail mymodules
------------------- ${ROOT}/mymodules -------------------
mymodules/hello/2.10
```

## Categories

`mymodules` (`${NAME}`) is the default **category** for all the modules you create. If you anticipate a lot of modules under different categories, you can also separate them using different categories.  For example, you could add a module for `moduledev` itself under a new `dev` category, you might do this:

```
$ moduledev init --category dev moduledev 0.1
$ git clone https://github.com/nijibabulu/moduledev.git
$ cd moduledev
$ pip install --no-deps --install-option="--prefix=$(pwd)/stage" .
$ moduledev path add PATH $(pwd)/stage/bin
$ moduledev path add moduledev PYTHONPATH $(pwd)/stage/lib/python3.8/site-packages
$ module avail dev
------------------- ${ROOT}/dev -------------------
dev/moduledev/0.1
```

A caveat is that we will have to add each of these categories to our module paths each time we create a new one:

```
module use --append $HOME/modules/modulefile/dev
```

## Behind the scenes

The structure of an empty root with the name `${NAME}` looks like this:

```
  ${ROOT}
  |-- module
  |   `-- ${NAME}_modulefile
  `-- modulefile
```

The `${NAME}_modulefile` is the *actual* modulefile which automatically loads
the abbreviated `.modulefile` file which we will interact with. For instance,
the structure after having made the hello module above:


```
$ tree modules
modules
|-- hello
|   `-- 2.10
|-- module
|   `-- ${NAME}_modulefile
`-- modulefile
    `-- ${NAME}
        `-- hello
            `-- 2.10 -> ${ROOT}/modules/module/${NAME}_modulefile
```

The master module file, `${NAME}_modulefile` finds the the `modules/hello/2.10`
path based on the name of the link `modulefile/${NAME}/hello/2.10` and reads in
additional variables, such as `DESCRIPTION`, `HELPTEXT`, and so on. 

The structure under the `modulefile` directory implies the aforementioned categories. In our example, the `dev` category appears directly under the `modulefile directory:

```
$ tree modules
modules 
...
|-- hello
|   `-- 2.10
|       |-- bin -> /Users/rpz/builds/hello-2.10/stage/bin
|       `-- man -> /Users/rpz/builds/hello-2.10/stage/share/man
|-- module
|   `-- mymodules_modulefile
|-- moduledev
|   `-- 0.1
|       |-- bin -> /Users/rpz/moduledev/stage/bin
|       `-- site-packages -> /Users/rpz/moduledev/stage/lib/python3.8/site-packages
`-- modulefile
    |-- dev
    |   `-- moduledev
    |       `-- 0.1 -> /Users/rpz/modules/module/mymodules_modulefile
    `-- mymodules
        `-- hello
            `-- 2.10 -> /Users/rpz/modules/module/mymodules_modulefile
```
