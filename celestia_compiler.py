"""
Celestia Compiler
A beginner-friendly toy language compiler written in Python.

This version implements a real compiler-style pipeline:

1. Lexer: converts source code into tokens
2. Parser: converts tokens into an Abstract Syntax Tree (AST)
3. Semantic Analyzer: checks variables, types, and invalid assignments
4. Code Generator: translates Celestia code into executable Python code
5. Runner: optionally runs the generated Python code

Supported Celestia features:
- num, String, Boolean declarations
- variable updates
- arithmetic expressions
- comparison expressions
- print statements
- if / else statements
- while loops
- // single-line comments
- /* block comments */
- reserved keyword protection
- file input support

Example Celestia program:

num score = 80
score = score + 15
print score

if score >= 90 {
    print "Great job"
} else {
    print "Keep practicing"
}

Run:
    python celestia_compiler.py example.cel
    python celestia_compiler.py example.cel --run
    python celestia_compiler.py example.cel --out output.py
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, List, Optional
import argparse
import re
import sys


# ============================================================
# Token Model
# ============================================================

@dataclass
class Token:
    type: str
    value: str
    line: int
    column: int


KEYWORDS = {
    "num",
    "String",
    "Boolean",
    "if",
    "else",
    "while",
    "print",
    "true",
    "false",
}

TYPE_KEYWORDS = {"num", "String", "Boolean"}


# ============================================================
# Lexer
# ============================================================

class LexerError(Exception):
    pass


class Lexer:
    TOKEN_SPEC = [
        ("NUMBER",   r"\d+(\.\d+)?"),
        ("STRING",   r'"([^"\\]|\\.)*"'),
        ("ID",       r"[A-Za-z][A-Za-z0-9_]*"),
        ("OP",       r"==|!=|<=|>=|\+|-|\*|/|=|<|>"),
        ("LBRACE",   r"\{"),
        ("RBRACE",   r"\}"),
        ("LPAREN",   r"\("),
        ("RPAREN",   r"\)"),
        ("SEMICOLON", r";"),
        ("NEWLINE",  r"\n"),
        ("SKIP",     r"[ \t]+"),
        ("MISMATCH", r"."),
    ]

    def __init__(self, source: str):
        self.source = self._remove_comments(source)
        self.regex = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in self.TOKEN_SPEC))

    @staticmethod
    def _remove_comments(source: str) -> str:
        source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
        source = re.sub(r"//.*", "", source)
        return source

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        line = 1
        line_start = 0

        for match in self.regex.finditer(self.source):
            kind = match.lastgroup
            value = match.group()
            column = match.start() - line_start + 1

            if kind == "NEWLINE":
                line += 1
                line_start = match.end()
                continue

            if kind == "SKIP":
                continue

            if kind == "MISMATCH":
                raise LexerError(f"Line {line}, Column {column}: Unexpected character '{value}'")

            if kind == "ID" and value in KEYWORDS:
                kind = value.upper()

            tokens.append(Token(kind, value, line, column))

        tokens.append(Token("EOF", "", line, 1))
        return tokens


# ============================================================
# AST Nodes
# ============================================================

@dataclass
class Program:
    statements: List[Any]

@dataclass
class VarDecl:
    var_type: str
    name: str
    expr: Any

@dataclass
class Assignment:
    name: str
    expr: Any

@dataclass
class PrintStmt:
    expr: Any

@dataclass
class IfStmt:
    condition: Any
    then_body: List[Any]
    else_body: Optional[List[Any]]

@dataclass
class WhileStmt:
    condition: Any
    body: List[Any]

@dataclass
class BinaryOp:
    left: Any
    op: str
    right: Any

@dataclass
class Literal:
    value: Any
    literal_type: str

@dataclass
class Variable:
    name: str


# ============================================================
# Parser
# ============================================================

class ParserError(Exception):
    pass


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def current(self) -> Token:
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def advance(self) -> Token:
        tok = self.current()
        self.pos += 1
        return tok

    def match(self, *types: str) -> bool:
        if self.current().type in types:
            self.advance()
            return True
        return False

    def expect(self, token_type: str, message: str) -> Token:
        if self.current().type == token_type:
            return self.advance()
        tok = self.current()
        raise ParserError(f"Line {tok.line}: {message}. Got '{tok.value or tok.type}'")

    def parse(self) -> Program:
        statements = []
        while self.current().type != "EOF":
            statements.append(self.statement())
        return Program(statements)

    def statement(self) -> Any:
        tok = self.current()

        if tok.type in {"NUM", "STRING", "BOOLEAN"}:
            return self.var_decl()

        if tok.type == "ID":
            return self.assignment()

        if tok.type == "PRINT":
            return self.print_stmt()

        if tok.type == "IF":
            return self.if_stmt()

        if tok.type == "WHILE":
            return self.while_stmt()

        raise ParserError(
            f"Line {tok.line}: Expected declaration, assignment, print, if, or while statement. Got '{tok.value}'"
        )

    def var_decl(self) -> VarDecl:
        type_tok = self.advance()
        var_type = {
            "NUM": "num",
            "STRING": "String",
            "BOOLEAN": "Boolean",
        }[type_tok.type]

        name_tok = self.expect("ID", "Expected variable name after type")

        if name_tok.value in KEYWORDS:
            raise ParserError(f"Line {name_tok.line}: '{name_tok.value}' is a reserved keyword")

        self.expect("OP", "Expected '=' after variable name")
        if self.tokens[self.pos - 1].value != "=":
            raise ParserError(f"Line {self.tokens[self.pos - 1].line}: Expected '=' in declaration")

        expr = self.expression()
        self.match("SEMICOLON")
        return VarDecl(var_type, name_tok.value, expr)

    def assignment(self) -> Assignment:
        name_tok = self.advance()
        self.expect("OP", "Expected '=' after variable name")
        if self.tokens[self.pos - 1].value != "=":
            raise ParserError(f"Line {self.tokens[self.pos - 1].line}: Expected '=' in assignment")

        expr = self.expression()
        self.match("SEMICOLON")
        return Assignment(name_tok.value, expr)

    def print_stmt(self) -> PrintStmt:
        self.advance()
        expr = self.expression()
        self.match("SEMICOLON")
        return PrintStmt(expr)

    def if_stmt(self) -> IfStmt:
        self.advance()
        condition = self.condition_expression()
        then_body = self.block()
        else_body = None

        if self.match("ELSE"):
            else_body = self.block()

        return IfStmt(condition, then_body, else_body)

    def while_stmt(self) -> WhileStmt:
        self.advance()
        condition = self.condition_expression()
        body = self.block()
        return WhileStmt(condition, body)

    def block(self) -> List[Any]:
        self.expect("LBRACE", "Expected '{' to start block")
        statements = []

        while self.current().type != "RBRACE":
            if self.current().type == "EOF":
                raise ParserError("Unexpected end of file. Missing '}'")
            statements.append(self.statement())

        self.expect("RBRACE", "Expected '}' to end block")
        return statements

    def condition_expression(self) -> Any:
        if self.match("LPAREN"):
            expr = self.expression()
            self.expect("RPAREN", "Expected ')' after condition")
            return expr
        return self.expression()

    def expression(self) -> Any:
        return self.equality()

    def equality(self) -> Any:
        expr = self.comparison()
        while self.current().type == "OP" and self.current().value in ("==", "!="):
            op = self.advance().value
            right = self.comparison()
            expr = BinaryOp(expr, op, right)
        return expr

    def comparison(self) -> Any:
        expr = self.term()
        while self.current().type == "OP" and self.current().value in ("<", ">", "<=", ">="):
            op = self.advance().value
            right = self.term()
            expr = BinaryOp(expr, op, right)
        return expr

    def term(self) -> Any:
        expr = self.factor()
        while self.current().type == "OP" and self.current().value in ("+", "-"):
            op = self.advance().value
            right = self.factor()
            expr = BinaryOp(expr, op, right)
        return expr

    def factor(self) -> Any:
        expr = self.primary()
        while self.current().type == "OP" and self.current().value in ("*", "/"):
            op = self.advance().value
            right = self.primary()
            expr = BinaryOp(expr, op, right)
        return expr

    def primary(self) -> Any:
        tok = self.current()

        if tok.type == "NUMBER":
            self.advance()
            return Literal(float(tok.value), "num")

        if tok.type == "STRING":
            self.advance()
            return Literal(tok.value[1:-1], "String")

        if tok.type == "TRUE":
            self.advance()
            return Literal(True, "Boolean")

        if tok.type == "FALSE":
            self.advance()
            return Literal(False, "Boolean")

        if tok.type == "ID":
            self.advance()
            return Variable(tok.value)

        if tok.type == "LPAREN":
            self.advance()
            expr = self.expression()
            self.expect("RPAREN", "Expected ')' after expression")
            return expr

        raise ParserError(f"Line {tok.line}: Expected expression. Got '{tok.value}'")


# ============================================================
# Symbol Table
# ============================================================

class SymbolTable:
    """
    Stores variable names and their declared types for the semantic analysis stage.

    Each entry maps an identifier (str) to its Celestia type: 'num', 'String', or 'Boolean'.
    The table is built incrementally as VarDecl nodes are visited and is consulted
    for every Assignment and Variable reference to enforce type safety.
    """

    def __init__(self):
        self._table: dict[str, str] = {}

    def declare(self, name: str, var_type: str) -> None:
        """Register a new variable. Raises KeyError if already declared."""
        if name in self._table:
            raise KeyError(f"Variable '{name}' is already declared")
        self._table[name] = var_type

    def lookup(self, name: str) -> str:
        """Return the type of a declared variable. Raises KeyError if undeclared."""
        if name not in self._table:
            raise KeyError(f"Variable '{name}' is undeclared")
        return self._table[name]

    def contains(self, name: str) -> bool:
        """Return True if the variable has been declared."""
        return name in self._table

    def all_entries(self) -> dict[str, str]:
        """Return a copy of the full symbol table (name -> type)."""
        return dict(self._table)

    def __repr__(self) -> str:
        rows = "\n".join(f"  {name:<20} {vtype}" for name, vtype in self._table.items())
        return f"SymbolTable({{\n{rows}\n}})" if rows else "SymbolTable({})"


# ============================================================
# Semantic Analyzer
# ============================================================

class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    def __init__(self):
        self.symbols = SymbolTable()

    def analyze(self, program: Program) -> None:
        for stmt in program.statements:
            self.check_statement(stmt)

    def check_statement(self, stmt: Any) -> None:
        if isinstance(stmt, VarDecl):
            if stmt.name in KEYWORDS:
                raise SemanticError(f"'{stmt.name}' is a reserved keyword and cannot be used as a variable name")

            if self.symbols.contains(stmt.name):
                raise SemanticError(f"Variable '{stmt.name}' is already declared")

            expr_type = self.check_expr(stmt.expr)

            if stmt.var_type != expr_type:
                raise SemanticError(
                    f"TypeError: cannot assign {expr_type} value to {stmt.var_type} variable '{stmt.name}'"
                )

            self.symbols.declare(stmt.name, stmt.var_type)
            return

        if isinstance(stmt, Assignment):
            if not self.symbols.contains(stmt.name):
                raise SemanticError(f"Variable '{stmt.name}' is undeclared")

            expected = self.symbols.lookup(stmt.name)
            actual = self.check_expr(stmt.expr)

            if expected != actual:
                raise SemanticError(
                    f"TypeError: cannot assign {actual} value to {expected} variable '{stmt.name}'"
                )
            return

        if isinstance(stmt, PrintStmt):
            self.check_expr(stmt.expr)
            return

        if isinstance(stmt, IfStmt):
            cond_type = self.check_expr(stmt.condition)
            if cond_type != "Boolean":
                raise SemanticError("Condition in if statement must evaluate to Boolean")

            for s in stmt.then_body:
                self.check_statement(s)

            if stmt.else_body:
                for s in stmt.else_body:
                    self.check_statement(s)
            return

        if isinstance(stmt, WhileStmt):
            cond_type = self.check_expr(stmt.condition)
            if cond_type != "Boolean":
                raise SemanticError("Condition in while statement must evaluate to Boolean")

            for s in stmt.body:
                self.check_statement(s)
            return

        raise SemanticError(f"Unknown statement type: {stmt}")

    def check_expr(self, expr: Any) -> str:
        if isinstance(expr, Literal):
            return expr.literal_type

        if isinstance(expr, Variable):
            if not self.symbols.contains(expr.name):
                raise SemanticError(f"Variable '{expr.name}' is undeclared")
            return self.symbols.lookup(expr.name)

        if isinstance(expr, BinaryOp):
            left_type = self.check_expr(expr.left)
            right_type = self.check_expr(expr.right)

            if expr.op in {"+", "-", "*", "/"}:
                if expr.op == "+" and left_type == "String" and right_type == "String":
                    return "String"

                if left_type == right_type == "num":
                    return "num"

                raise SemanticError(
                    f"TypeError: operator '{expr.op}' cannot be used with {left_type} and {right_type}"
                )

            if expr.op in {"<", ">", "<=", ">="}:
                if left_type == right_type == "num":
                    return "Boolean"

                raise SemanticError(
                    f"TypeError: comparison '{expr.op}' requires two num values"
                )

            if expr.op in {"==", "!="}:
                if left_type == right_type:
                    return "Boolean"

                raise SemanticError(
                    f"TypeError: cannot compare {left_type} and {right_type}"
                )

        raise SemanticError(f"Unknown expression type: {expr}")


# ============================================================
# Code Generator
# ============================================================

class CodeGenerator:
    def __init__(self):
        self.lines: List[str] = []
        self.indent_level = 0

    def emit(self, line: str = "") -> None:
        self.lines.append("    " * self.indent_level + line)

    def generate(self, program: Program) -> str:
        self.emit("# Generated Python code from Celestia")
        self.emit()

        for stmt in program.statements:
            self.gen_statement(stmt)

        return "\n".join(self.lines) + "\n"

    def gen_statement(self, stmt: Any) -> None:
        if isinstance(stmt, VarDecl):
            self.emit(f"{stmt.name} = {self.gen_expr(stmt.expr)}")
            return

        if isinstance(stmt, Assignment):
            self.emit(f"{stmt.name} = {self.gen_expr(stmt.expr)}")
            return

        if isinstance(stmt, PrintStmt):
            self.emit(f"print({self.gen_expr(stmt.expr)})")
            return

        if isinstance(stmt, IfStmt):
            self.emit(f"if {self.gen_expr(stmt.condition)}:")
            self.indent_level += 1
            if stmt.then_body:
                for s in stmt.then_body:
                    self.gen_statement(s)
            else:
                self.emit("pass")
            self.indent_level -= 1

            if stmt.else_body is not None:
                self.emit("else:")
                self.indent_level += 1
                if stmt.else_body:
                    for s in stmt.else_body:
                        self.gen_statement(s)
                else:
                    self.emit("pass")
                self.indent_level -= 1
            return

        if isinstance(stmt, WhileStmt):
            self.emit(f"while {self.gen_expr(stmt.condition)}:")
            self.indent_level += 1
            if stmt.body:
                for s in stmt.body:
                    self.gen_statement(s)
            else:
                self.emit("pass")
            self.indent_level -= 1
            return

        raise ValueError(f"Unknown statement type: {stmt}")

    def gen_expr(self, expr: Any) -> str:
        if isinstance(expr, Literal):
            if expr.literal_type == "String":
                return repr(expr.value)
            if expr.literal_type == "Boolean":
                return "True" if expr.value else "False"
            return str(expr.value)

        if isinstance(expr, Variable):
            return expr.name

        if isinstance(expr, BinaryOp):
            return f"({self.gen_expr(expr.left)} {expr.op} {self.gen_expr(expr.right)})"

        raise ValueError(f"Unknown expression type: {expr}")


# ============================================================
# Compiler Driver
# ============================================================

def compile_source(source: str) -> str:
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    parser = Parser(tokens)
    ast = parser.parse()

    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    generator = CodeGenerator()
    return generator.generate(ast)


def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Celestia toy compiler")
    arg_parser.add_argument("file", help="Path to Celestia source file")
    arg_parser.add_argument("--out", help="Path to generated Python file")
    arg_parser.add_argument("--run", action="store_true", help="Run generated Python code after compiling")
    arg_parser.add_argument("--show", action="store_true", help="Print generated Python code")
    args = arg_parser.parse_args()

    try:
        source = open(args.file, "r", encoding="utf-8").read()
        generated = compile_source(source)

        out_path = args.out or args.file.rsplit(".", 1)[0] + "_compiled.py"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(generated)

        print(f"Compilation successful.")
        print(f"Generated file: {out_path}")

        if args.show:
            print()
            print("Generated Python:")
            print("-" * 50)
            print(generated)

        if args.run:
            print()
            print("Program output:")
            print("-" * 50)
            exec(generated, {})

    except (LexerError, ParserError, SemanticError) as e:
        print(f"Compilation failed: {e}")
        sys.exit(1)

    except FileNotFoundError:
        print(f"Compilation failed: file not found: {args.file}")
        sys.exit(1)


if __name__ == "__main__":
    main()