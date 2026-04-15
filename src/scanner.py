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
        "long": TokenType.INT,
        "short": TokenType.INT,
        "unsigned": TokenType.INT,
        "signed": TokenType.INT,
        "double": TokenType.FLOAT,
        "true": TokenType.NUMBER,
        "false": TokenType.NUMBER,
        "struct": TokenType.IDENTIFIER,
        "class": TokenType.IDENTIFIER,
        "public": TokenType.IDENTIFIER,
        "private": TokenType.IDENTIFIER,
        "protected": TokenType.IDENTIFIER,
        "new": TokenType.IDENTIFIER,
        "delete": TokenType.IDENTIFIER,
        "nullptr": TokenType.IDENTIFIER,
        "null": TokenType.IDENTIFIER,
        "break": TokenType.IDENTIFIER,
        "continue": TokenType.IDENTIFIER,
        "const": TokenType.IDENTIFIER,
        "constexpr": TokenType.IDENTIFIER,
        "static": TokenType.IDENTIFIER,
        "inline": TokenType.IDENTIFIER,
        "extern": TokenType.IDENTIFIER,
        "virtual": TokenType.IDENTIFIER,
        "override": TokenType.IDENTIFIER,
        "final": TokenType.IDENTIFIER,
        "explicit": TokenType.IDENTIFIER,
        "mutable": TokenType.IDENTIFIER,
        "namespace": TokenType.IDENTIFIER,
        "using": TokenType.IDENTIFIER,
        "typedef": TokenType.IDENTIFIER,
        "typename": TokenType.IDENTIFIER,
        "template": TokenType.IDENTIFIER,
        "auto": TokenType.IDENTIFIER,
        "decltype": TokenType.IDENTIFIER,
        "static_assert": TokenType.IDENTIFIER,
        "noexcept": TokenType.IDENTIFIER,
        "throw": TokenType.IDENTIFIER,
        "try": TokenType.IDENTIFIER,
        "catch": TokenType.IDENTIFIER,
        "switch": TokenType.IDENTIFIER,
        "case": TokenType.IDENTIFIER,
        "default": TokenType.IDENTIFIER,
        "do": TokenType.IDENTIFIER,
        "goto": TokenType.IDENTIFIER,
        "enum": TokenType.IDENTIFIER,
        "sizeof": TokenType.IDENTIFIER,
        "alignof": TokenType.IDENTIFIER,
        "operator": TokenType.IDENTIFIER,
        "friend": TokenType.IDENTIFIER,
        "string": TokenType.IDENTIFIER,
        "vector": TokenType.IDENTIFIER,
        "array": TokenType.IDENTIFIER,
        "map": TokenType.IDENTIFIER,
        "unordered_map": TokenType.IDENTIFIER,
        "multimap": TokenType.IDENTIFIER,
        "unordered_multimap": TokenType.IDENTIFIER,
        "set": TokenType.IDENTIFIER,
        "unordered_set": TokenType.IDENTIFIER,
        "multiset": TokenType.IDENTIFIER,
        "unordered_multiset": TokenType.IDENTIFIER,
        "pair": TokenType.IDENTIFIER,
        "tuple": TokenType.IDENTIFIER,
        "optional": TokenType.IDENTIFIER,
        "variant": TokenType.IDENTIFIER,
        "any": TokenType.IDENTIFIER,
        "stack": TokenType.IDENTIFIER,
        "queue": TokenType.IDENTIFIER,
        "deque": TokenType.IDENTIFIER,
        "priority_queue": TokenType.IDENTIFIER,
        "list": TokenType.IDENTIFIER,
        "forward_list": TokenType.IDENTIFIER,
        "bitset": TokenType.IDENTIFIER,
        "valarray": TokenType.IDENTIFIER,
        "complex": TokenType.IDENTIFIER,
        "function": TokenType.IDENTIFIER,
        "shared_ptr": TokenType.IDENTIFIER,
        "unique_ptr": TokenType.IDENTIFIER,
        "weak_ptr": TokenType.IDENTIFIER,
        "make_shared": TokenType.IDENTIFIER,
        "make_unique": TokenType.IDENTIFIER,
        "move": TokenType.IDENTIFIER,
        "forward": TokenType.IDENTIFIER,
        "max": TokenType.IDENTIFIER,
        "min": TokenType.IDENTIFIER,
        "abs": TokenType.IDENTIFIER,
        "sort": TokenType.IDENTIFIER,
        "stable_sort": TokenType.IDENTIFIER,
        "partial_sort": TokenType.IDENTIFIER,
        "nth_element": TokenType.IDENTIFIER,
        "binary_search": TokenType.IDENTIFIER,
        "lower_bound": TokenType.IDENTIFIER,
        "upper_bound": TokenType.IDENTIFIER,
        "equal_range": TokenType.IDENTIFIER,
        "find": TokenType.IDENTIFIER,
        "find_if": TokenType.IDENTIFIER,
        "count": TokenType.IDENTIFIER,
        "count_if": TokenType.IDENTIFIER,
        "accumulate": TokenType.IDENTIFIER,
        "transform": TokenType.IDENTIFIER,
        "for_each": TokenType.IDENTIFIER,
        "fill": TokenType.IDENTIFIER,
        "copy": TokenType.IDENTIFIER,
        "reverse": TokenType.IDENTIFIER,
        "rotate": TokenType.IDENTIFIER,
        "unique": TokenType.IDENTIFIER,
        "remove": TokenType.IDENTIFIER,
        "remove_if": TokenType.IDENTIFIER,
        "merge": TokenType.IDENTIFIER,
        "next_permutation": TokenType.IDENTIFIER,
        "prev_permutation": TokenType.IDENTIFIER,
        "gcd": TokenType.IDENTIFIER,
        "lcm": TokenType.IDENTIFIER,
        "clamp": TokenType.IDENTIFIER,
        "size": TokenType.IDENTIFIER,
        "push_back": TokenType.IDENTIFIER,
        "pop_back": TokenType.IDENTIFIER,
        "push_front": TokenType.IDENTIFIER,
        "pop_front": TokenType.IDENTIFIER,
        "push": TokenType.IDENTIFIER,
        "pop": TokenType.IDENTIFIER,
        "top": TokenType.IDENTIFIER,
        "front": TokenType.IDENTIFIER,
        "back": TokenType.IDENTIFIER,
        "begin": TokenType.IDENTIFIER,
        "end": TokenType.IDENTIFIER,
        "rbegin": TokenType.IDENTIFIER,
        "rend": TokenType.IDENTIFIER,
        "cbegin": TokenType.IDENTIFIER,
        "cend": TokenType.IDENTIFIER,
        "empty": TokenType.IDENTIFIER,
        "clear": TokenType.IDENTIFIER,
        "insert": TokenType.IDENTIFIER,
        "emplace": TokenType.IDENTIFIER,
        "emplace_back": TokenType.IDENTIFIER,
        "emplace_front": TokenType.IDENTIFIER,
        "erase": TokenType.IDENTIFIER,
        "swap": TokenType.IDENTIFIER,
        "resize": TokenType.IDENTIFIER,
        "reserve": TokenType.IDENTIFIER,
        "shrink_to_fit": TokenType.IDENTIFIER,
        "capacity": TokenType.IDENTIFIER,
        "at": TokenType.IDENTIFIER,
        "substr": TokenType.IDENTIFIER,
        "length": TokenType.IDENTIFIER,
        "append": TokenType.IDENTIFIER,
        "assign": TokenType.IDENTIFIER,
        "compare": TokenType.IDENTIFIER,
        "contains": TokenType.IDENTIFIER,
        "starts_with": TokenType.IDENTIFIER,
        "ends_with": TokenType.IDENTIFIER,
        "replace": TokenType.IDENTIFIER,
        "find_first_of": TokenType.IDENTIFIER,
        "find_last_of": TokenType.IDENTIFIER,
        "c_str": TokenType.IDENTIFIER,
        "data": TokenType.IDENTIFIER,
        "get": TokenType.IDENTIFIER,
        "first": TokenType.IDENTIFIER,
        "second": TokenType.IDENTIFIER,
        "has_value": TokenType.IDENTIFIER,
        "value": TokenType.IDENTIFIER,
        "value_or": TokenType.IDENTIFIER,
        "reset": TokenType.IDENTIFIER,
        "make_optional": TokenType.IDENTIFIER,
        "to_string": TokenType.IDENTIFIER,
        "stoi": TokenType.IDENTIFIER,
        "stol": TokenType.IDENTIFIER,
        "stoll": TokenType.IDENTIFIER,
        "stof": TokenType.IDENTIFIER,
        "stod": TokenType.IDENTIFIER,
        "atoi": TokenType.IDENTIFIER,
        "atof": TokenType.IDENTIFIER,
        "printf": TokenType.IDENTIFIER,
        "scanf": TokenType.IDENTIFIER,
        "sprintf": TokenType.IDENTIFIER,
        "sscanf": TokenType.IDENTIFIER,
        "getline": TokenType.IDENTIFIER,
        "cin": TokenType.IDENTIFIER,
        "cout": TokenType.IDENTIFIER,
        "cerr": TokenType.IDENTIFIER,
        "endl": TokenType.IDENTIFIER,
        "INT_MAX": TokenType.NUMBER,
        "INT_MIN": TokenType.NUMBER,
        "LONG_MAX": TokenType.NUMBER,
        "LONG_MIN": TokenType.NUMBER,
        "DBL_MAX": TokenType.NUMBER,
        "FLT_MAX": TokenType.NUMBER,
        "UINT_MAX": TokenType.NUMBER,
        "SIZE_MAX": TokenType.NUMBER,
    }

    TOKEN_REGEX = [
        (r'[ \t\r\n]+', None),
        (r'//[^\n]*', None),
        (r'/\*.*?\*/', None),
        (r'#include\s*[<"][^>"]*[>"]', None),
        (r'#[^\n]*', None),
        (r'\.\.\.', TokenType.ELLIPSIS),
        (r'0[xX][0-9a-fA-F]+[uUlLfF]*', TokenType.NUMBER),
        (r'0[bB][01]+[uUlL]*', TokenType.NUMBER),
        (r'\d+\.\d+[fFlL]?', TokenType.NUMBER),
        (r'\d+[uUlLfF]*', TokenType.NUMBER),
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
        (r'\+=', TokenType.ASSIGN),
        (r'-=', TokenType.ASSIGN),
        (r'\*=', TokenType.ASSIGN),
        (r'/=', TokenType.ASSIGN),
        (r'%=', TokenType.ASSIGN),
        (r'&=', TokenType.ASSIGN),
        (r'\|=', TokenType.ASSIGN),
        (r'\^=', TokenType.ASSIGN),
        (r'<<=', TokenType.ASSIGN),
        (r'>>=', TokenType.ASSIGN),
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
        compiled_patterns = [(re.compile(p, re.DOTALL), t) for p, t in self.TOKEN_REGEX]
        while pos < len(self.source):
            match = None
            for regex, token_type in compiled_patterns:
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
                        if text == 'true':
                            self.tokens.append(Token(TokenType.NUMBER, '1', self.line, self.column))
                        elif text == 'false':
                            self.tokens.append(Token(TokenType.NUMBER, '0', self.line, self.column))
                        elif text in ('nullptr', 'null'):
                            self.tokens.append(Token(TokenType.NUMBER, '0', self.line, self.column))
                        elif text == 'INT_MAX':
                            self.tokens.append(Token(TokenType.NUMBER, '2147483647', self.line, self.column))
                        elif text == 'INT_MIN':
                            self.tokens.append(Token(TokenType.NUMBER, '-2147483648', self.line, self.column))
                        elif text == 'LONG_MAX':
                            self.tokens.append(Token(TokenType.NUMBER, '9223372036854775807', self.line, self.column))
                        elif text == 'LONG_MIN':
                            self.tokens.append(Token(TokenType.NUMBER, '-9223372036854775808', self.line, self.column))
                        elif text == 'UINT_MAX':
                            self.tokens.append(Token(TokenType.NUMBER, '4294967295', self.line, self.column))
                        elif text == 'SIZE_MAX':
                            self.tokens.append(Token(TokenType.NUMBER, '18446744073709551615', self.line, self.column))
                        elif text == 'DBL_MAX':
                            self.tokens.append(Token(TokenType.NUMBER, '1.7976931348623157e+308', self.line, self.column))
                        elif text == 'FLT_MAX':
                            self.tokens.append(Token(TokenType.NUMBER, '3.4028235e+38', self.line, self.column))
                        elif text in ('break', 'continue', 'const', 'constexpr', 'static',
                                      'inline', 'extern', 'virtual', 'override', 'final',
                                      'explicit', 'mutable', 'namespace', 'using', 'typedef',
                                      'typename', 'template', 'auto', 'decltype', 'noexcept',
                                      'throw', 'try', 'catch', 'switch', 'case', 'default',
                                      'do', 'goto', 'enum', 'sizeof', 'alignof', 'operator',
                                      'friend', 'static_assert', 'move', 'forward', 'class',
                                      'struct', 'public', 'private', 'protected', 'new', 'delete'):
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
