# Depo

## TODO

- [ ] Add first short-code model, an `item`.
- [ ] Need to decide how to organize between short-code and
      subsidiary paths like the image explorer or gist viewer and web vs. API.

## Project Structure

- `api/`
  - API views and URLs
- `web/`
  - All html & htmx rendered views and URLs.
- `common/`
  - All shared logic between django apps.

## Proposed Future Layout

- `item`
  - The main short-code producing views and URLs.
    - Will handle views for both HTML responses and JSON responses.
- `pic`
  - Views and URLs that handle saving, retrieving and exposing metadata of
      pictures that are indexed as an `item`.
