#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# ReplicantFM1: build the host renderer (tests/hostsim.c) that ht-tools/analyze.py, probe.py and plot.py drive.
# tests/run_tests.sh builds it too, but this is enough for sound work.
set -e
cd "$(dirname "$0")/.."
[ -f build/gen/felucca_tables.h ] || { echo "hostsim.sh: run ./build.sh once first (build/gen is missing)"; exit 1; }
cc -O2 -w -Ifirmware/hal -Ifirmware/bsp/chip -Ifirmware/bsp/boards/fm1 -Ifirmware/src -Ibuild/gen \
   -o build/hostsim tests/hostsim.c -lm
echo "build/hostsim ready"
