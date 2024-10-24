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

## v1.2.1 - 17/1/2023

### Fixed
- SQL syntax error

## 1.3.0 - 07/6/2023

### Added
- Dynamic categories support

### Removed
- `cached` option in latest circular

### Improved
- `CircularChecker` class now returns a sorted dict of new circulars

## v1.3.1 - 23/6/2023

### Fixed
- Changed the param name of /search to `query` from `title` to match API change

## v1.3.2 - 24/7/2023

### Fixed
- Fixed dict key error in `CircularChecker` class.

## v1.3.3 - 8/4/2024

### Improved
- The package now uses bpsapi.rajtech.me/latest/{category} instead of the params method for list and latest

## v1.4 - 12/8/24

### Fixed
- CircularChecker's false positives 

### Removed 
- Pickle method for cache storage

### Added
- mysql method for cache storage

## v1.4.1 - 24/8/24

### Fixed
- A small bug which caused an error when `amount` wasn't passed in list
- Fixed type hints having `or` instead of |

### Improved
- Many little improvements