#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan import ConanFile
from conan.tools.files import copy, replace_in_file
from conan.tools.files import get
from conan.tools.env import Environment
from conan.tools.env import Environment
from conan.errors import ConanInvalidConfiguration
import os, io

required_conan_version = ">=2.0"

class PhotonConan(ConanFile):

    # ---Package reference---
    name = "photon"
    version = "4.10.8"
    user = "imftool"
    channel = "stable"
    # ---Metadata---
    description = "Photon is a Java implementation of the Interoperable Master Format (IMF) standard"
    license = "Apache License 2.0"
    # ---Requirements---
    requires = []
    tool_requires = ["openjdk/[~8]@de.privatehive/stable"]
    # ---Sources---
    exports = []
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
        valid_arch = ["x86_64", "armv8"]
        if str(self.settings.arch) not in valid_arch:
            raise ConanInvalidConfiguration(f"{self.name} {self.version} is only supported for the following architectures on {self.settings.os}: {valid_arch}")

    def source(self):
        get(self, "https://github.com/Netflix/photon/archive/refs/tags/v4.10.8.zip", destination="photon", strip_root=True)
        #replace_in_file(self, os.path.join(self.source_folder, "build.gradle"), "JavaLanguageVersion.of(11)", "JavaLanguageVersion.of(19)")
        replace_in_file(self, os.path.join(self.source_folder, "photon", "build.gradle"), "id 'nebula.netflixoss' version '11.1.1'", "")
        replace_in_file(self, os.path.join(self.source_folder, "photon", "src", "main", "java", "com", "netflix", "imflibrary", "utils", "Utilities.java"), "\"0.0.0\"", "\"%s\"" % self.version)
        replace_in_file(self, os.path.join(self.source_folder, "photon", "src", "main", "java", "com", "netflix", "imflibrary", "utils", "Utilities.java"), "return theClass.getPackage().getImplementationVersion();", "return \"%s\";" % self.version)
        get(self, "https://github.com/wruppelx/photon/archive/refs/heads/feature/ADMAudio.zip", destination="photon-adm", strip_root=True)
        #replace_in_file(self, os.path.join(self.source_folder, "build.gradle"), "JavaLanguageVersion.of(11)", "JavaLanguageVersion.of(19)")
        replace_in_file(self, os.path.join(self.source_folder, "photon-adm", "build.gradle"), "id 'nebula.netflixoss' version '11.1.1'", "")
        replace_in_file(self, os.path.join(self.source_folder, "photon-adm", "src", "main", "java", "com", "netflix", "imflibrary", "utils", "Utilities.java"), "\"0.0.0\"", "\"%s-adm\"" % self.version)
        replace_in_file(self, os.path.join(self.source_folder, "photon-adm", "src", "main", "java", "com", "netflix", "imflibrary", "utils", "Utilities.java"), "return theClass.getPackage().getImplementationVersion();", "return \"%s\";" % self.version)

    def build_photon(self, buildFolder: str):
        with open(os.path.join(buildFolder, "gradle.properties"), "w") as f:
            f.write('version=%s' % self.version)

        env = Environment()
        env.define("GRADLE_USER_HOME", os.path.join(buildFolder, "gradle_home"))
        env.define("GRADLE_OPTS", "-Dorg.gradle.daemon=false")
        envvars = env.vars(self)
        with envvars.apply():
            stdout = io.StringIO()
            if self.settings.os == "Macos" or self.settings.os == "Linux":
                self.run("chmod +x gradlew", cwd=buildFolder)
                self.run("./gradlew build -x test", cwd=buildFolder)
                self.run("./gradlew getDependencies", cwd=buildFolder)
                #self.run("jdeps --multi-release 19 --module-path \"$JAVA_HOME/jmods\" -cp 'build/libs/*' --print-module-deps build/libs/Photon-%s.jar" % self.version, stdout=stdout)
                #self.run("jlink --compress 2 --strip-debug --no-header-files --no-man-pages --module-path \"$JAVA_HOME/jmods\" --output jre --add-modules java.desktop,%s" % stdout.getvalue())
            else:
                self.run("gradlew.bat build -x test", cwd=buildFolder)
                self.run("gradlew.bat getDependencies", cwd=buildFolder)
                #self.run("jdeps --multi-release 19 --module-path \"%%JAVA_HOME%%/jmods\" -cp build/libs/* --print-module-deps build/libs/Photon-%s.jar" % self.version, stdout=stdout)
                #self.run("jlink --compress 2 --strip-debug --no-header-files --no-man-pages --module-path \"%%JAVA_HOME%%/jmods\" --output jre --add-modules java.desktop,%s" % stdout.getvalue())

    def build(self):
        self.build_photon(os.path.join(self.build_folder, "photon"))
        self.build_photon(os.path.join(self.build_folder, "photon-adm"))
        if self.settings.os == "Macos" or self.settings.os == "Linux":
            self.run("cp -r \"$JAVA_HOME/jre\" \"%s\"" % self.build_folder)
        else:
            self.run("cmd /V:ON /C \"xcopy \"!JAVA_HOME!\\jre\" \"%s\\jre\" /E /H /C /I /Q\"" % self.build_folder)

    def package(self):
        copy(self, pattern="*.jar", src=os.path.join(self.build_folder, "photon", "build", "libs"), dst=os.path.join(self.package_folder, "photon"))
        copy(self, pattern="*.jar", src=os.path.join(self.build_folder, "photon-adm", "build", "libs"), dst=os.path.join(self.package_folder, "photon-adm"))
        copy(self, pattern="*", src=os.path.join(self.build_folder, "jre"), dst=os.path.join(self.package_folder, "jre"))
        with open(os.path.join(self.package_folder, "Findphoton.cmake"), "w") as f:
            f.write('set(photon_dir "${CMAKE_CURRENT_LIST_DIR}/photon" CACHE STRING "")\nset(photon_adm_dir "${CMAKE_CURRENT_LIST_DIR}/photon-adm" CACHE STRING "")\nset(photon_jre_dir "${CMAKE_CURRENT_LIST_DIR}/jre" CACHE STRING "")')

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "none")
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
        self.cpp_info.builddirs = ['./']
