class ParserResult(object):
    """解析器结果类"""

    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0 # 便于选择不同的报错，具体看failure方法
        self.last_registered_advance_count = 0
        self.to_reverse_count = 0 # 反向操作个数

    def register_advancement(self):
        self.advance_count += 1
        self.last_registered_advance_count = 1

    def register(self, parser_result):
        self.last_registered_advance_count = parser_result.advance_count
        self.advance_count += parser_result.advance_count
        if parser_result.error:
            self.error = parser_result.error
        return parser_result.node

    def try_register(self, parser_result):
        if parser_result.error:
            # 失败，则记录要回退的步数，用于回到执行前，所在的tokens列表中的位置
            self.to_reverse_count = parser_result.advance_count
            return None
        return self.register(parser_result)

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        # 使用advance_count来选择显示的报错信息
        if not self.error or self.last_registered_advance_count == 0:
            self.error = error
        return self


class RTResult(object):
    """RunTime 运行时结果类"""
    
    def __init__(self):
        self.reset()

    def reset(self):
        self.value = None
        self.error = None
        self.func_return_value = None
        self.loop_should_continue = False
        self.loop_should_break = False

    def register(self, res):
        if res.error:
            self.error = res.error
        self.func_return_value = res.func_return_value
        self.loop_should_continue = res.loop_should_continue
        self.loop_should_break = res.loop_should_break
        return res.value

    def success(self, value):
        self.reset()
        self.value = value
        return self

    def success_return(self, value):
        self.reset()
        self.func_return_value = value
        return self

    def success_continue(self):
        self.reset()
        self.loop_should_continue = True
        return self

    def success_break(self):
        self.reset()
        self.loop_should_break = True
        return self

    def should_return(self):
        # 其中一个为True，则返回True
        # 即：self.error 存错误，返回True；
        # self.func_return_value函数有返回值返回True；
        # self.loop_should_continue跳过此次循环返回True
        # self.loop_should_break 跳出此次循环返回True
        return (
            self.error or
            self.func_return_value or
            self.loop_should_continue or
            self.loop_should_break
        )

    def failure(self, error):
        self.reset()
        self.error = error
        return self