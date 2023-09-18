[intorods documentation](https://intorods.readthedocs.io/en/latest/index.html)

# Introduction

intorods is a python tool to import data into irods from a variety of sources.
It was especially targetted at importing data from Next Generation Sequencers, but it can
be used for all kinds of datasets. It is made for large datasets with large files.

This tool will typically be used in a configuration where it is run regularly on a schedule,
to check for new data to import, handle the import, and annotate the generated collections with
metadata to indicate data import is complete. The options are tailored to this use case.

Some of the features of intorods:


* Read data from local filesystem, over cifs/smb, (s)ftp or scp.


* Verify data integrity using checksumfiles.


* Import data while it is being generated.


* Annotate imported collections with static or template-based metadata


* Determine completeness of the source data by file age or presence of a *flag file*.

## Installation

intorods can be installed using:

```default
$ pip install intorods
```

This will install intorods and all dependencies

It is also possible to use conda to install the dependencies of intorods:

```default
$ conda env update -f conda/intorods.yaml

$ conda activate intorods
```

## Release

To release a new version of intorods on pypi, first set new version number in main branch:
 - `CHANGELOG.md`
 - `src/intorods/__init__.py`

Then release the current version by running the following git commands:
```
git checkout release
git merge main
git tag [version number]
git push
```

A github action that releases on pypi will run with every push to the release branch.
