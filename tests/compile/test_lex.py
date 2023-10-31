import pytest

from opyl.compile import lex


class TestTakeWhile:
    def test_take_while(self):
        tokenizer = lex.Tokenizer("123\n456")
        assert tokenizer.take_while(str.isdigit) == "123"

    def test_take_while_nothing(self):
        tokenizer = lex.Tokenizer("")
        with pytest.raises(lex.NoMatch):
            tokenizer.take_while(str.isdigit)

    def test_take_while_nomatch(self):
        tokenizer = lex.Tokenizer("\n")
        with pytest.raises(lex.NoMatch):
            tokenizer.take_while(str.isdigit)

    def test_take_while_leading_no_match(self):
        tokenizer = lex.Tokenizer("\n456")
        with pytest.raises(lex.NoMatch):
            tokenizer.take_while(str.isdigit)

    def test_take_while_two_separated(self):
        tokenizer = lex.Tokenizer("2\n456")
        assert tokenizer.take_while(str.isdigit) == "2"
        assert tokenizer.stream.index.absolute == 1

        with pytest.raises(lex.NoMatch):
            tokenizer.take_while(str.isdigit)


class TestSimpleInteger:
    @pytest.mark.parametrize(
        ("source", "integer", "stop"),
        (
            ("5", 5, lex.TextPosition(absolute=1, line=0, column=1)),
            ("123", 123, lex.TextPosition(absolute=3, line=0, column=3)),
            ("5 ", 5, lex.TextPosition(absolute=1, line=0, column=1)),
            ("123 ", 123, lex.TextPosition(absolute=3, line=0, column=3)),
            ("123 456", 123, lex.TextPosition(absolute=3, line=0, column=3)),
        ),
    )
    def test_integer(self, source: str, integer: int, stop: lex.TextPosition):
        tokenizer = lex.Tokenizer(source)
        token = tokenizer.tokenize_integer()

        assert token.integer == integer
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == stop

    @pytest.mark.parametrize(("source"), (" 5", " 123"))
    def test_bad_integer(self, source: str):
        tokenizer = lex.Tokenizer(source)

        with pytest.raises(lex.UnexpectedCharacter):
            tokenizer.tokenize_integer()


class TestWhiteSpace:
    def test_empty_whitespace(self):
        tokenizer = lex.Tokenizer("")

        with pytest.raises(lex.NoMatch):
            tokenizer.tokenize_whitespace()

    def test_single_newline(self):
        tokenizer = lex.Tokenizer("\n")
        token = tokenizer.tokenize_whitespace()

        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=1, line=1, column=0)

    def test_multiple_newlines(self):
        tokenizer = lex.Tokenizer("\n\n\n")
        token = tokenizer.tokenize_whitespace()

        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=3, line=3, column=0)

    def test_single_space(self):
        tokenizer = lex.Tokenizer(" ")
        token = tokenizer.tokenize_whitespace()

        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=1, line=0, column=1)

    def test_spaces_then_newline(self):
        tokenizer = lex.Tokenizer("  \n")
        token = tokenizer.tokenize_whitespace()

        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=3, line=1, column=0)

    def test_newline_then_spaces(self):
        tokenizer = lex.Tokenizer("\n  ")
        token = tokenizer.tokenize_whitespace()

        assert token.span.start == lex.TextPosition(absolute=0, line=0, column=0)
        assert token.span.stop == lex.TextPosition(absolute=3, line=1, column=2)


class TestComment:
    def test_empty_comment(self):
        token = lex.Tokenizer("#").tokenize_comment()

        assert token.comment == ""
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=1, line=0, column=1)

    def test_single_space_comment(self):
        token = lex.Tokenizer("# ").tokenize_comment()

        assert token.comment == " "
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=2, line=0, column=2)

    def test_actual_comment(self):
        token = lex.Tokenizer("# foo").tokenize_comment()

        assert token.comment == " foo"
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=5, line=0, column=5)

    def test_comment_with_newline(self):
        token = lex.Tokenizer("# foo\nbar").tokenize_comment()

        assert token.comment == " foo"
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=5, line=0, column=5)


class TestIdentifierOrKeyword:
    def test_single_char_name(self):
        token = lex.Tokenizer("a").tokenize_identifier_or_keyword()

        assert isinstance(token, lex.IdentifierToken)
        assert token.identifier == "a"
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=1, line=0, column=1)

    def test_multichar_name(self):
        token = lex.Tokenizer("abc").tokenize_identifier_or_keyword()

        assert isinstance(token, lex.IdentifierToken)
        assert token.identifier == "abc"
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=3, line=0, column=3)

    def test_underscore(self):
        token = lex.Tokenizer("_").tokenize_identifier_or_keyword()

        assert isinstance(token, lex.IdentifierToken)
        assert token.identifier == "_"
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=1, line=0, column=1)

    def test_starts_with_number(self):
        tokenizer = lex.Tokenizer("1abc")

        with pytest.raises(lex.UnexpectedCharacter):
            tokenizer.tokenize_identifier_or_keyword()

    def test_letter_then_number(self):
        token = lex.Tokenizer("a1").tokenize_identifier_or_keyword()

        assert isinstance(token, lex.IdentifierToken)
        assert token.identifier == "a1"
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=2, line=0, column=2)

    def test_keyword_not_identifier(self):
        token = lex.Tokenizer("let").tokenize_identifier_or_keyword()

        assert not isinstance(token, lex.IdentifierToken)

    def test_keyword(self):
        token = lex.Tokenizer("let").tokenize_identifier_or_keyword()

        assert isinstance(token, lex.KeywordToken)


class TestString:
    def test_empty_string(self):
        token = lex.Tokenizer('""').tokenize_string()

        assert token.string == ""
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=2, line=0, column=2)

    def test_single_space_string(self):
        token = lex.Tokenizer('" "').tokenize_string()

        assert token.string == " "
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=3, line=0, column=3)

    def test_single_char_string(self):
        token = lex.Tokenizer('"a"').tokenize_string()

        assert token.string == "a"
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=3, line=0, column=3)

    def test_multichar_string(self):
        token = lex.Tokenizer('"abc def"').tokenize_string()

        assert token.string == "abc def"
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=9, line=0, column=9)

    def test_unbalanced_string(self):
        tokenizer = lex.Tokenizer('"abc')
        with pytest.raises(lex.UnclosedStringLiteral):
            tokenizer.tokenize_string()

    def test_newlined_string(self):
        tokenizer = lex.Tokenizer('"abc\n"')
        with pytest.raises(lex.UnexpectedCharacter):
            tokenizer.tokenize_string()


class TestChar:
    def test_single_literal(self):
        token = lex.Tokenizer("'a'").tokenize_character()

        assert isinstance(token, lex.CharacterToken)
        assert token.char == "a"
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=3, line=0, column=3)


class TestTokenizer:
    def test_integer(self):
        tokens = lex.tokenize("56")

        assert len(tokens) == 1

        token = tokens[0]

        assert isinstance(token, lex.IntegerToken)
        assert token.integer == 56
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=2, line=0, column=2)

    def test_whitespace(self):
        tokens = lex.tokenize("   ")

        assert len(tokens) == 1
        token = tokens[0]

        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=3, line=0, column=3)

    def test_space_then_integer(self):
        tokens = lex.tokenize("   56")

        assert len(tokens) == 2

        assert isinstance(tokens[0], lex.WhiteSpaceToken)
        assert isinstance(tokens[1], lex.IntegerToken)

        assert tokens[0].span.start == lex.TextPosition.default()
        assert tokens[0].span.stop == lex.TextPosition(absolute=3, line=0, column=3)

        assert tokens[1].integer == 56
        # assert tokens[1].span.start == lex.TextPosition(absolute=1, line=0, column=1)
        # assert token.span.stop == lex.TextPosition(absolute=3, line=0, column=3)

    def test_integer_with_space(self):
        tokens = lex.tokenize("56 ")

        assert len(tokens) == 2

        token = tokens[0]

        assert isinstance(token, lex.IntegerToken)
        assert token.integer == 56
        assert token.span.start == lex.TextPosition.default()
        assert token.span.stop == lex.TextPosition(absolute=2, line=0, column=2)

    def test_integer_then_integer(self):
        tokens = lex.tokenize("56 78")

        assert len(tokens) == 3
        assert isinstance(tokens[0], lex.IntegerToken)
        assert isinstance(tokens[1], lex.WhiteSpaceToken)
        assert isinstance(tokens[2], lex.IntegerToken)

        assert tokens[0].integer == 56
        assert tokens[2].integer == 78

        assert tokens[0].span.start == lex.TextPosition(absolute=0, line=0, column=0)
        assert tokens[0].span.stop == lex.TextPosition(absolute=2, line=0, column=2)

        assert tokens[1].span.start == lex.TextPosition(absolute=2, line=0, column=2)
        assert tokens[1].span.stop == lex.TextPosition(absolute=3, line=0, column=3)

        assert tokens[2].span.start == lex.TextPosition(absolute=3, line=0, column=3)
        assert tokens[2].span.stop == lex.TextPosition(absolute=5, line=0, column=5)

    def test_variable_declaration(self):
        tokens = lex.tokenize("let foo: u8")
        assert len(tokens) == 6

    def test_char_assignment(self):
        tokens = lex.tokenize("bar = 'a'")
        assert len(tokens) == 5
