import asyncio, sys, os, time, json, logging, argparse, threading, http.server, socketserver, socket, concurrent.futures, platform
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from cookie_helpers import parse_cookies, is_running_in_docker
import threading
import functools
import platform
import asyncio as _asyncio

# Fix for Windows Playwright subprocess issues
if platform.system() == 'Windows':
    try:
        # Use Proactor event loop policy for Windows to support subprocesses with Playwright
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        # Fallback for older Python versions
        pass

load_dotenv()
logger = logging.getLogger("gemini-headless")

# ------------------- Helpers -------------------
def get_firefox_path():
    env = os.environ.get("FIREFOX_BIN")
    if env and Path(env).exists(): return env
    for path in ["/usr/bin/firefox", "/usr/local/bin/firefox", "/opt/firefox/firefox"]:
        if Path(path).exists(): return path
    raise FileNotFoundError("Firefox not found. Set FIREFOX_BIN env var.")

def start_http_server(port=8080) -> Tuple[socketserver.TCPServer, int]:
    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/headless":
                params = parse_qs(parsed.query)
                prompt = params.get("prompt", [""])[0]
                # run_headless is async; run it safely on Windows
                try:
                    # Check if we're on Windows and set event loop policy if needed
                    if platform.system() == 'Windows':
                        try:
                            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                        except AttributeError:
                            pass
                    
                    try:
                        result = asyncio.run(run_headless({"prompt": prompt, "no_headless": False}))
                    except RuntimeError as e:
                        if "cannot be called from a running event loop" in str(e):
                            # If an event loop is already running, create a new one in a thread
                            import threading
                            result_container = {}
                            def run_in_thread():
                                if platform.system() == 'Windows':
                                    try:
                                        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                                    except AttributeError:
                                        pass
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                try:
                                    result_container['result'] = loop.run_until_complete(run_headless({"prompt": prompt, "no_headless": False}))
                                finally:
                                    loop.close()
                            
                            t = threading.Thread(target=run_in_thread)
                            t.start()
                            t.join()
                            result = result_container.get('result', {"status": "error", "errors": ["Failed to run in thread"]})
                        else:
                            raise
                except Exception as e:
                    result = {"status": "error", "errors": [str(e)]}
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
            elif parsed.path == "/stream_log":
                log_content = Path("stream_full.log").read_text(encoding="utf-8") if Path("stream_full.log").exists() else ""
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.end_headers()
                self.wfile.write(json.dumps({"log": log_content}).encode())
            else: super().do_GET()
    for test_port in range(port, port+10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: s.bind(("", test_port)); port=test_port; break
        except OSError: continue
    httpd = socketserver.TCPServer(("", port), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port

# ------------------- Core -------------------
async def run_headless(args: Dict[str, Any]) -> Dict[str, Any]:
    firefox = get_firefox_path()
    prompt = args.get("prompt","")
    
    # Read no_headless from args (from API) or environment variable (direct call)
    # no_headless means "show the browser window" (opposite of headless)
    if "no_headless" in args:
        # Value explicitly passed from API (init.py already read HEADLESS env var)
        no_headless = args.get("no_headless", False)
        logger.info(f"Using no_headless={no_headless} from API call")
    else:
        # Direct call - read from HEADLESS environment variable
        # HEADLESS=false means show browser (no_headless=True)
        headless_env = os.getenv('HEADLESS', 'true').lower()
        no_headless = headless_env == 'false'
        logger.info(f"Direct call: Read HEADLESS={headless_env} from environment, no_headless={no_headless}")
    
    # Force headless mode in Docker containers (GUI not available)
    if is_running_in_docker():
        if no_headless:
            logger.warning("Docker container detected - overriding HEADLESS=false to force headless mode")
        no_headless = False
        logger.info("Running in Docker container - forcing headless mode")
    
    cookies = parse_cookies(args.get("cookies"), args.get("cookies_file"))
    if is_running_in_docker() and not cookies:
        return {"status":"error","errors":["Docker requires cookies"]}
    async def _playwright_flow():
        async with async_playwright() as p:
            browser = await p.firefox.launch(executable_path=firefox, headless=not no_headless)
            context = await browser.new_context()
            if cookies: await context.add_cookies(cookies)
            page = await context.new_page()
            await page.goto("https://gemini.google.com/app")
            
            # Check if user is signed in by looking for sign-in elements
            try:
                # Look for sign-in link with Google ServiceLogin URL - if visible, user is not signed in
                sign_in_visible = await page.locator("a[href*='accounts.google.com/ServiceLogin']").is_visible(timeout=5000)
                if sign_in_visible:
                    await context.close()
                    return {"status":"error","errors":["Not signed in"]}
            except:
                # If we can't find sign-in elements, assume user is signed in and continue
                logger.info("Could not detect sign-in status, proceeding...")
                
            # Updated selector for the input box based on current Gemini interface
            box = page.locator("div.ql-editor.textarea.new-input-ui[contenteditable='true']")
            await box.fill(prompt); await page.keyboard.press("Enter")
            
            # Wait longer for response generation and look for image buttons to appear
            logger.info("Waiting for Gemini response...")
            await asyncio.sleep(10)  # Increased wait time
            
            # Wait for image buttons to appear (indicating response is ready)
            try:
                await page.wait_for_selector("button.image-button", timeout=120000)  # 2 minute timeout
                logger.info("Image buttons detected - response ready")
            except:
                logger.warning("No image buttons found within timeout, proceeding anyway")
                # Wait a bit more for text response
                await asyncio.sleep(5)
            
            # Get text response using more comprehensive selectors
            resp_elems = await page.locator('[data-message-author-role="model"], message-content p, .model-response-text, .response-container p').all()
            text = " ".join([await e.text_content() or "" for e in resp_elems]).strip()
            logger.info(f"Extracted text response: {text[:100]}..." if text else "No text response found")
            
            # Get images using the updated selector
            imgs, media = await page.locator("button.image-button img").all(), []
            logger.info(f"Found {len(imgs)} images to download")
            
            for i, img in enumerate(imgs[:5], 1):
                src = await img.get_attribute("src")
                if not src: 
                    logger.warning(f"Image {i}: No src attribute found")
                    continue
                    
                filename = f"gemini_image_{int(time.time())}_{i}.jpg"
                logger.info(f"Downloading image {i}: {filename}")
                
                data = await page.request.get(src)
                if data.ok:
                    Path("output").mkdir(exist_ok=True)
                    Path("output",filename).write_bytes(await data.body())
                    media.append(filename)
                    logger.info(f"Successfully saved image: {filename}")
                    logger.info(f"Image accessible at: http://localhost:8080/output/{filename}")
                else:
                    logger.error(f"Failed to download image {i}: HTTP {data.status}")
                    
            await context.close()
            Path("stream_full.log").write_text(text, encoding="utf-8")
            
            result = {"status":"success","data":{"response":text,"media":media}}
            logger.info(f"Final result: {len(media)} images, text length: {len(text)}")
            return result

    try:
        # Try running Playwright in the current loop (typical async server case)
        return await _playwright_flow()
    except NotImplementedError as e:
        # Happens on Windows when the running event loop doesn't support subprocesses.
        # Run the playwright flow inside a dedicated thread with a Proactor event loop.
        logger.warning(f"NotImplementedError caught: {e}. Using thread-based workaround for Windows.")
        result_container = {}
        def _run_in_thread():
            try:
                # Create a new loop with Proactor policy for subprocess support
                if platform.system() == 'Windows':
                    try:
                        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    except AttributeError:
                        # Fallback for older Python versions
                        pass
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                res = loop.run_until_complete(_playwright_flow())
                result_container['res'] = res
            except Exception as e:
                logger.error(f"Error in thread: {e}")
                result_container['res'] = {"status":"error","errors":[str(e)]}
            finally:
                try: 
                    loop.close()
                except: 
                    pass
        t = threading.Thread(target=_run_in_thread)
        t.start(); t.join()
        return result_container.get('res', {"status":"error","errors":["Unknown error in thread execution"]})
    except Exception as e:
        logger.error(f"Unexpected error in run_headless: {e}")
        return {"status": "error", "errors": [str(e)]}

# ------------------- CLI -------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt"); parser.add_argument("--no-headless", action="store_true")
    parser.add_argument("--cookies"); parser.add_argument("--cookies-file"); parser.add_argument("--serve-http", action="store_true")
    parser.add_argument("--http-port", type=int, default=8080)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Ensure Windows event loop policy is set
    if platform.system() == 'Windows':
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            pass
    
    if args.serve_http:
        httpd, port = start_http_server(args.http_port)
        print(f"HTTP server running at http://localhost:{port}/headless?prompt=hi")
        try: 
            while True: time.sleep(1)
        except KeyboardInterrupt: httpd.shutdown()
    else:
        if not args.prompt: parser.error("--prompt required unless --serve-http")
        # run_headless is async; use asyncio.run when invoked from CLI
        try:
            result = asyncio.run(run_headless(vars(args)))
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(run_headless(vars(args)))
                finally:
                    loop.close()
            else:
                raise
        except Exception as e:
            logger.error(f"Error running headless: {e}")
            result = {"status": "error", "errors": [str(e)]}
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.exit(0 if result["status"]=="success" else 1)

if __name__=="__main__": main()
