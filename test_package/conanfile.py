"""Conan recipe for Macchina.io test package.

This test summons the macchina.io process, and check by a HTTP resquest on
port 22080.

"""

import os
import signal
import tempfile
import time
import sys
from conans import ConanFile, RunEnvironment, tools

# Solve httplib
if sys.version_info > (3, 0):
    import http.client
    httplib = http.client
else:
    import httplib


class MacchinaioTestConan(ConanFile):
    settings = "os", "compiler", "arch", "build_type"

    def imports(self):
        self.copy(pattern="*", src="bin", dst="bin")

    def test(self):
        config_file = os.path.join(self.deps_cpp_info["macchina.io"].res_paths[0], "macchina.properties")
        bundles_dir = os.path.join(self.deps_cpp_info["macchina.io"].lib_paths[0], "bundles")
        _, pid_file = tempfile.mkstemp()

        env_build = RunEnvironment(self)
        env_vars = env_build.vars
        env_vars["PATH"] = "bin"
        env_vars["LD_LIBRARY_PATH"].append(os.path.join("bin", "codeCache"))
        assert(os.path.join(self.deps_cpp_info["macchina.io"].res_paths[0], "macchina.pem"))

        os.symlink(os.path.join(self.deps_cpp_info["macchina.io"].res_paths[0], "macchina.pem"), os.path.join("bin", "macchina.pem"))
        os.symlink(os.path.join(self.deps_cpp_info["macchina.io"].res_paths[0], "rootcert.pem"), os.path.join("bin", "rootcert.pem"))
        with tools.environment_append(env_vars):
            suffix = "d" if self.settings.build_type == "Debug" else ""
            self.run("macchina%s --daemon -B%s -c%s --pidfile=%s" % (suffix, bundles_dir, config_file, pid_file))
            # Wait for server get ready
            time.sleep(3)

            try:
                conn = httplib.HTTPConnection("localhost:22080")
                conn.request("HEAD", "/macchina/login")
                res = conn.getresponse()

                assert(res.status == 200)
                assert("OSP Web Server" in str(res.msg))
            finally:
                with open(pid_file) as f:
                    os.kill(int(f.read()), signal.SIGTERM)
