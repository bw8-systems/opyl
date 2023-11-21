import typing as t

from compile import lexemes


class ParseException(Exception):
    ...


class UnexpectedEOF(ParseException):
    @classmethod
    def instead_of_primitive(cls, kind: "lexemes.PrimitiveKind") -> t.Self:
        return cls(
            f"Token stream was exhausted while looking for primitive token '{kind.value}'"
        )

    @classmethod
    def instead_of_integer(cls) -> t.Self:
        return cls("Token stream was exhausted while looking for integer literal.")


class UnexpectedToken(ParseException):
    @classmethod
    def instead_of_primitive(
        cls, got: "lexemes.Token", instead_of: "lexemes.PrimitiveKind"
    ) -> t.Self:
        return cls(
            f"Got token {got} while looking for primitive token '{instead_of.value}'"
        )

    @classmethod
    def wrong_primitive(
        cls, got: "lexemes.PrimitiveKind", expected: "lexemes.PrimitiveKind"
    ) -> t.Self:
        return cls(
            f"Got primitive token '{got.value}' while looking for primitive token '{expected.value}'"
        )

    @classmethod
    def instead_of_integer(cls, got: "lexemes.Token") -> t.Self:
        return cls(f"Got token {got} while looking for integer literal.")

    @classmethod
    def instead_of_identifier(cls, got: "lexemes.Token") -> t.Self:
        return cls(f"Got token {got} while looking for identifier token.")

    @classmethod
    def instead_of_keyword(
        cls, got: "lexemes.Token", expected: "lexemes.KeywordKind"
    ) -> t.Self:
        return cls(f"Got token {got} while looking for keyword '{expected}'")


class CompileError(Exception):
    ...


class LexError(CompileError):
    ...


class UnexpectedCharacter(LexError):
    ...


class NoMatch(LexError):
    ...


# class UnexpectedEOF(LexError):
#     ...


class UnclosedStringLiteral(LexError):
    ...


class IllegalCharacter(LexError):
    ...


class ParseError(CompileError):
    ...


# class UnexpectedToken(ParseError):
#     ...
