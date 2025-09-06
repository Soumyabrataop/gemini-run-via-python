import sys
import argparse

def netscape_to_cookie_string(netscape_file):
    cookies = []
    with open(netscape_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 7:
                cookies.append(f"{parts[5]}={parts[6]}")
    return '; '.join(cookies)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--cookies.txt', dest='cookies_file', required=True)
    args = parser.parse_args()
    print(netscape_to_cookie_string(args.cookies_file))

