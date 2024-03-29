intorods option reference
=========================

.. .. argparse::
..     :filename: ../intorods.py
..     :func: get_argument_parser
..     :prog: intorods

Source options
--------------

.. _option-o:

``-o|--source_options``
    Comma-separated list of attr=value options for connecting to the source filesystem. 
    The supported options are documented in :doc:`sources`

.. _option-s:

``-s|--source_fs``
    Specifies the soucre filesystem to import data from. 
    The list of supported source filesystems is shown by running ``intorods -l``. 
    This will also show supported conifguration options for each filesystem.
    (See also :ref:`-d <option-d>` and :ref:`-o <option-o>`)

iRODS options
-------------

.. _option-d:

``-d|--irods_options``
    Comma-separated list of attr=value options for connecting to the destination irods instance.
    If no options are supplied, the configured **irods_environment.json** will be used. 
    For supported options, refer to: :ref:`iRODS options <section-source-irods>`

.. _option-R:

``-R|--resource``
    The iRODS resource to use for the destination dataobjects. If omitted, the configured default
    resource will be used. 

``-S|--ssl``
    Use ssl to conect to iRODS.

Source select options
---------------------

.. _option-scan:

``--scan``
    Scan the input directory for files to copy. This is the default, this option will normally not be needed.
    It is only present for backward compatibility.

.. _option-search:

``--search``
    When specified, the source directory will be search for directories to import. This options works in
    combination with the :ref:`-P <option-P>` option to specify a search pattern, and the :ref:`-n <option-n>` option
    that specifies the mimimum search level.

``-a|--minage``
    Minimum age of all objects in the input in order to start copying.

``-A|--maxage``
    Maximum age of all objects in the input in order to start copying.

.. _option-f:

``-f|--flag_filename``
    Specify the name of a file in the source directory that has to be present in order to start copying.
    (See also :ref:`-g <option-g>`)

.. _option-g:

``-g|--flag_age``
    Minimum age of the flag file in seconds (See the :ref:`-f <option-f>` option) before it is considered valid and copying will start.

.. _option-n:

``-n|--skip_subdirs``
    In combination with the :ref:`--search <option-search>` option, this will skip the supplied number
    of subdirs before scanning for the directory pattern. 
    For example, if your import data is under **/data/department1/datasets** 
    and **/data/department2/datasets**, you could use:

    .. code-block:: console

        $ intorods --search -n 2 /data /demoZone/data

.. _option-OO:

``-O|--completion_avu``
    This option requires an argument, which is the attribute name of an AVU. 
    It will check if this attribute is present on destination collection,and if so, skip the sync action.
    This can mainly be used to mark imports as complete using the :ref:`-m <option-m>` and 
    skipping them on subsequent runs.

.. _option-P:

``-P|--folder_pattern``
    This options is used to supply a regular expression to match the import directory names with. 
    It is only used in combinatio with the :ref:`--search <option-search>` option. 
    Example: to import directories generated by Illumina sequencers, 
    that generally have names like **230517_NB502001_0011_AHK3YLAFX5**, you can use:

    .. code-block:: console

        $ intorods --search -P [0-9]{6}_.{8}_[0-9]{4}_.{10} /data /demoZone/data 

``--scan_filter_file``
    Name of a filter file that is used to filter files when scanning the input directory. 
    See the :ref:`section on filtering <section-filtering>` for the file format.

``-T|--timestamp_age``
    TODO

``-w|--last_write``
    In order to select for copying, the last write to files has to be longer ago than the specified number.


Metadata options
----------------

.. _option-m:

``-m|--metadata``
    This option can be used to add metadata to a completely synchronized collection. 
    It can be used multiple times, and it requires an **arg=value** parameter. 
    See for details the  :ref:`section on metadata <section-metadata>` 


.. _option-M:

``-M|--metadata-file``
    This option can be used to specify a JSON file with additional metadata to add to a completely synchronized collection. 
    It can be used alternatively to or in conjunction with the -m options. 
    The format of the referenced JSON-file is a single object containing the "key": "value" pairs used as metadata.
    If both -M and -m options are used, the -m option takes precedence.
    See for details the  :ref:`section on metadata <section-metadata>` 

Copy and compare options
------------------------

.. _option-c:

``-c|--checksum_file``
    The checksum file is expected to be in the source directory. It contains a list of files to sync, with corresponding checksums.
    Each line should contain a sha256 hash, blank space and the relative filename. See also :ref:`Checksum files <section-checksum-files>`

    .. code-block:: console

      $ cat checksumfile  
      3e7ad645dd20348351d3a7ffa2a61b80b8944daf280a7a0089819d66fc705453  test_checksumfile_parsing.py
      c2cba4b79d42a37717fff37c52808d09c6b08f24956f0905f4deaf33d4b76707  test_sync_functions.py
      c57a3d4adbfb348d5f4db53b2ec0d90cbb4a758115251a5891d26739a40107dc  test_intorods_functions.py
      0f218d4f5147fec04ca763fa4a58e8288b070951e6aa462c691d52bb90671dd9  output2/file2

.. _option-cf:

``-cf|--checksum_file_format``
    This opiton is used to support some very specific checksum file formats. Normally, you will want to use the
    default FILE_FORMAT_TEXT.

``-cs|--checksum_file_schema``
    This option is only used with some very specific :ref:`checksum file formats <option-cf>`, and is not 
    documented here.

``-cf|--checksum_filter_file|--filter_file``
    Name of a filter file that is used to filter files in the checksum file. 
    See the :ref:`section on filtering <section-filtering>` for the file format.

``-t|--copy_procs``
    Number of parallel copy processes to start.

.. _option-x:

``-x|--verify_checksums``
    Verify the sha256 checksum on all files that are synchronized. 
    If this option is not specified, file comparison will only be by size and timestamp.
    The most efficient way to use this option is:
     
    * Create an irods rule that automatically adds checksums to all dataobjects. (This is a good idea anyway!)
    * Create a checksum file for your source directory. See the :ref:`section on checksum files <section-checksum-files>`

.. _option-XX:

``-X|--exclude``
    Exclude these dirs/files from the synchronization. Can be supplied multiple times. 
    This should be a regular expression that matches the relative path of the file(s) to exclude

Logging options
---------------

``--data_source_name``
    Data source name used when logging to **syslog**

``--debuglevel``
    A number in the range **1..5** that sets the debug level.

``--syslog``
    Log to syslog