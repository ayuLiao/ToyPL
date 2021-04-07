from tokens import *
from ast_node import *
from result import ParserResult
from error import InvalidSyntaxError


class Parser(object):
    """Parser 解析器"""

    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self):
        """
        从tokens列表中获得下一个token
        :return:
        """
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    def reverse(self, amount=1):
        """
        从当前位置（self.tok_idx）往前移动amount个位置，获取该位置对应的tokens，与advance函数是相反的操作

        :param amount: 往前amount步
        :return:
        """
        self.tok_idx -= amount
        self.update_current_tok()
        return self.current_tok

    def update_current_tok(self):
        """
        更新当前token
        如果往前了几步，那么当前的token也需要更新成前几步对应的token
        :return:
        """
        if self.tok_idx >= 0 and self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]

    def parse(self):
        # 语法解析Tokens

        # 从其实非终结符开始 => AST Root Node
        res = self.statements()
        if not res.error and self.current_tok.type != TT_EOF:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '+', '-', '*', '/', '^', '==', '!=', '<', '>', <=', '>=', 'AND' or 'OR'"
            ))
        return res

    def statements(self):
        """
        statements  : NEWLINE* expr (NEWLINE+ statement)* NEWLINE*
        :return:
        """
        res = ParserResult()
        statements = []
        pos_start = self.current_tok.pos_start.copy()

        while self.current_tok.type == TT_NEWLINE: # 换行
            res.register_advancement()
            self.advance()

        statement = res.register(self.statement())
        if res.error: return res
        statements.append(statement)

        more_statements = True
        while True:
            newline_count = 0
            while self.current_tok.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()
                newline_count += 1
            if newline_count == 0:
                more_statements= False
            # 没有下一行了，退出循环
            if not more_statements: break
            # ??? 为什么使用 try_register 而不是 register ?
            # 仔细观察规则： statements  :NEWLINE* statement (NEWLINE+ statement)* NEWLINE*
            # 其中 (NEWLINE+ statement)* NEWLINE* 表示：
            # (NEWLINE+ statement)*  (NEWLINE+ statement)整体可能出现0次或多次，如果至少出现一次，那么其中的NEWLINE可以出现1次或多次而其中的statement则比如出现
            # 规则的另外一部分，NEWLINE* 表示NEWLINE可能出现0次或多次
            # 注意，(NEWLINE+ statement)* 与 NEWLINE*  都以 NEWLINE 开头，也就说，上一个token为NEWLINE，那么它下一个token是否为statement，无法判断
            # 此时就需要做尝试，通过try_register方法尝试解析，如果解析失败了，则回退
            statement = res.try_register(self.statement())
            if not statement:
                # 解析失败，回退
                self.reverse(res.to_reverse_count)
                more_statements = False
                continue
            statements.append(statement)

        # 多行逻辑返回list
        return res.success(ListNode(statements, pos_start, self.current_tok.pos_end.copy()))

    def statement(self):
        """
        statement   : KEYWORD:return expr?
                    : KEYWORD:continue
                    : KEYWORD:break
                    : expr
        :return:
        """
        res = ParserResult()
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.matches(TT_KEYWORD, 'return'):
            res.register_advancement()
            self.advance()

            # KEYWORD:return expr? => expr? 表示expr出现0次或1次
            # 语法上运行起返回为空，即只有return关键字
            expr = res.try_register(self.expr())
            if not expr:
                self.reverse(res.to_reverse_count)
            return res.success(ReturnNode(expr, pos_start, self.current_tok.pos_start.copy()))

        if self.current_tok.matches(TT_KEYWORD, 'continue'):
            res.register_advancement()
            self.advance()
            return res.success(ContinueNode(pos_start, self.current_tok.pos_start.copy()))

        if self.current_tok.matches(TT_KEYWORD, 'break'):
            res.register_advancement()
            self.advance()
            return res.success(BreakNode(pos_start, self.current_tok.pos_start.copy()))

        expr = res.register(self.expr())
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'return', 'continue', 'break', 'var', 'if', 'for', 'where', 'fun', int, float, identifier, '+', '-', '(', '[' or 'not'"
            ))
        return res.success(expr)


    def if_expr(self):
        """
        if-expr     : KEYWORD:if expr KEYWORD:then
              (expr if-expr-b | if-expr-c?) | (NEWLINE statements KEYWORD:end | if-expr-b | if-expr-c)
        :return:
        """
        res = ParserResult()
        # 如果是if
        cases, else_case = res.register(self.if_expr_cases('if'))
        if res.error: return res
        return res.success(IfNode(cases, else_case))

    def if_expr_b(self):
        """
        if-expr-b   : KEYWORD:elif expr KEYWORD:then
              (expr if-expr-b | if-expr-c?) | (NEWLINE statements KEYWORD:end | if-expr-b | if-expr-c)
        :return:
        """
        return self.if_expr_cases('elif')

    def if_expr_c(self):
        """
        if-expr-c   : KEYWORD:else
              expr | (NEWLINE statments KEYWORD:end)
        :return:
        """
        res = ParserResult()
        else_case = None

        if self.current_tok.matches(TT_KEYWORD, 'else'):
            res.register_advancement()
            self.advance()

            if self.current_tok.type == TT_NEWLINE:
                res.register_advancement()
                self.advance()

                statements = res.register(self.statements())
                if res.error: return res
                else_case = (statements, True)

                if self.current_tok.matches(TT_KEYWORD, 'end'):
                    res.register_advancement()
                    self.advance()
                else:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected 'end'"
                    ))
            else:
                expr = res.register(self.statement())
                if res.error: return res
                else_case = (expr, False)

        return res.success(else_case)

    def if_expr_b_or_c(self):
        """if判断中，使用elif还是else"""
        res = ParserResult()
        cases, else_case = [], None

        if self.current_tok.matches(TT_KEYWORD, 'elif'):
            all_cases = res.register(self.if_expr_b())
            if res.error: return res
            cases, else_case = all_cases
        else:
            else_case = res.register(self.if_expr_c())
            if res.error: return res

        return res.success((cases, else_case))

    def if_expr_cases(self, case_keyword):
        """
        KEYWORD:case_keyword expr KEYWORD:then
              (expr if-expr-b | if-expr-c?) | (NEWLINE statements KEYWORD:end | if-expr-b | if-expr-c)

        :param case_keyword: if 或 elif
        :return:
        """
        res = ParserResult()
        cases = []
        else_case = None

        # 判断关键字是为 if 或 elif
        if not self.current_tok.matches(TT_KEYWORD, case_keyword):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                f"Expected '{case_keyword}'"
            ))

        res.register_advancement()
        self.advance()

        # 执行if或elif关键字后的expr，获得判断条件的condition
        condition = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'then"
            ))

        res.register_advancement()
        self.advance()

        # 如果是换行
        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()
            statements = res.register(self.statements())
            if res.error: return res
            cases.append((condition, statements, True))
            # 判断关键字是否为end，如果为end，则说明if判断只有一层，即
            # if <expr> then;
            #   <expr>;
            #   <expr>;
            # end
            if self.current_tok.matches(TT_KEYWORD, 'end'):
                res.register_advancement()
                self.advance()
            else:
                # 如果不为end，则说明if判断有多层，即
                # if <expr> then;
                #   <expr>;
                #   <expr>;
                # elif <expr> then;
                #   <expr>;
                #   <expr>;
                # else;
                #   <expr>;
                # end
                new_cases, else_case = res.register(self.if_expr_b_or_c())
                if res.error: return res
                cases.extend(new_cases)

        else:
            # 不是换行符; 则说明当前层语句只有一行，即
            # if <expr> then <expr>
            # 但如果if有多层，无法保证其他是否会换行，如elif层可能会换行
            # if <expr> then <expr> elif <expr> then;
            expr = res.register(self.statement())
            if res.error: return res
            cases.append((condition, expr, False))
            # 调用if_expr_b_or_c方法，无论其他层是否换行，都可以通过递归调用来解决
            new_cases, else_case = res.register(self.if_expr_b_or_c())
            if res.error: return res
            cases.extend(new_cases)
        return res.success((cases, else_case))

    def for_expr(self):
        """
        for-expr    : KEYWORD:for IDENTIFIER EQ expr KEYWORD:to expr
              (KEYWORD:step expr)? KEYWROD: then expr | (NEWLINE statements KEYWORD:end)

        var res = 1
        for var i = 1 to 10 then
            var res = res * i
        :return:
        """
        res = ParserResult()

        if not self.current_tok.matches(TT_KEYWORD, 'for'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'for'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type != TT_IDENTIFIER:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'identifier'"
            ))

        var_name = self.current_tok
        res.register_advancement()
        self.advance()

        if self.current_tok.type != TT_EQ:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'identifier'"
            ))

        res.register_advancement()
        self.advance()
        start_value = res.register(self.expr()) # for循环起始值
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'to'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected 'to'"
            ))

        res.register_advancement()
        self.advance()
        end_value = res.register(self.expr()) # for循环结束值

        if res.error: return res

        if self.current_tok.matches(TT_KEYWORD, 'step'): # 单次循环跳跃多少元素
            res.register_advancement()
            self.advance()
            step_value = res.register(self.expr())
            if res.error: return res

        else:
            step_value = None

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected 'then'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()

            body = res.register(self.statements())
            if res.error: return res

            if not self.current_tok.matches(TT_KEYWORD, 'end'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'end'"
                ))

            res.register_advancement()
            self.advance()

            return res.success(ForNode(var_name, start_value, end_value, step_value, body, True))

        body = res.register(self.statement())
        if res.error: return res

        return res.success(ForNode(var_name, start_value, end_value, step_value, body, False))

    def while_expr(self):
        """
        while-expr  : KEYWORD:while expr KEYWROD:then
              statement | (NEWLINE statements KEYWORD:end)

        var i = 0
        while i < 10 then
            var i = i + 1
        :return:
        """
        res = ParserResult()

        if not self.current_tok.matches(TT_KEYWORD, 'while'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected 'while'"
            ))

        res.register_advancement()
        self.advance()

        condition = res.register(self.expr())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'then'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'then'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_NEWLINE:
            res.register_advancement()
            self.advance()
            # 调用statements方法，递归解析多行逻辑
            body = res.register(self.statements())
            if res.error: return res

            if not self.current_tok.matches(TT_KEYWORD, 'end'):
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected 'end'"
                ))

            res.register_advancement()
            self.advance()

            return res.success(WhileNode(condition, body, True))

        body = res.register(self.statement())
        if res.error: return res

        return res.success(WhileNode(condition, body, False))

    def func_expr(self):
        """
        解析函数定义
        func-expr   : KEYWORD func IDENTIFIER?
              LPAREN (IDENTIFIER (COMMA IDENTIFIER)*)? RPAREN
              ARROW expr
        :return:
        """
        res = ParserResult()

        if not self.current_tok.matches(TT_KEYWORD, 'func'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
            "Expected 'func'"
            ))

        res.register_advancement()
        self.advance()

        if self.current_tok.type == TT_IDENTIFIER: # 函数名
            var_name_tok = self.current_tok
            res.register_advancement()
            self.advance()
            # 函数名后必然跟着 ( => func a(
            if self.current_tok.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '('"
                ))
        else:
            var_name_tok = None # 匿名函数
            # 匿名函数后，直接跟 (
            if self.current_tok.type != TT_LPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier or '('"
                ))

        res.register_advancement()
        self.advance()
        arg_name_toks = []

        # 参数名，函数至少有一个参数 => func a(x
        if self.current_tok.type == TT_IDENTIFIER:
            arg_name_toks.append(self.current_tok)
            res.register_advancement()
            self.advance()
            # 参数中有逗号分隔，则有多个参数 => func a(x,y
            while self.current_tok.type == TT_COMMA:
                res.register_advancement()
                self.advance()
                if self.current_tok.type != TT_IDENTIFIER:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected identifier"
                    ))

                # 将参数添加到arg_name_toks列表中
                arg_name_toks.append(self.current_tok)
                res.register_advancement()
                self.advance()

            # 参数匹配完后，就需要匹配右括号 => func a(x,y)
            if self.current_tok.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected , or ')'"
                ))

        else: # 函数定义时，可以没有参数 => func a()
            if self.current_tok.type != TT_RPAREN:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier or ')'"
                ))

        res.register_advancement()
        self.advance()
        # func a (x,y) ->
        if self.current_tok.type == TT_ARROW: # (ARROW expr)

            res.register_advancement()
            self.advance()
            # 解析函数体中的逻辑，获得该函数的返回值
            node_to_return = res.register(self.expr())
            if res.error: return res
            # should_auto_return设置为True，表示自动返回，此时的函数为一行函数，不需要通过return关键字返回内容
            # func add(a,b) -> a + b  => add函数会返回 a+b 的结果
            return res.success(FuncNode(var_name_tok, arg_name_toks, node_to_return, True))

        if self.current_tok.type != TT_NEWLINE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '->' or ';' "
            ))

        res.register_advancement()
        self.advance()

        body = res.register(self.statements())
        if res.error: return res

        if not self.current_tok.matches(TT_KEYWORD, 'end'):
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected 'end' "
            ))

        res.register_advancement()
        self.advance()
        # 此时的函数为多行函数，需要通过return关键字才可返回
        #  func add(a,b); return a + b; end
        return res.success(FuncNode(var_name_tok, arg_name_toks, body, False))

    def call(self):
        """
        解析函数调用
        call        : atom (LPAREN (expr (COMMA expr)*)? RPAREN)
        a(1+2, 3+4)
        """

        res = ParserResult()

        atom = res.register(self.atom())
        if res.error: return res

        if self.current_tok.type == TT_LPAREN:
            res.register_advancement()
            self.advance()
            arg_nodes = []

            # 调用函数时，没有传参数
            if self.current_tok.type == TT_RPAREN:
                res.register_advancement()
                self.advance()
            else:
                # 调用函数时，参数可以写成expr，expr也包含INT|FLOAT|IDENTIFIER等 => a(1+2
                arg_nodes.append(res.register(self.expr()))
                if res.error:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ')', 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(' or 'NOT'"
                    ))

                # 多个参数，由逗号分开
                while self.current_tok.type == TT_COMMA:
                    res.register_advancement()
                    self.advance()
                    # 将调用参数添加到arg_nodes列表中
                    arg_nodes.append(res.register(self.expr()))
                    if res.error: return res

                # a(1+2, 3)
                if self.current_tok.type != TT_RPAREN:
                    return res.failure(InvalidSyntaxError(
                        self.current_tok.pos_start, self.current_tok.pos_end,
                        "Expected ',' or ')'"
                    ))

                res.register_advancement()
                self.advance()

            return res.success(CallNode(atom, arg_nodes))
        return res.success(atom)

    def atom(self):
        """
        atom        : INT|FLOAT|IDENTIFIER
                    : LPAREN expr RPAREN
                    : if-expr
                    : for-expr
                    : while-expr
                    : func-expr
        :return:
        """
        res = ParserResult()
        tok = self.current_tok

        # atom  : INT|FLOAT
        if tok.type in (TT_INT, TT_FLOAT):
            res.register_advancement()
            self.advance()
            return res.success(NumberNode(tok))

        # atom  : STRINg
        elif tok.type == TT_STRING:
            res.register_advancement()
            self.advance()
            return res.success(StringNode(tok))

        # atom  : IDENTIFIER
        elif tok.type == TT_IDENTIFIER:
            res.register_advancement()
            self.advance()
            # 访问变量时，只会输入单独的变量名
            return res.success(VarAccessNode(tok))

        # atom : LPAREN expr RPAREN => (1 + 2) * 3
        elif tok.type == TT_LPAREN:
            self.advance()
            expr = res.register(self.expr())
            if res.error:
                return res

            if self.current_tok.type == TT_RPAREN:
                self.advance()
                return res.success(expr)
            else:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')'"
                ))

        elif tok.type == TT_LSQUARE:
            list_expr = res.register(self.list_expr())
            if res.error: return res
            return res.success(list_expr)

        # atom : if-expr
        elif tok.matches(TT_KEYWORD, 'if'):
            if_expr = res.register(self.if_expr())
            if res.error: return res
            return res.success(if_expr)

        # atom : for-expr
        elif tok.matches(TT_KEYWORD, 'for'):
            for_expr = res.register(self.for_expr())
            if res.error: return res
            return res.success(for_expr)

        # atom : while-expr
        elif tok.matches(TT_KEYWORD, 'while'):
            while_expr = res.register(self.while_expr())
            if res.error: return res
            return res.success(while_expr)

        # atom : func-expr
        elif tok.matches(TT_KEYWORD, 'func'):
            func_expr = res.register(self.func_expr())
            if res.error: return res
            return res.success(func_expr)

        return res.failure(InvalidSyntaxError(
            tok.pos_start, tok.pos_end,
            # 报错中，期望的值中不包含var，虽然其文法中包含expr（LPAREN expr RPAREN），而expr中又包含var KEYWORD
            # 但这里并不存赋值的情况，所以报错中不包含var
            # 编程语言中的错误提示非常重要，所以要尽可能保持正确
            "Expected int, float, identifier, '+', '-', '(', 'IF', 'FOR', 'WHILE', 'FUN'"
        ))

    def list_expr(self):
        """
        List
        :return:
        """
        res = ParserResult()
        element_nodes = []
        pos_start = self.current_tok.pos_start.copy()

        if self.current_tok.type != TT_LSQUARE:
            return res.failure(InvalidSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '['"
            ))

        res.register_advancement()
        self.advance()
        # 空列表 => []
        if self.current_tok.type == TT_RSQUARE:
            res.register_advancement()
            self.advance()
        else:
            # 非空列表 => [1,2,3]
            element_nodes.append(res.register(self.expr()))
            if res.error:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ']', 'VAR', 'IF', 'FOR', 'WHILE', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'NOT'"
                ))

            # 匹配list中的元素
            while self.current_tok.type == TT_COMMA:
                res.register_advancement()
                self.advance()

                element_nodes.append(res.register(self.expr()))
                if res.error: return res

            if self.current_tok.type != TT_RSQUARE:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ',' or ']''"
                ))

            res.register_advancement()
            self.advance()

        return res.success(ListNode(element_nodes, pos_start, self.current_tok.pos_end.copy()))

    def power(self):
        """
        power       : call (POW factor)*
        :return:
        """
        return self.bin_op(self.call, (TT_POW,), self.factor)

    def factor(self):
        """
        factor  : (PLUS|MINUS) factor
                : power
        :return:
        """
        res = ParserResult()
        tok = self.current_tok

        # factor  : (PLUS|MINUS) factor
        if tok.type in (TT_PLUS, TT_MINUS):
            res.register_advancement()
            self.advance()
            factor = res.register(self.factor())
            if res.error: return res
            # UnaryOpNode 一元操作 => (PLUS|MINUS) factor
            return res.success(UnaryOpNode(tok, factor))
        # factor    : power
        return self.power()

    def term(self):
        """
        term    : factor (MUL|DIV) factor)*
        :return:
        """
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def comp_expr(self):
        res = ParserResult()

        # comp-expr   : NOT comp-expr
        if self.current_tok.matches(TT_KEYWORD, 'not'):
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()
            node = res.register(self.comp_expr())
            if res.error: return res
            return res.success(UnaryOpNode(op_tok, node))
        else:
            # comp-expr    : arith-expr ((EE|LT|GT|LTE|GTE) arith-expr)*
            node = res.register(self.bin_op(self.arith_expr, (TT_EE, TT_NE, TT_LT, TT_GT, TT_LTE, TT_GTE)))
            if res.error:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected int, float, identifier, '+', '-', '(' or 'not'"
                ))
            return res.success(node)

    def arith_expr(self):
        # arith-expr  : term ((PLUS|MINUS) term)*
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def expr(self):
        """
        表达式
        expr    : KEYWORD:var IDENTIFIER EQ expr
                : term ((PLUS|MINUS) term)*
        :return:
        """
        res = ParserResult()

        # 如果token为var，则是声明语句
        # expr    : KEYWORD:var IDENTIFIER EQ expr
        if self.current_tok.matches(TT_KEYWORD, 'var'):
            res.register_advancement()
            self.advance()

            if self.current_tok.type != TT_IDENTIFIER:
                # 不是变量名，语法异常，报错
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected identifier"
                ))

            var_name = self.current_tok
            res.register_advancement()
            self.advance()
            if self.current_tok.type != TT_EQ:
                # 表示等号，语法异常，报错
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected '='"
                ))

            res.register_advancement()
            self.advance()
            # 变量赋值时，右值为表达式expr，此时可以调用self.expr() 递归处理
            # 此外，等于操作符不会出现在生成树中
            # basic > var a = 1
            # [KEYWORDS:var, IDENTIFIER:a, EQ, INT:1, EOF]
            # (IDENTIFIER:a, INT:1) => EQ 不存在
            # 1
            expr = res.register(self.expr())
            if res.error: return res
            # 赋值操作 var a = 1 + 4 => KEYWORD: var, Identifier: a, expr: 1 + 4
            return res.success(VarAssignNode(var_name, expr))
        else:
            node = res.register(self.bin_op(self.comp_expr, ((TT_KEYWORD, 'and'), (TT_KEYWORD, 'or'))))
            if res.error:
                return res.failure(InvalidSyntaxError(
                    self.current_tok.pos_end, self.current_tok.pos_end,
                    # 期望的值中，包含var
                    "Expected 'var', int, float, identifier, '+', '-', '(' or 'not'"
                ))
            return res.success(node)


    def bin_op(self, func_a, ops, func_b=None):
        if func_b == None:
            func_b = func_a
        res = ParserResult()
        left = res.register((func_a()))  # 递归调用
        if res.error: return res

        while self.current_tok.type in ops or (self.current_tok.type, self.current_tok.value) in ops:
            op_tok = self.current_tok
            res.register_advancement()
            self.advance()
            right = res.register(func_b())
            if res.error: return res
            left = BinOpNode(left, op_tok, right)
        return res.success(left)
