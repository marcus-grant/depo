# Changelog

## Purpose

This document tracks completed changes to the Depo codebase, providing a historical record of implemented features, bug fixes, and other modifications.

## Unreleased Changes

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
