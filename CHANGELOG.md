# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- A deletefile method to the fs_local class (#1).
- Github test workflow (#2).
- uxhash as part of the package, with command line interface (#3).

### Changed

- Dependency ftputil to the project settings (#1).
- Pytest to correctly run from base directory by changing location of test
  files in test scripts (#2).

### Fixed 

- Broken import in ftp filesystem module (#1).
- The intorods.filesys.sync.sync method uses `<fs>.mkdir(path, parents=True)`,
  added `parents` kwarg to mkdir for all filesystem classes (#1).

## [0.0.7] - 2023-06-07

### Added

- Migrated internal RIVM version to github.
