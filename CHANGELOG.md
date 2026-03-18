# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [0.1.2] - 2026-03-17

### Changed
- Decoupled connection management from `start_manual_control()`. It now requires an external connection (`drone.connect()`).
- Manual control examples updated to use `with LiteWing() as drone:` and `drone.connect()`.
- `run_manual_control` now automatically calls `drone.arm()` if the drone is not already armed.

## [0.1.1] - 2026-03-12

### Changed
- Version is now auto-synced from `pyproject.toml` via `importlib.metadata` — single source of truth.
- Signal handler (`Ctrl+C` emergency stop) is now opt-in via `install_signal_handler` parameter.
- `install.bat` now works correctly when run from any directory (`pushd`/`popd`).

### Fixed
- Version mismatch between `pyproject.toml` and `__init__.py`.
- README manual install section no longer uses editable mode (`-e`).

## [0.1.0] - 2025-02-17

### Added
- Initial release of the LiteWing Python library.
- `LiteWing` main class with connection, flight, sensor, and LED control.
- Cascaded PID position hold controller using optical flow.
- Manual (keyboard/joystick) control with two hold modes: `"current"` and `"origin"`.
- `PIDConfig` class for tuning position and velocity PID gains.
- `SensorData` snapshot class for reading height, velocity, position, and battery.
- `LEDController` for NeoPixel LED color, blinking, and clearing.
- `FlightLogger` for CSV flight data recording.
- Firmware Z-axis parameter tuning (`thrust_base`, `z_position_kp`, `z_velocity_kp`).
- Waypoint navigation (`fly_to`, `fly_path`).
- Context manager support for safe emergency stops.
- Three tiered example scripts (beginner, intermediate, advanced).
- Full API reference documentation.
