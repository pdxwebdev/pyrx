import os
import re
import sys
import platform
import subprocess

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    @staticmethod
    def _get_cmake_version():
        out = subprocess.check_output(["cmake", "--version"])
        match = re.search(r"version\s*([\d.]+)", out.decode())
        if not match:
            raise RuntimeError("Unable to determine CMake version")
        return tuple(int(part) for part in match.group(1).split("."))

    @staticmethod
    def _get_pybind11_cmakedir():
        try:
            return subprocess.check_output(
                [sys.executable, "-m", "pybind11", "--cmakedir"],
                universal_newlines=True,
            ).strip()
        except Exception:
            return ""

    def run(self):
        try:
            cmake_version = self._get_cmake_version()
        except OSError:
            raise RuntimeError(
                "CMake must be installed to build the following extensions: "
                + ", ".join(e.name for e in self.extensions)
            )

        if cmake_version < (3, 10, 0):
            raise RuntimeError("CMake >= 3.10.0 is required")

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = [
            "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=" + extdir,
            "-DPython3_EXECUTABLE=" + sys.executable,
            "-DPython3_FIND_STRATEGY=LOCATION",
        ]

        pybind11_cmakedir = self._get_pybind11_cmakedir()
        if pybind11_cmakedir:
            cmake_args += ["-Dpybind11_DIR=" + pybind11_cmakedir]

        cfg = "Debug" if self.debug else "Release"
        build_args = ["--config", cfg]

        if platform.system() == "Windows":
            cmake_args += [
                "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}".format(cfg.upper(), extdir)
            ]
            if sys.maxsize > 2**32:
                machine = platform.machine().lower()
                if machine in ("arm64", "aarch64"):
                    cmake_args += ["-A", "ARM64"]
                else:
                    cmake_args += ["-A", "x64"]
            build_args += ["--", "/m"]
        else:
            cmake_args += ["-DCMAKE_BUILD_TYPE=" + cfg]
            if "CMAKE_BUILD_PARALLEL_LEVEL" not in os.environ:
                build_args += ["--", "-j{}".format(os.cpu_count() or 2)]

        env = os.environ.copy()
        env["CXXFLAGS"] = '{} -DVERSION_INFO=\\"{}\\"'.format(
            env.get("CXXFLAGS", ""), self.distribution.get_version()
        )
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        subprocess.check_call(
            ["cmake", ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env
        )
        subprocess.check_call(
            ["cmake", "--build", "."] + build_args, cwd=self.build_temp
        )


setup(
    name="pyrx",
    version="0.0.5",
    author="Jethro Grassie",
    author_email="jtgrassie@users.noreply.github.com",
    description="Python RandomX hashing module",
    long_description="",
    ext_modules=[CMakeExtension("pyrx")],
    cmdclass=dict(build_ext=CMakeBuild),
    zip_safe=False,
)
