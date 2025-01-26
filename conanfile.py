#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan import ConanFile
from conan.tools.files import copy, get, replace_in_file
from conan.tools.scm import Git
from conan.errors import ConanInvalidConfiguration
import json, os

required_conan_version = ">=2.0"

class OpenJDK(ConanFile):

    jsonInfo = json.load(open("info.json", 'r'))
    # ---Package reference---
    name = jsonInfo["projectName"]
    version = jsonInfo["version"]
    user = jsonInfo["domain"]
    channel = "stable"
    # ---Metadata---
    description = jsonInfo["projectDescription"]
    license = jsonInfo["license"]
    author = jsonInfo["vendor"]
    topics = jsonInfo["topics"]
    homepage = jsonInfo["homepage"]
    url = jsonInfo["repository"]
    # ---Requirements---
    requires = []
    tool_requires = ["openjdk/[~19]@%s/stable" % user]
    # ---Sources---
    exports = ["info.json"]
    exports_sources = []
    # ---Binary model---
    settings = "os", "arch"
    options = {}
    default_options = {}
    # ---Build---
    generators = []
    # ---Folders---
    no_copy_source = False

    def validate(self):
        valid_os = ["Windows", "Linux", "Macos"]
        if str(self.settings.os) not in valid_os:
            raise ConanInvalidConfiguration(f"{self.name} {self.version} is only supported for the following operating systems: {valid_os}")

    def source(self):
        git = Git(self)
        #git.clone(url="https://github.com/Netflix/photon.git", target="./")
        git.clone(url="https://github.com/fschleich/photon.git", target="./")
        #git.checkout("v%s" % self.version)
        git.checkout("CompositionRefactoring")
        replace_in_file(self, os.path.join(self.source_folder, "build.gradle"), "JavaLanguageVersion.of(11)", "JavaLanguageVersion.of(19)")

    def build(self):
        if self.settings.os == "Macos" or self.settings.os == "Linux":
            #self.run("./gradlew clean")
            self.run("./gradlew build")
            self.run("./gradlew getDependencies")
        else:
            #self.run("gradlew.bat clean")
            self.run("gradlew.bat build")
            self.run("gradlew.bat getDependencies")

    def package(self):
        copy(self, pattern="*.jar", src=os.path.join(self.build_folder, "build", "libs"), dst=os.path.join(self.package_folder, "bin"))
