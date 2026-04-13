"""
CppToPythonBytecode.py  (enhanced)

Translates C++ parser AST dicts → Python code object via `ast` module.
Handles: functions, loops, arrays, vectors, maps, sets, method calls,
         ternary, break/continue, member access, initializer lists.
"""

import ast
import dis


# ---------------------------------------------------------------------------
# Operator mappings
# ---------------------------------------------------------------------------

BINARY_OP_MAP = {
    "PLUS":          ast.Add(),
    "MINUS":         ast.Sub(),
    "STAR":          ast.Mult(),
    "SLASH":         ast.FloorDiv(),   # integer division by default (C++ int/int)
    "PERCENT":       ast.Mod(),
    "EQUAL":         ast.Eq(),
    "NOT_EQUAL":     ast.NotEq(),
    "LESS":          ast.Lt(),
    "LESS_EQUAL":    ast.LtE(),
    "GREATER":       ast.Gt(),
    "GREATER_EQUAL": ast.GtE(),
    "AND":           ast.And(),
    "OR":            ast.Or(),
    "SHIFT_LEFT":    ast.LShift(),
    "SHIFT_RIGHT":   ast.RShift(),
    "BITWISE_AND":   ast.BitAnd(),
    "BITWISE_OR":    ast.BitOr(),
    "BITWISE_XOR":   ast.BitXor(),
}

UNARY_OP_MAP = {
    "MINUS":       ast.USub(),
    "PLUS":        ast.UAdd(),
    "LOGICAL_NOT": ast.Not(),
    "BITWISE_NOT": ast.Invert(),
}

COMPARE_OPS = {"EQUAL", "NOT_EQUAL", "LESS", "LESS_EQUAL", "GREATER", "GREATER_EQUAL"}
BOOL_OPS    = {"AND", "OR"}


# ---------------------------------------------------------------------------
# C++ stdlib → Python runtime helpers injected at the top of every module
# ---------------------------------------------------------------------------

RUNTIME_SOURCE = """
import sys
import math
from collections import defaultdict, deque

# ---- C++ stdlib shims ----

def _cpp_vector(*args):
    if len(args) == 1 and isinstance(args[0], int):
        return [0] * args[0]
    if len(args) == 2 and isinstance(args[0], int):
        return [args[1]] * args[0]
    return list(args[0]) if args else []

def _cpp_vector_2d(rows, cols, val=0):
    return [[val]*cols for _ in range(rows)]

def _cpp_string(s=""):
    return str(s)

def _cpp_pair(a, b):
    return [a, b]

def _cpp_map():
    return {}

def _cpp_set():
    return set()

def _cpp_stack():
    return []

def _cpp_queue_new():
    return deque()

def _size(container):
    return len(container)

def _empty(container):
    return len(container) == 0

def _push_back(container, val):
    container.append(val)
    return container

def _pop_back(container):
    container.pop()
    return container

def _back(container):
    return container[-1]

def _front(container):
    return container[0]

def _push(container, val):
    if isinstance(container, deque):
        container.append(val)
    else:
        container.append(val)
    return container

def _pop(container):
    if isinstance(container, deque):
        container.popleft()
    else:
        container.pop()
    return container

def _top(container):
    return container[-1]

def _insert(container, *args):
    if isinstance(container, set):
        container.add(args[-1])
    elif isinstance(container, dict):
        container[args[0]] = args[1] if len(args) > 1 else None
    else:
        if len(args) == 2:
            container.insert(args[0], args[1])
        else:
            container.append(args[0])
    return container

def _erase(container, key):
    if isinstance(container, (set, dict)):
        container.discard(key) if isinstance(container, set) else container.pop(key, None)
    elif isinstance(container, list):
        if isinstance(key, int) and 0 <= key < len(container):
            container.pop(key)
    return container

def _find(container, val):
    if isinstance(container, (set, dict)):
        return val in container
    try:
        return container.index(val)
    except ValueError:
        return -1

def _count(container, val):
    if isinstance(container, (set, dict)):
        return 1 if val in container else 0
    return container.count(val)

def _clear(container):
    container.clear()
    return container

def _sort(container, reverse=False):
    container.sort(reverse=reverse)
    return container

def _reverse_container(container):
    container.reverse()
    return container

def _swap(a, b):
    return b, a

def _substr(s, start, length=None):
    if length is None:
        return s[start:]
    return s[start:start+length]

def _to_string(val):
    return str(val)

def _stoi(s):
    return int(s)

def _stof(s):
    return float(s)

def _abs_val(x):
    return abs(x)

def _max_val(*args):
    if len(args) == 1:
        return max(args[0])
    return max(args)

def _min_val(*args):
    if len(args) == 1:
        return min(args[0])
    return min(args)

def _sqrt_val(x):
    return math.sqrt(x)

def _pow_val(x, y):
    return x ** y

def _floor_val(x):
    return int(math.floor(x))

def _ceil_val(x):
    return int(math.ceil(x))

def _log_val(x):
    return math.log(x)

INT_MAX = 2147483647
INT_MIN = -2147483648
"""

# ---------------------------------------------------------------------------
# Method call dispatch table
# ---------------------------------------------------------------------------

METHOD_DISPATCH = {
    "push_back":  "_push_back",
    "pop_back":   "_pop_back",
    "push":       "_push",
    "pop":        "_pop",
    "top":        "_top",
    "front":      "_front",
    "back":       "_back",
    "size":       "_size",
    "empty":      "_empty",
    "insert":     "_insert",
    "erase":      "_erase",
    "find":       "_find",
    "count":      "_count",
    "clear":      "_clear",
    "sort":       "_sort",
    "reverse":    "_reverse_container",
    "swap":       "_swap",
    "substr":     "_substr",
    "length":     "_size",
    "at":         None,   # handled as index
}

FREE_FUNC_DISPATCH = {
    "max":        "_max_val",
    "min":        "_min_val",
    "abs":        "_abs_val",
    "sort":       "_sort",
    "reverse":    "_reverse_container",
    "swap":       "_swap",
    "to_string":  "_to_string",
    "stoi":       "_stoi",
    "stof":       "_stof",
    "sqrt":       "_sqrt_val",
    "pow":        "_pow_val",
    "floor":      "_floor_val",
    "ceil":       "_ceil_val",
    "log":        "_log_val",
    "printf":     "print",
    "cout":       None,    # handled specially
    "endl":       None,
}

# Constructor-like calls
CONSTRUCTOR_DISPATCH = {
    "vector":           "_cpp_vector",
    "string":           "_cpp_string",
    "pair":             "_cpp_pair",
    "map":              "_cpp_map",
    "unordered_map":    "_cpp_map",
    "set":              "_cpp_set",
    "unordered_set":    "_cpp_set",
    "stack":            "_cpp_stack",
    "queue":            "_cpp_queue_new",
    "deque":            "deque",
    "priority_queue":   "_cpp_stack",
}


# ---------------------------------------------------------------------------
# Translator
# ---------------------------------------------------------------------------

class CppToPythonBytecode:
    def __init__(self, parser_ast: list, debug: bool = False):
        self.ast_nodes = parser_ast
        self._debug    = debug

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compile(self) -> "code":
        runtime_stmts = ast.parse(RUNTIME_SOURCE, mode='exec').body
        body = list(runtime_stmts)
        for node in self.ast_nodes:
            if node is None:
                continue
            translated = self._translate(node)
            if isinstance(translated, list):
                body.extend(t for t in translated if t is not None)
            elif translated is not None:
                body.append(translated)
        module = ast.Module(body=body, type_ignores=[])
        ast.fix_missing_locations(module)
        return compile(module, "<cpp_transpiler>", "exec")

    def dump_python_ast(self):
        body = []
        for node in self.ast_nodes:
            if node is None:
                continue
            t = self._translate(node)
            if isinstance(t, list):
                body.extend(x for x in t if x is not None)
            elif t is not None:
                body.append(t)
        module = ast.Module(body=body, type_ignores=[])
        ast.fix_missing_locations(module)
        print(ast.dump(module, indent=2))

    def dump_bytecode(self):
        dis.dis(self.compile())

    # ------------------------------------------------------------------
    # Dispatcher
    # ------------------------------------------------------------------

    def _translate(self, node):
        if node is None:
            return None

        node_type = node.get("type")
        if self._debug:
            print(f"[translate] {node_type}")

        handler = getattr(self, f"_translate_{node_type}", None)
        if handler is None:
            raise NotImplementedError(
                f"No translation handler for node type: '{node_type}'\nNode: {node}"
            )
        return handler(node)

    def _expr_stmt(self, expr_node):
        """Wrap an expression in an Expr statement if needed."""
        if isinstance(expr_node, ast.expr):
            return ast.Expr(value=expr_node)
        return expr_node

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def _translate_FunctionDecl(self, node):
        args = ast.arguments(
            posonlyargs=[],
            args=[ast.arg(arg=p["name"]) for p in node.get("params", [])],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        )
        raw_body = []
        for stmt in node.get("body", []):
            if stmt is None:
                continue
            translated = self._translate(stmt)
            if isinstance(translated, list):
                raw_body.extend(t for t in translated if t is not None)
            elif translated is not None:
                raw_body.append(translated)
        body = raw_body if raw_body else [ast.Pass()]
        return ast.FunctionDef(
            name=node["name"],
            args=args,
            body=body,
            decorator_list=[],
            returns=None,
        )

    def _translate_VarDecl(self, node):
        target = ast.Name(id=node["name"], ctx=ast.Store())
        if node.get("init"):
            value = self._translate(node["init"])
        elif node.get("arraySize"):
            # int arr[n] -> [0] * n
            size = self._translate(node["arraySize"])
            value = ast.BinOp(
                left=ast.List(elts=[ast.Constant(value=0)], ctx=ast.Load()),
                op=ast.Mult(),
                right=size
            )
        else:
            # Default initialization based on type
            type_name = node.get("varType", "")
            if type_name in ("int", "long", "short", "char"):
                value = ast.Constant(value=0)
            elif type_name in ("float", "double"):
                value = ast.Constant(value=0.0)
            elif type_name == "bool":
                value = ast.Constant(value=False)
            elif type_name == "string":
                value = ast.Constant(value="")
            elif type_name in CONSTRUCTOR_DISPATCH:
                fn = ast.Name(id=CONSTRUCTOR_DISPATCH[type_name], ctx=ast.Load())
                value = ast.Call(func=fn, args=[], keywords=[])
            else:
                value = ast.Constant(value=None)
        return ast.Assign(targets=[target], value=value)

    def _translate_MultiVarDecl(self, node):
        stmts = []
        for decl in node["decls"]:
            stmts.append(self._translate_VarDecl(decl))
        return stmts

    def _translate_ReturnStmt(self, node):
        value = self._translate(node["expr"]) if node.get("expr") else None
        return ast.Return(value=value)

    def _translate_ExprStmt(self, node):
        expr_node = self._translate(node["expr"])
        if isinstance(expr_node, ast.expr):
            return ast.Expr(value=expr_node)
        return expr_node

    def _translate_BlockStmt(self, node):
        stmts = []
        for s in node.get("body", []):
            if s is None:
                continue
            t = self._translate(s)
            if isinstance(t, list):
                stmts.extend(x for x in t if x is not None)
            elif t is not None:
                stmts.append(t)
        return stmts

    def _translate_IfStmt(self, node):
        condition = self._translate(node["condition"])
        then_body = self._build_body(node.get("then", []))
        else_body = self._build_body(node.get("else", [])) if node.get("else") else []
        return ast.If(
            test=condition,
            body=then_body if then_body else [ast.Pass()],
            orelse=else_body
        )

    def _translate_WhileStmt(self, node):
        test = self._translate(node["condition"])
        body = self._build_body(node.get("body", []))
        return ast.While(
            test=test,
            body=body if body else [ast.Pass()],
            orelse=[]
        )

    def _translate_ForStmt(self, node):
        stmts = []
        if node.get("init"):
            init_node = self._translate(node["init"])
            if isinstance(init_node, list):
                stmts.extend(x for x in init_node if x is not None)
            elif init_node is not None:
                stmts.append(init_node)

        condition = self._translate(node["condition"]) if node.get("condition") else ast.Constant(value=True)
        body = self._build_body(node.get("body", []))

        if node.get("update"):
            update_node = self._translate(node["update"])
            if isinstance(update_node, ast.expr):
                update_node = ast.Expr(value=update_node)
            if update_node is not None:
                body.append(update_node)

        stmts.append(ast.While(
            test=condition,
            body=body if body else [ast.Pass()],
            orelse=[]
        ))
        return stmts

    def _translate_BreakContinueStmt(self, node):
        if node["keyword"] == "break":
            return ast.Break()
        return ast.Continue()

    def _translate_NoOp(self, node):
        return ast.Pass()

    def _build_body(self, stmts):
        result = []
        for s in stmts:
            if s is None:
                continue
            t = self._translate(s)
            if isinstance(t, list):
                result.extend(x for x in t if x is not None)
            elif t is not None:
                result.append(t)
        return result

    # ------------------------------------------------------------------
    # Expressions
    # ------------------------------------------------------------------

    def _translate_AssignExpr(self, node):
        left = node["left"]
        right_val = self._translate(node["right"])

        if left.get("type") == "Identifier":
            target = ast.Name(id=left["name"], ctx=ast.Store())
        elif left.get("type") == "IndexExpr":
            arr = self._translate(left["array"])
            idx = self._translate(left["index"])
            target = ast.Subscript(value=arr, slice=idx, ctx=ast.Store())
        elif left.get("type") == "MemberAccess":
            obj = self._translate(left["object"])
            target = ast.Attribute(value=obj, attr=left["member"], ctx=ast.Store())
        else:
            raise NotImplementedError(f"Assignment to {left.get('type')} not supported")

        return ast.Assign(targets=[target], value=right_val)

    def _translate_BinaryExpr(self, node):
        op_name = node["op"]
        left    = self._translate(node["left"])
        right   = self._translate(node["right"])

        if op_name in COMPARE_OPS:
            return ast.Compare(left=left, ops=[BINARY_OP_MAP[op_name]], comparators=[right])

        if op_name in BOOL_OPS:
            return ast.BoolOp(op=BINARY_OP_MAP[op_name], values=[left, right])

        py_op = BINARY_OP_MAP.get(op_name)
        if py_op is None:
            raise NotImplementedError(f"Unsupported binary operator: '{op_name}'")

        # Use true division for float operands, floor division otherwise
        # Since we can't know types at this point, always use regular Div for /
        # and let Python handle it; override for SLASH to use //
        if op_name == "SLASH":
            # Use integer division to match C++ semantics
            return ast.BinOp(left=left, op=ast.FloorDiv(), right=right)

        return ast.BinOp(left=left, op=py_op, right=right)

    def _translate_UnaryExpr(self, node):
        op_name = node["op"]
        operand = self._translate(node["expr"])
        py_op   = UNARY_OP_MAP.get(op_name)
        if py_op is None:
            raise NotImplementedError(f"Unsupported unary operator: '{op_name}'")
        return ast.UnaryOp(op=py_op, operand=operand)

    def _translate_UpdateExpr(self, node):
        target = node["expr"]
        if target.get("type") not in ("Identifier", "IndexExpr"):
            raise NotImplementedError("++/-- only on identifiers/indices")

        if target["type"] == "Identifier":
            name = target["name"]
            lhs = ast.Name(id=name, ctx=ast.Store())
            rhs_load = ast.Name(id=name, ctx=ast.Load())
        else:
            arr = self._translate(target["array"])
            idx = self._translate(target["index"])
            lhs = ast.Subscript(value=arr, slice=idx, ctx=ast.Store())
            rhs_load = ast.Subscript(
                value=self._translate(target["array"]),
                slice=self._translate(target["index"]),
                ctx=ast.Load()
            )

        op = ast.Add() if node["op"] == "INCREMENT" else ast.Sub()
        return ast.Assign(
            targets=[lhs],
            value=ast.BinOp(left=rhs_load, op=op, right=ast.Constant(value=1))
        )

    def _translate_TernaryExpr(self, node):
        return ast.IfExp(
            test=self._translate(node["condition"]),
            body=self._translate(node["then"]),
            orelse=self._translate(node["else"])
        )

    def _translate_CastExpr(self, node):
        # Just pass through the expression; Python is dynamically typed
        return self._translate(node["expr"])

    def _translate_NumberLiteral(self, node):
        raw = node["value"]
        try:
            value = int(raw)
        except ValueError:
            value = float(raw)
        return ast.Constant(value=value)

    def _translate_StringLiteral(self, node):
        return ast.Constant(value=node["value"])

    def _translate_CharLiteral(self, node):
        return ast.Constant(value=node["value"])

    def _translate_Identifier(self, node):
        name = node["name"]
        # Map special C++ names
        special = {
            "nullptr": ast.Constant(value=None),
            "null": ast.Constant(value=None),
            "true": ast.Constant(value=True),
            "false": ast.Constant(value=False),
            "INT_MAX": ast.Name(id="INT_MAX", ctx=ast.Load()),
            "INT_MIN": ast.Name(id="INT_MIN", ctx=ast.Load()),
            "endl": ast.Constant(value="\n"),
        }
        if name in special:
            return special[name]
        return ast.Name(id=name, ctx=ast.Load())

    def _translate_IndexExpr(self, node):
        arr = self._translate(node["array"])
        idx = self._translate(node["index"])
        return ast.Subscript(value=arr, slice=idx, ctx=ast.Load())

    def _translate_MemberAccess(self, node):
        obj = self._translate(node["object"])
        member = node["member"]
        # size -> len(obj)
        if member in ("size", "length"):
            return ast.Call(
                func=ast.Name(id="len", ctx=ast.Load()),
                args=[obj], keywords=[]
            )
        if member == "empty":
            return ast.Compare(
                left=ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[obj], keywords=[]),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=0)]
            )
        if member == "first":
            return ast.Subscript(value=obj, slice=ast.Constant(value=0), ctx=ast.Load())
        if member == "second":
            return ast.Subscript(value=obj, slice=ast.Constant(value=1), ctx=ast.Load())
        return ast.Attribute(value=obj, attr=member, ctx=ast.Load())

    def _translate_MethodCall(self, node):
        obj  = self._translate(node["object"])
        method = node["method"]
        args = [self._translate(a) for a in node.get("args", [])]

        # size() / length() -> len(obj)
        if method in ("size", "length"):
            return ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[obj], keywords=[])

        # empty() -> len(obj) == 0
        if method == "empty":
            return ast.Compare(
                left=ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[obj], keywords=[]),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=0)]
            )

        # at(i) -> obj[i]
        if method == "at":
            return ast.Subscript(value=obj, slice=args[0], ctx=ast.Load())

        # first / second (pair access)
        if method == "first":
            return ast.Subscript(value=obj, slice=ast.Constant(value=0), ctx=ast.Load())
        if method == "second":
            return ast.Subscript(value=obj, slice=ast.Constant(value=1), ctx=ast.Load())

        # map count / find -> key in dict
        if method == "count":
            return ast.Compare(left=args[0], ops=[ast.In()], comparators=[obj])
        if method == "find":
            return ast.Compare(left=args[0], ops=[ast.In()], comparators=[obj])

        # push_back -> .append()
        if method == "push_back":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="append", ctx=ast.Load()),
                args=args, keywords=[]
            )

        # pop_back -> .pop()
        if method == "pop_back":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="pop", ctx=ast.Load()),
                args=[], keywords=[]
            )

        # push (stack) -> .append()
        if method == "push":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="append", ctx=ast.Load()),
                args=args, keywords=[]
            )

        # pop (stack) -> .pop()
        if method == "pop":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="pop", ctx=ast.Load()),
                args=[], keywords=[]
            )

        # top (stack) -> [-1]
        if method == "top":
            return ast.Subscript(value=obj, slice=ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=1)), ctx=ast.Load())

        # front -> [0], back -> [-1]
        if method == "front":
            return ast.Subscript(value=obj, slice=ast.Constant(value=0), ctx=ast.Load())
        if method == "back":
            return ast.Subscript(value=obj, slice=ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=1)), ctx=ast.Load())

        # insert (set/map)
        if method == "insert":
            if len(args) == 1:
                # set insert: obj.add(val)
                return ast.Call(
                    func=ast.Attribute(value=obj, attr="add", ctx=ast.Load()),
                    args=args, keywords=[]
                )
            else:
                # vector insert at position
                return ast.Call(
                    func=ast.Attribute(value=obj, attr="insert", ctx=ast.Load()),
                    args=args, keywords=[]
                )

        # erase
        if method == "erase":
            # For sets/dicts: obj.discard(val); for lists: obj.pop(idx)
            return ast.Call(
                func=ast.Attribute(value=obj, attr="pop", ctx=ast.Load()),
                args=args, keywords=[]
            )

        # clear -> .clear()
        if method == "clear":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="clear", ctx=ast.Load()),
                args=[], keywords=[]
            )

        # resize -> handled by extending
        if method == "resize":
            # obj.extend([0] * max(0, n - len(obj)))
            n = args[0]
            fill = args[1] if len(args) > 1 else ast.Constant(value=0)
            return ast.Call(
                func=ast.Name(id="_push_back", ctx=ast.Load()),
                args=[obj, fill], keywords=[]
            )

        # sort -> .sort() - note this is void
        if method == "sort":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="sort", ctx=ast.Load()),
                args=[], keywords=[]
            )

        # reverse -> .reverse()
        if method == "reverse":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="reverse", ctx=ast.Load()),
                args=[], keywords=[]
            )

        # substr(pos, len)
        if method == "substr":
            if len(args) == 1:
                return ast.Subscript(
                    value=obj,
                    slice=ast.Slice(lower=args[0], upper=None),
                    ctx=ast.Load()
                )
            return ast.Subscript(
                value=obj,
                slice=ast.Slice(
                    lower=args[0],
                    upper=ast.BinOp(left=args[0], op=ast.Add(), right=args[1])
                ),
                ctx=ast.Load()
            )

        # Generic fallback: obj.method(args)
        return ast.Call(
            func=ast.Attribute(value=obj, attr=method, ctx=ast.Load()),
            args=args, keywords=[]
        )

    def _translate_CallExpr(self, node):
        callee = node["callee"]
        args   = [self._translate(a) for a in node.get("args", [])]

        # Constructor calls
        if callee in CONSTRUCTOR_DISPATCH:
            fn = ast.Name(id=CONSTRUCTOR_DISPATCH[callee], ctx=ast.Load())
            return ast.Call(func=fn, args=args, keywords=[])

        # Free function remapping
        if callee in FREE_FUNC_DISPATCH:
            mapped = FREE_FUNC_DISPATCH[callee]
            if mapped is None:
                return ast.Constant(value=None)
            fn = ast.Name(id=mapped, ctx=ast.Load())
            return ast.Call(func=fn, args=args, keywords=[])

        # abs / max / min builtins
        if callee == "abs":
            return ast.Call(func=ast.Name(id="abs", ctx=ast.Load()), args=args, keywords=[])
        if callee == "max":
            if len(args) == 2:
                return ast.Call(func=ast.Name(id="max", ctx=ast.Load()), args=args, keywords=[])
            return ast.Call(func=ast.Name(id="_max_val", ctx=ast.Load()), args=args, keywords=[])
        if callee == "min":
            if len(args) == 2:
                return ast.Call(func=ast.Name(id="min", ctx=ast.Load()), args=args, keywords=[])
            return ast.Call(func=ast.Name(id="_min_val", ctx=ast.Load()), args=args, keywords=[])

        fn = ast.Name(id=callee, ctx=ast.Load())
        return ast.Call(func=fn, args=args, keywords=[])

    def _translate_InitializerList(self, node):
        elements = [self._translate(e) for e in node.get("elements", [])]
        return ast.List(elts=elements, ctx=ast.Load())


# ---------------------------------------------------------------------------
# Convenience entry-point
# ---------------------------------------------------------------------------

def transpile(source_code: str, debug: bool = False) -> "code":
    from scanner import Scanner
    from parser  import Parser
    tokens    = Scanner(source_code).scan()
    ast_nodes = Parser(tokens).parse()
    return CppToPythonBytecode(ast_nodes, debug=debug).compile()


if __name__ == "__main__":
    import sys, json
    sample = """
int add(int a, int b) {
    return a + b;
}
int main() {
    int x = 3 + 4;
    return x;
}
"""
    source = open(sys.argv[1]).read() if len(sys.argv) == 2 else sample
    from scanner import Scanner
    from parser  import Parser
    tokens = Scanner(source).scan()
    nodes  = Parser(tokens).parse()
    print("=== Parser AST ===")
    print(json.dumps(nodes, indent=2, default=str))
    t = CppToPythonBytecode(nodes, debug=True)
    print("\n=== exec() test ===")
    ns = {}
    exec(t.compile(), ns)
    if "add" in ns:
        print(f"add(3, 4) = {ns['add'](3, 4)}")