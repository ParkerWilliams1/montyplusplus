import ast
import dis
from types import CodeType

class CppNode:
    def __init__(self, kind, **kwargs):
        self.kind = kind
        self.__dict__.update(kwargs)

class CppToPythonBytecode:
    def __init__(self, cpp_ast_root):
        self.root = cpp_ast_root
        self.env = {}            # maps C++ identifiers -> Python names
        self.indent = 0          # debug printing indent

    def debug(self, msg):
        print("  " * self.indent + msg)

    def compile(self):
        py_ast = self.translate(self.root)
        py_module = ast.Module(body=[py_ast], type_ignores=[])
        ast.fix_missing_locations(py_module)
        code_obj = compile(py_module, "<cpp_interpreter>", "exec")
        return code_obj

    def translate(self, node):
        self.debug(f"Translating node: {node.kind}")
        self.indent += 1

        if node.kind == "FunctionDecl":
            args = ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg=name) for name in node.params],
                kwonlyargs=[],
                defaults=[]
            )
            body = [self.translate(stmt) for stmt in node.body]
            fn = ast.FunctionDef(
                name=node.name,
                args=args,
                body=body,
                decorator_list=[]
            )
            self.indent -= 1
            return fn

        elif node.kind == "VarDecl":
            target = ast.Name(id=node.name, ctx=ast.Store())
            value = self.translate(node.value)
            assign = ast.Assign(targets=[target], value=value)
            self.env[node.name] = node.name
            self.indent -= 1
            return assign

        elif node.kind == "ReturnStmt":
            val = self.translate(node.expr)
            ret = ast.Return(value=val)
            self.indent -= 1
            return ret

        elif node.kind == "BinaryOperator":
            op_map = {
                "+": ast.Add(),
                "-": ast.Sub(),
                "*": ast.Mult(),
                "/": ast.Div()
            }
            py_op = op_map.get(node.op)
            left = self.translate(node.left)
            right = self.translate(node.right)
            expr = ast.BinOp(left=left, op=py_op, right=right)
            self.indent -= 1
            return expr

        elif node.kind == "IntegerLiteral":
            const = ast.Constant(value=node.value)
            self.indent -= 1
            return const

        elif node.kind == "Identifier":
            name = ast.Name(id=node.spelling, ctx=ast.Load())
            self.indent -= 1
            return name

        elif node.kind == "CallExpr":
            func = ast.Name(id=node.callee, ctx=ast.Load())
            args = [self.translate(a) for a in node.args]
            call = ast.Call(func=func, args=args, keywords=[])
            self.indent -= 1
            return call

        else:
            self.indent -= 1
            raise NotImplementedError(f"Unsupported C++ AST node: {node.kind}")

    def dump_python_ast(self):
        py_ast = self.translate(self.root)
        print(ast.dump(py_ast, indent=2))
