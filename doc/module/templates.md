# Templates

Jinja2 templates served via FastAPI.
Rendered by `web.templates.get_templates()`.

## Structure

```txt
templates/
├── base.html                # Full page layout wrapper, defines scripts block
├── theme.html               # Living style reference (extends base.html)
├── upload/
│   ├── page.html            # Upload form (extends base.html)
│   ├── formats.html         # Format select optgroups (included by page)
│   └── script.html          # File upload JS (included via scripts block)
├── info/
│   ├── page.html            # Shared info page shell (extends base.html)
│   ├── link.html            # LinkItem view (extends page.html)
│   ├── text.html            # TextItem view (extends page.html)
│   └── pic.html             # PicItem view (extends page.html)
├── partials/
│   ├── nav.html             # Titlebar navigation
│   ├── foot.html            # Site footer
│   └── success.html         # Upload success (HTMX fragment)
└── errors/
    ├── _content.html        # Shared error body (include, not rendered)
    ├── page.html            # Full-page error (extends base.html)
    └── partial.html         # Error pip (HTMX fragment)
```

## Inheritance hierarchy

```txt
base.html
├── upload/
│   ├── page.html
│   ├── formats.html
│   └── script.html
├── auth/
│   └── login.html           # Login form (extends base.html)
├── theme.html
├── info/page.html
│   ├── info/link.html
│   ├── info/text.html
│   └── info/pic.html
└── errors/
    ├── _content.html        # Shared error body (include, not rendered)
    ├── page.html            # Full-page error (extends base.html)
    └── partial.html         # Error pip (HTMX fragment)
```

`errors/partial.html` is a standalone fragment, not extending base.html.

`errors/_content.html` is an include, not a rendered template. Both
`errors/page.html` and `errors/partial.html` include it for the error body.

`base.html` provides the page shell:
`nav` partial, content block, footer partial.

`info/page.html` provides the info shell:
window container, shortcode heading, action row,
payload block, divider, metadata block.
Child templates fill:
`{% block payload %}`, `{% block metadata %}`, and `{% block payload_class %}`.

Same pattern repeated for the upload page.
The `templates/upload` directory contains everything for that page.
Then the `page.html` defines the main template for that page.
It includes partials included to split up the markup and scripts.

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

- Copy content button (per-type block):
  - text/pic: data-copy-url with extensioned raw URL, fetch-based clipboard
  - link: data-copy with origin URL, direct clipboard
- Copy link button (per-type block):
  - text/pic: data-copy with extensioned absolute URL
  - link: data-copy with /{code}/raw absolute URL
- Copy shortcode button (outline, data-copy with code)
- View Raw link (href to /{code}/raw)
- Facts anchor (href="#metadata")

Clipboard handling is a script block at the end of info/page.html.
Delegates via click listener on data-copy (direct writeText) and
data-copy-url (fetch, sniff Content-Type, writeText or ClipboardItem).

## Error pages

`errors/_content.html` carries the shared body:
the error message as a heading, and, for 401, a prompt linking to `/login`.
Both surfaces include it.

The wrappers differ deliberately, because their semantics differ.
`errors/page.html` wraps the content in `section.window.window--error`,
a landmark region on a freshly loaded page.
`errors/partial.html` wraps it in `div.error.error--{role}` with
a matching `role` attribute, an ARIA live region,
because htmx swaps it in dynamically and a screen reader must announce it.

The 5xx debug disclosure stays page-only.
A collapsed details element is useful on a full error page someone stops to read;
it is noise inside a transient alert.

404: Renders shortcode in a `code.shortcode` element with
a message that the code does not exist or was deleted.

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
