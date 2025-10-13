from tokens import Token, TokenType
from typing import List, Optional
from scanner import Token, TokenType

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
        while self.current.type != TokenType.RBRACE:
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
        elif self.current.type in (TokenType.INT, TokenType.VOID):
            return self.parse_function_or_variable()
        else:
            raise SyntaxError(f"Unexpected token in statement: {self.current}")

    # ----------------------------
    # Expressions
    # ----------------------------
    def parse_expression(self):
        return self.parse_assignment()

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
        if self.match(TokenType.PLUS, TokenType.MINUS, TokenType.LOGICAL_NOT):
            op = self.tokens[self.pos - 1].type
            operand = self.parse_unary()
            return {"type": "UnaryExpr", "op": op.name, "expr": operand}
        return self.parse_primary()

    def parse_primary(self):
        token = self.advance()
        if token.type == TokenType.NUMBER:
            self.consts.append(token.value)
            return {"type": "NumberLiteral", "value": token.value}
        elif token.type == TokenType.IDENTIFIER:
            self.ids.append(token.value)
            return {"type": "Identifier", "name": token.value}
        elif token.type == TokenType.LPAREN:
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        else:
            raise SyntaxError(f"Unexpected token in expression: {token}")
