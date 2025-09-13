# 🤖 Gemini Chat API

**Turn Google Gemini into your personal API!** This tool lets you chat with Google's Gemini AI through a simple web interface or programming code, without needing Google's official API keys.

## 🌟 What Does This Do?

- **Chat with Gemini AI** through a user-friendly web interface
- **Get AI responses** that you can use in your own projects
- **No API keys needed** - just use your Google account
- **Works with images** - Gemini can analyze and describe pictures
- **Free to use** - no subscription required

## 🚀 Getting Started (Easy Way)

### Step 1: Get Your "Login Cookie" 

Think of this like getting a temporary pass to use Gemini on your behalf:

1. **Open Google Chrome** and go to [gemini.google.com](https://gemini.google.com)
2. **Sign in** with your Google account
3. **Send any message** to Gemini (like "Hello!")
4. **Right-click anywhere** on the page and select "Inspect" (or press F12)
5. **Click the "Network" tab** at the top
6. **Send another message** to Gemini
7. **Look for a line** that says something like "batchexecute" and click on it
8. **Find "Cookie:"** in the details and copy everything after it
9. **Save this text** - you'll need it in the next step

*Don't worry if this seems complicated - you only need to do it once!*

### Step 2: Set Up Your Environment

1. **Download this project** to your computer
2. **Find the file** called `.env.example` 
3. **Make a copy** and rename it to `.env`
4. **Open the `.env` file** in any text editor (like Notepad)
5. **Replace** `your_cookies_here` with the cookie text you copied earlier:

```
GEMINI_COOKIES="paste_your_cookie_here"
HEADLESS=false
```

### Step 3: Install Required Software

**On Windows:**
1. Install Python from [python.org](https://python.org) (choose "Add to PATH" during installation)
2. Open Command Prompt and type these commands one by one:

```
pip install -r requirements.txt
playwright install firefox
```

**On Mac:**
1. Install Python from [python.org](https://python.org)
2. Open Terminal and type the same commands above

### Step 4: Start Chatting!

1. **Open your terminal/command prompt** in the project folder
2. **Type:** `python init.py`
3. **Open your web browser** and go to: `http://localhost:8080/docs`
4. **Start chatting** with Gemini through the web interface!

## 💬 How to Use

### Web Interface (Easiest)
Once you've started the program, visit `http://localhost:8080/docs` in your browser. You'll see a simple form where you can:
- Type your message to Gemini
- Click "Send" 
- Get Gemini's response instantly

### For Programmers
If you know how to code, you can send messages programmatically:

```bash
curl -X POST "http://localhost:8080/browser" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello Gemini!"}'
```

## 🐳 Advanced: Using Docker

If you're familiar with Docker, you can run this in a container:

1. **Create your `.env` file** (see Step 2 above)
2. **Build:** `docker build -t gemini-chat .`
3. **Run:** `docker run -p 8080:8080 gemini-chat`

## ❓ Common Problems & Solutions

**"Empty responses" or "Not signed in"**
- Your cookie has expired (they last about 1-2 weeks)
- Go back to Step 1 and get a fresh cookie from your browser

**"Command not found" errors**
- Make sure Python is installed and added to your system PATH
- Try `python3` instead of `python` on Mac/Linux

**"Port already in use"**
- Another program is using port 8080
- Close other programs or change the port in the code

**Still having trouble?**
- Make sure you're signed into Gemini in your browser
- Try using a fresh browser session
- Check that your internet connection is working

## 🎯 What Can You Do With This?

- **Personal AI assistant** for daily questions
- **Content creation** help (writing, ideas, etc.)
- **Image analysis** (describe photos, extract text)
- **Learning tool** (ask questions about any topic)
- **Integrate AI** into your own projects and websites

---

**Need help?** Open an issue on GitHub and we'll help you get started! 🚀
