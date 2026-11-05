#!/bin/sh
# SPDX-License-Identifier: GPL-3.0-only
# ReplicantFM1: build the host preview and render the firmware's own boot set to a WAV.
#   ht-tools/preview.sh OUT.wav [BARS] [BPM]
# env: SOLO=1..4 one track alone; ALTPAT=1 the FM track on the stab pattern
set -e
cd "$(dirname "$0")/.."
[ -f build/gen/felucca_tables.h ] || { echo "preview.sh: run ./build.sh once first (build/gen is missing)"; exit 1; }
cc -O2 -w -Ifirmware/hal -Ifirmware/bsp/chip -Ifirmware/bsp/boards/fm1 -Ifirmware/src -Ibuild/gen \
   -o build/ht_preview ht-tools/preview.c -lm
exec build/ht_preview "${1:-build/replicant-preview.wav}" "${2:-8}" "${3:-150}"
