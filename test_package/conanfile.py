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
    generators = "cmake"
    username = os.getenv("CONAN_USERNAME", "bincrafters")
    channel = os.getenv("CONAN_CHANNEL", "testing")
    requires = "macchina.io/0.7.0@%s/%s" % (username, channel)

    def test(self):
        config_file = os.path.join(self.deps_cpp_info["macchina.io"].res_paths[0], "macchina.properties")
        bundles_dir = os.path.join(self.deps_cpp_info["macchina.io"].lib_paths[0], "bundles")
        _, pid_file = tempfile.mkstemp()

        env_build = RunEnvironment(self)
        with tools.environment_append(env_build.vars):

            self.run("macchina --daemon -B%s -c%s -C --pidfile=%s" % (bundles_dir, config_file, pid_file))
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
