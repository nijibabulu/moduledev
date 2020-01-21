[![Build Status](https://travis-ci.com/nijibabulu/moduledev.svg?branch=master)](https://travis-ci.com/nijibabulu/moduledev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Coverage Status](https://codecov.io/gh/nijibabulu/moduledev/branch/master/graph/badge.svg)](https://codecov.io/gh/nijibabulu/moduledev)

# moduledev

`moduledev` is a tool to easily create, edit and manage a repository of environment modules. A module tree is setup as such:

```
  ${ROOT}
  |-- module
  |   `-- ${NAME}_modulefile
  `-- modulefile
```

Where all the other directories under `${ROOT}` that are not `module` and `modulefile` are modules. For instance, if a module is initialized as such:


```
$ mkdir modules
$ moduledev config set root $(pwd)/modules
$ moduledev setup mymodules
$ moduledev init hello 1.0
$ tree modules
modules
|-- hello
|   `-- 1.0
|-- module
|   `-- mymodules_modulefile
`-- modulefile
    `-- mymodules
        `-- hello
            `-- 1.0 -> ${ROOT}/modules/module/mymodules_modulefile
```

You can then add paths to the module:

```
$ mkdir bin
$ vi bin/exe.sh
# edit a script...
$ moduledev path add PATH bin
$ tree modules
modules
|-- hello
|   `-- 1.0
|       `-- bin -> ${BUILDDIR}/moduledev/bin
|-- module
|   `-- mymodules_modulefile
`-- modulefile
    `-- mymodules
        `-- hello
            `-- 1.0 -> ${ROOT}/modules/module/mymodules_modulefile
```

You can view and edit the module file:

```
$ moduledev location hello
${ROOT}/modules/hello/1.1
$ moduledev show hello
$ moduledev show hello
set MAINTAINER "testmaintainer"
set HELPTEXT "" 
set DESCRIPTION ""
$ moduledev edit hello
# .. add helptext, description and maintainer
```
