# Depo API Implementation Checklist

## **Phase 1: Logging Enhancements**

### **Step 1.1: Create Logging Module**

- [x] Create `core/util/logging.py` with the `DepoLogger` class.
- [x] Define `PROJECT_TAG` as a constant (`"DEPO"`).
- [ ] Define `STANDARD_MESSAGES` dictionary with preconfigured log messages.
- [ ] Implement the `log()` method supporting all standard log levels.
- [ ] Write `django.test` cases:
  - [x] Test to ensure PROJECT_TAG is `DEPO`.
  - [x] Test to ensure class is called `DepoLogger`.
  - [ ] Validate ISO8601 timestamp formatting.
  - [ ] Ensure the project tag appears in all logs.
  - [ ] Test all log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).
  - [ ] Verify importability of `STANDARD_MESSAGES`.

### **Step 1.2: Integrate Logging into DRF Views**

- [ ] Import `StandardLogger` and `STANDARD_MESSAGES` into API views.
- [ ] Add logging at the start of request processing (`"START OF REQUEST PROCESSING"`).
- [ ] Add logging after response generation (`"END OF REQUEST PROCESSING"`).
- [ ] Include request details (method, endpoint) in logs.
- [ ] Write `django.test` cases:
  - [ ] Confirm logs are emitted during API requests.
  - [ ] Validate log messages contain endpoint and method details.

---

## **Phase 2: Upload Endpoint Foundation**

### **Step 2.1: Basic POST Endpoint**

- [ ] Create `UploadAPIView` with `http_method_names = ["post"]`.
- [ ] Return a placeholder 200 response for POST requests.
- [ ] Write `django.test` cases:
  - [ ] Verify GET/PUT/DELETE return 405.
  - [ ] Confirm POST returns 200.

### **Step 2.2: Content Hash Calculation**

- [ ] Add SHA-256 hash computation for uploaded files.
- [ ] Store computed hash in Django’s cache for idempotency checks.
- [ ] Write `django.test` cases:
  - [ ] Ensure identical files produce identical hashes.
  - [ ] Validate hash storage in cache.

---

## **Phase 3: Idempotency & Metadata**

### **Step 3.1: Duplicate Detection**

- [ ] Query cache/database for existing file hashes.
- [ ] Return 200 with `X-Duplicate: true` header if duplicate detected.
- [ ] Write `django.test` cases:
  - [ ] Confirm duplicate uploads return 200 and header.
  - [ ] Ensure no duplicate files are stored.

### **Step 3.2: Automatic Metadata Computation**

- [ ] Compute `size` from uploaded file.
- [ ] Use `python-magic` to detect `format` from magic bytes.
- [ ] Set `mtime` and `btime` to `datetime.now()` if not provided.
- [ ] Write `django.test` cases:
  - [ ] Validate computed `size`, `format`, and timestamps.

### **Step 3.3: Metadata Override Validation**

- [ ] Accept `mtime`/`btime` overrides via headers or form fields.
- [ ] Return 400 if `format` header conflicts with computed format.
- [ ] Write `django.test` cases:
  - [ ] Test valid `mtime`/`btime` overrides.
  - [ ] Verify 400 error on format mismatch.

---

## **Phase 4: Error Handling & Edge Cases**

### **Step 4.1: Partial Upload Cleanup**

- [ ] Use atomic transactions for database writes.
- [ ] Delete temporary files on validation errors.
- [ ] Write `django.test` cases:
  - [ ] Simulate network failures and validate no partial data persists.

### **Step 4.2: Support Multiple Upload Types**

- [ ] Add `FileUploadParser` for `application/octet-stream`.
- [ ] Add `MultiPartParser` for `multipart/form-data`.
- [ ] Write `django.test` cases:
  - [ ] Test raw binary and form-data uploads.

---

## **Phase 5: Integration & Finalization**

### **Step 5.1: Combine Logging and Upload Logic**

- [ ] Log `"DUPLICATE UPLOAD DETECTED"` on duplicates.
- [ ] Log `"PARTIAL UPLOAD ABORTED"` on cleanup.
- [ ] Include computed metadata in logs.
- [ ] Write `django.test` cases:
  - [ ] Validate log messages align with API behavior.

### **Step 5.2: End-to-End Testing**

- [ ] Test all requirements together:
  - [ ] Idempotency, metadata, error handling, logging.
  - [ ] Validate response codes, headers, and database state.
  - [ ] Ensure logs follow standardized format.

---

## **Post-Completion Tasks**

- [ ] Review test coverage (aim for 95%+).
- [ ] Document API endpoints with Swagger/OpenAPI.
- [ ] Update deployment scripts for new dependencies (e.g., `python-magic`).
