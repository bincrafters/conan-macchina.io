[![Build Status on Travis](https://travis-ci.org/bincrafters/conan-macchina.io.svg?branch=release/0.7.0)](https://travis-ci.org/bincrafters/conan-macchina.io)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)


# conan-macchina.io

[Conan.io](https://conan.io) package for [macchina.io](http://macchina.io) project

The packages generated with this **conanfile** can be found in [conan.io](https://bintray.com/bincrafters/public-conan/macchina.io%3Abincrafters).

## Build packages

Download conan client from [Conan.io](https://conan.io) and run:

    $ python build.py

If your are in Windows you should run it from a VisualStudio console in order to get "mc.exe" in path.

## Add remote server

    $ conan remote add bincrafters https://api.bintray.com/conan/bincrafters/public-conan

## Upload packages to server

    $ conan upload -r bincrafters macchina.io/0.7.0@bincrafters/stable --all

## Reuse the packages

### Basic setup

    $ conan install -r bincrafters macchina.io/0.7.0@bincrafters/stable

### Project setup

If you handle multiple dependencies in your project is better to add a *conanfile.txt*

    [requires]
    macchina.io/0.7.0@bincrafters/stable

    [options]
    macchina.io:with_V8_snapshot=True # False

    [generators]
    txt
    cmake

Complete the installation of requirements for your project running:</small></span>

    conan install .

Project setup installs the library (and all his dependencies) and generates the files *conanbuildinfo.txt* and *conanbuildinfo.cmake* with all the paths and variables that you need to link with your dependencies.

## Version update

The script **update_version.py** is a helper to increment major, minor and patch version by 1, independently.

To update **only** minor version:

    $ python scripts/update_version.py --minor

To update minor version **and** major version:

    $ python scripts/update_version.py --major --minor

To update **only** patch version:

    $ python scripts/update_version.py --patch

## Cross-compiling and Custom configuration

As supported in macchina.io, **POCO_CONFIG** was integrated as an option. It's possible to set custom a configuration as below:

    [requires]
    macchina.io/0.7.0@bincrafters/stable

    [options]
    macchina.io:poco_config=ARM-Linux

    [generators]
    txt
    cmake

The configuration above will set the target to ARM arch.

## License
[Apache-2.0](LICENSE)
