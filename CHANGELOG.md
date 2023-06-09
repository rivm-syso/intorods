# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed 

- Broken import in ftp filesystem module.
- The intorods.filesys.sync.sync method uses `<fs>.mkdir(path, parents=True)`, added parents kw to mkdir for all filesystems.

## [0.0.7] - 2023-06-07

### Added

- Migrated internal RIVM version to github.
