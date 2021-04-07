from string_with_arrows import *

class Error(object):
    def __init__(self, pos_start, pos_end, error_name, details):
        """
        :param pos_start: 错误其实位置
        :param pos_end: 错误终止位置
        :param error_name: 错误类型名称
        :param details: 错误细节
        """
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f'{self.error_name}: {self.details}'
        # 更加细致的错误信息
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        # string_with_arrows()方法的效果 => 为了更清晰的标注出报错的位置
        # basic > 4 *
        # Invalid Syntax: Expected int or floatFile <stdin>, line 1
        # 4 *
        #    ^
        result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        # Illegal Character => 非法字符
        super().__init__(pos_start, pos_end, "Illegal Character", details)

class ExpectedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        # Expected Character => 预期字符
        super().__init__(pos_start, pos_end, 'Expected Character', details)

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        # Invalid Syntax => 无效的语法
        super().__init__(pos_start, pos_end, 'Invalid Syntax', details)

class RTError(Error):
    def __init__(self, pos_start, pos_end, detail, context):
        super().__init__(pos_start, pos_end, "Runtime Error", detail)
        self.context = context

    def as_string(self):
        result = self.generate_traceback()
        result += f'{self.error_name}: {self.details}'
        result += '\n\n' + string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

    def generate_traceback(self):
        """
        生成错误栈信息
        :return:
        """
        result = ''
        pos = self.pos_start
        ctx = self.context

        # 遍历运行时的上下文环境，构建错误栈信息，例如：
        # Traceback (most recent call last):
        #  File <stdin>, line 1, in <program>
        # Runtime Error: Division by zero
        #
        # 1 / 0
        #     ^
        while ctx:
            # pos.fn => 报错文件; pos.ln + 1 => 报错行; ctx.display_name => 报错上下文; result => 报错详情
            result = f' File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n' + result
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return 'Traceback (most recent call last):\n' + result