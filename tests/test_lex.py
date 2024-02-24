from opyl.compile.lex import (
    IntegerLiteral,
    Identifier,
    StringLiteral,
    CharacterLiteral,
    integer,
    identifier,
    string,
    character,
    basic,
)
from opyl.compile.token import Basic, IntegerLiteralBase
from opyl.compile.error import LexError
from .utils import parse_test_err, lex_test


class TestBasic:
    def test_single_plus(self):
        lex_test(basic, "+", Basic.Plus)

    def test_asterisk(self):
        lex_test(basic, "*", Basic.Asterisk)

    def test_newline(self):
        lex_test(basic, "\n", Basic.NewLine)

    def test_hyphen(self):
        lex_test(basic, "-", Basic.Hyphen)

    def test_right_arrow(self):
        lex_test(basic, "->", Basic.RightArrow)

    def test_pipe(self):
        lex_test(basic, "|", Basic.Pipe)

    def test_pipe2(self):
        lex_test(basic, "||", Basic.Pipe2)

    def test_angle2(self):
        lex_test(basic, ">>", Basic.RightAngle2)

    def test_angle_equal(self):
        lex_test(basic, ">=", Basic.RightAngleEqual)


class TestIntegerLiteral:
    def test_empty_integer(self):
        lex_test(integer, "", None)

    def test_single_digit_integer(self):
        lex_test(integer, "5", IntegerLiteral(5))

    def test_multi_digit_integer(self):
        lex_test(integer, "512", IntegerLiteral(512))

    def test_zero_integer(self):
        lex_test(integer, "0", IntegerLiteral(0))

    def test_illegal_integer(self):
        lex_test(
            integer, "05", IntegerLiteral(0)
        )  # TODO: Should be illegal. We'll fix it in post.

    def test_binary_literal(self):
        lex_test(integer, "0b01", IntegerLiteral(0b01, IntegerLiteralBase.Binary))

    def test_hex_literal(self):
        lex_test(
            integer,
            "0xdeadBEEF",
            IntegerLiteral(0xDEADBEEF, IntegerLiteralBase.Hexadecimal),
        )

    def test_underscore_in_literal(self):
        lex_test(integer, "4_5", IntegerLiteral(45))

    def test_invalid_integer_leading_underscore(self):
        lex_test(integer, "_45", None)

    def test_underscore_in_hex_literal(self):
        lex_test(
            integer, "0x_4_5", IntegerLiteral(0x45, IntegerLiteralBase.Hexadecimal)
        )

    def test_hex_literal_with_followers(self):
        lex_test(
            integer, "0x3 foo 'a'", IntegerLiteral(0x3, IntegerLiteralBase.Hexadecimal)
        )


class TestIdentifier:
    def test_ident(self):
        lex_test(identifier, "foo", Identifier("foo"))

    def test_empty_ident(self):
        lex_test(identifier, "", None)

    def test_illegal_ident_leading_digit(self):
        lex_test(identifier, "5foo", None)

    def test_ident_underscore(self):
        lex_test(identifier, "_", Identifier("_"))

    def test_ident_leading_underscore(self):
        lex_test(identifier, "_foo", Identifier("_foo"))


class TestStringLiteral:
    def test_string(self):
        lex_test(string, '"foo"', StringLiteral("foo"))

    def test_empty_string(self):
        lex_test(string, '""', StringLiteral(""))

    def test_unterminated_string(self):
        parse_test_err(string, '"foo', LexError.UnterminatedStringLiteral)

    def test_newline_string(self):
        parse_test_err(string, '"foo\n"', LexError.UnterminatedStringLiteral)


class TestCharacterLiteral:
    def test_char(self):
        lex_test(character, "'a'", CharacterLiteral("a"))

    def test_long_char(self):
        parse_test_err(character, "'aa'", LexError.UnterminatedCharacterLiteral)

    def test_unterminated_char(self):
        parse_test_err(character, "'a", LexError.UnterminatedCharacterLiteral)
