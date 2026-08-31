"""Canonical compiler pipeline for X-o-X source code to Python."""
from xoxlang.lexer import tokenize
from xoxlang.parser import parse
from xoxlang.semantic import analyze
from xoxlang.lowering import lower_to_python


def compile_source(source: str) -> str:
    """Compile X-o-X source code to target Python module source.

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
