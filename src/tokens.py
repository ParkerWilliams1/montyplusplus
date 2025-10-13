from enum import Enum, auto

__all__ = ['Token', 'TokenType']


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
