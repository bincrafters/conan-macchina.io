"""Script that update recipe version by 1.

This script update all files that contain macchina.io version included. The version will be incremented by 1.

Example:

    To update ONLY minor version:
    $ python scripts/update_version.py --minor
    or
    $ python scripts/update_version.py -mi

    To update minor version AND major version:
    $ python scripts/update_version.py --major --minor
    or
    python scripts/update_version.py -ma -mi

    To update ONLY patch version:
    $ python scripts/update_version.py --patch
    or
    python scripts/update_version.py -pa

"""

import os
import sys
import re
import argparse


class UserOptions(object):

    def __init__(self):
        parser = argparse.ArgumentParser(description="Update Macchina.io version value")
        parser.add_argument("-ma", "--major", help="Increment major version", action="store_true")
        parser.add_argument("-mi", "--minor", help="Increment minor version", action="store_true")
        parser.add_argument("-pa", "--patch", help="Increment patch version", action="store_true")
        self.args = parser.parse_args()

    def update_major(self):
        return self.args.major

    def update_minor(self):
        return self.args.minor

    def update_patch(self):
        return self.args.patch


class VersionUpdater(object):

    def __init__(self):
        self.macchina_path = os.path.dirname(os.path.realpath(os.path.dirname(sys.argv[0])))
        self.readme_path = os.path.join(self.macchina_path, "README.md")
        self.conan_path = os.path.join(self.macchina_path, "conanfile.py")
        self.travis_path = os.path.join(self.macchina_path, ".travis.yml")
        self.options = UserOptions()
        self.new_version = self.get_new_version()

    def _get_field_version(self, version, group):
        version_pattern = re.compile(r'(\d+)\.(\d+)\.(\d+.*)')
        match = re.match(version_pattern, version)
        return match.group(group)

    def version(self):
        version_pattern = r'    version = "(\d+\.\d+\.\d+.*)"'
        version_parser = re.compile(version_pattern)
        with open(self.conan_path, 'r') as f:
            for line in f:
                m = version_parser.match(line)
                if m:
                    return m.group(1)
        return ""

    def major_version(self):
        return self._get_field_version(self.version(), 1)

    def minor_version(self):
        return self._get_field_version(self.version(), 2)

    def patch_version(self):
        return self._get_field_version(self.version(), 3)

    def get_new_version(self):
        major = int(self.major_version()) + 1 if self.options.update_major() else int(self.major_version())
        minor = int(self.minor_version()) + 1 if self.options.update_minor() else int(self.minor_version())
        patch = int(self.patch_version()) + 1 if self.options.update_patch() else int(self.patch_version())
        return "%d.%d.%d" % (major, minor, patch)

    def update_conan_file(self):
        conan_parser = re.compile(r'    version = "\d+\.\d+\.\d+.*"')
        with open(self.conan_path, 'r') as f:
            lines = []
            for line in f:
                m = conan_parser.match(line)
                if m:
                    lines.append('    version = "%s"' % self.new_version)
                else:
                    lines.append(line.rstrip())
        with open(self.conan_path, 'w') as f:
            for line in lines:
                f.write(line + "\n")

    def update_readme_file(self):
        upload_parser = re.compile(r'    \$ conan upload -r bincrafters macchina\.io\/\d+\.\d+\.\d+.*@bincrafters\/stable --all')
        install_parser = re.compile(r'    \$ conan install -r bincrafters macchina\.io\/\d+\.\d+\.\d+.*@bincrafters\/stable')
        require_parser = re.compile(r'    macchina\.io\/\d+\.\d+\.\d+.*@bincrafters\/stable')
        with open(self.readme_path, 'r') as f:
            lines = []
            for line in f:
                upload_match = upload_parser.match(line)
                install_match = install_parser.match(line)
                require_match = require_parser.match(line)
                if upload_match:
                    lines.append('    $ conan upload -r bincrafters macchina.io/%s@bincrafters/stable --all' % self.new_version)
                elif install_match:
                    lines.append('    $ conan install -r bincrafters macchina.io/%s@bincrafters/stable' % self.new_version)
                elif require_match:
                    lines.append('    macchina.io/%s@bincrafters/stable' % self.new_version)
                else:
                    lines.append(line.rstrip())

        with open(self.readme_path, 'w') as f:
            for line in lines:
                f.write(line + "\n")

    def update_travis_file(self):
        travis_parser = re.compile(r'     - CONAN_REFERENCE: "macchina\.io\/\d+\.\d+\.\d+.*"')
        with open(self.travis_path, 'r') as f:
            lines = []
            for line in f:
                m = travis_parser.match(line)
                if m:
                    lines.append('     - CONAN_REFERENCE: "macchina.io/%s"' % self.new_version)
                else:
                    lines.append(line.rstrip())
        with open(self.travis_path, 'w') as f:
            for line in lines:
                f.write(line + "\n")

if __name__ == "__main__":
    version_updater = VersionUpdater()
    version_updater.update_conan_file()
    version_updater.update_travis_file()
    version_updater.update_readme_file()
