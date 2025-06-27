# TODO: Unified Content Upload Form - June 2025

**Quick Goal:** Smart content input form update.

## Section 1 - Frontend Smart single input + drag and drop

### Completed Tasks ✅

- [x] **Render the basic markup** — *COMPLETED*  
  Implemented full DOM structure with multiline text box, hidden file input, and accessible drop zone. All tests pass using role/label queries.

- [x] **Show a drag-over cue** — *COMPLETED*  
  Visual feedback system with `drag-over` class toggling implemented. DOM event simulation tests verify correct behavior.

- [x] **Open file picker on click/Enter** — *COMPLETED*  
  Drop zone click and Enter key handlers trigger hidden file input. Spy tests confirm `click()` method calls.

- [x] **Handle drag-and-drop events** — *COMPLETED*  
  All drag events properly handled with `preventDefault()` and `stopPropagation()`. FileList forwarding to validation implemented.

- [x] **Capture clipboard-pasted images** — *COMPLETED*  
  Paste event handler inspects `clipboardData.files` for JPEG/PNG. Image queuing, text box clearing, and thumbnail rendering working.

- [x] **Validate image files** — *COMPLETED*  
  Client-side validation enforces JPEG/PNG only with size limits. Toast error messages display for invalid files.

- [x] **Render thumbnail and queue image** — *COMPLETED*  
  100×100 thumbnail rendering implemented with proper image queuing for form submission.

- [x] **Classify URL vs text** — *COMPLETED*  
  `classify()` function distinguishes URLs from text with scheme inference. Fires on paste and blur events.

- [x] **Announce immediate feedback** — *COMPLETED*  
  ARIA live region provides accessibility announcements for content detection. Mutation observer tests verify messages.

- [x] **Gate the submit button** — *COMPLETED*  
  Submit button state management covers all scenarios (none, text-only, image-only, both content types).

### Remaining Frontend Tasks

- [ ] **Gracefully degrade without JS**  
  *Spec/tests*: With JavaScript disabled (or `<html class="js-disabled">`), fallback URL, text, and file inputs are visible and functional. End-to-end no-JS run confirms elements render and form submits.

- [ ] **Add developer documentation**  
  *Spec/tests*: Docs outline public events (`content:classified`, `file:queued`, `file:validationError`), tweakable constants (size limit, accepted types), and notes on extending to the future "chip list". Lint rule checks a heading "Extensibility Notes" is present.

## Section 2 — Backend Updates  

**Goal:** Accept base-64 clipboard images while preserving existing URL/text/image logic.

### Completed Backend Tasks ✅

- [x] **Detect base-64 payloads in the main view** — *COMPLETED*  
  Implemented detection logic for `data:image/(png|jpeg);base64,` prefixes. Sets `request.is_base64_image` flag correctly with comprehensive test coverage.

- [x] **Convert base-64 to `InMemoryUploadedFile`** — *COMPLETED*  
  Helper function `convert_base64_to_file()` strips prefixes, decodes base-64, and creates proper Django file objects. Includes content type mapping and error handling.

- [x] **Reuse existing size/type validation** — *COMPLETED*  
  Base-64 images flow through existing validation pipeline. Proper integration with `MAX_UPLOAD_SIZE` settings and error messages.

- [x] **Classify content type server-side** — *COMPLETED*  
  Functions `classify_content_type()` and `looks_like_url()` implemented with comprehensive logic. Returns `'image'`, `'url'`, or `'text'` with full test coverage including edge cases.

- [x] **Persist clipboard images to the Image model** — *COMPLETED*  
  Base-64 images automatically persist through existing `PicItem.ensure()` pipeline. Maintains content-based hashing and shortcode generation.

- [x] **Security hardening checks** — *COMPLETED*  
  Implemented comprehensive security measures:
  • Pre-decode size validation using `MAX_BASE64_SIZE` setting (8MB default)
  • Pillow-based MIME type verification prevents image type spoofing
  • Fail-safe behavior when Pillow unavailable (critical error)
  • Comprehensive test suite covering all security scenarios

### Remaining Backend Tasks

- [x] **Log and rate-limit base-64 uploads** — *IN PROGRESS*  
  *Spec/tests*:  
  • Successful decode logs one INFO entry: `{"event":"clipboard_image_saved","bytes":<len>}`.  
  • Malformed base-64 logs WARNING `{"event":"clipboard_image_error","reason":"DecodeError"}` and returns HTTP 400.  
  Logging test captures records and asserts count/level/JSON keys.

- [ ] **Feature flag for safe rollout**  
  *Spec/tests*: Setting `settings.ALLOW_BASE64_IMAGES = False` short-circuits the new path with HTTP 404.  
  Integration test toggles flag off and on, asserting 404 vs 200 responses.

- [ ] **End-to-end integration scenarios**  
  *Spec/tests*: Using Django test client:  
  1. POST plain text → response 302, DB record tagged `'text'`.  
  2. POST URL → response 302, record tagged `'url'`.  
  3. POST multipart JPEG file → response 302, record tagged `'image'`, file saved.  
  4. POST base-64 PNG data-URI → response 302, record tagged `'image'`, image bytes equal decode.  
  Each scenario asserts correct redirect, content-type tag, and database side-effects.

- [ ] **Developer documentation**  
  *Spec/tests*: Docs contain a section "Handling base-64 images" that lists: detection regex, size limit, Pillow verification, and `ALLOW_BASE64_IMAGES` flag. Doc-lint rule checks the section heading exists and that the regex appears verbatim.

## Progress Summary

**Frontend**: 10/12 tasks completed (83%) — Core functionality implemented  
**Backend**: 5/9 tasks completed (56%) — Security hardening and core features done  
**Next Priority**: Complete logging/rate-limiting, then feature flag implementation

## Recent Commits

- `dd94d0f` - Security hardening for base-64 uploads with comprehensive validation
- `c4c5332` - Server-side content type classification with URL detection
- `4378aca` - Base-64 image integration with existing validation pipeline
- `26b1620` - Base-64 data URI to InMemoryUploadedFile conversion
- `eb56d9a` - Submit button gating based on content validation state

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.