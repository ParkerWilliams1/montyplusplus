"""
CppToPythonBytecode.py (C++17 enhanced)

Translates C++ parser AST dicts -> Python code object via `ast` module.
Handles: functions, loops, arrays, vectors, maps, sets, method calls,
         ternary, break/continue, member access, initializer lists,
         range-for, switch/case, do-while, try/catch, lambdas,
         enums, structured bindings, optional, variant, tuple,
         smart pointers, algorithm functions, C++17 stdlib.
"""

import ast
import dis


BINARY_OP_MAP = {
    "PLUS":          ast.Add(),
    "MINUS":         ast.Sub(),
    "STAR":          ast.Mult(),
    "SLASH":         ast.FloorDiv(),
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


RUNTIME_SOURCE = """
import sys
import math
import copy
import itertools
import functools
from collections import defaultdict, deque, OrderedDict
from typing import Optional as _Optional

def _cpp_vector(*args):
    if len(args) == 1 and isinstance(args[0], int):
        return [0] * args[0]
    if len(args) == 2 and isinstance(args[0], int):
        return [args[1]] * args[0]
    if len(args) == 1 and hasattr(args[0], '__iter__'):
        return list(args[0])
    return list(args) if args else []

def _cpp_array(*args):
    return list(args)

def _cpp_vector_2d(rows, cols, val=0):
    return [[val]*cols for _ in range(rows)]

def _cpp_string(s=""):
    return str(s)

def _cpp_pair(a, b):
    return [a, b]

def _cpp_tuple(*args):
    return list(args)

def _cpp_map(*args):
    if args:
        return dict(args[0]) if len(args) == 1 else {}
    return {}

def _cpp_set(*args):
    if args and hasattr(args[0], '__iter__'):
        return set(args[0])
    return set(args) if args else set()

def _cpp_stack(*args):
    if args and hasattr(args[0], '__iter__'):
        return list(args[0])
    return []

def _cpp_queue_new(*args):
    if args and hasattr(args[0], '__iter__'):
        return deque(args[0])
    return deque()

def _cpp_optional(val=None):
    return [True, val] if val is not None else [False, None]

def _cpp_variant(*args):
    return args[0] if args else None

def _cpp_any(val=None):
    return val

def _cpp_bitset(n, val=0):
    return val & ((1 << n) - 1)

def _size(container):
    return len(container)

def _empty(container):
    return len(container) == 0

def _push_back(container, val):
    container.append(val)
    return container

def _pop_back(container):
    if container:
        container.pop()
    return container

def _back(container):
    return container[-1]

def _front(container):
    return container[0]

def _push(container, val):
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
        if len(args) == 2:
            container[args[0]] = args[1]
        elif len(args) == 1 and isinstance(args[0], (list, tuple)):
            container[args[0][0]] = args[0][1]
        else:
            container[args[0]] = None
    else:
        if len(args) == 2:
            container.insert(args[0], args[1])
        else:
            container.append(args[0])
    return container

def _emplace_back(container, *args):
    container.append(list(args) if len(args) > 1 else args[0])
    return container

def _emplace(container, *args):
    if isinstance(container, set):
        container.add(args[-1])
    elif isinstance(container, dict) and len(args) >= 2:
        container[args[0]] = args[1]
    elif isinstance(container, list) and len(args) >= 2:
        container.insert(args[0], args[1])
    else:
        container.append(args[0] if len(args) == 1 else list(args))
    return container

def _erase(container, key):
    if isinstance(container, set):
        container.discard(key)
    elif isinstance(container, dict):
        container.pop(key, None)
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
    if hasattr(container, 'clear'):
        container.clear()
    return container

def _sort(container, reverse=False):
    if hasattr(container, 'sort'):
        container.sort(reverse=reverse)
    return container

def _stable_sort(container, key=None, reverse=False):
    container.sort(key=key, reverse=reverse)
    return container

def _partial_sort(container, n, reverse=False):
    container[:n] = sorted(container[:n], reverse=reverse)
    return container

def _nth_element(container, n):
    container.sort()
    return container

def _reverse_container(container):
    if hasattr(container, 'reverse'):
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

def _stoi(s, pos=None, base=10):
    try:
        return int(str(s).strip(), base)
    except (ValueError, TypeError):
        return 0

def _stol(s, pos=None, base=10):
    return _stoi(s, pos, base)

def _stoll(s, pos=None, base=10):
    return _stoi(s, pos, base)

def _stof(s, pos=None):
    try:
        return float(str(s).strip())
    except (ValueError, TypeError):
        return 0.0

def _stod(s, pos=None):
    return _stof(s)

def _atoi(s):
    return _stoi(s)

def _atof(s):
    return _stof(s)

def _abs_val(x):
    return abs(x)

def _max_val(*args):
    if len(args) == 1 and hasattr(args[0], '__iter__'):
        return max(args[0])
    return max(args)

def _min_val(*args):
    if len(args) == 1 and hasattr(args[0], '__iter__'):
        return min(args[0])
    return min(args)

def _clamp(val, lo, hi):
    return max(lo, min(hi, val))

def _sqrt_val(x):
    return math.sqrt(x)

def _pow_val(x, y):
    return x ** y

def _floor_val(x):
    return int(math.floor(x))

def _ceil_val(x):
    return int(math.ceil(x))

def _round_val(x):
    return round(x)

def _log_val(x):
    return math.log(x)

def _log2_val(x):
    return math.log2(x)

def _log10_val(x):
    return math.log10(x)

def _exp_val(x):
    return math.exp(x)

def _sin_val(x):
    return math.sin(x)

def _cos_val(x):
    return math.cos(x)

def _tan_val(x):
    return math.tan(x)

def _asin_val(x):
    return math.asin(x)

def _acos_val(x):
    return math.acos(x)

def _atan_val(x):
    return math.atan(x)

def _atan2_val(y, x):
    return math.atan2(y, x)

def _gcd_val(a, b):
    return math.gcd(a, b)

def _lcm_val(a, b):
    return abs(a * b) // math.gcd(a, b) if a and b else 0

def _accumulate(container, init=0, fn=None):
    if fn:
        return functools.reduce(fn, container, init)
    return sum(container) + init

def _transform(container, fn):
    return list(map(fn, container))

def _for_each(container, fn):
    for x in container:
        fn(x)
    return container

def _fill(container, val):
    for i in range(len(container)):
        container[i] = val
    return container

def _copy_container(src):
    return list(src)

def _rotate(container, n):
    if not container:
        return container
    n = n % len(container)
    container[:] = container[n:] + container[:n]
    return container

def _unique_container(container):
    seen = []
    for x in container:
        if not seen or seen[-1] != x:
            seen.append(x)
    container[:] = seen
    return container

def _remove_val(container, val):
    container[:] = [x for x in container if x != val]
    return container

def _remove_if(container, pred):
    container[:] = [x for x in container if not pred(x)]
    return container

def _merge_containers(a, b):
    return sorted(a + b)

def _binary_search(container, val):
    import bisect
    i = bisect.bisect_left(container, val)
    return i < len(container) and container[i] == val

def _lower_bound(container, val):
    import bisect
    return bisect.bisect_left(container, val)

def _upper_bound(container, val):
    import bisect
    return bisect.bisect_right(container, val)

def _next_permutation(container):
    n = len(container)
    i = n - 2
    while i >= 0 and container[i] >= container[i + 1]:
        i -= 1
    if i < 0:
        container.sort()
        return False
    j = n - 1
    while container[j] <= container[i]:
        j -= 1
    container[i], container[j] = container[j], container[i]
    container[i+1:] = reversed(container[i+1:])
    return True

def _prev_permutation(container):
    n = len(container)
    i = n - 2
    while i >= 0 and container[i] <= container[i + 1]:
        i -= 1
    if i < 0:
        container.sort(reverse=True)
        return False
    j = n - 1
    while container[j] >= container[i]:
        j -= 1
    container[i], container[j] = container[j], container[i]
    container[i+1:] = reversed(container[i+1:])
    return True

def _make_shared(val):
    return [val]

def _make_unique(val):
    return [val]

def _make_optional(val):
    return [True, val]

def _optional_has_value(opt):
    return isinstance(opt, list) and opt[0] is True

def _optional_value(opt):
    if isinstance(opt, list) and opt[0]:
        return opt[1]
    raise RuntimeError("bad optional access")

def _optional_value_or(opt, default):
    if isinstance(opt, list) and opt[0]:
        return opt[1]
    return default

def _tuple_get(tup, idx):
    return tup[idx]

def _make_pair(a, b):
    return [a, b]

def _make_tuple(*args):
    return list(args)

def _iota(container, start):
    for i in range(len(container)):
        container[i] = start + i
    return container

def _getline(stream, s_ref):
    try:
        line = input()
        return line
    except EOFError:
        return ""

def _printf(fmt, *args):
    try:
        print(fmt % args if args else fmt, end='')
    except Exception:
        print(fmt, *args, end='')

def _sprintf(fmt, *args):
    try:
        return fmt % args
    except Exception:
        return str(fmt)

def _scanf(fmt, *args):
    return input()

def _sscanf(s, fmt, *args):
    parts = s.split()
    return parts

INT_MAX = 2147483647
INT_MIN = -2147483648
LONG_MAX = 9223372036854775807
LONG_MIN = -9223372036854775808
UINT_MAX = 4294967295
SIZE_MAX = 18446744073709551615
DBL_MAX = 1.7976931348623157e+308
FLT_MAX = 3.4028235e+38
M_PI = math.pi
M_E = math.e
M_SQRT2 = math.sqrt(2)
EOF_VAL = -1
"""


METHOD_DISPATCH = {
    "push_back":      "push_back",
    "emplace_back":   "emplace_back",
    "pop_back":       "pop_back",
    "push_front":     "push_front",
    "pop_front":      "pop_front",
    "push":           "push",
    "pop":            "pop",
    "emplace":        "emplace",
    "top":            "top",
    "front":          "front",
    "back":           "back",
    "size":           "size",
    "empty":          "empty",
    "insert":         "insert",
    "erase":          "erase",
    "find":           "find",
    "count":          "count",
    "clear":          "clear",
    "sort":           "sort",
    "reverse":        "reverse",
    "swap":           "swap",
    "substr":         "substr",
    "length":         "size",
    "at":             None,
    "resize":         "resize",
    "reserve":        None,
    "shrink_to_fit":  None,
    "capacity":       "size",
    "append":         "append",
    "contains":       "contains",
    "starts_with":    "starts_with",
    "ends_with":      "ends_with",
    "replace":        "replace",
    "find_first_of":  "find_first_of",
    "find_last_of":   "find_last_of",
    "c_str":          "c_str",
    "data":           "data",
    "has_value":      "has_value",
    "value":          "value",
    "value_or":       "value_or",
    "reset":          "reset",
    "get":            "get",
    "first":          "first",
    "second":         "second",
}

FREE_FUNC_DISPATCH = {
    "max":                "_max_val",
    "min":                "_min_val",
    "abs":                "_abs_val",
    "fabs":               "_abs_val",
    "sort":               "_sort",
    "stable_sort":        "_stable_sort",
    "partial_sort":       "_partial_sort",
    "nth_element":        "_nth_element",
    "reverse":            "_reverse_container",
    "swap":               "_swap",
    "to_string":          "_to_string",
    "stoi":               "_stoi",
    "stol":               "_stol",
    "stoll":              "_stoll",
    "stof":               "_stof",
    "stod":               "_stod",
    "atoi":               "_atoi",
    "atof":               "_atof",
    "sqrt":               "_sqrt_val",
    "pow":                "_pow_val",
    "floor":              "_floor_val",
    "ceil":               "_ceil_val",
    "round":              "_round_val",
    "log":                "_log_val",
    "log2":               "_log2_val",
    "log10":              "_log10_val",
    "exp":                "_exp_val",
    "sin":                "_sin_val",
    "cos":                "_cos_val",
    "tan":                "_tan_val",
    "asin":               "_asin_val",
    "acos":               "_acos_val",
    "atan":               "_atan_val",
    "atan2":              "_atan2_val",
    "gcd":                "_gcd_val",
    "lcm":                "_lcm_val",
    "clamp":              "_clamp",
    "accumulate":         "_accumulate",
    "transform":          "_transform",
    "for_each":           "_for_each",
    "fill":               "_fill",
    "copy":               "_copy_container",
    "rotate":             "_rotate",
    "unique":             "_unique_container",
    "remove":             "_remove_val",
    "remove_if":          "_remove_if",
    "merge":              "_merge_containers",
    "binary_search":      "_binary_search",
    "lower_bound":        "_lower_bound",
    "upper_bound":        "_upper_bound",
    "next_permutation":   "_next_permutation",
    "prev_permutation":   "_prev_permutation",
    "make_shared":        "_make_shared",
    "make_unique":        "_make_unique",
    "make_optional":      "_make_optional",
    "make_pair":          "_make_pair",
    "make_tuple":         "_make_tuple",
}

CONSTRUCTOR_DISPATCH = {
    "vector":               "_cpp_vector",
    "array":                "_cpp_array",
    "string":               "_cpp_string",
    "pair":                 "_cpp_pair",
    "tuple":                "_cpp_tuple",
    "optional":             "_cpp_optional",
    "variant":              "_cpp_variant",
    "any":                  "_cpp_any",
    "map":                  "_cpp_map",
    "unordered_map":        "_cpp_map",
    "multimap":             "_cpp_map",
    "unordered_multimap":   "_cpp_map",
    "set":                  "_cpp_set",
    "unordered_set":        "_cpp_set",
    "multiset":             "_cpp_set",
    "unordered_multiset":   "_cpp_set",
    "stack":                "_cpp_stack",
    "queue":                "_cpp_queue_new",
    "deque":                "deque",
    "priority_queue":       "_cpp_stack",
    "forward_list":         "_cpp_vector",
    "list":                 "_cpp_vector",
    "bitset":               "_cpp_bitset",
    "shared_ptr":           "_make_shared",
    "unique_ptr":           "_make_unique",
    "weak_ptr":             "_make_shared",
}


class CppToPythonBytecode:
    def __init__(self, parser_ast: list, debug: bool = False):
        self.ast_nodes = parser_ast
        self._debug    = debug
        self._enum_classes = {}

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
        if isinstance(expr_node, ast.expr):
            return ast.Expr(value=expr_node)
        return expr_node

    def _translate_FunctionDecl(self, node):
        params = node.get("params", [])
        py_args = []
        defaults = []
        for p in params:
            if p.get("type") == "...":
                continue
            py_args.append(ast.arg(arg=p["name"]))
            if "default" in p:
                defaults.append(self._translate(p["default"]))
        args = ast.arguments(
            posonlyargs=[],
            args=py_args,
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=defaults,
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
            size = self._translate(node["arraySize"])
            value = ast.BinOp(
                left=ast.List(elts=[ast.Constant(value=0)], ctx=ast.Load()),
                op=ast.Mult(),
                right=size
            )
        else:
            type_name = node.get("varType", "")
            if type_name in ("int", "long", "short", "char", "unsigned", "signed"):
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
            elif type_name == "auto":
                value = ast.Constant(value=None)
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
        stmts = []

        if node.get("init"):
            init_node = self._translate(node["init"])
            if isinstance(init_node, list):
                stmts.extend(x for x in init_node if x is not None)
            elif init_node is not None:
                stmts.append(init_node)

        condition = self._translate(node["condition"])
        then_body = self._build_body(node.get("then", []))
        else_body = self._build_body(node.get("else", [])) if node.get("else") else []
        if_node = ast.If(
            test=condition,
            body=then_body if then_body else [ast.Pass()],
            orelse=else_body
        )
        stmts.append(if_node)
        return stmts if len(stmts) > 1 else if_node

    def _translate_WhileStmt(self, node):
        test = self._translate(node["condition"])
        body = self._build_body(node.get("body", []))
        return ast.While(
            test=test,
            body=body if body else [ast.Pass()],
            orelse=[]
        )

    def _translate_DoWhileStmt(self, node):
        body = self._build_body(node.get("body", []))
        condition = self._translate(node["condition"])
        break_stmt = ast.If(
            test=ast.UnaryOp(op=ast.Not(), operand=condition),
            body=[ast.Break()],
            orelse=[]
        )
        full_body = body + [break_stmt] if body else [break_stmt]
        return ast.While(
            test=ast.Constant(value=True),
            body=full_body,
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
            update_raw = node["update"]
            if update_raw.get("type") == "ExprList":
                for e in update_raw["exprs"]:
                    update_node = self._translate(e)
                    if isinstance(update_node, ast.expr):
                        body.append(ast.Expr(value=update_node))
                    elif update_node is not None:
                        body.append(update_node)
            else:
                update_node = self._translate(update_raw)
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

    def _translate_RangeForStmt(self, node):
        var_name = node["varName"]
        iterable = self._translate(node["iterable"])
        body = self._build_body(node.get("body", []))

        target = ast.Name(id=var_name, ctx=ast.Store())
        return ast.For(
            target=target,
            iter=iterable,
            body=body if body else [ast.Pass()],
            orelse=[]
        )

    def _translate_SwitchStmt(self, node):
        expr = self._translate(node["expr"])
        tmp_var = "_switch_val"
        assign = ast.Assign(
            targets=[ast.Name(id=tmp_var, ctx=ast.Store())],
            value=expr
        )

        cases = node.get("cases", [])
        if not cases:
            return [assign]

        def build_if_chain(idx):
            if idx >= len(cases):
                return []
            case = cases[idx]
            body = self._build_body(case.get("body", []))

            has_break = any(
                s is not None and isinstance(s, ast.stmt) and
                (isinstance(s, ast.Break) or
                 (isinstance(s, ast.Expr) and False))
                for s in body
            )

            filtered_body = [s for s in body if not isinstance(s, ast.Break)]
            if not filtered_body:
                filtered_body = [ast.Pass()]

            rest = build_if_chain(idx + 1)

            if case["value"] is None:
                return filtered_body + rest
            else:
                cond = ast.Compare(
                    left=ast.Name(id=tmp_var, ctx=ast.Load()),
                    ops=[ast.Eq()],
                    comparators=[self._translate(case["value"])]
                )
                return [ast.If(test=cond, body=filtered_body, orelse=rest)]

        result = build_if_chain(0)
        return [assign] + result

    def _translate_TryStmt(self, node):
        try_body = self._build_body(node.get("body", []))
        handlers = []
        for catch in node.get("catches", []):
            catch_body = self._build_body(catch.get("body", []))
            if catch["type"] == "...":
                handler = ast.ExceptHandler(
                    type=None,
                    name=None,
                    body=catch_body if catch_body else [ast.Pass()]
                )
            else:
                handler = ast.ExceptHandler(
                    type=ast.Name(id="Exception", ctx=ast.Load()),
                    name=catch["name"],
                    body=catch_body if catch_body else [ast.Pass()]
                )
            handlers.append(handler)
        if not handlers:
            handlers = [ast.ExceptHandler(type=None, name=None, body=[ast.Pass()])]
        return ast.Try(
            body=try_body if try_body else [ast.Pass()],
            handlers=handlers,
            orelse=[],
            finalbody=[]
        )

    def _translate_ThrowStmt(self, node):
        if node.get("expr"):
            exc = self._translate(node["expr"])
            return ast.Raise(exc=ast.Call(
                func=ast.Name(id="RuntimeError", ctx=ast.Load()),
                args=[exc],
                keywords=[]
            ), cause=None)
        return ast.Raise(exc=None, cause=None)

    def _translate_EnumDecl(self, node):
        stmts = []
        for e in node.get("enumerators", []):
            stmts.append(ast.Assign(
                targets=[ast.Name(id=e["name"], ctx=ast.Store())],
                value=ast.Constant(value=e["value"])
            ))
        if node.get("name"):
            self._enum_classes[node["name"]] = {e["name"]: e["value"] for e in node.get("enumerators", [])}
            dict_entries = [
                ast.Tuple(
                    elts=[ast.Constant(value=e["name"]), ast.Constant(value=e["value"])],
                    ctx=ast.Load()
                )
                for e in node.get("enumerators", [])
            ]
            stmts.append(ast.Assign(
                targets=[ast.Name(id=node["name"], ctx=ast.Store())],
                value=ast.Dict(
                    keys=[ast.Constant(value=e["name"]) for e in node.get("enumerators", [])],
                    values=[ast.Constant(value=e["value"]) for e in node.get("enumerators", [])]
                )
            ))
        return stmts

    def _translate_Namespace(self, node):
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

    def _translate_LambdaExpr(self, node):
        params = node.get("params", [])
        py_args_list = [ast.arg(arg=p["name"]) for p in params if p.get("name") and p.get("type") != "..."]
        args = ast.arguments(
            posonlyargs=[],
            args=py_args_list,
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        )
        body = self._build_body(node.get("body", []))
        if not body:
            body = [ast.Return(value=ast.Constant(value=None))]
        has_return = any(isinstance(s, ast.Return) for s in body)
        if not has_return and body:
            last = body[-1]
            if isinstance(last, ast.Expr):
                body[-1] = ast.Return(value=last.value)
            else:
                body.append(ast.Return(value=ast.Constant(value=None)))
        # Single-expression body → real ast.Lambda
        if len(body) == 1 and isinstance(body[0], ast.Return):
            return ast.Lambda(args=args, body=body[0].value)
        # Multi-statement body → named inner function; caller must handle [FunctionDef, Name]
        return self._make_lambda_func(args, body)

    def _make_lambda_func(self, args, body):
        func_name = "_lambda_fn"
        func_def = ast.FunctionDef(
            name=func_name,
            args=args,
            body=body,
            decorator_list=[],
            returns=None,
        )
        # Return an expression that is the name of the just-defined function.
        # Callers embed this inside an ast.Expr or use it as a value; the
        # FunctionDef is prepended separately in _translate_LambdaExpr.
        return ast.Name(id=func_name, ctx=ast.Load())

    def _translate_BreakContinueStmt(self, node):
        if node["keyword"] == "break":
            return ast.Break()
        return ast.Continue()

    def _translate_NoOp(self, node):
        return ast.Pass()

    def _translate_DeleteExpr(self, node):
        return ast.Assign(
            targets=[self._as_store(self._translate(node["expr"]))],
            value=ast.Constant(value=None)
        )

    def _translate_NewExpr(self, node):
        callee = node.get("newType", "object")
        args = [self._translate(a) for a in node.get("args", [])]
        if callee in CONSTRUCTOR_DISPATCH:
            fn = ast.Name(id=CONSTRUCTOR_DISPATCH[callee], ctx=ast.Load())
            return ast.Call(func=fn, args=args, keywords=[])
        fn = ast.Name(id=callee, ctx=ast.Load())
        return ast.Call(func=fn, args=args, keywords=[])

    def _translate_NewArrayExpr(self, node):
        size = self._translate(node["size"])
        return ast.BinOp(
            left=ast.List(elts=[ast.Constant(value=0)], ctx=ast.Load()),
            op=ast.Mult(),
            right=size
        )

    def _translate_DecltypeExpr(self, node):
        return self._translate(node["expr"])

    def _as_store(self, expr):
        if isinstance(expr, ast.Name):
            return ast.Name(id=expr.id, ctx=ast.Store())
        if isinstance(expr, ast.Subscript):
            return ast.Subscript(value=expr.value, slice=expr.slice, ctx=ast.Store())
        if isinstance(expr, ast.Attribute):
            return ast.Attribute(value=expr.value, attr=expr.attr, ctx=ast.Store())
        return expr

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
        elif left.get("type") == "DerefExpr":
            target = ast.Name(id="_deref_target", ctx=ast.Store())
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

        if op_name == "SLASH":
            return ast.BinOp(left=left, op=ast.FloorDiv(), right=right)

        return ast.BinOp(left=left, op=py_op, right=right)

    def _translate_UnaryExpr(self, node):
        op_name = node["op"]
        operand = self._translate(node["expr"])
        py_op   = UNARY_OP_MAP.get(op_name)
        if py_op is None:
            raise NotImplementedError(f"Unsupported unary operator: '{op_name}'")
        return ast.UnaryOp(op=py_op, operand=operand)

    def _translate_DerefExpr(self, node):
        return self._translate(node["expr"])

    def _translate_AddressOfExpr(self, node):
        return self._translate(node["expr"])

    def _translate_UpdateExpr(self, node):
        target = node["expr"]
        if target.get("type") not in ("Identifier", "IndexExpr", "MemberAccess"):
            raise NotImplementedError("++/-- only on identifiers/indices/members")

        if target["type"] == "Identifier":
            name = target["name"]
            lhs = ast.Name(id=name, ctx=ast.Store())
            rhs_load = ast.Name(id=name, ctx=ast.Load())
        elif target["type"] == "MemberAccess":
            obj = self._translate(target["object"])
            lhs = ast.Attribute(value=obj, attr=target["member"], ctx=ast.Store())
            rhs_load = ast.Attribute(value=self._translate(target["object"]), attr=target["member"], ctx=ast.Load())
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
        return self._translate(node["expr"])

    def _translate_NumberLiteral(self, node):
        raw = node["value"]
        if raw.startswith('0x') or raw.startswith('0X'):
            clean = raw.rstrip('uUlL')
            try:
                return ast.Constant(value=int(clean, 16))
            except ValueError:
                pass
        if raw.startswith('0b') or raw.startswith('0B'):
            clean = raw.rstrip('uUlL')
            try:
                return ast.Constant(value=int(clean, 2))
            except ValueError:
                pass
        raw_clean = raw.rstrip('uUlLfF')
        try:
            return ast.Constant(value=int(raw_clean))
        except ValueError:
            pass
        try:
            return ast.Constant(value=float(raw_clean))
        except ValueError:
            return ast.Constant(value=0)

    def _translate_StringLiteral(self, node):
        return ast.Constant(value=node["value"])

    def _translate_CharLiteral(self, node):
        return ast.Constant(value=node["value"])

    def _translate_Identifier(self, node):
        name = node["name"]
        special = {
            "nullptr":  ast.Constant(value=None),
            "null":     ast.Constant(value=None),
            "true":     ast.Constant(value=True),
            "false":    ast.Constant(value=False),
            "INT_MAX":  ast.Name(id="INT_MAX", ctx=ast.Load()),
            "INT_MIN":  ast.Name(id="INT_MIN", ctx=ast.Load()),
            "LONG_MAX": ast.Name(id="LONG_MAX", ctx=ast.Load()),
            "LONG_MIN": ast.Name(id="LONG_MIN", ctx=ast.Load()),
            "UINT_MAX": ast.Name(id="UINT_MAX", ctx=ast.Load()),
            "SIZE_MAX": ast.Name(id="SIZE_MAX", ctx=ast.Load()),
            "DBL_MAX":  ast.Name(id="DBL_MAX", ctx=ast.Load()),
            "FLT_MAX":  ast.Name(id="FLT_MAX", ctx=ast.Load()),
            "M_PI":     ast.Name(id="M_PI", ctx=ast.Load()),
            "M_E":      ast.Name(id="M_E", ctx=ast.Load()),
            "M_SQRT2":  ast.Name(id="M_SQRT2", ctx=ast.Load()),
            "endl":     ast.Constant(value="\n"),
            "cin":      ast.Name(id="sys.stdin", ctx=ast.Load()),
            "cout":     ast.Name(id="sys.stdout", ctx=ast.Load()),
            "cerr":     ast.Name(id="sys.stderr", ctx=ast.Load()),
            "EOF":      ast.Name(id="EOF_VAL", ctx=ast.Load()),
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
        if member == "has_value":
            return ast.Call(
                func=ast.Name(id="_optional_has_value", ctx=ast.Load()),
                args=[obj], keywords=[]
            )
        if member == "value":
            return ast.Call(
                func=ast.Name(id="_optional_value", ctx=ast.Load()),
                args=[obj], keywords=[]
            )
        if member == "data":
            return obj
        if member == "c_str":
            return obj
        return ast.Attribute(value=obj, attr=member, ctx=ast.Load())

    def _translate_MethodCall(self, node):
        obj    = self._translate(node["object"])
        method = node["method"]
        args   = [self._translate(a) for a in node.get("args", [])]

        if method in ("size", "length"):
            return ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[obj], keywords=[])

        if method == "empty":
            return ast.Compare(
                left=ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[obj], keywords=[]),
                ops=[ast.Eq()],
                comparators=[ast.Constant(value=0)]
            )

        if method == "at":
            return ast.Subscript(value=obj, slice=args[0], ctx=ast.Load())

        if method == "first":
            return ast.Subscript(value=obj, slice=ast.Constant(value=0), ctx=ast.Load())

        if method == "second":
            return ast.Subscript(value=obj, slice=ast.Constant(value=1), ctx=ast.Load())

        if method == "count":
            return ast.Compare(left=args[0], ops=[ast.In()], comparators=[obj])

        if method == "find":
            return ast.Compare(left=args[0], ops=[ast.In()], comparators=[obj])

        if method == "contains":
            return ast.Compare(left=args[0], ops=[ast.In()], comparators=[obj])

        if method in ("starts_with", "startswith"):
            return ast.Call(
                func=ast.Attribute(value=obj, attr="startswith", ctx=ast.Load()),
                args=args, keywords=[]
            )

        if method in ("ends_with", "endswith"):
            return ast.Call(
                func=ast.Attribute(value=obj, attr="endswith", ctx=ast.Load()),
                args=args, keywords=[]
            )

        if method == "push_back":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="append", ctx=ast.Load()),
                args=args, keywords=[]
            )

        if method == "emplace_back":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="append", ctx=ast.Load()),
                args=[ast.List(elts=args, ctx=ast.Load()) if len(args) > 1 else (args[0] if args else ast.Constant(value=None))],
                keywords=[]
            )

        if method == "pop_back":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="pop", ctx=ast.Load()),
                args=[], keywords=[]
            )

        if method == "push_front":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="insert", ctx=ast.Load()),
                args=[ast.Constant(value=0)] + args, keywords=[]
            )

        if method == "pop_front":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="popleft", ctx=ast.Load()),
                args=[], keywords=[]
            )

        if method in ("push", "emplace"):
            return ast.Call(
                func=ast.Attribute(value=obj, attr="append", ctx=ast.Load()),
                args=args, keywords=[]
            )

        if method == "pop":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="pop", ctx=ast.Load()),
                args=[], keywords=[]
            )

        if method == "top":
            return ast.Subscript(
                value=obj,
                slice=ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=1)),
                ctx=ast.Load()
            )

        if method == "front":
            return ast.Subscript(value=obj, slice=ast.Constant(value=0), ctx=ast.Load())

        if method == "back":
            return ast.Subscript(
                value=obj,
                slice=ast.UnaryOp(op=ast.USub(), operand=ast.Constant(value=1)),
                ctx=ast.Load()
            )

        if method == "insert":
            if len(args) == 1:
                return ast.Call(
                    func=ast.Attribute(value=obj, attr="add", ctx=ast.Load()),
                    args=args, keywords=[]
                )
            else:
                return ast.Call(
                    func=ast.Attribute(value=obj, attr="insert", ctx=ast.Load()),
                    args=args, keywords=[]
                )

        if method == "erase":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="pop", ctx=ast.Load()),
                args=args, keywords=[]
            )

        if method == "clear":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="clear", ctx=ast.Load()),
                args=[], keywords=[]
            )

        if method == "resize":
            n = args[0]
            fill = args[1] if len(args) > 1 else ast.Constant(value=0)
            extend_call = ast.Call(
                func=ast.Attribute(value=obj, attr="extend", ctx=ast.Load()),
                args=[ast.BinOp(
                    left=ast.List(elts=[fill], ctx=ast.Load()),
                    op=ast.Mult(),
                    right=ast.Call(
                        func=ast.Name(id="max", ctx=ast.Load()),
                        args=[ast.Constant(value=0), ast.BinOp(
                            left=n,
                            op=ast.Sub(),
                            right=ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[obj], keywords=[])
                        )],
                        keywords=[]
                    )
                )],
                keywords=[]
            )
            return extend_call

        if method in ("reserve", "shrink_to_fit"):
            return ast.Constant(value=None)

        if method == "sort":
            if args:
                return ast.Call(
                    func=ast.Attribute(value=obj, attr="sort", ctx=ast.Load()),
                    args=[], keywords=[ast.keyword(arg="key", value=args[0])]
                )
            return ast.Call(
                func=ast.Attribute(value=obj, attr="sort", ctx=ast.Load()),
                args=[], keywords=[]
            )

        if method == "reverse":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="reverse", ctx=ast.Load()),
                args=[], keywords=[]
            )

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

        if method == "find_first_of":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="find", ctx=ast.Load()),
                args=args, keywords=[]
            )

        if method == "find_last_of":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="rfind", ctx=ast.Load()),
                args=args, keywords=[]
            )

        if method == "replace":
            if len(args) >= 3:
                return ast.Call(
                    func=ast.Attribute(value=obj, attr="replace", ctx=ast.Load()),
                    args=[args[-2], args[-1]], keywords=[]
                )
            return ast.Call(
                func=ast.Attribute(value=obj, attr="replace", ctx=ast.Load()),
                args=args, keywords=[]
            )

        if method == "c_str":
            return obj

        if method == "data":
            return obj

        if method == "append":
            return ast.Call(
                func=ast.Attribute(value=obj, attr="__add__", ctx=ast.Load()),
                args=args, keywords=[]
            )

        if method == "has_value":
            return ast.Call(
                func=ast.Name(id="_optional_has_value", ctx=ast.Load()),
                args=[obj], keywords=[]
            )

        if method == "value":
            return ast.Call(
                func=ast.Name(id="_optional_value", ctx=ast.Load()),
                args=[obj], keywords=[]
            )

        if method == "value_or":
            return ast.Call(
                func=ast.Name(id="_optional_value_or", ctx=ast.Load()),
                args=[obj] + args, keywords=[]
            )

        if method == "reset":
            return ast.Assign(
                targets=[self._as_store(obj)],
                value=ast.Constant(value=None)
            )

        if method == "get":
            if args:
                return ast.Subscript(value=obj, slice=args[0], ctx=ast.Load())
            return ast.Subscript(value=obj, slice=ast.Constant(value=0), ctx=ast.Load())

        if method == "swap":
            if args:
                return ast.Call(
                    func=ast.Name(id="_swap", ctx=ast.Load()),
                    args=[obj, args[0]], keywords=[]
                )

        if method in ("begin", "cbegin"):
            return ast.Constant(value=0)

        if method in ("end", "cend"):
            return ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[obj], keywords=[])

        if method in ("rbegin", "rend"):
            return ast.Constant(value=0)

        if method == "compare":
            return ast.Call(
                func=ast.Name(id="_cmp", ctx=ast.Load()),
                args=[obj] + args, keywords=[]
            )

        if method == "assign":
            return ast.BinOp(
                left=ast.List(elts=[args[1]] if len(args) > 1 else [], ctx=ast.Load()),
                op=ast.Mult(),
                right=args[0] if args else ast.Constant(value=0)
            )

        if method == "capacity":
            return ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[obj], keywords=[])

        return ast.Call(
            func=ast.Attribute(value=obj, attr=method, ctx=ast.Load()),
            args=args, keywords=[]
        )

    def _translate_CallExpr(self, node):
        callee = node["callee"]
        args   = [self._translate(a) for a in node.get("args", [])]

        if callee in CONSTRUCTOR_DISPATCH:
            fn = ast.Name(id=CONSTRUCTOR_DISPATCH[callee], ctx=ast.Load())
            return ast.Call(func=fn, args=args, keywords=[])

        if callee in FREE_FUNC_DISPATCH:
            mapped = FREE_FUNC_DISPATCH[callee]
            if mapped is None:
                return ast.Constant(value=None)
            fn = ast.Name(id=mapped, ctx=ast.Load())
            return ast.Call(func=fn, args=args, keywords=[])

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

        if callee == "get":
            if len(args) >= 2:
                return ast.Subscript(value=args[1], slice=args[0], ctx=ast.Load())
            if len(args) == 1:
                return ast.Subscript(value=args[0], slice=ast.Constant(value=0), ctx=ast.Load())
            return ast.Constant(value=None)

        if callee == "tie":
            return ast.Tuple(elts=args, ctx=ast.Store())

        if callee == "ignore":
            return ast.Constant(value=None)

        fn = ast.Name(id=callee, ctx=ast.Load())
        return ast.Call(func=fn, args=args, keywords=[])

    def _translate_InitializerList(self, node):
        elements = [self._translate(e) for e in node.get("elements", [])]
        if elements and all(isinstance(e, ast.Constant) and isinstance(e.value, (int, float)) for e in elements):
            return ast.List(elts=elements, ctx=ast.Load())
        return ast.List(elts=elements, ctx=ast.Load())

    def _translate_ExprList(self, node):
        exprs = node.get("exprs", [])
        if not exprs:
            return ast.Constant(value=None)
        last = self._translate(exprs[-1])
        return last


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
