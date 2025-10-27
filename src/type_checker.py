from tokens import TokenType, Token

# ------------------------------
# AST Nodes
# ------------------------------

class Node:
    """Base class for all AST nodes."""
    pass

class Program(Node):
    def __init__(self, statements):
        self.statements = statements  # list of Node

class VarDecl(Node):
    def __init__(self, name: Token, var_type: TokenType, initializer: Node = None):
        self.name = name
        self.var_type = var_type
        self.initializer = initializer

class Assignment(Node):
    def __init__(self, target: Token, value: Node):
        self.target = target
        self.value = value

class BinaryOp(Node):
    def __init__(self, left: Node, op: Token, right: Node):
        self.left = left
        self.op = op
        self.right = right

class Literal(Node):
    def __init__(self, value):
        self.value = value

class Identifier(Node):
    def __init__(self, name: str):
        self.name = name

class FunctionDecl(Node):
    def __init__(self, name: str, return_type: TokenType, params: list, body: list):
        self.name = name
        self.return_type = return_type
        self.params = params  # list of (name: str, type: TokenType)
        self.body = body      # list of Node

class Return(Node):
    def __init__(self, value: Node = None):
        self.value = value


# ------------------------------
# Symbol Table
# ------------------------------

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def declare(self, name, type_):
        if name in self.scopes[-1]:
            raise TypeError(f"Variable '{name}' already declared in this scope.")
        self.scopes[-1][name] = type_

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise TypeError(f"Undeclared variable '{name}'.")


# ------------------------------
# Type Checker
# ------------------------------

class TypeChecker:
    def __init__(self):
        self.symbols = SymbolTable()
        self.current_function_type = None
        self.functions = {}

    def check(self, node: Node):
        match node:
            case Program():
                if not node.statements:
                    return None
                for stmt in node.statements:
                    self.check(stmt)
                return None

            case VarDecl():
                expr_type = self.check(node.initializer) if node.initializer else None
                if expr_type and expr_type != node.var_type:
                    raise TypeError(
                        f"Type mismatch: variable '{node.name.value}' declared as {node.var_type.name}, "
                        f"but assigned {expr_type.name}."
                    )
                self.symbols.declare(node.name.value, node.var_type)
                return node.var_type

            case Assignment():
                var_type = self.symbols.lookup(node.target.value)
                expr_type = self.check(node.value)

                # C++-style int→float promotion
                if {var_type, expr_type} <= {TokenType.INT, TokenType.FLOAT}:
                    return var_type

                if var_type != expr_type:
                    raise TypeError(
                        f"Type mismatch in assignment to '{node.target.value}': "
                        f"expected {var_type.name}, got {expr_type.name}."
                    )
                return var_type

            case BinaryOp():
                left_type = self.check(node.left)
                right_type = self.check(node.right)
                op = node.op.type

                if op in {TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH}:
                    if left_type not in {TokenType.INT, TokenType.FLOAT} or right_type not in {TokenType.INT, TokenType.FLOAT}:
                        raise TypeError(f"Invalid operand type for {op.name}: {left_type.name}, {right_type.name}")
                    if TokenType.FLOAT in {left_type, right_type}:
                        return TokenType.FLOAT
                    return TokenType.INT

                if op in {TokenType.EQUAL, TokenType.NOT_EQUAL,
                          TokenType.LESS, TokenType.LESS_EQUAL,
                          TokenType.GREATER, TokenType.GREATER_EQUAL}:
                    if left_type != right_type:
                        raise TypeError(f"Cannot compare {left_type.name} with {right_type.name}")
                    return TokenType.BOOL

                if op in {TokenType.AND, TokenType.OR}:
                    if left_type != TokenType.BOOL or right_type != TokenType.BOOL:
                        raise TypeError("Logical operators require bool operands.")
                    return TokenType.BOOL

                raise TypeError(f"Unknown operator: {op}")

            case Literal():
                val = node.value
                if isinstance(val, bool):
                    return TokenType.BOOL
                elif isinstance(val, int):
                    return TokenType.INT
                elif isinstance(val, float):
                    return TokenType.FLOAT
                elif isinstance(val, str):
                    if len(val) == 1:
                        return TokenType.CHAR
                    return TokenType.STRING
                else:
                    raise TypeError(f"Unsupported literal type: {val}")

            case Identifier():
                return self.symbols.lookup(node.name)

            case FunctionDecl():
                if node.name in self.functions:
                    raise TypeError(f"Function '{node.name}' already declared.")
                self.functions[node.name] = node.return_type

                self.symbols.enter_scope()
                prev_func = self.current_function_type
                self.current_function_type = node.return_type

                for param_name, param_type in node.params:
                    self.symbols.declare(param_name, param_type)

                for stmt in node.body:
                    self.check(stmt)

                self.current_function_type = prev_func
                self.symbols.exit_scope()
                return node.return_type

            case Return():
                if self.current_function_type is None:
                    raise TypeError("Return statement outside of function.")
                if node.value:
                    value_type = self.check(node.value)
                    if value_type != self.current_function_type:
                        raise TypeError(
                            f"Return type mismatch: expected {self.current_function_type.name}, "
                            f"got {value_type.name}"
                        )
                elif self.current_function_type != TokenType.VOID:
                    raise TypeError("Non-void function must return a value.")
                return self.current_function_type

            case _:
                raise TypeError(f"Unknown node type: {type(node).__name__}")



