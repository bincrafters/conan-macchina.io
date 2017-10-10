"""Conan recipe for Macchina.io project.

This recipe exports all necessary sources, build the project and create a
package with all artifacts.

"""

import tempfile
from os import path
from conans import ConanFile, AutoToolsBuildEnvironment, tools


class MacchinaioConan(ConanFile):
    name = "macchina.io"
    version = "0.7.0"
    generators = "cmake", "txt"
    license = "https://github.com/macchina-io/macchina.io/blob/master/LICENSE"
    url = "https://github.com/macchina-io/macchina.io"
    author = "Bincrafters <bincrafters@gmail.com>"
    description = "macchina.io is a toolkit for building IoT edge and fog device applications in JavaScript and C++"
    settings = "os", "compiler", "build_type", "arch"
    options = {"with_V8_snapshot": [True, False], "install": ["all", "sdk", "runtime"], "poco_config": "ANY"}
    default_options = "with_V8_snapshot=True", "install=all", "poco_config=False"
    exports = "LICENSE"
    install_dir = tempfile.mkdtemp(prefix=name)
    release_dir = "macchina.io-macchina-%s-release" % version

    def source(self):
        """Download macchina.io on release version and unpack the file

        No checksum is validated
        """
        tools.get("https://github.com/macchina-io/macchina.io/archive/macchina-%s-release.tar.gz" % self.version)

    def configure(self):
        """Create alert about V8 SNAPSHOT

        With some cross toolchains building the V8 library may fail when building the mksnapshot executable.
        If this happens, you can disable the V8 snapshot feature by building with the variable V8_NOSNAPSHOT defined.
        """
        if tools.os_info.is_linux and self.settings.compiler.version >= "5.0" and self.settings.compiler == "gcc":
            self.output.warn("V8 SNAPSHOT may fail on gcc>=5.0")
        elif tools.os_info.is_linux and self.settings.compiler.version >= "3.8" and self.settings.compiler == "clang":
            self.output.warn("V8 SNAPSHOT may fail on clang>=3.8")

    def build(self):
        """Build macchina.io project

        Execute all steps necessary to build macchina.io project
        """
        with tools.chdir(self.release_dir):
            self._host_tools()
            self._build()
            self._install()

    def _make_args(self):
        """Fill make arguments to build macchina.io

        Listed arguments as target and V8 are passed to make during build stage
        """
        make_args = []
        make_args.append("-s")
        make_args.append("DEFAULT_TARGET=shared_%s" % self.settings.build_type.value.lower())
        make_args.append("V8_SNAPSHOT=1" if self.options.with_V8_snapshot else "V8_NOSNAPSHOT=1")
        return make_args

    def _host_tools(self):
        """Apply hosttools build

        Execute hosttools when target platform is not same on host
        """
        if tools.detected_architecture() != self.settings.arch or self.options.poco_config:
            env_build = AutoToolsBuildEnvironment(self)
            with tools.environment_append(env_build.vars):
                env_build.make(["-s", "hosttools"])

    def _build(self):
        """Execute make (no configure necessary)

        When cross-compiling is used, LINKMODE is add on the environment
        """
        env_build = AutoToolsBuildEnvironment(self)
        env_vars = env_build.vars
        if tools.detected_architecture() != self.settings.arch:
            env_vars["LINKMODE"] = "SHARED"
        if self.options.poco_config:
            env_vars.["POCO_CONFIG"] = self.options.poco_config
        with tools.environment_append(env_build.vars):
            env_build.make(args=self._make_args())

    def _install(self):
        """Install macchina.io artifacts to collect for the package

        Install all/runtime/sdk in a temporary folder
        """
        install_args = "install"
        if self.options.install == "sdk":
            install_args += "_sdk"
        if self.options.install == "runtime":
            install_args += "_runtime"
        make_args = [install_args]

        make_args.extend(self._make_args())
        make_args.append("INSTALLDIR=%s" % self.install_dir)

        env_build = AutoToolsBuildEnvironment(self)
        with tools.environment_append(env_build.vars):
            env_build.make(args=make_args)

    def package(self):
        """Copy macchina.io artifacts to the package

        Copy all necessary files to create a complete package.
        The libv8 is not installed by default, the package copies it from the build folder
        """
        self.copy("LICENSE", dst=".", src=".")
        self.copy("*.h", dst="include", src=path.join(self.install_dir, "include"))
        self.copy("*.bndl", dst="lib", src=path.join(self.install_dir, "lib"))

        self.copy("RemoteGenNG", dst="bin", src=path.join(self.install_dir, "bin"), keep_path=False)
        self.copy("bundle", dst="bin", src=path.join(self.install_dir, "bin"), keep_path=False)
        self.copy("ccutil", dst="bin", src=path.join(self.install_dir, "bin"), keep_path=False)
        self.copy("macchina", dst="bin", src=path.join(self.install_dir, "bin"), keep_path=False)

        self.copy("macchina.pem", dst="res", src=path.join(self.install_dir, "etc"), keep_path=False)
        self.copy("macchina.properties", dst="res", src=path.join(self.install_dir, "etc"), keep_path=False)
        self.copy("rootcert.pem", dst="res", src=path.join(self.install_dir, "etc"), keep_path=False)

        if tools.os_info.is_macos:
            self.copy(pattern="*.dylib", dst="lib", src=path.join(self.install_dir, "lib"), keep_path=False)
        else:
            self.copy(pattern="*.so*", dst="lib", src=path.join(self.install_dir, "lib"), keep_path=False, symlinks="*.so")

    def package_info(self):
        """Export macchina properties

        Solve dynamic library path and put macchina in PATH
        """
        self.cpp_info.libs = tools.collect_libs(self)
        self.env_info.PATH.append(path.join(self.package_folder, "bin"))
        if self.settings.os == "Linux":
            self.env_info.LD_LIBRARY_PATH.append(path.join(self.package_folder, "lib"))
        elif self.settings.os == "Macos":
            self.env_info.DYLD_LIBRARY_PATH.append(path.join(self.package_folder, "lib"))
