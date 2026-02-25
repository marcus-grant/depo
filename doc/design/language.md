# depo — Design Language

Purpose: define what must remain true as depo evolves,
while clearly marking what is intentionally unresolved and
must be learned through use.

## Core description

**Depo** is a simple ingest service:
content goes in, a short reference comes out.

The reference is the primary object users interact with.
Everything else
(aliases, tags, versions, metadata, discovery) is a lens on that reference.

The default workflow is intentionally trivial:
record content -> receive reference -> use reference anywhere.

**Key constant:** everything in depo is built around a simple reference.
This should be true in UX, language, visuals, and system behavior.

## 2. Guardrails

These are design constraints, not feature limitations.

Depo is not a file manager, not a folder hierarchy, not a social platform,
not an opinionated workflow tool, not an organizer by default.

Complexity exists, but it is optional, discoverable,
and never blocks the core workflow.

## Design philosophy

### Progressive complexity (UNIX-inspired)

Start with the simplest possible action.
Reveal complexity only when necessary.
Never force users to understand system internals.
Avoid creeping complexity at all costs.
The system may be powerful; the interface must remain calm.

### Old computing constraints as modern restraints

Early systems were constrained by
limited color, low resolution, and minimal affordances.
Those constraints enforced clarity and discipline.

Depo deliberately reuses these constraints as design discipline,
not aesthetic cosplay.
Sources of inspiration include early Macintosh bitmap patterns,
Susan Kare-era fills, and terminal TUI conventions
(box-drawing characters, cell-based alignment, block focus indicators).

## Language principles

### Reference-first language

Prefer showing references over naming "things."
Names, labels, aliases are conveniences, not identities.
Avoid metaphors that imply mutability of content.

### Provisional vocabulary (explicitly unresolved)

Core noun (Item / Thing / Deposit / none) is intentionally unsettled.
Some verbs exist in tension: record vs add, resolve vs view.

#### Design rule

UI language may simplify system truth, but must never contradict it.
This tension is expected to resolve through usage.

## Visual system — structural rules (LOCKED)

### Gray-scale-first structure (non-negotiable)

Layout, hierarchy, grouping, and affordances must work in pure grayscale.
Color must never be required to understand structure.
If removing color breaks the UI, the design is wrong.

Gray-scale handles: spacing, grouping, separation, emphasis via weight (not color).

### Structural tools (before color)

Use these instead of color wherever possible:

#### Spacing

Primary hierarchy via vertical rhythm,
generous white-space between groups.

#### Typography

Mono-space for references and system identifiers,
sans/neutral face for prose and labels.

#### Weight

Bold for primary elements, regular/light for metadata.

#### Sizing

Fewer size steps, clearly separated, avoid micro-hierarchies.

#### Dither patterns

1-bit bitmap fills (diagonal lines, checkerboards, crosshatch)
as a grayscale hierarchy primitive.
Implemented as small repeating SVG or CSS background patterns.
Used for separators, section fills, secondary surfaces.

#### TUI elements

Box-drawing characters for borders,
cell-based alignment, visible hard borders instead of shadows and gradients,
block-style focus indicators.

#### Shadows

Expressed as hard-edged dither pattern offsets for element hierarchy,
not CSS blur shadows. No gradients.

Color is a last resort, not a layout tool.

## Color philosophy (LOCKED)

### Color is semantic, not decorative

Every color must answer a specific question.
No "accent color" without meaning. No branding via color.
No expressive surfaces or gradients.

### Warm vs cool rule (core invariant)

Cool hues -> system state, stability, focus.
Warm hues -> attention, interruption.
Red -> failure only.

This rule holds regardless of palette choice.

### Light / dark mode parity

Light/dark mode changes polarity, not meaning.
Hue identity must remain consistent. Only luminance and contrast may change.

## Semantic color roles

These roles are stable even if hues change.

| Role | Meaning |
|------|---------|
| Structure | Grayscale |
| Success / Recorded | Stable reference exists |
| Attention | Salience; pause and notice |
| Error / Invalid | Failure states only |
| Secondary info | Quiet, optional emphasis |
| Focus | What you are currently working with (may be structural) |

## Candidate Palettes

Palette A is how we're starting as it's more traditional and
easier to work with to create a coherent design.
Its color signals are well understood so it's a good base to start with.

Palette B, or a shifted hue wheel of Palette B,
is more ideal because its colors make it clear this isn't just an 'app'.
A task, to play with it as a separate theme with real usage is forthcoming.

Final decision deferred to lived experience.

### Palette A — Classic Retro (orthodox, conservative)

Background (light):     RGB(245, 245, 245)
Background (dark):      RGB(24, 24, 24)

Text (primary):         RGB(32, 32, 32)
Text (secondary):       RGB(110, 110, 110)

Focus / Primary:        RGB(70, 110, 160)     muted blue
Success / Recorded:     RGB(90, 145, 95)      restrained green
Attention (info):       RGB(200, 185, 90)     yellow
Attention (pause):      RGB(200, 140, 60)     amber
Error / Invalid:        RGB(165, 60, 55)      deep red

Strengths: extremely familiar, lowest cognitive load, lowest risk.
Green-for-success is deeply ingrained. Users won't notice the palette — it just works.

Weaknesses: safe to the point of generic. Less distinctive personality.

```txt
Background (light):     RGB(242, 242, 240)
Background (dark):      RGB(26, 28, 30)

Text (primary):         RGB(36, 38, 40)
Text (secondary):       RGB(120, 125, 130)

Focus / Primary:        RGB(120, 130, 160)    muted blue-violet
Success / Recorded:     RGB(85, 145, 135)     desaturated teal
Attention (info):       RGB(195, 185, 105)    soft yellow
Attention (pause):      RGB(205, 135, 70)     amber/orange
Error / Invalid:        RGB(160, 70, 65)      oxide red
```

### Palette B — Rotated Legacy (starting choice)

```txt
Background (light):     RGB(242, 242, 240)
Background (dark):      RGB(26, 28, 30)

Text (primary):         RGB(36, 38, 40)
Text (secondary):       RGB(120, 125, 130)

Focus / Primary:        RGB(120, 130, 160)    muted blue-violet
Success / Recorded:     RGB(85, 145, 135)     desaturated teal
Attention (info):       RGB(195, 185, 105)    soft yellow
Attention (pause):      RGB(205, 135, 70)     amber/orange
Error / Invalid:        RGB(160, 70, 65)      oxide red
```

Strengths: more appliance-like, less "web app." Teal success feels calmer
and less brand-forward than green. Slightly warmer background grays give
subtle character without drawing attention. Mac + PlayStation lineage —
familiar but rotated enough to feel distinct.

Weaknesses: teal-for-success is less conventional — some users may not
immediately read it as positive. Needs fatigue testing to confirm the
shifted hues remain comfortable over extended use.

## Color usage rules

Color is foreground-only by default.
Large surfaces remain grayscale.
Any color must tolerate accidental overuse.
If a color draws attention to itself, it is too strong.
Red is rare and sacred.

## 10. Explicit tensions (INTENTIONAL)

These are not mistakes — they are acknowledged uncertainties.

### Attention vs Secondary

Mutability is architecturally important but usually safe.
Over-signaling mutability risks alarming users.
Under-signaling risks confusion later.
Boundary intentionally unresolved, to be refined through real usage.

### Success hue

### Green vs teal

Teal selected for v1 (Palette B). Offers a rotated legacy
that feels calmer and less brand-like. May revisit after fatigue testing.

### Focus color

May be expressed structurally (underline, border).
Focus color may exist but is not required for v1. Deferred.

### Yellow vs amber ladder

Yellow for informational attention, amber for decision-worthy attention.
May collapse to a single hue initially.

## CSS foundation

### Framework

Pico CSS (classless/semantic).
Earns its place by providing solid defaults with no build step.
Custom properties overridden with Palette B values.

### Evaluation

If Pico's defaults are fought more than used, Tailwind earns its seat.
Tailwind would add a build step — only justified when UI complexity demands it.
Currently mapped to Pico CSS custom properties in static/css/depo.css.

### HTMX

Bundled locally, no CDN.
Loaded by defer keyword to ensure quick first paint.

Everything served comes from the deployed host.

## Template conventions

All templates have boundary markers for debugging and testing:

```html
<!-- BEGIN: template-name.html -->
<!-- END: template-name.html -->
```

Full pages extend `base.html`.
Partials/fragments are standalone (no layout wrapper).
Those partials are stored in depo/templates/partials/ to clarify their role.
HTMX requests receive fragments;
full page loads receive wrapped templates.

Shortcodes displayed with `<code class="shortcode">`;
functional class, tested against.

## How to evolve this document

Design decisions are categorized as:

- **Locked** — must not change casually
- **Experimental** — intentionally unresolved
- **Deferred** — not required for v1

Experience, not theory, resolves tension.

## Self-check

If depo ever feels expressive, clever, brand-forward, or visually loud;
something has gone wrong.

If it feels calm, boring (in a good way),
and trustworthy after hours of use, it's working.
