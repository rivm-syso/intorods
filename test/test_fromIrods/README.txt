1. Execute the following script to create *many* small files with random content:
(there are already 100000 files under /demoZone/home/rods/test_lots_of_files)

icd /demoZone/home/rods/test_lots_of_files
for n in {1..10000}; do
    OUT_FILE=test_file$( printf %05d "$n" ).bin
    #dd if=/dev/urandom of=$OUT_FILE bs=1 count=$(( RANDOM + 1024 ))
    dd if=/dev/urandom of=$OUT_FILE bs=1 count=$(( 1024 ))
    iput -b $OUT_FILE
    rm $OUT_FILE
done

2. Get a file containing all created hashes:

iquest "  - %s" "SELECT  META_DATA_ATTR_VALUE WHERE META_DATA_ATTR_NAME = 'sys::object_id' AND COLL_NAME = '/demoZone/home/rods/test_lots_of_files'" --no-page > random_hashes.txt

cat random_hashes.txt | shuf > hashes_100k.txt

3. make it a yml-file by adding:

---
object_ids:
  - a473a7d8-72d4-4080-96d7-d5bb1ccd5983
  - 2b7f37fe-9c03-4944-9386-347a071de2ba
[...]
files:
  - /demoZone/home/rods/test_lots_of_files/does_not_exists.bin
  - /demoZone/home/rods/test_lots_of_files/test_file99999.bin
[...]


4. call fromIrods.py with either yaml-file as input or using appropriate option
