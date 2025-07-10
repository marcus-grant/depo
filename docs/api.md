# API and Routes Reference

## Overview

Depo provides both HTML web routes and REST API endpoints for file management.
All API routes are prefixed with `/api/`.

## HTML Web Routes

### Upload

- **GET `/upload/`** - Display upload form (requires authentication)
- **POST `/upload/`** - Process file upload (requires authentication)
  - Accepts: multipart form data, base64 data URIs
  - Returns: HTML page with success/error message

### File Access

- **GET `/{shortcode}/details`** - Display file metadata page
- **GET `/raw/{shortcode}`** - Download raw file content
- **GET `/raw/{shortcode}.{ext}`** - Download with extension validation
  - Returns 404 if extension doesn't match file type

### Authentication

- **GET `/accounts/login/`** - Login page
- **POST `/accounts/login/`** - Process login
- **GET `/accounts/logout/`** - Logout user

## API Endpoints

### Upload API

- **POST `/api/upload/`** - Upload file via API
  - Requires: Authentication token
  - Content-Type: `multipart/form-data`
  - Response headers:
    - `X-Code`: Shortcode for uploaded file
    - `X-Format`: File format (png, jpg, gif)
  - Response body: Filename

### Example API Usage

```bash
# Upload via API with authentication
curl -X POST \
  -H "Authorization: Token YOUR_TOKEN" \
  -F "content=@image.png" \
  http://localhost:8000/api/upload/

# Response headers:
# X-Code: ABC123
# X-Format: png
# Body: ABC123.png
```

## Content Types

### Supported Upload Types

- **File uploads**: PNG, JPG/JPEG, GIF
- **Base64 images**: `data:image/png;base64,...`
- **URLs**: Text starting with http/https or domain patterns
- **Plain text**: Any other text content

### Content Classification

The server automatically classifies content as:

- `image` - Binary image files or base64 images
- `url` - URL-like text content
- `text` - Plain text content

## Error Responses

### HTML Routes

Error pages include user-friendly messages for:

- 400 Bad Request - Invalid upload data
- 404 Not Found - Shortcode doesn't exist
- 500 Server Error - Processing errors

### API Routes

API errors return appropriate HTTP status codes:

- 400 - No file uploaded, invalid format, file too large
- 401 - Authentication required
- 404 - Resource not found
- 500 - Server processing error