# Depo API Implementation Checklist

## Current Tasks

### **ACTIVE: View Architecture Refactoring**

**Problem**: Upload view (`core/views/upload.py`) has 290+ lines with
business logic mixed into view code, making rapid changes difficult.

**Implementation Tasks**:

- **NEXT**: Integrate service into view layer
  - Update upload view to use handle_file_upload service
  - Replace existing business logic with service calls
  - Fix failing integration test for save_upload signature change
  - Ensure view becomes thin controller focused on HTTP concerns
- **Future**: Refactor UploadResult to use associated model instance
  - File type can be determined from PicItem.format property
  - Eventually Item models will include FileItem base for all file-backed items
  - This will simplify service interface and reduce duplication
- Create `core/util/` directory with utility modules (IN PROGRESS):
  - [x] Created `core/util/validator.py` with `looks_like_url()` function
  - [x] Created `core/util/content.py` with `classify_type()` function
  - `upload.py` functions from upload.py lines 160-210:
    - [x] Moved `validate_upload_bytes()` to validator.py
    - [x] Extracted empty file validation from `process_file_upload()`
          to `file_empty()` in validator.py
    - [x] Extracted size limit validation from `process_file_upload()`
          to `file_too_big()` in validator.py
    - [x] Renamed `validate_upload_bytes()` to `file_type()` for consistency
    - [x] Cleaned up file type validation to use single `file_type()` function with `if not file_type(data):`
    - [x] Extracted file I/O operations to `save_upload()` in files.py with proper error handling
    - **WIP**: Business logic placement for filename/filepath generation - multiple options identified:
      - Option A: Pure utility function (no model changes) - best testability/separation
      - Option B: Model filename property only - simple, good separation
      - Option C: Separate file management service - added abstraction
      - Option D: Settings-agnostic model + path builder - maximum flexibility
      - Option E: Current approach (properties with settings) - hard to test, tight coupling
      - Option F: Context-aware properties - good flexibility
      Current implementation (Option E) causes test mocking issues, suggests wrong placement
    - **Note**: Temporary checkpoint commit made - will be merged/replaced with final implementation
    - **Future consideration**: Consolidate multiple if-statement validators into single function
      that returns first failure message or None if valid, mapping validators to error messages
    - **Future consideration**: Move `file_type()` from validator.py to content.py since it's
      content classification rather than validation
    - **Important**: Current file type handling mixes classification and validation - need to
      reconsider architecture since validators should only validate, not classify content
  - [x] `content.py` functions completed:
    - [x] Created unit tests for `convert_base64_to_file()` function
    - [x] Moved `convert_base64_to_file()` function from upload.py  
  - `files.py`
    - Consolidate file saving, error handling from both upload.py and upload_api.py
- Refactor `web_upload_view()` & `upload_view_post()` to be...
  - thin controllers calling utility functions
- Extract test logic: split `test_upload.py` (800+ lines) into...
  - focused test modules by functionality
- Standardize error response patterns across
  - `upload.py`
  - `upload_api.py`
  - `raw_download.py`
- Clean up after refactoring:
  - Remove dead code from upload.py after function moves
  - Remove unused imports (base64, BytesIO, Optional, etc.)
  - Verify no orphaned TODOs or comments

**Files to modify**:

- `core/views/upload.py` - reduce from 290 to ~50 lines
- `core/views/upload_api.py` - extract shared logic with upload.py
- `core/tests/views/test_upload.py` - split into multiple focused test files
- Create new:
  - `core/utils/upload.py`
  - `core/utils/content.py`
  - `core/utils/files.py`

**Acceptance criteria**:

- Views are <256 lines
- business logic in testable utility modules
- no code duplication between web and API upload paths

### **ACTIVE: Database Schema Finalization**  

**Problem**: Item model has naming inconsistencies and TODO comments that
affect database structure, risking nasty migrations post-MVP.

**Implementation Tasks**:

- Fix field naming in `core/models/item.py`:
  - Rename `mtime` to `ctime`
    - *(line 47-49 TODO comment - metadata change time, not content change)*
  - Review `code`/`hash` field split logic in `ensure()` method (lines 104-124)
  - Standardize field lengths and constraints across Item/PicItem/LinkItem
- Address model inheritance concerns:
  - Review `get_child()` method composition vs inheritance (line 127 TODO)
  - Ensure consistent `context()` methods across all Item subclasses
- Add FileItem abstraction for file-backed content types:
  - Create intermediate model/mixin for items with file storage
  - Move common file properties (filename, filepath, etc.) to FileItem
  - PicItem should compose/inherit from FileItem
  - Future file types (documents, videos) will use FileItem base
  - This will fix type issues where services expect file properties
  - **Architecture Decision**: Keep current composition pattern (OneToOne to Item)
    but add FileItem as Python abstract base class/mixin for better type safety
    - Avoids complex database migrations
    - Provides clean Python interface via ABC or Protocol
    - Services can type hint against FileItem interface
    - Maintains flexibility of current schema
- Migration planning:
  - Identify any other field renames needed before MVP
  - Verify foreign key relationships in PicItem/LinkItem are optimal
  - Test that schema supports planned URL/text content types

**Files to modify**:

- `core/models/item.py` - field renames, method cleanup
- `core/models/pic.py` - ensure consistency with Item base class  
- `core/models/link.py` - review relationship structure
- Create migration for `mtime` -> `ctime` rename
- Update all references to renamed fields in views/tests

**Acceptance criteria**: No TODO comments affecting:

- DB schema
- consistent field naming patterns
- migration plan documented
- all tests pass with new schema

### **ACTIVE: Basic Project Documentation**

**Problem**: Need maintainable documentation before MVP deployment to support
future development when returning to project less frequently.

**Implementation Tasks**:

- Create `docs/architecture.md` with concise overview:
  - Models: Item, PicItem, LinkItem - purpose and key fields
  - Views: upload, shortcode, auth flows - what each does
  - URLs: routing patterns and shortcode system
  - Templates: base structure and key templates
  - Key settings: UPLOAD_DIR, authentication, file handling
- Document deployment basics in `docs/deployment.md`:
  - Environment setup requirements
  - Database migration process
  - Static file handling
  - Production settings overview
- Update README.md with:
  - Project purpose and core functionality
  - Quick setup instructions
  - Link to detailed documentation

**Files to create/modify**:

- `docs/architecture.md` - Core system overview
- `docs/deployment.md` - Deployment guide
- `README.md` - Project overview and setup
- Ensure docs/ directory structure

**Acceptance criteria**: Developer can understand project structure from:

- documentation
- deployment process is documented
- README explains what Depo does

### **ACTIVE: Basic Project Documentation**

**Problem**: Need maintainable documentation before MVP deployment to support future development when returning to project less frequently.

**Implementation Tasks**:

- Create `docs/architecture.md` with concise overview:
  - Models: Item, PicItem, LinkItem - purpose and key fields
  - Views: upload, shortcode, auth flows - what each does
  - URLs: routing patterns and shortcode system
  - Templates: base structure and key templates
  - Key settings: UPLOAD_DIR, authentication, file handling
- Document deployment basics in `docs/deployment.md`:
  - Environment setup requirements
  - Database migration process
  - Static file handling
  - Production settings overview
- Update README.md with:
  - Project purpose and core functionality
  - Quick setup instructions
  - Link to detailed documentation

**Files to create/modify**:

- `docs/architecture.md` - Core system overview
- `docs/deployment.md` - Deployment guide
- `README.md` - Project overview and setup
- Ensure docs/ directory structure

**Acceptance criteria**: Developer can understand project structure from documentation, deployment process is documented, README explains what Depo does

### **ACTIVE: Deployment and Backup Strategy Implementation**

**Problem**: Need deployment pipeline and backup procedures before
family/early users start using the system.
Must ensure zero data loss with 1-2 day acceptable restore window.

**Deployment Implementation (Simple approach for controlled access)**:

- Create single `Dockerfile` with production Django settings
- Basic `docker-compose.yml` for consistent local/production environments  
- Minimal Ansible playbook (`ansible/deploy.yml`) that:
  - Takes database backup before deployment
  - Builds and deploys new container
  - Keeps previous container for rollback
  - Handles environment variables via `.env` file
- nginx configuration for:
  - Reverse proxy to Django container
  - Direct serving of static files
  - Let's Encrypt SSL setup

**Backup Implementation (100MB/month scale)**:

- **Primary backup**: Borgbackup to homelab
  - Create `scripts/backup-borg.sh`:
    - Daily SQLite dump: `sqlite3 db.sqlite3 .dump > backup.sql`
    - Borg backup of database dump + entire `uploads/` directory
    - Retention: 7 daily, 4 weekly, 6 monthly snapshots
  - Add to cron for daily 2am execution
- **Secondary backup**: Weekly restic to object store  
  - Create `scripts/backup-restic.sh`:
    - Sync borg repository to object store for offsite copy
    - Run weekly via cron
- **Restore procedures**:
  - Create `scripts/restore.sh` with options for borg/restic sources
  - Document exact steps to restore database + files
  - Test restore procedure monthly

**Files to create**:

- `Dockerfile` - Simple production container
- `docker-compose.yml` - Development environment
- `docker-compose.prod.yml` - Production overrides
- `ansible/deploy.yml` - Basic deployment playbook
- `scripts/backup-borg.sh` - Primary backup script
- `scripts/backup-restic.sh` - Offsite backup script  
- `scripts/restore.sh` - Restore helper script
- `docs/operations.md` - Deployment, backup, restore documentation

**Acceptance criteria**:

- Automated daily backups running
- restore tested successfully
- deployment reduces to single Ansible command
- zero data loss verified

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

## Architecture Reconsiderations

- **Django Service Layer**:
  <https://github.com/HackSoftware/Django-Styleguide?tab=readme-ov-file#services>
  - Read this guide and plan refactoring tasks around service layer patterns
  - Focus on services, selectors, and proper separation of concerns
  - Views and models  don't necessarily follow these guidelines yet
  - Util modules - some might need rethinking into service modules/funcs/classes

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
