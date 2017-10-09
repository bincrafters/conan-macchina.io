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
    options = {"shared": [True, False], "with_V8_snapshot": [True, False], "install": ["all", "sdk", "runtime"]}
    default_options = "shared=True", "with_V8_snapshot=True", "install=all"
    exports = "LICENSE"
    install_dir = tempfile.mkdtemp(prefix=name)
    release_dir = "macchina.io-macchina-%s-release" % version

    def source(self):
        tools.get("https://github.com/macchina-io/macchina.io/archive/macchina-%s-release.tar.gz" % self.version)

    def configure(self):
        if tools.os_info.is_linux and self.settings.compiler.version >= "5.0" and self.settings.compiler == "gcc":
            self.output.warn("V8 SNAPSHOT may fail on gcc>=5.0")
        elif tools.os_info.is_linux and self.settings.compiler.version >= "3.8" and self.settings.compiler == "clang":
            self.output.warn("V8 SNAPSHOT may fail on clang>=3.8")

    def build(self):
        with tools.chdir(self.release_dir):
            self._host_tools()
            self._configure_v8()
            self._build()
            self._install()
            self._replace_configuration()

    def _make_args(self):
        make_args = []
        make_args.append("-s")
        make_args.append("DEFAULT_TARGET=%s_%s" % ("shared" if self.options.shared else "static", self.settings.build_type.value.lower()))
        make_args.append("V8_SNAPSHOT=1" if self.options.with_V8_snapshot else "V8_NOSNAPSHOT=1")
        return make_args

    def _host_tools(self):
        if tools.detected_architecture() != self.settings.arch:
            env_build = AutoToolsBuildEnvironment(self)
            with tools.environment_append(env_build.vars):
                env_build.make(["-s", "hosttools"])

    def _configure_v8(self):
        conan_magic_lines = """
all_shared: shared_debug shared_release

static_release: shared_release

static_debug: shared_debug
"""
        tools.replace_in_file(path.join(self.build_folder, self.release_dir, "platform", "JS", "V8", "Makefile"), "all_shared: shared_debug shared_release", conan_magic_lines)

    def _build(self):
        env_build = AutoToolsBuildEnvironment(self)
        env_vars = env_build.vars
        if tools.detected_architecture() != self.settings.arch:
            env_vars["LINKMODE"] = "SHARED" if self.options.shared else "STATIC"
        with tools.environment_append(env_vars):
            env_build.make(args=self._make_args())

    def _install(self):
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

    def _replace_configuration(self):
        conan_magic_lines = """
application.dir = %s/bin/
application.configDir = %s/res/
osp.codeCache          = ${application.dir}codeCache""" % (self.package_folder, self.package_folder)
        tools.replace_in_file(path.join(self.install_dir, "etc", "macchina.properties"), "osp.codeCache          = ${application.dir}codeCache", conan_magic_lines)

    def package(self):
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

        if self.options.shared:
            if tools.os_info.is_macos:
                self.copy(pattern="*.dylib", dst="lib", src=path.join(self.install_dir, "lib"), keep_path=False)
                self.copy("libv8.dylib", dst="lib", src=path.join("platform", "lib", str(self.settings.os), str(self.settings.arch)), keep_path=False)
            else:
                self.copy(pattern="*.so*", dst="lib", src=path.join(self.install_dir, "lib"), keep_path=False, symlinks="*.so")
                self.copy("libv8.so", dst="lib", src=path.join("platform", "lib", str(self.settings.os), str(self.settings.arch)), keep_path=False)
        else:
            self.copy(pattern="*.a", dst="lib", src=path.join(self.install_dir, "lib"), keep_path=False)
            self.copy("libv8.a", dst="lib", src=path.join("platform", "lib", str(self.settings.os), str(self.settings.arch)), keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
        self.env_info.PATH.append(path.join(self.package_folder, "bin"))
        if tools.os_info.is_linux:
            self.env_info.LD_LIBRARY_PATH.append(path.join(self.package_folder, "lib"))
        elif tools.os_info.is_macos:
            self.env_info.DYLD_LIBRARY_PATH.append(path.join(self.package_folder, "lib"))
