# Depo API Implementation Checklist

## Current Tasks

**Bug Fix Needed**: Fix logout flow (dev server returns 504 instead of redirect)

- Logout currently causes 504 error on dev server instead of redirecting to index
- Need to investigate logout view configuration
- After fixing, verify complete logout state:
  - User redirected to index page 
  - Navbar shows login button (not logout)
  - Upload form not present
  - Auth session properly cleared

- **Future**: Add drag and drop E2E tests and TDD fixes for upload
  functionality
- **Future**: Refactor URL scheme - change to `info/{shortcode}` for details
  pages, keep `raw/{shortcode}` for files, document URL patterns
  - More descriptive URLs that indicate content type upfront (info vs raw)
  - Consistent pattern with shortcode at end for both endpoints
- **Future**: Investigate shortcode routing flexibility
  - Make shortcode routes accept URLs without extensions and redirect to
    extension-containing versions
  - Following API design principle: "Be flexible in what you expect and explicit
    in what you give"
  - For example: `/raw/{shortcode}` could redirect to `/raw/{shortcode}.{ext}`
  - Note: This may not always be desirable - details/info pages should not
    redirect since they're about the shortcode item metadata, not the raw content
  - Consider which routes should auto-redirect vs which should stay as-is

## Upload Endpoint Foundation

### Content Hash Calculation**

*Other than porting test coverage for DRF APIs for PicItem.ensure these aren't
needed*

- [ ] Add SHA-256 hash computation for uploaded files.
- [ ] Store computed hash in Django’s cache for idempotency checks.

---

## Idempotency & Metadata

### Automatic Metadata Computation

- [ ] Compute `size` from uploaded file.
- [ ] Use `python-magic` to detect `format` from magic bytes.
- [ ] Set `mtime` and `btime` to `datetime.now()` if not provided.
- [ ] Write `django.test` cases:
  - [ ] Validate computed `size`, `format`, and timestamps.

### Metadata Override Validation**

- [ ] Accept `mtime`/`btime` overrides via headers or form fields.
- [ ] Return 400 if `format` header conflicts with computed format.
- [ ] Write `django.test` cases:
  - [ ] Test valid `mtime`/`btime` overrides.
  - [ ] Verify 400 error on format mismatch.

---

## Error Handling & Edge Cases**

### Partial Upload Cleanup**

- [ ] Use atomic transactions for database writes.
- [ ] Delete temporary files on validation errors.
- [ ] Write `django.test` cases:
  - [ ] Simulate network failures and validate no partial data persists.

### Support Multiple Upload Types**

- [ ] Add `FileUploadParser` for `application/octet-stream`.
- [ ] Add `MultiPartParser` for `multipart/form-data`.
- [ ] Write `django.test` cases:
  - [ ] Test raw binary and form-data uploads.

---

## Logging Enhancements**

### Create Logging Module**

>NOTE: This requires better planning, django already provides logging.
>So at most we should create a wrapper for it and
>apply logging to all views and file storage.

- **NOTE**: I don't know if we're continuing to create a separate logger
  - Django already has a logging system, so we might just use that
- [ ] Define `STANDARD_MESSAGES` dictionary with preconfigured log messages.
- [ ] Implement the `log()` method supporting all standard log levels.
- [ ] Write `django.test` cases:
  - [ ] Validate ISO8601 time-stamp formatting.
  - [ ] Ensure the project tag appears in all logs.
  - [ ] Test all log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
  - [ ] Verify importability of `STANDARD_MESSAGES`.

### Integrate Logging into DRF Views**

- [ ] Import `StandardLogger` and `STANDARD_MESSAGES` into API views.
- [ ] Add logging at the start of request processing
  (`"START OF REQUEST PROCESSING"`).
- [ ] Add logging after response generation (`"END OF REQUEST PROCESSING"`).
- [ ] Include request details (method, endpoint) in logs.
- [ ] Write `django.test` cases:
  - [ ] Confirm logs are emitted during API requests.
  - [ ] Validate log messages contain endpoint and method details.

---

## Integration & Finalization**

### Combine Logging and Upload Logic**

- [ ] Log `"DUPLICATE UPLOAD DETECTED"` on duplicates.
- [ ] Log `"PARTIAL UPLOAD ABORTED"` on cleanup.
- [ ] Include computed metadata in logs.
- [ ] Write `django.test` cases:
  - [ ] Validate log messages align with API behavior.

### End-to-End Testing**

- [ ] Test all requirements together:
  - [ ] Idempotency, metadata, error handling, logging.
  - [ ] Validate response codes, headers, and database state.
  - [ ] Ensure logs follow standardized format.

---

## **Post-Completion Tasks**

- [ ] Review test coverage (aim for 95%+).
- [ ] Document API endpoints with Swagger/OpenAPI.
- [ ] Update deployment scripts for new dependencies (e.g., `python-magic`).

---

## **Rich Link Preview Implementation**

### Overview

Implement Open Graph protocol meta tags for rich link previews in iMessage,
social media platforms (BlueSky, Reddit, Mastodon), and other messaging apps.
This will enable shared links to Depo shortcodes to display rich previews with
images, titles, and descriptions.

### Reference Materials

- [Apple TN2444: Best Practices for Link Previews in Messages][tn2444]
- [Open Graph Protocol Specification][ogp]
- [Apple TN3156: Create Rich Previews for Messages][tn3156]

[tn2444]: https://developer.apple.com/library/archive/technotes/tn2444/_index.html
[ogp]: https://ogp.me/
[tn3156]: https://developer.apple.com/documentation/technotes/tn3156-create-rich-previews-for-messages/

### Requirements Analysis

Based on Apple's TN2444 and Open Graph protocol specifications:

- **Required**: `og:title`, `og:type`, `og:image`, `og:url`
- **Images**: Minimum 900px width, avoid text in images, <10MB limit
- **Implementation**: Meta tags must be directly in HTML (no JavaScript)
- **Total resource limit**: 1MB for main page + 10MB for sub-resources

### Implementation Tasks

#### 1. Update Templates & Views

- [ ] **Modify `shortcode-details.html` template:**
  - Add Open Graph meta tags in `{% block head %}`
  - Dynamic meta tags based on content type (image/URL/text)
  - Include `og:title`, `og:description`, `og:image`, `og:url`, `og:type`,
    `og:site_name`

- [ ] **Update `shortcode_details` view:**
  - Enhance context to include Open Graph data
  - Generate appropriate titles/descriptions per content type
  - Handle image URLs, dimensions, and MIME types

#### 2. Content-Specific Meta Tags

- [ ] **Image Content (`ctype="pic"`):**
  - `og:type` = "website"
  - `og:image` = raw download URL (`/raw/{shortcode}`)
  - `og:title` = "Image {shortcode}" or filename if available
  - `og:description` = "View {format} image ({size} bytes)"

- [ ] **URL Content (`ctype="url"`):**
  - `og:type` = "website"
  - `og:title` = "Redirect to {domain}"
  - `og:description` = "Click to visit {url}"
  - `og:image` = default Depo logo/icon

- [ ] **Text Content (`ctype="txt"`):**
  - `og:type` = "article"
  - `og:title` = "Text Content {shortcode}"
  - `og:description` = First 100 chars of text content
  - `og:image` = default Depo logo/icon

#### 3. Models Enhancement

- [ ] **Extend context methods:**
  - Add `open_graph_context()` method to `Item` and child models
  - Include computed titles, descriptions, image URLs
  - Handle URL generation with proper domain/protocol

- [ ] **PicItem enhancements:**
  - Add image dimension detection (width/height)
  - Ensure images meet minimum size requirements
  - Add `og:image:width`, `og:image:height`, `og:image:type`

#### 4. Static Assets

- [ ] **Create default images:**
  - Depo logo/icon (minimum 900px wide for high-res devices)
  - Fallback image for non-image content
  - Store in `static/images/og-defaults/`

#### 5. Testing

- [ ] **Unit tests:**
  - Verify correct meta tags for each content type
  - Test image dimensions and MIME types
  - Validate URL generation

- [ ] **E2E tests:**
  - Test rich previews in actual messaging apps
  - Verify meta tag rendering in production
  - Check image loading and sizing

#### 6. Configuration

- [ ] **Settings additions:**
  - `OG_SITE_NAME` = "Depo"
  - `OG_DEFAULT_IMAGE` for fallback
  - Domain configuration for absolute URLs

### File Changes Required

1. **Templates:**
   - `core/templates/shortcode-details.html` - Add meta tags
   - `core/templates/base.html` - Ensure proper head structure

2. **Views:**
   - `core/views/shortcode.py` - Enhanced context

3. **Models:**
   - `core/models/item.py` - Add `open_graph_context()`
   - `core/models/pic.py` - Add image dimensions

4. **Static files:**
   - `static/images/og-defaults/` - Default images

5. **Tests:**
   - `core/tests/views/test_open_graph.py` - New test file
   - Update existing E2E tests

### Success Criteria

- [ ] Shared Depo links show rich previews in iMessage/iOS Messages
- [ ] Image shortcodes display actual images in previews
- [ ] Text/URL content shows appropriate fallback images
- [ ] Meta tags comply with Open Graph specification
- [ ] Images meet Apple's minimum size requirements (900px+)

---

## **Unified Content Upload Form**

**Goal:** Smart content input form that accepts URLs, text, and pasted images
in a single textarea.

### Frontend Remaining Tasks

- [ ] **Gracefully degrade without JS**  
  - With JavaScript disabled, fallback URL, text, and file inputs are visible
    and functional
  - End-to-end no-JS run confirms elements render and form submits

- [ ] **Add developer documentation**  
  - Document public events (`content:classified`, `file:queued`,
    `file:validationError`)
  - Document tweakable constants (size limit, accepted types)
  - Add notes on extending to the future "chip list"

### Backend Remaining Tasks

- [ ] **Developer documentation**  
  - Document "Handling base-64 images" section
  - Include: detection regex, size limit, Pillow verification,
    `ALLOW_BASE64_IMAGES` flag

### End-to-End Integration & Testing

#### Core Integration Scenarios

- [ ] **Basic content type routing**
  - POST plain text → response 302 redirect, DB record tagged `'text'`
  - POST URL → response 302 redirect, DB record tagged `'url'`  
  - POST multipart JPEG file → response 302 redirect, DB record tagged
    `'image'`, file saved to disk
  - POST base-64 PNG data-URI → response 302 redirect, DB record tagged
    `'image'`, image bytes match decode

#### Browser-Level Integration Testing

- [ ] **Frontend JavaScript functionality**
  - Real browser testing (Selenium/Playwright) for:
    - Drag and drop file handling with real files
    - Clipboard paste events with actual images  
    - Form submission and response handling
    - Error display and user feedback
    - Progressive enhancement without JavaScript

- [ ] **Cross-browser compatibility**
  - Chrome/Firefox/Safari desktop and mobile
  - File API support and fallbacks
  - Clipboard API variations
  - Form submission edge cases

#### System Integration Testing

- [ ] **File system integration**
  - Actual file writes to `UPLOAD_DIR`
  - File permissions and disk space handling
  - Concurrent upload scenarios
  - File cleanup and management

- [ ] **Database integration**
  - `PicItem.ensure()` with actual file hashing
  - Content type persistence and retrieval
  - Database constraints and error handling
  - Migration compatibility

#### Performance & Load Testing

- [ ] **Upload performance benchmarks**
  - Large file upload handling (up to MAX_UPLOAD_SIZE)
  - Base-64 encoding/decoding performance
  - Concurrent upload capacity
  - Memory usage patterns

#### Security Integration Testing

- [ ] **End-to-end security validation**
  - File type spoofing attempts with real malicious files
  - Size limit enforcement under load
  - CSRF protection with real browser sessions
  - Authentication and authorization flows

### Implementation Details

**Key features already implemented:**

- Base-64 clipboard image detection using `data:image/(png|jpeg|jpg);base64,`
  regex patterns
- Security hardening with pre-decode size limits (`MAX_BASE64_SIZE` setting,
  8MB default)
- Pillow-based MIME type verification to prevent image spoofing attacks
- Structured JSON logging for clipboard operations
- Feature flag implementation (`ALLOW_BASE64_IMAGES`) for safe production
  rollout
- Server-side content classification logic
- Base-64 to `InMemoryUploadedFile` conversion pipeline with error handling
- Integration with existing validation and persistence through
  `PicItem.ensure()`
