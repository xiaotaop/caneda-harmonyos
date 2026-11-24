QT += widgets testlib
TEMPLATE = lib
CONFIG += plugin release c++11
TARGET = caneda_d2
DESTDIR = $$OUT_PWD/plugins/generic
SOURCES += probe.cpp
OTHER_FILES += probe.json
