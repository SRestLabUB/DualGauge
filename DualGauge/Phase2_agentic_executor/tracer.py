import re


def parse_trace_output(raw_output, target_filename, language):
    """Parse trace output based on language.

    All languages now emit TRACE:<lineno> to stderr via static instrumentation,
    so py, c, cpp reuse the same JS TRACE: parser.
    """
    if language in ("py", "c", "cpp"):
        parsed = compress_trace(_parse_js_trace(raw_output))
        if parsed:
            return parsed
        # Fallback: any non-empty stderr counts as evidence
        stripped = (raw_output or "").strip()
        return stripped[:8000] if stripped else ""
    elif language == "js":
        parsed = compress_trace(_parse_js_trace(raw_output))
        if parsed:
            return parsed
        # Server mode: plain stdout/stderr — no TRACE: markers but content is evidence
        stripped = (raw_output or "").strip()
        return stripped[:8000] if stripped else ""
    else:
        raise NotImplementedError(f"{language} tracing not implemented")


def _parse_js_trace(trace_content):
    """Parse JS trace output.

    Handles instrumented format: TRACE:<lineno>
    For plain stdout/stderr captures (server mode), returns the raw content
    as a non-empty marker so trace_collected registers as True.
    """
    trace_lines = []
    pattern = re.compile(r'TRACE:(\d+)')

    for line in trace_content.splitlines():
        match = pattern.search(line)
        if match:
            trace_lines.append(int(match.group(1)))

    return trace_lines


def _parse_python_trace(trace_content, target_filename):
    """Parse Python trace.txt, extracting only lines from target_filename.

    Handles three formats produced by different harness implementations:

    1. tracer_wrapper sys.settrace (our preferred format):
         /workspace/candidate_code.py(42): func_name

    2. python -m trace --trace:
         candidate_code.py(42): func_name

    3. LLM-generated sys.settrace (alternative format):
         candidate_code.py:42 call func_name
         /workspace/candidate_code.py:42 line func_name
    """
    trace_lines = []
    base = re.escape(target_filename)
    # Format 1 & 2: path(lineno):
    pattern_paren = re.compile(rf'(?:^|[\\/]){base}\((\d+)\):')
    # Format 3: path:lineno event
    pattern_colon = re.compile(rf'(?:^|[\\/]){base}:(\d+)\s+(?:call|line|return)')

    for line in trace_content.splitlines():
        m = pattern_paren.search(line) or pattern_colon.search(line)
        if m:
            trace_lines.append(int(m.group(1)))

    return trace_lines

def parse_coverage_output(raw_output, target_filename, language):
    """Parse trace output based on language."""
    if language in ["c", "cpp"]:
        return _parse_c_cpp_coverage(raw_output)
    elif language == 'py' :
        return NotImplementedError(f"{language} tracing not implemented")
    else:
        raise NotImplementedError(f"{language} tracing not implemented")

def _parse_c_cpp_coverage(gcov_content):
    """
    Parse gcov output for C/C++ files and return only executed lines
    as an object: { line_number: execution_count }.
    Lines never executed (##### or -) are excluded.
    """
    executed = {}

    for line in (gcov_content or "").splitlines():
        # Example gcov lines:
        # "       12:  27:call();"
        # "    #####:  14:if (x) {"
        # "        -:   1:/* comment */"
        match = re.match(r'^\s*(\d+):\s*(\d+):', line)
        if match:
            exec_count_str, line_number_str = match.groups()
            try:
                exec_count = int(exec_count_str)
                line_number = int(line_number_str)
                if exec_count > 0:
                    executed[line_number] = exec_count
            except ValueError:
                # Ignore lines with invalid numeric data
                continue

    return executed

def compress_trace(trace_lines):
    """Remove consecutive duplicates from trace."""
    if not trace_lines:
        return ""
    
    compressed = []
    for line in trace_lines:
        if not compressed or compressed[-1] != line:
            compressed.append(line)
    
    return "->".join(str(line) for line in compressed)