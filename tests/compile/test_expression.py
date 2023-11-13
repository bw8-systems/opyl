from opyl import expression
from opyl import positioning
from opyl import lex


def test():
    parser = expression.ExpressionParser(
        stream=positioning.Stream(stream=lex.tokenize("1"))
    )
    print(parser())
    assert False
