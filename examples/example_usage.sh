#!/bin/bash

## conda env update -f intorods.yaml

source activate intorods

intorods -s local --search /home/user/data -C /demoZone/home/rods/dest \
        -x -R demoResc -m type=ngsdata,source=ftpserver,tools=intorods -q WGSTB- -S \
        -t 4 -n 0

source deactivate
