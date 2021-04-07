import string

"""
Constant 常量
"""

# DIGITS 数字
DIGITS = '0123456789'
# LETTERS 字母
LETTERS = string.ascii_letters # A~Z + a~z
LETTERS_DIGITS = LETTERS + DIGITS


"""
Tokens
"""

# Token type => TT
TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS" # 减法
TT_MUL = "MUL"
TT_DIV = "DIV" # 除法
TT_LPAREN = "LPAREN"
TT_RPAREN = "RPAREN"
TT_EOF = "EOF" # 终止符
TT_EQ = "EQ" # =
TT_POW = "POW" # 幂
TT_IDENTIFIER = "IDENTIFIER" # 标识符
TT_KEYWORD = "KEYWORD" # 关键字
TT_EE = "EE" # ==
TT_NE = "NE" # !=
TT_LT = "LT" # <
TT_GT = "GT" # >
TT_LTE = "LTE" # <=
TT_GTE = "GTE" # >=
TT_COMMA = "COMMA" # ,
TT_ARROW = "ARROW" # -> 中的箭头 >
TT_STRING = "STRING" # 字符串
TT_LSQUARE = "LSQUARE" # [
TT_RSQUARE = "RSQUARE" # ]
TT_NEWLINE = "NEWLINE" # ;\n 新的一行


KEYWORDS = [
    'var',
    'and',
    'or',
    'not',
    'if',
    'then',
    'elif',
    'else',
    'for',
    'to',
    'step',
    'while',
    'func',
    'end',
    'return',
    'continue',
    'break'
]

class Token(object):
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        # Token = <token-name, attribute-value>
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end

    def matches(self, type_, value):
        """
        判断Token是否相同
        """
        return self.type == type_ and self.value == value

    def __repr__(self):
        if self.value:
            return f'{self.type}:{self.value}'
        return f'{self.type}'