# Changelog

All notable changes to Amazon Ads MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Amazon Ads MCP
- MCP server implementation for Amazon Advertising API
- Authentication providers (Direct and Openbridge)
- OpenAPI-based dynamic tool generation
- Profile and region management
- Campaign management tools
- Reporting capabilities
- Docker support
- Comprehensive test suite

### Security
- Secure token storage implementation
- OAuth state management
- Environment-based credential handling

## Version History

This changelog will be automatically updated by our CI/CD pipeline when new releases are created.

---

*Note: Releases are automatically generated based on conventional commit messages:*
- `feat:` triggers minor version bump
- `fix:` triggers patch version bump
- `BREAKING CHANGE:` or `feat!:` triggers major version bump