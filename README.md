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

And finally we can start creating modules. First we'll build and install a
package in a non-system stage area (e.g. in the source directory):
```
$ curl -O https://ftp.gnu.org/gnu/hello/hello-2.10.tar.gz
$ tar xf hello-2.10.tar.gz
$ cd hello-2.10
$ ./configure --prefix=$(pwd)/stage
$ make install
$ ls stage
bin share
```

To creat the module, we will simply want to add `bin` to our PATH and
`share/man` to our MANPATH:

```
$ moduledev init hello 2.10
$ moduledev path add hello PATH stage/bin
$ moduledev path add hello MANPATH stage/share/man
$ tree $(moduledev location hello)
/Users/rpz/modules/hello/2.10
|-- bin -> $HOME/builds/hello-2.10/stage/bin
`-- man -> $HOME/builds/hello-2.10/stage/share/man
```
We can see that the directories havebeen linked off of the stage 
directory we created above. We can also see that a modulefile has been created
which points the environment variables to where we want them to go:

```
$ moduledev show hello
set MAINTAINER "testmaintainer"
set HELPTEXT ""
set DESCRIPTION ""

append-path PATH $basedir/bin
append-path MANPATH $basedir/man
```

This is a little spartan in terms of information. We could have set `HELPTEXT`
and `DESCRIPTION` at the `init` phase, but we can also easily edit the file
directly:


```
$ env EDITOR="nano" moduledev edit hello
```

We can already load and run `hello` using `module`:

```
$ module load hello
$ hello
Hello, world!
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

We can use the structure of the `modulefile` directory to create
pseudo-categories as well *to be documented...*
