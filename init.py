import asyncio, platform, sys, os, logging, json, time, threading, concurrent.futures
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import pyfiglet
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Import main functions
from main import run_main
from headless import run_headless

# Logging
logger = logging.getLogger("gemini-api")
logger.setLevel(logging.INFO)
fh = logging.FileHandler("stream_full.log", encoding="utf-8")
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)
logger.addHandler(logging.StreamHandler(sys.stdout))

# Windows asyncio fix - ensure we use ProactorEventLoop for Playwright subprocess support
if platform.system() == 'Windows':
    try: 
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        logger.info("Set Windows ProactorEventLoop policy for Playwright subprocess support")
    except AttributeError: 
        logger.warning("ProactorEventLoop not available, using default policy")

# Output dir
Path("./output").mkdir(exist_ok=True)

# Banner
def display_banner():
    ascii_art = pyfiglet.figlet_format("CODIIFYCODERS", font="slant")
    print("\n" + "\n".join(line.center(80) for line in ascii_art.splitlines() if line.strip()))
    print("\n" + "Telegram: https://t.me/codiifycoders".center(80))
    print("GitHub: https://github.com/codiifycoders".center(80) + "\n")

# FastAPI lifespan with environment validation
@asynccontextmanager
async def lifespan(app: FastAPI):
    display_banner()
    
    # Validate critical environment variables
    if not os.getenv('GEMINI_COOKIES') and not os.getenv('GEMINI_COOKIES_FILE'):
        logger.warning("No GEMINI_COOKIES or GEMINI_COOKIES_FILE configured. API may not work properly.")
    
    logger.info("API started")
    yield
    logger.info("API shutting down")

app = FastAPI(lifespan=lifespan)

# CORS + static
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/output", StaticFiles(directory="output"), name="output")

# Models with validation
class ApiRequest(BaseModel): 
    prompt: str
    at_token: str
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if len(self.prompt) > 10000:
            raise ValueError("Prompt too long (max 10000 characters)")

class BrowserRequest(BaseModel): 
    prompt: str
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        if len(self.prompt) > 10000:
            raise ValueError("Prompt too long (max 10000 characters)")

# Endpoints
@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Codiifycoders Gemini API",
        "endpoints": {
            "/api": "Gemini API request",
            "/browser": "Gemini browser automation",
            "/logs": "Get logs",
            "/docs": "API docs"
        },
        "usage": {
            "api": {"required": ["prompt","at_token"]},
            "browser": {"required": ["prompt"]}
        },
        "join": "https://telegram.me/codiifycoders"
    }

@app.post("/api")
async def api_endpoint(req: ApiRequest):
    try:
        args = req.dict()
        
        # Use the simplified run_main from main.py (no cookies_file parameter needed)
        result = run_main(args)
        return JSONResponse(content=result)
        
    except ValueError as e:
        logger.warning(f"API validation error: {e}")
        return JSONResponse(status_code=400, content={"status":"error","error":str(e)})
    except Exception as e:
        logger.error("API error", exc_info=True)
        return JSONResponse(status_code=500, content={"status":"error","error":str(e)})

@app.post("/browser")
async def browser_endpoint(req: BrowserRequest):
    try:
        args = req.dict()
        args.update({
            'cookies': os.getenv('GEMINI_COOKIES'),
            'cookies_file': os.getenv('GEMINI_COOKIES_FILE'),
            'public_url': os.getenv('PUBLIC_URL'),
            'no_headless': os.getenv('HEADLESS','false').lower() == 'false'
        })
        
        # Validate required environment variables for browser endpoint
        if not args.get('cookies') and not args.get('cookies_file'):
            logger.warning("No cookies configured for browser endpoint")
        
        # Run headless in a separate thread with proper event loop for Windows
        import threading
        import concurrent.futures
        
        def run_headless_sync():
            try:
                if platform.system() == 'Windows':
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(run_headless(args))
                finally:
                    loop.close()
            except Exception as e:
                logger.error(f"Error in headless execution: {e}", exc_info=True)
                return {"status": "error", "errors": [str(e)]}
        
        # Use thread pool to run the headless function
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_headless_sync)
            result = future.result(timeout=300)  # 5 minute timeout
        
        return JSONResponse(content=result)
        
    except ValueError as e:
        logger.warning(f"Browser validation error: {e}")
        return JSONResponse(status_code=400, content={"status":"error","error":str(e)})
    except Exception as e:
        logger.error("Browser error", exc_info=True)
        return JSONResponse(status_code=500, content={"status":"error","error":str(e)})

@app.get("/logs")
async def get_logs():
    try:
        log_path = Path("stream_full.log")
        if not log_path.exists():
            return {"status":"success","data":{"log_content":"","log_size":0}}
        
        # Read with error handling for encoding issues
        try:
            content = log_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            return {"status":"error","error":"Could not read log file"}
            
        return {
            "status":"success",
            "data":{
                "log_content":content,
                "log_size":len(content),
                "timestamp":time.time()
            }
        }
    except Exception as e:
        logger.error("Error in logs endpoint", exc_info=True)
        return JSONResponse(status_code=500, content={"status":"error","error":str(e)})

if __name__ == "__main__":
    uvicorn.run("init:app", host="0.0.0.0", port=8080, reload=True)
