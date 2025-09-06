import sys

def netscape_to_cookie_string(netscape_file, output_file):
    cookies = []

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

    cookie_string = '; '.join(cookies)

    with open(output_file, 'w') as f:
        f.write(cookie_string)

    print(f"Cookie string saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_cookies.py <netscape_cookie_file> <output_file>")
        sys.exit(1)
    netscape_file = sys.argv[1]
    output_file = sys.argv[2]
    netscape_to_cookie_string(netscape_file, output_file)

