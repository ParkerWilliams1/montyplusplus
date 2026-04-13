import re
import sys
import os
from tokens import TokenType, Token

class Scanner:
    KEYWORDS = {
        "int": TokenType.INT,
        "return": TokenType.RETURN,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "while": TokenType.WHILE,
        "for": TokenType.FOR,
        "void": TokenType.VOID,
        "include": TokenType.INCLUDE,
        "bool": TokenType.BOOL,
        "char": TokenType.CHAR,
        "float": TokenType.FLOAT,
        "long": TokenType.INT,     # treat long as int
        "short": TokenType.INT,    # treat short as int
        "true": TokenType.NUMBER,  # bool literals handled as numbers for now
        "false": TokenType.NUMBER,
        "struct": TokenType.IDENTIFIER,
        "class": TokenType.IDENTIFIER,
        "public": TokenType.IDENTIFIER,
        "private": TokenType.IDENTIFIER,
        "new": TokenType.IDENTIFIER,
        "delete": TokenType.IDENTIFIER,
        "nullptr": TokenType.IDENTIFIER,
        "null": TokenType.IDENTIFIER,
        "break": TokenType.IDENTIFIER,
        "continue": TokenType.IDENTIFIER,
        "string": TokenType.IDENTIFIER,
        "vector": TokenType.IDENTIFIER,
        "map": TokenType.IDENTIFIER,
        "unordered_map": TokenType.IDENTIFIER,
        "set": TokenType.IDENTIFIER,
        "unordered_set": TokenType.IDENTIFIER,
        "pair": TokenType.IDENTIFIER,
        "stack": TokenType.IDENTIFIER,
        "queue": TokenType.IDENTIFIER,
        "deque": TokenType.IDENTIFIER,
        "priority_queue": TokenType.IDENTIFIER,
        "list": TokenType.IDENTIFIER,
        "max": TokenType.IDENTIFIER,
        "min": TokenType.IDENTIFIER,
        "abs": TokenType.IDENTIFIER,
        "sort": TokenType.IDENTIFIER,
        "size": TokenType.IDENTIFIER,
        "push_back": TokenType.IDENTIFIER,
        "pop_back": TokenType.IDENTIFIER,
        "push": TokenType.IDENTIFIER,
        "pop": TokenType.IDENTIFIER,
        "top": TokenType.IDENTIFIER,
        "front": TokenType.IDENTIFIER,
        "back": TokenType.IDENTIFIER,
        "begin": TokenType.IDENTIFIER,
        "end": TokenType.IDENTIFIER,
        "find": TokenType.IDENTIFIER,
        "count": TokenType.IDENTIFIER,
        "empty": TokenType.IDENTIFIER,
        "clear": TokenType.IDENTIFIER,
        "insert": TokenType.IDENTIFIER,
        "erase": TokenType.IDENTIFIER,
        "swap": TokenType.IDENTIFIER,
        "reverse": TokenType.IDENTIFIER,
        "resize": TokenType.IDENTIFIER,
        "reserve": TokenType.IDENTIFIER,
        "at": TokenType.IDENTIFIER,
        "substr": TokenType.IDENTIFIER,
        "length": TokenType.IDENTIFIER,
        "INT_MAX": TokenType.NUMBER,
        "INT_MIN": TokenType.NUMBER,
    }

    TOKEN_REGEX = [
        (r'[ \t\n]+', None),
        (r'//[^\n]*', None),
        (r'/\*.*?\*/', None),
        (r'#include\s*[<"][^>"]*[>"]', None),  # skip includes
        (r'#[^\n]*', None),                     # skip other preprocessor
        (r'\d+\.\d+', TokenType.NUMBER),        # float literals
        (r'\d+', TokenType.NUMBER),
        (r'"([^"\\]|\\.)*"', TokenType.STRING),
        (r"'([^'\\]|\\.)'", TokenType.CHAR),
        (r'<<', TokenType.SHIFT_LEFT),
        (r'>>', TokenType.SHIFT_RIGHT),
        (r'<=', TokenType.LESS_EQUAL),
        (r'>=', TokenType.GREATER_EQUAL),
        (r'==', TokenType.EQUAL),
        (r'!=', TokenType.NOT_EQUAL),
        (r'&&', TokenType.AND),
        (r'\|\|', TokenType.OR),
        (r'\+\+', TokenType.INCREMENT),
        (r'--', TokenType.DECREMENT),
        (r'->', TokenType.ARROW),
        (r'\+=', TokenType.ASSIGN),   # treat += as special assign
        (r'-=', TokenType.ASSIGN),
        (r'\*=', TokenType.ASSIGN),
        (r'/=', TokenType.ASSIGN),
        (r'\+', TokenType.PLUS),
        (r'-', TokenType.MINUS),
        (r'\*', TokenType.STAR),
        (r'/', TokenType.SLASH),
        (r'%', TokenType.PERCENT),
        (r'=', TokenType.ASSIGN),
        (r'<', TokenType.LESS),
        (r'>', TokenType.GREATER),
        (r'&', TokenType.BITWISE_AND),
        (r'\|', TokenType.BITWISE_OR),
        (r'\^', TokenType.BITWISE_XOR),
        (r'~', TokenType.BITWISE_NOT),
        (r'!', TokenType.LOGICAL_NOT),
        (r'\?', TokenType.QUESTION),
        (r'::', TokenType.SCOPE),
        (r'\(', TokenType.LPAREN),
        (r'\)', TokenType.RPAREN),
        (r'\{', TokenType.LBRACE),
        (r'\}', TokenType.RBRACE),
        (r'\[', TokenType.LBRACKET),
        (r'\]', TokenType.RBRACKET),
        (r';', TokenType.SEMICOLON),
        (r',', TokenType.COMMA),
        (r':', TokenType.COLON),
        (r'\.', TokenType.DOT),
        (r'[A-Za-z_][A-Za-z0-9_]*', TokenType.IDENTIFIER),
    ]

    def __init__(self, source_code):
        self.source = source_code
        self.tokens = []
        self.line = 1
        self.column = 1

    def scan(self):
        pos = 0
        while pos < len(self.source):
            match = None
            for pattern, token_type in self.TOKEN_REGEX:
                regex = re.compile(pattern, re.DOTALL)
                match = regex.match(self.source, pos)
                if match:
                    text = match.group(0)
                    if token_type is None:
                        newlines = text.count('\n')
                        if newlines > 0:
                            self.line += newlines
                            self.column = len(text) - text.rfind('\n')
                        else:
                            self.column += len(text)
                        pos = match.end(0)
                        break

                    if token_type == TokenType.IDENTIFIER and text in self.KEYWORDS:
                        actual_type = self.KEYWORDS[text]
                        # Special handling for bool literals
                        if text == 'true':
                            self.tokens.append(Token(TokenType.NUMBER, '1', self.line, self.column))
                        elif text == 'false':
                            self.tokens.append(Token(TokenType.NUMBER, '0', self.line, self.column))
                        elif text == 'nullptr' or text == 'null':
                            self.tokens.append(Token(TokenType.NUMBER, '0', self.line, self.column))
                        elif text == 'INT_MAX':
                            self.tokens.append(Token(TokenType.NUMBER, '2147483647', self.line, self.column))
                        elif text == 'INT_MIN':
                            self.tokens.append(Token(TokenType.NUMBER, '-2147483648', self.line, self.column))
                        elif text in ('break', 'continue'):
                            self.tokens.append(Token(TokenType.IDENTIFIER, text, self.line, self.column))
                        else:
                            self.tokens.append(Token(actual_type, text, self.line, self.column))
                    else:
                        self.tokens.append(Token(token_type, text, self.line, self.column))

                    newlines = text.count('\n')
                    if newlines > 0:
                        self.line += newlines
                        self.column = len(text) - text.rfind('\n')
                    else:
                        self.column += len(text)
                    pos = match.end(0)
                    break

            if not match:
                start = max(0, pos - 10)
                end = min(len(self.source), pos + 10)
                context = self.source[start:end]
                raise SyntaxError(
                    f"Unexpected character '{self.source[pos]}' at line {self.line}, column {self.column}\n"
                    f"Context: ...{context}..."
                )

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens