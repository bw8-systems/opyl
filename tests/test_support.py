from opyl.compile.token import Identifier, IntegerLiteral
from opyl.support.stream import Stream
from opyl.compile import lex


class TestStream:
    def test_startswith_str_success(self):
        stream = Stream(list("foo"))

        assert stream.startswith("f")
        assert stream.startswith("fo")
        assert stream.startswith("foo")

    def test_startswith_str_fail(self):
        stream = Stream(list("foo"))

        assert not stream.startswith("oof")
        assert not stream.startswith("of")
        assert not stream.startswith(" f")

    def test_startswith_str_empty(self):
        stream = Stream(list(""))

        assert not stream.startswith("")
        assert not stream.startswith(" ")

    def test_startswith_empty_pattern(self):
        stream = Stream(list("foo"))

        assert not stream.startswith("")
        assert not stream.startswith(" ")

    def test_startswith_tok_success(self):
        tokens, _ = lex.tokenize("foo").unwrap()

        assert tokens.startswith([Identifier("foo")])

    def test_startswith_multi_tok_success(self):
        tokens, _ = lex.tokenize("foo 4").unwrap()

        assert tokens.startswith([Identifier("foo"), IntegerLiteral(4)])
