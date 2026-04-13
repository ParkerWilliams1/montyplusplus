from tokens import Token, TokenType
from typing import List, Optional

# C++ type keywords that can start a declaration
TYPE_TOKENS = (
    TokenType.INT, TokenType.VOID, TokenType.BOOL,
    TokenType.CHAR, TokenType.FLOAT,
)

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current = self.tokens[self.pos] if tokens else None

    # ----------------------------
    # Utility Methods
    # ----------------------------
    def peek(self, offset=0) -> Token:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def advance(self) -> Token:
        token = self.tokens[self.pos]
        if token.type != TokenType.EOF:
            self.pos += 1
            self.current = self.tokens[self.pos] if self.pos < len(self.tokens) else None
        return token

    def match(self, *types) -> bool:
        if self.current and self.current.type in types:
            self.advance()
            return True
        return False

    def expect(self, type_: TokenType) -> Token:
        if self.current and self.current.type == type_:
            return self.advance()
        raise SyntaxError(
            f"Expected {type_.name}, found {self.current} at pos {self.pos}"
        )

    def is_type_token(self):
        """Check if current token is a type keyword (possibly followed by <...> template)."""
        return self.current and self.current.type in TYPE_TOKENS

    def is_identifier_type(self):
        """Check if current looks like a complex type name (vector, string, etc.)."""
        if not self.current or self.current.type != TokenType.IDENTIFIER:
            return False
        type_names = {
            'vector', 'string', 'map', 'unordered_map', 'set', 'unordered_set',
            'pair', 'stack', 'queue', 'deque', 'priority_queue', 'list',
            'auto',
        }
        return self.current.value in type_names

    def skip_template_args(self):
        """Skip over <...> template arguments."""
        if self.current and self.current.type == TokenType.LESS:
            depth = 0
            while self.current and self.current.type != TokenType.EOF:
                if self.current.type == TokenType.LESS:
                    depth += 1
                    self.advance()
                elif self.current.type == TokenType.GREATER:
                    depth -= 1
                    self.advance()
                    if depth == 0:
                        break
                elif self.current.type == TokenType.SHIFT_RIGHT:
                    # >> can close two levels in C++
                    depth -= 2
                    self.advance()
                    if depth <= 0:
                        break
                else:
                    self.advance()

    def parse_type_name(self) -> str:
        """Parse a type name including templates like vector<int>, returning string."""
        if self.current.type in TYPE_TOKENS:
            type_str = self.advance().value
        elif self.current.type == TokenType.IDENTIFIER:
            type_str = self.advance().value
        else:
            raise SyntaxError(f"Expected type, got {self.current}")
        
        # Handle pointer/reference qualifiers
        while self.current and self.current.type in (TokenType.STAR, TokenType.BITWISE_AND):
            self.advance()

        # Handle template args
        if self.current and self.current.type == TokenType.LESS:
            self.skip_template_args()
        
        # Handle pointer/reference after template
        while self.current and self.current.type in (TokenType.STAR, TokenType.BITWISE_AND):
            self.advance()

        return type_str

    # ----------------------------
    # Top-level parse
    # ----------------------------
    def parse(self):
        ast = []
        while self.current and self.current.type != TokenType.EOF:
            node = self.parse_top_level()
            if node:
                ast.append(node)
        return ast

    def parse_top_level(self):
        # Skip class/struct definitions for now
        if self.current.type == TokenType.IDENTIFIER and self.current.value in ('class', 'struct'):
            self.skip_class_or_struct()
            return None
        
        # Skip standalone semicolons
        if self.match(TokenType.SEMICOLON):
            return None

        # Type + name -> function or variable
        if self.is_type_token() or self.is_identifier_type():
            return self.parse_function_or_variable()
        
        raise SyntaxError(f"Unexpected token at top level: {self.current}")

    def skip_class_or_struct(self):
        """Skip over a class/struct definition."""
        while self.current and self.current.type != TokenType.LBRACE:
            self.advance()
        depth = 0
        while self.current and self.current.type != TokenType.EOF:
            if self.current.type == TokenType.LBRACE:
                depth += 1
            elif self.current.type == TokenType.RBRACE:
                depth -= 1
                if depth == 0:
                    self.advance()
                    self.match(TokenType.SEMICOLON)
                    return
            self.advance()

    # ----------------------------
    # Declarations
    # ----------------------------
    def parse_function_or_variable(self):
        # Parse type
        type_name = self.parse_type_name()

        # Might be constructor name (same as class) - skip
        if not self.current or self.current.type not in (TokenType.IDENTIFIER,):
            raise SyntaxError(f"Expected identifier after type, got {self.current}")

        name = self.advance().value

        # Function call style (constructors at top level - skip)
        if self.match(TokenType.LPAREN):
            params = self.parse_param_list()
            self.expect(TokenType.RPAREN)
            
            # Function definition
            if self.current and self.current.type == TokenType.LBRACE:
                body = self.parse_block()
                return {
                    "type": "FunctionDecl",
                    "returnType": type_name,
                    "name": name,
                    "params": params,
                    "body": body
                }
            # Declaration only (;) - skip
            self.match(TokenType.SEMICOLON)
            return None

        # Array type: int arr[]  or  int arr[n]
        array_size = None
        if self.current and self.current.type == TokenType.LBRACKET:
            self.advance()
            if self.current.type != TokenType.RBRACKET:
                array_size = self.parse_expression()
            self.expect(TokenType.RBRACKET)

        # Variable declaration
        init = None
        if self.match(TokenType.ASSIGN):
            init = self.parse_expression()
        
        # Handle multiple declarators: int a, b, c;
        decls = [{"type": "VarDecl", "varType": type_name, "name": name, "init": init, "arraySize": array_size}]
        while self.match(TokenType.COMMA):
            # Each following one might also have array brackets and init
            extra_name = self.advance().value if self.current.type == TokenType.IDENTIFIER else None
            if not extra_name:
                break
            extra_array = None
            if self.current and self.current.type == TokenType.LBRACKET:
                self.advance()
                if self.current.type != TokenType.RBRACKET:
                    extra_array = self.parse_expression()
                self.expect(TokenType.RBRACKET)
            extra_init = None
            if self.match(TokenType.ASSIGN):
                extra_init = self.parse_expression()
            decls.append({"type": "VarDecl", "varType": type_name, "name": extra_name, "init": extra_init, "arraySize": extra_array})
        
        self.expect(TokenType.SEMICOLON)
        return decls[0] if len(decls) == 1 else {"type": "MultiVarDecl", "decls": decls}

    def parse_param_list(self):
        params = []
        if self.current.type == TokenType.RPAREN:
            return params
        while True:
            if not (self.is_type_token() or self.is_identifier_type()):
                break
            param_type = self.parse_type_name()
            if not self.current or self.current.type != TokenType.IDENTIFIER:
                break
            param_name = self.advance().value
            # Handle array params
            if self.current and self.current.type == TokenType.LBRACKET:
                self.advance()
                if self.current.type != TokenType.RBRACKET:
                    self.parse_expression()  # skip size
                self.expect(TokenType.RBRACKET)
            params.append({"type": param_type, "name": param_name})
            if not self.match(TokenType.COMMA):
                break
        return params

    # ----------------------------
    # Statements
    # ----------------------------
    def parse_block(self):
        self.expect(TokenType.LBRACE)
        statements = []
        while self.current and self.current.type != TokenType.RBRACE:
            stmts = self.parse_statement()
            if isinstance(stmts, list):
                statements.extend(stmts)
            elif stmts is not None:
                statements.append(stmts)
        self.expect(TokenType.RBRACE)
        return statements

    def parse_statement(self):
        # Empty statement
        if self.match(TokenType.SEMICOLON):
            return None

        if self.match(TokenType.RETURN):
            if self.current.type == TokenType.SEMICOLON:
                self.advance()
                return {"type": "ReturnStmt", "expr": None}
            expr = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return {"type": "ReturnStmt", "expr": expr}

        if self.match(TokenType.IF):
            return self.parse_if_statement()

        if self.match(TokenType.FOR):
            return self.parse_for_statement()

        if self.match(TokenType.WHILE):
            return self.parse_while_statement()

        if self.current.type == TokenType.LBRACE:
            body = self.parse_block()
            return {"type": "BlockStmt", "body": body}

        # break / continue
        if self.current.type == TokenType.IDENTIFIER and self.current.value in ('break', 'continue'):
            kw = self.advance().value
            self.expect(TokenType.SEMICOLON)
            return {"type": "BreakContinueStmt", "keyword": kw}

        # Variable declaration
        if self.is_type_token() or self.is_identifier_type():
            # Lookahead: type IDENTIFIER (not LPAREN at top of expression)
            result = self.parse_function_or_variable()
            return result

        # Expression statement
        expr = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        return {"type": "ExprStmt", "expr": expr}

    def parse_if_statement(self):
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)

        then_branch = self.parse_statement()
        if not isinstance(then_branch, list):
            then_branch = [then_branch] if then_branch else [{"type": "NoOp"}]

        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.parse_statement()
            if not isinstance(else_branch, list):
                else_branch = [else_branch] if else_branch else [{"type": "NoOp"}]

        return {"type": "IfStmt", "condition": condition, "then": then_branch, "else": else_branch}

    def parse_while_statement(self):
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        body = self.parse_statement()
        if not isinstance(body, list):
            body = [body] if body else []
        return {"type": "WhileStmt", "condition": condition, "body": body}

    def parse_for_statement(self):
        self.expect(TokenType.LPAREN)

        # init
        init = None
        if self.current.type != TokenType.SEMICOLON:
            if self.is_type_token() or self.is_identifier_type():
                init = self.parse_function_or_variable()
            else:
                init = self.parse_expression()
                self.expect(TokenType.SEMICOLON)
        else:
            self.expect(TokenType.SEMICOLON)

        # condition
        condition = None
        if self.current.type != TokenType.SEMICOLON:
            condition = self.parse_expression()
        self.expect(TokenType.SEMICOLON)

        # update
        update = None
        if self.current.type != TokenType.RPAREN:
            update = self.parse_expression()
        self.expect(TokenType.RPAREN)

        body = self.parse_statement()
        if not isinstance(body, list):
            body = [body] if body else []

        return {"type": "ForStmt", "init": init, "condition": condition, "update": update, "body": body}

    # ----------------------------
    # Expressions
    # ----------------------------
    def parse_expression(self):
        return self.parse_ternary()

    def parse_ternary(self):
        expr = self.parse_assignment()
        if self.match(TokenType.QUESTION):
            then_expr = self.parse_expression()
            self.expect(TokenType.COLON)
            else_expr = self.parse_ternary()
            return {"type": "TernaryExpr", "condition": expr, "then": then_expr, "else": else_expr}
        return expr

    def parse_assignment(self):
        left = self.parse_logical_or()
        
        if self.current and self.current.type == TokenType.ASSIGN:
            op_token = self.advance()
            right = self.parse_assignment()
            op_str = op_token.value  # could be =, +=, -=, etc.
            
            if op_str in ('+=', '-=', '*=', '/='):
                # Desugar: x += y  =>  x = x + y
                op_map = {'+=': 'PLUS', '-=': 'MINUS', '*=': 'STAR', '/=': 'SLASH'}
                return {
                    "type": "AssignExpr",
                    "left": left,
                    "right": {
                        "type": "BinaryExpr",
                        "op": op_map[op_str],
                        "left": left,
                        "right": right
                    }
                }
            return {"type": "AssignExpr", "left": left, "right": right}
        return left

    def parse_logical_or(self):
        expr = self.parse_logical_and()
        while self.match(TokenType.OR):
            right = self.parse_logical_and()
            expr = {"type": "BinaryExpr", "op": "OR", "left": expr, "right": right}
        return expr

    def parse_logical_and(self):
        expr = self.parse_bitwise_or()
        while self.match(TokenType.AND):
            right = self.parse_bitwise_or()
            expr = {"type": "BinaryExpr", "op": "AND", "left": expr, "right": right}
        return expr

    def parse_bitwise_or(self):
        expr = self.parse_bitwise_xor()
        while self.match(TokenType.BITWISE_OR):
            right = self.parse_bitwise_xor()
            expr = {"type": "BinaryExpr", "op": "BITWISE_OR", "left": expr, "right": right}
        return expr

    def parse_bitwise_xor(self):
        expr = self.parse_bitwise_and()
        while self.match(TokenType.BITWISE_XOR):
            right = self.parse_bitwise_and()
            expr = {"type": "BinaryExpr", "op": "BITWISE_XOR", "left": expr, "right": right}
        return expr

    def parse_bitwise_and(self):
        expr = self.parse_equality()
        while self.match(TokenType.BITWISE_AND):
            right = self.parse_equality()
            expr = {"type": "BinaryExpr", "op": "BITWISE_AND", "left": expr, "right": right}
        return expr

    def parse_equality(self):
        expr = self.parse_relational()
        while self.match(TokenType.EQUAL, TokenType.NOT_EQUAL):
            op = self.tokens[self.pos - 1].type
            right = self.parse_relational()
            expr = {"type": "BinaryExpr", "op": op.name, "left": expr, "right": right}
        return expr

    def parse_relational(self):
        expr = self.parse_shift()
        while self.match(TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL):
            op = self.tokens[self.pos - 1].type
            right = self.parse_shift()
            expr = {"type": "BinaryExpr", "op": op.name, "left": expr, "right": right}
        return expr

    def parse_shift(self):
        expr = self.parse_term()
        while self.match(TokenType.SHIFT_LEFT, TokenType.SHIFT_RIGHT):
            op = self.tokens[self.pos - 1].type
            right = self.parse_term()
            expr = {"type": "BinaryExpr", "op": op.name, "left": expr, "right": right}
        return expr

    def parse_term(self):
        expr = self.parse_factor()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.tokens[self.pos - 1].type
            right = self.parse_factor()
            expr = {"type": "BinaryExpr", "op": op.name, "left": expr, "right": right}
        return expr

    def parse_factor(self):
        expr = self.parse_unary()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.tokens[self.pos - 1].type
            right = self.parse_unary()
            expr = {"type": "BinaryExpr", "op": op.name, "left": expr, "right": right}
        return expr

    def parse_unary(self):
        if self.match(TokenType.INCREMENT, TokenType.DECREMENT):
            op = self.tokens[self.pos - 1].type
            operand = self.parse_unary()
            return {"type": "UpdateExpr", "op": op.name, "expr": operand, "prefix": True}

        if self.match(TokenType.PLUS, TokenType.MINUS, TokenType.LOGICAL_NOT, TokenType.BITWISE_NOT):
            op = self.tokens[self.pos - 1].type
            operand = self.parse_unary()
            return {"type": "UnaryExpr", "op": op.name, "expr": operand}

        # Cast: (int) expr  or  (type) expr
        if (self.current and self.current.type == TokenType.LPAREN
                and self.peek(1) and self.peek(1).type in TYPE_TOKENS):
            # Check it's actually a cast (not a grouped expr)
            # Simple heuristic: (type) 
            saved_pos = self.pos
            self.advance()  # consume (
            if self.is_type_token():
                self.parse_type_name()
                if self.current and self.current.type == TokenType.RPAREN:
                    self.advance()  # consume )
                    operand = self.parse_unary()
                    return {"type": "CastExpr", "expr": operand}
            # Not a cast, restore
            self.pos = saved_pos
            self.current = self.tokens[self.pos]

        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()

        while True:
            if self.current and self.current.type in (TokenType.INCREMENT, TokenType.DECREMENT):
                op = self.advance().type
                expr = {"type": "UpdateExpr", "op": op.name, "expr": expr, "prefix": False}

            elif self.current and self.current.type == TokenType.LBRACKET:
                self.advance()
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET)
                expr = {"type": "IndexExpr", "array": expr, "index": index}

            elif self.current and self.current.type == TokenType.DOT:
                self.advance()
                method = self.advance().value
                if self.current and self.current.type == TokenType.LPAREN:
                    self.advance()
                    args = []
                    if self.current.type != TokenType.RPAREN:
                        while True:
                            args.append(self.parse_expression())
                            if not self.match(TokenType.COMMA):
                                break
                    self.expect(TokenType.RPAREN)
                    expr = {"type": "MethodCall", "object": expr, "method": method, "args": args}
                else:
                    expr = {"type": "MemberAccess", "object": expr, "member": method}

            elif self.current and self.current.type == TokenType.ARROW:
                self.advance()
                member = self.advance().value
                if self.current and self.current.type == TokenType.LPAREN:
                    self.advance()
                    args = []
                    if self.current.type != TokenType.RPAREN:
                        while True:
                            args.append(self.parse_expression())
                            if not self.match(TokenType.COMMA):
                                break
                    self.expect(TokenType.RPAREN)
                    expr = {"type": "MethodCall", "object": expr, "method": member, "args": args}
                else:
                    expr = {"type": "MemberAccess", "object": expr, "member": member}

            elif self.current and self.current.type == TokenType.SCOPE:
                # e.g. std::vector or numeric_limits<int>::max()
                self.advance()
                member = self.advance().value if self.current else ""
                if self.current and self.current.type == TokenType.LPAREN:
                    self.advance()
                    args = []
                    if self.current.type != TokenType.RPAREN:
                        while True:
                            args.append(self.parse_expression())
                            if not self.match(TokenType.COMMA):
                                break
                    self.expect(TokenType.RPAREN)
                    expr = {"type": "CallExpr", "callee": member, "args": args}
                else:
                    expr = {"type": "Identifier", "name": member}
            else:
                break

        return expr

    def parse_primary(self):
        token = self.advance()

        if token.type == TokenType.NUMBER:
            return {"type": "NumberLiteral", "value": token.value}

        if token.type == TokenType.STRING:
            return {"type": "StringLiteral", "value": token.value[1:-1]}  # strip quotes

        if token.type == TokenType.CHAR:
            # 'c' -> ord value
            inner = token.value[1:-1]
            if inner.startswith('\\'):
                escapes = {'\\n': '\n', '\\t': '\t', '\\r': '\r', '\\\\': '\\', "\\'": "'", '\\"': '"', '\\0': '\0'}
                char_val = escapes.get(inner, inner[1:])
            else:
                char_val = inner
            return {"type": "CharLiteral", "value": char_val}

        if token.type == TokenType.IDENTIFIER:
            name = token.value

            # Function call
            if self.current and self.current.type == TokenType.LPAREN:
                self.advance()
                args = []
                if self.current.type != TokenType.RPAREN:
                    while True:
                        args.append(self.parse_expression())
                        if not self.match(TokenType.COMMA):
                            break
                self.expect(TokenType.RPAREN)
                return {"type": "CallExpr", "callee": name, "args": args}

            # Array initializer: vector<int> v = {1,2,3} -- handled in VarDecl
            return {"type": "Identifier", "name": name}

        if token.type == TokenType.LPAREN:
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        if token.type == TokenType.LBRACE:
            # Initializer list: {1, 2, 3}
            elements = []
            while self.current and self.current.type != TokenType.RBRACE:
                elements.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
            self.expect(TokenType.RBRACE)
            return {"type": "InitializerList", "elements": elements}

        raise SyntaxError(f"Unexpected token in expression: {token}")