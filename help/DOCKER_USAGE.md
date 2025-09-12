# Docker Guide

Run Gemini API in a container.

## Setup

**1. Copy and configure `.env` file:**

```bash
cp .env.example .env
```

Then edit `.env` and add your cookies:

```env
GEMINI_COOKIES="your_cookies_here"
DOCKER_CONTAINER=true
```

**2. Build:**

```bash
docker build -t gemini-chat .
```

**3. Run with mounted .env:**

```bash
docker run -p 8080:8080 -v "$(pwd)/.env:/app/.env" gemini-chat
```

## Usage

Visit: http://localhost:8080/docs

**Send message:**

```bash
curl -X POST "http://localhost:8080/browser" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello Docker!"}'
```

## Updating Environment (Cookies, etc.)

**Update cookies without rebuilding:**

1. Edit your local `.env` file
2. Restart container:

```bash
docker restart $(docker ps -q --filter ancestor=gemini-chat)
```

That's it! No rebuild needed.

## Options

**Custom port:**

```bash
docker run -p 3000:8080 -v "$(pwd)/.env:/app/.env" gemini-chat
```

**Background:**

```bash
docker run -d -p 8080:8080 -v "$(pwd)/.env:/app/.env" gemini-chat
```

## Troubleshooting

- **"Not signed in"?** Update cookies in local `.env` and restart container
- **Port issues?** Use `-p 3000:8080` for different port
- **Container stops?** Check cookies are valid

That's it! Simple Docker deployment.
