# Depo Documentation

## Overview

Depo is a Django-based file sharing application that provides secure upload,
storage, and retrieval of images and other content through web interfaces and
APIs.

## Documentation Index

### For Developers

- [Development Setup](development.md) - Getting started with local development
- [Testing](testing.md) - Running tests and understanding test output
- [API Reference](api.md) - REST API endpoints and usage

### For Administrators

- [Configuration](configuration.md) - Environment variables and settings
- [Deployment](deployment.md) - Production deployment guide
- [Logging](logging.md) - Logging configuration and troubleshooting

### Architecture

- [Models](models.md) - Database models and relationships
- [Views](views.md) - Request handling and business logic
- [Security](security.md) - Security features and considerations

## Quick Start

1. **Development**: See [Development Setup](development.md)
2. **Testing**: Run `python manage.py test` (quiet by default)
3. **Production**: See [Deployment](deployment.md)

## Key Features

- Secure file upload with validation
- Base64 clipboard image support
- Hash-based deduplication
- REST API with authentication
- Quiet test execution by default
- Configurable logging levels