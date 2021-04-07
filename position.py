class Position(object):
    """
    行号、列号、当前索引，便于定位报错
    """
    def __init__(self, idx, ln, col, fn, ftxt):
        """
        用于记录位置信息，便于报错时给出具体报错的文件与位置
        :param idx: 索引
        :param ln: 行号
        :param col: 列号
        :param fn: 文件名（定义报错用）
        :param ftxt: 内容
        """
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char=None):
        """
        读取下一个字符时
        :param current_char: 当前字符
        :return:
        """
        self.idx += 1 # 索引 + 1
        self.col += 1 # 列号 + 1

        if current_char == '\n': # 换行符
            self.ln += 1 # 行号 + 1
            self.col += 0 # 列号 归零

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)