# Changelog

## Purpose

This document tracks completed changes to the Depo codebase, providing a historical record of implemented features, bug fixes, and other modifications.

## Unreleased Changes

## 2025-09-05

- Upload Service Layer Implementation
  - Created UploadResult dataclass for type-safe service returns
  - Implemented handle_file_upload with complete validation pipeline
  - Added comprehensive test coverage with mocking patterns
  - Service handles business logic and logging responsibilities
- Validator Refactoring for Single Responsibility
  - Updated file_too_big() to handle settings internally
  - Removed max_size parameter coupling from calling code
  - Added override_settings tests for proper isolation
- File Utility Modernization  
  - Changed save_upload signature from (file_path: Path) to (filename: str)
  - Function constructs paths using settings.UPLOAD_DIR internally
  - Returns bool for saved/exists states, raises OSError for failures
  - Moved logging responsibility from utility to service layer
- Service Logging with Comprehensive Testing
  - Added logging for successful saves, existing files, and storage errors
  - Implemented keyword-based test assertions for robustness
  - Verified appropriate log levels (info/error) usage

## 2025-08-23

- Fixed logout flow bug (405 Method Not Allowed error)
  - Root cause: navbar logout used GET link but Django's logout view requires POST
  - Solution: Changed navbar logout from `<a>` link to POST form with CSRF token
  - Added comprehensive testing for session cookie invalidation verification
  - All logout state verification now working: redirect, navbar state, session cleanup
  - Updated navbar template tests to verify POST form instead of GET link
  - Added unit test for GET request to logout returns 405 Method Not Allowed
  - E2E test now properly verifies Django's session cookie expiration behavior

## 2025-08-22

- Fixed login form to preserve 'next' parameter
  - Added hidden 'next' input field to login template
  - Login now redirects to intended destination after authentication
  - Added unit test for 'next' parameter preservation
  - E2E test verifies 'next' parameter functionality
- Added login/logout buttons to navbar
  - Login button shown when user is not authenticated
  - Logout button shown when user is authenticated  
  - Added unit tests for both authenticated and unauthenticated states
  - E2E test now verifies navbar buttons are present
- Fixed logout redirect to index page
  - Added LOGOUT_REDIRECT_URL = "/" to settings
  - Created unit test for logout redirect behavior
  - E2E test now passes for logout redirect to index
- Fixed PicItem.context() to include URL field
  - Added URL field pointing to /raw/{shortcode}.{format}
  - Fixed template to check for 'pic' instead of 'image' ctype
  - Updated view to properly structure context for PicItem
  - Added unit tests for context structure and HTML rendering
  - E2E test now verifies image tags are rendered with correct src

## 2025-08-21

- Duplicate Detection implementation
  - Duplicate uploads return 200 with X-Duplicate: true header
  - No duplicate files stored (same filename reused)
- Content Hash Calculation - SHA-256 hash for uploads with PicItem.ensure integration
  - Identical files produce identical hashes
  - Hash validation in cache
  - Files saved using PicItem.ensure in settings.UPLOAD_DIR
  - Invalid format returns 500 response
- Basic POST Endpoint - UploadAPIView with POST-only support
  - GET/PUT/DELETE return 405, POST returns 200
- CLAUDE.md and TODO.md reorganization - separated instructions from tasks
- Logging Module - DepoLogger class with PROJECT_TAG constant
  - Created core/util/logging.py with DepoLogger class
  - Defined PROJECT_TAG as constant ("DEPO")
  - Tests ensure PROJECT_TAG is "DEPO"
  - Tests ensure class is called DepoLogger
- Upload Endpoint Foundation - basic POST endpoint with hash calculation
- Duplicate Detection - idempotent uploads with X-Duplicate headers
- Details page access tests - verify /{shortcode}/details endpoints work (bug documented)
- Download verification tests - raw file downloads with content matching and no HTML
- Invalid file rejection tests - .txt, .xyz, empty files with proper error verification
- File upload tests - PNG, JPG, GIF uploads with helper functions
- Login flow tests - guest verification, failed/successful login
- Test fixtures consolidation - centralized image data constants

## 2025-08-20

- E2E Web Test Rewrite - COMPLETED
  - Replaced string manipulation with BeautifulSoup HTML parsing
  - Single continuous flow test (not separate test methods)
  - Fixed shortcode extraction logic
  - Test all upload types: PNG, JPG, GIF, invalid files (.txt, .xyz), empty files
  - Download verification with content matching
  - Details page access tests
  - Guest can download but not upload after logout
  - Logout test (partially - redirect to index commented out pending navbar fix)
  - Guest download verification test
  - Guest upload prevention test
  - Index page verification after logout
  - Added commit message format rule: no signature block
