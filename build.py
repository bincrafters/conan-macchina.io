from conans import tools
from conan.packager import ConanMultiPackager


if __name__ == "__main__":
    builder = ConanMultiPackager()
    builder.add_common_builds(pure_c=False)

    builder.add(settings={"arch": "armv7", "build_type": "Release", "compiler": "gcc", "compiler.version": "6.3", "compiler.libcxx": "libstdc++"},
                options={"macchina.io:V8_snapshot": False},
                env_vars={"CC": "arm-linux-gnueabi-gcc", "CXX": "arm-linux-gnueabi-g++"},
                build_requires={})

    # V8 snapshot only works on gcc-4
    filtered_builds = []
    for settings, options, env_vars, build_requires in builder.builds:
        if tools.os_info.is_linux and settings["compiler"] == "gcc" and settings["compiler.version"] >= "5.0":
            options["macchina.io:V8_snapshot"] = False
        elif tools.os_info.is_linux and settings["compiler"] == "clang":
            options["macchina.io:V8_snapshot"] = False
        filtered_builds.append([settings, options, env_vars, build_requires])
    builder.builds = filtered_builds

    builder.run()
