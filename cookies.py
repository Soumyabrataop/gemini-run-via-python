import sys
import argparse
import os

def netscape_to_cookie_string(netscape_file, output_file=None):
    cookies = []

    try:
        with open(netscape_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split('\t')
                if len(parts) < 7:
                    continue
                name = parts[5]
                value = parts[6]
                cookies.append(f"{name}={value}")
    except FileNotFoundError:
        print(f"Error: Cookie file '{netscape_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading cookie file: {e}")
        sys.exit(1)

    cookie_string = '; '.join(cookies)

    if output_file:
        try:
            with open(output_file, 'w') as f:
                f.write(cookie_string)
            print(f"Cookie string saved to {output_file}")
        except Exception as e:
            print(f"Error writing to output file: {e}")
            sys.exit(1)
    else:
        # Output to stdout for piping
        print(cookie_string)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert Netscape cookie format to cookie string format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cookies.py --cookies.txt /path/to/cookies.txt
  python cookies.py --cookies.txt /path/to/cookies.txt --output converted_cookies.txt
  curl -s https://raw.githubusercontent.com/Soumyabrataop/gemini-run-via-python/main/cookies.py | python - --cookies.txt /path/to/cookies.txt
        """
    )
    
    parser.add_argument('--cookies.txt', '--cookies', 
                       dest='cookies_file',
                       required=True,
                       help='Path to the Netscape format cookies.txt file')
    
    parser.add_argument('--output', '-o',
                       dest='output_file',
                       help='Output file path (if not specified, prints to stdout)')
    
    # Handle legacy positional arguments for backward compatibility
    if len(sys.argv) == 3 and not any(arg.startswith('--') for arg in sys.argv[1:]):
        # Legacy mode: python cookies.py <input> <output>
        netscape_file = sys.argv[1]
        output_file = sys.argv[2]
        netscape_to_cookie_string(netscape_file, output_file)
    else:
        # New argument parsing mode
        args = parser.parse_args()
        netscape_to_cookie_string(args.cookies_file, args.output_file)

