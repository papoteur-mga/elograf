# TODO - Future Improvements

This document tracks potential improvements and features to implement in Elograf.

## Features

### User Interface
- [ ] Add visual feedback when dictation starts/stops (notification or toast)
- [ ] Add status indicator showing current model in use
- [ ] Add suspend/resume button/menu item in system tray
- [ ] Show dictation state (active/suspended/stopped) in tray icon
- [ ] Add visual indicator for number conversion mode
- [ ] Improve error messages when dependencies are missing
- [ ] Add GUI to test and preview text processing rules

### Functionality
- [ ] Support for multiple language models simultaneously
- [ ] Add suspend/resume functionality for dictation (using nerd-dictation's --suspend/--resume)
- [ ] Implement dictation history/log
- [ ] Add voice commands for punctuation and formatting
- [ ] Add number-to-digits conversion option (nerd-dictation --numbers-as-digits)
- [ ] Configure timeout and idle time settings
- [ ] Add option to capitalize first character automatically
- [ ] Support for text processing configuration via Python script
- [ ] Add output mode selection (keyboard simulation vs stdout)

### Configuration
- [ ] GUI for configuring global keyboard shortcuts
- [ ] GUI for configuring nerd-dictation text processing options
- [ ] Support for custom user configuration scripts (nerd-dictation --config)
- [ ] Configure number conversion settings (min-value, separators)
- [ ] Configure punctuation and capitalization rules
- [ ] Import/export configuration profiles
- [ ] Auto-detect optimal model based on system resources
- [ ] Audio backend selection (parec, sox, pw-cat)
- [ ] Input simulation tool configuration (already supports xdotool/dotool)

### Platform Support
- [ ] Test and improve Windows support
- [ ] Test and improve macOS support
- [ ] Add support for other Wayland compositors beyond KDE

### Performance
- [ ] Optimize model loading time
- [ ] Add caching for frequently used models
- [ ] Reduce memory footprint

### Documentation
- [ ] Add video tutorial
- [ ] Create FAQ section
- [ ] Add troubleshooting guide
- [ ] Translate documentation to more languages

## Technical Debt
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Set up CI/CD pipeline
- [ ] Improve error handling and logging
- [ ] Code coverage analysis

## Bug Fixes
- [ ] (None currently tracked)

---

To propose a new feature or report a bug, please open an issue on GitHub.
