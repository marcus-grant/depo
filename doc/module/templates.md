# Templates

Jinja2 templates served via FastAPI.
Rendered by `web.templates.get_templates()`.

## Structure

```txt
templates/
├── base.html                # Full page layout wrapper
├── upload.html              # Upload form (extends base.html)
├── theme.html               # Living style reference (extends base.html)
├── info/
│   ├── page.html            # Shared info page shell (extends base.html)
│   ├── link.html            # LinkItem view (extends page.html)
│   ├── text.html            # TextItem view (extends page.html)
│   └── pic.html             # PicItem view (extends page.html)
├── partials/
│   ├── nav.html             # Titlebar navigation
│   ├── foot.html            # Site footer
│   ├── success.html         # Upload success (HTMX fragment)
│   └── error.html           # Validation error (HTMX fragment)
└── errors/
    ├── 404.html             # Not found (extends base.html)
    └── 500.html             # Internal error (extends base.html)
```

## Inheritance hierarchy

```txt
base.html
├── upload.html
├── theme.html
├── info/page.html
│   ├── info/link.html
│   ├── info/text.html
│   └── info/pic.html
└── errors/
    ├── 404.html
    └── 500.html
```

`base.html` provides the page shell:
`nav` partial, content block, footer partial.

`info/page.html` provides the info shell:
window container, shortcode heading, action row,
payload block, divider, metadata block.
Child templates fill:
`{% block payload %}`, `{% block metadata %}`, and `{% block payload_class %}`.

## Info page system

`info/page.html` defines the reading order inside an `article.window.shadow-md`:

1. Shortcode heading (h2.shortcode)
2. Action row (div.action-row, role="toolbar")
3. Payload (div#payload, class from payload_class block)
4. Divider (hr.divider)
5. Metadata (dl#metadata.meta)

Blocks provided to child templates:

- `payload` -- type-specific content (link anchor, pre>code, img)
- `metadata` -- type-specific dt/dd pairs inside the dl wrapper
- `payload_class` -- modifier class (payload--link, payload--text, payload--pic)

Action row contains:

- Copy content button (disabled, deferred)
- Copy URL button (secondary, data-copy with absolute URL)
- Copy shortcode button (outline, data-copy with code)
- Facts anchor (href="#metadata")

Clipboard handling is a script block at the end of info/page.html.
Delegates via click listener on any element with data-copy attribute.

## Error pages

Both error templates use `section.window.window--error` as their container.
No action row, no metadata, no payload block.

404: Renders the shortcode in a code.shortcode element with a message
that the code does not exist or was deleted.

500: Renders a message heading, a paragraph with issues link, and a
details element (default closed) containing debug info as a dl with
path, method, and detail.

## Conventions

Template markers use boundary comments for debugging and testing:

```html:jinja2
    <!-- BEGIN: info/page.html -->
    <!-- END: info/page.html -->
```

Child templates note their parent:

```html:jinja2
    <!-- BEGIN: info/link.html -->
    <!-- EXTENDS: base.html -->
```

Block content in child templates uses fragment markers:

```html:jinja2
    <!-- BEGIN: info/link.html#payload -->
    <!-- END: info/link.html#payload -->
```

Shortcode display uses `code.shortcode` as a project-wide convention.
The shortcode class is functional (tested against), not purely visual.

Partials (`nav`, `footer`, `success`, `error`)
are standalone fragments with no extends.
Returned directly for HTMX requests.

## Testing

`render_template(name, ctx)` in `tests/factories`
renders a named template with a context dict and returns parsed BeautifulSoup.
Used by `test_info_templates.py` & `test_error_templates.py`.

Info template tests pass a stub request object with `base_url` for
the absolute URL in the copy URL button.
The stub is set up in the module-level `_info_page_soup` helper.

Route tests (`test_shortcode.py`) cover template selection only:
status code, content-type, template marker presence, & shortcode in response.
Template markup assertions are owned by the template test modules.
