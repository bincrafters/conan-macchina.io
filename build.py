from conans import tools
from conan.packager import ConanMultiPackager
import copy

if __name__ == "__main__":
    builder = ConanMultiPackager(args="--build missing")
    builder.add_common_builds()
    builder.add(settings={"arch": "armv7", "build_type": "Release", "compiler": "gcc", "compiler.version": "6.3", "compiler.libcxx": "libstdc++"},
                options={"macchina.io:V8_snapshot": False, "macchina.io:poco_config": "ARM-Linux"},
                env_vars={"TOOL": "arm-linux-gnueabi"},
                build_requires={})

    # V8 snapshot only works on gcc-4
    items = []
    for item in builder.items:
        new_options = copy.copy(item.options)
        if tools.os_info.is_linux and item.settings["compiler"] == "gcc" and item.settings["compiler.version"] >= "5.0":
            new_options["macchina.io:V8_snapshot"] = False
        elif tools.os_info.is_linux and settings["compiler"] == "clang":
            new_options["macchina.io:V8_snapshot"] = False
        items.append([item.settings, new_options, item.env_vars,
                      item.build_requires, item.reference])
    builder.items = items

    builder.run()
