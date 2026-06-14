cmake_minimum_required(VERSION 3.10)
project(pyrx LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

set(PYRX_MIN_PYBIND11_VERSION 3.0.0)
set(PYBIND11_FINDPYTHON ON)
find_package(Python3 COMPONENTS Interpreter Development.Module REQUIRED)

find_package(pybind11 ${PYRX_MIN_PYBIND11_VERSION} CONFIG QUIET)

if(NOT pybind11_FOUND)
	set(_pyrx_bundled_pybind11_common "${CMAKE_CURRENT_SOURCE_DIR}/external/pybind11/include/pybind11/detail/common.h")
	if(EXISTS "${_pyrx_bundled_pybind11_common}")
		file(STRINGS "${_pyrx_bundled_pybind11_common}" _pyrx_pybind11_ver_lines
			REGEX "#define PYBIND11_VERSION_(MAJOR|MINOR|PATCH) ")

		foreach(_line ${_pyrx_pybind11_ver_lines})
			if(_line MATCHES "#define PYBIND11_VERSION_MAJOR +([^ ]+)$")
				set(_pyrx_pybind11_major "${CMAKE_MATCH_1}")
			elseif(_line MATCHES "#define PYBIND11_VERSION_MINOR +([^ ]+)$")
				set(_pyrx_pybind11_minor "${CMAKE_MATCH_1}")
			elseif(_line MATCHES "#define PYBIND11_VERSION_PATCH +([^ ]+)$")
				set(_pyrx_pybind11_patch_raw "${CMAKE_MATCH_1}")
			endif()
		endforeach()

		string(REGEX MATCH "^[0-9]+" _pyrx_pybind11_patch "${_pyrx_pybind11_patch_raw}")
		if(_pyrx_pybind11_patch STREQUAL "")
			set(_pyrx_pybind11_patch 0)
		endif()

		set(_pyrx_bundled_pybind11_version "${_pyrx_pybind11_major}.${_pyrx_pybind11_minor}.${_pyrx_pybind11_patch}")

		if(_pyrx_bundled_pybind11_version VERSION_LESS PYRX_MIN_PYBIND11_VERSION)
			message(FATAL_ERROR
				"Bundled pybind11 (${_pyrx_bundled_pybind11_version}) is too old for Python 3.13. "
				"Install pybind11 >= ${PYRX_MIN_PYBIND11_VERSION} and configure pybind11_DIR, "
				"or update external/pybind11.")
		endif()

		add_subdirectory(external/pybind11)
	else()
		message(FATAL_ERROR
			"pybind11 >= ${PYRX_MIN_PYBIND11_VERSION} not found. Install pybind11 and set pybind11_DIR.")
	endif()
endif()

add_subdirectory(external/RandomX)

pybind11_add_module(pyrx src/main.cpp src/rx-slow-hash.c)
if(DEFINED RANDOMX_INCLUDE)
	target_include_directories(pyrx PRIVATE ${RANDOMX_INCLUDE})
endif()
target_link_libraries(pyrx PRIVATE randomx)

