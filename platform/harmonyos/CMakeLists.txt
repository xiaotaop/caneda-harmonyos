cmake_minimum_required(VERSION 3.16)
project(CanedaQtProbe LANGUAGES CXX)

if(NOT CMAKE_SYSTEM_NAME STREQUAL "OHOS" OR NOT OHOS_ARCH STREQUAL "x86_64")
    message(FATAL_ERROR "Use the HarmonyOS SDK toolchain with OHOS_ARCH=x86_64.")
endif()

set(saved_package_mode "${CMAKE_FIND_ROOT_PATH_MODE_PACKAGE}")
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE BOTH)
find_package(Qt5 5.15.16 EXACT CONFIG REQUIRED COMPONENTS Widgets
    PATHS "${CANEDA_QT_PREFIX}/lib/cmake/Qt5" NO_DEFAULT_PATH)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE "${saved_package_mode}")

add_library(caneda_qt_probe SHARED main.cpp)
target_link_libraries(caneda_qt_probe PRIVATE Qt5::Widgets)
