import re
from enum import Enum, auto
import sys
import os

# ----------------------------
# Token Types
# ----------------------------
class TokenType(Enum):
    # Keywords
    INT = auto()
    RETURN = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    VOID = auto()
    INCLUDE = auto()

    # Identifiers and literals
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    ASSIGN = auto()
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    SHIFT_LEFT = auto()      # <<
    SHIFT_RIGHT = auto()     # >>
    AND = auto()             # &&
    OR = auto()              # ||
    BITWISE_AND = auto()     # &
    BITWISE_OR = auto()      # |
    BITWISE_XOR = auto()     # ^
    BITWISE_NOT = auto()     # ~
    LOGICAL_NOT = auto()     # !
    INCREMENT = auto()       # ++
    DECREMENT = auto()       # --
    QUESTION = auto()        # ?
    ARROW = auto()           # ->

    # Punctuation
    LPAREN = auto()          # (
    RPAREN = auto()          # )
    LBRACE = auto()          # {
    RBRACE = auto()          # }
    LBRACKET = auto()        # [
    RBRACKET = auto()        # ]
    SEMICOLON = auto()       # ;
    COMMA = auto()
    SCOPE = auto()           # ::
    COLON = auto()
    HASH = auto()            # #
    DOT = auto()             # .

    # End of file
    EOF = auto()

# ----------------------------
# Token Class
# ----------------------------
class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.type.name}, {repr(self.value)}, line={self.line}, col={self.column})"

# ----------------------------
# Scanner Class
# ----------------------------
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
    }

    TOKEN_REGEX = [
        # Whitespace and comments
        (r'[ \t\n]+', None),        # Skip whitespace including newlines
        (r'//[^\n]*', None),        # Skip single-line comments
        (r'/\*.*?\*/', None),       # Skip multi-line comments

        # Preprocessor directives
        (r'#include', TokenType.HASH),
        (r'#', TokenType.HASH),

        # Numbers
        (r'\d+', TokenType.NUMBER),

        # Strings (handles escaped quotes)
        (r'"([^"\\]|\\.)*"', TokenType.STRING),

        # Multi-character operators (must come before single-character ones)
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

        # Single-character operators and punctuation
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

        # Punctuation and brackets
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

        # Identifiers
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

                    # Skip whitespace and comments
                    if token_type is None:
                        # Still update line/column for skipped content
                        newlines = text.count('\n')
                        if newlines > 0:
                            self.line += newlines
                            self.column = len(text) - text.rfind('\n')
                        else:
                            self.column += len(text)
                        pos = match.end(0)
                        break

                    # Handle preprocessor directives specially
                    if token_type == TokenType.HASH and text == '#include':
                        self.tokens.append(Token(TokenType.HASH, text, self.line, self.column))
                    else:
                        # If identifier is actually a keyword, upgrade its type
                        if token_type == TokenType.IDENTIFIER and text in self.KEYWORDS:
                            actual_type = self.KEYWORDS[text]
                        else:
                            actual_type = token_type

                        self.tokens.append(Token(actual_type, text, self.line, self.column))

                    # Update line/column positions
                    newlines = text.count('\n')
                    if newlines > 0:
                        self.line += newlines
                        # Reset column after last newline
                        self.column = len(text) - text.rfind('\n')
                    else:
                        self.column += len(text)

                    pos = match.end(0)
                    break

            if not match:
                # Show some context around the error
                start = max(0, pos - 10)
                end = min(len(self.source), pos + 10)
                context = self.source[start:end]
                raise SyntaxError(
                    f"Unexpected character '{self.source[pos]}' at line {self.line}, column {self.column}\n"
                    f"Context: ...{context}..."
                )

        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

# ----------------------------
# File Reading and Main Function
# ----------------------------
def read_cpp_file(filename):
    """Read a C++ file and return its contents as a string"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) != 2:
        print("Usage: python scanner.py <filename.cpp>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    # Check file extension
    if not filename.endswith(('.cpp', '.c', '.h', '.hpp', '.cc', '.cxx')):
        print("Warning: This looks like it might not be a C/C++ file.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Read the file
    source_code = read_cpp_file(filename)
    
    # Scan the file
    scanner = Scanner(source_code)
    try:
        tokens = scanner.scan()
        
        # Print tokens
        print(f"Tokens from {filename}:")
        print("-" * 50)
        for token in tokens:
            print(token)
    except SyntaxError as e:
        print(f"Syntax Error: {e}")

if __name__ == "__main__":
    main()