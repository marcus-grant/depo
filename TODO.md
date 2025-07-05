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
