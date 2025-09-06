# gemini-run-via-python

![Screenshot](https://github.com/user-attachments/assets/e275683a-5e73-4a62-a5d4-2ca2b2e385c0)

For updates and more information, visit the [Releases page](https://github.com/Soumyabrataop/gemini-run-via-python/releases).

---

### Important Notice

The scripts `headless.py` and `main.py` are currently designed to work **only on Windows OS** and with the **Firefox browser**. If you're using a different operating system or browser, these scripts might not work properly.

---

### Setup Instructions (For Windows Users with Firefox)

1. **Start the Program:**
      Run this command to get started:
      `python init.py`

2. **Use Headless Mode (Option 2):**
      If you want to get images, text, and videos from Gemini, use Option 2 (Headless Mode).

3. **Use API Mode (Option 1):**
      If you only need text responses from Gemini, choose Option 1 (API Mode).

4. **Exit the Program (Option 3):**
      If you're done, choose Option 3 to exit the program.

---

### Instructions (For Non-Windows Users or Those Without Firefox)

If you're not on Windows or don't have Firefox, you can still use the script by following these steps:

1. **Install a Cookie Exporter Extension**
      Download and install a browser extension that lets you export cookies to a `.txt` file (search for "cookies.txt export" in your browser's extension store).

2. **Export Your Cookies**
      Once you've installed the extension, use it to export your cookies and save them as a `.txt` file. Name the file `cookies.txt` and save it somewhere easy to find.

3. **Convert Your Cookies File**
      Convert your cookies into the right format by running this command:
      `curl -s https://raw.githubusercontent.com/Soumyabrataop/gemini-run-via-python/main/cookies.py | python - --cookies.txt /path/to/cookies.txt`

   Make sure to replace `/path/to/cookies.txt` with the location of your exported cookies file.

---

### Running the Main Script

To run the `main.py` script, you’ll need two things:

* **Your Prompt** (what you want to ask the Gemini service)
* **Your Authentication Token (`--at`)**
* **Your Cookies (`--cookie`)** (from the previous step)

---

#### Example Command:

```bash
python main.py --prompt "Hello, how are you?" --at "YOUR_AT_TOKEN" --cookie "$(cat /path/to/cookies.txt)"
```

* Replace `"YOUR_AT_TOKEN"` with the **authentication token** you copied from your browser's developer tools (find it under the "StreamGenerate" request from `gemini.google.com`).
* Replace `/path/to/cookies.txt` with the path to the `cookies.txt` file you saved earlier.

---

### Disclaimer

This repository is for educational purposes only. It is not intended to be used for scraping Gemini's website or APIs in any unauthorized way. The goal is to help users understand how Gemini's authentication system and cookies work.

