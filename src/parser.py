from tokens import Token, TokenType
from typing import List, Optional

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current = self.tokens[self.pos] if tokens else None
        self.ids = []
        self.consts = []

    # ----------------------------
    # Utility Methods
    # ----------------------------
    def peek(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def advance(self) -> Token:
        token = self.peek()
        if token and token.type != TokenType.EOF:
            self.pos += 1
            self.current = self.peek()
        return token

    def match(self, *types) -> bool:
        """Consume a token if its type matches one of `types`."""
        if self.current and self.current.type in types:
            self.advance()
            return True
        return False

    def expect(self, type_: TokenType):
        if not self.match(type_):
            raise SyntaxError(f"Expected {type_.name}, found {self.current}")

    # ----------------------------
    # Top-level parse
    # ----------------------------
    def parse(self):
        """Parse the full translation unit (a list of declarations)."""
        ast = []
        while self.current and self.current.type != TokenType.EOF:
            node = self.parse_declaration()
            ast.append(node)
        return ast

    # ----------------------------
    # Declarations
    # ----------------------------
    def parse_declaration(self):
        # Handle simple type + identifier declarations
        if self.current.type in (TokenType.INT, TokenType.VOID):
            return self.parse_function_or_variable()
        else:
            raise SyntaxError(f"Unexpected token {self.current}")

    def parse_function_or_variable(self):
        type_token = self.advance()  # int or void
        if self.current.type != TokenType.IDENTIFIER:
            raise SyntaxError(f"Expected identifier after type, got {self.current}")
        name = self.advance().value

        # Function declaration or variable?
        if self.match(TokenType.LPAREN):
            params = self.parse_param_list()
            self.expect(TokenType.RPAREN)
            body = self.parse_block()
            return {"type": "FunctionDecl", "returnType": type_token.value, "name": name, "params": params, "body": body}
        else:
            # Variable declaration
            init = None
            if self.match(TokenType.ASSIGN):
                init = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return {"type": "VarDecl", "varType": type_token.value, "name": name, "init": init}

    def parse_param_list(self):
        params = []
        if self.current.type == TokenType.RPAREN:
            return params
        while True:
            param_type = self.advance().value
            param_name = self.advance().value
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
            statements.append(self.parse_statement())
        self.expect(TokenType.RBRACE)
        return statements

    def parse_statement(self):
        if self.match(TokenType.RETURN):
            expr = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return {"type": "ReturnStmt", "expr": expr}
        elif self.current.type == TokenType.IDENTIFIER:
            # Could be assignment or expression statement
            expr = self.parse_expression()
            self.expect(TokenType.SEMICOLON)
            return {"type": "ExprStmt", "expr": expr}
        elif self.match(TokenType.IF):
            return self.parse_if_statement()
        elif self.match(TokenType.FOR):
            return self.parse_for_statement()
        elif self.current.type == TokenType.LBRACE:
            return self.parse_block()
        elif self.match(TokenType.WHILE):
            return self.parse_while_statement()
        elif self.current.type in (TokenType.INT, TokenType.VOID):
            return self.parse_function_or_variable()
        else:
            raise SyntaxError(f"Unexpected token in statement: {self.current}")

    # ----------------------------
    # Expressions
    # ----------------------------
    def parse_expression(self):
        return self.parse_assignment()
    
    def parse_if_statement(self):
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)

        then_branch = self.parse_statement()
        if not isinstance(then_branch, list):
            then_branch = [then_branch]

        else_branch = None
        if self.match(TokenType.ELSE):
            else_branch = self.parse_statement()
            if not isinstance(else_branch, list):
                else_branch = [else_branch]

        return {
            "type": "IfStmt",
            "condition": condition,
            "then": then_branch,
            "else": else_branch
        }
        
    def parse_while_statement(self):
        self.expect(TokenType.LPAREN)
        condition = self.parse_expression()
        self.expect(TokenType.RPAREN)

        body = self.parse_statement()

        # normalize to block
        if not isinstance(body, list):
            body = [body]

        return {
            "type": "WhileStmt",
            "condition": condition,
            "body": body
        }

    def parse_for_statement(self):
        self.expect(TokenType.LPAREN)

        # init
        init = None
        if self.current.type != TokenType.SEMICOLON:
            if self.current.type in (TokenType.INT, TokenType.VOID):
                init = self.parse_function_or_variable()
                # ⚠️ DO NOT expect another semicolon here
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

        # Normalize to block
        if not isinstance(body, list):
            body = [body]

        return {
            "type": "ForStmt",
            "init": init,
            "condition": condition,
            "update": update,
            "body": body
        }

    def parse_assignment(self):
        left = self.parse_equality()
        if self.match(TokenType.ASSIGN):
            right = self.parse_assignment()
            return {"type": "AssignExpr", "left": left, "right": right}
        return left

    def parse_equality(self):
        expr = self.parse_relational()
        while self.match(TokenType.EQUAL, TokenType.NOT_EQUAL):
            op = self.tokens[self.pos - 1].type
            right = self.parse_relational()
            expr = {"type": "BinaryExpr", "op": op.name, "left": expr, "right": right}
        return expr

    def parse_relational(self):
        expr = self.parse_term()
        while self.match(TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL):
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
        # prefix ++i or --i
        if self.match(TokenType.INCREMENT, TokenType.DECREMENT):
            op = self.tokens[self.pos - 1].type
            operand = self.parse_unary()

            return {
                "type": "UpdateExpr",
                "op": op.name,
                "expr": operand,
                "prefix": True
            }

        if self.match(TokenType.PLUS, TokenType.MINUS, TokenType.LOGICAL_NOT):
            op = self.tokens[self.pos - 1].type
            operand = self.parse_unary()
            return {"type": "UnaryExpr", "op": op.name, "expr": operand}

        return self.parse_postfix()
    
    def parse_postfix(self):
        expr = self.parse_primary()

        # postfix i++ or i--
        if self.match(TokenType.INCREMENT, TokenType.DECREMENT):
            op = self.tokens[self.pos - 1].type
            return {
                "type": "UpdateExpr",
                "op": op.name,
                "expr": expr,
                "prefix": False
            }

        return expr

    def parse_primary(self):
        token = self.advance()
        if token.type == TokenType.NUMBER:
            self.consts.append(token.value)
            return {"type": "NumberLiteral", "value": token.value}
        elif token.type == TokenType.IDENTIFIER:
            name = token.value

            # Function call?
            if self.match(TokenType.LPAREN):
                args = []

                if self.current.type != TokenType.RPAREN:
                    while True:
                        args.append(self.parse_expression())
                        if not self.match(TokenType.COMMA):
                            break

                self.expect(TokenType.RPAREN)

                return {
                    "type": "CallExpr",
                    "callee": name,
                    "args": args
                }

            self.ids.append(name)
            return {"type": "Identifier", "name": name}
        elif token.type == TokenType.LPAREN:
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        else:
            raise SyntaxError(f"Unexpected token in expression: {token}")
