import pytest

from opyl import lex
from opyl import errors
from opyl import positioning
from opyl import lexemes


class TestTakeWhile:
    def test_take_while(self):
        tokenizer = lex.Tokenizer("123\n456")
        assert tokenizer.take_while(str.isdigit) == "123"

    def test_take_while_nothing(self):
        tokenizer = lex.Tokenizer("")
        with pytest.raises(errors.NoMatch):
            tokenizer.take_while(str.isdigit)

    def test_take_while_nomatch(self):
        tokenizer = lex.Tokenizer("\n")
        with pytest.raises(errors.NoMatch):
            tokenizer.take_while(str.isdigit)

    def test_take_while_leading_no_match(self):
        tokenizer = lex.Tokenizer("\n456")
        with pytest.raises(errors.NoMatch):
            tokenizer.take_while(str.isdigit)

    def test_take_while_two_separated(self):
        tokenizer = lex.Tokenizer("2\n456")
        assert tokenizer.take_while(str.isdigit) == "2"
        assert tokenizer.stream.index.absolute == 1

        with pytest.raises(errors.NoMatch):
            tokenizer.take_while(str.isdigit)


class TestSimpleInteger:
    @pytest.mark.parametrize(
        ("source", "integer", "stop"),
        (
            ("5", 5, positioning.TextPosition(absolute=1, line=0, column=1)),
            ("123", 123, positioning.TextPosition(absolute=3, line=0, column=3)),
            ("5 ", 5, positioning.TextPosition(absolute=1, line=0, column=1)),
            ("123 ", 123, positioning.TextPosition(absolute=3, line=0, column=3)),
            ("123 456", 123, positioning.TextPosition(absolute=3, line=0, column=3)),
        ),
    )
    def test_integer(self, source: str, integer: int, stop: positioning.TextPosition):
        tokenizer = lex.Tokenizer(source)
        token = tokenizer.tokenize_integer()

        assert token.integer == integer
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == stop

    @pytest.mark.parametrize(("source"), (" 5", " 123"))
    def test_bad_integer(self, source: str):
        tokenizer = lex.Tokenizer(source)

        with pytest.raises(errors.UnexpectedCharacter):
            tokenizer.tokenize_integer()


class TestWhiteSpace:
    def test_empty_whitespace(self):
        tokenizer = lex.Tokenizer("")

        with pytest.raises(errors.NoMatch):
            tokenizer.tokenize_whitespace()

    def test_single_space(self):
        tokenizer = lex.Tokenizer(" ")
        token = tokenizer.tokenize_whitespace()

        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=1, line=0, column=1)

    def test_spaces_then_newline(self):
        tokenizer = lex.Tokenizer("  \n")
        token = tokenizer.tokenize_whitespace()

        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=2, line=0, column=2)


class TestComment:
    def test_empty_comment(self):
        token = lex.Tokenizer("#").tokenize_comment()

        assert token.comment == ""
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=1, line=0, column=1)

    def test_single_space_comment(self):
        token = lex.Tokenizer("# ").tokenize_comment()

        assert token.comment == " "
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=2, line=0, column=2)

    def test_actual_comment(self):
        token = lex.Tokenizer("# foo").tokenize_comment()

        assert token.comment == " foo"
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=5, line=0, column=5)

    def test_comment_with_newline(self):
        token = lex.Tokenizer("# foo\nbar").tokenize_comment()

        assert token.comment == " foo"
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=5, line=0, column=5)


class TestIdentifierOrKeyword:
    def test_single_char_name(self):
        token = lex.Tokenizer("a").tokenize_identifier_or_keyword()

        assert isinstance(token, lexemes.Identifier)
        assert token.identifier == "a"
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=1, line=0, column=1)

    def test_multichar_name(self):
        token = lex.Tokenizer("abc").tokenize_identifier_or_keyword()

        assert isinstance(token, lexemes.Identifier)
        assert token.identifier == "abc"
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=3, line=0, column=3)

    def test_underscore(self):
        token = lex.Tokenizer("_").tokenize_identifier_or_keyword()

        assert isinstance(token, lexemes.Identifier)
        assert token.identifier == "_"
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=1, line=0, column=1)

    def test_starts_with_number(self):
        tokenizer = lex.Tokenizer("1abc")

        with pytest.raises(errors.UnexpectedCharacter):
            tokenizer.tokenize_identifier_or_keyword()

    def test_letter_then_number(self):
        token = lex.Tokenizer("a1").tokenize_identifier_or_keyword()

        assert isinstance(token, lexemes.Identifier)
        assert token.identifier == "a1"
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=2, line=0, column=2)

    def test_keyword_not_identifier(self):
        token = lex.Tokenizer("let").tokenize_identifier_or_keyword()

        assert not isinstance(token, lexemes.Identifier)

    def test_keyword(self):
        token = lex.Tokenizer("let").tokenize_identifier_or_keyword()

        assert isinstance(token, lexemes.Keyword)


class TestString:
    def test_empty_string(self):
        token = lex.Tokenizer('""').tokenize_string()

        assert token.string == ""
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=2, line=0, column=2)

    def test_single_space_string(self):
        token = lex.Tokenizer('" "').tokenize_string()

        assert token.string == " "
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=3, line=0, column=3)

    def test_single_char_string(self):
        token = lex.Tokenizer('"a"').tokenize_string()

        assert token.string == "a"
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=3, line=0, column=3)

    def test_multichar_string(self):
        token = lex.Tokenizer('"abc def"').tokenize_string()

        assert token.string == "abc def"
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=9, line=0, column=9)

    def test_unbalanced_string(self):
        tokenizer = lex.Tokenizer('"abc')
        with pytest.raises(errors.UnclosedStringLiteral):
            tokenizer.tokenize_string()

    def test_newlined_string(self):
        tokenizer = lex.Tokenizer('"abc\n"')
        with pytest.raises(errors.UnexpectedCharacter):
            tokenizer.tokenize_string()


class TestChar:
    def test_single_literal(self):
        token = lex.Tokenizer("'a'").tokenize_character()

        assert isinstance(token, lexemes.CharacterLiteral)
        assert token.char == "a"
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=3, line=0, column=3)


class TestTokenizer:
    def test_integer(self):
        token_list = lex.tokenize("56")

        assert len(token_list) == 1

        token = token_list[0]

        assert isinstance(token, lexemes.IntegerLiteral)
        assert token.integer == 56
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=2, line=0, column=2)

    def test_whitespace(self):
        tokens = lex.tokenize("   ")

        assert len(tokens) == 1
        token = tokens[0]

        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=3, line=0, column=3)

    def test_space_then_integer(self):
        tokens_list = lex.tokenize("   56")

        assert len(tokens_list) == 2

        assert isinstance(tokens_list[0], lexemes.Whitespace)
        assert isinstance(tokens_list[1], lexemes.IntegerLiteral)

        assert tokens_list[0].span.start == positioning.TextPosition.default()
        assert tokens_list[0].span.stop == positioning.TextPosition(
            absolute=3, line=0, column=3
        )

        assert tokens_list[1].integer == 56
        # assert tokens_list[1].span.start == stream.TextPosition(absolute=1, line=0, column=1)
        # assert token.span.stop == stream.TextPosition(absolute=3, line=0, column=3)

    def test_integer_with_space(self):
        tokens_list = lex.tokenize("56 ")

        assert len(tokens_list) == 2

        token = tokens_list[0]

        assert isinstance(token, lexemes.IntegerLiteral)
        assert token.integer == 56
        assert token.span.start == positioning.TextPosition.default()
        assert token.span.stop == positioning.TextPosition(absolute=2, line=0, column=2)

    def test_integer_then_integer(self):
        token_list = lex.tokenize("56 78")

        assert len(token_list) == 3
        assert isinstance(token_list[0], lexemes.IntegerLiteral)
        assert isinstance(token_list[1], lexemes.Whitespace)
        assert isinstance(token_list[2], lexemes.IntegerLiteral)

        assert token_list[0].integer == 56
        assert token_list[2].integer == 78

        assert token_list[0].span.start == positioning.TextPosition(
            absolute=0, line=0, column=0
        )
        assert token_list[0].span.stop == positioning.TextPosition(
            absolute=2, line=0, column=2
        )

        assert token_list[1].span.start == positioning.TextPosition(
            absolute=2, line=0, column=2
        )
        assert token_list[1].span.stop == positioning.TextPosition(
            absolute=3, line=0, column=3
        )

        assert token_list[2].span.start == positioning.TextPosition(
            absolute=3, line=0, column=3
        )
        assert token_list[2].span.stop == positioning.TextPosition(
            absolute=5, line=0, column=5
        )

    def test_variable_declaration(self):
        tokens = lex.tokenize("let foo: u8")
        assert len(tokens) == 6

    def test_char_assignment(self):
        tokens = lex.tokenize("bar = 'a'")
        assert len(tokens) == 5
