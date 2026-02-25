# Styles

CSS class and token reference for the depo visual system.
Implements rules from [design language](./language.md).
Built on Pico CSS v2.1.1 with overrides in `static/css/depo.css`.

## Token summary

Typography: `--depo-font-mono`, `--depo-size-{heading,body,meta}`,
`--depo-weight-{body,heading,meta}`.

Dither patterns: `--depo-dither-{diag,check,cross,hstripe}`.
Fully opaque SVG data URIs, ground `rgb(230,230,230)`, fill `rgb(200,200,200)`.

Structure: `--depo-titlebar-height`, `--depo-bg`, `--depo-border`.

## Class reference

Dither fills: `.dither-diag`, `.dither-check`, `.dither-cross`.
Borders: `.tui-border` (2px), `.tui-border-heavy` (4px).
Metadata: `.meta` (small, mono, muted).
Form grouping: `.window-controls` (flex row).

## Shadows

`.shadow-sm` (11px offset), `.shadow-md` (19px offset).
Checkerboard `::after` pseudo-element, bordered, `z-index: -1`.
Stacking context lives on `main`, not the shadow parent.
`background-position: top left` for bottom-edge tile alignment.

Offsets are manually tuned — border width shifts background origin
so clean tile multiples don't land. Deeper fix deferred to v0.2.

## Titlebar

`.titlebar` — flex container with horizontal stripe dither.
`.titlebar-label` — child `<a>`, stretches to fill bar height,
solid background punchout matching stripe ground color.

Uses `overflow: hidden` to clip. Height via `--depo-titlebar-height`.

## Window

`.window` — bordered container, solid `--depo-bg` background.
Sits on gray `main` surface. Combine with shadow classes for depth.

## Pico override notes

Pico v2 scopes colors under `:root:not([data-theme=dark])`, not `:root`.
`base.html` requires `data-theme="light"` on `<html>`.
Source order wins when specificity matches.

`--pico-primary-background` controls buttons, `--pico-primary` controls links.
Both plus border/hover/focus variants needed for full control.

`--pico-font-weight` overrides body weight globally.
Form element fonts set directly — no Pico property for these.

`footer.site-footer` compound selector required to beat Pico's bare `footer`.

## Known issues

High-DPI: 1px SVG bits invisible, `background-size` scaling mandatory.
Zoom: fractional levels cause sub-pixel artifacts. Clean at 100% and 2x/3x.
Large-surface dither looked busy — flat grays used instead, dither deferred to v0.2.
