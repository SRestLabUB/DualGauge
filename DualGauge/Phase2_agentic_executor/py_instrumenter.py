"""
Python AST instrumenter — mirrors js_instrumenter.js.

Injects `print("TRACE:<lineno>", file=__import__('sys').stderr)` before every
statement in every function/class/module body.  The output file is
`instrumented_code.py` and is used for the trace pass only; the clean pass
always runs the original `candidate_code.py`.

Usage:
    python py_instrumenter.py candidate_code.py instrumented_code.py
"""

import ast
import sys


def _trace_stmt(lineno: int) -> ast.stmt:
    """Return an AST node for: print("TRACE:<n>", file=sys.stderr)"""
    node = ast.Expr(
        value=ast.Call(
            func=ast.Name(id="print", ctx=ast.Load()),
            args=[ast.Constant(value=f"TRACE:{lineno}")],
            keywords=[
                ast.keyword(
                    arg="file",
                    value=ast.Attribute(
                        value=ast.Name(id="sys", ctx=ast.Load()),
                        attr="stderr",
                        ctx=ast.Load(),
                    ),
                )
            ],
        )
    )
    ast.copy_location(node, ast.parse(f"x={lineno}").body[0])
    node.lineno = lineno
    node.col_offset = 0
    node.end_lineno = lineno
    node.end_col_offset = 0
    return node


class _TraceInjector(ast.NodeTransformer):
    def _inject(self, body: list) -> list:
        new_body = []
        for stmt in body:
            lineno = getattr(stmt, "lineno", None)
            if lineno is not None:
                new_body.append(_trace_stmt(lineno))
            new_body.append(stmt)
        return new_body

    def visit_Module(self, node):
        self.generic_visit(node)
        node.body = self._inject(node.body)
        return node

    def visit_FunctionDef(self, node):
        self.generic_visit(node)
        node.body = self._inject(node.body)
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.generic_visit(node)
        node.body = self._inject(node.body)
        return node

    def visit_For(self, node):
        self.generic_visit(node)
        node.body = self._inject(node.body)
        node.orelse = self._inject(node.orelse) if node.orelse else node.orelse
        return node

    visit_AsyncFor = visit_For

    def visit_While(self, node):
        self.generic_visit(node)
        node.body = self._inject(node.body)
        node.orelse = self._inject(node.orelse) if node.orelse else node.orelse
        return node

    def visit_If(self, node):
        self.generic_visit(node)
        node.body = self._inject(node.body)
        node.orelse = self._inject(node.orelse) if node.orelse else node.orelse
        return node

    def visit_With(self, node):
        self.generic_visit(node)
        node.body = self._inject(node.body)
        return node

    visit_AsyncWith = visit_With

    def visit_Try(self, node):
        self.generic_visit(node)
        node.body = self._inject(node.body)
        node.orelse = self._inject(node.orelse) if node.orelse else node.orelse
        node.finalbody = self._inject(node.finalbody) if node.finalbody else node.finalbody
        for handler in node.handlers:
            handler.body = self._inject(handler.body)
        return node


def instrument(source: str) -> str:
    tree = ast.parse(source)
    # Prepend `import sys` if not already present
    has_sys = any(
        (isinstance(n, ast.Import) and any(a.name == "sys" for a in n.names))
        or (isinstance(n, ast.ImportFrom) and n.module == "sys")
        for n in ast.walk(tree)
    )
    injector = _TraceInjector()
    new_tree = injector.visit(tree)
    ast.fix_missing_locations(new_tree)

    instrumented = ast.unparse(new_tree)
    if not has_sys:
        instrumented = "import sys\n" + instrumented
    return instrumented


def main():
    if len(sys.argv) != 3:
        print("Usage: python py_instrumenter.py <input.py> <output.py>", file=sys.stderr)
        sys.exit(1)

    input_file, output_file = sys.argv[1], sys.argv[2]
    try:
        source = open(input_file, "r", encoding="utf-8").read()
    except Exception as e:
        print(f"Instrumentation failed: cannot read {input_file}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        result = instrument(source)
    except SyntaxError as e:
        print(f"Instrumentation failed: syntax error in {input_file}: {e}", file=sys.stderr)
        sys.exit(1)
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
