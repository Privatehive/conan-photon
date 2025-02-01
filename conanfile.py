#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan import ConanFile
from conan.tools.files import copy, get, replace_in_file
from conan.tools.scm import Git
from conan.errors import ConanInvalidConfiguration
import json, os, io

required_conan_version = ">=2.0"

class Photon(ConanFile):

    jsonInfo = json.load(open("info.json", 'r'))
    # ---Package reference---
    name = jsonInfo["projectName"]
    version = jsonInfo["version"]
    user = jsonInfo["domain"]
    channel = "snapshot"
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
        version = self.version
        if self.channel == "snapshot":
            version += "-snapshot"
        replace_in_file(self, os.path.join(self.source_folder, "build.gradle"), "JavaLanguageVersion.of(11)", "JavaLanguageVersion.of(19)")
        replace_in_file(self, os.path.join(self.source_folder, "src", "main", "java", "com", "netflix", "imflibrary", "utils", "Utilities.java"), "\"0.0.0\"", "\"%s\"" % version)
        replace_in_file(self, os.path.join(self.source_folder, "src", "main", "java", "com", "netflix", "imflibrary", "utils", "Utilities.java"), "return theClass.getPackage().getImplementationVersion();", "return \"%s\";" % version)

    def build(self):

        with open(os.path.join(self.build_folder, "gradle.properties"), "w") as f:
            f.write('version=%s' % self.version)

        stdout = io.StringIO()
        if self.settings.os == "Macos" or self.settings.os == "Linux":
            self.run("./gradlew build -x test")
            self.run("./gradlew getDependencies")
            self.run("jdeps --multi-release 19 --module-path \"$JAVA_HOME/lib/jmods\" -cp 'build/libs/*' --print-module-deps build/libs/Photon-%s.jar" % self.version, stdout=stdout)
            self.run("jlink --compress 2 --strip-debug --no-header-files --no-man-pages --module-path \"$JAVA_HOME/lib/jmods\" --output jre --add-modules java.desktop,%s" % stdout.getvalue())
        else:
            self.run("gradlew.bat build -x test")
            self.run("gradlew.bat getDependencies")
            self.run("jdeps --multi-release 19 --module-path \"%JAVA_HOME%/lib/jmods\" -cp build/libs/* --print-module-deps build/libs/Photon-%s.jar" % self.version, stdout=stdout)
            self.run("jlink --compress 2 --strip-debug --no-header-files --no-man-pages --module-path \"%JAVA_HOME%/lib/jmods\" --output jre --add-modules java.desktop,%s" % stdout.getvalue())

    def package(self):
        copy(self, pattern="*.jar", src=os.path.join(self.build_folder, "build", "libs"), dst=os.path.join(self.package_folder, "photon"))
        copy(self, pattern="*", src=os.path.join(self.build_folder, "jre"), dst=os.path.join(self.package_folder, "jre"))
        with open(os.path.join(self.package_folder, "Findphoton.cmake"), "w") as f:
            f.write('file(GLOB photon_jar_files "${CMAKE_CURRENT_LIST_DIR}/photon/*.jar")\nset(photon_files ${photon_jar_files} CACHE STRING "")\nset(photon_dir "${CMAKE_CURRENT_LIST_DIR}/photon" CACHE STRING "")\nset(photon_jre_dir "${CMAKE_CURRENT_LIST_DIR}/jre" CACHE STRING "")')

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
        self.cpp_info.builddirs = ['./']
