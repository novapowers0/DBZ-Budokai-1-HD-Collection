# dbz1 - ReXGlue Recompiled Project
# Built against the pre-built ReXGlue SDK (rexglue/). Project logic (region
# mount, mods, launcher) lives in src/ on top of the SDK.

cmake_minimum_required(VERSION 3.25)
project(dbz1 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Locate the pre-built ReXGlue SDK distribution. The SDK is bundled next to the
# project in "rexglue/". Point REXSDK_DIR at the SDK install root elsewhere.
if(NOT DEFINED REXSDK_DIR)
    set(REXSDK_DIR "${CMAKE_CURRENT_SOURCE_DIR}/rexglue")
endif()
list(PREPEND CMAKE_PREFIX_PATH "${REXSDK_DIR}")

find_package(rexglue REQUIRED CONFIG)

# User source files
set(DBZ1_SOURCES
    src/main.cpp
    src/region.cpp
    src/mods.cpp
    src/launcher/settings.cpp
    src/launcher/launcher_state.cpp
    src/launcher/mod_pipeline.cpp
    src/ingame/menu.cpp
)

# Include generated code if codegen has been run
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/generated/sources.cmake")
    include(generated/sources.cmake)
    list(APPEND DBZ1_SOURCES ${GENERATED_SOURCES})
endif()

if(WIN32)
    add_executable(dbz1 WIN32 ${DBZ1_SOURCES})
else()
    add_executable(dbz1 ${DBZ1_SOURCES})
endif()

target_include_directories(dbz1 PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/generated
    ${CMAKE_CURRENT_SOURCE_DIR}/rexglue-sdk/include
)

target_link_libraries(dbz1 PRIVATE
    rex::runtime
    rex::gpu-xenos
)

if(UNIX AND NOT APPLE)
    # Whole-archive linking for kernel hooks
    target_link_options(dbz1 PRIVATE
        -Wl,--whole-archive
        $<TARGET_FILE:rex::kernel>
        -Wl,--no-whole-archive
    )
endif()

# SDK host-app configuration: adds SDL entry point + ReXApp source,
# REXGLUE_BUILD_CONFIG define, runtime DLL staging (rexruntime, TracyClient),
# and copies the xenos GPU plugin next to the executable.
rexglue_configure_target(dbz1 GPU_PLUGINS xenos)

# Codegen target - run 'cmake --build . --target dbz1_codegen'
add_custom_target(dbz1_codegen
    COMMAND $<TARGET_FILE:rex::rexglue> codegen ${CMAKE_CURRENT_SOURCE_DIR}/dbz1_config.toml
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Generating recompiled code for dbz1"
    VERBATIM
)
