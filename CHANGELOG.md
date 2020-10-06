# Change Log

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

This changelog is inspired by [keepachangelog.com](http://http://keepachangelog.com/de/)

## Unreleased

### Added
- Add some basic command line arguments

## 5.0.0 - 2020-09-11

### Changed
- MFA shell command fetcher does not assume specific token-string format anymore, but you have to provide a bash command that fetches the exact token (see README for example).

### Fixed
- handling of account ids with leading zeros
- catch and handle shell timeouts
- react to keyboard input while qt event loop is running

## 4.1.0 - 2020-06-25

### Added
- option to logout of your current profiles. All profiles will be removed from your .aws/credentials and .aws/config  
- session check will now have a timeout to fail faster if no connection can be established 
- add option to chain assume profiles
- added writing support file for active group (again)

## 4.0.0 - 2020-05-11

### Changed
- removed writing of support files for active account and team
- username will be used as session name

## 3.1.0 - 2020-01-30

### Added
- config dialog now has a button to test the mfa command
- logs will now contain stderr of failed shell commands 

## 3.0.0 - 2020-01-16

### Changed
- your personal access key will be saved in the 'access-key' profile
- remove hardcoded shell command to fetch mfa token. There is now an input field in the config dialog

### Added
- config dialog shows the application version in its title

## 2.1.0 - 2019-11-29

### Added
- check and create .aws directory on startup

### Fixed
- Fix for "write group file" checkbox

## 2.0.0 - 2019-11-18

### Added
- Option to write one of the profiles as default profile
- Config dialog now uses a monospace font
- Tabs are now somewhat usable in config dialog
- Option to write support files

### Fix
- use layouts in config dialog
- app does not crash with malformed config yaml

## 1.0.0 - 2019-11-11

### Added
- switch profiles 
- switch regions
- keeps you logged in
- removes unused profiles  
- icon will change color, you see which profiles you are using
- set access key
- rotate access key
