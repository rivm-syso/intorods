.. _section-checksum-files:

Using checksum files
====================

You can supply a list of checksums and files to **intorods**. This will change the behaviour of **intorods** in two ways:

* The list of files will be the files that are synchronized. No additional files will be synchronized.
* The checksums in the checksumfile are used as the checksums of the source files for verification. No checksums will be calculated.

The format of the file is as follows:

.. code-block:: console

    $ cat checksumfile  
    3e7ad645dd20348351d3a7ffa2a61b80b8944daf280a7a0089819d66fc705453  test_checksumfile_parsing.py
    c2cba4b79d42a37717fff37c52808d09c6b08f24956f0905f4deaf33d4b76707  test_sync_functions.py
    c57a3d4adbfb348d5f4db53b2ec0d90cbb4a758115251a5891d26739a40107dc  test_intorods_functions.py
    0f218d4f5147fec04ca763fa4a58e8288b070951e6aa462c691d52bb90671dd9  output2/file2

The hash is a sha256 has that can be calculated using **sha256sum**. 

The checksumfile is assumed to be in the source directory, so the supplied path is relative to the source directory.

Creating checksums in iRODS
---------------------------

By default, iRODS will not generate checksums for all dataobjects automatically. 
However, it is a good idea to do so, since it will help you protect your data integrity. 
When you use intorods with the checksum verification option :ref:`-x <option-x>`, it is almost a requirement to do so.

.. warning::

  intorods will not generate checksums in irods! If you do not configure rules to generate checksums,
  but still use the **-x** option, intorods will still work, but it will read back all files written to irods to calculate the checksum.
  This is a very inefficient mechanism, and you are not encouraged to use it!

To generate checksums for all dataojects craeted in irods, you could use a rule like:

.. code-block:: console

  acPostProcForPut {
    msiDataObjChksum($objPath, "", *Chksum)
  }

in **/etc/irods/core.re**

Creating checksum files
-----------------------

* On unix, you can use sha256sum to create checksums. It only accepts a single file as input, but the output is in the required format. With a find commando, you could do:


.. code-block:: console

  find . -type f -exec sha256sum {} 

* In the **uxhash** directory of the distribution, there is a utility **hash.py** that can create checksumfiles. For example:

.. code-block:: console

    python hash.py -o checksums.txt .

* On windows you can use something like `sha256deep.exe <https://md5deep.sourceforge.net/>`_.
