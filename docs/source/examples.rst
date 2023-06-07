Advanced examples
=================

In a typical configuration, the **intorods** script is run regularly, to check for and import
newly generated data. This section provides some typical configuration examples for this setup:

Example 1
---------

Suppose these are your synchronization requirements:

* Search the directory **/data** for subdirectories, at least two levels deep, that match the pattern **DATADIR_[0-9]{6}_INPUT**. 
* Synchronize these to the irods collection /demoZone/data, while the data is being generated.
* When the file DataComplete.txt is present in the input, mark the resulting collection as complete by setting the metadata attribute **data_complete** to **yes**, and skip this directory on subsequent runs.


.. code-block:: console

    #!/bin/bash
    SOURCE=/data
    DESTINATION=/demoZone/data
    PATTERN=DATADIR_[0-9]{6}_INPUT

    # First run copies everything to irods without verifying checksums, size or timestamp
    # Note that source contents may still change

    intorods -z --search --folder_pattern $PATTERN --completion_avu data_complete $SOURCE $DESTINATION

    # Second run only handles finished input sources, and verifies checksums.

    intorods --search --folder_pattern $PATTERN -x --completion_avu data_complete -m data_complete=yes $SOURCE $DESTINATION



