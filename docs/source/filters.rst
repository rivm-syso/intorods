.. _section-filtering:

Filtering data to import
========================

There are several ways to filter the files that you want to import.

Filtering using regular expression patterns
-------------------------------------------

The :ref:`-X <option-XX>` option allows you to supply regular expression patterns for files
that you want to exclude. Patterns should match against the relative path of the input files.

Example: to skip all files ending in *.tmp*, use:

.. code-block:: console

    intorods -X ".*\.tmp$" /data/input /demoZone/data


Filtering using the yml filter files
------------------------------------

TODO