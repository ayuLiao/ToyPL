from position import Position
from tokens import *
from error import *

class Lexer(object):
    """
    Lexer 词法分析
    """
    def __init__(self, fn, text):
        self.fn = fn # text来源 => 某个文件，方便报错定位
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text) # 位置
        self.current_char = None # 当前字符
        self.advance() # self.pos从-1开始，然后立刻调用self.advance

    def advance(self):
        """预读"""
        self.pos.advance(self.current_char)
        if self.pos.idx < len(self.text):
            self.current_char = self.text[self.pos.idx]
        else:
            self.current_char = None

    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in (' ', '\t'):
                # 为空格或制表符，直接跳过
                self.advance()
            elif self.current_char == '#':
                # 跳过注释
                self.skip_comment()
            elif self.current_char in DIGITS: # 识别数字
                tokens.append(self.make_number())

            elif self.current_char in LETTERS: # 识别字母
                tokens.append(self.make_identifier())

            elif self.current_char == '!':
                token, error = self.make_not_equals()
                if error:
                    return [], error
                tokens.append(token)
            elif self.current_char == '=':
                tokens.append(self.make_equals())
            elif self.current_char == '<':
                tokens.append(self.make_less_than())
            elif self.current_char == '>':
                tokens.append(self.make_greater_than())
            elif self.current_char == '^': # 幂操作 x^y => x的y次幂
                tokens.append(Token(TT_POW, pos_start=self.pos))
                self.advance()
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(self.make_minus_or_arrow())
            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.advance()
            elif self.current_char == '[':
                tokens.append(Token(TT_LSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == ']':
                tokens.append(Token(TT_RSQUARE, pos_start=self.pos))
                self.advance()
            elif self.current_char == ',':
                tokens.append(Token(TT_COMMA, pos_start=self.pos))
                self.advance()
            elif self.current_char == '"':
                tokens.append(self.make_string())
            elif self.current_char in ';\n': # 换行
                tokens.append(Token(TT_NEWLINE, pos_start=self.pos))
                self.advance()
            else:
                # 没有匹配任何Token，return some error
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")
        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens, None

    def skip_comment(self):
        # 跳过toypl中的注释
        self.advance()
        while self.current_char != '\n':
            self.advance()
        self.advance()

    def make_number(self):
        """
        识别数字
        :return:
        """
        num_str = ''
        dot_coumt = 0 # 点的个数 => . 小数点
        pos_start = self.pos.copy() # 拷贝，避免影响原self.pos

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_coumt == 1:
                    break # 只可有一个小数点
                dot_coumt += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()
        if dot_coumt == 0: # 整数
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

    def make_string(self):
        string = ''
        pos_start = self.pos.copy()
        escape_character = False # 是否为转义字符 => \"
        escape_characters = {
            'n': '\n',
            't': '\t'
        }

        self.advance()
        # 当前字符不为空 以及 (不为 " 或者是转义字符串 => \")
        while self.current_char != None and (self.current_char != '"' or escape_character):
            if escape_character:
                # 如果是转义字符，则需要获得字符原始的值
                string += escape_characters.get(self.current_char, self.current_char)
                escape_character = False
            else:
                if self.current_char == '\\': # python 中 \\ 其实就是当个 \
                    escape_character = True # 为转义字符
                else:
                    string += self.current_char # 普通字符，直接拼接则可

            self.advance()

        self.advance()
        return Token(TT_STRING, string, pos_start, self.pos)


    def make_identifier(self):
        """
        识别变量
        :return:
        """
        variable_str = ''
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in LETTERS_DIGITS + '_': # 运行变量名中存在下划线
            variable_str += self.current_char
            self.advance()

        # 如果字符串在KEYWORDS中，说明该Token是关键字，否则则是变量名
        if variable_str in KEYWORDS:
            tok_type = TT_KEYWORD
        else:
            tok_type = TT_IDENTIFIER

        return Token(tok_type, variable_str, pos_start, self.pos)

    def make_not_equals(self):
        """
        匹配 !=
        :return:
        """
        pos_start = self.pos.copy()

        self.advance()
        if self.current_char == '=': # != 不等于
            self.advance()
            return Token(TT_NE, pos_start=pos_start, pos_end=self.pos), None

        self.advance()
        return None, ExpectedCharError(pos_start, self.pos, "'=' (after '!')")

    def make_equals(self):
        """
        匹配 = 或 ==
        :return:
        """
        tok_type = TT_EQ
        pos_start = self.pos.copy()

        self.advance()
        if self.current_char == '=': # ==
            self.advance()
            tok_type = TT_EE
        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_less_than(self):
        """
        匹配 < 或 <=
        :return:
        """
        tok_type = TT_LT
        pos_start = self.pos.copy()

        self.advance()
        if self.current_char == '=': # <=
            self.advance()
            tok_type = TT_LTE
        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_greater_than(self):
        """
        匹配 > 或 >=
        :return:
        """
        tok_type = TT_GT
        pos_start = self.pos.copy()

        self.advance()
        if self.current_char == '=': # >=
            self.advance()
            tok_type = TT_GTE
        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)

    def make_minus_or_arrow(self):
        """
        匹配 - 或 ->
        :return:
        """
        tok_type = TT_MINUS
        pos_start = self.pos.copy()

        self.advance()
        if self.current_char == '>':
            self.advance()
            tok_type = TT_ARROW

        return Token(tok_type, pos_start=pos_start, pos_end=self.pos)