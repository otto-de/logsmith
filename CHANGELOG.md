# Change Log

All notable changes to this project will be documented in this file.
This project adheres to [Semantic Versioning](http://semver.org/).

This changelog is inspired by [keepachangelog.com](http://http://keepachangelog.com/de/).

Changes will be grouped by the following categories (and their respective version number changes):
- 'Changed' for changes in existing functionality (Major). 
- 'Removed' for now removed features (Major). 
- 'Added' for new features. (Minor).
- 'Deprecated' for soon-to-be removed features (Minor). 
- 'Fixed' for any bug fixes (Patch). 
- 'Dependency' for dependency updates (Patch).
- 'Security' in case of vulnerabilities (Patch).
- 'Notes' for additional notes.

Release dates will be in YYYY-MM-DD format.

## Unreleased

### Changed
- All tasks will now be performed as background tasks to avoid blocking the gui.
- region overwrite menu was renamed to "Overwrite region".

### Added
- Add "busy" taskbar icon to indicate that the application is performing an action.
- Add feature to assume roles in a "service" profile.
- Add the option to copy account ids and profile names to the clipboard.
- Add the option to specify a script path for each profile group that will be executed after login

### Fixed
- On login the current region text will now be updated.
- The region overwrite menu will not change text on selection.
- When not logged in, the tray icon will now display the outline variant of the icon.
- fix issue where config is not properly replaced on config edits.
- fix display of colord icons for profile groups.

## 7.0.0 - 2024-04-05

### Changed
- Each access-key now retains its own session-token to make switching between access-keys easier.
- When rotation a key, it will first try to use the session-token of the key to be rotated. If that fails, it will fetch a new session-token automatically.
- Set and rotate access keys are now directly in the menu instead of in a submenu

### Fixed
- Fix setting of access keys
- Rotation of access keys that are not named 'access-key'

## 6.3.0 - 2024-04-04 (yanked)

### Added
- Support for Google cloud projects (thanks to @3cham)
- Support for multiple aws access keys 

## 6.2.1 - 2024-01-04

### Dependency
- Dependency updates

### Notes
- This version will be a Re-Release via github action.

## 6.2.0 - 2023-06-05

### Fixed
- Dialogs should now appear in front (thanks to @MartinStarkNL)

### Changed
- Upgrade PyQT to Version 6

## 6.1.0 - 2020-01-12

### Added
- Add command line arguments to exit after login (thanks to @TomVollerthun1337)

## 6.0.0 - 2020-11-26

### Changed
- Gui and core are now decoupled in order to provide different interfaces.

### Added
- Add some basic command line arguments (thanks to @TomVollerthun1337)
- Add cli interface for all basic functions

### Fixed
- dialogs should now be opened in the foreground (thanks to @TomVollerthun1337)
- profiles will correctly updates if config is changed
- slightly increase sts timeouts to avoid sts availability issues
- set text color and text background color to black/white to that not everything is back on a dark themed os

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
