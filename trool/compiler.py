"""Canonical compiler pipeline for Trool source code to Python."""
from trool.lexer import tokenize
from trool.parser import parse
from trool.semantic import analyze
from trool.lowering import lower_to_python


def compile_source(source: str) -> str:
    """Compile Trool source code to target Python module source.

    Pipeline phases:
    1. Lexer (tokenization)
    2. Parser (syntactic / AST construction)
    3. Semantic analysis (types, exhaustiveness, definite return validation)
    4. Code generation (Python lowering)
    """
    tokens = tokenize(source)
    ast = parse(tokens)
    analyzer = analyze(ast)
    return lower_to_python(ast, analyzer.result)
