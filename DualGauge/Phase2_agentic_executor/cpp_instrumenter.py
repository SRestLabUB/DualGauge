"""
C/C++ line-based instrumenter — mirrors js_instrumenter.js.

Injects `fprintf(stderr, "TRACE:%d\\n", <lineno>);` as the first statement
inside every function/method body.  Only injects inside function bodies —
NOT at class/struct/namespace/enum scope — to avoid "statement at class scope"
compile errors.

The heuristic: a `{` opens a function body if the same line (or the
immediately preceding non-blank line) contains a `(...)` parameter list.
Brace depth tracking is used so inner blocks (if/for/while) inside a function
also get injected.

Output file is `instrumented_code.{c,cpp}` and is used for the trace pass only.
The clean pass always compiles and runs the original `candidate_code.*`.

Usage:
    python cpp_instrumenter.py candidate_code.cpp instrumented_code.cpp
    python cpp_instrumenter.py candidate_code.c   instrumented_code.c
"""

import re
import sys


_BLOCK_OPEN_RE = re.compile(r"\{[\s]*(//.*)?$")
_BLOCK_CLOSE_RE = re.compile(r"^\s*\}[;,]?\s*(//.*)?$")
_PREPROCESSOR_RE = re.compile(r"^\s*#")
# A line that looks like it introduces a function/method (has a paren group before {)
_FUNC_OPEN_RE = re.compile(r"\)\s*(const|override|noexcept|final|->.*?)?\s*\{[\s]*(//.*)?$")
# A line that opens an initializer list: = {  or  array[N] = {
# (constructor member-init  `: member{` is intentionally excluded — too ambiguous)
_INITIALIZER_OPEN_RE = re.compile(r"((?<!=)=\s*\{|\[\d*\]\s*=\s*\{)[\s]*(//.*)?$")


def _is_non_executable_open(line: str, prev_lines: list) -> bool:
    """Return True if this { should NOT be injected into (class/struct/namespace/initializer)."""
    stripped = line.strip()
    # Initializer list:  = {   or   arr[N] = {   or   : member{
    if _INITIALIZER_OPEN_RE.search(stripped):
        return True
    # If same line has a paren group before {, it's a function — inject
    if _FUNC_OPEN_RE.search(stripped):
        return False
    # If same line starts with class/struct/namespace/enum/union/extern
    if re.match(r"^\s*(class|struct|namespace|enum|union|extern)\b", line):
        return True
    # Look back at previous non-blank, non-comment lines
    for prev in reversed(prev_lines[-5:]):
        p = prev.strip()
        if not p or p.startswith("//") or p.startswith("*") or p.startswith("/*"):
            continue
        # class/struct/namespace/enum on a prior line
        if re.match(r"^\s*(class|struct|namespace|enum|union)\b", prev):
            return True
        # Initializer: prior line ends with = or has array/member init pattern
        if re.search(r"=\s*$", p) or re.search(r"\[\d*\]\s*=\s*$", p):
            return True
        # Prior line ends with ) → function signature → inject
        if re.search(r"\)\s*(const|override|noexcept|final|->.*?)?\s*$", p):
            return False
        break
    return False


def instrument(source: str) -> str:
    lines = source.splitlines(keepends=True)
    out = []

    # Prepend stdio include if not present
    has_stdio = any(
        re.search(r'#include\s*[<"]stdio\.h[">]', l) or
        re.search(r'#include\s*[<"]cstdio[">]', l)
        for l in lines
    )
    if not has_stdio:
        out.append('#include <cstdio>\n')

    # Stack of booleans: True = this brace level is inside a function body
    func_depth_stack: list[bool] = []

    for i, line in enumerate(lines, start=1):
        out.append(line)
        stripped = line.rstrip("\n\r")

        if _PREPROCESSOR_RE.match(stripped):
            continue

        opens = stripped.count("{") - stripped.count("}")

        if opens > 0 and _BLOCK_OPEN_RE.search(stripped):
            non_exec = _is_non_executable_open(stripped, [l.rstrip("\n\r") for l in out[:-1]])
            is_func_open = bool(_FUNC_OPEN_RE.search(stripped))

            if non_exec:
                # Class/struct/namespace/initializer — never inject here
                func_depth_stack.append(False)
            elif is_func_open:
                # Explicit function/method open — always inject
                func_depth_stack.append(True)
                indent = len(stripped) - len(stripped.lstrip())
                pad = " " * (indent + 4)
                out.append(f'{pad}fprintf(stderr, "TRACE:{i}\\n");\n')
            else:
                # Control-flow block (if/for/while/else) — inherit parent context
                inside_function = bool(func_depth_stack) and func_depth_stack[-1]
                func_depth_stack.append(inside_function)
                if inside_function:
                    indent = len(stripped) - len(stripped.lstrip())
                    pad = " " * (indent + 4)
                    out.append(f'{pad}fprintf(stderr, "TRACE:{i}\\n");\n')

        elif opens < 0:
            # Closing brace(s)
            for _ in range(abs(opens)):
                if func_depth_stack:
                    func_depth_stack.pop()

    return "".join(out)


def main():
    if len(sys.argv) != 3:
        print("Usage: python cpp_instrumenter.py <input> <output>", file=sys.stderr)
        sys.exit(1)

    input_file, output_file = sys.argv[1], sys.argv[2]
    try:
        source = open(input_file, "r", encoding="utf-8").read()
    except Exception as e:
        print(f"Instrumentation failed: cannot read {input_file}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = instrument(source)
    except Exception as e:
        print(f"Instrumentation failed: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        open(output_file, "w", encoding="utf-8").write(result)
        print(f"Instrumentation successful: {output_file}")
    except Exception as e:
        print(f"Instrumentation failed: cannot write {output_file}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
