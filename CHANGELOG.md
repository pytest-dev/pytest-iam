# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Versions follow [Semantic Versioning](https://semver.org/>) (<major>.<minor>.<patch>).

## [0.2.3] - 2025-07-09

### Fixed

- Use in-memory agnostic database instead of SQLite.

## [0.2.2] - 2025-06-25

### Fixed

- Support for Canaille 0.0.77.

## [0.2.1] - 2025-06-06

### Fixed

- Support for Canaille 0.0.75.

## [0.2.0] - 2025-04-24

### Added

- Implement `test_client` attribute.
- Implement `logout` method.
- Support for OIDC `create` prompt.

## [0.1.1] - 2025-04-04

### Changed

- Update to Canaille 0.0.70.
- Disable http access logs.

## [0.1.0] - 2024-07-25

### Changed

- Update to Canaille 0.0.54. This break the way models are saved and deleted (`iam_server.backend.save(user)` instead of `user.save()`).
  Please check the documentation to see examples.
- Documentation uses Shibuya theme.

## [0.0.12] - 2024-04-22

### Changed

- Configuration is read from `.pytest-iam.env`
- Configuration is read from environment vars prefixed by `PYTEST_IAM_`

## [0.0.11] - 2024-04-22

### Changed

- Ignores local .env #3

### Removed

- Stop Python 3.8 support

## [0.0.10] - 2024-04-12

### Changed

- Move the repository to https://github.com/pytest-dev/pytest-iam
- GHA support #1

## [0.0.9] - 2024-03-30

### Added

- Canaille 0.0.44 support

## [0.0.8] - 2024-03-14

### Added

- Loose dependency versions.

## [0.0.7] - 2024-03-12

### Added

- Display Canaille debug logs by default.

## [0.0.6] - 2024-01-24

### Fixed

- python <=3.8 incompatible typing

## [0.0.5] - 2023-12-22

### Added

- `iam_configuration` fixture

## [0.0.4] - 2023-12-15

### Fixed

- Ensure model instances are created within the Canaille application context.

## [0.0.3] - 2023-08-31

### Added

- Documentation draft
- Implement `Server.random_token`
- Loose canaille dependency

## [0.0.2] - 2023-08-21

### Added

- Implement `Server.consent` and `Server.login`

## [0.0.1] - 2023-08-17

### Added

- Initial release
