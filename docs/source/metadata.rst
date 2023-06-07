.. _section-metadata:

Setting metadata
================

The **intorods** script can set metadata on collections that are successfully synchronized.
The **-m** option allows you to set *static metadata* or *template metadata*.

Setting static metadata
-----------------------

Example of setting static metadata::

    intorods source_dir /demoZone/data/dest_coll -m attr1=value1 -m attr2=value2

As shown in the example above, multiple **-m** options are allowed.


Using templates in metadata
---------------------------

It is also possible to use template variables in the value part of metadata. 
Supported template variables are:

======== ==============
Template Expanded value
======== ==============
%t       unix timestamp
%sf      Basename of source directory
%sp      Full source path
%df      Basename of destination collection
%dp      Full destination collection
======== ==============

For example, this command will set the metadata attribute **source_directory** to the full path of the source dir,
and the attribute **import_time** to the time the data import was completed::

    intorods source_dir /demoZone/data/dest_coll -m source_directory=%sp -m import_time=%t

Using the metadata *complete* flag
------------------------------------

If you run the intorods script periodically, to scan for new directories to import, or to import data while it is being 
generated, the option to set metada can be used in combination with the **-k** flag.

This flag specifies a metadata attribute that you use to indicate a colletion has been imported completely. 
If intorods finds this attribute onm a destination collection, it will assume the import is complete, and not compare directories again.

For example::

    intorods -k import_complete -m import_complete=true --search /data -P dataset_[0-9]* /demoZone/data 

This command will search the directory **/data** for subdirectories matching **dataset_[0-9]\**. 
Suppose it finds a directory **/data/dataset_2301**. It will now:

* Check if collection /demoZone/data/dataset_2301 exists.
* If so, verify if a metadata attribute **import_complete** is present
* If not, import the data from /data/dataset_2301
* If the import runs successfully, set metadata attr **import_complete** to **true** on **/demoZone/data/dataset_2301**.

A subsequent scan for datasets to import will skip the already-imported directory, because the metadata attribute is present.



