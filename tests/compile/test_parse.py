from opyl import parse
from opyl import nodes


def test_parsing():
    parser = parse.OpalParser("const foo: Foo = 5\n")
    decls = parser()
    assert len(decls) == 1
