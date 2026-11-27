QT += widgets testlib
TEMPLATE = lib
CONFIG += plugin release c++11
TARGET = caneda_d4
DESTDIR = $$OUT_PWD/plugins/generic
!exists($$CANEDA_BUILD/config.h): error("Set CANEDA_BUILD to the matching Caneda CMake build directory")
INCLUDEPATH += $$PWD/../../../src $$CANEDA_BUILD
SOURCES += probe.cpp
OTHER_FILES += probe.json
