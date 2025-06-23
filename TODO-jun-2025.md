# TODO: Unified Content Upload Form - June 2025

Should be handled by current clde.md file

## H2: Core Form Changes

**Quick Goal:** Single textarea that handles URLs, text, and pasted images.

### TODOs

- [ ] Replace URL input with textarea in `shortcode-form.html`
- [ ] Add JavaScript paste listener for clipboard images
- [ ] Update `web_index` view to handle base64 image data
- [ ] Extend content detection in backend

### Simple Form Update

```html
<textarea 
    id="content" 
    name="content" 
    placeholder="Paste URL, text, or image here..."
    rows="3">
</textarea>
```

## H2: Clipboard Image Support

**Goal:** Handle Ctrl+V pasted images (screenshots, copied images).

### TODOs

- [ ] Add paste event listener to convert images to base64
- [ ] Update form submission to include base64 data
- [ ] Add base64 detection to existing `process_file_upload()`

### Minimal JavaScript

```javascript
document.getElementById('content').addEventListener('paste', (e) => {
    const items = e.clipboardData.items;
    for (const item of items) {
        if (item.type.startsWith('image/')) {
            const file = item.getAsFile();
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('content').value = e.target.result;
            };
            reader.readAsDataURL(file);
            e.preventDefault();
        }
    }
});
```

## Backend Updates

**Goal:** Handle base64 images in existing flow.

### TODOs

- [ ] Add base64 detection to `web_index` view
- [ ] Convert base64 to bytes in `process_file_upload()`
- [ ] Update content type detection

### Quick Backend Addition

```python
def decode_base64_image(base64_string):
    """Convert base64 image to bytes for existing upload flow"""
    if base64_string.startswith('data:image/'):
        header, data = base64_string.split(',', 1)
        return base64.b64decode(data)
    return None

# In web_index view:
content = req.POST.get("content")
if content and content.startswith('data:image/'):
    # Handle as base64 image
    file_data = decode_base64_image(content)
    result = process_file_upload(file_data)
    # ... rest of upload logic
```

## H2: Testing

**Simple validation:**

- [ ] Test URL paste still works
- [ ] Test screenshot paste (Ctrl+Shift+S, Ctrl+V)
- [ ] Test copied image paste
- [ ] Verify shortcode generation works for all types

## H2: Edge Cases

**Handle gracefully:**

- [ ] Large base64 images (add size check)
- [ ] Invalid base64 data
- [ ] Mixed content in textarea
- [ ] Empty paste events

**Total estimated time: 2-3 hours**
