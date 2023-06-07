#!/bin/sh

ZONE=$(ienv | grep irods_zone_name | cut -f3 -d' ' )

SOURCE=<some share>
NAME=`basename $SOURCE`
DIR=${SOURCE%/*}

IRODS_COLL=/${ZONE}/home/rods/dest

imkdir -p ${IRODS_COLL}

IRODS_PATH=${IRODS_COLL}/${NAME}

CHECKSUM_FILE=${SOURCE}/checksums.txt

irm -rf ${IRODS_PATH} 2> /dev/null
rm -rf ${CHECKSUM_FILE}

echo RUN iput time test

## { time iput -a -f -I -K -N 8 -P -R compResc -r -v ${SOURCE}  ${IRODS_COLL} ; } 2> iput.time

irm -rf ${IRODS_PATH} 2> /dev/null

echo RUN irsync time test

{ time irsync -K -N 8 -R compResc -r -v ${SOURCE}  i:${IRODS_PATH} ; } 2> irsync.time

irm -rf ${IRODS_PATH} 2> /dev/null

echo RUN intorods time test

# GEN CHECKSUMS

echo " time python uxhash/hash.py -d ${SOURCE} -o ${CHECKSUM_FILE} "
{ time python uxhash/hash.py -d ${SOURCE} -o ${CHECKSUM_FILE} ; } 2> hash.time

{ time intorods -s local -p ${DIR} -C ${IRODS_COLL} -x -R compResc -c checksums.txt -f checksums.txt -S ;} 2> torods.time


