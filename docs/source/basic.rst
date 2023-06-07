Basic usage examples
====================

To simply import a directory to a collection in irods, run:

.. code-block:: console

    $ intorods source_dir /demoZone/data/destination

Import a directory using four processes:

.. code-block:: console

    $ intorods -t 4 source_dir /demoZone/data/destination

Import a directory and verifiy checksums:

.. code-block:: console

    $ intorods -x source_dir /demoZone/data/destination


Using the search option
-----------------------

Search all directories that match the pattern DATA_[0-9]{6}_.* under a directory **/data**, 
and import those to subcollections of **/demoZone/data**, verifying checksums::

    intorods --search -P DATA_[0-9]{6}_.* -x /data /demoZone/data

Suppose this is my directory layout:

.. code-block:: console

    /data
    ├── DATA_230611_test1
    ├── DATA_221131
    ├── DATA_220815_test2         
    └── DATA_220730_pilot

It will import all directories except **DATA_221131**, since it does not match the pattern.
