# Depo API Implementation Checklist

## Upload Endpoint Foundation**

### Basic POST Endpoint**

- [x] Create `UploadAPIView` with `http_method_names = ["post"]`.
- [x] Return a placeholder 200 response for POST requests.
- [x] Write `django.test` cases:
  - [x] Verify GET/PUT/DELETE return 405.
  - [x] Confirm POST returns 200.

### Content Hash Calculation**

*Other than porting test coverage for DRF APIs for PicItem.ensure these aren't needed*

- [ ] Add SHA-256 hash computation for uploaded files.
- [ ] Store computed hash in Django’s cache for idempotency checks.

#### Better version

- [x] Write `django.test` cases:
  - [x] Ensure identical files produce identical hashes.
  - [x] Validate hash storage in cache.
  - [x] File saves using `PicItem.ensure` in `settings.UPLOAD_DIR`.
    - Using path: `f"{settings.UPLOAD_DIR}/{PicItem.item.code}.{PicItem.format}"`
  - [x] `PicItem.ensure` when raising, returns `Invalid format` (500) response.
- [x] Implementation for all these tests passing.

---

## Idempotency & Metadata**

### Duplicate Detection**

- [x] Write `django.test` cases:
  - [x] Confirm duplicate uploads return 200 and header when duplicate found.
  - [x] Ensure no duplicate files are stored, they'll result in same filename.
- [x] Make changes to `core/views/upload_api.py` to pass tests.
  - [x] Query cache/database for existing file hashes.
  - [x] Return 200 with `X-Duplicate: true` header if duplicate detected.

### Automatic Metadata Computation**

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
- [x] Create `core/util/logging.py` with the `DepoLogger` class.
- [x] Define `PROJECT_TAG` as a constant (`"DEPO"`).
- [ ] Define `STANDARD_MESSAGES` dictionary with preconfigured log messages.
- [ ] Implement the `log()` method supporting all standard log levels.
- [ ] Write `django.test` cases:
  - [x] Test to ensure PROJECT_TAG is `DEPO`.
  - [x] Test to ensure class is called `DepoLogger`.
  - [ ] Validate ISO8601 time-stamp formatting.
  - [ ] Ensure the project tag appears in all logs.
  - [ ] Test all log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
  - [ ] Verify importability of `STANDARD_MESSAGES`.

### Integrate Logging into DRF Views**

- [ ] Import `StandardLogger` and `STANDARD_MESSAGES` into API views.
- [ ] Add logging at the start of request processing (`"START OF REQUEST PROCESSING"`).
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

## **Web E2E Test Rewrite**

### Rewrite web E2E test with proper HTML parsing

- [ ] Replace string manipulation with regex pattern matching for shortcode extraction
  - Use pattern: `r'href="/([A-Z0-9]+)/details"'` to extract shortcodes
  - Avoids false matches from CSS or other href attributes
- [ ] Ensure single continuous flow (not separate test methods)
  - Guest attempt → Login → Upload files → Extract shortcodes → Download/verify → Logout
- [ ] Fix shortcode extraction logic that currently finds wrong href values
- [ ] Test all upload types in single flow:
  - PNG, JPG, GIF successful uploads
  - Base64 image upload
  - Duplicate detection
  - Invalid file type rejection
  - Empty file rejection
- [ ] Verify downloaded content matches original bytes
- [ ] Test details page access for each upload
- [ ] Confirm guest can download but not upload after logout

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
