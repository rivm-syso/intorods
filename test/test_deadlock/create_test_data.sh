#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

mkdir -p $${DIR}/test_data

for ((i=1;i<1001;i++)) ; do
echo TEST > $DIR/test_data/file_with_a_rather_long_name_which_might_under_the_right_circumstances_exhaust_the_error_queue_of_the_sync_process__${i}.txt
done
