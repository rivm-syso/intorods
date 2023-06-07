#!/bin/bash

## conda env update -f intorods.yaml
ZONE=$(ienv | grep irods_zone_name | cut -f3 -d' ' )

source activate intorods

intorods -s local -p ./source -P "basedir" -C /${ZONE}/home/rods/test_filter_11 \
        --scan_filter_file filter_a_dir.yml \
	-x -R computeResc -m tools=intorods -q TEST- -t 1 \
        -F "source_folder"  -S

#      -X ".*\.y" \


source deactivate
