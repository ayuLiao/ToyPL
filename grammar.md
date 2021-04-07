## 文法

支持多行编程

statements  : NEWLINE* expr (NEWLINE+ statement)* NEWLINE*

statement   : KEYWORD:return expr?
            : KEYWORD:continue
            : KEYWORD:break
            : expr

expr        : KEYWORD:var IDENTIFIER EQ expr
            : comp-expr ((KEYWORD:and | KEYWORD:or) comp-expr)*

comp-expr   : NOT comp-expr
            : arith-expr ((EE | LT | GT | LTE | GTE) arith-expr)*

arith-expr  : term ((PLUS | MINUS) term)*

term        : factor (MUL | DIV) factor)*

factor      : (PLUS | MINUS) factor
            : power
        
power       : call (POW factor)*

call        : atom (LPAREN (expr (COMMA expr)*)? RPAREN)?

atom        : INT | FLOAT | STRING | IDENTIFIER
            : LPAREN expr RPAREN
            : list-expr
            : if-expr
            : for-expr
            : while-expr
            : func-expr
            
list-exp    : LSQUARE (expr (COMMA expr)*)? RESQUARE // [1,2,3]
                 
if-expr     : KEYWORD:if statement KEYWORD:then
              (expr if-expr-b | if-expr-c?) | (NEWLINE statements KEYWORD:end | if-expr-b | if-expr-c)
              
if-expr-b   : KEYWORD:elif statement KEYWORD:then
              (expr if-expr-b | if-expr-c?) | (NEWLINE statements KEYWORD:end | if-expr-b | if-expr-c)
              
if-expr-c   : KEYWORD:else
              statement | (NEWLINE statments KEYWORD:end)
                          
for-expr    : KEYWORD:for IDENTIFIER EQ expr KEYWORD:to expr
              (KEYWORD:step expr)? KEYWROD: then 
              // 如果没有NEWLINE，则只是单纯的statement，如果有NEWLINE则说明有换行
              statement | (NEWLINE statements KEYWORD:end)
              
while-expr  : KEYWORD:while expr KEYWROD:then
              statement | (NEWLINE statements KEYWORD:end)
    
// 支持匿名函数          
func-expr   : KEYWORD func IDENTIFIER?
              LPAREN (IDENTIFIER (COMMA IDENTIFIER)*)? RPAREN
              (ARROW expr) | (NEWLINE statements KEYWORD:end)   
  
## 说明

*   0次或多次
?   0次或一次
+   1次或多次