from tokens import Token, TokenType
from typing import List, Optional

TYPE_TOKENS = (
    TokenType.INT, TokenType.VOID, TokenType.BOOL,
    TokenType.CHAR, TokenType.FLOAT,
)

STORAGE_QUALIFIERS = {'const', 'constexpr', 'static', 'inline', 'extern',
                      'virtual', 'override', 'final', 'explicit', 'mutable',
                      'volatile', 'register'}

COMPLEX_TYPE_NAMES = {
    'vector', 'string', 'map', 'unordered_map', 'set', 'unordered_set',
    'pair', 'tuple', 'optional', 'variant', 'any',
    'stack', 'queue', 'deque', 'priority_queue', 'list', 'forward_list',
    'multimap', 'unordered_multimap', 'multiset', 'unordered_multiset',
    'array', 'bitset', 'valarray', 'complex', 'function',
    'shared_ptr', 'unique_ptr', 'weak_ptr',
    'auto', 'decltype',
}


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current = self.tokens[self.pos] if tokens else None

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
        if self.current and self.current.type == TokenType.IDENTIFIER and self.current.value in STORAGE_QUALIFIERS:
            return True
        return self.current and self.current.type in TYPE_TOKENS

    def is_identifier_type(self):
        if not self.current or self.current.type != TokenType.IDENTIFIER:
            return False
        return self.current.value in COMPLEX_TYPE_NAMES

    def skip_template_args(self):
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
                    depth -= 2
                    self.advance()
                    if depth <= 0:
                        break
                else:
                    self.advance()

    def parse_type_name(self) -> str:
        while self.current and self.current.type == TokenType.IDENTIFIER and self.current.value in STORAGE_QUALIFIERS:
            self.advance()

        if self.current and self.current.type in TYPE_TOKENS:
            type_str = self.advance().value
        elif self.current and self.current.type == TokenType.IDENTIFIER:
            type_str = self.advance().value
        else:
            raise SyntaxError(f"Expected type, got {self.current}")

        while self.current and self.current.type in (TokenType.STAR, TokenType.BITWISE_AND):
            self.advance()

        if self.current and self.current.type == TokenType.LESS:
            self.skip_template_args()

        while self.current and self.current.type in (TokenType.STAR, TokenType.BITWISE_AND):
            self.advance()

        while self.current and self.current.type == TokenType.IDENTIFIER and self.current.value in STORAGE_QUALIFIERS:
            self.advance()

        return type_str

    def parse(self):
        ast = []
        while self.current and self.current.type != TokenType.EOF:
            node = self.parse_top_level()
            if node:
                ast.append(node)
        return ast

    def parse_top_level(self):
        if self.current.type == TokenType.IDENTIFIER and self.current.value in ('class', 'struct'):
            self.skip_class_or_struct()
            return None

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'namespace':
            return self.parse_namespace()

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'using':
            self.skip_to_semicolon()
            return None

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'typedef':
            self.skip_to_semicolon()
            return None

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'template':
            self.skip_template_decl()
            return self.parse_top_level()

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'enum':
            return self.parse_enum()

        if self.match(TokenType.SEMICOLON):
            return None

        if self.is_type_token() or self.is_identifier_type():
            return self.parse_function_or_variable()

        raise SyntaxError(f"Unexpected token at top level: {self.current}")

    def skip_to_semicolon(self):
        while self.current and self.current.type not in (TokenType.SEMICOLON, TokenType.EOF):
            self.advance()
        self.match(TokenType.SEMICOLON)

    def skip_template_decl(self):
        self.advance()
        if self.current and self.current.type == TokenType.LESS:
            self.skip_template_args()

    def parse_namespace(self):
        self.advance()
        if self.current and self.current.type == TokenType.IDENTIFIER:
            self.advance()
        if self.current and self.current.type == TokenType.SCOPE:
            self.advance()
            if self.current and self.current.type == TokenType.IDENTIFIER:
                self.advance()
        if self.current and self.current.type == TokenType.LBRACE:
            self.advance()
            stmts = []
            depth = 1
            saved_pos = self.pos
            while self.current and self.current.type != TokenType.EOF and depth > 0:
                if self.current.type == TokenType.LBRACE:
                    depth += 1
                    self.advance()
                elif self.current.type == TokenType.RBRACE:
                    depth -= 1
                    if depth == 0:
                        self.advance()
                        break
                    self.advance()
                else:
                    if depth == 1:
                        node = None
                        try:
                            node = self.parse_top_level()
                        except Exception:
                            self.advance()
                        if node:
                            stmts.append(node)
                    else:
                        self.advance()
            return {"type": "Namespace", "body": stmts} if stmts else None
        return None

    def parse_enum(self):
        self.advance()
        is_class = False
        if self.current and self.current.type == TokenType.IDENTIFIER and self.current.value in ('class', 'struct'):
            is_class = True
            self.advance()
        name = ""
        if self.current and self.current.type == TokenType.IDENTIFIER:
            name = self.advance().value
        if self.current and self.current.type == TokenType.COLON:
            self.advance()
            self.parse_type_name()
        if self.current and self.current.type == TokenType.LBRACE:
            self.advance()
            enumerators = []
            counter = 0
            while self.current and self.current.type != TokenType.RBRACE:
                if self.match(TokenType.COMMA):
                    continue
                if self.current.type == TokenType.IDENTIFIER:
                    ename = self.advance().value
                    val = counter
                    if self.match(TokenType.ASSIGN):
                        expr = self.parse_expression()
                        if expr.get("type") == "NumberLiteral":
                            val = int(expr["value"])
                    enumerators.append({"name": ename, "value": val})
                    counter = val + 1
                else:
                    self.advance()
            self.expect(TokenType.RBRACE)
            self.match(TokenType.SEMICOLON)
            return {"type": "EnumDecl", "name": name, "is_class": is_class, "enumerators": enumerators}
        self.match(TokenType.SEMICOLON)
        return None

    def skip_class_or_struct(self):
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

    def parse_function_or_variable(self):
        type_name = self.parse_type_name()

        if not self.current or self.current.type not in (TokenType.IDENTIFIER,):
            raise SyntaxError(f"Expected identifier after type, got {self.current}")

        name = self.advance().value

        if self.match(TokenType.LPAREN):
            params = self.parse_param_list()
            self.expect(TokenType.RPAREN)

            while self.current and self.current.type == TokenType.IDENTIFIER and self.current.value in (
                'const', 'noexcept', 'override', 'final', 'volatile'
            ):
                self.advance()

            if self.current and self.current.type == TokenType.LBRACE:
                body = self.parse_block()
                return {
                    "type": "FunctionDecl",
                    "returnType": type_name,
                    "name": name,
                    "params": params,
                    "body": body
                }
            self.match(TokenType.SEMICOLON)
            return None

        array_size = None
        if self.current and self.current.type == TokenType.LBRACKET:
            self.advance()
            if self.current.type != TokenType.RBRACKET:
                array_size = self.parse_expression()
            self.expect(TokenType.RBRACKET)

        init = None
        if self.match(TokenType.ASSIGN):
            init = self.parse_expression()

        if self.current and self.current.type == TokenType.LBRACE:
            init = self.parse_brace_initializer()

        decls = [{"type": "VarDecl", "varType": type_name, "name": name, "init": init, "arraySize": array_size}]
        while self.match(TokenType.COMMA):
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
            if self.current and self.current.type == TokenType.LBRACE:
                extra_init = self.parse_brace_initializer()
            decls.append({"type": "VarDecl", "varType": type_name, "name": extra_name, "init": extra_init, "arraySize": extra_array})

        self.expect(TokenType.SEMICOLON)
        return decls[0] if len(decls) == 1 else {"type": "MultiVarDecl", "decls": decls}

    def parse_brace_initializer(self):
        self.expect(TokenType.LBRACE)
        elements = []
        while self.current and self.current.type != TokenType.RBRACE:
            elements.append(self.parse_expression())
            if not self.match(TokenType.COMMA):
                break
        self.expect(TokenType.RBRACE)
        return {"type": "InitializerList", "elements": elements}

    def parse_param_list(self):
        params = []
        if self.current.type == TokenType.RPAREN:
            return params
        while True:
            if self.current and self.current.type == TokenType.ELLIPSIS:
                self.advance()
                params.append({"type": "...", "name": "args"})
                break
            if not (self.is_type_token() or self.is_identifier_type()):
                break
            param_type = self.parse_type_name()
            if not self.current or self.current.type not in (TokenType.IDENTIFIER, TokenType.RPAREN, TokenType.COMMA):
                break
            if self.current.type in (TokenType.RPAREN, TokenType.COMMA):
                params.append({"type": param_type, "name": f"_p{len(params)}"})
            else:
                param_name = self.advance().value
                if self.current and self.current.type == TokenType.LBRACKET:
                    self.advance()
                    if self.current.type != TokenType.RBRACKET:
                        self.parse_expression()
                    self.expect(TokenType.RBRACKET)
                if self.current and self.current.type == TokenType.ASSIGN:
                    self.advance()
                    default_val = self.parse_expression()
                    params.append({"type": param_type, "name": param_name, "default": default_val})
                else:
                    params.append({"type": param_type, "name": param_name})
            if not self.match(TokenType.COMMA):
                break
        return params

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

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'do':
            return self.parse_do_while_statement()

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'switch':
            return self.parse_switch_statement()

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'try':
            return self.parse_try_statement()

        if self.current.type == TokenType.LBRACE:
            body = self.parse_block()
            return {"type": "BlockStmt", "body": body}

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'break':
            self.advance()
            self.expect(TokenType.SEMICOLON)
            return {"type": "BreakContinueStmt", "keyword": "break"}

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'continue':
            self.advance()
            self.expect(TokenType.SEMICOLON)
            return {"type": "BreakContinueStmt", "keyword": "continue"}

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'throw':
            return self.parse_throw_statement()

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'goto':
            self.advance()
            if self.current and self.current.type == TokenType.IDENTIFIER:
                self.advance()
            self.expect(TokenType.SEMICOLON)
            return None

        if self.current.type == TokenType.IDENTIFIER and self.current.value in ('namespace', 'using', 'typedef'):
            self.skip_to_semicolon()
            return None

        if self.current.type == TokenType.IDENTIFIER and self.current.value == 'static_assert':
            self.advance()
            self.expect(TokenType.LPAREN)
            depth = 1
            while self.current and depth > 0:
                if self.current.type == TokenType.LPAREN:
                    depth += 1
                elif self.current.type == TokenType.RPAREN:
                    depth -= 1
                self.advance()
            self.match(TokenType.SEMICOLON)
            return None

        if self.is_type_token() or self.is_identifier_type():
            result = self.parse_function_or_variable()
            return result

        expr = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        return {"type": "ExprStmt", "expr": expr}

    def parse_if_statement(self):
        self.expect(TokenType.LPAREN)

        init_stmt = None
        if self._looks_like_init_statement():
            init_stmt = self.parse_function_or_variable()
            if isinstance(init_stmt, list):
                init_stmt = init_stmt[0] if init_stmt else None

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

        return {"type": "IfStmt", "condition": condition, "then": then_branch, "else": else_branch, "init": init_stmt}

    def _looks_like_init_statement(self):
        if not self.current:
            return False
        if self.current.type in TYPE_TOKENS:
            return True
        if self.current.type == TokenType.IDENTIFIER and self.current.value in COMPLEX_TYPE_NAMES:
            return True
        return False

    def parse_do_while_statement(self):
        self.advance()
        body = self.parse_statement()
        if not isinstance(body, list):
            body = [body] if body else []
        if self.current and self.current.type == TokenType.IDENTIFIER and self.current.value == 'while':
            self.advance()
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.SEMICOLON)
        return {"type": "DoWhileStmt", "condition": condition, "body": body}

    def parse_switch_statement(self):
        self.advance()
        self.expect(TokenType.LPAREN)
        expr = self.parse_expression()
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.LBRACE)
        cases = []
        current_case = None
        while self.current and self.current.type != TokenType.RBRACE:
            if self.current.type == TokenType.IDENTIFIER and self.current.value == 'case':
                self.advance()
                val = self.parse_expression()
                self.expect(TokenType.COLON)
                current_case = {"type": "SwitchCase", "value": val, "body": []}
                cases.append(current_case)
            elif self.current.type == TokenType.IDENTIFIER and self.current.value == 'default':
                self.advance()
                self.expect(TokenType.COLON)
                current_case = {"type": "SwitchCase", "value": None, "body": []}
                cases.append(current_case)
            else:
                stmt = self.parse_statement()
                if current_case is not None and stmt is not None:
                    if isinstance(stmt, list):
                        current_case["body"].extend(stmt)
                    else:
                        current_case["body"].append(stmt)
        self.expect(TokenType.RBRACE)
        return {"type": "SwitchStmt", "expr": expr, "cases": cases}

    def parse_try_statement(self):
        self.advance()
        try_body = self.parse_block()
        catches = []
        while self.current and self.current.type == TokenType.IDENTIFIER and self.current.value == 'catch':
            self.advance()
            self.expect(TokenType.LPAREN)
            if self.current and self.current.type == TokenType.ELLIPSIS:
                self.advance()
                catch_type = "..."
                catch_name = "_e"
            else:
                catch_type = self.parse_type_name()
                catch_name = "_e"
                if self.current and self.current.type == TokenType.IDENTIFIER:
                    catch_name = self.advance().value
            self.expect(TokenType.RPAREN)
            catch_body = self.parse_block()
            catches.append({"type": catch_type, "name": catch_name, "body": catch_body})
        return {"type": "TryStmt", "body": try_body, "catches": catches}

    def parse_throw_statement(self):
        self.advance()
        if self.current and self.current.type == TokenType.SEMICOLON:
            self.advance()
            return {"type": "ThrowStmt", "expr": None}
        expr = self.parse_expression()
        self.expect(TokenType.SEMICOLON)
        return {"type": "ThrowStmt", "expr": expr}

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

        init = None
        if self.current.type != TokenType.SEMICOLON:
            if self.is_type_token() or self.is_identifier_type():
                saved_pos = self.pos
                try:
                    type_name = self.parse_type_name()
                    if self.current and self.current.type == TokenType.IDENTIFIER:
                        var_name = self.advance().value
                        if self.current and self.current.type == TokenType.COLON:
                            self.advance()
                            iterable = self.parse_expression()
                            self.expect(TokenType.RPAREN)
                            body = self.parse_statement()
                            if not isinstance(body, list):
                                body = [body] if body else []
                            return {"type": "RangeForStmt", "varType": type_name, "varName": var_name, "iterable": iterable, "body": body}
                        else:
                            self.pos = saved_pos
                            self.current = self.tokens[self.pos]
                    else:
                        self.pos = saved_pos
                        self.current = self.tokens[self.pos]
                except Exception:
                    self.pos = saved_pos
                    self.current = self.tokens[self.pos]
                init = self.parse_function_or_variable()
            else:
                init = self.parse_expression()
                self.expect(TokenType.SEMICOLON)
        else:
            self.expect(TokenType.SEMICOLON)

        condition = None
        if self.current.type != TokenType.SEMICOLON:
            condition = self.parse_expression()
        self.expect(TokenType.SEMICOLON)

        update = None
        if self.current.type != TokenType.RPAREN:
            updates = []
            while self.current.type != TokenType.RPAREN:
                updates.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
            update = updates[0] if len(updates) == 1 else {"type": "ExprList", "exprs": updates}
        self.expect(TokenType.RPAREN)

        body = self.parse_statement()
        if not isinstance(body, list):
            body = [body] if body else []

        return {"type": "ForStmt", "init": init, "condition": condition, "update": update, "body": body}

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
            op_str = op_token.value

            compound_map = {
                '+=': 'PLUS', '-=': 'MINUS', '*=': 'STAR', '/=': 'SLASH',
                '%=': 'PERCENT', '&=': 'BITWISE_AND', '|=': 'BITWISE_OR',
                '^=': 'BITWISE_XOR', '<<=': 'SHIFT_LEFT', '>>=': 'SHIFT_RIGHT',
            }
            if op_str in compound_map:
                return {
                    "type": "AssignExpr",
                    "left": left,
                    "right": {
                        "type": "BinaryExpr",
                        "op": compound_map[op_str],
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

        if self.current and self.current.type == TokenType.STAR:
            self.advance()
            operand = self.parse_unary()
            return {"type": "DerefExpr", "expr": operand}

        if self.current and self.current.type == TokenType.BITWISE_AND:
            self.advance()
            operand = self.parse_unary()
            return {"type": "AddressOfExpr", "expr": operand}

        if (self.current and self.current.type == TokenType.LPAREN
                and self.peek(1) and self.peek(1).type in TYPE_TOKENS):
            saved_pos = self.pos
            self.advance()
            if self.is_type_token():
                self.parse_type_name()
                if self.current and self.current.type == TokenType.RPAREN:
                    self.advance()
                    operand = self.parse_unary()
                    return {"type": "CastExpr", "expr": operand}
            self.pos = saved_pos
            self.current = self.tokens[self.pos]

        if self.current and self.current.type == TokenType.IDENTIFIER:
            if self.current.value == 'sizeof':
                self.advance()
                if self.match(TokenType.LPAREN):
                    depth = 1
                    while self.current and depth > 0:
                        if self.current.type == TokenType.LPAREN:
                            depth += 1
                        elif self.current.type == TokenType.RPAREN:
                            depth -= 1
                        self.advance()
                return {"type": "NumberLiteral", "value": "4"}

            if self.current.value == 'alignof':
                self.advance()
                if self.match(TokenType.LPAREN):
                    depth = 1
                    while self.current and depth > 0:
                        if self.current.type == TokenType.LPAREN:
                            depth += 1
                        elif self.current.type == TokenType.RPAREN:
                            depth -= 1
                        self.advance()
                return {"type": "NumberLiteral", "value": "8"}

            if self.current.value == 'new':
                return self.parse_new_expr()

            if self.current.value == 'delete':
                self.advance()
                if self.current and self.current.type == TokenType.LBRACKET:
                    self.advance()
                    self.expect(TokenType.RBRACKET)
                operand = self.parse_unary()
                return {"type": "DeleteExpr", "expr": operand}

        return self.parse_postfix()

    def parse_new_expr(self):
        self.advance()
        if self.current and self.current.type == TokenType.LBRACKET:
            self.advance()
            size = self.parse_expression()
            self.expect(TokenType.RBRACKET)
            return {"type": "NewArrayExpr", "size": size}

        if self.is_type_token() or self.is_identifier_type():
            type_name = self.parse_type_name()
        else:
            type_name = "int"

        args = []
        if self.current and self.current.type == TokenType.LPAREN:
            self.advance()
            if self.current.type != TokenType.RPAREN:
                while True:
                    args.append(self.parse_expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.expect(TokenType.RPAREN)
        elif self.current and self.current.type == TokenType.LBRACE:
            init = self.parse_brace_initializer()
            args = init.get("elements", [])

        return {"type": "NewExpr", "newType": type_name, "args": args}

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
                if not self.current or self.current.type not in (TokenType.IDENTIFIER,):
                    break
                member = self.advance().value
                if self.current and self.current.type == TokenType.LPAREN:
                    self.advance()
                    args = self._parse_call_args()
                    expr = {"type": "MethodCall", "object": expr, "method": member, "args": args}
                else:
                    expr = {"type": "MemberAccess", "object": expr, "member": member}

            elif self.current and self.current.type == TokenType.ARROW:
                self.advance()
                member = self.advance().value if self.current and self.current.type == TokenType.IDENTIFIER else ""
                if self.current and self.current.type == TokenType.LPAREN:
                    self.advance()
                    args = self._parse_call_args()
                    expr = {"type": "MethodCall", "object": expr, "method": member, "args": args}
                else:
                    expr = {"type": "MemberAccess", "object": expr, "member": member}

            elif self.current and self.current.type == TokenType.SCOPE:
                self.advance()
                member = self.advance().value if self.current and self.current.type == TokenType.IDENTIFIER else ""
                if self.current and self.current.type == TokenType.LPAREN:
                    self.advance()
                    args = self._parse_call_args()
                    expr = {"type": "CallExpr", "callee": member, "args": args}
                else:
                    expr = {"type": "Identifier", "name": member}
            else:
                break

        return expr

    def _parse_call_args(self):
        args = []
        if self.current and self.current.type != TokenType.RPAREN:
            while True:
                if self.current and self.current.type == TokenType.LBRACE:
                    args.append(self.parse_brace_initializer())
                else:
                    args.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
        self.expect(TokenType.RPAREN)
        return args

    def parse_primary(self):
        if self.current and self.current.type == TokenType.IDENTIFIER and self.current.value == 'decltype':
            self.advance()
            self.expect(TokenType.LPAREN)
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return {"type": "DecltypeExpr", "expr": expr}

        if self.current and self.current.type == TokenType.IDENTIFIER and self.current.value == 'make_shared':
            self.advance()
            if self.current and self.current.type == TokenType.LESS:
                self.skip_template_args()
            self.expect(TokenType.LPAREN)
            args = self._parse_call_args()
            return {"type": "CallExpr", "callee": "make_shared", "args": args}

        if self.current and self.current.type == TokenType.IDENTIFIER and self.current.value == 'make_unique':
            self.advance()
            if self.current and self.current.type == TokenType.LESS:
                self.skip_template_args()
            self.expect(TokenType.LPAREN)
            args = self._parse_call_args()
            return {"type": "CallExpr", "callee": "make_unique", "args": args}

        if self.current and self.current.type == TokenType.IDENTIFIER and self.current.value == 'make_optional':
            self.advance()
            self.expect(TokenType.LPAREN)
            args = self._parse_call_args()
            return {"type": "CallExpr", "callee": "make_optional", "args": args}

        if self.current and self.current.type == TokenType.IDENTIFIER and self.current.value == 'move':
            self.advance()
            self.expect(TokenType.LPAREN)
            args = self._parse_call_args()
            return args[0] if args else {"type": "Identifier", "name": "_moved"}

        if self.current and self.current.type == TokenType.IDENTIFIER and self.current.value == 'forward':
            self.advance()
            if self.current and self.current.type == TokenType.LESS:
                self.skip_template_args()
            self.expect(TokenType.LPAREN)
            args = self._parse_call_args()
            return args[0] if args else {"type": "Identifier", "name": "_fwd"}

        token = self.advance()

        if token.type == TokenType.NUMBER:
            return {"type": "NumberLiteral", "value": token.value}

        if token.type == TokenType.STRING:
            val = token.value[1:-1]
            val = val.replace('\\n', '\n').replace('\\t', '\t').replace('\\r', '\r').replace('\\"', '"').replace('\\\\', '\\')
            return {"type": "StringLiteral", "value": val}

        if token.type == TokenType.CHAR:
            inner = token.value[1:-1]
            if inner.startswith('\\'):
                escapes = {'\\n': '\n', '\\t': '\t', '\\r': '\r', '\\\\': '\\', "\\'": "'", '\\"': '"', '\\0': '\0'}
                char_val = escapes.get(inner, inner[1:])
            else:
                char_val = inner
            return {"type": "CharLiteral", "value": char_val}

        if token.type == TokenType.IDENTIFIER:
            name = token.value

            if name == 'lambda' or name == '[':
                return {"type": "NumberLiteral", "value": "0"}

            if self.current and self.current.type == TokenType.LESS:
                if name in COMPLEX_TYPE_NAMES:
                    self.skip_template_args()
                    if self.current and self.current.type == TokenType.LPAREN:
                        self.advance()
                        args = self._parse_call_args()
                        return {"type": "CallExpr", "callee": name, "args": args}
                    elif self.current and self.current.type == TokenType.LBRACE:
                        init = self.parse_brace_initializer()
                        return {"type": "CallExpr", "callee": name, "args": init.get("elements", [])}

            if self.current and self.current.type == TokenType.LPAREN:
                self.advance()
                args = self._parse_call_args()
                return {"type": "CallExpr", "callee": name, "args": args}

            if self.current and self.current.type == TokenType.LBRACE:
                if name in COMPLEX_TYPE_NAMES:
                    init = self.parse_brace_initializer()
                    return {"type": "CallExpr", "callee": name, "args": init.get("elements", [])}

            return {"type": "Identifier", "name": name}

        if token.type == TokenType.LBRACKET:
            params = []
            if self.current and self.current.type != TokenType.RBRACKET:
                while True:
                    if self.current.type == TokenType.BITWISE_AND:
                        self.advance()
                    if self.current.type == TokenType.RBRACKET:
                        break
                    params.append(self.advance().value if self.current.type == TokenType.IDENTIFIER else "")
                    if not self.match(TokenType.COMMA):
                        break
            self.expect(TokenType.RBRACKET)
            lambda_params = []
            if self.current and self.current.type == TokenType.LPAREN:
                self.advance()
                lambda_params = self.parse_param_list()
                self.expect(TokenType.RPAREN)
            while self.current and self.current.type == TokenType.IDENTIFIER and self.current.value in ('mutable', 'noexcept', 'constexpr'):
                self.advance()
            if self.current and self.current.type == TokenType.ARROW:
                self.advance()
                self.parse_type_name()
            body = []
            if self.current and self.current.type == TokenType.LBRACE:
                body = self.parse_block()
            return {"type": "LambdaExpr", "captures": params, "params": lambda_params, "body": body}

        if token.type == TokenType.LPAREN:
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        if token.type == TokenType.LBRACE:
            elements = []
            while self.current and self.current.type != TokenType.RBRACE:
                if self.current.type == TokenType.LBRACE:
                    elements.append(self.parse_brace_initializer())
                else:
                    elements.append(self.parse_expression())
                if not self.match(TokenType.COMMA):
                    break
            self.expect(TokenType.RBRACE)
            return {"type": "InitializerList", "elements": elements}

        raise SyntaxError(f"Unexpected token in expression: {token}")
