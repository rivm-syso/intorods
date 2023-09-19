#!/bin/bash

## conda env update -f intorods.yaml
ZONE=$(ienv | grep irods_zone_name | cut -f3 -d' ' )

source activate intorods

intorods -s local --search \
        -c checksums.wrong \
        -x -R computeResc -m type=tgsdata -m source=minion -m tools=intorods -t 8 \
        -S ./test_deadlock /${ZONE}/home/rods/JTH_test_deadlock_2


source deactivate
