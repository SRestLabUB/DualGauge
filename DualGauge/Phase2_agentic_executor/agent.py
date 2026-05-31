import os
import json
import shutil
import subprocess
import copy
import hashlib
import re
import signal
from utils import write_file, extract_script, extract_structured_result, detect_language, format_test_result, log_to_file
from tracer import parse_trace_output, parse_coverage_output
from docker_manager import DockerManager
from service_manager import AuxiliaryServiceManager, write_service_context
from prompts import INFER_SETUP_PROMPT, CLASSIFY_ERROR_TYPE_PROMPT, PYTHON_SERVER_PROMPT, PYTHON_CLIENT_PROMPT, C_CPP_CLIENT_PROMPT, C_CPP_SERVER_PROMPT, GENERATE_FIX_SCRIPT, VALIDATE_OUTPUT_PROMPT, FIX_HARNESS_PYTHON, FIX_HARNESS_C_CPP, RETRY_FIX_SCRIPT, JAVASCRIPT_SERVER_PROMPT, JAVASCRIPT_CLIENT_PROMPT, FIX_HARNESS_JAVASCRIPT, _BRACE_SAFETY_NOTE

# Global execution timeout (5 minutes)
TIMEOUT_SECONDS = 300


def _workspace_safe_path(workspace_dir, path_str):
    """Resolve a runtime file path inside the workspace."""
    rel = str(path_str).replace("\\", "/").lstrip("/")
    candidate = os.path.normpath(os.path.join(workspace_dir, rel))
    workspace_abs = os.path.abspath(workspace_dir)
    candidate_abs = os.path.abspath(candidate)
    if not (candidate_abs == workspace_abs or candidate_abs.startswith(workspace_abs + os.sep)):
        # Clamp traversal attempts back into the workspace.
        candidate_abs = os.path.join(workspace_abs, os.path.basename(rel))
    return candidate_abs


def resolve_effective_input(test_case, workspace_dir, log_file):
    """
    Resolve the effective input for a test case.

    Rules:
    - If `input` exists, use it.
    - If `input_from_file` exists, load benchmark-owned file contents:
      - parse as JSON only when the payload is clearly an object or array
      - otherwise treat file content as raw scalar text
    """
    if isinstance(test_case, dict) and "input" in test_case:
        return test_case["input"]

    if not isinstance(test_case, dict):
        return ""

    input_from_file = test_case.get("input_file_path") or test_case.get("input_from_file")
    if not input_from_file:
        return ""

    file_path = _workspace_safe_path(workspace_dir, input_from_file)
    if not os.path.exists(file_path):
        log_to_file(log_file, "WARN", f"input_from_file target missing: {input_from_file}")
        return ""

    with open(file_path, "r", encoding="utf-8") as f:
        raw = f.read()

    stripped = raw.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            return json.loads(raw)
        except Exception as e:
            log_to_file(log_file, "WARN", f"Failed to parse JSON input_from_file {input_from_file}: {e}; using raw text")

    return raw


def materialize_test_files(test_case, workspace_dir, log_file):
    """
    Materialize runtime files described inside test inputs.

    Supports:
    - input.file_path + input.file_content/file_contents
    - input.<prefix>_file_path + input.<prefix>_file_content/file_contents

    Returns a list of restoration actions for cleanup.
    """
    if not isinstance(test_case, dict):
        return []

    input_obj = test_case.get("input")
    if not isinstance(input_obj, dict):
        return []

    restoration_actions = []
    path_specs = []

    for key, value in input_obj.items():
        if not isinstance(value, str):
            continue
        if key == "file_path":
            candidate_content_keys = ["file_content", "file_contents"]
        elif key.endswith("_file_path"):
            prefix = key[:-10]
            candidate_content_keys = [
                f"{prefix}_file_content",
                f"{prefix}_file_contents",
            ]
        else:
            continue

        content_key = next((k for k in candidate_content_keys if k in input_obj), None)
        path_specs.append((value, content_key))

    for file_path_str, content_key in path_specs:
        runtime_path = _workspace_safe_path(workspace_dir, file_path_str)
        parent = os.path.dirname(runtime_path)
        if parent:
            os.makedirs(parent, exist_ok=True)

        action = {"path": runtime_path, "existed": os.path.exists(runtime_path), "original": None}
        if action["existed"]:
            try:
                with open(runtime_path, "rb") as f:
                    action["original"] = f.read()
            except Exception:
                action["original"] = None

        if content_key is not None:
            content = input_obj.get(content_key, "")
            if not isinstance(content, (str, bytes, bytearray)):
                content = json.dumps(content)
            write_file(runtime_path, content)
            log_to_file(log_file, "INFO", f"Materialized runtime file for test: {runtime_path}")
        else:
            # Treat missing content as an explicit file-absence setup for this path.
            if os.path.exists(runtime_path):
                os.remove(runtime_path)
                log_to_file(log_file, "INFO", f"Removed runtime file for absence case: {runtime_path}")

        restoration_actions.append(action)

    return restoration_actions


def cleanup_materialized_test_files(restoration_actions, log_file):
    """Restore or remove files created specifically for a single test case."""
    for action in restoration_actions or []:
        path = action["path"]
        existed = action["existed"]
        original = action["original"]
        try:
            if existed:
                if original is not None:
                    write_file(path, original)
                elif not os.path.exists(path):
                    # Best effort restore as empty if the original bytes were unreadable.
                    write_file(path, "")
            else:
                if os.path.exists(path):
                    os.remove(path)
            log_to_file(log_file, "INFO", f"Restored per-test runtime file state: {path}")
        except Exception as e:
            log_to_file(log_file, "WARN", f"Failed to restore materialized file {path}: {e}")



def select_first_functional_test(test_cases):
    """Choose the first test with usable input or expected-behavior fields.

    The selected test is only a schema example for harness generation. The harness
    must still read test_case.json/input.dat at runtime for every test.
    """
    if not test_cases:
        return {}, 0

    input_keys = {"input", "input_file_path", "input_from_file"}
    expected_keys = {
        "expected_behavior/output",
        "expected_output",
        "expected",
        "output",
        "expected_behavior",
    }

    for idx, test in enumerate(test_cases):
        if not isinstance(test, dict):
            continue
        if any(k in test for k in input_keys) or any(k in test for k in expected_keys):
            return test, idx

    return test_cases[0], 0


def _stringify_effective_input(value):
    """Convert normalized input to text for input.dat/stdin."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)


def _input_source(test_case):
    if not isinstance(test_case, dict):
        return "raw_test_case"
    if "input" in test_case:
        return "inline_input"
    if "input_file_path" in test_case:
        return "input_file_path"
    if "input_from_file" in test_case:
        return "input_from_file"
    return "no_input"


def _truncate_text(value, limit=12000):
    if value is None:
        return ""
    if not isinstance(value, str):
        try:
            value = json.dumps(value, ensure_ascii=False)
        except Exception:
            value = str(value)
    if len(value) <= limit:
        return value
    digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()
    head = value[: limit // 2]
    tail = value[-limit // 2 :]
    return f"{head}\n...[truncated {len(value)} chars sha256={digest}]...\n{tail}"


def _preview_value(value, limit=1000):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)
    digest = hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()
    return {
        "size_bytes": len(text.encode("utf-8", errors="replace")),
        "sha256": digest,
        "preview": text[:limit],
        "truncated": len(text) > limit,
    }


def _extract_structured_result_robust(response):
    """Parse JSON responses even if fenced, preceded by RESULT:, or mixed with prose."""
    result = extract_structured_result(response)
    if result:
        return result
    if not response:
        return None
    candidates = []
    candidates.extend(re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", response, flags=re.DOTALL))
    m = re.search(r"RESULT:\s*(\{.*\})", response, flags=re.DOTALL)
    if m:
        candidates.append(m.group(1))
    if "{" in response and "}" in response:
        candidates.append(response[response.find("{"): response.rfind("}") + 1])
    for cand in reversed(candidates):
        try:
            return json.loads(cand)
        except Exception:
            continue
    return None


def _deterministic_error_category(error_message, harness_path=None):
    """Classify obvious executor/harness errors before asking an LLM."""
    msg = error_message or ""
    lower = msg.lower()
    if "command exceeded" in lower or "possible ddos" in lower or "timed out" in lower or "timeout" in lower:
        return "timeout"
    if "syntaxerror" in lower and ("harness.py" in lower or (harness_path and harness_path in msg)):
        return "script"
    if "traceback" in lower and "harness.py" in lower:
        return "script"
    if "unexpected '{' in field name" in lower or "f-string: invalid syntax" in lower or "unmatched '}'" in lower:
        return "script"
    if "modulenotfounderror" in lower or "cannot find module" in lower:
        return "environment"
    if ("fatal error:" in lower and ".h:" in lower) or ("no such file or directory" in lower and ".h" in lower):
        return "environment"
    if "undefined reference" in lower:
        return "compilation"
    if "error:" in lower and ("gcc" in lower or "g++" in lower or ".c:" in lower or ".cpp:" in lower):
        return "compilation"
    if "connection refused" in lower or "server not ready" in lower or "failed to connect" in lower:
        return "service"
    return None


def _sanitize_harness_braces(harness_code):
    """Fallback sanitizer: fix common brace-escaping bugs in generated harnesses.

    The LLM sometimes writes f-strings or .format() calls on strings containing
    raw JS/C++ braces, producing ValueError or SyntaxError at runtime.

    Strategy: scan for the pattern  `"...{...".format(` or `f"...{..."`  where
    the string contains { or } that are NOT Python format placeholders (i.e. they
    look like JS/C++ code). Replace the string construction with a safe equivalent
    using string concatenation or sentinel replacement.

    This is intentionally conservative — it only patches lines where the problem
    is unambiguous, to avoid corrupting valid Python format strings.
    """
    import re as _re

    lines = harness_code.splitlines(keepends=True)
    fixed_lines = []
    changed = False

    for line in lines:
        new_line = line

        # Pattern 1: f"..." where the string contains unbalanced {{ or }} from JS
        # Symptom: f-string with doubled braces that don't match any placeholder
        # e.g.  f"function f() {{ return x; }}"
        # Fix: convert to plain string + replace doubled braces with single
        fstring_match = _re.search(r'\bf"([^"]*\{\{[^"]*)"', new_line)
        if fstring_match and '{' not in _re.sub(r'\{\{|\}\}', '', fstring_match.group(1)):
            # The string has {{ }} but no real {placeholder} — safe to de-fstring
            inner = fstring_match.group(1).replace('{{', '{').replace('}}', '}')
            new_line = new_line[:fstring_match.start()] + repr(inner) + new_line[fstring_match.end():]
            changed = True

        # Pattern 2: "...".format(...) where string contains JS-style { }
        # e.g.  "if (x) { return y; }".format(x=val)
        format_match = _re.search(r'"([^"]*\{[^"]*)"\.format\(', new_line)
        if format_match:
            inner = format_match.group(1)
            # Check if braces look like JS (no word chars directly after {)
            placeholders = _re.findall(r'\{(\w*)\}', inner)
            js_braces = _re.findall(r'\{[^}\w]', inner)  # { followed by non-word — JS style
            if js_braces and not placeholders:
                # No real placeholders, all braces are JS — remove .format()
                new_line = new_line.replace(format_match.group(0), repr(inner) + '  # sanitized')
                changed = True

        fixed_lines.append(new_line)

    if changed:
        import logging
        logging.getLogger(__name__).warning("_sanitize_harness_braces: applied brace-escaping fixes to generated harness")

    return "".join(fixed_lines), changed


def _check_harness_syntax(workdir):
    """Return (ok, message) after py_compile of harness.py."""
    proc = subprocess.run(
        ["python", "-m", "py_compile", "harness.py"],
        cwd=workdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    msg = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0, msg.strip()


def _run_local_harness(workdir, timeout):
    """Run harness.py locally and kill its process group on timeout."""
    proc = subprocess.Popen(
        ["python", "harness.py"],
        cwd=workdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        start_new_session=True,
    )
    try:
        out, err = proc.communicate(timeout=timeout)
        return {
            "stdout": (out or b"").decode(errors="replace"),
            "stderr": (err or b"").decode(errors="replace"),
            "exit_code": proc.returncode,
        }
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except Exception:
            proc.kill()
        out, err = proc.communicate()
        return {
            "stdout": (out or b"").decode(errors="replace"),
            "stderr": ((err or b"").decode(errors="replace") + f"\nCommand exceeded {timeout}s and was terminated.").strip(),
            "exit_code": 124,
        }


def _output_channels(parsed):
    channels = []
    for key in ["printed_output", "return_value", "file_output", "http_response", "exception", "stderr", "compile_error", "runtime_error"]:
        val = parsed.get(key)
        if val not in (None, "", [], {}):
            channels.append(key)
    if parsed.get("timeout"):
        channels.append("timeout")
    if parsed.get("exit_code") is not None:
        channels.append("exit_code")
    if parsed.get("trace"):
        channels.append("trace")
    if parsed.get("coverage"):
        channels.append("coverage")
    return sorted(set(channels))


def _classify_execution_status(parsed, result_meta=None):
    result_meta = result_meta or {}
    exit_code = parsed.get("exit_code", 1)
    exception = parsed.get("exception") or ""
    printed = parsed.get("printed_output") or ""
    http_response = parsed.get("http_response") or ""
    stderr = parsed.get("stderr") or exception
    all_text = "\n".join(str(x) for x in [exception, printed, http_response, stderr] if x)
    lower = all_text.lower()

    if exit_code == 124 or result_meta.get("timeout"):
        return "candidate_timeout", "candidate"
    if exit_code == 137:
        return "candidate_oom", "candidate"
    if result_meta.get("harness_error"):
        return "harness_error", "executor"
    if result_meta.get("validator_parse_error"):
        return "validator_parse_error", "executor"
    if "harness.py" in lower and ("syntaxerror" in lower or "traceback" in lower):
        return "harness_error", "executor"
    if "unexpected '{' in field name" in lower or "f-string: invalid syntax" in lower or "unmatched '}'" in lower:
        return "harness_error", "executor"
    if "modulenotfounderror" in lower or "cannot find module" in lower or ("fatal error:" in lower and ".h:" in lower):
        return "environment_error", "environment"
    if "undefined reference" in lower or ("error:" in lower and ("gcc" in lower or "g++" in lower or ".c:" in lower or ".cpp:" in lower)):
        return "candidate_compile_error", "candidate"
    if "connection refused" in lower or "failed to connect" in lower or "server not ready" in lower:
        return "candidate_server_error", "candidate"
    if exit_code == 0:
        return "executed", None
    if exit_code not in (0, None):
        return "candidate_runtime_error", "candidate"
    return "unknown_execution_status", "unknown"


def build_phase2_test_result(test, execution_result, language=None, duration_ms=None):
    """Format Phase 2 result as execution/evidence, not pass/fail."""
    exit_code = execution_result.get("exit_code", 1)
    status, origin = _classify_execution_status(execution_result, execution_result.get("_phase2_meta") or {})
    channels = _output_channels(execution_result)
    # exit_code alone is not sufficient evidence — require at least one substantive channel
    substantive_channels = set(channels) - {"exit_code"}
    evidence_collected = bool(substantive_channels) and origin != "executor"
    if status in {"harness_error", "harness_generation_error", "harness_validation_error", "environment_error", "input_resolution_error", "docker_error"}:
        evidence_collected = False
    executed = evidence_collected or status.startswith("candidate_") or status == "executed"

    trace_collected = bool(execution_result.get("trace"))
    coverage_collected = bool(execution_result.get("coverage"))
    # full_evidence requires trace for all languages (gcov replaced by instrumentation)
    full_evidence_collected = evidence_collected and trace_collected

    input_source = _input_source(test)
    normalized_input = test.get("input") if isinstance(test, dict) else None
    test_case = {
        "input": normalized_input,
        "category": test.get("category", "unknown") if isinstance(test, dict) else "unknown",
        "expected_behavior": test.get("expected_behavior", test.get("expected_behavior/output", "")) if isinstance(test, dict) else "",
        "expected_output": test.get("expected_output") if isinstance(test, dict) else None,
        "cwe": test.get("CWE", "") if isinstance(test, dict) else "",
    }
    if isinstance(test, dict):
        for key in ["input_file_path", "input_from_file"]:
            if test.get(key):
                test_case[key] = test[key]
        if normalized_input not in (None, ""):
            test_case["input_preview"] = _preview_value(normalized_input, limit=500)

    observed = {
        "return_value": execution_result.get("return_value"),
        "exception": _truncate_text(execution_result.get("exception") or "", 4000),
        "printed_output": _truncate_text(execution_result.get("printed_output") or "", 4000),
        "stderr": _truncate_text(execution_result.get("stderr") or "", 4000),
        "file_output": _truncate_text(execution_result.get("file_output") or "", 8000),
        "trace": _truncate_text(execution_result.get("trace") or "", 4000),
        "coverage": execution_result.get("coverage", ""),
        "http_response": _truncate_text(execution_result.get("http_response") or "", 12000),
        "exit_code": exit_code,
        "timeout": bool(execution_result.get("timeout") or exit_code == 124),
        "timeout_seconds": execution_result.get("timeout_seconds"),
    }

    return {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "test_case": test_case,
        "observed": observed,
        "phase2": {
            "executed": executed,
            "evidence_collected": evidence_collected,
            "full_evidence_collected": full_evidence_collected,
            "execution_status": status,
            "failure_origin": origin,
            "input_source": input_source,
            "invocation_path": execution_result.get("invocation_path", "unknown"),
            "output_channels": channels,
            "trace_collected": trace_collected,
            "coverage_collected": coverage_collected,
            "harness_repaired": bool(execution_result.get("harness_repaired")),
            "duration_ms": duration_ms,
        },
        "executed": executed,
        "evidence_collected": evidence_collected,
        "full_evidence_collected": full_evidence_collected,
        "exit_code": exit_code,
        "language": language or "",
    }


def normalize_test_case_for_runtime(test_case, workspace_dir, log_file):
    """Return (normalized_test_case, effective_input_text).

    Every test is normalized independently. Inline `input` wins. Otherwise,
    file-backed inputs are resolved into `input` while preserving the original
    `input_file_path` / `input_from_file` fields for candidates that need a path.
    """
    normalized = copy.deepcopy(test_case) if isinstance(test_case, dict) else test_case
    effective_input = resolve_effective_input(test_case, workspace_dir, log_file)

    if isinstance(normalized, dict):
        normalized["input"] = effective_input
    else:
        normalized = {"input": effective_input, "raw_test_case": normalized}

    return normalized, _stringify_effective_input(effective_input)


def validate_reusable_harness(harness_code, example_test, language=None, execution_mode=None):
    """Detect obvious harness contract violations before running the full suite."""
    errors = []
    if "test_case.json" not in harness_code:
        errors.append("Harness must read test_case.json at runtime.")
    if "input.dat" not in harness_code and "stdin" not in harness_code and "input=" not in harness_code:
        errors.append("Harness must use input.dat or pipe runtime input/stdin.")

    # All languages must use instrumented_code.* for the trace pass
    if language in ("py", "c", "cpp"):
        if "instrumented_code" not in harness_code:
            errors.append(
                f"Harness must run instrumented_code.{language} for the trace pass. "
                f"Use: script = 'instrumented_code.{language}' if os.path.exists('instrumented_code.{language}') else 'candidate_code.{language}'"
            )
    if language in ("py", "c", "cpp", "js"):
        if "trace.txt" not in harness_code:
            errors.append("Harness must write TRACE output to trace.txt.")
    # C/C++ client: trace binary must receive input.dat on stdin (otherwise exits immediately with no trace)
    if language in ("c", "cpp") and execution_mode == "client":
        if "input.dat" not in harness_code:
            errors.append(
                "C/C++ client harness must pipe input.dat to stdin for both trace and clean passes. "
                "Without input, the binary exits immediately and trace.txt will be empty."
            )

    # C/C++ harnesses must use C++17
    if language == "cpp" and "-std=c++17" not in harness_code:
        errors.append("-std=c++17 is required for modern C++ features like std::optional.")

    example_values = []
    if isinstance(example_test, dict):
        for key in ["input", "expected_behavior/output", "expected_output", "expected", "output"]:
            value = example_test.get(key)
            if isinstance(value, str) and len(value) >= 20:
                example_values.append(value)
            elif value is not None and not isinstance(value, (dict, list)):
                text = str(value)
                if len(text) >= 20:
                    example_values.append(text)

    for value in example_values:
        if value and value in harness_code:
            errors.append(f"Harness appears to hardcode an example-test value: {value[:80]}")
    return errors

def infer_setup(sample_code, language, llm, log_file, benchmark_metadata=None, error_context=None):
    """
    Infer execution mode and required services from code, prompt, and implementation details.
    Returns a dict with keys: execution_mode, server_type, services.
    Falls back to client/no-services on parse failure.
    """
    benchmark_metadata = benchmark_metadata or {}
    prompt_text = benchmark_metadata.get("prompt", "")
    impl_details = benchmark_metadata.get("implementation_details", "")
    input_files = benchmark_metadata.get("input_files", {})

    if input_files:
        input_files_section = "\n".join(f"  - {f}" for f in input_files.keys())
    else:
        input_files_section = "None"

    extra = ""
    if error_context:
        extra = f"\n\nNOTE: A previous setup attempt failed with this error — adjust your answer accordingly:\n{error_context}\n"

    prompt = INFER_SETUP_PROMPT.format(
        prompt=prompt_text,
        implementation_details=impl_details or "(none)",
        language=language,
        sample_code=sample_code,
        input_files_section=input_files_section,
    ) + extra

    response = llm.generate(prompt)
    log_to_file(log_file, "LLM", "", {"type": "prompt", "call": "infer_setup", "content": prompt})
    log_to_file(log_file, "LLM", "", {"type": "response", "call": "infer_setup", "content": response})

    result = _extract_structured_result_robust(response)
    if not result:
        log_to_file(log_file, "WARN", "infer_setup: could not parse structured result, defaulting to client/no-services")
        return {"execution_mode": "client", "server_type": None, "services": []}

    result.setdefault("execution_mode", "client")
    result.setdefault("server_type", None)
    result.setdefault("services", [])
    return result


def revise_setup(sample_code, language, llm, log_file, benchmark_metadata, previous_setup, error_message):
    """Re-infer setup after a service error, passing error context to the LLM."""
    log_to_file(log_file, "WARN", f"revise_setup triggered by service error: {error_message[:200]}")
    return infer_setup(
        sample_code=sample_code,
        language=language,
        llm=llm,
        log_file=log_file,
        benchmark_metadata=benchmark_metadata,
        error_context=error_message,
    )


def generate_harness(execution_mode, sample_code, example_test, language, llm, log_file, input_files=None):
    """Stage 0: Generate execution script based on execution mode and language."""
    log_to_file(log_file, "INFO", f"Generating execution script for {language} ({execution_mode})...")

    if language == "py":
        harness = _generate_python_script(execution_mode, sample_code, example_test, llm, log_file, input_files)
    elif language in ["c", "cpp"]:
        harness = _generate_c_cpp_script(execution_mode, sample_code, example_test, language, llm, log_file, input_files)
    elif language == "js":
        harness = _generate_javascript_script(execution_mode, sample_code, example_test, llm, log_file, input_files)
    else:
        raise NotImplementedError(f"{language} not supported")

    # Fallback 1: deterministic brace-escaping sanitizer (catches JS/C++ brace bugs
    # before py_compile or runtime failure)
    if language in ["js", "c", "cpp"] and harness:
        harness, sanitized = _sanitize_harness_braces(harness)
        if sanitized:
            log_to_file(log_file, "WARN", "generate_harness: brace-escaping sanitizer applied fixes to harness")

    return harness


def _generate_python_script(execution_mode, sample_code, example_test, llm, log_file, input_files=None):
    """Generate Python execution script.
    
    For client code, the generated Python harness must:
    - Read the *full* test_case.json (but forward only .input to the program)
    - Decide ENTRYPOINT vs WRAPPER mode
    - Do a two-pass run (trace pass -> trace.txt, then clean pass)
    - Be silent except for the program's actual output (and wrapper sentinels if used)
    - Exit with the program's real exit code
    
    For server code, generate a wrapper-free runner that:
    - Runs candidate_code.py under trace, captures URL from logs (wait up to 60s)
    - Optionally prepares /images (symlink to /workspace/images if present; else mkdir)
    - Sends one HTTP request built from the test_case.json `.input` string
    - Prints ONLY the HTTP response body to stdout and exits with curl's exit code
    - Leaves full trace in trace.txt and no coverage
    """

    input_files_section = ""
    input_files_section = f"\n\nAVAILABLE INPUT FILES:\nNone"
    if input_files:
        file_list = "\n".join(f"  - /workspace/{filename}" for filename in input_files.keys())
        input_files_section = f"\n\nAVAILABLE INPUT FILES:\n{file_list}\nNOTE: These files are already present in the workspace directory.\n"
    if not isinstance(example_test, str):
        example_test = json.dumps(example_test, indent=2)
    # --------------------- SERVER PROMPT ---------------------
    if execution_mode == "server":
        prompt = PYTHON_SERVER_PROMPT.format(sample_code=sample_code, example_test_string=example_test, input_files_section=input_files_section)
        response = llm.generate(prompt)
        log_to_file(log_file, "LLM", "", {"type": "prompt", "call": "generate_execution_script_server_py", "content": prompt})
        log_to_file(log_file, "LLM", "", {"type": "response", "call": "generate_execution_script_server_py", "content": response})
        return extract_script(response)

    # --------------------- CLIENT PROMPT ---------------------
    elif execution_mode == "client":
        prompt = PYTHON_CLIENT_PROMPT.format(sample_code=sample_code, example_test_string=example_test, input_files_section=input_files_section)
        response = llm.generate(prompt)
        log_to_file(log_file, "LLM", "", {"type": "prompt", "call": "generate_execution_script_client_py", "content": prompt})
        log_to_file(log_file, "LLM", "", {"type": "response", "call": "generate_execution_script_client_py", "content": response})
        return extract_script(response)

    return NotImplementedError


def _generate_c_cpp_script(execution_mode, sample_code, example_test, language, llm, log_file, input_files=None):
    """Generate C/C++ execution script."""
    
    compiler = "gcc" if language == "c" else "g++"
    
    input_files_section = ""
    if input_files:
        file_list = "\n".join(f"  - /workspace/{filename}" for filename in input_files.keys())
        input_files_section = f"\n\nAVAILABLE INPUT FILES:\n{file_list}\n\nNote: These files are already present in the workspace directory.\n"
    
    language_upper_case = language.upper()
    if not isinstance(example_test, str):
        example_test = json.dumps(example_test, indent=2)

    if execution_mode == "server":
        prompt = C_CPP_SERVER_PROMPT.format(language_upper_case=language_upper_case, language=language, sample_code=sample_code, example_test_string=example_test, input_files_section=input_files_section, compiler=compiler) + _BRACE_SAFETY_NOTE
        response = llm.generate(prompt)
        log_to_file(log_file, "LLM", "", {"type": "prompt", "call": "generate_harness_server_c", "content": prompt})
        log_to_file(log_file, "LLM", "", {"type": "response", "call": "generate_harness_server_c", "content": response})
        return extract_script(response)
    elif execution_mode == "client":
        prompt = C_CPP_CLIENT_PROMPT.format(language_upper_case=language_upper_case, language=language, sample_code=sample_code, example_test_string=example_test, input_files_section=input_files_section, compiler=compiler) + _BRACE_SAFETY_NOTE
        response = llm.generate(prompt)
        log_to_file(log_file, "LLM", "", {"type": "prompt", "call": "generate_harness_client_c", "content": prompt})
        log_to_file(log_file, "LLM", "", {"type": "response", "call": "generate_harness_client_c", "content": response})
        return extract_script(response)
    return NotImplementedError   

def _generate_javascript_script(execution_mode, sample_code, example_test, llm, log_file, input_files=None):
    """Generate JavaScript execution script (Python runner)."""
    
    input_files_section = ""
    input_files_section = f"\\n\\nAVAILABLE INPUT FILES:\\nNone"
    if input_files:
        file_list = "\\n".join(f"  - /workspace/{filename}" for filename in input_files.keys())
        input_files_section = f"\\n\\nAVAILABLE INPUT FILES:\\n{file_list}\\nNOTE: These files are already present in the workspace directory.\\n"
    if not isinstance(example_test, str):
        example_test = json.dumps(example_test, indent=2)

    if execution_mode == "server":
        prompt = JAVASCRIPT_SERVER_PROMPT.format(sample_code=sample_code, example_test_string=example_test, input_files_section=input_files_section) + _BRACE_SAFETY_NOTE
        response = llm.generate(prompt)
        log_to_file(log_file, "LLM", "", {"type": "prompt", "call": "generate_execution_script_server_js", "content": prompt})
        log_to_file(log_file, "LLM", "", {"type": "response", "call": "generate_execution_script_server_js", "content": response})
        
        script = extract_script(response)
        # Use instrumented code
        script = script.replace("candidate_code.js", "instrumented_code.js")
        return script

    elif execution_mode == "client":
        prompt = JAVASCRIPT_CLIENT_PROMPT.format(sample_code=sample_code, example_test_string=example_test, input_files_section=input_files_section) + _BRACE_SAFETY_NOTE
        response = llm.generate(prompt)
        log_to_file(log_file, "LLM", "", {"type": "prompt", "call": "generate_execution_script_client_js", "content": prompt})
        log_to_file(log_file, "LLM", "", {"type": "response", "call": "generate_execution_script_client_js", "content": response})
        
        script = extract_script(response)
        # Use instrumented code
        script = script.replace("candidate_code.js", "instrumented_code.js")
            
        return script

    return NotImplementedError

def collect_trace_and_coverage(workdir, language, source_filename, container, docker_manager, is_docker, log_file):
    """Collect trace after execution.  All languages now use trace.txt with TRACE:<n> lines."""
    trace = None
    coverage = None

    if language in ("py", "c", "cpp", "js"):
        trace_file = os.path.join(workdir, "trace.txt") if not is_docker else "/workspace/trace.txt"
        if is_docker:
            result = docker_manager.execute_in_container(container, f"cat {trace_file}", timeout=TIMEOUT_SECONDS)
            if result.get("exit_code") == 124:
                log_to_file(log_file, "ERROR", "Timeout reading trace.txt")
            trace_content = result["stdout"] if result["exit_code"] == 0 else ""
            if not trace_content.strip():
                log_to_file(log_file, "WARN", "trace.txt is empty or missing")
            else:
                log_to_file(log_file, "INFO", f"Trace content (first 100 chars): {trace_content[:100]}")
        else:
            try:
                with open(trace_file, "r") as f:
                    trace_content = f.read()
            except Exception:
                trace_content = ""

        # JS server mode: plain stdout/stderr lines count as evidence even without TRACE: markers
        if language == "js":
            parsed = parse_trace_output(trace_content, source_filename, "js")
            if parsed:
                trace = parsed
            else:
                stripped = trace_content.strip()
                trace = stripped[:8000] if stripped else ""
        else:
            trace = parse_trace_output(trace_content, source_filename, language)

        coverage = []

    else:
        log_to_file(log_file, "WARN", f"Trace collection not supported for language: {language}")
        trace = ""
        coverage = []

    return trace, coverage


def parse_execution_result(stdout, stderr, trace, coverage, exit_code, language, workdir):
    """Stage 3: Parse execution results (type-agnostic).
    
    For server mode, extracts HTTP status code and body from structured output.
    For client mode, uses the original parsing logic.
    """
    
    printed_output = stdout
    return_value = None
    exception = None
    warnings = []
    http_response = None
    file_output = ""
    
    output_dat_path = os.path.join(workdir, "output.dat")
    if os.path.exists(output_dat_path):
        try:
            with open(output_dat_path, 'r', encoding='utf-8') as f:
                file_output = f.read().strip()
            # Clean up for the next test
            os.remove(output_dat_path)
        except Exception:
            pass
    
    # Server mode: extract structured HTTP response
    if language == "py":
        if os.path.exists(os.path.join(workdir, "request_output.txt")):
            with open(os.path.join(workdir, "request_output.txt"), 'r') as f:
                http_response = f.read()
    
    elif language == "js":
        if os.path.exists(os.path.join(workdir, "request_output.txt")):
            with open(os.path.join(workdir, "request_output.txt"), 'r') as f:
                http_response = f.read()
        
        # Filter TRACE lines from stdout
        if printed_output:
            printed_output = "\n".join([line for line in printed_output.splitlines() if not line.strip().startswith("TRACE:")])
    
    elif language in ["c", "cpp"]:
        # Read request_output.txt — C/C++ harnesses write compile/server/request evidence here
        req_out_path = os.path.join(workdir, "request_output.txt")
        if os.path.exists(req_out_path):
            with open(req_out_path, 'r') as f:
                http_response = f.read()
        elif exit_code != 0 and (stdout.strip() or stderr.strip()):
            # Fallback: harness didn't write request_output.txt but there's raw output —
            # preserve it so evidence isn't lost
            http_response = json.dumps({
                "fallback_stdout": stdout.strip()[:4000],
                "fallback_stderr": stderr.strip()[:4000],
                "exit_code": exit_code,
            })

        return_value = exit_code

        clean_lines = []
        warning_patterns = [
            "-macosx_version_min",
            "-macos_version_min",
            "deployment version",
            "was built for newer",
            "-Woverriding",
            "warning",
            "runtimewarning"
        ]
        
        for line in stdout.splitlines():
            if any(pattern in line.lower() for pattern in warning_patterns):
                warnings.append(line.strip())
            else:
                clean_lines.append(line)
        
        printed_output = "\n".join(clean_lines).strip()
        
        if stderr:
            for line in stderr.splitlines():
                if any(pattern in line for pattern in warning_patterns):
                    warnings.append(line.strip())
    
    if exception is None and stderr and stderr.strip():
        stderr_lines = []
        for line in stderr.splitlines():
            if not any(pattern in line for pattern in ["warning:", "deployment version", "-macosx", "-macos"]):
                stderr_lines.append(line)
        
        stderr_clean = "\n".join(stderr_lines).strip()
        if stderr_clean:
            exception = stderr_clean
    
    meta = {
        "printed_output": _truncate_text(printed_output, 20000),
        "return_value": return_value,
        "exception": _truncate_text(exception, 12000) if exception else None,
        "stderr": _truncate_text(stderr, 12000) if stderr else "",
        # "warnings": warnings,
        "trace": _truncate_text(trace, 20000),
        "coverage": coverage,
        "exit_code": exit_code,
        "http_response": _truncate_text(http_response, 20000) if http_response else http_response,
        "file_output": _truncate_text(file_output, 20000),
        "timeout": exit_code == 124,
        "timeout_seconds": TIMEOUT_SECONDS if exit_code == 124 else None,
    }
    return meta

def classify_error_with_llm(error_message, harness, sample_code, language, llm, log_file):
    """Classify error type using deterministic checks first, then LLM."""
    deterministic = _deterministic_error_category(error_message)
    if deterministic:
        log_to_file(log_file, "INFO", f"Error deterministically classified as: {deterministic}")
        return deterministic
    valid_categories = {"environment", "compilation", "code", "script", "service", "timeout"}
    prompt = CLASSIFY_ERROR_TYPE_PROMPT.format(
        error_message=error_message,
        harness=harness,
        language=language,
        sample_code=sample_code,
    )
    response = llm.generate(prompt)
    log_to_file(log_file, "LLM", "", {"type": "prompt", "call": "classify_error", "content": prompt})
    log_to_file(log_file, "LLM", "", {"type": "response", "call": "classify_error", "content": response})

    result = _extract_structured_result_robust(response)
    if result and result.get("category") in valid_categories:
        log_to_file(log_file, "INFO", f"Error classified as: {result['category']} — {result.get('reason', '')}")
        return result["category"]

    log_to_file(log_file, "WARN", "classify_error: could not parse structured result, defaulting to script for first-test repair")
    return "script"


def generate_fix_script(error_message, llm, log_file, is_docker=False):
    """Generate environment fix script."""
    
    error_message = error_message #[-100:]
    
    if is_docker:
        context = "Docker container (running as root, no sudo)"
        pkg_install = "apt-get update && apt-get install -y <package>"
    else:
        context = "Local machine"
        pkg_install = "pip install <package> --break-system-packages (or sudo apt-get install)"
    
    prompt = GENERATE_FIX_SCRIPT.format(error_message=error_message, context=context, pkg_install=pkg_install) 
    
    response = llm.generate(prompt)
    log_to_file(log_file, "LLM", "", { "type": "prompt", "call": "generate_fix_script", "content": prompt })
    log_to_file(log_file, "LLM", "", { "type": "response", "call": "generate_fix_script", "content": response })
    
    if "```bash" not in response:
        return None
    
    return extract_script(response)

def retry_fix_script(fix_script, error_message, llm, log_file, is_docker=False):
    """Generate environment fix script."""
    
    error_message = error_message #[-100:]
    
    if is_docker:
        context = "Docker container (running as root, no sudo)"
        pkg_install = "apt-get update && apt-get install -y <package>"
    else:
        context = "Local machine"
        pkg_install = "pip install <package> --break-system-packages (or sudo apt-get install)"
    
    prompt = RETRY_FIX_SCRIPT.format(fix_script=fix_script, error_message=error_message, context=context, pkg_install=pkg_install) 
    
    response = llm.generate(prompt)
    log_to_file(log_file, "LLM", "", { "type": "prompt", "call": "retry_fix_script", "content": prompt })
    log_to_file(log_file, "LLM", "", { "type": "response", "call": "retry_fix_script", "content": response })
    
    if "```bash" not in response:
        return None
    
    return extract_script(response)


def apply_fix(fix_script, workdir, container, docker_manager, is_docker, log_file):
    """Apply environment fix."""

    log_to_file(log_file, "INFO", "Applying environment fix...")
    script_path = os.path.join(workdir, "fix_env.sh")
    with open(script_path, "w") as f:
        f.write(fix_script)
    os.chmod(script_path, 0o755)

    if is_docker:
        # Copy and run inside the container
        cmd = f"cd /workspace && bash fix_env.sh"
        result = docker_manager.execute_in_container(container, cmd, timeout=TIMEOUT_SECONDS)
        if result.get("exit_code") == 124:
            log_to_file(log_file, "ERROR", "Timeout")
        if result["exit_code"] == 0:
            log_to_file(log_file, "INFO", "Fix applied successfully")
            return  result["exit_code"], result['stdout']
        else:
            log_to_file(log_file, "WARN", f"Fix may have failed: {result['stderr']}")
            return result["exit_code"], result['stderr']
    else:
        try:
            proc = subprocess.run(
                ["bash", "-c", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=TIMEOUT_SECONDS,
                cwd=workdir
            )
            if proc.returncode == 0:
                log_to_file(log_file, "INFO", "Fix applied successfully")
            else:
                log_to_file(log_file, "WARN", f"Fix may have failed: {proc.stderr.decode()}")
            return proc.returncode, (proc.stdout.decode(errors="replace") if proc.returncode == 0 else proc.stderr.decode(errors="replace"))
        except subprocess.TimeoutExpired:
            log_to_file(log_file, "ERROR", "Timeout")
            return 1, "Timeout"
        except Exception as e:
            log_to_file(log_file, "ERROR", f"Failed to apply fix: {e}")
            return 1, str(e)


def validate_output_with_llm(test_case, harness, execution_result, sample_code, language, llm, log_file, input_files=None):
    """
    Use LLM to check if output semantically matches expected, and diagnose script issues.
    
    Returns:
        dict with:
        - "matches": bool - does output match expected semantically
        - "issue": None or string describing the problem
        - "fix_suggestion": None or string with how to fix the script
    """
    
    expected = test_case.get("expected_output", test_case.get("expected_behavior/output", ""))
    observed = execution_result.get("printed_output", "")
    exception = execution_result.get("exception")
    exit_code = execution_result.get("exit_code", 0)
    http_info = execution_result.get("http_response", "")
    file_output = execution_result.get("file_output", "")
    
    
    input_files_section = ""
    if input_files:
        file_list = "\n".join(f"  - /workspace/{filename}" for filename in input_files.keys())
        input_files_section = f"\n\nAVAILABLE INPUT FILES:\n{file_list}\n"
    if not isinstance(test_case, str):
        test_case = json.dumps(test_case, indent=2, ensure_ascii=False)
    test_case = _truncate_text(test_case, 4000)
    observed = _truncate_text(observed, 4000)
    http_info = _truncate_text(http_info, 8000)
    file_output = _truncate_text(file_output, 4000)
    exception = _truncate_text(exception, 4000)
    prompt = VALIDATE_OUTPUT_PROMPT.format(harness=harness, test_case_strings=test_case, expected=_truncate_text(expected, 4000), exit_code=exit_code, observed=observed, http_info=http_info, file_output=file_output, exception=exception, language=language, sample_code=sample_code, input_files_section=input_files_section)
    
    response = llm.generate(prompt)
    log_to_file(log_file, "LLM", "", {"type": "prompt", "call": "validate_output", "content": prompt})
    log_to_file(log_file, "LLM", "", {"type": "response", "call": "validate_output", "content": response})

    result = _extract_structured_result_robust(response)
    if result:
        matches = bool(result.get("match", False))
        issue = result.get("issue") or None
        fix_suggestion = result.get("fix") or None
        return {"matches": matches, "issue": issue, "fix_suggestion": fix_suggestion, "parse_error": False}

    log_to_file(log_file, "WARN", "validate_output: could not parse structured result; not assuming match")
    return {"matches": False, "issue": "validator_parse_error", "fix_suggestion": None, "parse_error": True}


def regenerate_harness_with_fix(harness, fix_suggestion, test_case, sample_code, language, llm, log_file, input_files=None):
    """Regenerate the reusable Python harness with specific fix applied."""
    input_files_section = ""
    if input_files:
        file_list = "\n".join(f"  - /workspace/{filename}" for filename in input_files.keys())
        input_files_section = f"\n\nAVAILABLE INPUT FILES:\n{file_list}\n"
    if not isinstance(test_case, str):
        test_case = json.dumps(test_case, indent=2)
    if language == 'py':
        prompt = FIX_HARNESS_PYTHON.format(harness=harness, fix_suggestion=fix_suggestion, test_case_string=test_case, language=language, sample_code=sample_code, input_files_section=input_files_section) 
    elif language == 'js':
        prompt = FIX_HARNESS_JAVASCRIPT.format(harness=harness, fix_suggestion=fix_suggestion, test_case_string=test_case, language=language, sample_code=sample_code, input_files_section=input_files_section)
    else:
        prompt = FIX_HARNESS_C_CPP.format(harness=harness, fix_suggestion=fix_suggestion, test_case_string=test_case, language=language, sample_code=sample_code, input_files_section=input_files_section)
    response = llm.generate(prompt)
    log_to_file(log_file, "LLM", "", { "type": "prompt", "call": "regenerate_harness_with_fix", "content": prompt })
    log_to_file(log_file, "LLM", "", { "type": "response", "call": "regenerate_harness_with_fix", "content": response })
    return extract_script(response)


def execute_single_test(test_case, harness, sample_code, language, harness_language, source_filename, workdir, container,
                       docker_manager, is_docker, llm, log_file, max_retries=3, test_index=0, input_files=None, execution_mode="client", timeout=300, allow_harness_repair=False, set_call_type=None):
    """Execute a single test.

    The reusable harness may only be repaired for the selected first functional
    validation test. Later tests run once with the frozen harness. Phase 2
    records execution evidence; it does not decide benchmark correctness.
    """
    _tag = set_call_type if callable(set_call_type) else (lambda t: None)
    materialized_actions = materialize_test_files(test_case, workdir, log_file)
    normalized_test_case, input_str = normalize_test_case_for_runtime(test_case, workdir, log_file)

    # ReDoS / file-backed tests are allowed to time out, but they must not hang
    # the whole executor. The caller-provided timeout remains the upper bound.
    file_backed = isinstance(test_case, dict) and (test_case.get("input_file_path") or test_case.get("input_from_file"))
    effective_timeout = min(timeout, 30) if file_backed else timeout

    test_json_path = os.path.join(workdir, "test_case.json")
    write_file(test_json_path, json.dumps(normalized_test_case, indent=2, ensure_ascii=False))

    input_dat_path = os.path.join(workdir, "input.dat")
    write_file(input_dat_path, input_str)

    input_meta = _preview_value(input_str, limit=500)
    log_to_file(log_file, "INFO", f"Runtime input source={_input_source(test_case)} size={input_meta['size_bytes']} sha256={input_meta['sha256']} timeout={effective_timeout}s")
    if input_meta["truncated"]:
        log_to_file(log_file, "INFO", f"Runtime input preview: {input_meta['preview']}...[truncated]")


    attempt_limit = max_retries if allow_harness_repair else 1
    harness_repaired = False
    last_result = {"stdout": "", "stderr": "No execution attempt completed", "exit_code": 1}
    result_meta = {}

    for attempt in range(attempt_limit):
        log_to_file(log_file, "INFO", f"Executing test (attempt {attempt + 1}/{attempt_limit}).")

        # Always syntax-check harness.py before the first validation attempt. This
        # catches JS/C driver template bugs before we misclassify them as code.
        if allow_harness_repair:
            ok, pyc_msg = _check_harness_syntax(workdir)
            if not ok:
                log_to_file(log_file, "ERROR", f"harness.py failed py_compile: {pyc_msg[:500]}")
                if attempt + 1 < attempt_limit:
                    new_script = regenerate_harness_with_fix(
                        harness,
                        f"harness.py is not valid Python. py_compile error:\n{pyc_msg}",
                        test_case,
                        sample_code,
                        language,
                        llm,
                        log_file,
                        input_files,
                    )
                    harness_path = os.path.join(workdir, "harness.py")
                    write_file(harness_path, new_script)
                    harness = new_script
                    harness_repaired = True
                    continue
                last_result = {"stdout": "", "stderr": pyc_msg, "exit_code": 1}
                result_meta["harness_error"] = True
                break

        if is_docker:
            result = docker_manager.execute_in_container(
                container,
                "cd /workspace && python harness.py",
                timeout=effective_timeout,
            )
        else:
            result = _run_local_harness(workdir, effective_timeout)

        last_result = result

        if result.get("exit_code") == 124:
            log_to_file(log_file, "WARN", f"Execution timed out after {effective_timeout}s; recording timeout evidence")
            result["stderr"] = (result.get("stderr") or "") + f"\nCommand exceeded {effective_timeout}s and was terminated."
            result_meta["timeout"] = True
            break

        if result.get("exit_code") == 137:
            log_to_file(log_file, "WARN", "Container OOM-killed (exit 137); recording OOM evidence")
            break

        if result.get("exit_code") == 0:
            log_to_file(log_file, "INFO", "Harness execution completed")
            if allow_harness_repair:
                trace_preliminary, coverage_preliminary = collect_trace_and_coverage(workdir, language, source_filename, container, docker_manager, is_docker, log_file)
                parsed_preliminary = parse_execution_result(
                    result.get("stdout", ""),
                    result.get("stderr", ""),
                    trace_preliminary,
                    coverage_preliminary,
                    result.get("exit_code", 1),
                    language,
                    workdir,
                )
                _tag("validate_output")
                validation = validate_output_with_llm(test_case, harness, parsed_preliminary, sample_code, language, llm, log_file, input_files)
                if validation.get("parse_error"):
                    result_meta["validator_parse_error"] = True
                    log_to_file(log_file, "WARN", "Validator parse error; not assuming correctness and not repairing without a concrete fix")
                elif validation.get("fix_suggestion"):
                    log_to_file(log_file, "INFO", f"Harness validation suggested fix: {validation['fix_suggestion']}")
                    if attempt + 1 < attempt_limit:
                        _tag("regenerate_harness_validation")
                        new_script = regenerate_harness_with_fix(harness, validation["fix_suggestion"], test_case, sample_code, language, llm, log_file, input_files)
                        harness_path = os.path.join(workdir, "harness.py")
                        write_file(harness_path, new_script)
                        harness = new_script
                        harness_repaired = True
                        log_to_file(log_file, "INFO", "Harness regenerated; retrying validation test")
                        continue
                else:
                    log_to_file(log_file, "INFO", "Harness validation did not request repair")
            break

        error_msg = result.get("stderr") or result.get("stdout") or ""
        # If harness produced no output, fall back to request_output.txt written by the harness
        if not error_msg.strip():
            req_out_path = os.path.join(workdir, "request_output.txt") if not is_docker else None
            if is_docker:
                ro = docker_manager.execute_in_container(container, "cat /workspace/request_output.txt 2>/dev/null", timeout=TIMEOUT_SECONDS)
                error_msg = ro.get("stdout", "").strip() or error_msg
            elif req_out_path and os.path.exists(req_out_path):
                try:
                    error_msg = open(req_out_path).read().strip() or error_msg
                except Exception:
                    pass
        log_to_file(log_file, "ERROR", f"Execution failed with exit code {result.get('exit_code')}: {error_msg[:500]}")

        if not allow_harness_repair:
            break

        _tag("classify_error")
        error_type = _deterministic_error_category(error_msg) or classify_error_with_llm(error_msg, harness, sample_code, language, llm, log_file)
        log_to_file(log_file, "WARN", f"{error_type} error detected")

        if error_type == "environment":
            _tag("generate_fix_script")
            fix_script = generate_fix_script(error_msg, llm, log_file, is_docker)
            if fix_script:
                for try_fix in range(3):
                    failed, stderr_or_stdout = apply_fix(fix_script, workdir, container, docker_manager, is_docker, log_file)
                    if failed:
                        _tag("retry_fix_script")
                        fix_script = retry_fix_script(fix_script, stderr_or_stdout, llm, log_file, is_docker)
                        log_to_file(log_file, "ERROR", "Failed to apply environment fix; retrying...")
                        continue
                    break
                continue
            log_to_file(log_file, "ERROR", "Environment issue was not fixable")
            break

        if error_type == "service":
            result["_service_error"] = error_msg
            break

        if error_type == "timeout":
            result["exit_code"] = 124
            result_meta["timeout"] = True
            break

        if error_type == "script":
            if attempt + 1 < attempt_limit:
                _tag("regenerate_harness_error")
                new_script = regenerate_harness_with_fix(harness, error_msg, test_case, sample_code, language, llm, log_file, input_files)
                harness_path = os.path.join(workdir, "harness.py")
                write_file(harness_path, new_script)
                harness = new_script
                harness_repaired = True
                log_to_file(log_file, "INFO", "Harness regenerated; retrying")
                continue
            result_meta["harness_error"] = True
            break

        # Compilation/code errors are candidate evidence. Do not repair candidate.
        break

    trace, coverage = collect_trace_and_coverage(workdir, language, source_filename, container, docker_manager, is_docker, log_file)
    parsed = parse_execution_result(
        last_result.get("stdout", ""),
        last_result.get("stderr", ""),
        trace,
        coverage,
        last_result.get("exit_code", 1),
        language,
        workdir,
    )
    if result_meta.get("timeout"):
        parsed["timeout"] = True
        parsed["timeout_seconds"] = effective_timeout
    if harness_repaired:
        parsed["harness_repaired"] = True
    if result_meta:
        parsed["_phase2_meta"] = result_meta

    cleanup_materialized_test_files(materialized_actions, log_file)
    return parsed


def execute_sample(sample_code, sample_filepath, fc_test_cases, sec_test_cases, input_files, llm, use_docker,
                  max_retries, log_dir, timeout=300, keep_workdir=False, progress_callback=None, workdir_base=None,
                  benchmark_metadata=None, cached_setup=None):
    """Execute all tests for a sample.

    Returns (test_results, stats) where stats is a dict with:
        llm_calls, retry_count, per_test_elapsed, setup_elapsed, runner_elapsed
    """
    import time as _time

    test_cases = fc_test_cases + sec_test_cases
    log_file = os.path.join(log_dir, "execution.log")
    log_to_file(log_file, "INFO", "="*60)
    log_to_file(log_file, "INFO", "Starting sample execution")
    log_to_file(log_file, "INFO", "="*60)

    stats = {
        "llm_calls": 0,
        "llm_calls_by_type": {},   # breakdown: infer_setup, generate_harness, validate_output, etc.
        "retry_count": 0,
        "per_test_elapsed": [],
        "setup_elapsed": 0.0,
        "runner_elapsed": 0.0,
        "last_setup": None,
        "phase2_status_counts": {},
        "failure_origin_counts": {},
        "input_source_counts": {},
        "output_channel_counts": {},
        "harness_repairs": 0,
    }

    # Wrap llm.generate to count calls by type.
    # Functions pass call_type via a closure variable set just before calling generate.
    _orig_generate = llm.generate
    _current_call_type = ["unknown"]

    def _counted_generate(prompt):
        stats["llm_calls"] += 1
        ctype = _current_call_type[0]
        stats["llm_calls_by_type"][ctype] = stats["llm_calls_by_type"].get(ctype, 0) + 1
        return _orig_generate(prompt)

    llm.generate = _counted_generate

    def _set_call_type(ctype):
        _current_call_type[0] = ctype

    language = detect_language(sample_filepath)
    # harness_language is set after infer_setup since C server needs 'py' not 'sh'
    harness_language = None
    source_filename = f"candidate_code.{language}"
    
    log_to_file(log_file, "INFO", f"Language: {language}")
    log_to_file(log_file, "INFO", f"Total tests: {len(test_cases)}")
    
    workspace_dir = os.path.join(log_dir, "workspace")
    
    # Safety check: ensure all parent directories are actually directories, not files
    parent = os.path.dirname(workspace_dir)
    if os.path.exists(parent) and not os.path.isdir(parent):
        error_msg = f"Path conflict: {parent} exists as a file, not a directory. Please remove it."
        log_to_file(log_file, "ERROR", error_msg)
        raise RuntimeError(error_msg)
    
    os.makedirs(workspace_dir, exist_ok=True)
    
    write_file(os.path.join(workspace_dir, source_filename), sample_code)
    
    for filename, content in (input_files or {}).items():
        write_file(os.path.join(workspace_dir, filename), content)

    # Copy instrumenters to workspace
    for fname in ("js_instrumenter.js", "py_instrumenter.py", "cpp_instrumenter.py"):
        src = os.path.join(os.path.dirname(__file__), fname)
        if os.path.exists(src):
            write_file(os.path.join(workspace_dir, fname), open(src, "r").read())
    
    container = None
    docker_manager_inst = None
    
    if use_docker:
        from config.constants import DEFAULT_DOCKER_IMAGE_PYTHON, DEFAULT_DOCKER_IMAGE_C
        docker_image = DEFAULT_DOCKER_IMAGE_C if language in ["c", "cpp"] else DEFAULT_DOCKER_IMAGE_PYTHON
        # Note: We use the Python image for JS as well since we installed Node.js in it
        
        
        from config.constants import OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_KEY, DEEPSEEK_KEY, GROK_KEY
        
        env_vars = {
            "OPENAI_API_KEY": OPENAI_API_KEY,
            "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
            "GEMINI_KEY": GEMINI_KEY,
            "DEEPSEEK_KEY": DEEPSEEK_KEY,
            "GROK_KEY": GROK_KEY
        }
        
        log_to_file(log_file, "INFO", f"Using Docker image: {docker_image}")
        docker_manager_inst = DockerManager(image_name=docker_image)
        container = docker_manager_inst.create_container(
            host_workdir=workspace_dir,
            container_workdir="/workspace",
            environment=env_vars
        )

    service_manager = AuxiliaryServiceManager(
        workspace_dir=workspace_dir,
        log_file=log_file,
        use_docker=use_docker,
        docker_manager=docker_manager_inst,
        container=container,
    )
    # Service setup is deferred until after infer_setup runs (below)

    # Perform JS Instrumentation if needed
    if language == "js":
        log_to_file(log_file, "INFO", "Instrumenting JavaScript code...")
        
        # Detect dependencies
        import re
        dependencies = set()
        # require('pkg') or require("pkg")
        dependencies.update(re.findall(r"require\(['\"](.*?)['\"]\)", sample_code))
        # import ... from 'pkg'
        dependencies.update(re.findall(r"from\s+['\"](.*?)['\"]", sample_code))
        
        # Filter built-ins and local files
        builtins = {"fs", "path", "http", "https", "child_process", "os", "util", "events", "stream", "buffer", "crypto", "url", "querystring", "zlib", "net", "dgram", "dns", "readline", "repl", "vm", "assert", "module", "process", "timers", "console", "constants", "string_decoder", "punycode", "tls", "tty", "cluster", "v8"}
        
        packages_to_install = []
        for dep in dependencies:
            if dep.startswith(".") or dep.startswith("/"):
                continue
            # Handle sub-paths like @anthropic-ai/sdk/client
            pkg_name = dep
            if dep.startswith("@"):
                # Scoped package: @scope/pkg
                parts = dep.split("/")
                if len(parts) >= 2:
                    pkg_name = f"{parts[0]}/{parts[1]}"
            else:
                # Normal package: pkg/subpath
                pkg_name = dep.split("/")[0]
                
            if pkg_name not in builtins:
                packages_to_install.append(pkg_name)
        
        # Only install packages not already available globally
        all_pkgs = list({"acorn", "estraverse", "escodegen"} | set(packages_to_install))
        install_cmd = "npm install " + " ".join(all_pkgs) + " --prefer-offline --silent"
        instrument_cmd = "node js_instrumenter.js candidate_code.js instrumented_code.js"
        log_to_file(log_file, "INFO", f"Installing JS dependencies: {install_cmd}")

        if use_docker:
            # Run npm install and instrumentation as separate steps so a failed
            # instrumentation doesn't prevent packages being installed.
            res = docker_manager_inst.execute_in_container(container, f"cd /workspace && {install_cmd}", timeout=300)
            if res["exit_code"] != 0:
                log_to_file(log_file, "WARN", f"npm install failed: {res['stderr']}")
            res = docker_manager_inst.execute_in_container(container, f"cd /workspace && {instrument_cmd}", timeout=60)
            if res["exit_code"] != 0:
                log_to_file(log_file, "WARN", f"Instrumentation failed (will use candidate_code.js): {res['stderr'][:200]}")
        else:
            try:
                subprocess.run(install_cmd, shell=True, cwd=workspace_dir, capture_output=True)
            except Exception as e:
                log_to_file(log_file, "WARN", f"npm install failed: {e}")
            try:
                subprocess.run(instrument_cmd, shell=True, cwd=workspace_dir, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                log_to_file(log_file, "WARN", f"Instrumentation failed (will use candidate_code.js): {e.stderr.decode()[:200]}")

    # Perform Python instrumentation
    if language == "py":
        log_to_file(log_file, "INFO", "Instrumenting Python code...")
        instrument_cmd = "python py_instrumenter.py candidate_code.py instrumented_code.py"
        if use_docker:
            res = docker_manager_inst.execute_in_container(container, f"cd /workspace && {instrument_cmd}", timeout=60)
            if res["exit_code"] != 0:
                log_to_file(log_file, "WARN", f"Python instrumentation failed (will trace without): {res['stderr'][:200]}")
            else:
                log_to_file(log_file, "INFO", res["stdout"].strip())
        else:
            try:
                subprocess.run(instrument_cmd, shell=True, cwd=workspace_dir, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                log_to_file(log_file, "WARN", f"Python instrumentation failed: {e.stderr.decode()[:200]}")

    # Perform C/C++ instrumentation
    if language in ("c", "cpp"):
        log_to_file(log_file, "INFO", "Instrumenting C/C++ code...")
        out_file = f"instrumented_code.{language}"
        instrument_cmd = f"python cpp_instrumenter.py candidate_code.{language} {out_file}"
        if use_docker:
            res = docker_manager_inst.execute_in_container(container, f"cd /workspace && {instrument_cmd}", timeout=60)
            if res["exit_code"] != 0:
                log_to_file(log_file, "WARN", f"C/C++ instrumentation failed (will trace without): {res['stderr'][:200]}")
            else:
                log_to_file(log_file, "INFO", res["stdout"].strip())
        else:
            try:
                subprocess.run(instrument_cmd, shell=True, cwd=workspace_dir, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                log_to_file(log_file, "WARN", f"C/C++ instrumentation failed: {e.stderr.decode()[:200]}")

    log_to_file(log_file, "INFO", "--- STAGE 0: Setup Inference & Script Generation ---")
    _t_setup = _time.time()
    if cached_setup:
        setup = cached_setup
        log_to_file(log_file, "INFO", "Using cached setup (skipping infer_setup LLM call)")
    else:
        _set_call_type("infer_setup")
        setup = infer_setup(sample_code, language, llm, log_file, benchmark_metadata)
        stats["last_setup"] = setup
    execution_mode = setup["execution_mode"]
    # Clean breaking change: Phase 2 always uses a reusable Python harness.
    harness_language = "py"
    log_to_file(log_file, "INFO", f"Execution mode: {execution_mode}, services: {setup.get('services', [])}, harness_language: {harness_language}")

    # Prefer explicit benchmark-declared auxiliary services over inferred services.
    explicit_services = []
    if benchmark_metadata:
        explicit_services = (benchmark_metadata.get("service_setup") or {}).get("services") or []
    services = explicit_services or setup.get("services", [])
    service_metadata = {"service_setup": {"services": services}}
    service_context = service_manager.setup(service_metadata)
    if service_context:
        write_service_context(workspace_dir, service_context)
        log_to_file(log_file, "INFO", f"Service context initialized: {json.dumps(service_context, ensure_ascii=False)}")

    example_test, validation_test_index = select_first_functional_test(test_cases)
    log_to_file(log_file, "INFO", f"Selected test index {validation_test_index} as harness schema/validation test")
    _set_call_type("generate_harness")
    harness = generate_harness(
        execution_mode, sample_code, example_test, language, llm, log_file, input_files
    )

    reusable_errors = validate_reusable_harness(harness, example_test, language=language, execution_mode=execution_mode)
    if reusable_errors:
        fix_msg = "Reusable-harness contract violations:\n" + "\n".join(f"- {e}" for e in reusable_errors)
        log_to_file(log_file, "WARN", fix_msg)
        _set_call_type("regenerate_harness_contract")
        harness = regenerate_harness_with_fix(harness, fix_msg, example_test, sample_code, language, llm, log_file, input_files)

    stats["setup_elapsed"] = round(_time.time() - _t_setup, 2)

    harness_path = os.path.join(workspace_dir, "harness.py")
    write_file(harness_path, harness)
    log_to_file(log_file, "INFO", f"Python harness generated ({len(harness)} bytes)")
    
    test_results = []
    
    for i, test_case in enumerate(test_cases):
        log_to_file(log_file, "INFO", f"--- TEST {i+1}/{len(test_cases)} ---")
        try:
            test_case_str = json.dumps(test_case, ensure_ascii=False) if not isinstance(test_case, str) else test_case
        except Exception:
            test_case_str = str(test_case)
        log_to_file(log_file, "INFO", f"Input: {_truncate_text(test_case_str, 4000)}")
        _t_test = _time.time()
        execution_result = execute_single_test(
            test_case, harness, sample_code, language, harness_language, source_filename,
            workspace_dir, container, docker_manager_inst, use_docker,
            llm, log_file, max_retries, test_index=i, input_files=input_files, execution_mode=execution_mode, timeout=timeout,
            allow_harness_repair=(i == validation_test_index), set_call_type=_set_call_type
        )

        # Handle service error: revise setup and retry this test once
        if execution_result.get("_service_error"):
            service_error_msg = execution_result["_service_error"]
            log_to_file(log_file, "WARN", "Service error detected — revising setup and retrying test")
            service_manager.teardown()
            _set_call_type("revise_setup")
            revised_setup = revise_setup(sample_code, language, llm, log_file, benchmark_metadata, setup, service_error_msg)
            setup = revised_setup
            execution_mode = revised_setup["execution_mode"]
            explicit_services = []
            if benchmark_metadata:
                explicit_services = (benchmark_metadata.get("service_setup") or {}).get("services") or []
            service_metadata = {"service_setup": {"services": explicit_services or revised_setup.get("services", [])}}
            service_context = service_manager.setup(service_metadata)
            if service_context:
                write_service_context(workspace_dir, service_context)
            # Retry the same test
            execution_result = execute_single_test(
                test_case, harness, sample_code, language, harness_language, source_filename,
                workspace_dir, container, docker_manager_inst, use_docker,
                llm, log_file, max_retries, test_index=i, input_files=input_files, execution_mode=execution_mode, timeout=timeout,
                allow_harness_repair=False, set_call_type=_set_call_type
            )

        exit_code = execution_result.get("exit_code", 1)
        test_elapsed = round(_time.time() - _t_test, 2)
        stats["per_test_elapsed"].append(test_elapsed)

        if i < len(fc_test_cases):
            test_case["category"] = "Functional Correctness"
        else:
            test_case["category"] = "Security"

        test_result = build_phase2_test_result(test_case, execution_result, language=language, duration_ms=int(test_elapsed * 1000))
        test_results.append(test_result)

        phase2 = test_result["phase2"]
        status = phase2["execution_status"]
        origin = phase2.get("failure_origin") or "none"
        input_source = phase2.get("input_source", "unknown")
        stats["phase2_status_counts"][status] = stats["phase2_status_counts"].get(status, 0) + 1
        stats["failure_origin_counts"][origin] = stats["failure_origin_counts"].get(origin, 0) + 1
        stats["input_source_counts"][input_source] = stats["input_source_counts"].get(input_source, 0) + 1
        if phase2.get("harness_repaired"):
            stats["harness_repairs"] += 1
        for channel in phase2.get("output_channels", []):
            stats["output_channel_counts"][channel] = stats["output_channel_counts"].get(channel, 0) + 1

        log_to_file(
            log_file,
            "INFO",
            f"Test {i+1}: status={status} executed={phase2['executed']} evidence={phase2['evidence_collected']} origin={origin} ({test_elapsed}s)"
        )

        # If the validation test exhausted all repair attempts and still failed with a
        # harness/environment error, abort remaining tests — they will all fail the same way.
        if i == validation_test_index and status in ("executor_error", "environment_error"):
            remaining = test_cases[i+1:]
            if remaining:
                log_to_file(log_file, "WARN",
                    f"Validation test failed after all repair attempts (status={status}); "
                    f"skipping remaining {len(remaining)} tests.")
                for j, remaining_tc in enumerate(remaining, start=i+1):
                    if j < len(fc_test_cases):
                        remaining_tc["category"] = "Functional Correctness"
                    else:
                        remaining_tc["category"] = "Security"
                    skipped_result = build_phase2_test_result(
                        remaining_tc, execution_result, language=language, duration_ms=0
                    )
                    test_results.append(skipped_result)
                    skipped_phase2 = skipped_result["phase2"]
                    skipped_status = skipped_phase2["execution_status"]
                    stats["phase2_status_counts"][skipped_status] = stats["phase2_status_counts"].get(skipped_status, 0) + 1
                    stats["failure_origin_counts"][origin] = stats["failure_origin_counts"].get(origin, 0) + 1
                    log_to_file(log_file, "INFO",
                        f"Test {j+1}: status={skipped_status} executed=False evidence=False origin={origin} (skipped — validation failed)")
            break
    
    service_manager.teardown()

    if use_docker and docker_manager_inst:
        docker_manager_inst.execute_in_container(
                container,
                f"chmod -R 777 /workspace",
                timeout=30
            )
        docker_manager_inst.cleanup_container(container)
        docker_manager_inst.close()
    
    if not keep_workdir:
        shutil.rmtree(workspace_dir)
        log_to_file(log_file, "INFO", "Workspace removed")
    else:
        log_to_file(log_file, "INFO", f"Workspace preserved at {workspace_dir}")
    
    log_to_file(log_file, "INFO", "="*60)
    log_to_file(log_file, "INFO", "Execution complete")
    log_to_file(log_file, "INFO", "="*60)

    # Restore original llm.generate
    llm.generate = _orig_generate

    return test_results, stats
