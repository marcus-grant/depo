# TODO: Unified Content Upload Form - June 2025

**Quick Goal:** Smart content input form update.

## Section 1 - Frontend Smart single input + drag and drop

### TODOs

- [ ] **Render the basic markup**  
  *Spec/tests*: The DOM contains  
  • a focusable multiline text box with placeholder “Paste text or link…”,  
  • a hidden `<input type="file">` restricted to `.jpg`, `.jpeg`, `.png`,  
  • a visible, focusable drop zone labelled for screen-readers.  
  Unit tests query by role/label and assert presence and required attributes.

- [ ] **Show a drag-over cue**  
  *Spec/tests*: When `dragenter` or `dragover` fires, class `drag-over` is added (dashed-border highlight); it’s removed on `dragleave` or `drop`. DOM test simulates the events and checks class toggling.

- [ ] **Open file picker on click/Enter**  
  *Spec/tests*: Clicking—or pressing **Enter** on—the drop zone programmatically triggers a click on the hidden file input. Spy asserts the hidden input’s `click()` was called.

- [ ] **Handle drag-and-drop events**  
  *Spec/tests*: `dragenter`, `dragover`, `dragleave`, `drop` all call `preventDefault()` / `stopPropagation()`. A dropped `FileList` is forwarded to validation.

- [ ] **Capture clipboard-pasted images**  
  *Spec/tests*: `paste` on the text box inspects `event.clipboardData.files`. If a JPEG/PNG is present, it bypasses text classification, queues the image, and clears the text box. Unit test simulates a paste with a fake PNG blob and asserts (a) queue length increments, (b) text box becomes empty, (c) thumbnail is rendered.

- [ ] **Validate image files**  
  *Spec/tests*: Accept only `image/jpeg` or `image/png` with size ≤ 5 MB. Invalid files raise a toast “Only JPG or PNG under 5 MB”. Test ensures invalid files do **not** enter the queue and toast appears.

- [ ] **Render thumbnail and queue image**  
  *Spec/tests*: On successful validation, a 100 × 100 thumbnail is rendered beneath the zone and the file object is stored for form submission. Test asserts thumbnail node exists and internal queue contains the file.

- [ ] **Classify URL vs text**  
  *Spec/tests*: `classify(str)` returns `'url'` if the string parses as a URL (scheme may be inferred), else `'text'`. Fired on `paste` (when clipboard held only text) and on text-box `blur`; result stored in hidden `detected_type`. Tests:  
  - `"https://foo.bar"` → `'url'`  
  - `"foo.com"` → `'url'`  
  - `"Hello world"` → `'text'`.

- [ ] **Announce immediate feedback**  
  *Spec/tests*: After classification or image capture, an `aria-live="polite"` region announces “Link detected”, “Plain text detected”, or “Image pasted”. Mutation observer in tests verifies correct message appears.

- [ ] **Gate the submit button**  
  *Spec/tests*: Submit remains disabled until **either** a valid image is queued **or** the text box holds non-empty content that has been classified. Tests cover all four states (none, text-only, image-only, both) and assert the button’s `disabled` state.

- [ ] **Gracefully degrade without JS**  
  *Spec/tests*: With JavaScript disabled (or `<html class="js-disabled">`), fallback URL, text, and file inputs are visible and functional. End-to-end no-JS run confirms elements render and form submits.

- [ ] **Add developer documentation**  
  *Spec/tests*: Docs outline public events (`content:classified`, `file:queued`, `file:validationError`), tweakable constants (size limit, accepted types), and notes on extending to the future “chip list”. Lint rule checks a heading “Extensibility Notes” is present.

## Section 2 — Backend Updates  

**Goal:** Accept base-64 clipboard images while preserving existing URL/text/image logic.

- [ ] **Detect base-64 payloads in the main view**  
  *Spec/tests*: A POST body whose `raw_input` field starts with `data:image/(png|jpeg);base64,` sets `request.is_base64_image` to `True`; all other posts leave it `False`.  
  • Unit test 1: POST a minimal 1 × 1 PNG data-URI → flag is `True`.  
  • Unit test 2: POST `"https://example.com"` → flag is `False`.  

- [ ] **Convert base-64 to `InMemoryUploadedFile`**  
  *Spec/tests*: When `request.is_base64_image` is `True`, helper strips the prefix, decodes, wraps bytes in `InMemoryUploadedFile` named `clipboard.png`/`.jpg`, and injects it into `request.FILES["image"]`.  
  • Unit test: feed a known base-64 PNG string → returned object is `InMemoryUploadedFile`, `content_type == "image/png"`, `size == decoded_length`.  

- [ ] **Reuse existing size/type validation**  
  *Spec/tests*: The newly injected file flows through the current validation that enforces `image/jpeg|png` and ≤ 5 MB.  
  • Test: oversize base-64 image yields HTTP 400 with message “Only JPG or PNG under 5 MB”; no DB write occurs.  

- [ ] **Classify content type server-side**  
  *Spec/tests*: The classification function returns  
  • `'image'` if `request.is_base64_image` is `True` **or** `request.FILES` contains an image;  
  • `'url'` if `looks_like_url(raw_input)` is `True`;  
  • `'text'` otherwise.  
  Unit tests cover all three branches.  

- [ ] **Persist clipboard images to the Image model**  
  *Spec/tests*: Saving a decoded clipboard image creates an `Image` instance; reading `image.file` returns the original byte length. ORM test asserts equality.  

- [ ] **Log and rate-limit base-64 uploads**  
  *Spec/tests*:  
  • Successful decode logs one INFO entry: `{"event":"clipboard_image_saved","bytes":<len>}`.  
  • Malformed base-64 logs WARNING `{"event":"clipboard_image_error","reason":"DecodeError"}` and returns HTTP 400.  
  Logging test captures records and asserts count/level/JSON keys.  

- [ ] **Security hardening checks**  
  *Spec/tests*:  
  • Strings longer than 8 MB are rejected before decode with HTTP 400 “Image too large”.  
  • `Pillow` verifies that claimed MIME matches actual header bytes; mismatch raises `ValidationError`.  
  Regression test submits a PNG encoded but labelled `image/jpeg` → receives 400 “Invalid image data”.  

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
  *Spec/tests*: Docs contain a section “Handling base-64 images” that lists: detection regex, size limit, Pillow verification, and `ALLOW_BASE64_IMAGES` flag. Doc-lint rule checks the section heading exists and that the regex appears verbatim.
