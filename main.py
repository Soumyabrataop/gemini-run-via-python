import argparse, os, sys, requests, time, random, json, threading, http.server, socket, re
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from cookie_helpers import parse_cookies
load_dotenv()

DEFAULT_URL = "https://gemini.google.com/_/BardChatUi/data/assistant.lamda.BardFrontendService/StreamGenerate"

# ---------------- COOKIES ---------------- #
def load_cookies():
    cookies = parse_cookies()
    if cookies:
        return "; ".join([f"{c['name']}={c['value']}" for c in cookies])
    return None

def build_headers(cookie): 
    h = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Referer": "https://gemini.google.com/",
        "X-Same-Domain": "1",
        "sec-ch-ua": '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Origin": "https://gemini.google.com",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br"
    }
    if cookie: h["Cookie"] = cookie
    return h

# ---------------- HELPERS ---------------- #
def _random_fsid(): 
    import secrets
    return "-"+str(secrets.randbelow(10**18))

def _extract_media(buf:str)->List[str]: 
    return re.findall(r'https?://\S+\.(?:png|jpg|jpeg|webp|gif|mp4|webm)',buf)

def download_media(url,out="./output"): 
    Path(out).mkdir(exist_ok=True)
    fn=Path(out)/f"gemini_{int(time.time())}{Path(url).suffix or '.jpg'}"
    try: 
        r=requests.get(url,stream=True,timeout=15)
        r.raise_for_status()
        open(fn,"wb").write(r.content)
        return str(fn)
    except: 
        return None

# ---------------- CORE ---------------- #
def run_main(args:Dict[str,Any])->Dict[str,Any]:
    try:
        if not args.get("at_token"): 
            return {"status":"error","errors":["Missing at_token"]}
        
        cookie = load_cookies()
        if not cookie: 
            return {"status":"error","errors":["No cookies found in GEMINI_COOKIES environment variable"]}
        
        headers = build_headers(cookie)
        prompt = args.get("prompt")
        if isinstance(prompt, list):
            prompt = " ".join(prompt)
        
        # Build the f.req parameter
        req_data = [
            None,
            json.dumps([
                [prompt, 0, None, None, None, None, 0],
                ["en"],
            ])
        ]
        
        data = {
            "f.req": json.dumps(req_data),
            "at": args["at_token"]
        }
        
        params = {
            "bl": "boq_assistant-bard-web-server_20250909.02_p1",
            "hl": "en",
            "_reqid": str(random.randint(1000000, 9999999)),
            "rt": "c",
            "f.sid": _random_fsid()
        }
        
        buf = ""
        with requests.post(DEFAULT_URL, headers=headers, params=params, data=data, timeout=60, stream=True) as r:
            if r.status_code != 200: 
                return {"status":"error","errors":[f"HTTP {r.status_code}"]}
            
            with open("stream_full.log", "w", encoding="utf-8") as f:
                for ln in r.iter_lines(decode_unicode=True): 
                    if not ln: continue
                    f.write(ln + "\n")
                    buf += ln + "\n"
        
        # Extract response text using improved logic
        response_text = ""
        
        # Method 1: Look for lines starting with )]}'
        lines = buf.strip().split('\n')
        for line in lines:
            if line.startswith(')]}\'\n') or line.startswith(')]}\'\r\n'):
                line = line[5:]  # Remove the prefix
            elif line.startswith(')]}\''): 
                line = line[4:]  # Remove the prefix
            
            # Skip non-JSON lines
            if not line.strip() or not line.startswith('['):
                continue
                
            try:
                # Parse the JSON line
                response_data = json.loads(line)
                
                # Look for the specific structure: [["wrb.fr", null, "..."]]
                if (isinstance(response_data, list) and len(response_data) > 0 and 
                    isinstance(response_data[0], list) and len(response_data[0]) > 2 and
                    response_data[0][0] == "wrb.fr"):
                    
                    # The third element contains the nested JSON string
                    nested_json_str = response_data[0][2]
                    if isinstance(nested_json_str, str):
                        try:
                            # Parse the nested JSON
                            nested_data = json.loads(nested_json_str)
                            
                            # Navigate to response: nested_data[4][0][1][0]
                            if (isinstance(nested_data, list) and len(nested_data) > 4 and
                                isinstance(nested_data[4], list) and len(nested_data[4]) > 0 and
                                isinstance(nested_data[4][0], list) and len(nested_data[4][0]) > 1 and
                                isinstance(nested_data[4][0][1], list) and len(nested_data[4][0][1]) > 0):
                                
                                text = nested_data[4][0][1][0]
                                if isinstance(text, str) and len(text.strip()) > len(response_text.strip()):
                                    response_text = text.strip()
                                    
                        except json.JSONDecodeError:
                            continue
                            
            except json.JSONDecodeError:
                continue
        
        # Method 2: Fallback regex if structured parsing fails
        if not response_text:
            # Look for quoted strings that look like responses
            text_patterns = [
                r'"(I\'m [^"]{50,})"',  # Starts with "I'm" 
                r'"([^"]{100,})"',     # Long quoted strings
                r'\[\"([^\"]{50,})\"\]',  # Text in array format
            ]
            
            all_matches = []
            for pattern in text_patterns:
                matches = re.findall(pattern, buf)
                all_matches.extend(matches)
            
            # Filter for conversational text
            for match in all_matches:
                # Skip technical strings
                if any(skip in match.lower() for skip in ['http', 'www.', 'data=', 'wrb.fr', 'maps.google']):
                    continue
                # Look for response-like content
                if any(word in match.lower() for word in ['gemini', 'language model', 'help', 'conversation', 'i am', "i'm"]):
                    if len(match) > len(response_text):
                        response_text = match
        
        # Clean up response - handle escaped characters
        if response_text:
            response_text = response_text.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"')
            
        media = [{"url": u, "local": download_media(u)} for u in _extract_media(buf)]
        return {"status": "success", "data": {"response": response_text, "media": media}}
        
    except Exception as e: 
        return {"status": "error", "errors": [str(e)]}

# ---------------- CLI ---------------- #
def main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", nargs='+')
    p.add_argument("--at", required=True)
    a = p.parse_args(argv)
    
    res = run_main({"prompt": a.prompt, "at_token": a.at})
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res["status"] == "success" else -1

if __name__ == "__main__": 
    raise SystemExit(main())