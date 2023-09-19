#!/bin/bash

## conda env update -f intorods.yaml

source activate intorods

intorods -s local --search \
        -x -R demoResc -m type=ngsdata -m source=ftpserver -m tools=intorods -S \
        -t 4 -n 0 /home/user/data /demoZone/home/rods/dest

source deactivate
