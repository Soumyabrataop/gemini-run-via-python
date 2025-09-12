import asyncio
import os
from dotenv import load_dotenv
from playwright.async_api import async_playwright

# Load environment variables from .env
load_dotenv()

async def run():
    firefox_path = os.getenv("FIREFOX_BIN")
    
    if not firefox_path:
        print("❌ FIREFOX_BIN not set in environment.")
        return

    print(f"✅ Using Firefox binary at: {firefox_path}")

    async with async_playwright() as p:
        browser = await p.firefox.launch(
            executable_path=firefox_path,
            headless=False  # Set to True if you want headless mode
        )
        page = await browser.new_page()
        await page.goto("https://www.google.com")
        print("🌐 Opened Google. Waiting 10 seconds...")
        await asyncio.sleep(10)
        await browser.close()
        print("✅ Done.")

asyncio.run(run())
