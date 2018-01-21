"""Conan recipe for Macchina.io project.

This recipe exports all necessary sources, build the project and create a
package with all artifacts.

"""

from conans import ConanFile, AutoToolsBuildEnvironment, tools
import os


class MacchinaioConan(ConanFile):
    name = "macchina.io"
    version = "0.7.0"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake", "txt"

    license = "Apache-2.0"
    url = "https://github.com/macchina-io/macchina.io"
    description = "macchina.io is a toolkit for building IoT edge and fog device applications in JavaScript and C++"
    exports = ["LICENSE.md"]

    options = {"V8_snapshot": [True, False], "install": ["all", "sdk", "runtime"], "poco_config": "ANY"}
    default_options = "V8_snapshot=True", "install=all", "poco_config=False"
    source_subfolder = "source_subfolder"
    install_subfolder = "install_subfolder"


    def source(self):
        """Download macchina.io on release version and unpack the file

        No checksum is validated
        """
        tools.get("https://github.com/macchina-io/macchina.io/archive/macchina-%s-release.tar.gz" % self.version)
        os.rename("macchina.io-macchina-%s-release" % self.version, self.source_subfolder)

    def build(self):
        """Build macchina.io project

        Execute all steps necessary to build macchina.io project
        """
        with tools.chdir(self.source_subfolder):
            self._solve_debug_names()
            self._host_tools()
            self._build()
            self._install()

    def _solve_debug_names(self):
        """Replace bundle tool name when the build mode is debug

        BUNDLE_TOOL can be found in many files, using the release. However, when the tools is build in debug mode,
        the suffix `d` is added to the name
        """
        if self.settings.build_type != "Debug":
            return

        magic_line = "BUNDLE_TOOL = $(POCO_BASE)/OSP/BundleCreator/$(POCO_HOST_BINDIR)/bundle"
        for root, _, files in os.walk("."):
            for f in files:
                if f == "Makefile" or f == "Makefile-Bundle":
                    try:
                        tools.replace_in_file(os.path.join(root, f), magic_line, "%sd" % magic_line)
                    except:
                        pass

    def _make_args(self):
        """Fill make arguments to build macchina.io

        Listed arguments as target and V8 are passed to make during build stage
        """
        make_args = []
        make_args.append("-s")
        make_args.append("DEFAULT_TARGET=shared_%s" % self.settings.build_type.value.lower())
        make_args.append("V8_SNAPSHOT=1" if self.options.V8_snapshot else "V8_NOSNAPSHOT=1")
        return make_args

    def _env_vars(self, env_build):
        """Solve environment variables to build macchina.io

        When cross-compiling is required, some addictional variables should be defined
        """
        env_vars = env_build.vars
        if self.options.poco_config:
            env_vars["POCO_CONFIG"] = str(self.options.poco_config)
        return env_vars

    def _host_tools(self):
        """Apply hosttools build

        Execute hosttools when target platform is not same on host
        """
        if tools.cross_building(self.settings) or self.options.poco_config:
            env_build = AutoToolsBuildEnvironment(self)
            env_vars = env_build.vars
            with tools.environment_append(env_vars):
                env_build.make(["-s", "hosttools", "DEFAULT_TARGET=shared_%s" % self.settings.build_type.value.lower()])

    def _build(self):
        """Execute make (no configure necessary)

        When cross-compiling is used, LINKMODE is add on the environment
        """
        env_build = AutoToolsBuildEnvironment(self)
        with tools.environment_append(self._env_vars(env_build)):
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
        make_args.append("INSTALLDIR=%s" % os.path.abspath(self.install_subfolder))

        env_build = AutoToolsBuildEnvironment(self)
        with tools.environment_append(self._env_vars(env_build)):
            env_build.make(args=make_args)

    def package(self):
        """Copy macchina.io artifacts to the package

        Copy all necessary files to create a complete package.
        The libv8 is not installed by default, the package copies it from the build folder
        """
        self.copy("LICENSE", src=self.source_subfolder, dst="licenses", ignore_case=True, keep_path=False)
        self.copy("*.h", dst="include", src=os.path.join(self.install_subfolder, "include"))
        self.copy("*.bndl", dst="lib", src=os.path.join(self.install_subfolder, "lib"))

        suffix = "d" if self.settings.build_type == "Debug" else ""
        self.copy("RemoteGenNG%s" % suffix, dst="bin", src=os.path.join(self.install_subfolder, "bin"), keep_path=False)
        self.copy("bundle%s" % suffix, dst="bin", src=os.path.join(self.install_subfolder, "bin"), keep_path=False)
        self.copy("ccutil%s" % suffix, dst="bin", src=os.path.join(self.install_subfolder, "bin"), keep_path=False)
        self.copy("macchina%s" % suffix, dst="bin", src=os.path.join(self.install_subfolder, "bin"), keep_path=False)

        self.copy("macchina.pem", dst="res", src=os.path.join(self.install_subfolder, "etc"), keep_path=False)
        self.copy("macchina.properties", dst="res", src=os.path.join(self.install_subfolder, "etc"), keep_path=False)
        self.copy("rootcert.pem", dst="res", src=os.path.join(self.install_subfolder, "etc"), keep_path=False)

        if tools.os_info.is_macos:
            self.copy(pattern="*.dylib", dst="lib", src=os.path.join(self.install_subfolder, "lib"), keep_path=False)
        else:
            self.copy(pattern="*.so*", dst="lib", src=os.path.join(self.install_subfolder, "lib"), keep_path=False, symlinks="*.so")

    def package_info(self):
        """Export macchina properties

        Solve dynamic library path and put macchina in PATH
        """
        self.cpp_info.libs = tools.collect_libs(self)
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
        if self.settings.os == "Linux":
            self.env_info.LD_LIBRARY_PATH.append(os.path.join(self.package_folder, "lib"))
        elif self.settings.os == "Macos":
            self.env_info.DYLD_LIBRARY_PATH.append(os.path.join(self.package_folder, "lib"))
