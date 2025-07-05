# TODO: Unified Content Upload Form - June 2025

**Quick Goal:** Smart content input form update.

## Section 1 - Frontend Remaining Tasks

- [ ] **Gracefully degrade without JS**  
  *Spec/tests*: With JavaScript disabled (or `<html class="js-disabled">`), fallback URL, text, and file inputs are visible and functional. End-to-end no-JS run confirms elements render and form submits.

- [ ] **Add developer documentation**  
  *Spec/tests*: Docs outline public events (`content:classified`, `file:queued`, `file:validationError`), tweakable constants (size limit, accepted types), and notes on extending to the future "chip list". Lint rule checks a heading "Extensibility Notes" is present.

## Section 2 — Backend Remaining Tasks

- [ ] **Developer documentation**  
  *Spec/tests*: Docs contain a section "Handling base-64 images" that lists: detection regex, size limit, Pillow verification, and `ALLOW_BASE64_IMAGES` flag. Doc-lint rule checks the section heading exists and that the regex appears verbatim.

## Section 3 — End-to-End Integration & Testing

**Goal:** Comprehensive testing of the entire upload flow from browser to database and back.

### Core Integration Scenarios

- [ ] **Basic content type routing** — *NEXT BRANCH*  
  *Spec/tests*: Using Django test client verify complete flow:  
  1. POST plain text → response 302 redirect, DB record tagged `'text'`, proper response handling
  2. POST URL → response 302 redirect, DB record tagged `'url'`, proper response handling  
  3. POST multipart JPEG file → response 302 redirect, DB record tagged `'image'`, file saved to disk
  4. POST base-64 PNG data-URI → response 302 redirect, DB record tagged `'image'`, image bytes match decode

### Browser-Level Integration Testing

- [ ] **Frontend JavaScript functionality** — *NEXT BRANCH*  
  *Spec/tests*: Real browser testing (Selenium/Playwright) for:
  • Drag and drop file handling with real files
  • Clipboard paste events with actual images  
  • Form submission and response handling
  • Error display and user feedback
  • Progressive enhancement without JavaScript

- [ ] **Cross-browser compatibility** — *NEXT BRANCH*  
  *Spec/tests*: Test matrix covering:
  • Chrome/Firefox/Safari desktop and mobile
  • File API support and fallbacks
  • Clipboard API variations
  • Form submission edge cases

### System Integration Testing

- [ ] **File system integration** — *NEXT BRANCH*  
  *Spec/tests*: Real file operations with:
  • Actual file writes to `UPLOAD_DIR`
  • File permissions and disk space handling
  • Concurrent upload scenarios
  • File cleanup and management

- [ ] **Database integration** — *NEXT BRANCH*  
  *Spec/tests*: Real database operations:
  • `PicItem.ensure()` with actual file hashing
  • Content type persistence and retrieval
  • Database constraints and error handling
  • Migration compatibility

### Performance & Load Testing

- [ ] **Upload performance benchmarks** — *NEXT BRANCH*  
  *Spec/tests*: Performance testing for:
  • Large file upload handling (up to MAX_UPLOAD_SIZE)
  • Base-64 encoding/decoding performance
  • Concurrent upload capacity
  • Memory usage patterns

### Security Integration Testing

- [ ] **End-to-end security validation** — *NEXT BRANCH*  
  *Spec/tests*: Security testing including:
  • File type spoofing attempts with real malicious files
  • Size limit enforcement under load
  • CSRF protection with real browser sessions
  • Authentication and authorization flows

## Progress Summary

**Current Branch Status:**
- Frontend: 2 remaining tasks (graceful degradation, docs)
- Backend: 1 remaining task (docs)  
- Core functionality complete with security hardening and feature flags

**Next Branch Focus:**
- Comprehensive E2E integration testing
- Browser automation testing
- Performance and security validation
- Production readiness verification

## Documentation Prompts

**Key changes implemented in this branch that should be documented:**

- Base-64 clipboard image detection using `data:image/(png|jpeg|jpg);base64,` regex patterns
- Security hardening with pre-decode size limits (`MAX_BASE64_SIZE` setting, 8MB default)
- Pillow-based MIME type verification to prevent image spoofing attacks
- Structured JSON logging for clipboard operations (`clipboard_image_saved`, `clipboard_image_error`)
- Feature flag implementation (`ALLOW_BASE64_IMAGES`) for safe production rollout
- Server-side content classification logic (`classify_content_type()`, `looks_like_url()`)
- Base-64 to `InMemoryUploadedFile` conversion pipeline with error handling
- Integration with existing validation and persistence through `PicItem.ensure()`
- Comprehensive test coverage for security scenarios and feature flag states
- Error handling patterns for malformed base-64 data and validation failures

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.