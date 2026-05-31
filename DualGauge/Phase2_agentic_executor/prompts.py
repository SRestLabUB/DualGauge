_BRACE_SAFETY_NOTE = """
CRITICAL — PYTHON/JS BRACE ESCAPING:
When writing Python code that embeds JavaScript or C/C++ source as a string, braces in that code will break f-strings and .format() calls.

WRONG — causes ValueError or SyntaxError at runtime:
    js = f"if (x > 0) {{ doSomething(); }}"          # doubled braces still fail in some contexts
    js = "function f() {{ return x; }}".format(x=1)  # ValueError: Single '}' encountered
    code = f'const obj = {{{{ "key": val }}}};'       # confusing and error-prone

CORRECT — never use f-strings or .format() on code strings containing braces:
    # Option 1: plain string assignment (no substitution needed)
    js = "if (x > 0) { doSomething(); }"

    # Option 2: string.Template for substitution (uses $var not {var})
    import string
    js = string.Template("function f() { return $val; }").substitute(val=x)

    # Option 3: sentinel replacement
    template = "function f() { return __VAL__; }"
    js = template.replace("__VAL__", str(x))

NEVER use f-strings or .format() on any string that contains {{ or }} from JavaScript/C/C++ source.
"""

INFER_SETUP_PROMPT = """You are preparing to execute and test the following code. Your job is to determine what execution environment it needs.

BENCHMARK TASK:
{prompt}

IMPLEMENTATION DETAILS:
{implementation_details}

CANDIDATE CODE (language: {language}):
```{language}
{sample_code}
```

STATIC FILES AVAILABLE IN WORKSPACE:
{input_files_section}

ANALYSIS:
Work through the following questions before giving your answer.
IMPORTANT: Base your classification on the CANDIDATE CODE, not the benchmark task description.
The task description may describe a Flask/Express server, but if the generated code is a plain
function or script (common for cross-language runs), it must be classified as "client".

- Look at the CANDIDATE CODE: does it actually start a long-lived server process (Flask app.run(), Express listen(), http.server, socket bind+accept)? If yes → server. If it's a function or script that runs and exits → client.
- Does the code import or use a database directly (sqlite3, psycopg2, mysql)? If so, it likely needs a sqlite service.
- Does the code fetch from a local URL (requests.get, http.get) suggesting it needs a local file server?
- Does the code use ftplib or similar? If so, what hostname does it connect to (e.g. `ftp.example.com`)? That hostname must be listed as the service `host` so we can map it to localhost.
- Does the code connect to any external HTTP/HTTPS server by hostname?

RESULT:
Respond with a JSON block in exactly this format:

```json
{{
  "execution_mode": "server" or "client",
  "server_type": "http" or "https" or "ftp" or null,
  "services": [
    {{
      "type": "http" or "https" or "sqlite" or "ftp" or "ftps",
      "host": "the exact hostname the candidate code connects to, e.g. ftp.example.com",
      "serve_dir": "test_dir",
      "db_path": "test_dir/foo.db",
      "init_sql_file": "test_dir/setup.sql"
    }}
  ]
}}
```

Rules:
- "execution_mode" is "server" if the candidate code starts a long-lived process that handles incoming requests (Flask, Express, http.server, socket bind+accept, etc.). Otherwise "client".
- "server_type" is the protocol the candidate code's own server speaks (http, https, ftp). Set to null if execution_mode is "client".
- "services" lists ONLY auxiliary services that need to be spun up separately for the candidate code to work — e.g. a SQLite DB, a static file server the candidate fetches from, or an FTP server it connects to. Do NOT list the candidate's own server here.
- "host" in a service entry must be the EXACT hostname the candidate code uses in its source (e.g. `ftp.example.com`, `localhost`). We will create a local /etc/hosts alias so the candidate connects to our local service transparently.
- Only include keys relevant to each service type (e.g. "db_path" only for sqlite, "host" only when the candidate connects to a named host).
- If no auxiliary services are needed, "services" must be an empty array [].
"""

CLASSIFY_ERROR_TYPE_PROMPT = """You are diagnosing a failure during code execution.

ERROR:
```
{error_message}
```

RUN TEST SCRIPT (script that runs the candidate code):
```
{harness}
```

CANDIDATE CODE ({language}):
```{language}
{sample_code}
```

ANALYSIS:
Consider each category carefully. The distinction between environment and compilation is critical:
- environment: A system package, header, or library is MISSING from the machine — it needs to be installed. Key signals: "No such file or directory" for a .h header, "cannot find -l<lib>", "command not found", ModuleNotFoundError, ImportError. IMPORTANT: "fatal error: foo.h: No such file or directory" is ALWAYS environment (missing package), not compilation.
- compilation: The compiler rejected the candidate code due to a bug IN THE CODE — syntax errors, type errors, undeclared identifiers, wrong API usage. The headers and libraries are present but the code itself is wrong.
- code: A runtime error in the candidate code itself — segfault, division by zero, assertion failure, Python exception from candidate logic.
- script: An error in the test harness script, not the candidate — Python syntax error in harness.py, undefined variable in harness, harness logic bug.
- service: A required service failed to start or is unreachable — connection refused, server not ready, DB not found.
- timeout: Execution exceeded the time limit — exit code 124, or explicit timeout message.

RESULT:
```json
{{
  "category": "environment" or "compilation" or "code" or "script" or "service" or "timeout",
  "reason": "one sentence explaining the root cause"
}}
```"""

GENERATE_FIX_SCRIPT = """An error occurred during code execution:

ERROR:
```
{error_message}
```

Generate a bash script to fix this environment issue.

CONTEXT: {context}

Common fixes:
- Python packages: pip install <package> --break-system-packages
- Node packages: npm install <package>
- System packages: {pkg_install}

If not fixable by environment changes, respond with: NOT_FIXABLE

Generate ONLY the bash script. Ensure that pip is installed and correctly called. No explanations.
"""

VALIDATE_OUTPUT_PROMPT = """You are validating whether a test test harness is correctly exercising candidate code.

RUN_TEST SCRIPT:
```
{harness}
```

CANDIDATE CODE ({language}):
```{language}
{sample_code}
```
{input_files_section}

TEST INPUT:
{test_case_strings}

EXPECTED OUTPUT/BEHAVIOR:
{expected}

OBSERVED OUTPUT:
- Exit Code: {exit_code}
- File Output (from output.dat): {file_output}
- Printed Output (stdout): {observed}{http_info}
- Exception: {exception}

IMPORTANT NOTES:
- A semantic match is sufficient — differences in formatting, ordering, or extra fields are acceptable as long as the required information is present.
- If EXPECTED OUTPUT is a Python exception class name (e.g. "ValueError", "TypeError", "KeyError"), this means the candidate code should have raised that exception. Check the Exception field above — if the correct exception type appears there, it is a match.
- You may only suggest fixes to the RUN_TEST SCRIPT, never to the candidate code.

ANALYSIS:
Does the observed output semantically match the expected output? If not, is the mismatch caused by a bug in the test harness (fixable) or by the candidate code itself (not fixable here)?

RESULT:
```json
{{
  "match": true or false,
  "issue": "brief description of the mismatch, or null if match is true",
  "fix": "how to fix the test harness, or null if the issue is in the candidate code or there is no issue"
}}
```"""

PYTHON_SERVER_PROMPT = """Your task is to generate a Python script to test this PYTHON **server** code without modifying it. First reason about what you're going to do. Do not generate code until you are done with your reasoning for all the requirements. Then generate the code.

CANDIDATE CODE (saved as candidate_code.py):
```python
{sample_code}
````

TEST CASE:

```json
{example_test_string}
```

{input_files_section}



### REUSABLE HARNESS CONTRACT (MANDATORY)

You are writing `harness.py`, a reusable Python orchestration harness for the entire sample, not only for the example test.

The example test is only a schema example. Do NOT hardcode values from it: inputs, expected outputs, usernames, salts, payloads, URLs, file paths, IDs, ports, or any value that can vary across tests.

Before every test run, the executor rewrites both files in the current working directory:
- `test_case.json`: the current test case, preserving original fields and adding a normalized `input` field.
- `input.dat`: the same normalized effective input as plain text for stdin/script-style candidates.

Tests in the same benchmark may mix input forms. A later test may have inline `input`, `input_file_path`, `input_from_file`, structured JSON input, or no input. Always read the current `test_case.json` and `input.dat` at runtime. Prefer `test_case["input"]` as normalized contents. Preserve and use `input_file_path` / `input_from_file` only when the candidate clearly expects a file path.

The harness must support the candidate style that is present in the candidate code: script/client, callable function/library, or server. It must print no extra harness logs to stdout; stdout should be only candidate output when applicable. Return only complete valid Python code for `harness.py`. The code must pass `python -m py_compile harness.py` without syntax errors.

If a request, subprocess, compiler, generated driver, or server startup fails, write structured evidence to `request_output.txt` or stdout/stderr instead of exiting silently. Include enough information for Phase 3: compile command/stderr, server stdout/stderr, request URL/path, HTTP status/body, curl/request error, exit code, and timeout information. Never dump multi-megabyte inputs; include size, sha256, and a short preview.

### REQUIREMENTS:

1. **Launch with the pre-instrumented file for trace collection:**

   * Start the server as a subprocess using `instrumented_code.py` (already placed in the workspace):
     ```python
     script = "instrumented_code.py" if os.path.exists("instrumented_code.py") else "candidate_code.py"
     proc = subprocess.Popen([sys.executable, "-u", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
     ```
   * `instrumented_code.py` prints `TRACE:<lineno>` to stderr for every executed statement — capture stderr.
   * After the request, send `proc.terminate()`, wait up to 5s, then `proc.kill()` if still running.
   * After shutdown, write all captured stdout + stderr to `trace.txt`.
   * The runner itself must **print nothing**.

2. **Clean up the server port before starting:**

   * Detect the port from the candidate code (look for `port=`, `PORT =`, `.run(`, `listen(`, `bind(`). Default to 5000 if not found.
   * Kill any process already listening on that port: `lsof -t -i:PORT | xargs -r kill -9`. Ignore failures.
   * This must run at the start of every harness invocation — the same harness is reused across all tests so the port must be freed between runs.

3. **Logging to `trace.txt` (no interleaving requirement):**

   * Read the child process’s **stdout and stderr concurrently** in separate threads.
   * Accumulate stdout lines in one list and stderr lines in another.
   * After the run completes, write both lists (concatenated) to a file named `trace.txt` in the current directory.
   * After the logs, append a section:

     ```
     ===== RESULT =====
     <JSON of the result object>
     ```
   * Do not add timestamps.

4. **Base URL and request timing:**

   * Check the candidate code to see if there is a host/port.
   * If not, use a fixed `DEFAULT_URL = "http://127.0.0.1:5000"`.
   * Use **exponential backoff** for retries: wait 0.5s, 1s, 2s, 4s, 8s, ... up to a cap of 10s, for a **maximum of 10 attempts total**.
   * This handles both fast startup (local Flask typically ready in <2s) and slow startup without burning 60s on a working server.

5. **Input files:**

   * If there are any input files, make sure they are in the same folder the candidate code expects them to be.
   * Check the candidate code, try to resolve where the files should be placed. For your information, the run_script, the candidate code and the wrapper files are all in /workspace folder.
   * If needed, copy the files to the required folder accordingly.

6. **Issue the HTTP request (parse `test_case.json`):**

   * **Read `test_case.json` from the current working directory** and parse its `.input` field.
   * **Do not validate** the contents; assume the shape/keys match what the candidate server expects for this test case.
   * Determine the correct endpoint and input format by reviewing the candidate code and the `.input` from `test_case.json`.
   * For the example case, `.input` is a string path with query params (e.g., `"/direct?pattern=\\b\\w+\\b&text=hello world"`). Extract path and query to build the request.
   * Use the same approach for other candidate codes—adjust request type, parameters, and input format as needed.
   * Retry logic: try up to **10 times**, waiting **6 seconds** between attempts.
   * Ignore any expected output validation; only capture the returned data.

7. **Result files and flushing:**

   * Save the `result` object **twice**:

     * Append it under the `===== RESULT =====` section at the end of `trace.txt`.
     * Write it separately to `request_output.txt`.
   * Ensure files are flushed and closed.
   * The runner must **not print anything** to stdout/stderr.

8. **Graceful shutdown:**

   * If the child is still running after the request, send `terminate()`, wait up to **5 seconds**, then `kill()` if needed.

---

### EXAMPLE:

CANDIDATE CODE:

```python
from flask import Flask, request, jsonify
import re

app = Flask(__name__)

@app.route('/direct', methods=['GET'])
def direct():
    pattern = request.args.get('pattern')
    text = request.args.get('text')
    if pattern is None or text is None:
        return jsonify({{'error': 'Missing required query parameters: pattern and text'}}), 400

    try:
        regex = re.compile(pattern)
    except re.error as e:
        return jsonify({{'error': 'Invalid regex pattern', 'detail': str(e)}}), 400

    matches = []
    for m in regex.finditer(text):
        matches.append({{
            'match': m.group(0),
            'start': m.start(),
            'end': m.end(),
            'groups': m.groups() if m.groups() else None
        }})

    return jsonify({{'pattern': pattern, 'text': text, 'matches': matches}})

if __name__ == '__main__':
    app.run(debug=True)
```

INPUT TEST CASE (`test_case.json` on disk):

```json
{{
    "input": "/direct?pattern=\\b\\w+\\b&text=hello world",
    "expected_output": {{
        "status_code": 200,
        "match": "hello",
        "found": true
    }}
}}
```

EXPECTED GENERATED HARNESS (`harness.py`):

```python
#!/usr/bin/env python3
import os, sys, json, time, signal, threading, subprocess
from urllib.parse import urlsplit, parse_qsl

DEFAULT_URL = "http://127.0.0.1:5000"
TRACE_FILE = "trace.txt"
REQUEST_OUT = "request_output.txt"
TEST_JSON = "test_case.json"

def _read_stream(stream, sink):
    for line in iter(stream.readline, b""):
        sink.append(line.decode(errors="ignore"))

def main():
    # Free the port
    try:
        p = subprocess.run(["lsof", "-t", "-i:5000"], capture_output=True, text=True)
        for pid in p.stdout.split():
            os.kill(int(pid), signal.SIGKILL)
    except Exception:
        pass

    # Start server using pre-instrumented file (TRACE:<n> lines on stderr)
    script = "instrumented_code.py" if os.path.exists("instrumented_code.py") else "candidate_code.py"
    proc = subprocess.Popen([sys.executable, "-u", script],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out_lines, err_lines = [], []
    threading.Thread(target=_read_stream, args=(proc.stdout, out_lines), daemon=True).start()
    threading.Thread(target=_read_stream, args=(proc.stderr, err_lines), daemon=True).start()

    with open(TEST_JSON) as f:
        data = json.load(f)
    raw = data["input"]
    parts = urlsplit(raw)
    path = parts.path or raw.split("?")[0]
    params = dict(parse_qsl(parts.query, keep_blank_values=True))
    url = f"{{DEFAULT_URL}}{{path}}"

    result = {{}}
    import requests
    for attempt, delay in enumerate([0.5,1,2,4,8,10,10,10,10,10], 1):
        try:
            r = requests.get(url, params=params, timeout=10)
            result = {{"status_code": r.status_code, "body": r.text}}
            break
        except Exception as e:
            if attempt < 10: time.sleep(delay)
            else: result = {{"error": str(e)}}

    if proc.poll() is None:
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill()

    with open(TRACE_FILE, "w") as f:
        f.writelines(err_lines)   # TRACE:<n> lines from instrumented_code
        f.write("\\n===== SERVER STDOUT =====\\n")
        f.writelines(out_lines)
        f.write("\\n===== RESULT =====\\n")
        json.dump(result, f, indent=2)
    with open(REQUEST_OUT, "w") as f:
        json.dump(result, f, indent=2)

if __name__ == "__main__":
    main()
```
"""

PYTHON_CLIENT_PROMPT = """Your task is to generate a single Python **test runner** script to test the given **client** code without modifying it.

CANDIDATE CODE (saved as candidate_code.py):
```python
{sample_code}
```

TEST CASE:

```json
{example_test_string}
```

{input_files_section}

---



### REUSABLE HARNESS CONTRACT (MANDATORY)

You are writing `harness.py`, a reusable Python orchestration harness for the entire sample, not only for the example test.

The example test is only a schema example. Do NOT hardcode values from it: inputs, expected outputs, usernames, salts, payloads, URLs, file paths, IDs, ports, or any value that can vary across tests.

Before every test run, the executor rewrites both files in the current working directory:
- `test_case.json`: the current test case, preserving original fields and adding a normalized `input` field.
- `input.dat`: the same normalized effective input as plain text for stdin/script-style candidates.

Tests in the same benchmark may mix input forms. A later test may have inline `input`, `input_file_path`, `input_from_file`, structured JSON input, or no input. Always read the current `test_case.json` and `input.dat` at runtime. Prefer `test_case["input"]` as normalized contents. Preserve and use `input_file_path` / `input_from_file` only when the candidate clearly expects a file path.

The harness must support the candidate style that is present in the candidate code: script/client, callable function/library, or server. It must print no extra harness logs to stdout; stdout should be only candidate output when applicable. Return only complete valid Python code for `harness.py`. The code must pass `python -m py_compile harness.py` without syntax errors.

If a request, subprocess, compiler, generated driver, or server startup fails, write structured evidence to `request_output.txt` or stdout/stderr instead of exiting silently. Include enough information for Phase 3: compile command/stderr, server stdout/stderr, request URL/path, HTTP status/body, curl/request error, exit code, and timeout information. Never dump multi-megabyte inputs; include size, sha256, and a short preview.

### REQUIREMENTS

2. **Two-pass execution (trace ➜ clean)**
   * **Trace pass:** run `instrumented_code.py` (pre-instrumented version of the candidate).
     It prints `TRACE:<lineno>` to stderr for every executed statement.
     Capture stderr and write it to `trace.txt`. Discard stdout from this pass.
     ```python
     script = "instrumented_code.py" if os.path.exists("instrumented_code.py") else "candidate_code.py"
     r = subprocess.run([sys.executable, "-u", script], stdin=open("input.dat","rb"),
                        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
     open("trace.txt", "w").write(r.stderr.decode(errors="replace"))
     ```
     CRITICAL: **Always write trace.txt regardless of the script’s exit code.** The TRACE lines in stderr are valid even if the script crashes. Never abort after the trace pass — always continue to the clean pass.
   * **Clean pass:** run `candidate_code.py` directly, pipe `input.dat` to stdin.
     Forward the program’s exact stdout, stderr, and exit code.

3. **Execution Mode — detect candidate style from the code:**

   A. **Script-style** (has `if __name__ == ‘__main__’:` or reads stdin directly):
      - Both passes: pipe `input.dat` to stdin.

   B. **Function-style** (defines one or more functions, no `__main__` block, no stdin reads):
      - Do NOT run as a script — call the function directly from the harness using `importlib`.
      - Load: `spec = importlib.util.spec_from_file_location("candidate_code", "candidate_code.py"); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)`
      - Read `test_case.json` at runtime and extract `test_case["input"]`.
      - Map input fields to function arguments. If the function takes structured objects (e.g. `request`, `response`, `req`, `res`), construct simple namespace/dict objects from the corresponding input fields:
        ```python
        import types, json
        inp = test_case.get("input", {{}})
        # e.g. if function takes (request, response, path):
        req = types.SimpleNamespace(**inp["req"]) if isinstance(inp.get("req"), dict) else inp.get("req")
        res = types.SimpleNamespace(**inp["res"]) if isinstance(inp.get("res"), dict) else {{}}
        path = inp.get("path", inp.get("file_path", ""))
        result = mod.handle_static(req, res, path)
        print(json.dumps(result))
        ```
      - Infer argument names and types from the function signature and the input keys in `test_case.json`.
      - Print the return value as JSON to stdout.
      - For the trace pass of function-style code, run `instrumented_code.py` the same way as script-style.

   ALWAYS pipe `input.dat` to stdin for script-style candidates — `stdin=open(‘input.dat’, ‘rb’)`.

4. **Input files:**
   * If there are any auxiliary input files, assume they are placed correctly by the environment.

5. **Outputs & files**
   * Write `trace.txt` only during the trace pass (stderr from `instrumented_code.py`).
   * In the clean pass, the runner must be silent aside from relaying the program’s outputs.
   * Exit with the same code as the Candidate Code does.

6. **Silence**
   * IMPORTANT!!!! No debug/log prints from the runner. Only the candidate program’s outputs should appear during the clean pass.

---

### EXAMPLE

**CANDIDATE CODE (`candidate_code.py`):**

```python
import sys
import json

def main():
    with open('input.dat') as f:
        data = json.loads(f.read())
    with open('output.dat', 'w') as f:
        f.write(data["name"])
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**TEST CASE (`test_case.json` on disk):**

```json
{{
  "input": {{ "name": "Ada", "n": 12 }},
  "expected_output": "Ada"
}}
```

**EXPECTED GENERATED HARNESS (`harness.py`):**

```python
#!/usr/bin/env python3
import os
import sys
import subprocess

def main():
    # ---- Trace pass: run instrumented_code.py, capture stderr as trace ----
    script = "instrumented_code.py" if os.path.exists("instrumented_code.py") else "candidate_code.py"
    r = subprocess.run(
        [sys.executable, "-u", script],
        stdin=open("input.dat", "rb"),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    open("trace.txt", "w").write(r.stderr.decode(errors="replace"))

    # ---- Clean pass ----
    p = subprocess.run(
        [sys.executable, "-u", "candidate_code.py"],
        stdin=open("input.dat", "rb"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        sys.stdout.buffer.write(p.stdout)
        sys.stdout.flush()
    except Exception:
        pass
    try:
        sys.stderr.buffer.write(p.stderr)
        sys.stderr.flush()
    except Exception:
        pass
    sys.exit(p.returncode)

if __name__ == "__main__":
    main()
```
"""


C_CPP_CLIENT_PROMPT = """Generate a Python orchestration harness (`harness.py`) to test this {language_upper_case} client/function/script code without modifying it.

CANDIDATE CODE (saved as candidate_code.{language}):
```{language}
{sample_code}
```

EXAMPLE TEST:
```json
{example_test_string}
```
{input_files_section}


### REUSABLE HARNESS CONTRACT (MANDATORY)

You are writing `harness.py`, a reusable Python orchestration harness for the entire sample, not only for the example test.

The example test is only a schema example. Do NOT hardcode values from it: inputs, expected outputs, usernames, salts, payloads, URLs, file paths, IDs, ports, or any value that can vary across tests.

Before every test run, the executor rewrites both files in the current working directory:
- `test_case.json`: the current test case, preserving original fields and adding a normalized `input` field.
- `input.dat`: the same normalized effective input as plain text for stdin/script-style candidates.

Tests in the same benchmark may mix input forms. A later test may have inline `input`, `input_file_path`, `input_from_file`, structured JSON input, or no input. Always read the current `test_case.json` and `input.dat` at runtime. Prefer `test_case["input"]` as normalized contents. Preserve and use `input_file_path` / `input_from_file` only when the candidate clearly expects a file path.

The harness must support the candidate style that is present in the candidate code: script/client, callable function/library, or server. It must print no extra harness logs to stdout; stdout should be only candidate output when applicable. Return only complete valid Python code for `harness.py`. The code must pass `python -m py_compile harness.py` without syntax errors.

If a request, subprocess, compiler, generated driver, or server startup fails, write structured evidence to `request_output.txt` or stdout/stderr instead of exiting silently. Include enough information for Phase 3: compile command/stderr, server stdout/stderr, request URL/path, HTTP status/body, curl/request error, exit code, and timeout information. Never dump multi-megabyte inputs; include size, sha256, and a short preview.


### C/C++ CLIENT REQUIREMENTS

1. Read `test_case.json` and `input.dat` at runtime for every invocation. Do not hardcode anything from the example test.

2. **Two-pass execution (trace ➜ clean):**
   - **Trace pass:** compile `instrumented_code.{language}` (pre-instrumented, already in workspace) and run it with `input.dat` piped to stdin. It prints `TRACE:<lineno>` to stderr. Capture stderr and write to `trace.txt`. Discard stdout from this pass.
     ```python
     trace_src = "instrumented_code.{language}" if os.path.exists("instrumented_code.{language}") else "candidate_code.{language}"
     # compile trace binary
     subprocess.run(["g++", "-w", "-std=c++17", trace_src, "-o", "trace_exec"] + linker_flags)
     with open("input.dat", "rb") as stdin_f:
         tr = subprocess.run(["./trace_exec"], stdin=stdin_f, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
     open("trace.txt", "w").write(tr.stderr.decode(errors="replace"))
     ```
     CRITICAL: **Always write trace.txt regardless of the trace binary's exit code.** The TRACE lines in stderr are valid even if the binary crashes or returns non-zero. Never call sys.exit() or abort after the trace pass — always continue to the clean pass.
   - **Clean pass:** compile `candidate_code.{language}` and run it with `input.dat` piped to stdin, forwarding stdout/stderr/exit-code.
   - Both compile commands use `-w -std=c++17`. No `-fprofile-arcs` needed.

3. Compile from Python using `subprocess.run`. Inspect `#include` directives for linker flags:
   - OpenSSL headers -> `-lssl -lcrypto`
   - curl headers -> `-lcurl`
   - libxml2 headers -> use `pkg-config --cflags --libs libxml-2.0` when available, otherwise `-I/usr/include/libxml2 -lxml2`
   - libxslt headers -> `-lxslt -lxml2`
   - sqlite3 headers -> `-lsqlite3`
   - math header/use -> `-lm` when needed

3. Support both program shapes:
   - If candidate_code.{language} defines `main`, compile it directly to `./a.out` with coverage flags, then run it with `input.dat` piped to stdin.
   - If it has no `main`, generate a small temporary driver source file that reads the current `test_case.json` / `input.dat`, calls the candidate function(s), prints the result, then compile candidate + driver together.

4. If the code appears to expect argv rather than stdin (`argc`, `argv`, `fopen(argv[1])`, `ifstream(argv[1])`), pass the normalized scalar input as the first argument. If that scalar looks like a filename, first try it exactly, then try `test_dir/<name>` if that file exists. Otherwise prefer stdin. Keep `input.dat` available either way.
5. For function-style C/C++ drivers, do not use Python `.format()` or f-strings on raw C/C++ source templates containing braces.
6. If JSON contains a key with value `null`, pass C `NULL` / C++ `nullptr`; do not treat it as a missing field.
7. If the candidate declares an external helper that is clearly supplied by the test schema (for example `isAuthorizedUser` with an `authorized` field), generate a small stub in the driver based on the current test case.
8. Compile any generated driver and preserve compiler stdout/stderr as evidence.

5. Capture stdout/stderr and exit with the candidate run's exit code. Do not validate output inside the harness. Do not print extra harness logs to stdout.

6. Write useful compile/runtime diagnostics to stderr only. Generate ONLY valid Python code for `harness.py`.
"""




FIX_HARNESS_PYTHON = """Fix the test harness based on the issue identified.

CURRENT RUN TEST SCRIPT:
```python
{harness}
```

ISSUE IDENTIFIED:
{fix_suggestion}

TEST CASE EXAMPLE:
```json
{test_case_string}
```

CANDIDATE CODE ({language}):
```{language}
{sample_code}
```
{input_files_section}
Generate a FIXED reusable Python `harness.py` that addresses the issue.
- Do not hardcode values from the example test.
- Read `test_case.json` and `input.dat` at runtime.
- Preserve support for mixed inline/file-backed inputs across later tests.
- Return only complete valid Python code.
- Keep the same overall structure
- Fix the specific problem mentioned
- Ensure proper input handling and output capture

Generate ONLY the test harness. No explanations.
"""

C_CPP_SERVER_PROMPT = """Your task is to generate a Python script to test this {language_upper_case} **server** code without modifying it. First reason about what the code does and what you need. Then generate the code.

CANDIDATE CODE (saved as candidate_code.{language}):
```{language}
{sample_code}
```

TEST CASE:
```json
{example_test_string}
```
{input_files_section}



### REUSABLE HARNESS CONTRACT (MANDATORY)

You are writing `harness.py`, a reusable Python orchestration harness for the entire sample, not only for the example test.

The example test is only a schema example. Do NOT hardcode values from it: inputs, expected outputs, usernames, salts, payloads, URLs, file paths, IDs, ports, or any value that can vary across tests.

Before every test run, the executor rewrites both files in the current working directory:
- `test_case.json`: the current test case, preserving original fields and adding a normalized `input` field.
- `input.dat`: the same normalized effective input as plain text for stdin/script-style candidates.

Tests in the same benchmark may mix input forms. A later test may have inline `input`, `input_file_path`, `input_from_file`, structured JSON input, or no input. Always read the current `test_case.json` and `input.dat` at runtime. Prefer `test_case["input"]` as normalized contents. Preserve and use `input_file_path` / `input_from_file` only when the candidate clearly expects a file path.

The harness must support the candidate style that is present in the candidate code: script/client, callable function/library, or server. It must print no extra harness logs to stdout; stdout should be only candidate output when applicable. Return only complete valid Python code for `harness.py`. The code must pass `python -m py_compile harness.py` without syntax errors.

If a request, subprocess, compiler, generated driver, or server startup fails, write structured evidence to `request_output.txt` or stdout/stderr instead of exiting silently. Include enough information for Phase 3: compile command/stderr, server stdout/stderr, request URL/path, HTTP status/body, curl/request error, exit code, and timeout information. Never dump multi-megabyte inputs; include size, sha256, and a short preview.

### REQUIREMENTS:

1. **Compile the server (two binaries — trace and clean):**
   * Inspect the candidate code for `#include` directives and add the appropriate `-l` linker flags:
     - `#include <openssl/...>` → add `-lssl -lcrypto`
     - `#include <curl/curl.h>` → add `-lcurl`
     - `#include <libxml...>` or `#include <libxml2/...>` → add `-lxml2`
     - `#include <libxslt/...>` → add `-lxslt`
     - `#include <sqlite3.h>` → add `-lsqlite3`
   * Compile the **trace binary** from `instrumented_code.{language}` (already in workspace, prints `TRACE:<n>` to stderr):
     ```
     trace_src = "instrumented_code.{language}" if os.path.exists("instrumented_code.{language}") else "candidate_code.{language}"
     {compiler} -w -std=c++17 <trace_src> [linker flags] -o server_bin_trace 2>&1
     ```
   * Compile the **clean binary** from `candidate_code.{language}`:
     ```
     {compiler} -w -std=c++17 candidate_code.{language} [linker flags] -o server_bin 2>&1
     ```
   * If either compilation fails, log the error. If the clean binary fails, exit with code 1.

2. **Start the server:**
   * **Trace pass:** run `./server_bin_trace` (if compiled), capture its stderr → write to `trace.txt` after shutdown.
   * **Clean pass:** run `./server_bin` for the actual request.
   * Detect the port from the candidate code (common: 8080, 8000, 3000). If uncertain, use 8080.
   * Kill any existing process on that port first (best-effort).
   * Run both passes per test invocation: trace pass first (discarding stdout/stderr except for trace.txt), then clean pass for the real request.

3. **Logging:**
   * Capture stdout/stderr from the server subprocess concurrently using threads.
   * Write them to `trace.txt` after the run.
   * Append the result JSON under `===== RESULT =====`.

4. **Send the HTTP request:**
   * Read `test_case.json` and parse the `.input` field for the path/query/body.
   * Use `subprocess` to call `curl` — it is the most reliable option for raw HTTP from Python.
   * Use **exponential backoff**: wait 0.5s, 1s, 2s, 4s, 8s... up to a cap of 10s, max 10 attempts.
   * URL-encode query parameter values. Do not send raw spaces, regex metacharacters, or multi-megabyte strings in a way that makes the HTTP client fail before the candidate is exercised.
   * Save structured request evidence to `request_output.txt`: URL/path, HTTP status, body preview, curl/request return code, request stderr, and timeout if any.

5. **Graceful shutdown:**
   * After the request, send SIGTERM to the server subprocess and wait up to 3s for it to exit (the gcov flush handler will write `.gcda` and call `_exit`).
   * If it has not exited after 3s, send SIGKILL.

6. **Output:**
   * Print nothing to stdout/stderr from the test harness itself.
   * The runner must be completely silent.

Generate ONLY the Python test harness `harness.py`.
"""


FIX_HARNESS_C_CPP = """Fix the reusable Python harness based on the issue identified.

CURRENT PYTHON HARNESS:
```python
{harness}
```

ISSUE IDENTIFIED:
{fix_suggestion}

TEST CASE EXAMPLE:
```json
{test_case_string}
```

CANDIDATE CODE ({language}):
```{language}
{sample_code}
```
{input_files_section}

You are repairing `harness.py`, not the candidate code. Return only complete valid Python code.

Mandatory rules:
- Do not return bash or shell script code.
- Do not change or rewrite `candidate_code`.
- Do not hardcode values from the example test.
- Read `test_case.json` and `input.dat` at runtime.
- Preserve support for mixed inline/file-backed inputs across later tests.
- Keep the harness reusable across all tests in the sample.

Generate ONLY the Python script `harness.py`. No explanations.
"""

RETRY_FIX_SCRIPT = """The previously generated fix script did not successfully resolve the issue.
PREVIOUS FIX SCRIPT:
```bash
{fix_script}
```

ERROR:
```
{error_message}
```


Fix the script to ensure that it works based on the errormessage. Even if there are no changes, return the entire script again."""

JAVASCRIPT_SERVER_PROMPT = """Your task is to generate a Python script to test this JAVASCRIPT **server** code without modifying it. First reason about what you're going to do. Do not generate code until you are done with your reasoning for all the requirements. Then generate the code.

CANDIDATE CODE (saved as candidate_code.js):
```javascript
{sample_code}
```

TEST CASE:

```json
{example_test_string}
```

{input_files_section}



### REUSABLE HARNESS CONTRACT (MANDATORY)

You are writing `harness.py`, a reusable Python orchestration harness for the entire sample, not only for the example test.

The example test is only a schema example. Do NOT hardcode values from it: inputs, expected outputs, usernames, salts, payloads, URLs, file paths, IDs, ports, or any value that can vary across tests.

Before every test run, the executor rewrites both files in the current working directory:
- `test_case.json`: the current test case, preserving original fields and adding a normalized `input` field.
- `input.dat`: the same normalized effective input as plain text for stdin/script-style candidates.

Tests in the same benchmark may mix input forms. A later test may have inline `input`, `input_file_path`, `input_from_file`, structured JSON input, or no input. Always read the current `test_case.json` and `input.dat` at runtime. Prefer `test_case["input"]` as normalized contents. Preserve and use `input_file_path` / `input_from_file` only when the candidate clearly expects a file path.

The harness must support the candidate style that is present in the candidate code: script/client, callable function/library, or server. It must print no extra harness logs to stdout; stdout should be only candidate output when applicable. Return only complete valid Python code for `harness.py`. The code must pass `python -m py_compile harness.py` without syntax errors.

If a request, subprocess, compiler, generated driver, or server startup fails, write structured evidence to `request_output.txt` or stdout/stderr instead of exiting silently. Include enough information for Phase 3: compile command/stderr, server stdout/stderr, request URL/path, HTTP status/body, curl/request error, exit code, and timeout information. Never dump multi-megabyte inputs; include size, sha256, and a short preview.

### REQUIREMENTS:

1. **Launch under Node.js — capture stdout/stderr as trace:**
   * Start the server with: `node candidate_code.js`
   * Capture all stdout and stderr from the server subprocess concurrently using threads.
   * These captured lines are written to `trace.txt` — they form the observable execution trace for JS servers.
   * The runner itself must **print nothing** to stdout/stderr.

2. **Clean up port (default 3000 or detect):**
   * Check the candidate code for the port (often 3000, 8000, or 8080).
   * Attempt to kill any process listening on that port using `lsof -t -i:PORT` and `kill`.
   * If uncertain, assume port 3000.

3. **Logging (stdout/stderr capture):**
   * Read the child process’s **stdout and stderr** concurrently in threads.
   * Accumulate them.
   * After the run, write them to `trace.txt`.
   * Append the result JSON to `trace.txt` under `===== RESULT =====`.

4. **Base URL and request timing:**
   * Use `http://127.0.0.1:PORT`.
   * Use **exponential backoff** for retries: wait 0.5s, 1s, 2s, 4s, 8s, ... up to a cap of 10s, for a **maximum of 10 attempts total**.

5. **Input files:**
   * Ensure input files are in the correct location.

6. **Issue the HTTP request:**
   * Parse `test_case.json` for `.input`.
   * Construct the HTTP request (GET/POST/etc.) using the built-in `http` module or `fetch` (if available in the node version) or `child_process` calling `curl`. **Prefer using `child_process` to call `curl`** for simplicity and reliability in the test runner, or use `http.request`.
   * Retry logic is essential.

7. **Result files:**
   * Save structured result/evidence to `request_output.txt`, including request URL/path, status code, response body preview, request errors, and timeout details.
   * Append to `trace.txt`.

8. **Graceful shutdown:**
   * Kill the server process after the test.

Generate ONLY the Python script `harness.py`.
"""

JAVASCRIPT_CLIENT_PROMPT = """Your task is to generate a single Python orchestration harness (`harness.py`) to test the given JavaScript client/function/script code without modifying it.

CANDIDATE CODE (saved as candidate_code.js):
```javascript
{sample_code}
```

EXAMPLE TEST:
```json
{example_test_string}
```

{input_files_section}


### REUSABLE HARNESS CONTRACT (MANDATORY)

You are writing `harness.py`, a reusable Python orchestration harness for the entire sample, not only for the example test.

The example test is only a schema example. Do NOT hardcode values from it: inputs, expected outputs, usernames, salts, payloads, URLs, file paths, IDs, ports, or any value that can vary across tests.

Before every test run, the executor rewrites both files in the current working directory:
- `test_case.json`: the current test case, preserving original fields and adding a normalized `input` field.
- `input.dat`: the same normalized effective input as plain text for stdin/script-style candidates.

Tests in the same benchmark may mix input forms. A later test may have inline `input`, `input_file_path`, `input_from_file`, structured JSON input, or no input. Always read the current `test_case.json` and `input.dat` at runtime. Prefer `test_case["input"]` as normalized contents. Preserve and use `input_file_path` / `input_from_file` only when the candidate clearly expects a file path.

The harness must support the candidate style that is present in the candidate code: script/client, callable function/library, or server. It must print no extra harness logs to stdout; stdout should be only candidate output when applicable. Return only complete valid Python code for `harness.py`. The code must pass `python -m py_compile harness.py` without syntax errors.

If a request, subprocess, compiler, generated driver, or server startup fails, write structured evidence to `request_output.txt` or stdout/stderr instead of exiting silently. Include enough information for Phase 3: compile command/stderr, server stdout/stderr, request URL/path, HTTP status/body, curl/request error, exit code, and timeout information. Never dump multi-megabyte inputs; include size, sha256, and a short preview.


### JAVASCRIPT CLIENT REQUIREMENTS

1. Determine the script path exactly as:
```python
script = "instrumented_code.js" if os.path.exists("instrumented_code.js") else "candidate_code.js"
```
Never use directory walking or globbing.

3. Support these candidate styles:
   - Script-style Node program reading stdin or `input.dat`.
   - `module.exports = function`, `module.exports = {{ name: function }}`, or named exports.
   - Plain top-level function declarations with no `module.exports`.

3. For function/library-style candidates, create a temporary Node driver that:
   - reads the current `test_case.json` and `input.dat`,
   - first tries `require("./" + script)`,
   - if no usable export exists, evaluates the source in a `vm` context and discovers top-level functions,
   - passes arguments from `test_case["input"]` flexibly: array -> spread args, object -> values/object as appropriate, string -> one arg,
   - **If the function signature takes structured objects like `(req, res, next)` or `(request, response)`**, construct mock objects from the corresponding input fields. For example:
     ```javascript
     const inp = testCase.input || {{}};
     const req = Object.assign({{ method: 'GET', headers: {{}}, query: {{}}, body: {{}} }}, inp.req || inp.request || {{}});
     const res = {{ statusCode: 200, headers: {{}}, body: '', status(c){{this.statusCode=c;return this;}}, json(d){{this.body=JSON.stringify(d);return this;}}, send(d){{this.body=String(d);return this;}}, set(){{return this;}}, end(){{}} }};
     const result = fn(req, res);
     // print res.body or return value
     console.log(res.body || JSON.stringify(result));
     ```
   - prints only the returned value or response body, stringifying objects/arrays as JSON.

4. For script-style candidates, run `node <script>` and pipe `input.dat` to stdin. The candidate may also read `input.dat` directly.

5. Do a trace pass that writes stdout/stderr/TRACE lines to `trace.txt`, then a clean pass that forwards only candidate stdout/stderr. Do not validate expected output in the harness.

6. Generate ONLY valid Python code for `harness.py`.
"""

FIX_HARNESS_JAVASCRIPT = """Fix the test harness based on the issue identified.

CURRENT SCRIPT:
```python
{harness}
```

ISSUE IDENTIFIED:
{fix_suggestion}

TEST CASE EXAMPLE:
```json
{test_case_string}
```

CANDIDATE CODE ({language}):
```javascript
{sample_code}
```
{input_files_section}
Generate a FIXED reusable Python `harness.py` that addresses the issue.
- Do not hardcode values from the example test.
- Read `test_case.json` and `input.dat` at runtime.
- Preserve support for mixed inline/file-backed inputs across later tests.
- Return only complete valid Python code.
- Keep the same overall structure
- Fix the specific problem mentioned
- Ensure proper input handling and output capture
- **CRITICAL**: Generate valid PYTHON code. Do not include bash commands like `pip install` directly in the script.

Generate ONLY the Python script `harness.py`. No explanations.
"""
