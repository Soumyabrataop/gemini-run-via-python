# API Guide

Simple HTTP endpoints to chat with Gemini.

## Start Server

```bash
python init.py
```

Visit: http://localhost:8080/docs for interactive testing.

## Endpoints

### Browser Chat (Recommended)

**POST** `/browser`

```json
{
  "prompt": "Your message here"
}
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "response": "Gemini's reply",
    "media": []
  }
}
```

### Direct API

**POST** `/api`

```json
{
  "prompt": "Your message",
  "at_token": "your_at_token"
}
```

## Cookie Setup

Copy and configure `.env` file:

```bash
cp .env.example .env
```

Then edit `.env` and add your cookies:

```env
GEMINI_COOKIES="your_cookies_from_browser"
```

Get cookies:

1. Open gemini.google.com
2. F12 → Network → Send message
3. Copy cookies from batchexecute request

## Examples

**Simple chat:**

```bash
curl -X POST "http://localhost:8080/browser" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello!"}'
```

**With image:**

```bash
curl -X POST "http://localhost:8080/browser" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Describe this", "image_url": "https://example.com/image.jpg"}'
```

That's it! Use `/docs` for interactive testing.
