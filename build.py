from conans import tools
from conan.packager import ConanMultiPackager


if __name__ == "__main__":
    builder = ConanMultiPackager()
    builder.add_common_builds(shared_option_name="macchina.io:shared", pure_c=False)

    # XXX: V8 snapshot only works on gcc-4
    filtered_builds = []
    for settings, options, env_vars, build_requires in builder.builds:
        if tools.os_info.is_linux and settings["compiler"] == "gcc" and settings["compiler.version"] >= "5.0":
            options["macchina.io:with_V8_snapshot"] = False
        elif tools.os_info.is_linux and settings["compiler"] == "clang":
            options["macchina.io:with_V8_snapshot"] = False
        filtered_builds.append([settings, options, env_vars, build_requires])
    builder.builds = filtered_builds

    builder.run()
