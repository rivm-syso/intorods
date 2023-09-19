#!/bin/bash

## conda env update -f intorods.yaml
ZONE=$(ienv | grep irods_zone_name | cut -f3 -d' ' )

source activate intorods

intorods -s local --search \
        -c checksums.wrong \
        -x -R computeResc -m type=tgsdata,source=minion,tools=intorods -q TEST- -t 8 \
        -F "source_folder"  -S ./test_deadlock /${ZONE}/home/rods/JTH_test_deadlock_2


source deactivate
