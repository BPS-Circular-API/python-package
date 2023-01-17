# Changelog

All notable changes to this project will be documented in this file.

## v1.0.0 - 12/11/2022

### Added
- Initial release
- `API` class
- `CircularChecker` class

## v1.0.1 - 12/11/2022

### Fixed
- A breaking issue with import statements

## v1.0.2 - 13/11/2022

### Added
- Improvements 
- README.md

## v1.1.0 - 14/11/2022

### Added
- `CircularCheckerGroup` class
- Updated README.md
- Added CHANGELOG.md

## v1.1.1 - 15/11/2022

### Added
- `refesh_cache()` and `get_cache()` methods to `CircularCheckerGroup` class
- More minor improvements
- Debug mode to `CircularCheckerGroup` class
- Updated README.md

## v1.1.2 - 16/11/2022

### Fixed
- A bug with `CircularCheckerGroup` class where debug being False would cause an error

## v1.2.0 - 17/1/2023

### Added
- `refresh_db_con()` method to `CircularChecker` class in hopes to fix a bug

### Fixed
- A bug with `CircularChecker` class where the database connection would be closed after a while and would report 20 new circulars
- Minor improvements