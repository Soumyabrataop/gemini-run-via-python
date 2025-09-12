# Gemini Chat API

Simple way to chat with Google Gemini using your browser cookies.

## Quick Start

### 1. Get Your Cookies

1. Open [gemini.google.com](https://gemini.google.com) in Chrome
2. Sign in and start a chat
3. Press F12 → Network tab → Send a message
4. Find a request to `batchexecute` → Copy cookies from headers
5. Save them in a `.env` file (see below)

### 2. Setup

**Copy and configure `.env` file:**

```bash
cp .env.example .env
```

Then edit `.env` and add your cookies:

```env
GEMINI_COOKIES="your_cookies_here"
HEADLESS=false
```

**Install:**

```bash
pip install -r requirements.txt
playwright install firefox
```

### 3. Run

**With browser UI (recommended):**

```bash
python init.py
```

Visit: http://localhost:8080/docs

**Quick test:**

```bash
python main.py
# Type your message when prompted
```

## API Usage

**Send message:**

```bash
curl -X POST "http://localhost:8080/browser" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello Gemini!"}'
```

**Response:**

```json
{
  "status": "success",
  "data": {
    "response": "Hello! How can I help you today?",
    "media": []
  }
}
```

## Docker

**Build & Run:**

```bash
# Create .env file first (see above)
# Option 1: Direct cookies in .env
# Option 2: Cookie file path in .env
docker build -t gemini-chat .
docker run -p 8080:8080 gemini-chat
```

## Troubleshooting

- **Empty responses?** Check your cookies are fresh
- **"Not signed in"?** Update cookies from browser
- **Docker issues?** Add `DOCKER_CONTAINER=true` to `.env`

That's it! Check `/docs` endpoint for interactive testing.
