# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

## [0.0.16] - 2025-12-16

- Fix checksum calculation for scp
- Add option skip_inaccessible to ls function
- Add accessible function for fs_scp
- Add missing import to __init__.py

## [0.0.15] - 2025-04-28

- Allow applying of numeric metadata values

## [0.0.14] - 2025-04-09

- Change irods fs parameters to use only an irods environment file

## [0.0.13] - 2024-02-06

- Correctly process a checksumfile when it is not in the source directory

## [0.0.12] - 2023-10-09

### Added

- option -M to specify a JSON file with metadata as an alternative to the -m key=value argument.

## [0.0.11] - 2023-09-19

### Fixed

- Search option argument removed since it was not required and not documented
- Fixed example scripts

## [0.0.10] - 2023-09-18

### Fixed

- Github workflow download artifact destination folder (directly in main).

## [0.0.9] - 2023-09-18

### Fixed

- Some typos in the README (#6).

## [0.0.8] - 2023-09-15

### Added

- A deletefile method to the fs_local class (#1).
- Github test workflow (#2).
- uxhash as part of the package, with command line interface (#3).
- Github release workflow (#4).

### Changed

- Dependency ftputil to the project settings (#1).
- Pytest to correctly run from base directory by changing location of test
  files in test scripts (#2).

### Fixed 

- Broken import in ftp filesystem module (#1).
- The intorods.filesys.sync.sync method uses `<fs>.mkdir(path, parents=True)`,
  added `parents` kwarg to mkdir for all filesystem classes (#1).
- Filesize for ftp now directly instead of via lstat, as that gave strange results (#5).

## [0.0.7] - 2023-06-07

### Added

- Migrated internal RIVM version to github.
