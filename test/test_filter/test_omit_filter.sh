#!/bin/bash

## conda env update -f intorods.yaml
ZONE=$(ienv | grep irods_zone_name | cut -f3 -d' ' )

source activate intorods

intorods -s local -p ./source/input -C /${ZONE}/path \
        --scan --scan_filter_file filter_omit.yml -x \
	-R computeResc -t 1 -S

#      -X ".*\.y" \


