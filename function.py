import os

from symbol_table import SymbolTable
from result import RTResult
from context import Context
from type_operate import *
from error import *


class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or "<anonymous>"

    def generate_new_context(self):
        """
        创建上下文
        :return:
        """

        # 为函数创建新的上下文，每个函数都有独立的上下文
        # 其parent.context为调该用函数的对象的context，即self.context
        new_context = Context(self.name, self.context, self.pos_start)
        # 为函数创建新的符号表，每个函数都有独立的符号表
        # 其parent.symbol_table为调用该函数的对象的symbol_table
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context

    def check_args(self, arg_names, args):
        """
        检测函数参数
        :param arg_names: 函数参数名
        :param args: 函数参数值
        :return:
        """
        res = RTResult()

        # 调用函数时传入的参数多于函数定义中的参数
        if len(args) > len(arg_names):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"{len(args) - len(arg_names)} too many args passed into '{self.name}'",
                self.context
            ))

        # 调用函数时传入的参数多于函数定义中的参数
        if len(args) < len(arg_names):
            return res.failure(RTError(
                self.pos_start, self.pos_end,
                f"{len(args) - len(arg_names)} too few args passed into '{self.name}'",
                self.context
            ))

        return res.success(None)

    def populate_args(self, arg_names, args, exec_ctx):
        """
        将函数参数添加到函数上下文的符号表中
        :param arg_names: 函数参数名
        :param args: 函数参数
        :param exec_ctx: 函数上下文
        :return:
        """

        for i in range(len(args)):
            arg_name = arg_names[i]
            arg_value = args[i]
            # 更新当前节点的上下文，方便报错时定位
            arg_value.set_context(exec_ctx)
            # 将调用函数时，传入的参数值存入函数符号表中
            exec_ctx.symbol_table.set(arg_name, arg_value)

    def check_and_populate_args(self, arg_names, args, exec_ctx):
        res = RTResult()
        res.register(self.check_args(arg_names, args))
        if res.should_return(): return res
        self.populate_args(arg_names, args, exec_ctx)
        return res.success(None)


class Function(BaseFunction):
    def __init__(self, name, body_node, arg_names, should_auto_return):
        """
        函数对象
        :param name: 函数名
        :param body_node: 函数体
        :param arg_names: 函数参数
        """
        super().__init__(name)
        # anonymous 匿名
        self.body_node = body_node
        self.arg_names = arg_names
        self.should_auto_return = should_auto_return

    def execute(self, args, interpreter):
        """
        执行函数
        :param args: 执行函数时，传入的参数
        :return:
        """
        res = RTResult()
        # 为函数单独创建新的解释器
        # interpreter = Interpreter()
        exec_ctx = self.generate_new_context()
        res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
        if res.should_return(): return res

        # 通过解释器执行函数体中的逻辑
        value = res.register(interpreter.visit(self.body_node, exec_ctx))
        # 如果函数应该返回且函数返回值（func_return_value）为None，则直接返回res
        if res.should_return() and res.func_return_value == None:
            return res
        # 如果应该自动返回
        ret_value = (value if self.should_auto_return else None) or res.func_return_value or Number.null

        return res.success(ret_value)

    def copy(self):
        copy = Function(self.name, self.body_node, self.arg_names, self.should_auto_return)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<function {self.name}>"


class BuiltInFunction(BaseFunction):
    """
    内建函数
    """

    def __init__(self, name):
        super().__init__(name)

    def execute(self, args, _):
        """
        执行内建函数
        :param args: 函数参数
        :return:
        """
        res = RTResult()
        exec_ctx = self.generate_new_context()

        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)

        # 检测函数参数以及将参数填充到函数上下文的符号表中
        res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
        if res.should_return(): return res

        # 调用内建函数
        return_value = res.register(method(exec_ctx))
        if res.should_return(): return res
        return res.success(return_value)

    def no_visit_method(self, node, context):
        raise Exception(f'No execute_{self.name} method defined!')

    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.pos_start, self.pos_end)
        return copy

    def __repr__(self):
        return f"<built-in function {self.name}>"

    #########  内建函数  ###########

    def execute_print(self, exec_ctx):
        """打印内容"""
        return RTResult().success(String(str(exec_ctx.symbol_table.get('value'))))

    # 定义该函数的参数
    # BuiltInFunction -> self.check_and_populate_args(method.arg_names, args, exec_ctx)方法
    # 将方法的arg_names作为函数参数名与对应的参数值存入符号表中，所以这里才以这种方式定义函数的参数
    execute_print.arg_names = ['value']

    def execute_input(self, exec_ctx):
        """输入内容"""
        text = input()
        return RTResult().success(String(text))
    execute_input.arg_names = []

    def execute_clear(self, exec_ctx):
        """清空终端输出"""
        if os.name == 'posix': # MacOS
            os.system('clear') # MacOS/Linxu 清理屏幕命令
        else:
            os.system('cls') # Windows 清理屏幕命令
        return RTResult().success(Number.null)
    execute_clear.arg_names = []

    def execute_is_number(self, exec_ctx):
        """判断是否为Number类型"""
        is_number = isinstance(exec_ctx.symbol_table.get('value'), Number)
        return RTResult().success(Number.true if is_number else Number.false)
    execute_is_number.arg_names = ['value']

    def execute_is_string(self, exec_ctx):
        """判断是否为String类型"""
        is_string = isinstance(exec_ctx.symbol_table.get('value'), String)
        return RTResult().success(Number.true if is_string else Number.false)
    execute_is_string.arg_names = ['value']

    def execute_is_list(self, exec_ctx):
        """判断是否为List类型"""
        is_list = isinstance(exec_ctx.symbol_table.get('value'), List)
        return RTResult().success(Number.true if is_list else Number.false)
    execute_is_list.arg_names = ['value']

    def execute_is_function(self, exec_ctx):
        """判断是否为func类型"""
        is_func = isinstance(exec_ctx.symbol_table.get('value'), BaseFunction)
        return RTResult().success(Number.true if is_func else Number.false)
    execute_is_list.arg_names = ['value']

    def execute_append(self, exec_ctx):
        """
        向list中添加元素
        非就地操作
        append([1,2,3], 4) => 返回结果：[1,2,3,4]，但原本的列表[1,2,3]并没有改变
        """
        list_ = exec_ctx.symbol_table.get('list')
        value = exec_ctx.symbol_table.get('value')

        if not isinstance(list_, List):
            return RTResult.failure(RTError(
                self.pos_start, self.pos_end,
                # append内置方法的第一个参数必须为list
                "First argument must be list",
                exec_ctx
            ))

        list_.elements.append(value)
        return RTResult().success(list_)
    execute_append.arg_names = ["list", "value"]

    def execute_pop(self, exec_ctx):
        """
        删除列表中index下标对应的元素
        :param exec_ctx:
        :return:
        """
        list_ = exec_ctx.symbol_table.get('list')
        index = exec_ctx.symbol_table.get('index')

        if not isinstance(list_, List):
            return RTResult.failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be list",
                exec_ctx
            ))

        if not isinstance(index, Number):
            return RTResult.failure(RTError(
                self.pos_start, self.pos_end,
                "Secord argument must be number",
                exec_ctx
            ))

        try:
            element = list_.elements.pop(index.value)
        except:
            return RTResult.failure(RTError(
                self.pos_start, self.pos_end,
                'Element at this index could not be removed from list because index is out of bounds',
                exec_ctx
            ))

        return RTResult().success(element)
    execute_pop.arg_names = ["list", "index"]

    def execute_extend(self, exec_ctx):
        list_1 = exec_ctx.symbol_table.get("list_1")
        list_2 = exec_ctx.symbol_table.get("list_2")

        if not isinstance(list_1, List):
            return RTResult.failure(RTError(
                self.pos_start, self.pos_end,
                "First argument must be list",
                exec_ctx
            ))

        if not isinstance(list_2, List):
            return RTResult.failure(RTError(
                self.pos_start, self.pos_end,
                "Secord argument must be list",
                exec_ctx
            ))

        list_1.elements.extend(list_2.elements)
        return RTResult().success(list_1)
    execute_extend.arg_names = ["list_1", "list_2"]

    def execute_len(self, exec_ctx):
        """获得list的长度"""
        list_ = exec_ctx.symbol_table.get('list')
        if not isinstance(list_, List):
            return RTResult().failure(RTError(
                self.pos_start, self.pos_end,
                "Argment must be list",
                exec_ctx
            ))

        return RTResult().success(Number(len(list_.elements)))
    execute_len.arg_names = ["list"]


# 内建函数
BuiltInFunction.print       = BuiltInFunction("print")
BuiltInFunction.input       = BuiltInFunction("input")
BuiltInFunction.clear       = BuiltInFunction("clear")
BuiltInFunction.is_number   = BuiltInFunction("is_number")
BuiltInFunction.is_string   = BuiltInFunction("is_string")
BuiltInFunction.is_list     = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append      = BuiltInFunction("append")
BuiltInFunction.pop         = BuiltInFunction("pop")
BuiltInFunction.extend      = BuiltInFunction("extend")
BuiltInFunction.len         = BuiltInFunction("len")
