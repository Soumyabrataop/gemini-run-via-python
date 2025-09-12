import json
import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("gemini-browser")

def parse_cookies(cookie_str: Optional[str] = None, cookie_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse cookies from various sources in different formats.
    
    Args:
        cookie_str: String containing cookies in key=value format only
        cookie_file: Path to file containing cookies in JSON, Netscape, or key=value format
        
    Returns:
        List of cookie dictionaries in Playwright format
    """
    cookies = []
    
    # Try environment variable first if no parameters provided
    if not cookie_str and not cookie_file:
        cookie_str = os.environ.get("GEMINI_COOKIES")
        cookie_file = os.environ.get("GEMINI_COOKIES_FILE")
        
        if not cookie_str and not cookie_file:
            logger.warning("No cookies provided via parameters or environment variables")
            return []
            
    # Process cookie string if provided
    if cookie_str:
        try:
            # Try parsing as JSON first
            if cookie_str.strip().startswith("[") or cookie_str.strip().startswith("{"):
                parsed_cookies = json.loads(cookie_str)
                
                # Handle both array of cookies and single cookie object
                if isinstance(parsed_cookies, dict):
                    cookies.append(parsed_cookies)
                elif isinstance(parsed_cookies, list):
                    cookies.extend(parsed_cookies)
                    
            # If not JSON, try key=value format
            else:
                # Handle multiple cookies separated by semicolons
                for cookie_pair in cookie_str.split(";"):
                    if "=" in cookie_pair:
                        name, value = cookie_pair.strip().split("=", 1)
                        cookies.append({
                            "name": name.strip(),
                            "value": value.strip(),
                            "domain": ".google.com",
                            "path": "/",
                            "sameSite": "Lax"
                        })
        except Exception as e:
            logger.error(f"Error parsing cookie string: {e}")

    # Process cookie file if provided
    if cookie_file:
        try:
            cookie_path = Path(cookie_file)
            if not cookie_path.exists():
                logger.error(f"Cookie file not found: {cookie_file}")
            else:
                # Try multiple encodings for better Windows compatibility
                content = None
                encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
                
                for encoding in encodings_to_try:
                    try:
                        with open(cookie_path, 'r', encoding=encoding, errors='ignore') as f:
                            content = f.read()
                        break
                    except (UnicodeDecodeError, OSError) as e:
                        logger.debug(f"Failed to read with {encoding}: {e}")
                        continue
                
                if content is None:
                    logger.error(f"Could not read cookie file with any supported encoding")
                    return cookies
                
                logger.info(f"Successfully read cookie file, content length: {len(content)} characters")
                
                # Try parsing as JSON
                try:
                    parsed_cookies = json.loads(content)
                    logger.info(f"Successfully parsed cookies as JSON, found {len(parsed_cookies) if isinstance(parsed_cookies, list) else 1} cookies")
                    
                    # Handle both array of cookies and single cookie object
                    if isinstance(parsed_cookies, dict):
                        cookies.append(parsed_cookies)
                    elif isinstance(parsed_cookies, list):
                        cookies.extend(parsed_cookies)
                        
                # If not JSON, try Netscape cookie format
                except json.JSONDecodeError as je:
                    logger.info(f"Not JSON format, trying Netscape format: {je}")
                    netscape_cookies = 0
                    for line in content.splitlines():
                        if line.strip() and not line.startswith('#'):
                            parts = line.strip().split('\t')
                            if len(parts) >= 7:
                                cookies.append({
                                    "name": parts[5],
                                    "value": parts[6],
                                    "domain": parts[0],
                                    "path": parts[2],
                                    "secure": parts[3] == "TRUE",
                                    "httpOnly": False,
                                    "sameSite": "Lax"
                                })
                                netscape_cookies += 1
                    logger.info(f"Parsed {netscape_cookies} cookies from Netscape format")
        except Exception as e:
            logger.error(f"Error parsing cookie file: {e}")

    # Ensure cookies are in the format Playwright expects
    for cookie in cookies:
        # Ensure required fields
        if "name" not in cookie or "value" not in cookie:
            continue
            
        # Add domain if missing
        if "domain" not in cookie:
            cookie["domain"] = ".google.com"
            
        # Add path if missing
        if "path" not in cookie:
            cookie["path"] = "/"
            
        # Add sameSite if missing (required by Playwright)
        if "sameSite" not in cookie:
            cookie["sameSite"] = "Lax"  # Default to "Lax" for Google cookies
            
        # Ensure sameSite has a valid value and convert browser export values
        sameSite_value = cookie.get("sameSite")
        if sameSite_value == "unspecified":
            cookie["sameSite"] = "Lax"
        elif sameSite_value == "no_restriction":
            cookie["sameSite"] = "None"
        elif sameSite_value == "strict":
            cookie["sameSite"] = "Strict"
        elif sameSite_value == "lax":
            cookie["sameSite"] = "Lax"
        elif sameSite_value not in ["Strict", "Lax", "None"]:
            cookie["sameSite"] = "Lax"  # Default fallback

    logger.info(f"Successfully parsed {len(cookies)} cookies")
    return cookies

def is_running_in_docker() -> bool:
    """Check if the script is running in a Docker container"""
    # Check for .dockerenv file
    if Path('/.dockerenv').exists():
        return True
        
    # Check cgroup
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except (IOError, FileNotFoundError):
        pass
        
    docker_env = os.environ.get('DOCKER_CONTAINER', 'false').lower().strip()
    if docker_env in ('true', '1', 'yes', 'on'):
        return True
        
    return False
